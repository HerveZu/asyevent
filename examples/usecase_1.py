from __future__ import annotations

import asyncio
import random

from typing import Union
from warnings import warn

# imports needed classes
from asyevent import Event, EventManager, EventWrapperMixin, Callback, IParsable

# creates an event manager
manager = EventManager()


class Data(IParsable):
    """
    Creating our own parsing type by implementing IParable.
    """
    def __init__(self, value: Union[int, float, str]):
        self.value = value

    def __repr__(self) -> str:
        """
        Implement a representation.
        """
        return f'>> Data :: {self.value!r} <<'

    @classmethod
    def __parse__(cls, value: Union[int, float, str]) -> Data:
        """
        The method that returns an `Data` instance from a value.
        """
        return cls(value)


class Server:
    """
    An example server class which is listening for data
    """
    def __init__(self):
        # creates an event for data received
        self.data_received = manager.create_event('data_received')
        # creates an event for data lost
        self.data_lost = manager.create_event('data_lost')
        # creates an event for data ok
        self.data_ok = manager.create_event('data_ok')
        # creates an event for server shut down, handle_errors set to false avoid exceptions to be catch and pass
        # into the manager error handler
        self.shutdown = manager.create_event('shut_down', handle_errors=False)

    async def process_data(self, data: str):
        """
        An example method which process data
        """

        print('\n---- starting process ----\n')

        # raises the data received event if the data correctly processed
        # pass `data` as a parameter of the event
        await self.data_received.raise_event(data)

        # raises the shutdown event
        await self.shutdown.raise_event()


server = Server()


class DataProcess(EventWrapperMixin):
    """
    A class that wrap event/command callbacks.
    It inherits from `EventWrapperMixin` to be able to use `self` param.
    """

    # add `on_data_received` coroutine as a callback for the event `data_received`.
    # type hinting data with `Data` force the parsing.
    @server.data_received.before.as_class_callback()
    async def on_data_received(self, data: Data):
        print(f'Data received : {data!r}.')

    @server.data_received.as_class_callback()
    async def process_data(self, data: Data):
        # simulate processing time
        await asyncio.sleep(1)

        if len(data.value) + random.randint(0, 10) % 2 == 0:
            # raises the data lost event if the data are lost
            await server.data_lost.raise_event()

        else:
            # raises the data lost event if the data are OK
            await server.data_ok.raise_event()

    @server.data_lost.as_class_callback()
    async def on_data_lose(self):
        raise RuntimeError('Data lost')

    @server.data_ok.as_class_callback()
    async def on_data_ok(self):
        print('Data OK !')

    # uses `.after` event which refers to an event that is raised
    # when the parent event's (data_lost) callbacks are ended
    # start delay is the delay before the callback
    @server.data_received.after.as_class_callback()
    async def after_data_received(self, time_took: float, data: Data):
        print(f'Processing {data} took {time_took} seconds')


# uses `.before` event which refers to an event that is raised
# before any parent's event (shutdown) is invoked
@server.shutdown.before.as_callback()
async def shutting_down():
    print('Shutting down...')

    # simulate shutting down processing time
    await asyncio.sleep(3)


@server.shutdown.as_callback()
async def ready_to_shutdown():
    print('Server shut down.')


# the manager error handler event. It is raised when a error occur in a manager's event
# only if the param `handle_errors` is set to true (default).
# this event pass in the parameters the error, the event and the callback where the error happened.
# args and kwargs are the arguments/keyword arguments passed when the event has be raised.
@manager.error_handler.as_callback()
async def on_error(error: Exception, event: Event, callback: Callback, *args, **kwargs):
    warn(Warning(
        f'An {type(error)} error occurred while raising {event.event_name!r} event -> Callback : {callback.__name__!r}. '
        f'Passed args : {args, kwargs}.'
    ))


if __name__ == '__main__':
    # initializes wrapped callbacks, this is a absolute mandatory step in order to use classmethod callbacks
    DataProcess().init_callbacks()

    # displays the registered events and commands
    print(f'Registered events : {[e.event_name for e in manager.events]}')
    print(f'Registered commands : {[e.command_name for e in manager.commands]}.')

    # sends data to the server
    manager.loop.run_until_complete(server.process_data('A cool data'))

from __future__ import annotations

import asyncio
import random

from typing import Union
from warnings import warn

# imports needed classes
from asyevent import Event, EventManager, EventWrapper, Callback


# creates an event manager
manager = EventManager()

# creates a global event
start_event = manager.create_event("starting")


class Data:
    """
    Creating our own parsing type by implementing IParable.
    """

    def __init__(self, value: Union[int, float, str]):
        self.value = value

    def __repr__(self) -> str:
        """
        Implement a representation.
        """
        return f">> Data :: {self.value!r} <<"

    @classmethod
    def __parse__(cls, value: Union[int, float, str]) -> Data:
        """
        The method that returns an `Data` instance from a value.
        """
        return cls(value)


class Server(EventWrapper):
    """
    An example server class which is listening for data.
    It inherits from `EventWrapper` in order to use `self` param.
    """

    def __init__(self, m: EventManager):
        super().__init__()

        # creates events
        self.data_received = m.create_event("data_received")
        self.data_lost = m.create_event("data_lost")
        self.data_ok = m.create_event("data_ok")

        # handle_errors set to false avoid exceptions to be catch and pass
        self.shutdown = m.create_event("shut_down", handle_errors=False)

    # `start_delay` is the time took the the callback to start perform
    @start_event.as_callback(start_delay=1)
    async def process_data(self, data: str):
        """
        An example method which processes data
        """
        print("\n---- starting process ----\n")

        # raises the data received event if the data correctly processed
        # pass `data` as a parameter of the event
        await self.data_received.raise_event(data)

        # raises the shutdown event
        await self.shutdown.raise_event()


class EventsWrapper(EventWrapper):
    """
    A class that wrap event/command callbacks.
    It inherits from `EventWrapper` in order to use `self` param.
    """

    server = Server(manager)

    # add `on_data_received` coroutine as a callback for the event `on_data_received`.
    # type hinting data with `Data` forces the parsing from the passed parameter to a `Data` type.
    # `Event.before` is an event which is raised before its parent event.
    @server.data_received.before().as_callback()
    async def on_data_received(self, data: Data):
        print(f"Data received : {data!r}.")

    @server.data_received.as_callback()
    async def process_data(self, data: Data):
        # simulate processing time
        await asyncio.sleep(1)

        # random choice between lose or not data
        if len(data.value) + random.randint(0, 10) % 2 == 0:
            # raises the data lost event if the data are lost
            await self.server.data_lost.raise_event()

        else:
            # raises the data lost event if the data are OK
            await self.server.data_ok.raise_event()

    @server.data_lost.as_callback()
    async def on_data_lose(self):
        raise RuntimeError("Data lost")

    @server.data_ok.as_callback()
    async def on_data_ok(self):
        print("Data OK !")

    # uses `.after` event which refers to an event that is raised,
    # the first argument is the time took by the previous event's callbacks
    # when all if the parent event's callbacks finish
    @server.data_received.after(pass_extra=True).as_callback()
    async def after_data_received(self, time_took: int, data: Data):
        print(f"Processing {data} took {time_took} seconds")

    # before any parent's event (shutdown) is invoked
    @server.shutdown.before().as_callback()
    async def shutting_down(self):
        print("Shutting down...")

        # simulate shutting down processing time
        await asyncio.sleep(3)

    @server.shutdown.as_callback()
    async def ready_to_shutdown(self):
        print("Server shut down.")


# the manager error handler event.
# It is raised when a error occur in a manager's event only if the param `handle_errors` is set to true (default).
# this event pass in the parameters the error, the event and the callback where the error happened.
# args and kwargs are the arguments/keyword arguments passed when the event has be raised.
@manager.error_handler.as_callback()
async def on_error(error: Exception, event: Event, callback: Callback, *args, **kwargs):
    warn(
        Warning(
            f"An {type(error)} error occurred while raising {event.event_name!r} event -> Callback : {callback.__name__!r}."
            f"\nPassed args : {args, kwargs}."
            f"\n {error}"
        )
    )


async def main():
    # raises the start event
    await start_event.raise_event("A cool data")


if __name__ == "__main__":
    events = EventsWrapper()

    # displays the registered events and commands
    print(f"Registered events : {[e.event_name for e in manager.events]}")
    print(f"Registered commands : {[e.command_name for e in manager.commands]}.")

    # main
    manager.loop.run_until_complete(main())

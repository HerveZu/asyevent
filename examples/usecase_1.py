import asyncio
import random
import time

# imports needed classes
from asyevent import Event, EventManager, EventWrapperMixin, Callback

# creates a main event manager
manager = EventManager()


class Server:
    """
    An example server class which is listening for data
    """
    def __init__(self):
        # creates an event for data received
        self.data_received = manager.create_event('data_received')
        # creates an event for data lost
        self.data_lost = manager.create_event('data_lost')
        # creates an event for server shut down, handle_errors set to false avoid exceptions to be catch and pass
        # into the manager error handler
        self.shutdown = manager.create_event('shut_down', handle_errors=False)

        self.start_at = time.time()

    async def send_data(self, data: str):
        print('\n---- starting process ----\n')

        # invokes the command `hello`
        print('invokes the command `hello`')
        await manager.invoke_command('hello', 'world')

        # replaces the command's name
        manager.replace_command_name('hello', 'hello2')

        # invokes the command with the new name
        print('invokes the command with the new name')
        await manager.invoke_command('hello2', 'I\'m still working')

        print('\n---- sending data process ----\n')

        await self.process_data(data)

    async def process_data(self, data: str):
        """
        An example method which process data
        """

        # 1/2 chance to lost data
        if bool(int(random.randint(0, 1))):
            # raises the data received event if the data correctly processed
            # pass `data` as a parameter of the event
            await self.data_received.raise_event(data)

        else:
            # raises the data lost event if the data are lost
            await self.data_lost.raise_event()

        # raises the shutdown event
        await self.shutdown.raise_event(time.time() - self.start_at)


server = Server()


class Events(EventWrapperMixin):
    """
    A class that wrap event/command callbacks.
    It inherits from `EventWrapperMixin` to be able to use `self` param.
    """

    # add `data_received_callback` coroutine as a callback for the event `data_received`.
    @server.data_received.as_class_callback()
    async def data_received_callback(self, data):
        print(f'Data received : {data!r}.')

    # priority defines in which position the callback is in the invocation queue.
    # Higher it is, earlier it will be raised
    @server.data_lost.as_class_callback(priority=1)
    async def data_lost_callback1(self):
        raise RuntimeError('Data lost.')

    @server.data_lost.as_class_callback(priority=2)
    async def data_lost_callback2(self):
        print('Data lost.')

    # uses `.after` event which refers to an event that is raised
    # when the parent event's (data_lost) callbacks are ended
    # start delay is the delay before the callback
    @server.data_lost.after.as_class_callback(start_delay=1)
    async def after_data_lost(self, time_took: int):
        print(f'1 sec after data lost. Process time took {time_took} seconds.')

    # the manager error handler event. It is raised when a error occur in a manager's event
    # only if the param `handle_errors` is set to true (default).
    # this event pass in the parameters the error, the event and the callback where the error happened.
    # args and kwargs are the arguments/keyword arguments passed when the event has be raised.
    @manager.error_handler.as_class_callback()
    async def on_error(self, error: Exception, event: Event, callback: Callback, *args, **kwargs):
        print(
            f'An {type(error)} error occurred while raising {event.event_name!r} event -> Callback : {callback.__name__!r}. '
            f'Passed args : {args, kwargs}.'
        )


# adds the hello_command as a callback of both a manager's command and the `data_received` event
@server.data_received.as_callback()
@manager.as_command(name='hello')
async def hello_command(mess: str):
    print(f'Hello, {mess} !')


# uses `.before` event which refers to an event that is raised
# before any parent's event (shutdown) is invoked
@server.shutdown.before.as_callback()
async def shutdown_before(_: int):
    print('Shutting down...')

    await asyncio.sleep(3)


# adds a callback to the `shutdown_callback` event but it is not wrapped into a class
# note the decorator name changes
@server.shutdown.as_callback(priority=1)
async def shutdown_callback(life_duration: int):
    print(f'The server was running for {life_duration} seconds.')


@server.shutdown.as_callback(priority=2)
async def shutdown_callback(_: int):
    print('Juste before shut down.')


if __name__ == '__main__':
    # initializes wrapped callbacks, this is a absolute mandatory step in order to use classmethod callbacks
    Events().init_callbacks()

    # displays the registered events and commands
    print(f'Registered events : {[e.event_name for e in manager.events]}')
    print(f'Registered commands : {[e.command_name for e in manager.commands]}.')

    # sends data to the server
    manager.loop.run_until_complete(server.send_data('A cool data'))

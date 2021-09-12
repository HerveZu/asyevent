import asyncio
import random
import time

from asyevent import Event, EventManager, EventWrapperMixin, Callback

manager = EventManager()


class Server:
    def __init__(self):
        self.data_received = manager.create_event('data_received')
        self.data_lost = manager.create_event('data_lost')
        self.shutdown = manager.create_event('shut_down', handle_errors=False)

        self.start_at = time.time()

    async def send_data(self, data: str):
        if bool(int(random.randint(0, 1))):
            await self.data_received.raise_event(data)

        else:
            await self.data_lost.raise_event()

        await self.shutdown.raise_event(time.time() - self.start_at)


server = Server()


class Events(EventWrapperMixin):
    @server.data_received.as_class_callback()
    async def data_received(self, data):
        print(f'Data received : {data!r}.')

    @manager.as_class_command(name='I CAN LOOP', loop=3, loop_delay=0.5)
    async def can_loop(self):
        print('I loop.')

    @server.data_lost.as_class_callback(priority=1)
    async def data_lost(self):
        raise RuntimeError('Data lost.')

    @server.data_lost.as_class_callback(priority=2)
    async def data_lost_print(self):
        print('Data lost.')

    @server.data_lost.after.as_class_callback(start_delay=1)
    async def after_data_lost(self, time_took: int):
        print(f'1 sec after data lost. Process time took {time_took} seconds.')

    @manager.error_handler.as_class_callback()
    async def on_error(self, error: Exception, event: Event, callback: Callback, *args, **kwargs):
        print(
            f'An {type(error)} error occurred while raising {event.event_name!r} event -> Callback : {callback.__name__!r}. '
            f'Passed args : {args, kwargs}.'
        )


@server.data_received.as_callback()
@manager.as_command()
async def hello(mess: str):
    print(f'Hello, {mess} !')


@server.shutdown.before.as_callback()
async def shutdown_before(_: int):
    print('Shutting down...')

    await asyncio.sleep(3)


@server.shutdown.as_callback(priority=1)
async def shutdown(life_duration: int):
    print(f'The server was running for {life_duration} seconds.')


@server.shutdown.as_callback(priority=2)
async def shutdown(_: int):
    print('Juste before shut down.')


if __name__ == '__main__':
    Events().init_callbacks()
    print(f'Registered events : {[e.event_name for e in manager.events]}')
    print(f'Registered commands : {[e.command_name for e in manager.commands]}.')

    manager.loop.run_until_complete(manager.invoke_command('hello', 'world'))

    manager.replace_command_name('hello', 'hello2')

    manager.loop.run_until_complete(manager.invoke_command('hello2', 'I\'m still working'))
    manager.loop.run_until_complete(manager.invoke_command('I can loop', case_sensitive=False))
    manager.loop.run_until_complete(server.send_data('A cool data'))

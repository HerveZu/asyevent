import asyncio
from asyevent import EventManager


# creates a main event manager
manager = EventManager()

# creates an event
sample_event = manager.create_event('sample_event')


# adds `call_on_event` coroutine as sample_event's callback
@sample_event.as_callback()
async def sample_event_callback(text: str):
    print(text)
    await asyncio.sleep(2)


# uses `.after` event which refers to an event that is raised
# when the parent event's callbacks are ended (data_lost)
@sample_event.after.as_callback()
async def after_event(time_took: int, *args):
    # invokes the command `say`
    await manager.invoke_command('say', f'I\'ve been here for {time_took} seconds')


# adds the `hello` coroutine as a callback of the command `say_hello`
@manager.as_command(name='say')
async def say_stm(name: str):
    print(f'Hello, {name} !')


if __name__ == '__main__':
    # raises the event `sample_event`
    manager.loop.run_until_complete(
        sample_event('Hello, world !')
    )

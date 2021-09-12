import asyncio

from asyevent import EventManager

manager = EventManager()
sample_event = manager.create_event('sample_event')


@sample_event.as_callback()
async def call_on_event(text: str):
    print(text)
    await asyncio.sleep(2)


@sample_event.after.as_callback()
async def after_event(time_took: int, *args):
    await manager.invoke_command('say_hello', f'I\'ve been here for {time_took} seconds')


@manager.as_command('say_hello')
async def hello(name: str):
    print(f'Hello, {name} !')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(sample_event('Hello, world !'))    # could use `Event`.raise_event() instead.

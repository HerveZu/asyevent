"""
An implementation of events and asynchronous callbacks using decorators.

Code documentation is not currently complete.
Any contribution is greatly appreciated.

example :
    import asyncio

    manager = EventManager()
    sample_event = manager.create_event('sample_event')


    @sample_event.as_callback()
    async def call_on_event(text: str):
        print(text)

    manager.loop.run_until_complete(sample_event('Hello, world !'))    # could use `Event`.raise_event() instead.

"""

from asyevent.event import Event
from asyevent.event_manager import EventManager
from asyevent.event_wrapper import EventWrapper
from asyevent.callback import Callback
from asyevent.command import Command


__author__ = "Zucchinetti Hervé"
__status__ = "In development"
__version__ = "0.2.3"

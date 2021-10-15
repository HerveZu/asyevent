from __future__ import annotations

import asyncio
import time

from typing import Callable, Union, List, Dict, Tuple

from asyevent.callback import Callback
from asyevent.exceptions import EventAlreadyExists


class Event:
    """
    Do not manually initialise this class. Use instead `EventManager.create_event()`.

    Events contain `Callback` objects. They can be raised for invoke all callbacks stored.
    """

    def __init__(
        self,
        name: str,
        *,
        event_manager,
        handle_errors: bool = True,
        multiple_callbacks: bool = True,
    ):
        """
        Initialises an event.

        :param name: The event name. Must be unique in the event manager.
        :param event_manager: An event manager.
        :param handle_errors: Are the errors handled into the `event_manager` error handler.
        :param multiple_callbacks: Does the command allow multiple callbacks associated to.

        :raise EventAlreadyExists: If the event name is not unique in the event_manager.
        """
        self.event_name = name

        if event_manager.get_event(self.event_name, case_sensitive=False):
            raise EventAlreadyExists(event_manager.get_event(self.event_name))

        self.handle_errors = handle_errors
        self.event_manager = event_manager
        self.multiple_callbacks = multiple_callbacks

        self._before = None
        self._after = None

        self._loop = asyncio.get_event_loop()
        self._tasks: List[asyncio.Task] = []
        self._callbacks: Dict[int, List[Callback]] = {}

    def __iadd__(self, callback: Callback):
        # default priority, use `.add_callback()` to custom it.
        self.add_callback(callback)

        return self

    def __isub__(self, callback: Callback):
        self.remove_callback(callback)

        return self

    async def __call__(self, *args, **kwargs):
        await self.raise_event(*args, **kwargs)

    @property
    def before(self) -> Event:
        """
        Returns an event that is raised before callbacks.
        The current parameters will be passed to the callback.
        """
        if not self._before:
            self._before = self.event_manager.create_event(
                f"<before:{self.event_name}>", handle_errors=self.handle_errors
            )

        return self._before

    @property
    def after(self) -> Event:
        """
        Returns an event that is raised after the callbacks.
        Their execution duration in seconds as
        well as the current parameters, will be passed to the callback.
        """
        if not self._after:
            self._after = self.event_manager.create_event(
                f"<after:{self.event_name}>", handle_errors=self.handle_errors
            )

        return self._after

    @property
    def callbacks(self) -> Tuple[Callback]:
        """
        Sorts callbacks by layer level desc and return them into a tuple.

        :return: A tuple of callbacks.
        """

        return tuple(
            callback
            for key in reversed(sorted(self._callbacks))
            for callback in self._callbacks[key]
        )

    def as_callback(
        self, priority: int = 1, **options
    ) -> Callable[[Union[Callable, Callback]], Callback]:
        """
        A decorator which registers a coroutine as a callback of this event.
        All event's callbacks are invoked when `raise_event` is called.

        :return: `Callback` object.
        """

        def decorator(coroutine: Union[Callable, Callback]) -> Callback:
            return self.create_callback(
                coroutine=coroutine, priority=priority, **options
            )

        return decorator

    def create_callback(
        self, coroutine: Union[Callable, Callback], *, priority: int = 1, **options
    ) -> Callback:
        """
        Creates a callback and add it to this event.

        :param coroutine: The coroutine that will be executed
        :param priority: When the event is raised, callbacks are invoked in priority ascending order.
        :param options: Callback options.

        :return: The created callback.
        """
        callback = Callback(coroutine=coroutine, **options)

        self.add_callback(callback=callback, priority=priority)

        return callback

    def add_callback(self, callback: Callback, *, priority: int = 1):
        """
        Registers a callback to this event.

        :param callback: The callback to register.
        :param priority: When the event is raised, callbacks are invoked in priority ascending order.

        :raise ValueError: If the callback is already registered or if there are multiple callbacks and `multiple_callbacks` is `False`.:
        """
        if not self.multiple_callbacks and self.callbacks:
            raise ValueError(
                f"Cannot add multiple callbacks on event {self.event_name!r}."
            )

        if callback in self.callbacks:
            raise ValueError(f"Callback {callback.__name__!r} is already registered.")

        if self._callbacks.get(priority) is None:
            self._callbacks[priority] = []

        self._callbacks[priority].append(callback)

    def remove_callback(self, callback: Callback):
        """
        Removes a callback from this event.

        :param callback: The callback to remove.

        :raise ValueError: If the callbacks is not registered in this event.:
        """
        new = {
            p: [c_ for c_ in c if c_ != callback] for p, c in self._callbacks.items()
        }

        if new == self._callbacks:
            raise ValueError(f"Callback {callback.__name__!r} is not registered.")

        self._callbacks = new

    async def raise_event(self, *args, **kwargs):
        """
        Calls all registered callbacks. If `handle_errors` is True, `error_handler` event will be raised.
        Parameters passed are : :class: `Exception` the error, :class: `Event` the event where the error occurred,
        *args and **kwargs passed into the initial event.

        :param args: Invocation parameters.
        :param kwargs: Invocation keyword parameters.
        """
        if self._before and self.before.callbacks:
            await self.before.raise_event(*args, **kwargs)

        start_time = time.time()
        for callback in self.callbacks:
            self._tasks.append(
                self._loop.create_task(
                    callback.invoke(
                        *args,
                        **kwargs,
                        _event=self,
                        _handler=self.event_manager.error_handler
                        if self.handle_errors
                        else None,
                    )
                )
            )

        await asyncio.gather(*self._tasks)

        if self._after and self.after.callbacks:
            await self.after.raise_event(time.time() - start_time, *args, **kwargs)

    def cancel(self):
        """
        Cancel all callbacks that run.
        """
        for task in self._tasks:
            task.cancel()

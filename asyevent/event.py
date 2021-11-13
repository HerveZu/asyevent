from __future__ import annotations

import asyncio
import time
import typing

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
        if event_manager.get_event(name, case_sensitive=False):
            raise EventAlreadyExists(event_manager.get_event(name))

        self.event_name = name

        self.handle_errors = handle_errors
        self.event_manager = event_manager
        self.multiple_callbacks = multiple_callbacks

        self.pass_extra_after = False

        self._before = None
        self._after = None

        self._loop = asyncio.get_event_loop()
        self._tasks: typing.List[asyncio.Task] = []
        self._callbacks: typing.Dict[int, typing.List[Callback]] = {}

        self._internal_event = asyncio.Event()

    def __iadd__(self, callback: Callback):
        # default priority, use `.add_callback()` to custom it.
        self.add_callback(callback)

        return self

    def __isub__(self, callback: Callback):
        self.remove_callback(callback)

        return self

    def __await__(self) -> typing.Generator[typing.Any, None, typing.Any]:
        return self._internal_event.wait().__await__()

    async def __call__(self, *args, **kwargs):
        await self.raise_event(*args, **kwargs)

    def before(self, *, handle_errors: bool = True) -> Event:
        """
        Returns an event that is raised before callbacks.
        The current parameters will be passed to the callback.

        :param handle_errors: Are the errors handled into the `event_manager` error handler.
        """
        if self._before is None:
            self._before = self.event_manager.create_event(
                f"<before:{self.event_name}>", handle_errors=handle_errors
            )

        return self._before

    def after(self, *, handle_errors: bool = True, pass_extra: bool = False) -> Event:
        """
        Returns an event that is raised after the callbacks.
        Their execution duration in seconds as
        well as the current parameters, will be passed to the callback.

        :param handle_errors: Are the errors handled into the `event_manager` error handler.
        :param pass_extra: Pass the callbacks execution time if it is set to `True`.

        """
        self.pass_extra_after = pass_extra

        if self._after is None:
            self._after = self.event_manager.create_event(
                f"<after:{self.event_name}>", handle_errors=handle_errors
            )

        return self._after

    @property
    def callbacks(self) -> typing.Tuple[Callback]:
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
        self, *, priority: int = 1, **options
    ) -> typing.Callable[[typing.Union[typing.Callable, Callback]], Callback]:
        """
        A decorator which registers a coroutine as a callback of this event.
        All event's callbacks are invoked when `raise_event` is called.

        :return: `Callback` object.
        """

        def decorator(callback: typing.Union[typing.Callable, Callback]) -> Callback:
            return self.create_callback(callback, priority=priority, **options)

        return decorator

    def create_callback(
        self, callback: typing.Union[typing.Callable, Callback], *, priority: int = 1, **options
    ) -> Callback:
        """
        Creates a callback and add it to this event.

        :param callback: The coroutine that will be executed
        :param priority: When the event is raised, callbacks are invoked in priority ascending order.
        :param options: Callback options.

        :return: The created callback.
        """
        callback = Callback(callback, **options)

        self.add_callback(callback, priority=priority)

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
        if self._before is not None and self._before.callbacks:
            await self._before.raise_event(*args, **kwargs)

        self._internal_event.set()
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

        if self._after is not None and self._after.callbacks:
            # pass extra parameter only if specified
            if self.pass_extra_after:
                args = (time.time() - start_time, *args)

            await self._after.raise_event(*args, **kwargs)

    def cancel(self):
        """
        Cancel all callbacks that run.
        """
        for task in self._tasks:
            task.cancel()

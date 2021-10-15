from __future__ import annotations

import asyncio
import inspect

from typing import Callable, Union, Tuple
from asyevent.utils.parser import parse_parameters


class Callback:
    """
    Callable objet, wrap the coroutine behavior with options and errors handler.
    """

    def __init__(
            self,
            coroutine: Union[Callable, Callback],
            *,
            is_active: bool = True,
            refuse_handling: bool = False,
            continue_on_error: bool = False,
            loop: int = 1,
            loop_delay: float = 0,
            start_delay: float = 0,
    ):
        """
        Initialises a callback with a coroutine and options.

        :param coroutine: The coroutine that will be executed on invoke.
        :param is_active: Is the coroutine active.
        :param refuse_handling: Even if an handler is pass in `.invoke()` method,
            exceptions will be raised if it is set to `True`.

        :param continue_on_error: When a exception occur, if it's handled,
            defines if the loop iterations should continue.

        :param loop: The coroutine will be called `loop` times.
        :param loop_delay: The delay in seconds between every loop iteration.
        :param start_delay: The delay in seconds before the coroutine call.
            It does not impact the event raising process.

        :raise TypeError: If the `coroutine` parameter is not a coroutine.:
        """
        if isinstance(coroutine, Callback):
            # copy old callback's attributes.
            self.__dict__ = coroutine.__dict__

            return

        self._coroutine = coroutine
        self.__name__ = self._coroutine.__name__

        self.is_classmethod = self.signature.parameters.get("self") is not None

        if not inspect.iscoroutinefunction(coroutine):
            raise TypeError(
                f"Callback function {self.__name__!r} must be a _coroutine."
            )

        self.is_running = False
        self.wrapper = None

        self.is_active = is_active
        self.refuse_handling = refuse_handling
        self.continue_on_error = continue_on_error

        self.loop = loop
        self.loop_delay = loop_delay
        self.start_delay = start_delay

    async def __call__(self, *args, _event=None, _handler=None, **kwargs):
        """
        Invokes the coroutine.

        :param _event: If an error is handled, the event will be passed as a parameter.
        :param _handler: If an error occur, the `_handler` event will be raised.
        :param args: Coroutine parameters.
        :param kwargs: Coroutine keyword parameters.

        :raise Exception: If an exception cannot be handle, it will be raised.:
        """
        await self.invoke(*args, **kwargs, _event=_event, _handler=_handler)

    @property
    def signature(self) -> inspect.Signature:
        """
        The coroutine signature.

        :return: The coroutine signature.
        """
        return inspect.signature(self._coroutine)

    async def invoke(self, *args, _event=None, _handler=None, **kwargs):
        """
        Invokes the coroutine.

        :param _event: If an error is handled, the event will be passed as a parameter.
        :param _handler: If an error occur, the `_handler` event will be raised.
        :param args: Coroutine parameters.
        :param kwargs: Coroutine keyword parameters.

        :raise Exception: If an exception cannot be handle, it will be raised.:
        """
        if self.is_active:
            self.is_running = True
            await asyncio.sleep(self.start_delay)

            async def iterate():
                # stop iteration if an error is returned.
                if isinstance(
                    await self._invoke_once(
                        *args,
                        **kwargs,
                        _event=_event,
                        _handler=_handler,
                    ),
                    Exception,
                ):
                    return

            if self.loop <= 0:
                while True:
                    await iterate()

            else:
                for _ in range(self.loop):
                    await iterate()

            self.is_running = False

    async def _invoke_once(
        self, *args, _event=None, _handler=None, **kwargs
    ) -> Exception:
        try:
            parameters = self._parse_arguments(*args, **kwargs)
            await self._coroutine(*parameters[0], **parameters[1])

        except Exception as e:
            if _handler and not self.refuse_handling:
                asyncio.create_task(
                    _handler.raise_event(e, _event, self, *args, **kwargs)
                )

                if not self.continue_on_error:
                    return e

            else:
                raise e

        if self.loop > 1:
            await asyncio.sleep(self.loop_delay)

    def _parse_arguments(self, *args, **kwargs) -> Tuple[tuple, dict]:
        args, kwargs = parse_parameters(self._coroutine, *args, **kwargs)

        if self.is_classmethod:
            if self.wrapper is None:
                raise ValueError(
                    f"Missing wrapper instance on classmethod callback {self.__name__!r}. "
                    f"\n Commune causes are : "
                    f"\n * Missing to to call EventWrapper.init_callbacks()."
                    f"\n * Declaring callback as class callbacks."
                    f"\n * Overriding this callback method."
                ) from None

            args = (self.wrapper,) + tuple(args)

        return args, kwargs

    def enable(self):
        """
        Enables the callback.
        """
        self.is_active = True

    def disable(self):
        """
        Disables the callback.
        """
        self.is_active = False

    def loop(self, *, times: int, delay: float = 0):
        """
        Shortcut for loop settings.

        :param times: How many times the _coroutine iterate on invocation.
        :param delay: Delay between _coroutine iterations.
        """
        self.loop = times
        self.loop_delay = delay

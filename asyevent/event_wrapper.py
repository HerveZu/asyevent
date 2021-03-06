from asyevent.callback import Callback

from typing import List


class EventWrapper:
    """
    !! Implement this class to create callbacks from classmethods !!

    Implements a way to deal with classmethod coroutines.
    """

    def __init__(self):
        self.callbacks: List[Callback] = []

        # initialises callbacks
        self._init_callbacks()

    def _init_callbacks(self):
        """
        Pass to all contained callbacks a `self instance` parameter.
        Use this if a callback has been added after the instance initialisation.

        :raise TypeError: If a registered callback is not a classmethod.
        """

        for attr in dir(self):
            if attr != self._init_callbacks.__name__:  # avoid recursive calls
                if isinstance(getattr(self, attr), Callback):
                    self.callbacks.append(getattr(self, attr))

        for callback in self.callbacks:
            if not callback.is_classmethod:
                raise TypeError("Wrapper's callbacks must be as class callbacks.")

            callback.wrapper = self

    def load(self):
        """
        Enables all callbacks contained in implemented class.
        """
        for callback in self.callbacks:
            callback.enable()

    def unload(self):
        """
        Disables all callbacks contained in implemented class.
        """
        for callback in self.callbacks:
            callback.disable()

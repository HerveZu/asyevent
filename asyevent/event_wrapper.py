from asyevent.callback import Callback

from typing import List


class EventWrapperMixin:
    """
    !! Implement this class to create callbacks from classmethods !!

    Mixin class which implements a way to deal with classmethod callbacks.
    """
    def __init__(self):
        self.callbacks: List[Callback] = []

    def init_callbacks(self):
        """
        !! Use this method to make classmethod callbacks work !!

        Pass to all contained callbacks a `self instance` parameter.

        :raise TypeError: If none classmethod callbacks are registered.
        """

        for attr in dir(self):
            if attr != self.init_callbacks.__name__:  # avoid recursive calls
                if isinstance(getattr(self, attr), Callback):
                    self.callbacks.append(getattr(self, attr))

        for callback in self.callbacks:
            if not callback.is_classmethod:
                raise TypeError('Wrapper\'s callbacks must be declared as class callbacks.')

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

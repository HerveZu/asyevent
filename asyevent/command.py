from __future__ import annotations

from asyevent.callback import Callback
from asyevent.event import Event
from asyevent.exceptions import CommandAlreadyExists

from typing import Callable, Union


class Command(Event):
    """
    Do not manually initialise this class. Use instead `EventManager.create_command()`.

    A `Command` object is not different of a `Event` one.
    Commands are stored separately from events and are created with an initial callback,
    that is making easier an usage of one callback for on event.
    """
    _COMMAND_EVENT_FORMAT = '<command:{}>'

    def __init__(
            self, coroutine: Union[Callable, Callback], *, event_manager, name: str = None,
            handle_errors: bool = True, multiple_callbacks: bool = True, priority: int = 1, **options
    ):
        """
        Initialises a command with an initial coroutine or callback and event parameters.

        :param coroutine: The initial coroutine or callback from what the command is created.
        :param event_manager: An event manager
        :param name: The command name. Must be unique in the event manager.
        :param handle_errors: Do the errors handled into the `event_manager` error handler.
        :param multiple_callbacks: Does the command allow multiple callbacks associated to.
        :param priority: When the command will be raised, the callbacks are invoked int a priority ascending order.
        :param options: The callback options.

        :raise CommandAlreadyExists: If the command name is not unique in the event_manager.
        """
        self.command_name = name or coroutine.__name__

        if event_manager.get_command(self.command_name, case_sensitive=False):
            raise CommandAlreadyExists(event_manager.get_command(self.command_name))

        super().__init__(
            name=self._COMMAND_EVENT_FORMAT.format(self.command_name),
            event_manager=event_manager,
            handle_errors=handle_errors,
            multiple_callbacks=multiple_callbacks
        )

        self._initial_callback = self.create_callback(
            coroutine=coroutine,
            priority=priority,
            **options
        )

    @property
    def initial_callback(self) -> Callback:
        """
        The callback from what the command was created.

        :return: The initial callback.
        """
        return self._initial_callback

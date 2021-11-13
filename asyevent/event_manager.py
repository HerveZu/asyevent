import asyncio

from asyevent.callback import Callback
from asyevent.event import Event
from asyevent.command import Command

from asyevent.exceptions import (
    CommandNotFound,
    EventNotFound,
    CommandAlreadyRegistered,
    EventAlreadyRegistered,
)

from typing import Callable, Optional, Union, List, Tuple


class EventManager:
    """
    The manager stores events and commands, it
    provides an error handler for them.
    """

    def __init__(self):
        """
        Initialises an event manager.
        """
        self._events: List[Event] = []
        self._commands: List[Command] = []

        self.loop = asyncio.get_event_loop()

        # For all events and commands that define `handle_errors` to True, their
        # exceptions are handled in this event.
        # Passed parameters are : the exception, the event, the callback, args, **kwargs.
        self.error_handler = self.create_event("<error_handler>", handle_errors=False)

    @property
    def events(self) -> Tuple[Event]:
        """
        Returns all registered events.

        :return: A tuple of events.
        """
        return tuple(self._events)

    @property
    def commands(self) -> Tuple[Command]:
        """
        Returns all registered commands.

        :return: A tuple of commands.
        """
        return tuple(self._commands)

    def as_command(
        self,
        *,
        name: str = None,
        handle_errors: bool = True,
        multiple_callbacks: bool = True,
        priority: int = 1,
        **options
    ) -> Callable[[Union[Callable, Callback]], Callback]:
        """
        A decorator which registers a coroutine as a callback of this command.

        :param priority: When an event is raised, associated callbacks will be invoked by ascending priority order.
        :param name: The command name. Coroutine's name by default.
        :param handle_errors: Determines if exceptions are handle into the error handler event.
        :param multiple_callbacks: Does the command allow multiple callbacks.

        :return: A callback.
        """

        def decorator(callback: Union[Callable, Callback]) -> Callback:
            command = self.create_command(
                callback,
                name=name,
                handle_errors=handle_errors,
                multiple_callbacks=multiple_callbacks,
                priority=priority,
                **options
            )

            return command.initial_callback

        return decorator

    def create_command(
        self,
        callback: Union[Callable, Callback],
        *,
        name: str = None,
        handle_errors: bool = True,
        multiple_callbacks: bool = True,
        priority: int = 1,
        **options
    ) -> Command:
        """
        Registers a coroutine as a `command` event.
        The purpose of using this instead of `Event.as_callback` is dynamic event names.

        :param multiple_callbacks: Does the command allow multiple callbacks associated to.
        :param callback: Coroutine which will be called when the command event is raised.
        :param name: The command name. Coroutine name by default.
        :param handle_errors: Determines if exceptions are handle into the error handler event.
        :param priority: When an event is raised, associated callbacks will be invoked by ascending priority order.
        :param options: Callback options

        :return: A command.
        """
        command = Command(
            callback,
            event_manager=self,
            name=name,
            handle_errors=handle_errors,
            multiple_callbacks=multiple_callbacks,
            priority=priority,
            **options
        )
        self._commands.append(command)

        return command

    def create_event(
        self, name: str, *, handle_errors: bool = True, multiple_callbacks: bool = True
    ) -> Event:
        """
        Creates an event associated to the manager.

        :param multiple_callbacks: Does the command allow multiple callbacks associated to.
        :param name: The event name.
        :param handle_errors: Determines if exceptions are handle into the error handler event.

        :return: The event.
        """
        event = Event(
            name=name,
            event_manager=self,
            handle_errors=handle_errors,
            multiple_callbacks=multiple_callbacks,
        )
        self._events.append(event)

        return event

    def get_command(
        self, name: str, *, case_sensitive: bool = True
    ) -> Optional[Command]:
        """
        Get a command by its name. The command must be associate to this manager.

        :param name: The command name.
        :param case_sensitive: Is case sensitive.

        :return: A command if found.
        """

        def checker(cmd: Command) -> bool:
            if case_sensitive:
                return cmd.command_name == name

            return cmd.command_name.casefold() == name.casefold()

        return next(filter(checker, self._commands), None)

    def get_event(self, name: str, *, case_sensitive: bool = True) -> Optional[Event]:
        """
        Get an event by its name. The event must be associate to this manager.

        :param name: The event name.
        :param case_sensitive: Is case sensitive.

        :return: An event if found.
        """

        def checker(event: Event) -> bool:
            if case_sensitive:
                return event.event_name == name

            return event.event_name.casefold() == name.casefold()

        return next(filter(checker, self._events), None)

    def replace_command_name(self, name: str, *, new_name: str):
        """
        Replace a command name.

        :param name: The name of the command to replace.
        :param new_name: The new name.

        :raise: CommandNotFound: If no command was found.
        """
        command = self.get_command(name)

        if command is None:
            raise CommandNotFound(name=name)

        command.command_name = new_name

    def add_event(self, event: Event):
        """
        Add an event to this event manager, and remove it from the previous one.

        :param event: The event to add.

        :raise: EventAlreadyRegistered: If the event is already registered.
        """
        if event in self._events:
            raise EventAlreadyRegistered(event=event)

        event.event_manager.remove_event(event)
        self._events.append(event)
        event.event_manager = self

    def remove_event(self, event: Event):
        """
        Remove an event from this event manager.

        :param event: The event to remove.
        """
        self._events.remove(event)
        event.event_manager = None

    def remove_event_by_name(self, name: str):
        """
        Remove an event by its name from this event manager.

        :param name: The name of the event to remove.

        :raise: EventNotFound: If no event was found.
        """
        event = self.get_event(name)

        if event is None:
            raise EventNotFound(name=name)

        self.remove_event(event)

    def add_command(self, command: Command):
        """
        Add a command to this event manager, and remove it from the previous one.

        :param command: The command to add.

        :raise: CommandAlreadyRegistered: If the command is already registered.
        """
        if command in self._commands:
            raise CommandAlreadyRegistered(command=command)

        command.event_manager.remove_command(command)
        self._commands.append(command)
        command.event_manager = self

    def remove_command(self, command: Command):
        """
        Remove a command from this event manager.

        :param command: The command to remove.
        """
        self._commands.remove(command)
        command.event_manager = None

    def remove_command_by_name(self, name: str):
        """
        Remove a command by its name from this event manager.

        :param name: The name of the command to remove.

        :raise: CommandNotFound: If no command was found.
        """
        command = self.get_command(name)

        if command is None:
            raise CommandNotFound(name=name)

        self.remove_command(command)

    async def invoke_command(
        self, name: str, *args, _case_sensitive: bool = True, **kwargs
    ):
        """
        Invokes a command by its name.

        :param name: The command name.
        :param args: The command parameters.
        :param _case_sensitive: Is event research case sensitive.
        :param kwargs: The command keyword parameters.

        :raise CommandNotFound: If no command was found.:
        """
        command = self.get_command(name, case_sensitive=_case_sensitive)

        if command is None:
            raise CommandNotFound(name)

        await command.raise_event(*args, **kwargs)

    async def raise_event(
        self, name: str, *args, _case_sensitive: bool = True, **kwargs
    ):
        """
        Raises an event by its name.

        :param name: The event name.
        :param _case_sensitive: Is event research case sensitive.
        :param args: The event parameters.
        :param kwargs: The event keyword parameters.

        :raise EventNotFound: If no event was found.:
        """
        event = self.get_event(name, case_sensitive=_case_sensitive)

        if event is None:
            raise EventNotFound(name)

        await event.raise_event(*args, **kwargs)

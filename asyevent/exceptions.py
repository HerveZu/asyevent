"""
All specific package's exceptions.
Cannot type hint custom classes due to circular import.
"""

from typing import Any


class AsyeventException(Exception):
    """
    Base exception.
    """
    pass


class EventException(AsyeventException):
    """
    Base event exception.
    """
    def __init__(self, message: str, event=None):
        self.event = event
        super().__init__(message)


class CommandException(AsyeventException):
    """
    Base command exception.
    """
    def __init__(self, message: str, command=None):
        self.command = command
        super().__init__(message)


class EventNotFound(EventException):
    """
    Raised when a unknown event is invoked.
    """
    def __init__(self, name: str):
        self.name = name
        super().__init__(f'Event {self.name!r} cannot be found.')


class EventAlreadyExists(EventException):
    """
    Raised when an event that is already defined by its event_name is created.
    """
    def __init__(self, event):
        super().__init__(f'Event {event.event_name!r} already exists.', event)


class EventAlreadyRegistered(EventException):
    """
    Raised when an event is add to en event_manager that already contains the event.
    """
    def __init__(self, event):
        super().__init__(f'Event {event.event_name!r} is already registered.', event)


class CommandNotFound(CommandException):
    """
    Raised when a unknown command is invoked.
    """
    def __init__(self, name: str):
        self.name = name
        super().__init__(f'Command {self.name!r} cannot be found.')


class CommandAlreadyExists(CommandException):
    """
    Raised when an event that is already defined by its event_name is created.
    """
    def __init__(self, command):
        super().__init__(f'Command {command.command_name!r} already exists.', command)


class CommandAlreadyRegistered(CommandException):
    """
    Raised when a command is add to en event_manager that already contains the command.
    """
    def __init__(self, command):
        super().__init__(f'Command {command.command_name!r} is already registered.', command)


class ParsingFailed(AsyeventException):
    """
    Raised on function parameters parsing failed.
    """
    def __init__(self, value: Any, excepted_type: type):
        self.value = value
        self.excepted_type = excepted_type
        super().__init__(f'Parameter {value!r} of type {type(value)} cannot be parsed into {excepted_type}.')

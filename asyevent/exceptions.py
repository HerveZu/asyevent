"""
All specific package's exceptions raised.
"""


class EventSystemException(Exception):
    """
    Base exception.
    """
    pass


class EventException(EventSystemException):
    """
    Base event exception.
    """
    def __init__(self, message: str, event=None):
        self.event = event
        super().__init__(message)


class CommandException(EventSystemException):
    """
    Base command exception.
    """
    def __init__(self, message: str, command=None):
        self.command = command
        super().__init__(message)


class EventNotFound(EventException):
    """
    Raise when a unknown event is invoked.
    """
    def __init__(self, name: str):
        self.name = name
        super().__init__(f'Event {self.name!r} cannot be found.')


class EventAlreadyExists(EventException):
    """
    Raise when an event that is already defined by its event_name is created.
    """
    def __init__(self, event):
        super().__init__(f'Event {event.event_name!r} already exists.', event)


class EventAlreadyRegistered(EventException):
    """
    Raise when an event is add to en event_manager that already contains the event.
    """
    def __init__(self, event):
        super().__init__(f'Event {event.event_name!r} is already registered.', event)


class CommandNotFound(CommandException):
    """
    Raise when a unknown command is invoked.
    """
    def __init__(self, name: str):
        self.name = name
        super().__init__(f'Command {self.name!r} cannot be found.')


class CommandAlreadyExists(CommandException):
    """
    Raise when an event that is already defined by its event_name is created.
    """
    def __init__(self, command):
        super().__init__(f'Command {command.command_name!r} already exists.', command)


class CommandAlreadyRegistered(CommandException):
    """
    Raise when a command is add to en event_manager that already contains the command.
    """
    def __init__(self, command):
        super().__init__(f'Command {command.command_name!r} is already registered.', command)

from __future__ import annotations

import typing

from inspect import signature

from abc import abstractmethod

from asyevent.exceptions import ParsingError, ParsingNotImplemented

# the list of builtins types that can be use for parsing values
__parsable_builtins__ = {str, int, float, dict, list, tuple, set, frozenset}


@typing.runtime_checkable
class _IParsable(typing.Protocol):
    """
    Parser protocol that provides a parser method call when passing parameters to callbacks.
    """

    @classmethod
    @abstractmethod
    def __parse__(cls, value: typing.Any) -> _IParsable:
        """
        Parsing method to override.
        Raise `asyevent.exceptions.ParsingError` for parsing errors.

        Type hinting forces a match before parsing.
        Otherwise, `ParsingError` is raised.
        """
        pass


def _parse_parameter(cls: type, value: typing.Any) -> typing.Any:
    if typing.get_origin(cls) is typing.Union:
        cls = typing.get_args(cls)[0]

    if cls is typing.Any or cls is None or isinstance(value, cls):
        return value

    if cls in __parsable_builtins__:
        try:
            return cls(value)

        except ValueError:
            raise ParsingError(value=value, excepted_type=cls)

    elif issubclass(cls, _IParsable):
        params = [p.annotation for p in signature(cls.__parse__).parameters.values()]

        # checks if the values passed matches the parsing method
        if type(params[0]) is not type(value):
            raise ParsingError(value=value, excepted_type=cls)

        return cls.__parse__(value)

    raise ParsingNotImplemented(value=value, excepted_type=cls)


def parse_parameters(f: typing.Callable, *args, **kwargs) -> typing.Tuple[tuple, dict]:
    """
    Parse parameters to match with the signature.
    Parsing to `typing.Union` will try to parse into the first possibility.

    :raise `ParsingError`: If a parameter cannot be parsed while it is type hinted.
    :return:
    """
    types = {k: typing.Any for k in dict(signature(f).parameters).keys()}
    types.pop("self", None)

    # merging signatures names and hint types
    hints: dict[str, typing.Any] = types | typing.get_type_hints(f)

    kwargs = {k: _parse_parameter(hints.get(k), v) for k, v in kwargs.items()}

    delta = max(0, len(args) - len(hints.values()))
    final_hints = list(hints.values()) + [typing.Any] * delta

    args = tuple(_parse_parameter(final_hints[i], arg) for i, arg in enumerate(args))

    return args, kwargs

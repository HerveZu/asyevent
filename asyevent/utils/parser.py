from __future__ import annotations

from typing import Any, Tuple, Callable, Protocol, get_type_hints, runtime_checkable
from inspect import signature

from abc import abstractmethod

from asyevent.exceptions import ParsingError, ParsingNotImplemented

# the list of builtins types that can be use for parsing values
__builtin_parsable__ = {str, int, float, dict, list, tuple, set, frozenset}


@runtime_checkable
class _IParsable(Protocol):
    """
    Parser protocol that provides a parser method call when passing parameters to callbacks.
    """

    @classmethod
    @abstractmethod
    def __parse__(cls, value: Any) -> _IParsable:
        """
        Parsing method to override.
        Raise `asyevent.exceptions.ParsingError` for parsing errors.

        Type hinting forces a match before parsing.
        Otherwise, `ParsingError` is raised.
        """
        pass


def _parse_parameter(cls: type, value: Any) -> Any:
    if cls is Any or cls is None or isinstance(value, cls):
        return value

    if cls in __builtin_parsable__:
        try:
            return cls(value)

        except ValueError:
            raise ParsingError(value=value, excepted_type=cls) from None

    elif issubclass(cls, _IParsable):
        params = [
            p.annotation for p in signature(cls.__parse__).parameters.values()
        ]

        # checks if the values passed matches the parsing method
        if type(params[0]) is not type(value):
            raise ParsingError(value=value, excepted_type=cls) from None

        return cls.__parse__(value)

    raise ParsingNotImplemented(value=value, excepted_type=cls) from None


def parse_parameters(f: Callable, *args, **kwargs) -> Tuple[tuple, dict]:
    """
    Parse parameters to match with the signature.

    :raise `ParsingError`: If a parameter cannot be parsed while it is type hinted.
    :return:
    """
    types = {k: Any for k in dict(signature(f).parameters).keys()}
    types.pop("self", None)

    # merging signatures names and hint types
    hints: dict[str, Any] = types | get_type_hints(f)

    kwargs = {k: _parse_parameter(hints.get(k), v) for k, v in kwargs.items()}

    delta = max(0, len(args) - len(hints.values()))
    final_hints = list(hints.values()) + [Any] * delta

    args = tuple(
        _parse_parameter(final_hints[i], arg) for i, arg in enumerate(args)
    )

    return args, kwargs

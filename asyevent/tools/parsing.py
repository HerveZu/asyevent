from __future__ import annotations

from typing import Any, Tuple, get_type_hints, Callable
from inspect import signature

from abc import ABCMeta, abstractmethod

from asyevent.exceptions import ParsingFailed
from warnings import warn


# the list of builtins types that can be use for parsing values
__builtin_parsable__ = (
    str,
    int,
    float,
    dict,
    list,
    tuple,
    set,
    frozenset
)


class IParsable(metaclass=ABCMeta):
    """
    Implement this interface allows the class, by overriding `__parse__()`,
    to provide a parser method used when passing parameters to callbacks.
    """

    @classmethod
    @abstractmethod
    def __parse__(cls, x: Any) -> IParsable:
        """
        Parsing method.
        Raise `asyevent.exceptions.ParsingFailed` for parsing errors.
        """
        pass


def _parse_arg(cls: type, value: Any) -> Any:
    if cls is not None:
        if isinstance(value, cls):
            return value

        if cls in __builtin_parsable__:
            try:
                return cls(value)

            except ValueError:
                raise ParsingFailed(
                    value=value,
                    excepted_type=cls
                ) from None

        elif issubclass(cls, IParsable):
            return cls.__parse__(value)

        warn(Warning(f'Parameter {value!r} is not of type {cls}, but {cls} is not parsable.'))

    return value


def parse(f: Callable, *args, **kwargs) -> Tuple[tuple, dict]:
    types = dict(signature(f).parameters)
    types = {k: None for k in types.keys()}

    if 'self' in types.keys():
        del types['self']

    # merging signatures names and hint types
    types_hint: dict[str, Any] = types | get_type_hints(f)

    kwargs = {k: _parse_arg(types_hint.get(k), v) for k, v in kwargs.items()}
    args = tuple(
        _parse_arg(
            list(types_hint.values())[i],
            arg
        ) for i, arg in enumerate(args)
    )

    return args, kwargs

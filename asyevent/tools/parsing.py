from __future__ import annotations

from typing import Any, Tuple, get_type_hints, Callable
from inspect import signature

from abc import ABCMeta, abstractmethod

from asyevent.exceptions import ParsingError, ParsingNotImplemented

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
    def __parse__(cls, value: Any) -> IParsable:
        """
        Parsing method.
        Raise `asyevent.exceptions.ParsingError` for parsing errors.

        Type hinting forces a match before parsing.
        In other case, `ParsingError` is raised.


        """
        pass


def _parse_parameter(cls: type, value: Any) -> Any:
    if cls is not Any:
        if isinstance(value, cls):
            return value

        if cls in __builtin_parsable__:
            try:
                return cls(value)

            except ValueError:
                raise ParsingError(
                    value=value,
                    excepted_type=cls
                ) from None

        elif issubclass(cls, IParsable):
            params = [p.annotation for p in signature(cls.__parse__).parameters.values()]

            # checks if the values passed matches the parsing method
            if type(params[0]) is not type(value):
                raise ParsingError(
                    value=value,
                    excepted_type=cls
                ) from None

            return cls.__parse__(value)

        raise ParsingNotImplemented(
            value=value,
            excepted_type=cls
        ) from None

    return value


def parse_parameters(f: Callable, *args, **kwargs) -> Tuple[tuple, dict]:
    """
    Parse parameters to match with the signature.

    :raise `ParsingError`: If a parameter cannot be parsed while it is type hinted.
    """
    types = dict(signature(f).parameters)
    types = {k: Any for k in types.keys()}

    if 'self' in types.keys():
        del types['self']

    # merging signatures names and hint types
    types_hint: dict[str, Any] = types | get_type_hints(f)

    kwargs = {k: _parse_parameter(types_hint.get(k), v) for k, v in kwargs.items()}
    args = tuple(
        _parse_parameter(
            list(types_hint.values())[i],
            arg
        ) for i, arg in enumerate(args)
    )

    return args, kwargs

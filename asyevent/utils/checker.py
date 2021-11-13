import typing


def checker(lamb: typing.Callable[..., bool], *, error: Exception):
    def wrapper(*args, **kwargs) -> bool:
        if lamb(*args, **kwargs):
            return True

        raise error

    return wrapper

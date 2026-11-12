"""Exceptions raised by the Stateskol data contract."""


class StateskolError(Exception):
    """Base class for every error Stateskol raises on purpose."""


class EmptyDataError(StateskolError, ValueError):
    """No present values remain, so the summary is undefined."""


class InvalidTypeError(StateskolError, TypeError):
    """An input is not an int or float (bool, str, Decimal, ... are rejected)."""


class InvalidValueError(StateskolError, ValueError):
    """An input has an accepted type but an unacceptable value (inf, abs(n) > 2**53)."""


class MissingDataError(StateskolError, ValueError):
    """A missing value was found while policy="strict"."""
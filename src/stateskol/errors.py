"""The exceptions the data contract raises.

Every exception in this module is part of the published contract, so a caller
can catch it without importing anything else from stateskol. Nothing here
imports from the package; the module must stay importable on its own.

Error taxonomy
--------------
ContractError
    Subclass of TypeError. Raised when a value is not a measurement the
    contract understands, or when a missing value is seen under
    policy="strict". A caller who only catches TypeError still catches it.
EmptyDataError
    Raised when a summary needs present values and none survive the policy.
    Not a TypeError: the input was legal, the sample was empty.
UnknownPolicyError
    Subclass of ValueError. Raised when the policy argument is not one of the
    documented strings. This is a programming error, not a statement about
    the data.
"""


class ContractError(TypeError):
    """A value is not a measurement, or a missing value broke policy="strict".

    Attributes:
        index: position of the offending value in the input, or None.
        value: the offending value itself.
    """

    def __init__(self, message, index=None, value=None):
        super().__init__(message)
        self.index = index
        self.value = value


class EmptyDataError(Exception):
    """No present values remained, so the summary is undefined."""


class UnknownPolicyError(ValueError):
    """The policy argument was not one the contract documents."""

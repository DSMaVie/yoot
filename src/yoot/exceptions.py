class YootException(Exception):
    """Base class for all exceptions raised by Yoot."""


class TaskDefinitionError(YootException):
    """Raised when a task definition is invalid."""

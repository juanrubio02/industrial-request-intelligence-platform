from app.application.common.exceptions import ResourceConflictError, ResourceNotFoundError


class UserEmailAlreadyExistsError(ResourceConflictError):
    """Raised when a user email is already in use."""


class UserNotFoundError(ResourceNotFoundError):
    """Raised when a user cannot be found."""


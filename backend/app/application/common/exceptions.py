class ApplicationError(Exception):
    """Base application exception."""


class ValidationError(ApplicationError):
    """Raised when the input is invalid for an application use case."""


class ResourceConflictError(ApplicationError):
    """Raised when a resource cannot be created due to a uniqueness conflict."""


class ResourceNotFoundError(ApplicationError):
    """Raised when a requested resource does not exist."""


class AuthenticationError(ApplicationError):
    """Raised when authentication fails."""


class AuthorizationError(ApplicationError):
    """Raised when the authenticated actor is not allowed to access a resource."""

from app.application.common.exceptions import ResourceConflictError, ResourceNotFoundError


class OrganizationSlugAlreadyExistsError(ResourceConflictError):
    """Raised when an organization slug is already in use."""


class OrganizationNotFoundError(ResourceNotFoundError):
    """Raised when an organization cannot be found."""


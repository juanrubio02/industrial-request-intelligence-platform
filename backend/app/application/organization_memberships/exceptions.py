from app.application.common.exceptions import ResourceConflictError, ResourceNotFoundError


class OrganizationMembershipAlreadyExistsError(ResourceConflictError):
    """Raised when an active membership already exists for a user in an organization."""


class OrganizationMembershipNotFoundError(ResourceNotFoundError):
    """Raised when an organization membership cannot be found."""


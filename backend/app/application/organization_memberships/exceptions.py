from app.application.common.exceptions import (
    AuthorizationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)


class OrganizationMembershipAlreadyExistsError(ResourceConflictError):
    """Raised when an active membership already exists for a user in an organization."""


class OrganizationMembershipNotFoundError(ResourceNotFoundError):
    """Raised when an organization membership cannot be found."""


class OrganizationMembershipRoleUpdateNotAllowedError(AuthorizationError):
    """Raised when the actor cannot assign the requested membership role."""


class OrganizationMembershipStatusUpdateNotAllowedError(AuthorizationError):
    """Raised when the actor cannot update the requested membership status."""


class LastOrganizationOwnerChangeError(ValidationError):
    """Raised when the last active organization owner would be removed or disabled."""

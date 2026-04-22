from app.application.common.exceptions import ResourceConflictError, ResourceNotFoundError


class RequestNotFoundError(ResourceNotFoundError):
    """Raised when a request cannot be found."""


class RequestCustomerNotFoundError(ResourceNotFoundError):
    """Raised when a customer cannot be found for the active organization."""


class RequestMembershipOrganizationMismatchError(ResourceConflictError):
    """Raised when a membership does not belong to the provided organization."""


class RequestOrganizationMismatchError(ResourceConflictError):
    """Raised when a request does not belong to the provided organization."""


class InvalidRequestStatusTransitionError(ResourceConflictError):
    """Raised when a request status transition is not allowed."""


class RequestAssignedMembershipOrganizationMismatchError(ResourceConflictError):
    """Raised when an assigned membership does not belong to the request organization."""

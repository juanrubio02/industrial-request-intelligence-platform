from app.application.common.exceptions import AuthenticationError, AuthorizationError


class InvalidCredentialsError(AuthenticationError):
    """Raised when the provided credentials are invalid."""


class InvalidAccessTokenError(AuthenticationError):
    """Raised when the provided access token is invalid."""


class InvalidMembershipContextError(AuthorizationError):
    """Raised when the provided membership context is invalid for the authenticated user."""


class MembershipPermissionDeniedError(AuthorizationError):
    """Raised when the current membership role does not have permission for an action."""

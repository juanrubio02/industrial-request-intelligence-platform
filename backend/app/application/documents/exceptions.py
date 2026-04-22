from app.application.common.exceptions import (
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)


class DocumentNotFoundError(ResourceNotFoundError):
    """Raised when a document cannot be found."""


class DocumentStorageKeyAlreadyExistsError(ResourceConflictError):
    """Raised when a document storage key already exists."""


class DocumentRequestOrganizationMismatchError(ResourceConflictError):
    """Raised when a request does not belong to the provided organization."""


class DocumentOrganizationMismatchError(ResourceConflictError):
    """Raised when a document does not belong to the provided organization."""


class DocumentMembershipOrganizationMismatchError(ResourceConflictError):
    """Raised when a membership does not belong to the provided organization."""


class DocumentUploadInvalidFileError(ValidationError):
    """Raised when the uploaded file is invalid."""


class DocumentStoragePathError(ValidationError):
    """Raised when a storage path is invalid or escapes the base directory."""


class InvalidDocumentProcessingStatusTransitionError(ResourceConflictError):
    """Raised when a document processing status transition is not allowed."""

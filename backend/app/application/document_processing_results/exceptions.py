from app.application.common.exceptions import ResourceNotFoundError


class DocumentProcessingResultNotFoundError(ResourceNotFoundError):
    """Raised when a document processing result cannot be found."""

from app.domain.documents.statuses import DocumentProcessingStatus

ALLOWED_DOCUMENT_PROCESSING_STATUS_TRANSITIONS: dict[
    DocumentProcessingStatus,
    frozenset[DocumentProcessingStatus],
] = {
    DocumentProcessingStatus.PENDING: frozenset({DocumentProcessingStatus.PROCESSING}),
    DocumentProcessingStatus.PROCESSING: frozenset(
        {
            DocumentProcessingStatus.PROCESSED,
            DocumentProcessingStatus.FAILED,
        }
    ),
    DocumentProcessingStatus.PROCESSED: frozenset(),
    DocumentProcessingStatus.FAILED: frozenset({DocumentProcessingStatus.PENDING}),
}


def is_valid_document_processing_status_transition(
    current_status: DocumentProcessingStatus,
    new_status: DocumentProcessingStatus,
) -> bool:
    return new_status in ALLOWED_DOCUMENT_PROCESSING_STATUS_TRANSITIONS[current_status]

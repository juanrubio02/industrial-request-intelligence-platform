from pathlib import PurePath

from app.application.documents.processing import DocumentProcessingOutput
from app.application.documents.processing import DocumentProcessor
from app.application.documents.storage import DocumentStorage
from app.domain.documents.entities import Document
from app.infrastructure.document_processing.classifier import (
    RuleBasedDocumentTypeClassifier,
)
from app.infrastructure.document_processing.ocr import PdfOcrExtractor
from app.infrastructure.document_processing.ocr import RapidOcrPdfExtractor
from app.infrastructure.document_processing.pdf import EmbeddedTextPdfExtractor
from app.infrastructure.document_processing.pdf import PdfEmbeddedTextNotFoundError
from app.infrastructure.document_processing.structured_data import (
    RuleBasedStructuredDataExtractor,
)
from app.infrastructure.document_processing.summarizer import (
    HeuristicDocumentSummarizer,
)


class StorageBackedDocumentProcessor(DocumentProcessor):
    _SUPPORTED_CONTENT_TYPES: dict[str, str] = {
        "text/plain": "PLAIN_TEXT",
        "text/markdown": "MARKDOWN",
        "application/pdf": "PDF",
    }
    _SUPPORTED_SUFFIXES: dict[str, str] = {
        ".txt": "PLAIN_TEXT",
        ".md": "MARKDOWN",
        ".pdf": "PDF",
    }

    def __init__(
        self,
        document_storage: DocumentStorage,
        pdf_extractor: EmbeddedTextPdfExtractor | None = None,
        pdf_ocr_extractor: PdfOcrExtractor | None = None,
        document_type_classifier: RuleBasedDocumentTypeClassifier | None = None,
        document_summarizer: HeuristicDocumentSummarizer | None = None,
        structured_data_extractor: RuleBasedStructuredDataExtractor | None = None,
    ) -> None:
        self._document_storage = document_storage
        self._pdf_extractor = pdf_extractor or EmbeddedTextPdfExtractor()
        self._pdf_ocr_extractor = pdf_ocr_extractor or RapidOcrPdfExtractor()
        self._document_type_classifier = (
            document_type_classifier or RuleBasedDocumentTypeClassifier()
        )
        self._document_summarizer = document_summarizer or HeuristicDocumentSummarizer()
        self._structured_data_extractor = (
            structured_data_extractor or RuleBasedStructuredDataExtractor()
        )

    async def process(self, document: Document) -> DocumentProcessingOutput:
        document_type = self._resolve_supported_type(document)
        file_bytes = await self._document_storage.read(storage_key=document.storage_key)
        extraction_strategy = "DIRECT"
        ocr_used = False

        if document_type == "PDF":
            extracted_text, extraction_strategy, ocr_used = self._extract_pdf_text(file_bytes)
        else:
            try:
                extracted_text = file_bytes.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise RuntimeError("Document content is not valid UTF-8 text.") from exc

        detected_document_type = self._document_type_classifier.classify(
            original_filename=document.original_filename,
            content_type=document.content_type,
            extracted_text=extracted_text,
        )

        return DocumentProcessingOutput(
            extracted_text=extracted_text,
            summary=self._document_summarizer.summarize(extracted_text),
            detected_document_type=detected_document_type,
            structured_data={
                "detected_format": document_type,
                "content_type": document.content_type,
                "original_filename": document.original_filename,
                "text_extraction_strategy": extraction_strategy,
                "ocr_used": ocr_used,
                "extracted_fields": self._structured_data_extractor.extract(
                    extracted_text=extracted_text,
                    detected_document_type=detected_document_type,
                ),
            },
        )

    def _extract_pdf_text(self, file_bytes: bytes) -> tuple[str, str, bool]:
        try:
            return self._pdf_extractor.extract_text(file_bytes), "EMBEDDED_TEXT", False
        except PdfEmbeddedTextNotFoundError:
            return self._pdf_ocr_extractor.extract_text(file_bytes), "OCR", True

    def _resolve_supported_type(self, document: Document) -> str:
        if document.content_type in self._SUPPORTED_CONTENT_TYPES:
            return self._SUPPORTED_CONTENT_TYPES[document.content_type]

        suffix = PurePath(document.original_filename).suffix.lower()
        if suffix in self._SUPPORTED_SUFFIXES:
            return self._SUPPORTED_SUFFIXES[suffix]

        raise RuntimeError(
            "Unsupported document format. Supported formats: text/plain (.txt), "
            "text/markdown (.md), application/pdf (.pdf)."
        )

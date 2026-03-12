from io import BytesIO

from pypdf import PdfReader


class PdfProcessingError(RuntimeError):
    """Base error for PDF text extraction."""


class PdfReadError(PdfProcessingError):
    """Raised when a PDF file cannot be opened."""


class PdfTextExtractionError(PdfProcessingError):
    """Raised when embedded PDF text cannot be extracted."""


class PdfEmbeddedTextNotFoundError(PdfProcessingError):
    """Raised when a PDF does not contain useful embedded text."""


class EmbeddedTextPdfExtractor:
    def extract_text(self, file_bytes: bytes) -> str:
        try:
            reader = PdfReader(BytesIO(file_bytes))
        except Exception as exc:
            raise PdfReadError("PDF file could not be read.") from exc

        extracted_pages: list[str] = []

        try:
            for page in reader.pages:
                page_text = (page.extract_text() or "").strip()
                if page_text:
                    extracted_pages.append(page_text)
        except Exception as exc:
            raise PdfTextExtractionError("PDF text could not be extracted.") from exc

        extracted_text = "\n\n".join(extracted_pages).strip()
        if not extracted_text:
            raise PdfEmbeddedTextNotFoundError(
                "PDF does not contain extractable embedded text."
            )

        return extracted_text

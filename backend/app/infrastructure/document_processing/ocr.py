from abc import ABC, abstractmethod

import fitz
from rapidocr_onnxruntime import RapidOCR


class PdfOcrExtractor(ABC):
    @abstractmethod
    def extract_text(self, file_bytes: bytes) -> str:
        raise NotImplementedError


class RapidOcrPdfExtractor(PdfOcrExtractor):
    def __init__(
        self,
        *,
        ocr_engine: RapidOCR | None = None,
        render_scale: float = 2.0,
    ) -> None:
        self._ocr_engine = ocr_engine or RapidOCR()
        self._render_scale = render_scale

    def extract_text(self, file_bytes: bytes) -> str:
        try:
            document = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as exc:
            raise RuntimeError("PDF file could not be rasterized for OCR.") from exc

        extracted_pages: list[str] = []

        try:
            for page in document:
                pixmap = page.get_pixmap(
                    matrix=fitz.Matrix(self._render_scale, self._render_scale),
                    alpha=False,
                )
                page_png = pixmap.tobytes("png")
                page_text = self._extract_page_text(page_png)
                if page_text:
                    extracted_pages.append(page_text)
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError("OCR processing failed for the PDF.") from exc
        finally:
            document.close()

        extracted_text = "\n\n".join(extracted_pages).strip()
        if not extracted_text:
            raise RuntimeError("OCR could not extract useful text from the PDF.")

        return extracted_text

    def _extract_page_text(self, page_png: bytes) -> str:
        try:
            result, _ = self._ocr_engine(page_png)
        except Exception as exc:
            raise RuntimeError("OCR processing failed for the PDF.") from exc

        if not result:
            return ""

        lines = [
            str(item[1]).strip()
            for item in result
            if isinstance(item, (list, tuple)) and len(item) >= 2 and str(item[1]).strip()
        ]
        return "\n".join(lines).strip()

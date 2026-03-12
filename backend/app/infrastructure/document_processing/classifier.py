import re
from pathlib import PurePath

from app.domain.document_processing_results.document_types import (
    DocumentDetectedType,
)


class RuleBasedDocumentTypeClassifier:
    def classify(
        self,
        *,
        original_filename: str,
        content_type: str,
        extracted_text: str,
    ) -> DocumentDetectedType:
        filename = original_filename.lower()
        suffix = PurePath(original_filename).suffix.lower()
        normalized_text = self._normalize(extracted_text)

        if self._matches_drawing(filename=filename, suffix=suffix, text=normalized_text):
            return DocumentDetectedType.DRAWING

        if self._matches_purchase_order(filename=filename, text=normalized_text):
            return DocumentDetectedType.PURCHASE_ORDER

        if self._matches_quote_request(filename=filename, text=normalized_text):
            return DocumentDetectedType.QUOTE_REQUEST

        if self._matches_technical_spec(
            filename=filename,
            content_type=content_type.lower(),
            text=normalized_text,
        ):
            return DocumentDetectedType.TECHNICAL_SPEC

        return DocumentDetectedType.OTHER

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip().lower()

    @staticmethod
    def _matches_quote_request(*, filename: str, text: str) -> bool:
        filename_signals = ("rfq", "quote_request", "request_for_quote", "quote-request")
        text_signals = (
            "request for quotation",
            "request for quote",
            "quote request",
            "rfq",
        )
        return any(signal in filename for signal in filename_signals) or any(
            signal in text for signal in text_signals
        )

    @staticmethod
    def _matches_technical_spec(*, filename: str, content_type: str, text: str) -> bool:
        filename_signals = ("spec", "specification", "datasheet", "technical")
        text_signals = (
            "technical specification",
            "specification",
            "datasheet",
            "operating conditions",
            "material grade",
        )
        return any(signal in filename for signal in filename_signals) or any(
            signal in text for signal in text_signals
        )

    @staticmethod
    def _matches_purchase_order(*, filename: str, text: str) -> bool:
        filename_signals = ("purchase_order", "po_", "po-", "purchase-order")
        text_signals = (
            "purchase order",
            "po number",
            "buyer",
            "ship to",
        )
        return any(signal in filename for signal in filename_signals) or any(
            signal in text for signal in text_signals
        )

    @staticmethod
    def _matches_drawing(*, filename: str, suffix: str, text: str) -> bool:
        if suffix in {".dwg", ".dxf"}:
            return True

        filename_signals = ("drawing", "blueprint", "layout", "plan")
        text_signals = (
            "general arrangement drawing",
            "drawing no",
            "revision",
            "scale",
            "sheet",
        )
        return any(signal in filename for signal in filename_signals) or any(
            signal in text for signal in text_signals
        )

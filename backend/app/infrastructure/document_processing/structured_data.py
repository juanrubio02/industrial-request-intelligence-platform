import re
from typing import Any

from app.domain.document_processing_results.document_types import (
    DocumentDetectedType,
)


class RuleBasedStructuredDataExtractor:
    _RFQ_NUMBER_PATTERNS = (
        re.compile(
            r"\brfq\s*(?:number|no\.?|#|ref(?:erence)?)?\s*[:\-]?\s*"
            r"([A-Z0-9][A-Z0-9/_-]*)",
            re.IGNORECASE,
        ),
        re.compile(
            r"\brequest\s+for\s+quot(?:e|ation)\s*(?:number|no\.?|#|ref(?:erence)?)\s*"
            r"[:\-]?\s*([A-Z0-9][A-Z0-9/_-]*)",
            re.IGNORECASE,
        ),
    )
    _PURCHASE_ORDER_NUMBER_PATTERNS = (
        re.compile(
            r"\b(?:purchase\s+order|po)\s*(?:number|no\.?|#)\s*[:\-]?\s*"
            r"([A-Z0-9][A-Z0-9/_-]*)",
            re.IGNORECASE,
        ),
    )
    _DOCUMENT_REFERENCE_PATTERNS = (
        re.compile(
            r"\b(?:document\s+reference|document\s+ref(?:erence)?|drawing\s+no\.?|"
            r"reference(?:\s+number)?|ref(?:erence)?\s+number)\s*[:\-]?\s*"
            r"([A-Z0-9][A-Z0-9/_-]*)",
            re.IGNORECASE,
        ),
    )
    _REQUESTED_QUANTITY_PATTERNS = (
        re.compile(
            r"\b(?:requested\s+quantity|quantity|qty)\s*[:\-]?\s*"
            r"([0-9]+(?:[.,][0-9]+)?(?:\s*[A-Za-z]+)?)",
            re.IGNORECASE,
        ),
    )
    _MATERIAL_PATTERNS = (
        re.compile(
            r"\b(?:material(?:\s+grade)?|grade)\s*[:\-]?\s*([^\n\r.;]{2,80})",
            re.IGNORECASE,
        ),
    )
    _DELIVERY_DEADLINE_PATTERNS = (
        re.compile(
            r"\b(?:delivery\s+(?:deadline|date)|needed\s+before|required\s+before)\s*"
            r"[:\-]?\s*([^\n\r.;]{3,80})",
            re.IGNORECASE,
        ),
    )

    def extract(
        self,
        *,
        extracted_text: str,
        detected_document_type: DocumentDetectedType | None = None,
    ) -> dict[str, Any]:
        if not self._normalize_text(extracted_text):
            return {}

        fields: dict[str, Any] = {}

        rfq_number = self._extract_first(extracted_text, self._RFQ_NUMBER_PATTERNS)
        if rfq_number is not None:
            fields["rfq_number"] = rfq_number

        purchase_order_number = self._extract_first(
            extracted_text, self._PURCHASE_ORDER_NUMBER_PATTERNS
        )
        if purchase_order_number is not None:
            fields["purchase_order_number"] = purchase_order_number

        document_reference = self._extract_first(
            extracted_text, self._DOCUMENT_REFERENCE_PATTERNS
        )
        if document_reference is not None:
            fields["document_reference"] = document_reference

        requested_quantity = self._extract_first(
            extracted_text, self._REQUESTED_QUANTITY_PATTERNS
        )
        if requested_quantity is not None:
            fields["requested_quantity"] = requested_quantity

        material = self._extract_first(extracted_text, self._MATERIAL_PATTERNS)
        if material is not None:
            fields["material"] = material

        delivery_deadline = self._extract_first(
            extracted_text, self._DELIVERY_DEADLINE_PATTERNS
        )
        if delivery_deadline is not None:
            fields["delivery_deadline"] = delivery_deadline

        if detected_document_type is not None:
            fields["extraction_context"] = detected_document_type.value

        return fields

    def _extract_first(
        self,
        text: str,
        patterns: tuple[re.Pattern[str], ...],
    ) -> str | None:
        for pattern in patterns:
            match = pattern.search(text)
            if match is None:
                continue

            value = self._normalize_value(match.group(1))
            if value:
                return value

        return None

    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _normalize_value(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip(" \t\r\n:;,.")

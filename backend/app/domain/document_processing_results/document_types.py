from enum import StrEnum


class DocumentDetectedType(StrEnum):
    QUOTE_REQUEST = "QUOTE_REQUEST"
    TECHNICAL_SPEC = "TECHNICAL_SPEC"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    DRAWING = "DRAWING"
    OTHER = "OTHER"

from enum import StrEnum


class RequestStatus(StrEnum):
    NEW = "NEW"
    UNDER_REVIEW = "UNDER_REVIEW"
    QUOTE_PREPARING = "QUOTE_PREPARING"
    QUOTE_SENT = "QUOTE_SENT"
    NEGOTIATION = "NEGOTIATION"
    WON = "WON"
    LOST = "LOST"


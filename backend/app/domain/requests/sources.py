from enum import StrEnum


class RequestSource(StrEnum):
    EMAIL = "EMAIL"
    WEB_FORM = "WEB_FORM"
    API = "API"
    MANUAL = "MANUAL"


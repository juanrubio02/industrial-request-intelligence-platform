from app.domain.requests.statuses import RequestStatus

ALLOWED_REQUEST_STATUS_TRANSITIONS: dict[RequestStatus, frozenset[RequestStatus]] = {
    RequestStatus.NEW: frozenset({RequestStatus.UNDER_REVIEW}),
    RequestStatus.UNDER_REVIEW: frozenset({RequestStatus.QUOTE_PREPARING}),
    RequestStatus.QUOTE_PREPARING: frozenset({RequestStatus.QUOTE_SENT}),
    RequestStatus.QUOTE_SENT: frozenset(
        {
            RequestStatus.NEGOTIATION,
            RequestStatus.WON,
            RequestStatus.LOST,
        }
    ),
    RequestStatus.NEGOTIATION: frozenset({RequestStatus.WON, RequestStatus.LOST}),
    RequestStatus.WON: frozenset(),
    RequestStatus.LOST: frozenset(),
}

REQUEST_STATUS_TRANSITION_ORDER: tuple[RequestStatus, ...] = (
    RequestStatus.NEW,
    RequestStatus.UNDER_REVIEW,
    RequestStatus.QUOTE_PREPARING,
    RequestStatus.QUOTE_SENT,
    RequestStatus.NEGOTIATION,
    RequestStatus.WON,
    RequestStatus.LOST,
)


def get_available_request_status_transitions(
    current_status: RequestStatus,
) -> list[RequestStatus]:
    allowed_transitions = ALLOWED_REQUEST_STATUS_TRANSITIONS[current_status]
    return [
        status
        for status in REQUEST_STATUS_TRANSITION_ORDER
        if status in allowed_transitions
    ]


def is_valid_request_status_transition(
    current_status: RequestStatus,
    new_status: RequestStatus,
) -> bool:
    return new_status in ALLOWED_REQUEST_STATUS_TRANSITIONS[current_status]

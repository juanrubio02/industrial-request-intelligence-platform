from __future__ import annotations

import json
import logging
from contextvars import ContextVar, Token
from typing import Any, Sequence

LOGGER_NAME = "forgeflow_request_intelligence.http"

_LOG_CONTEXT_VARS: dict[str, ContextVar[Any | None]] = {
    "request_id": ContextVar("request_id", default=None),
    "user_id": ContextVar("user_id", default=None),
    "membership_id": ContextVar("membership_id", default=None),
    "organization_id": ContextVar("organization_id", default=None),
    "job_id": ContextVar("job_id", default=None),
    "path": ContextVar("path", default=None),
    "method": ContextVar("method", default=None),
    "status_code": ContextVar("status_code", default=None),
    "latency_ms": ContextVar("latency_ms", default=None),
    "error_type": ContextVar("error_type", default=None),
}

_REQUIRED_LOG_FIELDS = tuple(_LOG_CONTEXT_VARS)


def get_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def bind_log_context(**fields: Any | None) -> list[Token[Any | None]]:
    tokens: list[Token[Any | None]] = []
    for field_name, value in fields.items():
        if field_name not in _LOG_CONTEXT_VARS:
            raise KeyError(f"Unknown log context field: {field_name}")
        tokens.append(_LOG_CONTEXT_VARS[field_name].set(value))
    return tokens


def reset_log_context(tokens: Sequence[Token[Any | None]]) -> None:
    for token in reversed(tokens):
        token.var.reset(token)


def clear_log_context() -> None:
    for context_var in _LOG_CONTEXT_VARS.values():
        context_var.set(None)


def snapshot_log_context() -> dict[str, Any | None]:
    return {name: context_var.get() for name, context_var in _LOG_CONTEXT_VARS.items()}


def log_event(level: int, event: dict[str, Any]) -> None:
    payload = {field: None for field in _REQUIRED_LOG_FIELDS}
    payload.update(snapshot_log_context())
    payload.update(event)
    get_logger().log(level, json.dumps(payload, default=str, separators=(",", ":")))

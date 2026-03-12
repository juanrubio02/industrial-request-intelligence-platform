import base64
import binascii
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.application.auth.exceptions import InvalidAccessTokenError
from app.application.auth.tokens import AccessTokenService


class HmacAccessTokenService(AccessTokenService):
    def __init__(self, secret_key: str, ttl_seconds: int) -> None:
        self._secret_key = secret_key.encode("utf-8")
        self._ttl_seconds = ttl_seconds

    def issue(self, user_id: UUID) -> str:
        payload = {
            "sub": str(user_id),
            "exp": int((datetime.now(UTC) + timedelta(seconds=self._ttl_seconds)).timestamp()),
        }
        encoded_payload = self._encode(payload)
        signature = self._sign(encoded_payload)
        return f"{encoded_payload}.{signature}"

    def verify(self, token: str) -> UUID:
        try:
            encoded_payload, signature = token.split(".", maxsplit=1)
        except ValueError as exc:
            raise InvalidAccessTokenError("Invalid or expired access token.") from exc

        expected_signature = self._sign(encoded_payload)
        if not hmac.compare_digest(signature, expected_signature):
            raise InvalidAccessTokenError("Invalid or expired access token.")

        try:
            payload = self._decode(encoded_payload)
            if payload.get("exp", 0) < int(datetime.now(UTC).timestamp()):
                raise InvalidAccessTokenError("Invalid or expired access token.")
            return UUID(payload["sub"])
        except (KeyError, ValueError, TypeError, json.JSONDecodeError, binascii.Error) as exc:
            raise InvalidAccessTokenError("Invalid or expired access token.") from exc

    def _sign(self, encoded_payload: str) -> str:
        digest = hmac.new(
            self._secret_key,
            encoded_payload.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

    @staticmethod
    def _encode(payload: dict[str, object]) -> str:
        raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

    @staticmethod
    def _decode(encoded_payload: str) -> dict[str, object]:
        padding = "=" * (-len(encoded_payload) % 4)
        raw = base64.urlsafe_b64decode((encoded_payload + padding).encode("ascii"))
        return json.loads(raw.decode("utf-8"))

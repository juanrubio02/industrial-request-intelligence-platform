import base64
import binascii
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.application.auth.exceptions import InvalidAccessTokenError, InvalidRefreshTokenError
from app.application.auth.tokens import RefreshTokenClaims, TokenService


class JwtTokenService(TokenService):
    _ALGORITHM = "HS256"

    def __init__(
        self,
        secret_key: str,
        access_token_ttl_seconds: int,
        refresh_token_ttl_seconds: int,
    ) -> None:
        self._secret_key = secret_key.encode("utf-8")
        self._access_token_ttl_seconds = access_token_ttl_seconds
        self._refresh_token_ttl_seconds = refresh_token_ttl_seconds

    def issue_access_token(self, user_id: UUID) -> str:
        return self._issue(user_id, token_type="access", ttl_seconds=self._access_token_ttl_seconds)

    def issue_refresh_token(self, user_id: UUID, token_id: UUID) -> str:
        return self._issue(
            user_id,
            token_type="refresh",
            ttl_seconds=self._refresh_token_ttl_seconds,
            token_id=token_id,
        )

    def verify_access_token(self, token: str) -> UUID:
        payload = self._verify(
            token,
            expected_type="access",
            error_type=InvalidAccessTokenError,
        )
        try:
            return UUID(str(payload["sub"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise InvalidAccessTokenError("Invalid or expired access token.") from exc

    def verify_refresh_token(self, token: str) -> RefreshTokenClaims:
        payload = self._verify(
            token,
            expected_type="refresh",
            error_type=InvalidRefreshTokenError,
        )
        try:
            return RefreshTokenClaims(
                token_id=UUID(str(payload["jti"])),
                user_id=UUID(str(payload["sub"])),
                expires_at=datetime.fromtimestamp(int(payload["exp"]), UTC),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise InvalidRefreshTokenError("Invalid or expired refresh token.") from exc

    def _issue(
        self,
        user_id: UUID,
        *,
        token_type: str,
        ttl_seconds: int,
        token_id: UUID | None = None,
    ) -> str:
        issued_at = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "iat": int(issued_at.timestamp()),
            "exp": int((issued_at + timedelta(seconds=ttl_seconds)).timestamp()),
            "type": token_type,
        }
        if token_id is not None:
            payload["jti"] = str(token_id)
        header = {
            "alg": self._ALGORITHM,
            "typ": "JWT",
        }
        encoded_header = self._encode(header)
        encoded_payload = self._encode(payload)
        signature = self._sign(f"{encoded_header}.{encoded_payload}")
        return f"{encoded_header}.{encoded_payload}.{signature}"

    def _verify(
        self,
        token: str,
        *,
        expected_type: str,
        error_type: type[Exception],
    ) -> dict[str, object]:
        try:
            encoded_header, encoded_payload, signature = token.split(".", maxsplit=2)
        except ValueError as exc:
            raise error_type(f"Invalid or expired {expected_type} token.") from exc

        expected_signature = self._sign(f"{encoded_header}.{encoded_payload}")
        if not hmac.compare_digest(signature, expected_signature):
            raise error_type(f"Invalid or expired {expected_type} token.")

        try:
            header = self._decode(encoded_header)
            payload = self._decode(encoded_payload)
            if header.get("alg") != self._ALGORITHM or header.get("typ") != "JWT":
                raise error_type(f"Invalid or expired {expected_type} token.")
            if payload.get("type") != expected_type:
                raise error_type(f"Invalid or expired {expected_type} token.")
            if payload.get("exp", 0) < int(datetime.now(UTC).timestamp()):
                raise error_type(f"Invalid or expired {expected_type} token.")
            return payload
        except (KeyError, ValueError, TypeError, json.JSONDecodeError, binascii.Error) as exc:
            raise error_type(f"Invalid or expired {expected_type} token.") from exc

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

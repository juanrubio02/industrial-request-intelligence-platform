import base64
import binascii
import hashlib
import hmac
import secrets

from app.application.auth.password import PasswordHasher


class ScryptPasswordHasher(PasswordHasher):
    _N = 2**14
    _R = 8
    _P = 1
    _DKLEN = 32
    _SALT_BYTES = 16

    def hash(self, password: str) -> str:
        salt = secrets.token_bytes(self._SALT_BYTES)
        derived_key = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=self._N,
            r=self._R,
            p=self._P,
            dklen=self._DKLEN,
        )
        return (
            "scrypt$"
            f"{self._N}${self._R}${self._P}$"
            f"{base64.urlsafe_b64encode(salt).decode('ascii')}$"
            f"{base64.urlsafe_b64encode(derived_key).decode('ascii')}"
        )

    def verify(self, password: str, password_hash: str | None) -> bool:
        if password_hash is None:
            return False

        try:
            algorithm, n, r, p, salt_b64, hash_b64 = password_hash.split("$", maxsplit=5)
            salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
            expected_hash = base64.urlsafe_b64decode(hash_b64.encode("ascii"))
            derived_key = hashlib.scrypt(
                password.encode("utf-8"),
                salt=salt,
                n=int(n),
                r=int(r),
                p=int(p),
                dklen=len(expected_hash),
            )
        except (ValueError, binascii.Error):
            return False

        if algorithm != "scrypt":
            return False

        return hmac.compare_digest(derived_key, expected_hash)

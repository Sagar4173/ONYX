"""
Encryption service for sensitive data at rest.
Uses Fernet (symmetric AES-128-CBC with HMAC) for field-level encryption.
"""

import base64
import logging
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from config import settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """Field-level encryption for sensitive stored data.

    Uses Fernet (authenticated symmetric encryption) derived from the
    application SECRET_KEY, so no additional key management is needed.
    """

    def __init__(self, key: Optional[str] = None):
        self._fernet: Optional[Fernet] = None
        if key:
            self._init_fernet(key)

    def _derive_key(self, secret: str) -> bytes:
        salt = b"onyx-encryption-salt-v1"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600_000,
        )
        return base64.urlsafe_b64encode(kdf.derive(secret.encode()))

    def _init_fernet(self, key: str) -> None:
        fernet_key = self._derive_key(key)
        self._fernet = Fernet(fernet_key)

    @property
    def fernet(self) -> Fernet:
        if self._fernet is None:
            if not settings.secret_key:
                raise RuntimeError("SECRET_KEY not configured, cannot initialize encryption")
            self._init_fernet(settings.secret_key)
        return self._fernet

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return ""
        try:
            token = self.fernet.encrypt(plaintext.encode("utf-8"))
            return token.decode("utf-8")
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        try:
            return self.fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            logger.error("Decryption failed: invalid token or key mismatch")
            raise
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def encrypt_dict(self, data: dict, fields: list[str]) -> dict:
        result = dict(data)
        for field in fields:
            if field in result and isinstance(result[field], str):
                result[field] = self.encrypt(result[field])
        return result

    def decrypt_dict(self, data: dict, fields: list[str]) -> dict:
        result = dict(data)
        for field in fields:
            if field in result and isinstance(result[field], str):
                try:
                    result[field] = self.decrypt(result[field])
                except InvalidToken:
                    pass
        return result


encryption_service = EncryptionService()

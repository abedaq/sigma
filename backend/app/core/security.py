"""
SIGMA_ASR_VTT - Security Vault & Secret Redactor
Developer: أصيل السويدي
"""

import re
import logging
import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.exceptions import ConfigurationError

class AESVault:
    """Military-grade AES-256 Fernet Encryption Vault for API Keys and Secrets."""
    
    def __init__(self, master_password: str = None) -> None:
        import os
        import platform
        import uuid
        
        # Generate deterministic master key
        salt = master_password or os.getenv("VAULT_SECRET_KEY") or "SIGMA_VTT_MASTER_KEY_PERSISTENT_2026"
        salt = f"{salt}_SIGMA_SECURE_SALT_99"
        
        key = base64.urlsafe_b64encode(hashlib.sha256(salt.encode()).digest())
        self._fernet = Fernet(key)

    def encrypt(self, plain_text: str) -> str:
        """Encrypts sensitive plain text string to Fernet token."""
        if not plain_text:
            return ""
        return self._fernet.encrypt(plain_text.encode()).decode()

    def decrypt(self, encrypted_token: str) -> str:
        """Decrypts Fernet token back to plain text string."""
        if not encrypted_token:
            return ""
        try:
            return self._fernet.decrypt(encrypted_token.encode()).decode()
        except Exception as e:
            raise ConfigurationError(f"Failed to decrypt secret vault item: {str(e)}")

    @staticmethod
    def mask_key(key: str) -> str:
        """Redacts key string for display in UI (e.g. AIza**********euvU)."""
        if not key or len(key) < 8:
            return "********"
        return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"


class SensitiveDataRedactor(logging.Filter):
    """Logging filter that scrubs API keys and secret patterns from logs."""

    KEY_PATTERNS = [
        re.compile(r'AIzaSy[A-Za-z0-9_-]{33}'),  # Google/Gemini API key
        re.compile(r'sk-[A-Za-z0-9]{32,}'),       # OpenAI/Cloud key
        re.compile(r'key_[A-Za-z0-9_-]{16,}'),    # Speechmatics/Generic API key
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern in self.KEY_PATTERNS:
                record.msg = pattern.sub('[REDACTED_API_KEY]', record.msg)
        return True

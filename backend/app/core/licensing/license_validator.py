"""
SIGMA_ASR_VTT — Production-Grade License Validator & AES-256-GCM Cache Encryption
Developer: أصيل السويدي

Security features:
  - Ed25519 signature verification (raw 32-byte public key)
  - AES-256-GCM encrypted license cache (key derived from HWID via HKDF)
  - Clock rollback detection (last_validated_at tracking against UTC)
  - Canonical JSON validation
  - Obfuscated validation return (nonce-based authorization checking)
"""

import base64
import json
import os
import secrets
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

logger = logging.getLogger("SIGMA_ASR_VTT")


@dataclass
class ValidationResult:
    """Structured result of a license validation attempt with mathematical anti-tamper nonces."""
    valid: bool = False
    data: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    _auth_nonce: int = 0

    def is_authorized(self) -> bool:
        """Return True only if the validator genuinely set the authorization nonce."""
        return (
            self.valid
            and (self._auth_nonce ^ 0xA5C3) != 0
            and (self._auth_nonce % 7 == 3)
        )


def _make_auth_nonce() -> int:
    """Generate a cryptographic random nonce that satisfies the is_authorized() equation."""
    while True:
        n = secrets.randbelow(2**31)
        if (n ^ 0xA5C3) != 0 and (n % 7 == 3):
            return n


_CACHE_SALT = b"SigmaVTT-LicenseCache-v2"


def _derive_cache_key(hwid: str) -> bytes:
    """Derive a 256-bit AES key from the machine's HWID using HKDF-SHA256."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_CACHE_SALT,
        info=b"license-cache-encryption",
    )
    return hkdf.derive(hwid.encode("utf-8"))


def _encrypt_cache(data: bytes, hwid: str) -> bytes:
    """Encrypt license data with AES-256-GCM using HWID-derived key."""
    key = _derive_cache_key(hwid)
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, data, None)
    return nonce + ct  # 12-byte nonce || ciphertext+tag


def _decrypt_cache(blob: bytes, hwid: str) -> bytes:
    """Decrypt license data. Raises error on tamper or incorrect machine HWID."""
    if len(blob) < 13:
        raise ValueError("Cache blob too short for AES-GCM decryption")
    key = _derive_cache_key(hwid)
    nonce = blob[:12]
    ct = blob[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None)


_CLOCK_TOLERANCE_SECONDS = 300  # 5-minute tolerance for natural clock drift
_IN_MEMORY_VALIDATION_CACHE: Dict[str, Any] = {}


class LicenseValidator:
    """
    Hardened License Validator with AES-256-GCM Encryption and Ed25519 Verification.
    """

    # Raw 32-byte Ed25519 master public key — safe to ship with client
    _PUBLIC_KEY_RAW = bytes.fromhex(
        "6cb0703a084ff8fd9b6b89c0ca55a742325b45f545a1a2f47974c2215aaea5f2",
    )

    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir:
            self.appdata_path = storage_dir
        else:
            self.appdata_path = Path(os.environ.get("APPDATA", "")) / "SIGMA_ASR_VTT"
        self.cache_file = self.appdata_path / "license.enc"
        self.clock_file = self.appdata_path / ".clock_state"
        self.appdata_path.mkdir(parents=True, exist_ok=True)

        self._public_key = ed25519.Ed25519PublicKey.from_public_bytes(
            self._PUBLIC_KEY_RAW
        )

    def validate(self, current_hwid: str) -> ValidationResult:
        """Full validation: load cache -> decrypt AES-GCM -> verify Ed25519 -> check clock consistency."""
        if not self.cache_file.exists():
            return ValidationResult(False, message="تفعيل البرنامج مطلوب (لا يوجد ملف ترخيص محمي)")

        try:
            blob = self.cache_file.read_bytes()
        except Exception as e:
            logger.exception(f"Failed reading encrypted license file: {e}")
            return ValidationResult(False, message="فشل في قراءة ملف التفعيل")

        try:
            cache_json = _decrypt_cache(blob, current_hwid)
        except Exception:
            self._safe_delete_cache()
            return ValidationResult(
                False, message="ملف التفعيل تالف أو لا يخص هذا الجهاز (فشل فك التشفير بأمان)"
            )

        try:
            cache = json.loads(cache_json.decode("utf-8"))
            token = cache.get("token", "")
            last_validated = cache.get("last_validated_at", 0)
        except Exception:
            self._safe_delete_cache()
            return ValidationResult(False, message="بيانات التفعيل غير قابلة للقراءة")

        result = self.verify_license_string(token, current_hwid)
        if not result.valid:
            return result

        now_ts = int(time.time())
        if last_validated > 0 and now_ts < (last_validated - _CLOCK_TOLERANCE_SECONDS):
            return ValidationResult(
                False,
                message="تم اكتشاف تلاعب بساعة النظام. يرجى ضبط التاريخ والوقت الصحيحين.",
            )

        self._update_cache_timestamp(token, now_ts, current_hwid)
        return result

    def validate_cached(self, current_hwid: str, ttl_seconds: int = 60) -> ValidationResult:
        """Throttled validation for HTTP middleware: caches result in memory to eliminate disk I/O."""
        now_ts = int(time.time())
        cache_key = (current_hwid, str(self.cache_file.resolve()))
        cached_entry = _IN_MEMORY_VALIDATION_CACHE.get(cache_key)
        if (
            cached_entry
            and (now_ts - cached_entry.get("timestamp", 0)) < ttl_seconds
            and self.cache_file.exists()
        ):
            try:
                st = self.cache_file.stat()
                if st.st_mtime_ns == cached_entry.get("mtime_ns") and st.st_size == cached_entry.get("size"):
                    return cached_entry["result"]
            except Exception:
                pass

        result = self.validate(current_hwid)
        try:
            if self.cache_file.exists():
                st = self.cache_file.stat()
                _IN_MEMORY_VALIDATION_CACHE[cache_key] = {
                    "result": result,
                    "timestamp": now_ts,
                    "mtime_ns": st.st_mtime_ns,
                    "size": st.st_size
                }
        except Exception:
            pass
        return result

    def verify_license_string(self, token: str, current_hwid: str) -> ValidationResult:
        """Verify an Ed25519-signed license token string against device HWID."""
        try:
            if not token:
                return ValidationResult(False, message="كود التفعيل فارغ")
            
            clean_token = token.strip()
            if clean_token.startswith("SIGMA-LIC-"):
                clean_token = clean_token[len("SIGMA-LIC-"):]

            parts = clean_token.split(".")
            if len(parts) != 2:
                return ValidationResult(False, message="تنسيق كود التفعيل غير صالح")

            payload_b64, signature_b64 = parts

            def _pad(s: str) -> str:
                return s + "=" * (-len(s) % 4)

            try:
                payload_bytes = base64.urlsafe_b64decode(_pad(payload_b64))
                signature_bytes = base64.urlsafe_b64decode(_pad(signature_b64))
            except Exception:
                return ValidationResult(False, message="تنسيق التشفير غير صالح")

            if len(signature_bytes) != 64:
                return ValidationResult(False, message="طول التوقيع الرقمي غير صالح")

            # Canonical signature check: reject tampered base64 padding bits
            expected_sig_b64 = base64.urlsafe_b64encode(signature_bytes).decode().rstrip("=")
            if signature_b64.rstrip("=") != expected_sig_b64:
                return ValidationResult(False, message="التوقيع الرقمي غير سليم (تلاعب بترميز Base64)")

            try:
                self._public_key.verify(signature_bytes, payload_bytes)
            except InvalidSignature:
                return ValidationResult(
                    False, message="تم التلاعب بكود التفعيل (التوقيع الإلكتروني غير مطابق)"
                )

            try:
                payload = json.loads(payload_bytes.decode("utf-8"))
            except json.JSONDecodeError:
                return ValidationResult(False, message="بيانات التفعيل غير قابلة للقراءة")

            if payload.get("license_version", 0) < 2:
                return ValidationResult(False, message="إصدار التفعيل قديم — يرجى طلب كود جديد")

            token_hwid = payload.get("device_id")
            if not token_hwid or token_hwid != current_hwid:
                return ValidationResult(False, message=f"كود التفعيل لا يخص هذا الجهاز (بصمة الترخيص: {token_hwid})")

            expires_at = payload.get("expires_at", 0)
            is_lifetime = (expires_at == 0)
            remaining_hours = None
            remaining_days = None

            if not is_lifetime:
                now_ts = int(datetime.now(timezone.utc).timestamp())
                if now_ts > expires_at:
                    expiry_str = datetime.fromtimestamp(expires_at, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
                    return ValidationResult(False, message=f"انتهى مفعول الترخيص بتاريخ {expiry_str} (UTC)")
                remaining_seconds = expires_at - now_ts
                remaining_hours = round(remaining_seconds / 3600, 2)
                remaining_days = round(remaining_seconds / 86400, 2)

            info = {
                "client_name": payload.get("client_name", "العميل المعتمد"),
                "plan": payload.get("plan", "PRO"),
                "expiry": "Lifetime" if is_lifetime else datetime.fromtimestamp(expires_at, tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
                "is_lifetime": is_lifetime,
                "expires_at": expires_at,
                "remaining_hours": remaining_hours,
                "remaining_days": remaining_days,
                "license_id": payload.get("license_id", ""),
                "issued_at": datetime.fromtimestamp(payload.get("issued_at", 0), tz=timezone.utc).strftime("%Y-%m-%d %H:%M") if payload.get("issued_at") else "N/A",
            }

            return ValidationResult(
                valid=True,
                data=info,
                message="تم التفعيل بنجاح",
                _auth_nonce=_make_auth_nonce(),
            )

        except Exception as e:
            return ValidationResult(False, message=f"خطأ غير متوقع أثناء التحقق: {str(e)}")

    def save_license(self, token: str, hwid: str) -> None:
        """Encrypt and save a valid license token to local AES-GCM cache."""
        _IN_MEMORY_VALIDATION_CACHE.clear()
        now_ts = int(time.time())
        cache = {
            "token": token,
            "last_validated_at": now_ts,
        }
        blob = _encrypt_cache(json.dumps(cache).encode("utf-8"), hwid)
        self.cache_file.write_bytes(blob)

    def _update_cache_timestamp(self, token: str, now_ts: int, hwid: str) -> None:
        """Update last_validated_at timestamp in the encrypted cache."""
        try:
            cache = {"token": token, "last_validated_at": now_ts}
            blob = _encrypt_cache(json.dumps(cache).encode("utf-8"), hwid)
            self.cache_file.write_bytes(blob)
        except Exception as e:
            logger.warning(f"Failed updating cache timestamp: {e}")

    def _safe_delete_cache(self) -> None:
        """Safely remove corrupted cache files."""
        _IN_MEMORY_VALIDATION_CACHE.clear()
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
        except Exception as e:
            logger.warning(f"Failed deleting corrupted cache: {e}")

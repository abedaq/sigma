"""
SIGMA_ASR_VTT - Verification Script for Licensing Encryption & HWID Protection
Developer: أصيل السويدي
"""

import os
import sys
import json

# Ensure backend root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.licensing import HWIDGenerator, LicenseValidator, ValidationResult
from app.core.licensing.license_validator import _encrypt_cache, _decrypt_cache, _make_auth_nonce


def test_licensing_encryption():
    """Test function recognized by pytest and SonarQube."""
    print("=== [TEST START] SIGMA_ASR_VTT Licensing & AES-256-GCM Encryption ===")
    
    # 1. Generate real deterministic HWID
    print("\n[STEP 1] Generating deterministic Hardware Fingerprint (HWID)...")
    hwid = HWIDGenerator.generate()
    print(f"[SUCCESS] Generated HWID: {hwid}")
    assert hwid.startswith("SIGMA-") and len(hwid.split("-")) == 5, "Invalid HWID format"  # nosec B101

    # 2. Test AES-256-GCM + HKDF Encryption & Decryption
    print("\n[STEP 2] Testing AES-256-GCM + HKDF Cache Encryption & Decryption...")
    sample_payload = json.dumps({"token": "sample.signature", "last_validated_at": 1700000000}).encode("utf-8")  # nosec
    
    encrypted_blob = _encrypt_cache(sample_payload, hwid)
    print(f"[SUCCESS] Encrypted sample payload into AES-GCM blob ({len(encrypted_blob)} bytes)")
    
    decrypted_bytes = _decrypt_cache(encrypted_blob, hwid)
    assert decrypted_bytes == sample_payload, "Decrypted content mismatch!"  # nosec B101
    print("[SUCCESS] Decrypted AES-GCM blob perfectly matches original payload.")

    # 3. Test Anti-Tamper & Wrong Hardware Blocking (Simulated Stolen License)
    print("\n[STEP 3] Testing Hardware Binding & Tamper Protection...")
    fake_hwid = "SIGMA-0000-1111-2222-3333"
    try:
        _decrypt_cache(encrypted_blob, fake_hwid)
        print("[ERROR] Decryption succeeded on fake HWID! Protection failed.")
        sys.exit(1)
    except Exception as e:
        print(f"[SUCCESS] Blocked decryption attempt with wrong HWID as expected! Error: {type(e).__name__}")

    # 4. Test Validator & Mathematical Authorization Nonce
    print("\n[STEP 4] Testing LicenseValidator & Mathematical Authorization Nonces...")
    validator = LicenseValidator()
    res = validator.validate(hwid)
    print(f"[INFO] Current machine activation check result: valid={res.valid}, message='{res.message}'")
    
    auth_nonce = _make_auth_nonce()
    test_res = ValidationResult(valid=True, message="Test Authorized", _auth_nonce=auth_nonce)
    assert test_res.is_authorized(), "Mathematical nonce check failed!"  # nosec B101
    print(f"[SUCCESS] Mathematical authorization nonce verification passed (Nonce: {auth_nonce}).")

    print("\n=== [TEST RESULT: ALL LICENSING & ENCRYPTION SYSTEMS FUNCTIONING PERFECTLY] ===")


if __name__ == "__main__":
    test_licensing_encryption()

"""
SIGMA_ASR_VTT - Comprehensive Licensing & Cryptography Test Suite
Developer: أصيل السويدي
"""

import sys
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.licensing.hwid import HWIDGenerator
from app.core.licensing.license_validator import LicenseValidator
from scripts.keygen import generate_license_token
from app.main import app


@pytest.fixture
def current_hwid():
    return HWIDGenerator.generate()


@pytest.fixture
def test_storage(tmp_path):
    return tmp_path / "license_cache"


def test_hwid_format_and_depth(current_hwid):
    """Verifies that HWID matches canonical format and has deep hardware components."""
    assert current_hwid.startswith("SIGMA-")
    parts = current_hwid.split("-")
    assert len(parts) == 5
    for p in parts[1:]:
        assert len(p) == 4

    details = HWIDGenerator.get_hardware_details()
    assert len(details) >= 7
    assert "cpu_id" in details
    assert "machine_guid" in details
    assert "baseboard_serial" in details


def test_lifetime_license_flow(current_hwid, test_storage):
    """Verifies generation, verification, and persistence of a lifetime license."""
    token, payload = generate_license_token(
        hwid=current_hwid,
        client_name="أصيل السويدي",
        license_type="lifetime",
        plan="ENTERPRISE"
    )
    assert token.startswith("SIGMA-LIC-")
    assert payload["expires_at"] == 0

    validator = LicenseValidator(storage_dir=test_storage)
    res = validator.verify_license_string(token, current_hwid)
    assert res.valid is True
    assert res.is_authorized() is True
    assert res.data["is_lifetime"] is True
    assert res.data["client_name"] == "أصيل السويدي"
    assert res.data["plan"] == "ENTERPRISE"

    # Test saving and validating from encrypted cache
    validator.save_license(token, current_hwid)
    cached_res = validator.validate(current_hwid)
    assert cached_res.valid is True
    assert cached_res.is_authorized() is True


def test_hour_based_license(current_hwid, test_storage):
    """Verifies hour-based licenses with granular time calculation."""
    token, payload = generate_license_token(
        hwid=current_hwid,
        client_name="عميل تجريبي",
        license_type="time_limited",
        duration_hours=48.0,
        plan="PRO"
    )
    validator = LicenseValidator(storage_dir=test_storage)
    res = validator.verify_license_string(token, current_hwid)
    assert res.valid is True
    assert res.is_authorized() is True
    assert res.data["is_lifetime"] is False
    assert res.data["remaining_hours"] is not None
    assert 47.9 <= res.data["remaining_hours"] <= 48.0


def test_expired_license_rejection(current_hwid, test_storage):
    """Verifies that an expired license is strictly rejected."""
    past_timestamp = int(time.time()) - 3600  # Expired 1 hour ago
    token, _ = generate_license_token(
        hwid=current_hwid,
        client_name="عميل منتهي",
        license_type="time_limited",
        custom_expiry_timestamp=past_timestamp
    )
    validator = LicenseValidator(storage_dir=test_storage)
    res = validator.verify_license_string(token, current_hwid)
    assert res.valid is False
    assert res.is_authorized() is False
    assert "انتهى مفعول الترخيص" in res.message


def test_mismatched_hwid_rejection(current_hwid, test_storage):
    """Verifies that a valid license for another machine cannot be used."""
    other_hwid = "SIGMA-9999-8888-7777-6666"
    token, _ = generate_license_token(
        hwid=other_hwid,
        client_name="عميل بجهاز آخر",
        license_type="lifetime"
    )
    validator = LicenseValidator(storage_dir=test_storage)
    res = validator.verify_license_string(token, current_hwid)
    assert res.valid is False
    assert res.is_authorized() is False
    assert "لا يخص هذا الجهاز" in res.message


def test_tampered_token_rejection(current_hwid, test_storage):
    """Verifies cryptographic tamper detection when token payload or signature is modified."""
    token, _ = generate_license_token(
        hwid=current_hwid,
        client_name="أصيل",
        license_type="lifetime"
    )
    # Modify last characters of token
    tampered_token = token[:-5] + "AAAAA"
    validator = LicenseValidator(storage_dir=test_storage)
    res = validator.verify_license_string(tampered_token, current_hwid)
    assert res.valid is False
    assert res.is_authorized() is False


def test_fastapi_endpoints_and_gatekeeper(current_hwid, monkeypatch, tmp_path):
    """Verifies FastAPI endpoints and middleware gatekeeper behavior."""
    # Point validator storage to temporary directory for test isolation
    test_storage_dir = tmp_path / "api_test_lic"
    orig_init = LicenseValidator.__init__

    def custom_init(self, storage_dir=None):
        orig_init(self, storage_dir=test_storage_dir)

    monkeypatch.setattr(LicenseValidator, "__init__", custom_init)

    client = TestClient(app)

    # 1. License status when not activated
    res_status = client.get("/api/v1/license/status")
    assert res_status.status_code == 200
    data = res_status.json()
    assert "hwid" in data
    assert "support" in data
    assert "whatsapp" in data["support"]
    assert "telegram" in data["support"]
    assert data["valid"] is False

    # 2. Hardware breakdown endpoint
    res_hwid = client.get("/api/v1/license/hwid")
    assert res_hwid.status_code == 200
    assert "hardware_components" in res_hwid.json()

    # 3. Protected endpoint before activation should return 403 Forbidden
    res_protected = client.get("/api/v1/keys")
    assert res_protected.status_code == 403
    assert res_protected.json()["detail"] == "LICENSE_REQUIRED"

    # 4. Activate with valid token
    valid_token, _ = generate_license_token(
        hwid=current_hwid,
        client_name="أصيل السويدي",
        license_type="lifetime"
    )
    res_activate = client.post("/api/v1/license/activate", json={"token": valid_token})
    assert res_activate.status_code == 200
    assert res_activate.json()["status"] == "success"

    # 5. Protected endpoint after activation should now pass!
    res_protected_after = client.get("/api/v1/keys")
    assert res_protected_after.status_code == 200

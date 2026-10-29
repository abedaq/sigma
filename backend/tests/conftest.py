"""
SIGMA_ASR_VTT - Pytest Shared Fixtures & Environment Configuration
Developer: أصيل السويدي
"""

import sys
from pathlib import Path
import pytest

# Ensure backend root is on sys.path for all test discovery
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.infrastructure.database import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initializes the database schema, directories, and test license for the test session."""
    init_db()
    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    from app.core.licensing.hwid import HWIDGenerator
    from app.core.licensing.license_validator import LicenseValidator
    from scripts.keygen import generate_license_token
    
    hwid = HWIDGenerator.generate()
    token, _ = generate_license_token(hwid=hwid, client_name="Test Suite", license_type="lifetime")
    validator = LicenseValidator()
    validator.save_license(token, hwid)

    yield


@pytest.fixture
def anyio_backend():
    """Specifies asyncio as the default async backend for anyio tests."""
    return "asyncio"


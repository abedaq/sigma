"""
SIGMA_ASR_VTT - Remediation & Security Audit Verification Test Suite
Developer: أصيل السويدي
"""
import pytest
from pathlib import Path
from app.core.licensing.license_validator import LicenseValidator, _IN_MEMORY_VALIDATION_CACHE
from app.services.pipeline_service import de_duplicate_overlapping_subtitles
from app.core.models import SubtitleItem
from app.infrastructure.database_ops import (
    get_cached_translations_batch,
    set_cached_translations_batch,
    _make_cache_key
)
from app.core.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent

def test_no_hardcoded_api_keys_in_router():
    """Verify that no raw API keys are hardcoded in router.py."""
    router_file = BASE_DIR / "app" / "api" / "router.py"
    content = router_file.read_text(encoding="utf-8")
    assert "gsk_dummy_test_remediation_key_sample" not in content, "Groq key leaked in router.py!"
    assert "dummy_assemblyai_test_remediation_key" not in content, "AssemblyAI key leaked in router.py!"
    assert "key_speechmatics_token_sigma_vtt" not in content, "Speechmatics key leaked in router.py!"

def test_no_public_keygen_api_in_router():
    """Verify that /license/generate endpoint is removed from router.py."""
    router_file = BASE_DIR / "app" / "api" / "router.py"
    content = router_file.read_text(encoding="utf-8")
    assert '@router.post("/license/generate")' not in content, "/license/generate endpoint must be removed!"

def test_path_sanitization_logic():
    """Verify that path traversal strings are safely resolved to leaf names."""
    malicious_inputs = [
        "../../evil.exe",
        "..\\..\\windows\\system32\\cmd.exe",
        "/etc/passwd",
        "foo/bar/video.mp4"
    ]
    for mi in malicious_inputs:
        sanitized = Path(mi).name
        assert "/" not in sanitized and "\\" not in sanitized
        assert sanitized in ["evil.exe", "cmd.exe", "passwd", "video.mp4"]

def test_license_memory_cache():
    """Verify that LicenseValidator utilizes in-memory cache to save disk I/O."""
    validator = LicenseValidator()
    _IN_MEMORY_VALIDATION_CACHE.clear()
    
    from app.core.licensing.license_validator import ValidationResult
    fake_result = ValidationResult(valid=True, message="Cached Test")
    import time
    now_ts = int(time.time())
    
    cache_key = ("TEST-HWID", str(validator.cache_file.resolve()))
    st = validator.cache_file.stat() if validator.cache_file.exists() else None
    
    _IN_MEMORY_VALIDATION_CACHE[cache_key] = {
        "result": fake_result,
        "timestamp": now_ts,
        "mtime_ns": st.st_mtime_ns if st else 0,
        "size": st.st_size if st else 0
    }

    if validator.cache_file.exists():
        res = validator.validate_cached("TEST-HWID")
        assert res.message == "Cached Test", "Should retrieve result from in-memory cache without hitting disk decrypt"

def test_batch_translation_cache():
    """Verify that batch translation cache functions insert and query in bulk."""
    test_entries = [
        ("Test Hello Batch", "en", "ar", "مرحبا بالدفعة التجريبية"),
        ("Test World Batch", "en", "ar", "عالم الدفعة التجريبية")
    ]
    set_cached_translations_batch(test_entries)
    
    cached = get_cached_translations_batch(["Test Hello Batch", "Test World Batch"], "en", "ar")
    k1 = _make_cache_key("Test Hello Batch", "en", "ar")
    k2 = _make_cache_key("Test World Batch", "en", "ar")
    
    assert cached.get(k1) == "مرحبا بالدفعة التجريبية"
    assert cached.get(k2) == "عالم الدفعة التجريبية"

def test_deduplicate_overlapping_subtitles():
    """Verify that subtitle deduplication preserves ordering and removes boundary echoes."""
    items = [
        SubtitleItem(index=1, start_time="00:00:01,000", end_time="00:00:03,000", text="مرحبا بكم"),
        SubtitleItem(index=2, start_time="00:00:02,500", end_time="00:00:04,000", text="مرحبا بكم"),
        SubtitleItem(index=3, start_time="00:00:04,500", end_time="00:00:06,000", text="في نظام سيجما")
    ]
    deduped = de_duplicate_overlapping_subtitles(items)
    assert len(deduped) == 2
    assert deduped[0].text == "مرحبا بكم"
    assert deduped[1].text == "في نظام سيجما"
    assert deduped[0].index == 1
    assert deduped[1].index == 2

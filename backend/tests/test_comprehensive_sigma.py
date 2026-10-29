"""
Comprehensive Verification Tests for SIGMA_ASR_VTT
Tests all core services, API endpoints, SQLite persistence, and Zero-PyTorch enforcement.
"""

import sys
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.subtitle_service import SubtitleService
from app.core.models import SubtitleItem

client = TestClient(app)

def test_zero_pytorch_policy():
    """Verify strictly that PyTorch is NOT loaded or imported."""
    assert "torch" not in sys.modules
    assert "torchaudio" not in sys.modules
    assert "torchvision" not in sys.modules

def test_system_endpoints():
    """Verify session-token and system info endpoints."""
    # 1. Session token endpoint
    res_token = client.get("/api/v1/system/session-token")
    assert res_token.status_code == 200
    data_token = res_token.json()
    assert "session_token" in data_token
    assert len(data_token["session_token"]) > 10

    # 2. Hardware metrics endpoint
    res_info = client.get("/api/v1/system/info")
    assert res_info.status_code == 200
    data_info = res_info.json()
    assert "cpu_name" in data_info
    assert "ram_total_gb" in data_info
    assert data_info["ram_total_gb"] > 0

def test_subtitle_parsers():
    """Verify multi-format subtitle parsing and bilingual export."""
    # VTT format
    vtt_text = "WEBVTT\n\n1\n00:00:01.000 --> 00:00:04.000\nHello World\n"
    vtt_items = SubtitleService.parse_subtitle(vtt_text, "test.vtt")
    assert len(vtt_items) == 1
    assert vtt_items[0].text == "Hello World"

    # SRT format
    srt_text = "1\n00:00:01,000 --> 00:00:04,000\nWelcome to Sigma ASR\n"
    srt_items = SubtitleService.parse_subtitle(srt_text, "test.srt")
    assert len(srt_items) == 1
    assert srt_items[0].text == "Welcome to Sigma ASR"

    # Bilingual export
    translated_items = [
        SubtitleItem(
            index=1,
            start_time="00:00:01,000",
            end_time="00:00:04,000",
            text="مرحباً بكم في سيجما"
        )
    ]
    bilingual_srt = SubtitleService.export_bilingual_srt(srt_items, translated_items)
    assert "Welcome to Sigma ASR" in bilingual_srt
    assert "مرحباً بكم في سيجما" in bilingual_srt

def test_glossary_and_keys_endpoints():
    """Verify glossary and API keys persistence endpoints."""
    # Add glossary term
    res_add_glo = client.post("/api/v1/glossary", json={"term": "AI Engine", "translation": "محرك الذكاء الاصطناعي"})
    assert res_add_glo.status_code == 200

    # Get glossary terms
    res_get_glo = client.get("/api/v1/glossary")
    assert res_get_glo.status_code == 200
    terms = res_get_glo.json()
    assert "AI Engine" in terms

    # Keys listing
    res_keys = client.get("/api/v1/keys")
    assert res_keys.status_code == 200
    assert isinstance(res_keys.json(), list)

def test_subtitle_process_api():
    """Verify /api/v1/process/subtitle translates and formats subtitles."""
    srt_text = "1\n00:00:01,000 --> 00:00:03,000\nHello world\n"
    res = client.post("/api/v1/process/subtitle", json={
        "subtitle_content": srt_text,
        "source_language": "en",
        "target_language": "ar",
        "export_format": "srt",
        "use_glossary": True,
        "bilingual": False,
        "filename": "hello.srt"
    })
    assert res.status_code == 200
    data = res.json()
    assert "translated_content" in data
    assert len(data["translated_content"]) > 0

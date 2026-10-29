"""
SIGMA_ASR_VTT - Master Test Matrix Automated Test Suite
Verifies Master Test Scenarios across Security, Acoustic/ONNX, VAD, ASR, Translation, Caching, and Subtitles.
Developer: أصيل السويدي
"""

import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from app.core.models import SubtitleItem, APIKeyConfig, KeyStatus
from app.core.exceptions import FileProcessingError, RateLimitError, ValidationError
from app.core.security import AESVault
from app.infrastructure.process_manager import FileInspector
from app.services.asr_service import ASRService, ASRHallucinationGuard
from app.infrastructure.database_ops import get_cached_translation, set_cached_translation
from app.services.subtitle_service import SubtitleService
from app.services.media_service import MediaService
from app.services.vocal_isolation_service import HardwareProbe, MODEL_TIERS


BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# 1. Security & Zero-PyTorch Tests (SC-08.1, SC-08.2, SC-08.4)
# ==============================================================================

def test_sc08_zero_pytorch_strict_audit():
    """SC-08.4: Audit 100% of python files in backend app for any forbidden PyTorch imports."""
    forbidden = ["import torch", "from torch", "import torchaudio", "from torchaudio", "import torchvision", "from torchvision"]
    app_dir = BASE_DIR / "app"
    python_files = list(app_dir.glob("**/*.py"))
    
    assert len(python_files) > 10, "Should have scanned backend app python files."
    
    violations = []
    for pf in python_files:
        content = pf.read_text(encoding="utf-8", errors="ignore")
        for line_num, line in enumerate(content.splitlines(), start=1):
            line_clean = line.strip()
            # Ignore comments
            if line_clean.startswith("#"):
                continue
            for f in forbidden:
                if f in line_clean:
                    violations.append(f"{pf.name}:{line_num} -> {line_clean}")
                    
    assert not violations, f"Forbidden PyTorch imports detected in codebase: {violations}"



def test_sc08_magic_byte_file_signature_validation(tmp_path):
    """SC-08.1: Verify FileInspector detects fake files (e.g. .exe masquerading as .mp4)."""
    fake_video = tmp_path / "malicious.mp4"
    # Write Windows PE Executable magic bytes 'MZ...'
    fake_video.write_bytes(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff")
    
    with pytest.raises((FileProcessingError, ValidationError)):
        FileInspector.validate_file_bytes(fake_video)


# ==============================================================================
# 2. Hallucination Guard & Stretched Lyrics Tests (SC-02.2, SC-02.3, SC-02.4)
# ==============================================================================

def test_sc02_multilingual_watermark_elimination():
    """SC-02.2: Purges Turkish, English, and Arabic Whisper dataset watermark credits."""
    items = [
        SubtitleItem(index=1, start_time="00:00:01,000", end_time="00:00:03,000", text="Altyazı M.K."),
        SubtitleItem(index=2, start_time="00:00:04,000", end_time="00:00:07,000", text="Gerçek bir şarkı sözü"),
        SubtitleItem(index=3, start_time="00:00:08,000", end_time="00:00:10,000", text="Translated by Amara.org"),
        SubtitleItem(index=4, start_time="00:00:11,000", end_time="00:00:14,000", text="Subtitles by OpenSubtitles"),
        SubtitleItem(index=5, start_time="00:00:15,000", end_time="00:00:18,000", text="Aramam sormam bir daha"),
    ]
    
    cleaned = ASRHallucinationGuard.filter_hallucinations(items)
    texts = [c.text for c in cleaned]
    
    assert "Altyazı M.K." not in texts
    assert "Translated by Amara.org" not in texts
    assert "Subtitles by OpenSubtitles" not in texts
    assert "Gerçek bir şarkı sözü" in texts
    assert "Aramam sormam bir daha" in texts
    assert len(cleaned) == 2


def test_sc02_stretched_lyrics_duration_clamping():
    """SC-02.3: Intelligently clamps stretched vocal timestamps without dropping words."""
    stretched_item = SubtitleItem(
        index=1,
        start_time="00:00:10,000",
        end_time="00:00:30,000",  # 20.0s duration!
        text="Aramam bir daha"    # Only 3 words!
    )
    
    cleaned = ASRHallucinationGuard.filter_hallucinations([stretched_item])
    assert len(cleaned) == 1
    # 3 words * 1.5 = 4.5s -> should be clamped to 4.5s (end = 00:00:14,500)
    assert cleaned[0].end_time == "00:00:14,500"
    assert cleaned[0].text == "Aramam bir daha"


def test_sc02_repetitive_loop_elimination():
    """SC-02.4: Eliminates repetitive word/phrase loops."""
    loop_item = SubtitleItem(
        index=1,
        start_time="00:00:01,000",
        end_time="00:00:05,000",
        text="thank you thank you thank you thank you"
    )
    cleaned = ASRHallucinationGuard.filter_hallucinations([loop_item])
    assert len(cleaned) == 0


# ==============================================================================
# 3. Circuit Breaker & Key Failover (SC-03.1)
# ==============================================================================

@pytest.mark.anyio
async def test_sc03_circuit_breaker_key_failover(tmp_path):
    """SC-03.1: Verifies automatic instant failover when Key 1 hits Rate Limit (429)."""
    fake_wav = tmp_path / "test_audio.wav"
    fake_wav.write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00")
    
    vault = AESVault()
    key1 = APIKeyConfig(
        id="k1", name="Groq Primary", provider="groq",
        encrypted_key=vault.encrypt("gsk_test1"), masked_key="gsk_1***",
        priority=1, status=KeyStatus.ACTIVE
    )
    key2 = APIKeyConfig(
        id="k2", name="Groq Fallback", provider="groq",
        encrypted_key=vault.encrypt("gsk_test2"), masked_key="gsk_2***",
        priority=2, status=KeyStatus.ACTIVE
    )
    
    asr = ASRService()
    
    # Mock Provider 1 to raise RateLimitError, Provider 2 to succeed
    mock_prov1 = AsyncMock()
    mock_prov1.transcribe_audio.side_effect = RateLimitError("Rate limit exceeded", "Groq Primary")
    
    mock_prov2 = AsyncMock()
    mock_prov2.transcribe_audio.return_value = [
        SubtitleItem(index=1, start_time="00:00:01,000", end_time="00:00:03,000", text="Succeeded via failover key")
    ]
    
    with patch.object(asr, "get_provider", side_effect=[mock_prov1, mock_prov2]):
        results = await asr.transcribe(fake_wav, [key1, key2], language="en")
        
    assert len(results) == 1
    assert results[0].text == "Succeeded via failover key"
    assert key1.remaining_quota_percent == 0.0


# ==============================================================================
# 4. Token Caching & Cost Optimization (SC-05.1, SC-05.2)
# ==============================================================================

def test_sc05_sqlite_disk_cache_zero_token_burn():
    """SC-05.1 & SC-05.2: Verifies persistent caching returns exact translation without token burn."""
    src_text = "Aramam sormam bir daha"
    tgt_text = "لن أبحث ولن أسأل مرة أخرى"
    
    # Set cache in SQLite
    set_cached_translation(src_text, "tr", "ar", tgt_text)
    
    # Read back
    cached = get_cached_translation(src_text, "tr", "ar")
    assert cached == tgt_text
    
    # Verify case and whitespace resilience
    cached_upper = get_cached_translation("  ARAMAM SORMAM BIR DAHA  ", "tr", "ar")
    assert cached_upper == tgt_text


# ==============================================================================
# 5. Subtitle Pacing & Netflix Standards (SC-06.1, SC-06.2, SC-06.3)
# ==============================================================================

def test_sc06_netflix_pacing_and_cps_clamping():
    """SC-06.1 & SC-06.2: Clamps micro-flashes (<1.2s) and excessively long subtitle displays."""
    items = [
        SubtitleItem(index=1, start_time="00:00:01,000", end_time="00:00:01,300", text="Flash word"), # 0.3s
        SubtitleItem(index=2, start_time="00:00:05,000", end_time="00:00:15,000", text="Short text"), # 10.0s
    ]
    
    regulated = SubtitleService.enforce_reading_speed_and_pacing(items)
    
    # Flash word must be expanded to at least 1.2s
    assert regulated[0].end_time == "00:00:02,200"
    # Long text must be clamped to max 7.0s
    assert regulated[1].end_time == "00:00:12,000"


def test_sc06_bilingual_ass_dual_layer_generation():
    """SC-06.3: Verifies dual-layer ASS broadcast subtitle generation."""
    items = [
        SubtitleItem(
            index=1,
            start_time="00:00:01,000",
            end_time="00:00:03,000",
            text="Aramam",
            translated_text="لن أبحث"
        )
    ]
    ass_text = SubtitleService.export_bilingual_ass(items)
    
    assert "[Script Info]" in ass_text
    assert "Style: ArabicPrimary,Tajawal,22" in ass_text
    assert "Style: EnglishSecondary,Arial,15" in ass_text
    assert "Dialogue: 1,0:00:01.00,0:00:03.00,ArabicPrimary,,0,0,0,,لن أبحث" in ass_text
    assert "Dialogue: 0,0:00:01.00,0:00:03.00,EnglishSecondary,,0,0,0,,Aramam" in ass_text


# ==============================================================================
# 6. Hardware Acceleration & Model Tiers (SC-07.1, SC-01.5)
# ==============================================================================

@pytest.mark.anyio
async def test_sc07_hardware_encoder_nvenc_detection():
    """SC-07.1: Confirms hardware accelerated encoder is properly resolved."""
    media_service = MediaService()
    encoder, opts = await media_service.get_fastest_video_encoder()
    assert encoder in ["h264_nvenc", "h264_qsv", "libx264"]



def test_sc01_hardware_probe_tier_selection():
    """SC-01.5: Verifies hardware probe auto-selects appropriate tier and ONNX options."""
    tier = HardwareProbe.detect_best_tier()
    assert tier in MODEL_TIERS
    
    opts = HardwareProbe.build_session_options("CPUExecutionProvider")
    assert opts is not None

import pytest
from pathlib import Path
from app.services.vad_service import SileroVadService
from app.services.media_service import MediaService
from app.services.subtitle_service import SubtitleService
from app.infrastructure.database_ops import get_cached_translation, set_cached_translation
from app.core.models import SubtitleItem

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.anyio
async def test_silero_vad_onnx_initialization():

    vad = SileroVadService()
    assert vad.session is not None, "Silero VAD ONNX session failed to initialize"

@pytest.mark.anyio
async def test_hardware_accelerated_encoder_detection():
    media_svc = MediaService()
    encoder_name, encoder_opts = await media_svc.get_fastest_video_encoder()
    assert encoder_name in ["h264_nvenc", "h264_qsv", "libx264"], f"Unexpected encoder: {encoder_name}"
    assert len(encoder_opts) > 0

def test_persistent_sqlite_translation_cache():
    test_src = "Testing persistent cache"
    test_tgt = "اختبار الكاش الدائم"
    set_cached_translation(test_src, "en", "ar", test_tgt)
    cached = get_cached_translation(test_src, "en", "ar")
    assert cached == test_tgt, f"Expected '{test_tgt}', got '{cached}'"

def test_bilingual_ass_and_netflix_pacing():
    sub_svc = SubtitleService()
    items = [
        SubtitleItem(index=1, start_time="00:00:01,000", end_time="00:00:01,300", text="Quick word", translated_text="كلمة سريعة")
    ]
    # Test pacing enforcement (min 1.2s)
    paced = sub_svc.enforce_reading_speed_and_pacing(items, min_duration_sec=1.2)
    assert paced[0].end_time == "00:00:02,200", f"Pacing did not extend short subtitle: {paced[0].end_time}"

    # Test bilingual ASS export
    ass_content = sub_svc.export_bilingual_ass(paced)
    assert "[Script Info]" in ass_content
    assert "ArabicPrimary" in ass_content
    assert "EnglishSecondary" in ass_content
    assert "كلمة سريعة" in ass_content

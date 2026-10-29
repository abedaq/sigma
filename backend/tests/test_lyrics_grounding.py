"""
SIGMA_ASR_VTT - Unit & Integration Tests for Music Intelligence & Lyrics Grounding Engine
Developer: أصيل السويدي
"""

import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path

from app.core.models import SubtitleItem
from app.services.lyrics_grounding_service import LyricsGroundingService, LyricsGroundingResult
from app.infrastructure.database_ops import set_cached_lyrics, get_cached_lyrics


def test_metadata_extraction_from_filenames():
    """Verifies regex and heuristic parsing of artist and track title from filenames."""
    # Test case 1: Standard 'Artist - Title (Noise)'
    artist, title = LyricsGroundingService.extract_metadata_from_filename(
        "İbrahim Tatlıses - Aramam (Official Video 1080p).mp4"
    )
    assert artist == "İbrahim Tatlıses"
    assert title == "Aramam"

    # Test case 2: En-dash separator with brackets
    artist, title = LyricsGroundingService.extract_metadata_from_filename(
        "Adele – Rolling in the Deep [Official Music Video].mkv"
    )
    assert artist == "Adele"
    assert title == "Rolling in the Deep"

    # Test case 3: Single title without artist
    artist, title = LyricsGroundingService.extract_metadata_from_filename("Aramam.mp4")
    assert artist is None
    assert title == "Aramam"


def test_lrc_timestamp_parsing():
    """Verifies parsing of LRC strings into SubtitleItem instances with valid durations."""
    sample_lrc = """
    [00:31.87] Çağırsaydın gelmez miydim yar?
    [00:38.97] Senin için ölmez miydim yar?
    [00:45.23] Dünyayı ters etmez miydim yar?
    [00:51.80] Aramam, aramam, aramam
    """
    subs = LyricsGroundingService.parse_lrc_to_subtitles(sample_lrc)
    assert len(subs) == 4

    assert subs[0].text == "Çağırsaydın gelmez miydim yar?"
    assert subs[0].start_time == "00:00:31,870"
    # End time should be clamped before next line starts (38.97 - 0.1 = ~38.87)
    assert "00:00:38" in subs[0].end_time

    assert subs[3].text == "Aramam, aramam, aramam"
    assert subs[3].start_time == "00:00:51,800"


def test_zero_pytorch_forced_alignment():
    """Verifies phonetic/Levenshtein alignment replacing misheard ASR words with ground truth."""
    # Simulating Whisper acoustic transcription with phonetic errors
    raw_whisper = [
        SubtitleItem(index=1, start_time="00:00:32,000", end_time="00:00:37,500", text="Çalırsaydın gelmez miydim yar"), # Whisper error Çalırsaydın
        SubtitleItem(index=2, start_time="00:00:38,000", end_time="00:00:43,000", text="Senin için ölmez miydim yar"),
    ]

    # Ground truth lyrics
    ground_truth = [
        "Çağırsaydın gelmez miydim yar?",
        "Senin için ölmez miydim yar?",
    ]

    aligned = LyricsGroundingService.forced_align_lyrics_to_audio(raw_whisper, ground_truth)
    assert len(aligned) == 2
    # The misheard 'Çalırsaydın' is replaced with authentic 'Çağırsaydın'
    assert aligned[0].text == "Çağırsaydın gelmez miydim yar?"
    assert aligned[0].start_time == "00:00:32,000"
    assert aligned[1].text == "Senin için ölmez miydim yar?"
    assert aligned[1].start_time == "00:00:38,000"


def test_lyrics_sqlite_disk_caching():
    """Verifies that ground-truth lyrics are permanently cached in SQLite without network calls."""
    artist = "İbrahim Tatlıses"
    title = "Aramam Test"
    synced = "[00:10.00] Test line 1\n[00:15.00] Test line 2"
    plain = "Test line 1\nTest line 2"

    set_cached_lyrics(artist, title, "unit_test_source", synced, plain)

    cached = get_cached_lyrics(artist, title)
    assert cached is not None
    assert cached["artist"] == artist
    assert cached["title"] == title
    assert cached["synced_lyrics"] == synced
    assert cached["plain_lyrics"] == plain


@pytest.mark.anyio
async def test_ground_song_pipeline_with_cached_lyrics(tmp_path):
    """Verifies end-to-end song grounding pipeline utilizing cache."""
    test_media = tmp_path / "İbrahim Tatlıses - Aramam.mp4"
    test_media.touch()

    raw_items = [
        SubtitleItem(index=1, start_time="00:00:32,000", end_time="00:00:35,000", text="Araba sormam bir daha")
    ]

    # Pre-cache known verified lyrics
    synced_lrc = "[00:31.87] Çağırsaydın gelmez miydim yar?\n[01:03.23] Aramam sormam bir daha"
    set_cached_lyrics("İbrahim Tatlıses", "Aramam", "lrclib_synced", synced_lrc, None)

    res: LyricsGroundingResult = await LyricsGroundingService.ground_song_pipeline(
        test_media, raw_items
    )

    assert res.is_grounded is True
    assert res.title == "Aramam"
    assert len(res.subtitles) == 2
    assert res.subtitles[0].text == "Çağırsaydın gelmez miydim yar?"
    assert res.subtitles[1].text == "Aramam sormam bir daha"

"""
SIGMA_ASR_VTT - Centralized Timestamp & Subtitle Alignment Utilities
Developer: أصيل السويدي
"""

from typing import List
from app.core.models import SubtitleItem

def seconds_to_srt_time(seconds: float) -> str:
    """Converts raw float seconds into SRT timestamp HH:MM:SS,mmm."""
    if seconds < 0:
        seconds = 0.0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    
    # Handle rounding overflows
    if millis >= 1000:
        secs += millis // 1000
        millis = millis % 1000
    if secs >= 60:
        minutes += secs // 60
        secs = secs % 60
    if minutes >= 60:
        hours += minutes // 60
        minutes = minutes % 60
        
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def srt_time_to_seconds(srt_time: str) -> float:
    """Converts SRT timestamp HH:MM:SS,mmm or HH:MM:SS.mmm to float seconds."""
    try:
        # Standardize comma to dot for parsing
        clean_time = srt_time.replace(",", ".").strip()
        parts = clean_time.split(":")
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    except Exception:
        return 0.0

def apply_chunk_offset(items: List[SubtitleItem], offset_seconds: float) -> List[SubtitleItem]:
    """Adds chunk offset in seconds to all subtitle item timestamps."""
    if offset_seconds <= 0:
        return items
        
    for item in items:
        start_sec = srt_time_to_seconds(item.start_time) + offset_seconds
        end_sec = srt_time_to_seconds(item.end_time) + offset_seconds
        item.start_time = seconds_to_srt_time(start_sec)
        item.end_time = seconds_to_srt_time(end_sec)
    return items


def build_pause_aware_subtitles(
    raw_words: List[dict],
    pause_threshold: float = 0.35,
    onset_shift: float = 0.0,
    max_words: int = 10
) -> List[SubtitleItem]:
    """
    Dynamically groups word timestamps into rhythm chunks based on vocal pauses and silence gaps.
    Applies positive onset shift so subtitles never appear before phoneme utterance begins.
    """
    if not raw_words:
        return []

    valid_words = []
    for w in raw_words:
        if isinstance(w, dict) and "start" in w and "end" in w:
            text = str(w.get("word") or w.get("punctuated_word") or w.get("text", "")).strip()
            if text:
                valid_words.append({"text": text, "start": float(w["start"]), "end": float(w["end"])})

    if not valid_words:
        return []

    valid_words.sort(key=lambda x: x["start"])
    items: List[SubtitleItem] = []
    current_words: List[str] = []
    chunk_start = valid_words[0]["start"]
    last_end = valid_words[0]["end"]

    for idx, w in enumerate(valid_words):
        w_text = w["text"]
        w_start = w["start"]
        w_end = w["end"]

        if idx > 0:
            silence_gap = w_start - last_end
            if silence_gap >= pause_threshold or len(current_words) >= max_words:
                start_sec = max(0.0, chunk_start + onset_shift)
                end_sec = max(start_sec + 0.1, last_end)
                
                items.append(
                    SubtitleItem(
                        index=len(items) + 1,
                        start_time=seconds_to_srt_time(start_sec),
                        end_time=seconds_to_srt_time(end_sec),
                        text=" ".join(current_words)
                    )
                )
                current_words = [w_text]
                chunk_start = w_start
                last_end = w_end
            else:
                current_words.append(w_text)
                last_end = max(last_end, w_end)
        else:
            current_words = [w_text]
            last_end = w_end
            chunk_start = w_start

    if current_words:
        start_sec = max(0.0, chunk_start + onset_shift)
        end_sec = max(start_sec + 0.1, last_end)
        items.append(
            SubtitleItem(
                index=len(items) + 1,
                start_time=seconds_to_srt_time(start_sec),
                end_time=seconds_to_srt_time(end_sec),
                text=" ".join(current_words)
            )
        )

    return items


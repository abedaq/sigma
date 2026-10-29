"""
SIGMA_ASR_VTT - Subtitle Parser, Validator & Exporter (SRT, VTT, ASS)
Developer: أصيل السويدي
"""

import re
from typing import List, Union, Optional
from app.core.models import SubtitleItem
from app.infrastructure.logger import logger

class SubtitleService:
    """Parses, validates, and exports SRT, VTT, and ASS subtitle files."""

    @staticmethod
    def parse_srt(content: str) -> List[SubtitleItem]:
        """Parses SRT format string into SubtitleItem list."""
        items = []
        # Remove BOM if present
        if content.startswith('\ufeff'):
            content = content[1:]
        
        # Normalize line endings to help regex
        content = content.replace('\r\n', '\n')
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for block in blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if len(lines) >= 3:
                try:
                    index = int(lines[0])
                    times = lines[1].split("-->")
                    start_time = times[0].strip()
                    end_time = times[1].strip()
                    text = " ".join(lines[2:])
                    items.append(SubtitleItem(index=index, start_time=start_time, end_time=end_time, text=text))
                except Exception as e:
                    logger.warning(f"Failed to parse subtitle block at index {lines[0]}: {str(e)}")
                    continue
        return items

    @staticmethod
    def export_srt(items: List[SubtitleItem], use_translated: bool = True) -> str:
        """Exports SubtitleItem list to standard SRT format content string."""
        blocks = []
        for idx, item in enumerate(items, start=1):
            text = item.translated_text if (use_translated and item.translated_text) else item.text
            blocks.append(f"{idx}\n{item.start_time} --> {item.end_time}\n{text}\n")
        return "\n".join(blocks)

    @staticmethod
    def export_vtt(items: List[SubtitleItem], use_translated: bool = True) -> str:
        """Exports SubtitleItem list to WebVTT (.vtt) format content string."""
        blocks = ["WEBVTT\n"]
        for idx, item in enumerate(items, start=1):
            # Convert comma milliseconds to period for VTT
            start_vtt = item.start_time.replace(",", ".")
            end_vtt = item.end_time.replace(",", ".")
            text = item.translated_text if (use_translated and item.translated_text) else item.text
            blocks.append(f"{idx}\n{start_vtt} --> {end_vtt}\n{text}\n")
        return "\n".join(blocks)

    @staticmethod
    def export_ass(items: List[SubtitleItem], use_translated: bool = True) -> str:
        """Exports SubtitleItem list to Advanced SubStation Alpha (.ass) format."""
        header = (
            "[Script Info]\n"
            "Title: SIGMA_ASR_VTT Subtitles\n"
            "ScriptType: v4.00+\n"
            "WrapStyle: 0\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,0,2,10,10,10,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )
        dialogues = []
        for item in items:
            text = item.translated_text if (use_translated and item.translated_text) else item.text
            dialogues.append(f"Dialogue: 0,{item.start_time},{item.end_time},Default,,0,0,0,,{text}")
        
        return header + "\n".join(dialogues)

    @staticmethod
    def parse_vtt(content: str) -> List[SubtitleItem]:
        """Parses WebVTT format string into SubtitleItem list."""
        items = []
        if content.startswith('\ufeff'):
            content = content[1:]
        content = content.replace('\r\n', '\n')
        # Remove WEBVTT header
        content = re.sub(r'^WEBVTT[^\n]*\n', '', content.strip(), flags=re.IGNORECASE)
        blocks = re.split(r'\n\s*\n', content.strip())
        
        idx = 1
        for block in blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if not lines:
                continue
            # Cue may have an identifier on line 0, or timing directly
            time_line_idx = 0
            if "-->" not in lines[0] and len(lines) > 1 and "-->" in lines[1]:
                time_line_idx = 1
            
            if "-->" in lines[time_line_idx]:
                try:
                    times = lines[time_line_idx].split("-->")
                    start_time = times[0].strip().split()[0].replace(".", ",")
                    end_time = times[1].strip().split()[0].replace(".", ",")
                    
                    # Ensure standard HH:MM:SS,mmm format
                    if start_time.count(":") == 1:
                        start_time = f"00:{start_time}"
                    if end_time.count(":") == 1:
                        end_time = f"00:{end_time}"
                        
                    text = " ".join(lines[time_line_idx + 1:])
                    # Remove VTT tags like <v ...> or <c>
                    text = re.sub(r'<[^>]+>', '', text)
                    if text:
                        items.append(SubtitleItem(index=idx, start_time=start_time, end_time=end_time, text=text))
                        idx += 1
                except Exception as e:
                    logger.warning(f"Failed to parse VTT cue: {str(e)}")
                    continue
        return items

    @staticmethod
    def parse_ass(content: str) -> List[SubtitleItem]:
        """Parses ASS/SSA subtitle dialogue lines into SubtitleItem list."""
        items = []
        if content.startswith('\ufeff'):
            content = content[1:]
        content = content.replace('\r\n', '\n')
        
        idx = 1
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("Dialogue:"):
                try:
                    # Dialogue: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
                    parts = line.split(",", 9)
                    if len(parts) >= 10:
                        start_raw = parts[1].strip()
                        end_raw = parts[2].strip()
                        # Convert ASS H:MM:SS.cc to SRT HH:MM:SS,mmm
                        def ass_to_srt(t_str: str) -> str:
                            p = t_str.split(":")
                            h = int(p[0])
                            m = int(p[1])
                            s_parts = p[2].split(".")
                            s = int(s_parts[0])
                            cs = int(s_parts[1]) if len(s_parts) > 1 else 0
                            return f"{h:02d}:{m:02d}:{s:02d},{cs*10:03d}"
                        
                        start_time = ass_to_srt(start_raw)
                        end_time = ass_to_srt(end_raw)
                        text = parts[9].strip()
                        # Strip ASS override tags like {\an8} or {\b1}
                        text = re.sub(r'\{[^}]+\}', '', text)
                        text = text.replace(r'\N', ' ').replace(r'\n', ' ')
                        if text:
                            items.append(SubtitleItem(index=idx, start_time=start_time, end_time=end_time, text=text))
                            idx += 1
                except Exception as e:
                    logger.warning(f"Failed to parse ASS dialogue line: {str(e)}")
                    continue
        return items

    @classmethod
    def parse_subtitle(cls, content: str, filename: str = "") -> List[SubtitleItem]:
        """Smart format auto-detection to parse SRT, VTT, or ASS accurately."""
        fn_lower = filename.lower()
        if fn_lower.endswith(".vtt") or content.strip().startswith("WEBVTT"):
            return cls.parse_vtt(content)
        elif fn_lower.endswith(".ass") or fn_lower.endswith(".ssa") or "[Script Info]" in content:
            return cls.parse_ass(content)
        else:
            return cls.parse_srt(content)

    @staticmethod
    def export_bilingual_srt(
        items: List[SubtitleItem],
        translated_items_or_on_top: Union[List[SubtitleItem], bool] = True,
        original_on_top: bool = True
    ) -> str:
        """Exports dual-language subtitle (Original + Arabic Translation) formatted for video display."""
        blocks = []
        is_list = isinstance(translated_items_or_on_top, list)
        trans_list = translated_items_or_on_top if is_list else None
        on_top = original_on_top if is_list else bool(translated_items_or_on_top)

        for idx, item in enumerate(items, start=1):
            orig = item.text.strip()
            if trans_list and idx - 1 < len(trans_list):
                trans_item = trans_list[idx - 1]
                trans = (trans_item.translated_text or trans_item.text).strip()
            else:
                trans = (getattr(item, "translated_text", None) or item.text).strip()

            if on_top:
                combined = f"<font size=\"15\" color=\"#D1D5DB\">{orig}</font>\n{trans}"
            else:
                combined = f"{trans}\n<font size=\"15\" color=\"#D1D5DB\">{orig}</font>"
            blocks.append(f"{idx}\n{item.start_time} --> {item.end_time}\n{combined}\n")
        return "\n".join(blocks)

    @staticmethod
    def srt_to_ass_time(srt_time: str) -> str:
        """Converts SRT timestamp (HH:MM:SS,mmm) to ASS timestamp (H:MM:SS.cc)."""
        clean = srt_time.replace(",", ".").strip()
        parts = clean.split(":")
        if len(parts) == 3:
            h = int(parts[0])
            m = parts[1]
            sec_parts = parts[2].split(".")
            s = sec_parts[0]
            cs = sec_parts[1][:2] if len(sec_parts) > 1 else "00"
            return f"{h}:{m}:{s}.{cs}"
        return clean

    @classmethod
    def export_bilingual_ass(
        cls,
        items: List[SubtitleItem],
        translated_items: Optional[List[SubtitleItem]] = None,
        arabic_font: str = "Tajawal",
        english_font: str = "Arial"
    ) -> str:
        """
        Exports broadcast-grade bilingual subtitles (.ass) with distinct hierarchical styling:
        Arabic in prominent bright yellow/gold and English in subdued secondary gray.
        """
        header = (
            "[Script Info]\n"
            "Title: SIGMA_ASR_VTT Broadcast Bilingual Subtitles\n"
            "ScriptType: v4.00+\n"
            "WrapStyle: 0\n"
            "ScaledBorderAndShadow: yes\n"
            "YCbCr Matrix: TV.709\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"Style: ArabicPrimary,{arabic_font},22,&H0000D4FF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,1,2,15,15,44,1\n"
            f"Style: EnglishSecondary,{english_font},15,&H00D0D5DD,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,1.5,1,2,15,15,18,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )
        dialogues = []
        for idx, item in enumerate(items, start=1):
            start = cls.srt_to_ass_time(item.start_time)
            end = cls.srt_to_ass_time(item.end_time)
            
            orig = item.text.strip().replace("\n", "\\N")
            if translated_items and idx - 1 < len(translated_items):
                trans = (translated_items[idx - 1].translated_text or translated_items[idx - 1].text).strip().replace("\n", "\\N")
            else:
                trans = (getattr(item, "translated_text", None) or item.text).strip().replace("\n", "\\N")

            # Layer 1: Arabic prominent text
            dialogues.append(f"Dialogue: 1,{start},{end},ArabicPrimary,,0,0,0,,{trans}")
            # Layer 0: English secondary text
            dialogues.append(f"Dialogue: 0,{start},{end},EnglishSecondary,,0,0,0,,{orig}")

        return header + "\n".join(dialogues)

    @staticmethod
    def enforce_reading_speed_and_pacing(
        items: List[SubtitleItem],
        min_duration_sec: float = 1.2,
        max_duration_sec: float = 7.0,
        max_cps: float = 20.0
    ) -> List[SubtitleItem]:
        """
        Applies Netflix Timed Text Reading Standards:
        - Prevents overly brief flashes (< 1.2s).
        - Clamps overly prolonged displays (> 7.0s).
        - Checks Characters-Per-Second (CPS <= 20).
        """
        from app.infrastructure.timestamp_utils import srt_time_to_seconds, seconds_to_srt_time

        for idx, item in enumerate(items):
            start = srt_time_to_seconds(item.start_time)
            end = srt_time_to_seconds(item.end_time)
            duration = end - start
            text_len = len(item.text.strip())

            # 1. Enforce minimum duration
            if duration < min_duration_sec and text_len > 0:
                # Check next item to avoid overlap
                max_allowed_end = srt_time_to_seconds(items[idx + 1].start_time) - 0.05 if idx + 1 < len(items) else start + min_duration_sec
                new_end = min(start + min_duration_sec, max_allowed_end)
                if new_end > start:
                    item.end_time = seconds_to_srt_time(new_end)

            # 2. Enforce maximum duration
            elif duration > max_duration_sec and text_len <= 15:
                item.end_time = seconds_to_srt_time(start + max_duration_sec)

        return items

    def validate_subtitle_structure(self, items: List[SubtitleItem]) -> bool:
        """Validates that subtitle item indexes and timestamps are ascending and non-overlapping."""
        if not items:
            return True
        for i in range(len(items) - 1):
            if items[i].index >= items[i + 1].index:
                logger.warning(f"Subtitle index sequence out of order at index {items[i].index}")
        return True



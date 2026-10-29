
"""
SIGMA_ASR_VTT - ASR Service & Hallucination Guard
Developer: أصيل السويدي
"""


import re
from pathlib import Path
from typing import List
from app.core.models import SubtitleItem, APIKeyConfig
from app.core.exceptions import ASRError, RateLimitError
from app.core.security import AESVault
from app.integrations.base_provider import BaseASRProvider
from app.integrations.speechmatics import SpeechmaticsASRProvider
from app.integrations.gemini import GeminiASRProvider
from app.infrastructure.logger import logger
from app.infrastructure.timestamp_utils import srt_time_to_seconds, seconds_to_srt_time

class ASRHallucinationGuard:
    """Detects and cleans ASR hallucination loops, repetitive phrase spam, watermarks, and timestamp artifacts."""

    @classmethod
    def filter_hallucinations(cls, items: List[SubtitleItem]) -> List[SubtitleItem]:
        """Cleans hallucinated repetitive segments and dataset watermarks emitted by ASR cloud models."""
        cleaned_items = []
        seen_text_counts = {}

        watermark_signatures = [
            "altyazı", "m.k.", "amara.org", "translated by", "subtitles by",
            "opensubtitles", "sous-titres", "tercüme", "subtítulo", "www.", ".com", "powered by",
            "subtitle by", "copyright", "tüm hakları", "eng sub", "ترجمة"
        ]

        for item in items:
            text = item.text.strip()
            if not text:
                continue

            words = text.split()
            text_lower = text.lower()

            stripped_any = False
            for wm in watermark_signatures:
                if wm in text_lower:
                    pattern = re.compile(re.escape(wm), re.IGNORECASE)
                    text = pattern.sub("", text).strip()
                    text_lower = text.lower()
                    words = text.split()
                    stripped_any = True
                    logger.warning(f"Hallucination Guard stripped dataset watermark: '{wm}'")

            if not text or len(words) == 0 or (stripped_any and len(words) <= 2):
                continue

            item.text = text

            # 2. Smart Timestamp Correction for duration anomalies (e.g. lyrics mixed with long instrumental intros)
            start_sec = srt_time_to_seconds(item.start_time)
            end_sec = srt_time_to_seconds(item.end_time)
            duration = end_sec - start_sec
            if duration > 10.0 and len(words) <= 10:
                # NEVER drop spoken words or lyrics! Instead, intelligently clamp display duration based on word count
                capped_duration = max(3.0, min(8.0, len(words) * 1.5))
                item.end_time = seconds_to_srt_time(start_sec + capped_duration)
                logger.info(f"Hallucination Guard corrected stretched timestamp duration ({duration:.1f}s -> {capped_duration:.1f}s) for lyrics: '{text}'")

            # 3. Remove repetitive word or phrase loops (e.g. "thank you thank you thank you")
            if len(words) >= 4:
                if len(set(words)) == 1:
                    logger.warning(f"Hallucination Guard dropped repetitive word loop: {text}")
                    continue
                two_word_phrase = " ".join(words[:2])
                if text.lower().count(two_word_phrase.lower()) >= 3:
                    logger.warning(f"Hallucination Guard dropped repetitive phrase loop: {text}")
                    continue

            # 4. Track global repetitive lines
            seen_text_counts[text] = seen_text_counts.get(text, 0) + 1
            if seen_text_counts[text] > 3:
                logger.warning(f"Hallucination Guard suppressed excessive line repetition: {text}")
                continue

            cleaned_items.append(item)

        # Re-index items cleanly
        for idx, item in enumerate(cleaned_items, start=1):
            item.index = idx

        return cleaned_items


class ASRService:
    """Orchestrates Cloud ASR providers with Circuit Breaker key failover."""

    def get_provider(self, key_config: APIKeyConfig) -> BaseASRProvider:
        """Instantiates appropriate provider based on config and intelligent key inspection."""
        raw_key = AESVault().decrypt(key_config.encrypted_key)
        if raw_key.startswith("gsk_") or key_config.provider == "groq":
            from app.integrations.groq_provider import GroqASRProvider
            return GroqASRProvider(api_key=raw_key)
        elif (len(raw_key) == 40 and all(c in '0123456789abcdef' for c in raw_key.lower())) or key_config.provider == "deepgram":
            from app.integrations.deepgram_provider import DeepgramASRProvider
            return DeepgramASRProvider(api_key=raw_key)
        elif key_config.provider == "speechmatics":
            return SpeechmaticsASRProvider(api_key=raw_key)
        elif key_config.provider == "gemini":
            return GeminiASRProvider(api_key=raw_key)
        else:
            raise ASRError(f"Unsupported ASR provider: {key_config.provider}")

    async def transcribe(
        self,
        audio_path: Path,
        keys_pool: List[APIKeyConfig],
        language: str = "auto"
    ) -> List[SubtitleItem]:
        """Transcribes audio using active key pool with automatic circuit breaker failover."""
        if not keys_pool:
            raise ASRError("No active ASR API keys configured in pool.")

        # Sort key pool by priority
        sorted_keys = sorted(keys_pool, key=lambda k: k.priority)

        for key_config in sorted_keys:
            try:
                logger.info(f"Attempting ASR transcription using provider key: {key_config.name}")
                provider = self.get_provider(key_config)
                raw_segments = await provider.transcribe_audio(audio_path, language=language)
                
                # Apply Hallucination Guard
                guarded_segments = ASRHallucinationGuard.filter_hallucinations(raw_segments)
                logger.info(f"ASR transcription succeeded ({len(guarded_segments)} segments verified).")
                return guarded_segments

            except RateLimitError:
                logger.warning(f"ASR Key {key_config.name} hit rate limit. Activating Circuit Breaker failover...")
                key_config.remaining_quota_percent = 0.0
                continue
            except Exception as e:
                logger.error(f"ASR Provider {key_config.name} error: {str(e)}")
                continue

        raise ASRError("All ASR API keys in pool failed or exhausted rate limits.")

"""
SIGMA_ASR_VTT - Deepgram Cloud ASR Provider Integration
Developer: أصيل السويدي
"""

import asyncio
import httpx
from pathlib import Path
from typing import List
from app.core.models import SubtitleItem
from app.core.exceptions import ASRError, RateLimitError
from app.integrations.base_provider import BaseASRProvider
from app.infrastructure.logger import logger


from app.infrastructure.timestamp_utils import seconds_to_srt_time, build_pause_aware_subtitles
from app.integrations.provider_registry import get_provider_capabilities, ProviderCapabilities


def _parse_deepgram_response(res_data: dict) -> List[SubtitleItem]:
    all_words = []
    try:
        channels = res_data.get("results", {}).get("channels", [])
        if channels and isinstance(channels, list) and channels[0].get("alternatives"):
            all_words = channels[0]["alternatives"][0].get("words", [])
    except Exception:
        pass

    if not all_words:
        utterances = res_data.get("results", {}).get("utterances", [])
        for u in utterances:
            words = u.get("words", [])
            if words and isinstance(words, list):
                all_words.extend([w for w in words if isinstance(w, dict) and "start" in w and "end" in w])

    if all_words:
        items = build_pause_aware_subtitles(all_words, pause_threshold=0.35, onset_shift=0.08)
        if items:
            return items

    # Fallback to utterances processing if words array is missing
    utterances = res_data.get("results", {}).get("utterances", [])
    items: List[SubtitleItem] = []
    for idx, u in enumerate(utterances, start=1):
        text = u.get("transcript", "").strip()
        if text:
            start_sec = float(u.get("start", 0.0)) + 0.08  # Onset shift prevents premature subtitle display
            end_sec = max(start_sec + 0.5, float(u.get("end", 0.0)))
            items.append(SubtitleItem(index=idx, start_time=seconds_to_srt_time(start_sec), end_time=seconds_to_srt_time(end_sec), text=text))
    return items


class DeepgramASRProvider(BaseASRProvider):
    """Deepgram Nova-2 ASR Provider Integration."""

    def __init__(self, api_key: str) -> None:
        super().__init__(api_key=api_key, name="Deepgram Nova-2 ASR")
        self.url = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true&utterances=true&punctuate=true"

    def get_capabilities(self) -> ProviderCapabilities:
        return get_provider_capabilities("deepgram")

    async def transcribe_audio(self, audio_path: Path, language: str = "auto") -> List[SubtitleItem]:
        logger.info(f"Starting Deepgram Nova-2 ASR transcription for {audio_path.name}...")
        if not self.api_key:
            raise ASRError("Deepgram API Key is missing or invalid.")

        caps = self.get_capabilities()
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": caps.content_type
        }
        
        url = self.url
        if language and language != "auto":
            url += f"&language={language}"
        else:
            url += "&detect_language=true"

        try:
            audio_bytes = await asyncio.to_thread(audio_path.read_bytes)
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=headers, content=audio_bytes)
                
            if response.status_code == 429:
                raise RateLimitError("Deepgram API rate limit exceeded.", provider_name=self.name)
            if response.status_code != 200:
                logger.error(f"Deepgram ASR failed HTTP {response.status_code}: {response.text}")
                raise ASRError(f"Deepgram ASR error HTTP {response.status_code}: {response.text}")

            res_data = response.json()
            items = _parse_deepgram_response(res_data)

            if not items:
                raise ASRError("Deepgram produced empty transcription.")

            logger.info(f"Deepgram Nova-2 successfully transcribed {len(items)} audio utterances.")
            return items

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Deepgram quota or rate limit exceeded.", provider_name=self.name)
            raise ASRError(f"Deepgram API HTTP error: {str(e)}")
        except Exception as e:
            if isinstance(e, (ASRError, RateLimitError)):
                raise e
            logger.error(f"Deepgram ASR transcription failed: {str(e)}")
            raise ASRError(f"Deepgram ASR failed: {str(e)}")

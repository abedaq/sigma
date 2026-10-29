"""
SIGMA_ASR_VTT - Gemini Audio ASR & LLM Translation Provider Integration
Developer: أصيل السويدي
"""

import base64
import httpx
from pathlib import Path
from typing import List, Dict, Optional
from app.core.models import SubtitleItem
from app.core.exceptions import ASRError, TranslationError, RateLimitError
from app.integrations.base_provider import BaseASRProvider, BaseTranslationProvider
from app.infrastructure.logger import logger
from app.integrations.provider_registry import get_provider_capabilities, ProviderCapabilities


class GeminiASRProvider(BaseASRProvider):
    """Gemini Multimodal Audio ASR Provider Integration."""

    def __init__(self, api_key: str) -> None:
        super().__init__(api_key=api_key, name="Gemini ASR")
        self.endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def get_capabilities(self) -> ProviderCapabilities:
        return get_provider_capabilities("gemini")

    async def transcribe_audio(self, audio_path: Path, language: str = "auto") -> List[SubtitleItem]:
        logger.info(f"Starting real Gemini Cloud Audio ASR for {audio_path.name}...")
        if not self.api_key:
            raise ASRError("Gemini API Key is missing.")

        url = f"{self.endpoint}?key={self.api_key}"
        
        try:
            audio_bytes = audio_path.read_bytes()
            # If audio size > 20MB, skip inline to avoid 413 payload limit
            if len(audio_bytes) > 20 * 1024 * 1024:
                raise ASRError("Audio file exceeds inline size limit for Gemini API (max 20MB per chunk).")

            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            
            prompt = (
                "Listen carefully to this audio and produce accurate, verbatim subtitles with start and end timestamps in standard SRT format.\n"
                f"Audio language: {language if language != 'auto' else 'detect automatically'}.\n"
                "Output strictly in standard SRT format without markdown fences or pleasantries."
            )

            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inlineData": {
                                    "mimeType": "audio/wav",
                                    "data": audio_b64
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.0
                }
            }

            async with httpx.AsyncClient(timeout=90.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 429:
                    raise RateLimitError("Gemini ASR quota exceeded or rate limited.", provider_name=self.name)
                if res.status_code != 200:
                    raise ASRError(f"Gemini ASR HTTP {res.status_code}: {res.text}")

                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]

            from app.services.subtitle_service import SubtitleService
            items = SubtitleService.parse_srt(text)
            if not items:
                raise ASRError("Gemini did not return valid SRT timestamps.")
            return items

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Gemini ASR rate limit hit.", provider_name=self.name)
            raise ASRError(f"Gemini ASR error: {str(e)}")
        except Exception as e:
            if isinstance(e, (ASRError, RateLimitError)):
                raise e
            logger.error(f"Gemini ASR failed: {e}")
            raise ASRError(f"Gemini ASR failed: {str(e)}")


class GeminiTranslationProvider(BaseTranslationProvider):
    """Gemini Context-Aware LLM Subtitle Translation Provider."""

    def __init__(self, api_key: str) -> None:
        super().__init__(api_key=api_key, name="Gemini Translation")
        self.endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def _build_system_prompt(self, source_lang: str, target_lang: str, glossary: Optional[Dict[str, str]], profile_prompt: Optional[str]) -> str:
        terms = ", ".join([f"'{k}' -> '{v}'" for k, v in glossary.items()]) if glossary else ""
        glossary_text = f"\nMandatory Terminology Glossary: {terms}." if terms else ""
        style_text = f"\nStyle Profile: {profile_prompt}." if profile_prompt else ""
        return (
            f"You are a master literary and subtitle translator translating from {source_lang} to {target_lang}.\n"
            f"Translate each numbered subtitle line into eloquent, natural, grammatically immaculate {target_lang}.\n"
            "CRITICAL RULES:\n"
            "1. Output ONLY the numbered translated lines in the exact format: '1. Translated text'.\n"
            "2. ZERO LINE MERGING: Never merge lines. Translate each numbered line separately to preserve video synchronization.\n"
            f"3. Entire output MUST be in {target_lang}. Never leave foreign words unless protected by glossary.\n"
            "4. POETIC & EMOTIONAL DEPTH: For songs or dramatic movies, translate with musical rhythm and emotional flow.\n"
            f"{glossary_text}{style_text}"
        )

    def _parse_gemini_translations(self, content: str, items: List[SubtitleItem], glossary: Optional[Dict[str, str]]) -> List[SubtitleItem]:
        trans_dict = {}
        for line in content.strip().split('\n'):
            line = line.strip()
            if '.' in line:
                parts = line.split('.', 1)
                if parts[0].strip().isdigit():
                    trans_dict[int(parts[0].strip())] = parts[1].strip()

        translated_items = []
        for item in items:
            t_text = trans_dict.get(item.index, item.text)
            if glossary:
                for src_term, tgt_term in glossary.items():
                    if src_term.lower() in item.text.lower() or src_term.lower() in t_text.lower():
                        t_text = t_text.replace(src_term, tgt_term)
            translated_items.append(
                SubtitleItem(
                    index=item.index,
                    start_time=item.start_time,
                    end_time=item.end_time,
                    text=item.text,
                    translated_text=t_text
                )
            )
        return translated_items

    async def translate_items(
        self,
        items: List[SubtitleItem],
        source_lang: str,
        target_lang: str,
        glossary: Optional[Dict[str, str]] = None,
        profile_prompt: Optional[str] = None
    ) -> List[SubtitleItem]:
        logger.info(f"Translating batch of {len(items)} items using real Gemini API ({source_lang} -> {target_lang})...")
        if not self.api_key:
            raise TranslationError("Gemini API Key is missing.")

        url = f"{self.endpoint}?key={self.api_key}"
        lines_text = "\n".join([f"{item.index}. {item.text}" for item in items])
        system_instruction = self._build_system_prompt(source_lang, target_lang, glossary, profile_prompt)

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{system_instruction}\n\nLines to translate:\n{lines_text}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2
            }
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 429:
                    raise RateLimitError("Gemini API rate limit exceeded.", provider_name=self.name)
                if res.status_code != 200:
                    logger.error(f"Gemini Translation HTTP {res.status_code}: {res.text}")
                    raise TranslationError(f"Gemini API returned HTTP {res.status_code}")

                data = res.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]

            return self._parse_gemini_translations(raw_text, items, glossary)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Gemini rate limit exceeded.", provider_name=self.name)
            raise TranslationError(f"Gemini API error: {str(e)}")
        except Exception as e:
            if isinstance(e, (TranslationError, RateLimitError)):
                raise e
            logger.error(f"Gemini translation failed: {e}")
            raise TranslationError(f"Gemini translation failed: {str(e)}")

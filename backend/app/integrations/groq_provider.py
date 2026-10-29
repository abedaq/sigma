"""
SIGMA_ASR_VTT - Groq Whisper ASR & Llama Translation Provider Integration
Developer: أصيل السويدي
"""

import asyncio
import httpx
from pathlib import Path
from typing import List, Dict, Optional
from app.core.models import SubtitleItem
from app.core.exceptions import ASRError, TranslationError, RateLimitError
from app.integrations.base_provider import BaseASRProvider, BaseTranslationProvider
from app.infrastructure.logger import logger


from app.infrastructure.timestamp_utils import seconds_to_srt_time, build_pause_aware_subtitles
from app.integrations.provider_registry import get_provider_capabilities, ProviderCapabilities


def _parse_groq_whisper_segments(res_data: dict) -> List[SubtitleItem]:
    segments = res_data.get("segments", [])
    if not segments:
        text = res_data.get("text", "").strip()
        if not text:
            raise ASRError("No transcription generated from audio.")
        return [SubtitleItem(index=1, start_time="00:00:00,080", end_time="00:00:10,000", text=text)]
    
    # Collect all words across root response or segments for dynamic vocal-pause chunking & positive onset shift
    all_words = []
    if isinstance(res_data.get("words"), list):
        all_words.extend([w for w in res_data["words"] if isinstance(w, dict) and "start" in w and "end" in w])
        
    if not all_words:
        for seg in segments:
            words = seg.get("words", [])
            if words and isinstance(words, list):
                all_words.extend([w for w in words if isinstance(w, dict) and "start" in w and "end" in w])
                    
    if all_words:
        items = build_pause_aware_subtitles(all_words, pause_threshold=0.35, onset_shift=0.08)
        if items:
            return items

    # Fallback to segment processing with onset shift if word timestamps are missing
    items: List[SubtitleItem] = []
    for idx, seg in enumerate(segments, start=1):
        text = seg.get("text", "").strip()
        if text:
            start_sec = float(seg.get("start", 0.0)) + 0.08  # Onset shift prevents premature subtitle display
            end_sec = max(start_sec + 0.5, float(seg.get("end", 0.0)))
            start_time = seconds_to_srt_time(start_sec)
            end_time = seconds_to_srt_time(end_sec)
            items.append(SubtitleItem(index=idx, start_time=start_time, end_time=end_time, text=text))
    return items


class GroqASRProvider(BaseASRProvider):
    """Groq Cloud Whisper ASR Provider Integration."""

    def __init__(self, api_key: str) -> None:
        super().__init__(api_key=api_key, name="Groq Whisper ASR")
        self.url = "https://api.groq.com/openai/v1/audio/transcriptions"

    def get_capabilities(self) -> ProviderCapabilities:
        return get_provider_capabilities("groq")

    async def transcribe_audio(self, audio_path: Path, language: str = "auto") -> List[SubtitleItem]:
        logger.info(f"Starting real Groq Whisper ASR transcription for {audio_path.name}...")
        if not self.api_key:
            raise ASRError("Groq API Key is missing or invalid.")

        headers = {"Authorization": f"Bearer {self.api_key}"}
        caps = self.get_capabilities()
        
        try:
            audio_bytes = await asyncio.to_thread(audio_path.read_bytes)
            async with httpx.AsyncClient(timeout=120.0) as client:
                files = {"file": (audio_path.name, audio_bytes, caps.content_type)}
                data = {
                    "model": "whisper-large-v3",
                    "response_format": "verbose_json",
                    "timestamp_granularities[]": ["segment", "word"]
                }
                if language and language != "auto":
                    data["language"] = language
                    
                response = await client.post(self.url, headers=headers, files=files, data=data)
                
            if response.status_code == 429:
                raise RateLimitError("Groq API rate limit exceeded.", provider_name=self.name)
            if response.status_code != 200:
                logger.error(f"Groq ASR failed HTTP {response.status_code}: {response.text}")
                raise ASRError(f"Groq ASR error HTTP {response.status_code}: {response.text}")

            res_data = response.json()
            items = _parse_groq_whisper_segments(res_data)

            logger.info(f"Groq Whisper successfully transcribed {len(items)} audio segments.")
            return items

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Groq quota or rate limit exceeded.", provider_name=self.name)
            raise ASRError(f"Groq API HTTP error: {str(e)}")
        except Exception as e:
            if isinstance(e, (ASRError, RateLimitError)):
                raise e
            logger.error(f"Groq ASR transcription failed: {str(e)}")
            raise ASRError(f"Groq ASR failed: {str(e)}")


class GroqTranslationProvider(BaseTranslationProvider):
    """Groq Context-Aware Llama Subtitle Translation Provider."""

    def __init__(self, api_key: str) -> None:
        super().__init__(api_key=api_key, name="Groq Llama Translation")
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def _build_system_prompt(self, source_lang: str, target_lang: str, glossary: Optional[Dict[str, str]], profile_prompt: Optional[str]) -> str:
        terms = ", ".join([f"'{k}' -> '{v}'" for k, v in glossary.items()]) if glossary else ""
        glossary_text = f"\nMandatory Terminology Glossary: {terms}." if terms else ""
        style_text = f"\nStyle Profile: {profile_prompt}." if profile_prompt else ""
        return (
            f"You are an expert film, literature, and music subtitle translator translating from {source_lang} into {target_lang}.\n"
            f"Translate each numbered subtitle line into eloquent, precise, idiomatic, and grammatically immaculate language in EXACTLY {target_lang}.\n"
            "CRITICAL TRANSLATION & MUSICAL RHYTHM RULES:\n"
            "1. Maintain the exact formatting and numbering (e.g. '1. Translated text').\n"
            "2. ZERO LINE MERGING: Each numbered input line represents a distinct rhythmic phrase or vocal burst separated by musical or vocal pauses. NEVER combine or blend adjacent lines! Translate each numbered line individually so it syncs one-to-one with the exact spoken/sung rhythm.\n"
            "3. Do not add conversational filler, introductions, or explanations. Output ONLY the translated numbered list.\n"
            f"4. The entire translation MUST be completely in {target_lang}. Do NOT leave any words, terms, or letters in {source_lang} or English.\n"
            "5. POETIC & MUSICAL ARTISTRY: When translating songs, drama, or emotional dialogue, translate with artistic elegance, emotional depth, and flowing musical rhyme/rhythm suitable for lyrics. AVOID dry, literal, cold journalistic or news-style language! (e.g., translate lyric poetry with soul and vocal rhythm rather than word-for-word prose).\n"
            "6. GRAMMATICAL & PRONOUN ACCURACY: Strictly preserve pronoun directions (distinguish clearly between 'you return' vs 'I return') and enforce correct gender agreement in verb conjugations and nouns.\n"
            "7. CONTEXT-AWARE ASR RECOVERY: If an input line contains minor phonetic typos or fragmented words from audio transcription, deduce the intended poetic meaning from surrounding context without merging the line timing."
            f"{glossary_text}{style_text}"
        )

    def _parse_groq_translations(self, content: str, items: List[SubtitleItem], glossary: Optional[Dict[str, str]]) -> List[SubtitleItem]:
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
                    if src_term.lower() in t_text.lower() or src_term in item.text:
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
        logger.info(f"Translating batch of {len(items)} items using Groq Llama ({source_lang} -> {target_lang})...")
        if not self.api_key:
            raise TranslationError("Groq API Key is missing.")

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        lines_text = "\n".join([f"{item.index}. {item.text}" for item in items])
        system_prompt = self._build_system_prompt(source_lang, target_lang, glossary, profile_prompt)
        models_to_try = [
            "qwen/qwen3.8-27b",
            "allam-2-7b",
            "openai/gpt-oss-120b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant"
        ]
        content = None



        async with httpx.AsyncClient(timeout=45.0) as client:
            for model_name in models_to_try:
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": lines_text}
                    ],
                    "temperature": 0.2
                }
                res = await client.post(self.url, headers=headers, json=payload)
                if res.status_code == 429:
                    raise RateLimitError("Groq Translation rate limit exceeded.")
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    break
                logger.warning(f"Groq Translation with model {model_name} returned HTTP {res.status_code}: {res.text[:100]}")

        if not content:
            raise TranslationError("Groq Translation failed on all configured models.")

        return self._parse_groq_translations(content, items, glossary)

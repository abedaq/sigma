"""
SIGMA_ASR_VTT - Context Translation Service & Glossary Middleware
Developer: أصيل السويدي
"""

from typing import List, Dict, Optional
from app.core.models import SubtitleItem, APIKeyConfig
from app.core.exceptions import RateLimitError
from app.core.security import AESVault
from app.integrations.base_provider import BaseTranslationProvider
from app.integrations.gemini import GeminiTranslationProvider
from app.integrations.google_translate import GoogleTranslationProvider
from app.infrastructure.logger import logger
from app.infrastructure.database_ops import (
    get_cached_translation,
    set_cached_translation,
    get_cached_translations_batch,
    set_cached_translations_batch,
    _make_cache_key
)

class TranslationService:
    """Handles context-aware sliding window translation with dynamic glossary injection and persistent cache."""

    def get_provider(self, key_config: APIKeyConfig) -> BaseTranslationProvider:
        raw_key = AESVault().decrypt(key_config.encrypted_key)
        if raw_key.startswith("gsk_") or key_config.provider == "groq":
            from app.integrations.groq_provider import GroqTranslationProvider
            return GroqTranslationProvider(api_key=raw_key)
        elif (len(raw_key) == 40 and all(c in '0123456789abcdef' for c in raw_key.lower())) or key_config.provider == "deepgram":
            return GoogleTranslationProvider(api_key="")
        elif key_config.provider == "gemini":
            return GeminiTranslationProvider(api_key=raw_key)
        elif key_config.provider == "google_translate":
            return GoogleTranslationProvider(api_key=raw_key)
        else:
            return GoogleTranslationProvider(api_key="")

    # Global in-memory translation cache (saves LLM tokens for repeated lines, songs refrains, and common phrases)
    _translation_cache: Dict[str, str] = {}

    async def translate_subtitles(
        self,
        items: List[SubtitleItem],
        keys_pool: List[APIKeyConfig],
        source_lang: str = "auto",
        target_lang: str = "ar",
        glossary: Optional[Dict[str, str]] = None,
        profile_prompt: Optional[str] = None,
        chunk_size: int = 25
    ) -> List[SubtitleItem]:
        """Translates subtitles in sliding window batches while preserving timestamps and context."""
        if not items:
            return []

        logger.info(f"Translating {len(items)} items into {target_lang} with chunk size {chunk_size} (Token-Optimized)...")
        
        # 1. Warm in-memory cache from persistent SQLite disk cache via batch query
        uncached_items = [
            it for it in items
            if f"{target_lang}:{it.text.strip().lower()}" not in self._translation_cache
        ]
        if uncached_items:
            batch_cached = get_cached_translations_batch(
                [it.text for it in uncached_items], source_lang, target_lang
            )
            for it in uncached_items:
                ck = f"{target_lang}:{it.text.strip().lower()}"
                mk = _make_cache_key(it.text, source_lang, target_lang)
                if mk in batch_cached:
                    self._translation_cache[ck] = batch_cached[mk]

        # Batch items into sliding window context chunks
        chunks = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
        translated_items: List[SubtitleItem] = []

        sorted_keys = sorted(keys_pool, key=lambda k: k.priority) if keys_pool else []

        for chunk in chunks:
            needed_translation = []
            for it in chunk:
                cache_key = f"{target_lang}:{it.text.strip().lower()}"
                if cache_key not in self._translation_cache:
                    needed_translation.append(it)

            if needed_translation:
                translated_needed = await self._translate_single_chunk(
                    needed_translation, sorted_keys, source_lang, target_lang, glossary, profile_prompt
                )
                new_cache_entries = []
                for it in translated_needed:
                    if it.translated_text and it.translated_text.strip() and it.translated_text.strip() != it.text.strip():
                        self._translation_cache[f"{target_lang}:{it.text.strip().lower()}"] = it.translated_text
                        new_cache_entries.append((it.text, source_lang, target_lang, it.translated_text))
                if new_cache_entries:
                    set_cached_translations_batch(new_cache_entries)
            else:
                logger.info(f"⚡ Token Saver: Reused cached translations for {len(chunk)} items without external call!")

            for it in chunk:
                cached_text = self._translation_cache.get(f"{target_lang}:{it.text.strip().lower()}", it.text)
                translated_items.append(SubtitleItem(
                    index=it.index,
                    start_time=it.start_time,
                    end_time=it.end_time,
                    text=it.text,
                    translated_text=cached_text
                ))


        logger.info(f"Successfully translated {len(translated_items)} subtitle items.")
        return translated_items


    async def _translate_single_chunk(
        self,
        chunk: List[SubtitleItem],
        sorted_keys: List[APIKeyConfig],
        source_lang: str,
        target_lang: str,
        glossary: Optional[Dict[str, str]],
        profile_prompt: Optional[str]
    ) -> List[SubtitleItem]:
        for key_config in sorted_keys:
            try:
                provider = self.get_provider(key_config)
                res = await provider.translate_items(
                    items=chunk,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    glossary=glossary,
                    profile_prompt=profile_prompt
                )
                if res:
                    return res
            except RateLimitError:
                logger.warning(f"Translation key {key_config.name} rate limited. Trying next key...")
            except Exception as e:
                logger.error(f"Translation provider {key_config.name} error: {str(e)}")

        fallback_provider = GoogleTranslationProvider(api_key="")
        return await fallback_provider.translate_items(
            items=chunk,
            source_lang=source_lang,
            target_lang=target_lang,
            glossary=glossary,
            profile_prompt=profile_prompt
        )

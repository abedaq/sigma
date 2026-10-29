"""
SIGMA_ASR_VTT - Google Translation API Provider Integration
Developer: أصيل السويدي
"""

import asyncio
import httpx
from typing import List, Dict, Optional
from app.core.models import SubtitleItem
from app.integrations.base_provider import BaseTranslationProvider
from app.infrastructure.logger import logger

class GoogleTranslationProvider(BaseTranslationProvider):
    """Google Translation Cloud API Provider Integration."""

    def __init__(self, api_key: str = "") -> None:
        super().__init__(api_key=api_key, name="Google Translate")

    def _apply_glossary(self, text: str, original_text: str, glossary: Optional[Dict[str, str]]) -> str:
        if not glossary:
            return text
        result = text
        for src_term, tgt_term in glossary.items():
            if src_term.lower() in original_text.lower() or src_term.lower() in result.lower():
                result = result.replace(src_term, tgt_term)
        return result

    async def _fetch_single_translation(self, client: httpx.AsyncClient, text: str, sl: str, tl: str, idx: int) -> str:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": sl, "tl": tl, "dt": "t", "q": text}
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        try:
            res = await client.get(url, params=params, headers=headers)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and data and data[0]:
                    translated = "".join([chunk[0] for chunk in data[0] if chunk and chunk[0]])
                    if translated.strip():
                        return translated
        except Exception:
            pass

        # Resilient Cloud Fallback: Translation Memory (MyMemory API)
        try:
            pair = f"{sl}|{tl}"
            mm_res = await client.get("https://api.mymemory.translated.net/get", params={"q": text, "langpair": pair})
            if mm_res.status_code == 200:
                mm_data = mm_res.json()
                trans_text = mm_data.get("responseData", {}).get("translatedText")
                if trans_text and trans_text.strip() and not trans_text.startswith("MYMEMORY WARNING:"):
                    return trans_text.strip()
        except Exception as mm_err:
            logger.debug(f"MyMemory fallback notice for item {idx}: {mm_err}")

        return text


    async def translate_items(
        self,
        items: List[SubtitleItem],
        source_lang: str,
        target_lang: str,
        glossary: Optional[Dict[str, str]] = None,
        profile_prompt: Optional[str] = None
    ) -> List[SubtitleItem]:
        logger.info(f"Translating {len(items)} items into {target_lang} using Google Translate API (Adaptive Concurrency)...")
        sl = source_lang if source_lang and source_lang != "auto" else "auto"
        sem = asyncio.Semaphore(3)

        async def _translate_one(client: httpx.AsyncClient, item: SubtitleItem) -> SubtitleItem:
            async with sem:
                await asyncio.sleep(0.04)
                translated_text = await self._fetch_single_translation(client, item.text, sl, target_lang, item.index)
                translated_text = self._apply_glossary(translated_text, item.text, glossary)
                return SubtitleItem(
                    index=item.index,
                    start_time=item.start_time,
                    end_time=item.end_time,
                    text=item.text,
                    translated_text=translated_text
                )


        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = [_translate_one(client, item) for item in items]
            translated_items = await asyncio.gather(*tasks)

        return list(translated_items)


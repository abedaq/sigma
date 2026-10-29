"""
SIGMA_ASR_VTT - Abstract Provider Interfaces
Developer: أصيل السويدي
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional
from app.core.models import SubtitleItem
from app.integrations.provider_registry import ProviderCapabilities

class BaseASRProvider(ABC):
    """Abstract interface for all Cloud ASR Providers (Speechmatics, Gemini Audio, Google ASR)."""
    
    def __init__(self, api_key: str, name: str = "Cloud ASR") -> None:
        self.api_key = api_key
        self.name = name

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Returns the specific capabilities of this ASR provider."""
        pass

    @abstractmethod
    async def transcribe_audio(self, audio_path: Path, language: str = "auto") -> List[SubtitleItem]:
        """Transcribes audio file to timestamped subtitle items."""
        pass


class BaseTranslationProvider(ABC):
    """Abstract interface for all Translation Providers (Gemini, Google Translate)."""

    def __init__(self, api_key: str, name: str = "Translation Provider") -> None:
        self.api_key = api_key
        self.name = name

    @abstractmethod
    async def translate_items(
        self,
        items: List[SubtitleItem],
        source_lang: str,
        target_lang: str,
        glossary: Optional[Dict[str, str]] = None,
        profile_prompt: Optional[str] = None
    ) -> List[SubtitleItem]:
        """Translates a list of subtitle items while preserving context and timestamps."""
        pass

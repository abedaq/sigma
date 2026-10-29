"""
SIGMA_ASR_VTT - Provider Capabilities Registry
Developer: أصيل السويدي
"""

from typing import Dict
from pydantic import BaseModel

class ProviderCapabilities(BaseModel):
    provider_name: str
    upload_format: str         # "wav" or "flac"
    content_type: str          # "audio/wav" or "audio/flac"
    max_file_mb: int           # Maximum file size in MB (e.g. 25 for Groq)
    supports_word_timestamps: bool
    supports_diarization: bool
    supports_translation: bool

PROVIDER_CAPABILITIES: Dict[str, ProviderCapabilities] = {
    "groq": ProviderCapabilities(
        provider_name="groq",
        upload_format="wav",
        content_type="audio/wav",
        max_file_mb=25,
        supports_word_timestamps=True,
        supports_diarization=False,
        supports_translation=True
    ),
    "deepgram": ProviderCapabilities(
        provider_name="deepgram",
        upload_format="flac",
        content_type="audio/flac",
        max_file_mb=2000,
        supports_word_timestamps=True,
        supports_diarization=True,
        supports_translation=True
    ),
    "speechmatics": ProviderCapabilities(
        provider_name="speechmatics",
        upload_format="wav",
        content_type="audio/wav",
        max_file_mb=500,
        supports_word_timestamps=True,
        supports_diarization=True,
        supports_translation=True
    ),
    "gemini": ProviderCapabilities(
        provider_name="gemini",
        upload_format="wav",
        content_type="audio/wav",
        max_file_mb=200,
        supports_word_timestamps=False,
        supports_diarization=False,
        supports_translation=True
    )
}

def get_provider_capabilities(provider: str) -> ProviderCapabilities:
    """Returns capabilities for the specified provider, falling back to groq/wav default."""
    prov_key = provider.lower().strip()
    if prov_key in PROVIDER_CAPABILITIES:
        return PROVIDER_CAPABILITIES[prov_key]
    
    # Safest default fallback
    return ProviderCapabilities(
        provider_name=provider,
        upload_format="wav",
        content_type="audio/wav",
        max_file_mb=25,
        supports_word_timestamps=False,
        supports_diarization=False,
        supports_translation=True
    )

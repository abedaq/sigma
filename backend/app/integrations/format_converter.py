"""
SIGMA_ASR_VTT - Audio Format Converter
Developer: أصيل السويدي
"""

import shutil
from pathlib import Path
from typing import Tuple
from app.infrastructure.process_manager import SafeProcessManager
from app.integrations.provider_registry import get_provider_capabilities
from app.infrastructure.logger import logger

class FormatConverter:
    """Converts internal WAV audio into provider-preferred formats (e.g. FLAC)."""

    def __init__(self) -> None:
        self.process_manager = SafeProcessManager()

    async def prepare_for_upload(self, wav_path: Path, provider: str, output_dir: Path) -> Tuple[Path, str]:
        """Converts wav_path to provider's upload_format and returns (path_to_file, content_type)."""
        caps = get_provider_capabilities(provider)
        
        # If target format is already WAV, return original
        if caps.upload_format == "wav":
            return wav_path, caps.content_type

        # If provider prefers FLAC (like Deepgram) for bandwidth optimization
        if caps.upload_format == "flac":
            flac_path = output_dir / f"{wav_path.stem}.flac"
            
            ffmpeg_binary = shutil.which("ffmpeg") or "ffmpeg"
            cmd = [
                ffmpeg_binary,
                "-y",
                "-i", str(wav_path),
                "-c:a", "flac",
                str(flac_path)
            ]
            
            logger.info(f"Converting internal WAV to FLAC lossless for ASR provider: {provider}...")
            try:
                await self.process_manager.run_command(cmd)
                if not flac_path.exists() or flac_path.stat().st_size == 0:
                    logger.warning("FLAC conversion produced empty file, falling back to original WAV.")
                    return wav_path, "audio/wav"
                return flac_path, caps.content_type
            except Exception as e:
                logger.error(f"FLAC conversion failed, falling back to WAV: {str(e)}")
                return wav_path, "audio/wav"

        # Safe fallback
        return wav_path, "audio/wav"

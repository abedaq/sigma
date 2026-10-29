"""
SIGMA_ASR_VTT - Media Extraction Service & Temp Sandbox Manager
Developer: أصيل السويدي
"""

import uuid
import shutil
from pathlib import Path
from typing import Tuple, Optional, List
from app.core.config import settings
from app.core.constants import AudioMode
from app.core.exceptions import FileProcessingError
from app.infrastructure.process_manager import (
    SafeProcessManager,
    FileInspector,
    FFMPEG_BINARY,
)
from app.infrastructure.logger import logger


class MediaService:
    """Handles secure audio extraction (16kHz WAV PCM S16LE) and temp directory sandbox lifecycles."""

    def __init__(self) -> None:
        self.process_manager = SafeProcessManager()

    def create_job_sandbox(self) -> Tuple[str, Path]:
        """Creates an isolated UUID temp directory for job execution."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        sandbox_dir = settings.TEMP_DIR / job_id
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"Created isolated sandboxed directory for job {job_id}: {sandbox_dir}"
        )
        return job_id, sandbox_dir

    def purge_job_sandbox(self, sandbox_dir: Path) -> None:
        """Purges temporary job sandbox directory safely upon completion or cancellation."""
        if sandbox_dir and sandbox_dir.exists() and sandbox_dir.is_dir():
            try:
                shutil.rmtree(sandbox_dir)
                logger.info(f"Cleaned up sandboxed temporary directory: {sandbox_dir}")
            except Exception as e:
                logger.warning(
                    f"Failed to purge temp directory {sandbox_dir}: {str(e)}"
                )

    async def extract_audio_for_api(
        self,
        video_path: Path,
        output_dir: Path,
        audio_mode: AudioMode = AudioMode.STANDARD,
    ) -> Path:
        """Extracts and optimizes audio to 16kHz WAV PCM format for Cloud ASR API upload."""
        FileInspector.validate_file_bytes(video_path)

        output_audio_path = output_dir / f"{video_path.stem}_audio.wav"

        # Determine channel mapping
        channels = "1"
        if audio_mode == AudioMode.MULTICHANNEL:
            channels = "2"

        # Base conversion command using lossless PCM signed 16-bit little-endian WAV
        cmd = [
            FFMPEG_BINARY,
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-ac",
            channels,
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            "-f",
            "wav",
        ]

        # Apply EBU R128 dynamic normalization & highpass filter only if explicitly requested
        if audio_mode == AudioMode.ENHANCED:
            cmd.extend(["-af", "highpass=f=80,loudnorm=I=-16:TP=-1.5:LRA=11"])

        cmd.append(str(output_audio_path))

        logger.info(
            f"Extracting 16kHz Mono WAV audio from {video_path.name} in mode {audio_mode.value}..."
        )
        try:
            _, _, _ = await self.process_manager.run_command(cmd)
            if not output_audio_path.exists() or output_audio_path.stat().st_size == 0:
                raise FileProcessingError(
                    f"Audio extraction produced empty file: {output_audio_path}"
                )

            logger.info(
                f"Successfully extracted audio ({output_audio_path.stat().st_size} bytes): {output_audio_path.name}"
            )
            return output_audio_path
        except Exception as e:
            if isinstance(e, FileProcessingError):
                raise e
            raise FileProcessingError(
                f"Failed to extract audio from video: {e.__class__.__name__} - {str(e)}"
            )

    _cached_encoder: Optional[Tuple[str, List[str]]] = None

    async def get_fastest_video_encoder(self) -> Tuple[str, List[str]]:
        """Detects fastest hardware-accelerated video encoder (NVIDIA NVENC > Intel QSV > CPU libx264)."""
        if self._cached_encoder:
            return self._cached_encoder

        # 1. Test NVIDIA NVENC
        try:
            ret, _, _ = await self.process_manager.run_command(
                [FFMPEG_BINARY, "-f", "lavfi", "-i", "color=c=black:s=128x128:d=0.1", "-c:v", "h264_nvenc", "-f", "null", "-"],
                timeout_seconds=5
            )
            if ret == 0:
                logger.info("⚡ Hardware Acceleration detected: NVIDIA NVENC enabled for high-speed subtitle burning.")
                self._cached_encoder = ("h264_nvenc", ["-preset", "p4", "-cq", "23"])
                return self._cached_encoder
        except Exception:
            pass

        # 2. Test Intel QuickSync (QSV)
        try:
            ret, _, _ = await self.process_manager.run_command(
                [FFMPEG_BINARY, "-f", "lavfi", "-i", "color=c=black:s=128x128:d=0.1", "-c:v", "h264_qsv", "-f", "null", "-"],
                timeout_seconds=5
            )
            if ret == 0:
                logger.info("⚡ Hardware Acceleration detected: Intel QuickSync (QSV) enabled for high-speed subtitle burning.")
                self._cached_encoder = ("h264_qsv", ["-preset", "fast", "-global_quality", "23"])
                return self._cached_encoder
        except Exception:
            pass

        # 3. Fallback: CPU libx264
        logger.info("No supported GPU encoder detected. Falling back to CPU libx264.")
        self._cached_encoder = ("libx264", ["-preset", "veryfast", "-crf", "22"])
        return self._cached_encoder

    async def embed_subtitles(
        self, video_path: Path, subtitle_path: Path, output_video_path: Path, font_size: int = 16, font_color: str = "#ffffff"
    ) -> Path:
        """Securely merges subtitle stream into video container using GPU hardware-accelerated FFmpeg."""
        FileInspector.validate_file_bytes(video_path)
        FileInspector.validate_file_bytes(subtitle_path)

        if not video_path.exists():
            raise FileProcessingError(f"Video file not found: {video_path}")
        if not subtitle_path.exists():
            raise FileProcessingError(f"Subtitle file not found: {subtitle_path}")

        # Format Windows path for FFmpeg subtitle VF filter securely: escape drive colon and backslashes
        sub_path_clean = (
            str(subtitle_path.resolve()).replace("\\", "/").replace(":", "\\:")
        )

        # Convert hex color (#RRGGBB) to ASS color format (&H00BBGGRR&)
        ass_color = "&H00FFFFFF&"
        if font_color and font_color.startswith("#") and len(font_color) == 7:
            hex_c = font_color.lstrip("#")
            r, g, b = hex_c[0:2].upper(), hex_c[2:4].upper(), hex_c[4:6].upper()
            ass_color = f"&H00{b}{g}{r}&"

        style_parts = []
        if font_size and font_size > 0:
            style_parts.append(f"FontSize={font_size}")
        if ass_color:
            style_parts.append(f"PrimaryColour={ass_color}")

        style_suffix = f":force_style='{','.join(style_parts)}'" if style_parts else ""

        encoder_name, encoder_opts = await self.get_fastest_video_encoder()

        cmd = [
            FFMPEG_BINARY,
            "-y",
            "-i",
            str(video_path),
            "-vf",
            f"subtitles='{sub_path_clean}'{style_suffix}",
            "-c:v",
            encoder_name,
            *encoder_opts,
            "-c:a",
            "copy",
            str(output_video_path),
        ]


        logger.info(
            f"Burning-in hard subtitles {subtitle_path.name} into video frames of {output_video_path.name} using secure subprocess..."
        )
        try:
            _, _, _ = await self.process_manager.run_command(cmd)
            if not output_video_path.exists() or output_video_path.stat().st_size == 0:
                raise FileProcessingError(
                    f"Video embedding produced empty or missing file: {output_video_path}"
                )

            logger.info(
                f"Successfully created merged video ({output_video_path.stat().st_size} bytes): {output_video_path.name}"
            )
            return output_video_path
        except Exception as e:
            if isinstance(e, FileProcessingError):
                raise e
            raise FileProcessingError(
                f"Failed to embed subtitles into video: {e.__class__.__name__} - {str(e)}"
            )

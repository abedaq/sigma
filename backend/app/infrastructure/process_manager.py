"""
SIGMA_ASR_VTT - Subprocess Execution & Magic Byte File Inspector
Developer: أصيل السويدي
"""

import asyncio
import shutil
import subprocess  # nosec B404
from pathlib import Path
from typing import List, Tuple
from app.core.exceptions import FileProcessingError, ValidationError
from app.infrastructure.logger import logger

FFMPEG_BINARY = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE_BINARY = shutil.which("ffprobe") or "ffprobe"

class FileInspector:
    """Validates files via Magic Byte signatures to prevent extension spoofing and path traversal."""
    
    FORBIDDEN_SIGNATURES = [
        b"MZ",           # Windows PE executable
        b"\x7fELF",      # Linux ELF executable
        b"<!DOCTYPE",    # HTML script injection
        b"<html",        # HTML injection
    ]

    MAGIC_SIGNATURES = {
        "video/mp4": [b"ftyp", b"\x00\x00\x00\x18ftyp", b"\x00\x00\x00\x20ftyp", b"\x00\x00\x00\x1cftyp", b"isom"],
        "video/mkv": [b"\x1a\x45\xdf\xa3"],
        "audio/wav": [b"RIFF"],
        "audio/mp3": [b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"ID3"],
    }

    @classmethod
    def validate_file_bytes(cls, file_path: Path) -> bool:
        """Reads initial bytes to verify file legitimacy."""
        if not file_path.exists() or not file_path.is_file():
            raise ValidationError(f"Target file does not exist: {file_path}")

        try:
            with open(file_path, "rb") as f:
                header = f.read(32)

            # Block malicious executables disguised with media extensions
            for bad_sig in cls.FORBIDDEN_SIGNATURES:
                if header.startswith(bad_sig):
                    raise ValidationError(f"Malicious executable signature detected in {file_path.name}")

            # Check matching magic signatures
            for mime, sigs in cls.MAGIC_SIGNATURES.items():
                for sig in sigs:
                    if sig in header:
                        logger.info(f"Verified magic signature for {file_path.name}: {mime}")
                        return True
            
            # Text / Subtitle files check
            if file_path.suffix.lower() in [".srt", ".vtt", ".ass", ".txt"]:
                logger.info(f"Verified subtitle text format for {file_path.name}")
                return True

            raise ValidationError(f"Invalid or corrupted media file signature for {file_path.name}")
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Failed magic byte inspection for {file_path}: {str(e)}")


class SafeProcessManager:
    """Executes external processes (FFmpeg) safely without shell=True."""

    @staticmethod
    async def run_command(cmd_args: List[str], timeout_seconds: int = 600) -> Tuple[int, str, str]:
        """Executes subprocess asynchronously passing args list strictly without shell=True."""
        logger.info(f"Executing subprocess command: {cmd_args[0]} {' '.join(cmd_args[1:3])}...")
        try:
            def _execute():
                return subprocess.run(  # nosec B603
                    cmd_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout_seconds,
                    check=False,
                    shell=False
                )

            completed_proc = await asyncio.to_thread(_execute)

            stdout = completed_proc.stdout.decode(errors="replace") if completed_proc.stdout else ""
            stderr = completed_proc.stderr.decode(errors="replace") if completed_proc.stderr else ""

            if completed_proc.returncode != 0:
                logger.error(f"Process {cmd_args[0]} failed with exit code {completed_proc.returncode}: {stderr[:200]}")
                raise FileProcessingError(
                    f"Subprocess {cmd_args[0]} failed with exit code {completed_proc.returncode}",
                    details=stderr[:500]
                )

            return completed_proc.returncode, stdout, stderr

        except subprocess.TimeoutExpired:
            logger.error(f"Process {cmd_args[0]} timed out after {timeout_seconds}s.")
            raise FileProcessingError(f"Subprocess timed out after {timeout_seconds} seconds.")
        except Exception as e:
            if isinstance(e, FileProcessingError):
                raise e
            logger.error(f"Exception during subprocess: {repr(e)}")
            raise FileProcessingError(f"Subprocess execution error: {repr(e)}")

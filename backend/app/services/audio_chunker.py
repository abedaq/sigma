"""
SIGMA_ASR_VTT - Built-in FFmpeg Silence-Aware Audio Chunker
Developer: أصيل السويدي
"""

import re
import shutil
from pathlib import Path
from typing import List
from pydantic import BaseModel
from app.infrastructure.process_manager import SafeProcessManager
from app.core.constants import (
    CHUNK_MAX_DURATION_SECONDS, CHUNK_OVERLAP_SECONDS
)
from app.infrastructure.logger import logger
from app.services.vad_service import SileroVadService

class AudioChunk(BaseModel):
    path: Path
    offset_seconds: float
    duration_seconds: float

class AudioChunker:
    """Chunks long audio files at natural silence gaps to respect API limits without breaking words."""

    def __init__(self) -> None:
        self.process_manager = SafeProcessManager()
        self.vad_service = SileroVadService()


    async def detect_silence_gaps(self, wav_path: Path) -> List[float]:
        """Runs FFmpeg silencedetect filter and parses silence start timestamps."""
        ffmpeg_binary = shutil.which("ffmpeg") or "ffmpeg"
        
        # silencedetect parameters: noise threshold -35dB, duration at least 0.4s
        cmd = [
            ffmpeg_binary,
            "-i", str(wav_path),
            "-af", "silencedetect=noise=-35dB:d=0.4",
            "-f", "null",
            "-"
        ]

        logger.info(f"Running FFmpeg silencedetect on {wav_path.name}...")
        try:
            _, _, stderr = await self.process_manager.run_command(cmd)
            
            silences = []
            for line in stderr.splitlines():
                if "silence_start:" in line:
                    match = re.search(r"silence_start:\s*([\d.]+)", line)
                    if match:
                        silences.append(float(match.group(1)))
            
            logger.info(f"Detected {len(silences)} silence gaps in {wav_path.name}.")
            return sorted(silences)
        except Exception as e:
            logger.error(f"Silence detection failed: {str(e)}")
            return []

    def calculate_split_points(self, duration: float, silences: List[float]) -> List[float]:
        """Determines the optimal split timestamps based on silence gaps and max chunk duration."""
        if duration <= CHUNK_MAX_DURATION_SECONDS:
            return []

        splits = []
        current_start = 0.0
        max_chunk = CHUNK_MAX_DURATION_SECONDS

        while (duration - current_start) > max_chunk:
            target_split = current_start + max_chunk - 30.0  # Search boundary buffer
            
            # Find silence gaps between current_start + 10 mins and target_split
            min_bound = current_start + (max_chunk * 0.5)
            max_bound = current_start + max_chunk
            
            candidates = [s for s in silences if min_bound <= s <= max_bound]
            
            if candidates:
                # Select silence closest to the target split point
                best_split = min(candidates, key=lambda s: abs(s - target_split))
            else:
                # Fallback: mechanical split if no silence gap is found
                best_split = current_start + max_chunk - 5.0
                logger.warning(f"No silence gap found between {min_bound}s and {max_bound}s. Falling back to mechanical split at {best_split}s.")

            splits.append(best_split)
            current_start = best_split

        return splits

    async def chunk_audio(self, wav_path: Path, duration_seconds: float, output_dir: Path) -> List[AudioChunk]:
        """Splits WAV file into chunks using Silero VAD neural speech detection, with FFmpeg fallback."""
        splits = self.vad_service.find_best_split_points(wav_path, max_chunk_sec=CHUNK_MAX_DURATION_SECONDS)
        if not splits:
            silences = await self.detect_silence_gaps(wav_path)
            splits = self.calculate_split_points(duration_seconds, silences)


        if not splits:
            # Single chunk (no split needed)
            return [
                AudioChunk(
                    path=wav_path,
                    offset_seconds=0.0,
                    duration_seconds=duration_seconds
                )
            ]

        logger.info(f"Splitting {wav_path.name} into {len(splits) + 1} chunks using overlap of {CHUNK_OVERLAP_SECONDS}s...")
        ffmpeg_binary = shutil.which("ffmpeg") or "ffmpeg"
        chunks = []
        
        # Build bounds
        bounds = [0.0] + splits + [duration_seconds]
        
        for i in range(len(bounds) - 1):
            chunk_start = bounds[i]
            chunk_end = bounds[i+1]
            
            # Calculate trim endpoints with overlaps
            trim_start = max(0.0, chunk_start - CHUNK_OVERLAP_SECONDS) if i > 0 else 0.0
            trim_end = min(duration_seconds, chunk_end + CHUNK_OVERLAP_SECONDS) if i < len(bounds) - 2 else duration_seconds
            
            chunk_file = output_dir / f"{wav_path.stem}_chunk_{i+1}.wav"
            
            # Trim chunk command using copy codec for fast lossless splicing
            cmd = [
                ffmpeg_binary,
                "-y",
                "-ss", f"{trim_start:.3f}",
                "-to", f"{trim_end:.3f}",
                "-i", str(wav_path),
                "-c", "copy",
                str(chunk_file)
            ]
            
            try:
                await self.process_manager.run_command(cmd)
                if chunk_file.exists() and chunk_file.stat().st_size > 0:
                    chunks.append(
                        AudioChunk(
                            path=chunk_file,
                            offset_seconds=trim_start,
                            duration_seconds=trim_end - trim_start
                        )
                    )
                    logger.info(f"Created chunk {i+1}: {chunk_file.name} (offset={trim_start:.2f}s, duration={trim_end-trim_start:.2f}s)")
                else:
                    raise Exception("Output file missing or empty.")
            except Exception as e:
                logger.error(f"Failed to create chunk {i+1}: {str(e)}")
                raise e
                
        return chunks

"""
SIGMA_ASR_VTT - Audio Processing Constants
Developer: أصيل السويدي
"""

from enum import Enum

# Audio extraction defaults
AUDIO_SAMPLE_RATE = 16000          # Hz — optimal input rate for ASR transformer models
AUDIO_CHANNELS = 1                 # Mono by default to prevent duplicate API pricing
AUDIO_BIT_DEPTH = 16               # 16-bit PCM quality
AUDIO_INTERNAL_FORMAT = "wav"      # WAV PCM S16LE format
AUDIO_INTERNAL_CODEC = "pcm_s16le" # Lossless PCM audio codec

# Chunking thresholds
CHUNK_MAX_DURATION_SECONDS = 1200  # 20 minutes (optimal size before API payload timeout)
CHUNK_MAX_FILE_SIZE_MB = 20        # Conservative ceiling below Groq's 25MB HTTP limit
CHUNK_OVERLAP_SECONDS = 2.0        # Continuous context overlap at chunk boundaries
CHUNK_MIN_SILENCE_MS = 300         # Minimal silence duration for safe voice separation

# Audio Processing Enhancement Modes
class AudioMode(str, Enum):
    STANDARD = "standard"            # No filters, pure lossless extraction
    ENHANCED = "enhanced"            # low-frequency cutoff (80Hz) + EBU R128 normalization
    MULTICHANNEL = "multichannel"    # Preserve original multi-channel tracks (Diarization)

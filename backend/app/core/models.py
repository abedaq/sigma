"""
SIGMA_ASR_VTT - Pydantic Domain Schemas & Contracts
Developer: أصيل السويدي
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

class KeyStatus(str, Enum):
    ACTIVE = "active"
    STANDBY = "standby"
    EXHAUSTED = "exhausted"
    INVALID = "invalid"

class APIKeyConfig(BaseModel):
    id: str
    name: str
    provider: str  # e.g. "gemini", "speechmatics", "google_translate"
    encrypted_key: str
    masked_key: str
    priority: int = 1
    status: KeyStatus = KeyStatus.ACTIVE
    quota_limit_rpm: int = 15
    current_rpm: int = 0
    remaining_quota_percent: float = 100.0

    def evaluate_usage(self) -> tuple[KeyStatus, float]:
        """Calculate current usage status and the remaining quota percentage."""
        if self.quota_limit_rpm <= 0:
            return KeyStatus.INVALID, 0.0

        remaining_percent = max(0.0, 100.0 - (self.current_rpm / self.quota_limit_rpm) * 100.0)
        if remaining_percent <= 0.0:
            return KeyStatus.EXHAUSTED, 0.0
        if remaining_percent < 20.0:
            return KeyStatus.STANDBY, remaining_percent
        return self.status, remaining_percent

class SubtitleItem(BaseModel):
    index: int
    start_time: str  # e.g. "00:00:01,000"
    end_time: str    # e.g. "00:00:04,500"
    text: str
    translated_text: Optional[str] = None

class ProcessingStage(str, Enum):
    IDLE = "idle"
    VALIDATING = "validating"
    EXTRACTING_AUDIO = "extracting_audio"
    ASR_PROCESSING = "asr_processing"
    ASR_GUARD_FILTERING = "asr_guard_filtering"
    TRANSLATING = "translating"
    BUILDING_SUBTITLES = "building_subtitles"
    EMBEDDING_SUBTITLES = "embedding_subtitles"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobProgress(BaseModel):
    job_id: str
    file_name: str
    stage: ProcessingStage = ProcessingStage.IDLE
    progress_percent: float = 0.0
    current_step_description: str = "Ready"
    error_message: Optional[str] = None
    detected_media_type: Optional[str] = None
    detected_media_label: Optional[str] = None
    detected_confidence: Optional[float] = None

class SystemHardwareInfo(BaseModel):
    os_name: str
    cpu_name: str
    cpu_cores_physical: int
    cpu_cores_logical: int
    ram_total_gb: float
    ram_available_gb: float
    gpu_name: str = "N/A"
    vram_total_gb: float = 0.0
    vram_available_gb: float = 0.0
    cuda_available: bool = False
    ffmpeg_version: str = "Detected"
    python_version: str
    app_version: str = "3.0.0"

class AudioMetadata(BaseModel):
    """FFprobe-extracted media metadata and AI semantic acoustic genre classification."""
    duration_seconds: float
    codec: str
    sample_rate: int
    channels: int
    file_size_bytes: int
    media_type: str = "general"          # "song", "course", "movie", "general"
    media_label_ar: str = "🎵 محتوى صوتي أو فيديو مرئ (تخصيص افتراضي)"
    detection_confidence: float = 92.5

class BatchJobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class BatchJobFile(BaseModel):
    file_id: str
    job_id: str
    original_filename: str
    status: BatchJobStatus = BatchJobStatus.PENDING
    progress_percent: float = 0.0
    current_phase: str = ""
    error_message: Optional[str] = None
    result_srt_path: Optional[str] = None
    result_video_path: Optional[str] = None

class BatchJob(BaseModel):
    job_id: str
    status: BatchJobStatus = BatchJobStatus.PENDING
    created_at: str
    completed_at: Optional[str] = None
    total_files: int = 0
    completed_files: int = 0
    failed_files: int = 0
    target_lang: str = "ar"
    engine: str = "gemini"
    mode: str = "merge"
    files: List[BatchJobFile] = []


class VideoProcessRequest(BaseModel):
    video_path: str
    source_language: str = "auto"
    target_language: str = "ar"
    asr_provider: str = "auto"
    translation_provider: str = "gemini"
    embed_subtitles: bool = False
    audio_mode: str = "standard"
    enable_vocal_isolation: bool = False
    auto_detect_media: bool = True
    enable_lyrics_grounding: bool = True
    bilingual: bool = False
    font_size: int = 16
    font_color: str = "#ffffff"


class SubtitleProcessRequest(BaseModel):
    subtitle_content: str
    source_language: str = "auto"
    target_language: str = "ar"
    export_format: str = "srt"  # srt, vtt, ass
    use_glossary: bool = True
    bilingual: bool = False
    filename: str = ""


"""
SIGMA_ASR_VTT - Hardware-Aware Zero-PyTorch Vocal Isolation Engine (Direct ONNX Runtime)
Developer: 
Architecture:
    This service performs high-precision vocal isolation using raw ONNX Runtime
    inference sessions (MDX-Net architecture) WITHOUT any dependency on PyTorch,
    audio-separator, or any torch-based library.

    It automatically detects the host machine's hardware capabilities (CPU cores,
    RAM, GPU via DirectML) and selects the optimal ONNX model tier accordingly:
        - Low-End Tier:  UVR_MDXNET_KARA_2.onnx     (~17 MB, CPU-only)
        - Mid-Range Tier: UVR_MDXNET_Main_340.onnx   (~60 MB, CPU/DirectML)
        - High-End Tier:  UVR_MDXNET_Inst_HQ_4.onnx  (~130 MB, DirectML/CUDA)

    Execution Providers (ordered by priority):
        1. DmlExecutionProvider   (DirectML - any GPU on Windows: NVIDIA/AMD/Intel)
        2. CUDAExecutionProvider  (NVIDIA CUDA, if available)
        3. CPUExecutionProvider   (Universal fallback with multi-threading)
"""

import gc
import asyncio
import subprocess  # nosec B404
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import psutil
import numpy as np

from app.infrastructure.logger import logger
from app.core.exceptions import FileProcessingError
from app.core.config import settings
from app.infrastructure.process_manager import FileInspector, FFMPEG_BINARY


# ---------------------------------------------------------------------------
# Model Tier Definitions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ModelTier:
    """Describes a single ONNX vocal isolation model and its resource requirements."""
    name: str
    filename: str
    download_url: str
    size_mb: int
    min_ram_gb: float
    min_cores: int
    description_ar: str


# Official UVR Community Model Hub URLs (Hugging Face Repository - Verified 200 OK)
_UVR_MODEL_BASE = "https://huggingface.co/Blane187/all_public_uvr_models/resolve/main"

MODEL_TIERS = {
    "low": ModelTier(
        name="KARA-2 (Lightweight)",
        filename="UVR_MDXNET_KARA_2.onnx",
        download_url=f"{_UVR_MODEL_BASE}/UVR_MDXNET_KARA_2.onnx",
        size_mb=17,
        min_ram_gb=1.0,
        min_cores=2,
        description_ar="🟢 الموديل الاقتصادي: سريع وخفيف، مناسب للأجهزة الضعيفة"
    ),
    "mid": ModelTier(
        name="Main-340 (Balanced)",
        filename="UVR-MDX-NET-Inst_Main.onnx",
        download_url=f"{_UVR_MODEL_BASE}/UVR-MDX-NET-Inst_Main.onnx",
        size_mb=56,
        min_ram_gb=4.0,
        min_cores=4,
        description_ar="🟡 الموديل المتوازن: توازن ذهبي بين الجودة والسرعة"
    ),
    "high": ModelTier(
        name="Inst-HQ-4 (Studio)",
        filename="UVR-MDX-NET-Inst_HQ_4.onnx",
        download_url=f"{_UVR_MODEL_BASE}/UVR-MDX-NET-Inst_HQ_4.onnx",
        size_mb=56,
        min_ram_gb=8.0,
        min_cores=6,
        description_ar="🟣 الموديل الاحترافي: جودة استوديو فائقة للأجهزة القوية"
    ),
}


class HardwareProbe:
    """
    Inspects the host system's hardware capabilities to determine the optimal
    ONNX execution provider and model tier for vocal isolation inference.
    """

    @staticmethod
    def get_available_providers() -> list[str]:
        """Returns ONNX Runtime execution providers available on this machine."""
        try:
            import onnxruntime as ort
            return ort.get_available_providers()
        except ImportError:
            return []

    @staticmethod
    def detect_best_provider() -> str:
        """
        Selects the fastest available ONNX execution provider.
        Priority: DirectML > CUDA > CPU
        """
        available = HardwareProbe.get_available_providers()
        if "DmlExecutionProvider" in available:
            logger.info("Hardware Probe: DirectML GPU acceleration detected (NVIDIA/AMD/Intel).")
            return "DmlExecutionProvider"
        if "CUDAExecutionProvider" in available:
            logger.info("Hardware Probe: NVIDIA CUDA GPU acceleration detected.")
            return "CUDAExecutionProvider"
        logger.info("Hardware Probe: CPU-only mode active (multi-threaded).")
        return "CPUExecutionProvider"

    @staticmethod
    def detect_best_tier() -> str:
        """
        Analyzes RAM and CPU core count to select the appropriate model tier.
        Returns 'low', 'mid', or 'high'.
        """
        ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        cores = psutil.cpu_count(logical=False) or 2

        if ram_gb >= 16 and cores >= 6:
            tier = "high"
        elif ram_gb >= 8 and cores >= 4:
            tier = "mid"
        else:
            tier = "low"

        model = MODEL_TIERS[tier]
        logger.info(
            f"Hardware Probe: RAM={ram_gb:.1f}GB, Cores={cores} -> "
            f"Selected tier '{tier}' ({model.name}, ~{model.size_mb}MB)"
        )
        return tier

    @staticmethod
    def build_session_options(provider: str):
        """
        Configures optimized ONNX session options based on execution provider.
        For CPU: maximizes thread parallelism.
        For GPU: uses default GPU thread scheduling.
        """
        import onnxruntime as ort

        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        if provider == "CPUExecutionProvider":
            logical_cores = psutil.cpu_count(logical=True) or 4
            # Use 75% of logical cores to avoid starving the system
            thread_count = max(2, int(logical_cores * 0.75))
            opts.intra_op_num_threads = thread_count
            opts.inter_op_num_threads = max(1, thread_count // 2)
            logger.info(f"ONNX Session: CPU threads configured (intra={thread_count}, inter={thread_count // 2})")
        else:
            opts.intra_op_num_threads = 0  # Let GPU provider manage threads
            opts.inter_op_num_threads = 0

        return opts


class ModelManager:
    """
    Manages ONNX model downloading, caching, and integrity verification.
    Models are cached in the application's persistent data directory.
    """

    MODELS_CACHE_DIR = settings.BASE_DIR / "models" / "vocal_isolation"

    @classmethod
    def ensure_model(cls, tier_key: str) -> Path:
        """
        Ensures the requested ONNX model is available locally.
        Downloads from the official UVR repository if not cached.
        Returns the absolute path to the .onnx model file.
        """
        cls.MODELS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tier = MODEL_TIERS[tier_key]
        model_path = cls.MODELS_CACHE_DIR / tier.filename

        if model_path.exists() and model_path.stat().st_size > 1_000_000:
            logger.debug(f"Model cache hit: {tier.filename} ({model_path.stat().st_size / 1e6:.1f}MB)")
            return model_path

        logger.info(f"Model '{tier.filename}' not found in cache. Downloading from UVR repository (~{tier.size_mb}MB)...")
        cls._download_model(tier.download_url, model_path, tier.size_mb)
        return model_path

    @classmethod
    def _download_model(cls, url: str, dest: Path, expected_mb: int) -> None:
        """Downloads an ONNX model from a URL with progress logging and integrity check."""
        import httpx

        temp_path = dest.with_suffix(".downloading")
        try:
            with httpx.stream("GET", url, follow_redirects=True, timeout=300.0) as response:
                response.raise_for_status()
                total = int(response.headers.get("content-length", 0))
                downloaded = 0

                with open(temp_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=262144):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0 and downloaded % (5 * 1024 * 1024) < 262144:
                            pct = (downloaded / total) * 100
                            logger.info(f"Downloading {dest.name}: {pct:.0f}% ({downloaded / 1e6:.1f}/{total / 1e6:.1f}MB)")

            # Verify minimum size sanity check
            actual_mb = temp_path.stat().st_size / (1024 * 1024)
            if actual_mb < expected_mb * 0.5:
                temp_path.unlink(missing_ok=True)
                raise FileProcessingError(
                    f"Downloaded model is suspiciously small ({actual_mb:.1f}MB vs expected ~{expected_mb}MB). "
                    "The download may have been corrupted or intercepted."
                )

            temp_path.rename(dest)
            logger.info(f"Model downloaded successfully: {dest.name} ({actual_mb:.1f}MB)")

        except Exception as e:
            temp_path.unlink(missing_ok=True)
            if isinstance(e, FileProcessingError):
                raise
            raise FileProcessingError(f"Failed to download ONNX model from {url}: {e}")

    @classmethod
    def list_cached_models(cls) -> list[dict]:
        """Returns metadata about all cached ONNX models."""
        results = []
        for tier_key, tier in MODEL_TIERS.items():
            path = cls.MODELS_CACHE_DIR / tier.filename
            results.append({
                "tier": tier_key,
                "name": tier.name,
                "filename": tier.filename,
                "size_mb": tier.size_mb,
                "cached": path.exists(),
                "cached_size_mb": round(path.stat().st_size / 1e6, 1) if path.exists() else 0,
                "description_ar": tier.description_ar
            })
        return results


class VocalIsolationService:
    """
    Hardware-Aware Zero-PyTorch Vocal Isolation Engine.

    Performs high-precision vocal/speech isolation from music and accompaniment
    using direct ONNX Runtime inference with MDX-Net architecture models.

    Key features:
        - Zero PyTorch dependency (strict project policy compliance)
        - Automatic hardware detection (CPU cores, RAM, GPU)
        - Dynamic model tier selection (low/mid/high)
        - DirectML support for ANY Windows GPU (NVIDIA, AMD, Intel)
        - CUDA fallback for NVIDIA-specific acceleration
        - CPU multi-threading fallback for GPU-less machines
        - Explicit VRAM/RAM garbage collection after inference
    """

    def __init__(self, tier_override: Optional[str] = None) -> None:
        """
        Initialize the vocal isolation service.

        Args:
            tier_override: Force a specific tier ('low', 'mid', 'high').
                           If None, auto-detects based on hardware.
        """
        self._provider = HardwareProbe.detect_best_provider()
        self._tier_key = tier_override if tier_override in MODEL_TIERS else HardwareProbe.detect_best_tier()
        self._tier = MODEL_TIERS[self._tier_key]

    @property
    def tier_info(self) -> dict:
        """Returns metadata about the currently selected model tier."""
        return {
            "tier": self._tier_key,
            "model_name": self._tier.name,
            "model_filename": self._tier.filename,
            "model_size_mb": self._tier.size_mb,
            "provider": self._provider,
            "description_ar": self._tier.description_ar
        }

    def cleanup_memory(self) -> None:
        """Explicitly purges memory caches and ONNX runtime inference sessions."""
        logger.debug("Running explicit ONNX memory and garbage collection...")
        gc.collect()
        try:
            import onnxruntime as ort
            logger.debug(f"ONNX Runtime cleanup executed (Providers: {ort.get_available_providers()}).")
        except ImportError:
            pass

    async def isolate(self, audio_path: Path, output_dir: Path) -> Path:
        """
        Isolates human speech/vocals from accompaniment and music.
        Exports a clean vocals_only.wav file.

        Uses asynchronous thread delegation to prevent blocking the FastAPI event loop.

        Args:
            audio_path: Path to the input audio WAV file.
            output_dir: Directory to write the isolated vocals file.

        Returns:
            Path to the generated vocals-only WAV file.
        """
        FileInspector.validate_file_bytes(audio_path)
        if not audio_path.exists():
            raise FileProcessingError(f"Input audio file for vocal isolation not found: {audio_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        target_vocal_path = output_dir / f"{audio_path.stem}_vocals_only.wav"

        logger.info(
            f"Starting ONNX vocal isolation for {audio_path.name} "
            f"using {self._tier.name} on {self._provider}..."
        )

        try:
            await asyncio.to_thread(self._run_isolation_sync, audio_path, output_dir, target_vocal_path)

            if not target_vocal_path.exists() or target_vocal_path.stat().st_size == 0:
                raise FileProcessingError(f"Vocal isolation failed to generate output file: {target_vocal_path}")

            logger.info(
                f"Vocal isolation successful: {target_vocal_path.name} "
                f"({target_vocal_path.stat().st_size} bytes) "
                f"[Tier={self._tier_key}, Provider={self._provider}]"
            )
            return target_vocal_path

        except Exception as e:
            if isinstance(e, FileProcessingError):
                raise
            logger.error(f"Vocal isolation pipeline encountered an exception: {e}")
            raise FileProcessingError(f"Failed to isolate vocals from audio: {e.__class__.__name__} - {e}")
        finally:
            self.cleanup_memory()

    def _run_isolation_sync(self, input_path: Path, output_dir: Path, target_path: Path) -> None:
        """
        Synchronous ONNX inference pipeline for MDX-Net vocal separation.

        Pipeline:
            1. Load audio as numpy float32 array via soundfile
            2. Apply STFT to convert to frequency domain
            3. Run ONNX inference to generate vocal/instrumental masks
            4. Apply mask and inverse STFT to reconstruct vocal waveform
            5. Export clean vocals as WAV
        """
        try:
            import onnxruntime as ort
        except ImportError:
            raise FileProcessingError(
                "onnxruntime is not installed. Please install it: "
                "'pip install onnxruntime-directml' (GPU) or 'pip install onnxruntime' (CPU)."
            )

        try:
            import soundfile as sf
        except ImportError:
            raise FileProcessingError(
                "soundfile is not installed. Please install it: 'pip install soundfile'."
            )

        # Ensure model is cached locally
        model_path = ModelManager.ensure_model(self._tier_key)

        # Build optimized ONNX session
        session_opts = HardwareProbe.build_session_options(self._provider)

        try:
            session = ort.InferenceSession(
                str(model_path),
                sess_options=session_opts,
                providers=[self._provider, "CPUExecutionProvider"]
            )
            logger.info(f"ONNX session initialized: {self._tier.filename} on {session.get_providers()}")
        except Exception as e:
            # Fallback to CPU if preferred provider fails
            logger.warning(f"Failed to create session with {self._provider}: {e}. Falling back to CPU.")
            session = ort.InferenceSession(
                str(model_path),
                sess_options=session_opts,
                providers=["CPUExecutionProvider"]
            )

        try:
            # 1. Extract 44.1kHz Stereo PCM audio via FFmpeg to guarantee full studio bandwidth for MDX-Net
            temp_stereo_path = output_dir / f"{input_path.stem}_44k_stereo.wav"
            subprocess.run(  # nosec B603
                [
                    FFMPEG_BINARY, "-y", "-i", str(input_path),
                    "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le",
                    str(temp_stereo_path)
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            audio_data, sample_rate = sf.read(str(temp_stereo_path), dtype="float32")
            temp_stereo_path.unlink(missing_ok=True)

            if audio_data.ndim == 1:
                audio_data = np.stack([audio_data, audio_data], axis=-1)
            logger.info(f"Loaded high-fidelity studio audio: {audio_data.shape}, SR={sample_rate}")

            # 2. Get model input/output metadata
            input_meta = session.get_inputs()[0]
            input_name = input_meta.name
            input_shape = input_meta.shape
            logger.debug(f"ONNX model input: name={input_name}, shape={input_shape}")

            # 3. Process audio in overlapping 4D tensor STFT windows
            vocals = self._process_with_overlap(
                session, input_name, audio_data, sample_rate, input_shape
            )

            # 4. Export intermediate high-res vocal file, then downmix to 16kHz Mono for Whisper ASR
            temp_vocal_path = output_dir / f"{input_path.stem}_raw_vocal_temp.wav"
            sf.write(str(temp_vocal_path), vocals, sample_rate, subtype="PCM_16")

            subprocess.run(  # nosec B603
                [
                    FFMPEG_BINARY, "-y", "-i", str(temp_vocal_path),
                    "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
                    str(target_path)
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            temp_vocal_path.unlink(missing_ok=True)
            logger.info(f"Exported clean 16kHz isolated vocals to: {target_path}")

        finally:
            del session
            gc.collect()

    def _process_with_overlap(
        self,
        session,
        input_name: str,
        audio: np.ndarray,
        sample_rate: int,
        input_shape: list,
    ) -> np.ndarray:
        """
        Processes 44.1kHz stereo audio through MDX-Net ONNX model using overlap-add.
        MDX-Net models require 4D tensor input shape [1, 4, 2560, 256] representing
        STFT Real & Imaginary parts of both stereo channels with n_fft=5120 and hop_length=1024.
        """
        from scipy.signal import stft, istft  # type: ignore

        n_fft = 5120
        hop_length = 1024
        chunk_samples = 261120  # Exactly 256 time frames when n_fft=5120 and hop=1024
        step_samples = chunk_samples // 2  # 50% overlap for smooth transitions

        total_samples = audio.shape[0]
        output_audio = np.zeros_like(audio)
        weight_sum = np.zeros((total_samples, 1), dtype=np.float32)

        # Hann window for overlap-add smoothing
        window = np.hanning(chunk_samples).astype(np.float32)[:, np.newaxis]

        start = 0
        segment_idx = 0

        while start < total_samples:
            end = min(start + chunk_samples, total_samples)
            segment = audio[start:end]
            actual_len = len(segment)
            segment_idx += 1

            logger.debug(f"Processing segment {segment_idx}: samples {start}-{end} ({(end - start) / sample_rate:.1f}s)")

            if actual_len < chunk_samples:
                pad_len = chunk_samples - actual_len
                chunk = np.pad(segment, ((0, pad_len), (0, 0)), mode="constant")
            else:
                chunk = segment

            try:
                # Compute STFT for Left and Right channels
                _, _, Z_L = stft(chunk[:, 0], fs=sample_rate, nperseg=n_fft, noverlap=n_fft - hop_length)
                _, _, Z_R = stft(chunk[:, 1], fs=sample_rate, nperseg=n_fft, noverlap=n_fft - hop_length)

                # Ensure exact 2560 frequency bins and 256 time frames
                def fix_shape(Z):
                    Z_2560 = Z[:-1, :]
                    if Z_2560.shape[1] > 256:
                        return Z_2560[:, :256]
                    elif Z_2560.shape[1] < 256:
                        return np.pad(Z_2560, ((0, 0), (0, 256 - Z_2560.shape[1])), mode="constant")
                    return Z_2560

                Z_L_2560 = fix_shape(Z_L)
                Z_R_2560 = fix_shape(Z_R)

                # Scale Scipy STFT spectrum to unscaled FFT magnitudes expected by MDX-Net ONNX models (2560.0 / 2.0 = 1280.0)
                stft_scale = 1280.0

                # Construct 4D input tensor: [1, 4, 2560, 256] -> L_real, L_imag, R_real, R_imag
                model_input = np.stack(
                    [Z_L_2560.real, Z_L_2560.imag, Z_R_2560.real, Z_R_2560.imag],
                    axis=0
                )[np.newaxis, ...].astype(np.float32) * stft_scale

                # Run zero-PyTorch ONNX GPU inference
                outputs = session.run(None, {input_name: model_input})
                inst_tensor = outputs[0][0] / stft_scale  # Rescale back to Scipy spectrum domain

                # Reconstruct complex STFT for Instrumental track
                inst_L_2560 = inst_tensor[0, :, :] + 1j * inst_tensor[1, :, :]
                inst_R_2560 = inst_tensor[2, :, :] + 1j * inst_tensor[3, :, :]

                inst_L_full = np.vstack([inst_L_2560, np.zeros((1, 256), dtype=np.complex64)])
                inst_R_full = np.vstack([inst_R_2560, np.zeros((1, 256), dtype=np.complex64)])

                # Inverse STFT to obtain instrumental waveforms
                _, inst_wav_L = istft(inst_L_full, fs=sample_rate, nperseg=n_fft, noverlap=n_fft - hop_length)
                _, inst_wav_R = istft(inst_R_full, fs=sample_rate, nperseg=n_fft, noverlap=n_fft - hop_length)

                inst_chunk = np.stack([inst_wav_L[:chunk_samples], inst_wav_R[:chunk_samples]], axis=-1)
                if len(inst_chunk) < chunk_samples:
                    inst_chunk = np.pad(inst_chunk, ((0, chunk_samples - len(inst_chunk)), (0, 0)), mode="constant")

                # Pure vocals = Mixed audio - Instrumental audio
                vocal_chunk = chunk - inst_chunk

            except Exception as e:
                logger.warning(f"ONNX inference failed for segment {segment_idx}: {e}. Using passthrough.")
                vocal_chunk = chunk

            # Overlap-add into output buffer
            output_audio[start:end] += (vocal_chunk[:actual_len] * window[:actual_len])
            weight_sum[start:end] += window[:actual_len]

            start += step_samples

        # Normalize by overlap weights
        safe_weights = np.maximum(weight_sum, 1e-8)
        output_audio = output_audio / safe_weights
        return np.clip(output_audio, -1.0, 1.0)

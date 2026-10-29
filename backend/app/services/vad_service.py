"""
SIGMA_ASR_VTT - Silero VAD Voice Activity Detector (Pure ONNX / Zero-PyTorch)
Developer: أصيل السويدي
"""

import math
import wave
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
import onnxruntime as ort
from app.infrastructure.logger import logger

class SileroVadService:
    """
    Zero-PyTorch Voice Activity Detection (VAD) using ONNX Runtime.
    Detects true speech boundaries, eliminates hallucinations on non-speech/silence,
    and enables adaptive audio splitting at natural conversational pauses.
    """

    def __init__(self, model_path: Optional[Path] = None) -> None:
        if model_path is None:
            model_path = Path(__file__).resolve().parent.parent.parent / "models" / "vad" / "silero_vad.onnx"
        
        self.model_path = model_path
        self.session: Optional[ort.InferenceSession] = None
        self._load_model()

    def _load_model(self) -> None:
        """Loads the ONNX VAD model using available ONNX providers."""
        if not self.model_path.exists():
            logger.warning(f"Silero VAD model not found at {self.model_path}. VAD disabled.")
            return

        try:
            opts = ort.SessionOptions()
            opts.inter_op_num_threads = 1
            opts.intra_op_num_threads = 2
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

            providers = ["CPUExecutionProvider"]
            self.session = ort.InferenceSession(str(self.model_path), sess_options=opts, providers=providers)
            logger.info("Silero VAD ONNX model initialized successfully (Zero-PyTorch).")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD ONNX model: {str(e)}")
            self.session = None

    def read_wav_16k_mono(self, wav_path: Path) -> np.ndarray:
        """Reads a 16kHz mono WAV file into a normalized float32 numpy array [-1.0, 1.0]."""
        with wave.open(str(wav_path), "rb") as wf:
            channels = wf.getnchannels()
            sample_rate = wf.getframerate()
            sample_width = wf.getsampwidth()
            n_frames = wf.getnframes()
            
            raw_bytes = wf.readframes(n_frames)
            
        if sample_width == 2:
            audio = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        elif sample_width == 4:
            audio = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            audio = np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0

        if channels > 1:
            audio = audio.reshape(-1, channels).mean(axis=1)

        return audio

    def get_speech_timestamps(
        self,
        wav_path: Path,
        threshold: float = 0.5,
        min_speech_duration_ms: int = 250,
        min_silence_duration_ms: int = 400,
        window_size_samples: int = 512
    ) -> List[Dict[str, float]]:
        """
        Analyzes audio and returns list of speech intervals: [{'start': sec, 'end': sec}].
        """
        if not self.session:
            logger.warning("Silero VAD not loaded; returning entire file as single speech segment.")
            return [{"start": 0.0, "end": 999999.0}]

        audio = self.read_wav_16k_mono(wav_path)
        sr = np.array([16000], dtype=np.int64)
        
        # State tensor for LSTM/GRU in Silero VAD: [2, 1, 128]
        state = np.zeros((2, 1, 128), dtype=np.float32)
        
        speech_probs = []
        num_windows = len(audio) // window_size_samples

        for i in range(num_windows):
            chunk = audio[i * window_size_samples : (i + 1) * window_size_samples]
            chunk_input = np.expand_dims(chunk, axis=0) # [1, 512]
            
            ort_inputs = {
                "input": chunk_input,
                "state": state,
                "sr": sr
            }
            out, state = self.session.run(None, ort_inputs)
            prob = float(out[0][0])
            speech_probs.append(prob)

        # Detect speech intervals using hysteresis thresholds
        triggered = False
        speech_intervals = []
        current_speech = {"start": 0.0, "end": 0.0}
        
        window_duration_sec = window_size_samples / 16000.0
        min_speech_windows = int(min_speech_duration_ms / (window_duration_sec * 1000))
        min_silence_windows = int(min_silence_duration_ms / (window_duration_sec * 1000))
        
        silence_counter = 0

        for idx, prob in enumerate(speech_probs):
            time_sec = idx * window_duration_sec
            
            if prob >= threshold:
                silence_counter = 0
                if not triggered:
                    triggered = True
                    current_speech["start"] = round(time_sec, 3)
            else:
                if triggered:
                    silence_counter += 1
                    if silence_counter >= min_silence_windows:
                        triggered = False
                        current_speech["end"] = round(time_sec - (silence_counter * window_duration_sec), 3)
                        
                        # Verify duration threshold
                        if (current_speech["end"] - current_speech["start"]) * 1000 >= min_speech_duration_ms:
                            speech_intervals.append(dict(current_speech))
                        silence_counter = 0

        if triggered:
            current_speech["end"] = round(len(audio) / 16000.0, 3)
            speech_intervals.append(dict(current_speech))

        logger.info(f"Silero VAD detected {len(speech_intervals)} distinct speech segments in {wav_path.name}.")
        return speech_intervals

    def find_best_split_points(
        self,
        wav_path: Path,
        max_chunk_sec: float = 300.0, # 5 minutes default
        min_chunk_sec: float = 60.0
    ) -> List[float]:
        """
        Finds optimal splitting timestamps located strictly within conversational silence gaps.
        Prevents word truncation and ASR boundary hallucinations.
        """
        try:
            intervals = self.get_speech_timestamps(wav_path)
            if not intervals:
                return []

            # Compute silence gaps between speech segments
            silence_gaps = []
            for i in range(len(intervals) - 1):
                gap_start = intervals[i]["end"]
                gap_end = intervals[i + 1]["start"]
                if gap_end > gap_start:
                    silence_gaps.append((gap_start + gap_end) / 2.0)

            total_duration = intervals[-1]["end"]
            if total_duration <= max_chunk_sec:
                return []

            split_points = []
            last_split = 0.0

            for gap in silence_gaps:
                if (gap - last_split) >= min_chunk_sec:
                    if (gap - last_split) >= (max_chunk_sec * 0.75):
                        split_points.append(round(gap, 2))
                        last_split = gap

            return split_points
        except Exception as e:
            logger.error(f"VAD split points detection error: {str(e)}")
            return []

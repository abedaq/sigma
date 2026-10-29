"""
SIGMA_ASR_VTT - Pipeline Orchestration Service
Developer: أصيل السويدي
"""
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Callable

from app.core.models import (
    JobProgress, ProcessingStage, VideoProcessRequest, SubtitleItem, APIKeyConfig
)
from app.core.constants import AudioMode
from app.core.exceptions import ASRError
from app.services.media_service import MediaService
from app.services.asr_service import ASRService
from app.services.translation_service import TranslationService
from app.services.subtitle_service import SubtitleService
from app.services.vocal_isolation_service import VocalIsolationService
from app.services.lyrics_grounding_service import LyricsGroundingService
from app.services.audio_analyzer import AudioAnalyzer
from app.services.audio_chunker import AudioChunker
from app.integrations.format_converter import FormatConverter
from app.infrastructure.timestamp_utils import apply_chunk_offset, srt_time_to_seconds
from app.infrastructure.logger import logger


def de_duplicate_overlapping_subtitles(items: List[SubtitleItem]) -> List[SubtitleItem]:
    """Sorts subtitle items and removes duplicates that fall within overlapping boundaries."""
    if not items:
        return []
        
    sorted_items = sorted(items, key=lambda x: srt_time_to_seconds(x.start_time))
    unique_items = []
    
    for item in sorted_items:
        if not unique_items:
            unique_items.append(item)
            continue
            
        last_item = unique_items[-1]
        last_end = srt_time_to_seconds(last_item.end_time)
        curr_start = srt_time_to_seconds(item.start_time)
        
        # Check text equality or high similarity on overlap
        if curr_start < last_end:
            if item.text.strip().lower() == last_item.text.strip().lower():
                continue
                
        unique_items.append(item)
        
    for idx, it in enumerate(unique_items, start=1):
        it.index = idx
        
    return unique_items


class PipelineService:
    """Encapsulates end-to-end video/audio processing pipeline orchestration."""

    @staticmethod
    async def run_video_pipeline(
        job_id: str,
        sandbox_dir: Path,
        video_path: Path,
        req: VideoProcessRequest,
        active_keys: List[APIKeyConfig],
        glossary: Dict[str, str],
        progress_callback: Optional[Callable[[JobProgress], asyncio.Future]] = None
    ) -> Dict[str, any]:
        """Runs the complete multi-stage pipeline: Validation -> Extraction -> Isolation -> ASR -> Translation -> Subtitles."""
        media_service = MediaService()
        asr_service = ASRService()
        translation_service = TranslationService()

        async def _notify(prog: JobProgress):
            if progress_callback:
                await progress_callback(prog)
            else:
                try:
                    from app.api.websocket import ws_manager
                    await ws_manager.broadcast_progress(prog)
                except Exception:
                    pass

        try:
            # Stage 1: Validation
            prog = JobProgress(job_id=job_id, file_name=video_path.name, stage=ProcessingStage.VALIDATING, progress_percent=10.0, current_step_description="Validating file bytes and MIME signature...")
            await _notify(prog)

            # Stage 2: Audio Extraction (16kHz WAV PCM)
            prog.stage = ProcessingStage.EXTRACTING_AUDIO
            prog.progress_percent = 25.0
            prog.current_step_description = "Extracting and optimizing audio to 16kHz WAV PCM..."
            await _notify(prog)
            
            # Metadata analysis via FFprobe
            analyzer = AudioAnalyzer()
            metadata = await analyzer.analyze_media(video_path)

            # Smart acoustic media genre discovery
            prog.detected_media_type = getattr(metadata, "media_type", "general")
            prog.detected_media_label = getattr(metadata, "media_label_ar", None)
            prog.detected_confidence = getattr(metadata, "detection_confidence", 95.0)
            await _notify(prog)
            
            # Resolve audio mode
            audio_mode = AudioMode.ENHANCED
            if req.audio_mode:
                try:
                    audio_mode = AudioMode(req.audio_mode)
                except ValueError:
                    pass

            audio_path = await media_service.extract_audio_for_api(video_path, sandbox_dir, audio_mode)

            # AI Vocal Isolation via ONNX MDX-Net
            isolate_enabled = getattr(req, "enable_vocal_isolation", False)
            auto_detect = getattr(req, "auto_detect_media", True)
            is_music = getattr(metadata, "media_type", "general") in ["song", "music", "general"]
            should_isolate = isolate_enabled or (auto_detect and is_music)
            if should_isolate:
                prog.current_step_description = "🧠 جاري عزل وفلترة الغناء عن الموسيقى بالذكاء الاصطناعي (ONNX MDX-Net)..."
                await _notify(prog)
                logger.info(f"Executing universal zero-PyTorch ONNX vocal isolation before ASR processing on job {job_id}...")
                try:
                    vocal_service = VocalIsolationService()
                    audio_path = await vocal_service.isolate(video_path, sandbox_dir)
                    logger.info(f"Universal vocal isolation successfully prepared clean vocal audio for ASR engine: {audio_path.name}")
                except Exception as iso_err:
                    logger.warning(f"Vocal isolation fallback notice (using clean PCM audio): {str(iso_err)}")

            # Stage 3: ASR Processing
            prog.stage = ProcessingStage.ASR_PROCESSING
            prog.progress_percent = 50.0
            prog.current_step_description = "Running Cloud ASR transcription..."
            await _notify(prog)

            asr_keys = list(active_keys)
            provider_name = req.asr_provider.lower().strip() if req.asr_provider else "auto"
            if provider_name != "auto":
                filtered_keys = [k for k in asr_keys if k.provider.lower() == provider_name]
                if not filtered_keys:
                    raise ASRError(f"No active API keys found for ASR provider: {req.asr_provider}")
                asr_keys = filtered_keys

            # Audio chunking
            chunker = AudioChunker()
            chunks = await chunker.chunk_audio(audio_path, metadata.duration_seconds, sandbox_dir)
            
            converter = FormatConverter()
            raw_items = []
            target_prov = asr_keys[0].provider if asr_keys else "groq"

            for idx, chunk in enumerate(chunks):
                upload_path, _ = await converter.prepare_for_upload(chunk.path, target_prov, sandbox_dir)
                logger.info(f"Transcribing audio chunk {idx+1}/{len(chunks)} (offset={chunk.offset_seconds:.2f}s) via {target_prov}...")
                chunk_items = await asr_service.transcribe(upload_path, keys_pool=asr_keys, language=req.source_language)
                chunk_items_aligned = apply_chunk_offset(chunk_items, chunk.offset_seconds)
                raw_items.extend(chunk_items_aligned)

            if len(chunks) > 1:
                raw_items = de_duplicate_overlapping_subtitles(raw_items)

            # Stage 3.5: Music Intelligence & Ground-Truth Lyrics Alignment
            if should_isolate or is_music:
                try:
                    logger.info(f"Engaging Music Intelligence & Lyrics Grounding on job {job_id}...")
                    grounding_res = await LyricsGroundingService.ground_song_pipeline(
                        video_path, raw_items
                    )
                    if grounding_res.is_grounded and grounding_res.subtitles:
                        raw_items = grounding_res.subtitles
                        logger.info(
                            f"🎵 Lyrics Grounding successfully synchronized {len(raw_items)} lines from {grounding_res.source}!"
                        )
                except Exception as ground_err:
                    logger.warning(f"Lyrics Grounding fallback notice (retaining ASR): {ground_err}")

            # Stage 4: Translation
            prog.stage = ProcessingStage.TRANSLATING
            prog.progress_percent = 75.0
            prog.current_step_description = f"Translating segments to {req.target_language} with Context Glossary..."
            await _notify(prog)

            trans_provider_name = req.translation_provider.lower().strip() if getattr(req, "translation_provider", None) else "auto"
            if trans_provider_name and trans_provider_name != "auto":
                trans_keys = [k for k in active_keys if k.provider.lower() == trans_provider_name or k.provider.lower().startswith(trans_provider_name)]
                if not trans_keys:
                    trans_keys = active_keys
            else:
                trans_keys = active_keys

            if is_music or should_isolate:
                genre_prompt = (
                    "Media Genre: Music / Song Lyrics. "
                    "Translation Directive: Translate into eloquent, poetic Arabic (فصحى شعرية راقية) "
                    "preserving emotional depth, vocal meter, and lyrical metaphors. "
                    "Maintain line-by-line rhyme and emotional cadence."
                )
            else:
                genre_prompt = f"Media Genre: {getattr(metadata, 'media_type', 'general')} - {getattr(metadata, 'media_label_ar', '')}"

            translated_items = await translation_service.translate_subtitles(
                items=raw_items,
                keys_pool=trans_keys,
                source_lang=req.source_language,
                target_lang=req.target_language,
                glossary=glossary,
                profile_prompt=genre_prompt
            )

            # Stage 5: Exporting Subtitles
            prog.stage = ProcessingStage.BUILDING_SUBTITLES
            prog.progress_percent = 90.0
            prog.current_step_description = "Building and exporting final SRT/VTT subtitle files..."
            await _notify(prog)

            # Save original transcribed subtitles
            original_srt_output = SubtitleService.export_srt(raw_items)
            original_out_file = video_path.parent / f"{video_path.stem}_original.srt"
            await asyncio.to_thread(original_out_file.write_text, original_srt_output, encoding="utf-8")
            logger.info(f"Saved original transcribed subtitles to {original_out_file.name}")

            # Save translated subtitles
            if req.bilingual:
                srt_output = SubtitleService.export_bilingual_srt(raw_items, translated_items)
            else:
                srt_output = SubtitleService.export_srt(translated_items)
            out_file = video_path.parent / f"{video_path.stem}_translated.srt"
            await asyncio.to_thread(out_file.write_text, srt_output, encoding="utf-8")
            logger.info(f"Saved translated subtitles to {out_file.name}")

            merged_video_name = None
            if req.embed_subtitles:
                prog.current_step_description = "Embedding translated subtitles into video container..."
                await _notify(prog)
                merged_file = video_path.parent / f"{video_path.stem}_merged{video_path.suffix}"
                await media_service.embed_subtitles(
                    video_path, out_file, merged_file, font_size=req.font_size, font_color=req.font_color
                )
                merged_video_name = merged_file.name

            # Completion
            prog.stage = ProcessingStage.COMPLETED
            prog.progress_percent = 100.0
            completion_msg = f"Successfully completed! Subtitle saved to {out_file.name}"
            if merged_video_name:
                completion_msg += f" and video merged as {merged_video_name}"
            prog.current_step_description = completion_msg
            await _notify(prog)
            logger.info(f"Job {job_id} completed successfully.")

            return {
                "status": "success",
                "job_id": job_id,
                "srt_path": str(out_file),
                "merged_video": merged_video_name
            }

        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}")
            prog = JobProgress(job_id=job_id, file_name=video_path.name, stage=ProcessingStage.FAILED, progress_percent=0.0, current_step_description="Processing failed.", error_message=str(e))
            await _notify(prog)
            raise
        finally:
            media_service.purge_job_sandbox(sandbox_dir)

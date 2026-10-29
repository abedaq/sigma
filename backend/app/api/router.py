"""
SIGMA_ASR_VTT - REST API Router
Developer: أصيل السويدي
"""

import uuid
import asyncio
from pathlib import Path
from typing import List, Dict, Annotated, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, File, UploadFile, Form
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import AESVault
from app.core.licensing import HWIDGenerator, LicenseValidator
from app.core.models import (
    APIKeyConfig, KeyStatus, SubtitleItem, JobProgress,
    ProcessingStage, VideoProcessRequest, SubtitleProcessRequest
)
from app.core.exceptions import ValidationError, ASRError
from app.core.constants import AudioMode
from app.services.media_service import MediaService
from app.services.audio_analyzer import AudioAnalyzer
from app.services.audio_chunker import AudioChunker
from app.services.asr_service import ASRService
from app.services.translation_service import TranslationService
from app.services.subtitle_service import SubtitleService
from app.services.vocal_isolation_service import VocalIsolationService
from app.services.lyrics_grounding_service import LyricsGroundingService
from app.integrations.format_converter import FormatConverter

from app.infrastructure.timestamp_utils import apply_chunk_offset, srt_time_to_seconds
from app.api.websocket import ws_manager
from app.infrastructure.logger import logger
from app.infrastructure.database_ops import (
    get_all_keys as db_get_all_keys,
    add_or_update_key as db_add_key,
    delete_key as db_delete_key,
    get_glossary as db_get_glossary,
    update_glossary_item as db_update_glossary
)

router = APIRouter(prefix="/api/v1")
vault = AESVault()
_active_background_tasks: set = set()

# In-memory store for keys & glossaries (persisted in SQLite encrypted db)
key_store: Dict[str, APIKeyConfig] = {}

glossary_store: Dict[str, str] = {
    "Cybersecurity": "الأمن السيبراني",
    "SOC Analyst": "محلل مركز العمليات الأمنية",
    "ASR": "التفريغ الصوتي التلقائي"
}

# Sync with SQLite database
try:
    _persisted_keys = db_get_all_keys()
    if _persisted_keys:
        key_store = _persisted_keys
    else:
        for _k in key_store.values():
            db_add_key(_k)

    _persisted_glossary = db_get_glossary()
    if _persisted_glossary:
        glossary_store = _persisted_glossary
    else:
        for _term, _trans in glossary_store.items():
            db_update_glossary(_term, _trans)
except Exception as _e:
    logger.warning(f"Database sync warning: {str(_e)}")


def _refresh_key_usage_stats() -> None:
    for key_config in key_store.values():
        status, remaining_percent = key_config.evaluate_usage()
        key_config.status = status
        key_config.remaining_quota_percent = remaining_percent

_refresh_key_usage_stats()


class KeyCreateRequest(BaseModel):
    name: str
    provider: str
    raw_key: str
    priority: int = 1



@router.get("/keys", response_model=List[APIKeyConfig])
async def list_keys():
    """Returns list of configured API keys with masked key values and quota stats."""
    _refresh_key_usage_stats()
    return [k.model_copy(update={"encrypted_key": "PROTECTED"}) for k in key_store.values()]


@router.post("/keys", response_model=APIKeyConfig)
async def add_key(req: KeyCreateRequest):
    """Encrypts raw key with AES-256 and adds to vault."""
    key_id = f"key_{uuid.uuid4().hex[:8]}"
    enc_key = vault.encrypt(req.raw_key)
    masked = AESVault.mask_key(req.raw_key)
    
    config = APIKeyConfig(
        id=key_id,
        name=req.name,
        provider=req.provider,
        encrypted_key=enc_key,
        masked_key=masked,
        priority=req.priority,
        status=KeyStatus.ACTIVE,
        remaining_quota_percent=100.0
    )
    key_store[key_id] = config
    try:
        db_add_key(config)
    except Exception as e:
        logger.error(f"Failed to persist key to SQLite: {e}")
    _refresh_key_usage_stats()
    logger.info(f"Added new encrypted API key to vault: {config.name}")
    return config.model_copy(update={"encrypted_key": "PROTECTED"})


@router.delete("/keys/{key_id}", responses={404: {"description": "Key not found"}})
async def delete_key(key_id: str):
    if key_id in key_store:
        deleted = key_store.pop(key_id)
        try:
            db_delete_key(key_id)
        except Exception as e:
            logger.error(f"Failed to delete key from SQLite: {e}")
        logger.info(f"Deleted API key: {deleted.name}")
        return {"status": "deleted", "id": key_id}
    raise HTTPException(status_code=404, detail="Key not found")


class GlossaryItemRequest(BaseModel):
    term: str
    translation: str


@router.get("/glossary")
async def get_glossary_route():
    return glossary_store


@router.post("/glossary")
async def add_glossary_item(req: GlossaryItemRequest):
    glossary_store[req.term] = req.translation
    try:
        db_update_glossary(req.term, req.translation)
    except Exception as e:
        logger.error(f"Failed to persist glossary to SQLite: {e}")
    return {"status": "updated", "glossary": glossary_store}


@router.post("/process/subtitle", responses={500: {"description": "Internal server error"}})
async def process_subtitle_translation(req: SubtitleProcessRequest):
    """Translates SRT/VTT/ASS subtitle content directly using Context Translation Engine."""
    try:
        items = SubtitleService.parse_subtitle(req.subtitle_content, req.filename or f"file.{req.export_format}")
        if not items:
            raise ValidationError("Failed to parse subtitle content or empty file provided.")

        translation_service = TranslationService()
        active_keys = list(key_store.values())
        glossary = glossary_store if req.use_glossary else None

        translated_items = await translation_service.translate_subtitles(
            items=items,
            keys_pool=active_keys,
            source_lang=req.source_language,
            target_lang=req.target_language,
            glossary=glossary
        )

        if req.bilingual:
            exported_content = SubtitleService.export_bilingual_srt(translated_items)
        elif req.export_format == "vtt":
            exported_content = SubtitleService.export_vtt(translated_items)
        elif req.export_format == "ass":
            exported_content = SubtitleService.export_ass(translated_items)
        else:
            exported_content = SubtitleService.export_srt(translated_items)

        return {
            "status": "success",
            "item_count": len(translated_items),
            "export_format": req.export_format,
            "translated_content": exported_content
        }
    except Exception as e:
        logger.error(f"Subtitle translation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
        
        # If current item starts before the last item ends (overlap)
        if curr_start < last_end - 0.2:
            last_text = last_item.text.strip().lower()
            curr_text = item.text.strip().lower()
            
            # Simple substring or prefix match to identify duplicates
            if last_text in curr_text or curr_text in last_text or last_text[:10] == curr_text[:10]:
                if len(curr_text) > len(last_text):
                    unique_items[-1] = item  # Keep the longer, more contextual version
                continue
                
        unique_items.append(item)
        
    # Re-index items cleanly
    for idx, item in enumerate(unique_items, start=1):
        item.index = idx
        
    return unique_items


async def _run_video_pipeline_background(job_id: str, sandbox_dir: Path, video_path: Path, req: VideoProcessRequest):
    """Background orchestrator delegating to PipelineService."""
    from app.services.pipeline_service import PipelineService
    return await PipelineService.run_video_pipeline(
        job_id=job_id,
        sandbox_dir=sandbox_dir,
        video_path=video_path,
        req=req,
        active_keys=list(key_store.values()),
        glossary=glossary_store
    )

@router.post("/process", responses={500: {"description": "Upload processing failed"}})
async def process_video_upload(
    file: Annotated[UploadFile, File(...)],
    target_lang: Annotated[str, Form()] = "ar",
    engine: Annotated[str, Form()] = "gemini",
    mode: Annotated[str, Form()] = "merge",
    keep_srt: Annotated[str, Form()] = "true",
    audio_mode: Annotated[str, Form()] = "standard",
    bilingual: Annotated[str, Form()] = "false",
    font_size: Annotated[str, Form()] = "16",
    font_color: Annotated[str, Form()] = "#ffffff"
):
    """Synchronous endpoint to handle video upload from frontend, run ASR and Translation, and return SRT content."""
    media_service = MediaService()
    asr_service = ASRService()
    translation_service = TranslationService()
    
    _, sandbox_dir = media_service.create_job_sandbox()
    
    try:
        # 1. Save uploaded file safely
        safe_filename = Path(file.filename or "upload.tmp").name
        video_path = (sandbox_dir / safe_filename).resolve()
        if not video_path.is_relative_to(sandbox_dir.resolve()):
            raise HTTPException(status_code=400, detail="Invalid file path")
        def _save_upload_sync():
            import shutil
            with open(video_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        await asyncio.to_thread(_save_upload_sync)
            
        # 2. Analyze media details via FFprobe
        analyzer = AudioAnalyzer()
        metadata = await analyzer.analyze_media(video_path)
        
        # Resolve audio mode
        mode_enum = AudioMode.ENHANCED
        if audio_mode:
            try:
                mode_enum = AudioMode(audio_mode)
            except ValueError:
                pass

        # Extract Audio (16kHz WAV PCM)
        audio_path = await media_service.extract_audio_for_api(video_path, sandbox_dir, mode_enum)
        
        # Universal AI Vocal Isolation via ONNX MDX-Net before ASR transcription
        logger.info(f"Executing universal zero-PyTorch ONNX vocal isolation on uploaded file {file.filename}...")
        try:
            vocal_service = VocalIsolationService()
            audio_path = await vocal_service.isolate(video_path, sandbox_dir)
            logger.info(f"Vocal isolation successfully extracted speech/vocals: {audio_path.name}")
        except Exception as iso_err:
            logger.warning(f"Vocal isolation fallback notice (using clean PCM audio): {str(iso_err)}")

        logger.info(f"Processing upload for {file.filename} in mode '{mode}' using engine '{engine}' and audio_mode '{audio_mode}'...")
        
        # 3. ASR with engine-aware key filtering
        active_keys = list(key_store.values())
        if engine == "gemini":
            active_keys.sort(key=lambda k: 0 if k.provider in ["gemini", "groq"] else 1)
        elif engine == "gtx":
            active_keys.sort(key=lambda k: 0 if k.provider == "google_translate" else 1)

        # Truncate/chunk audio if needed
        chunker = AudioChunker()
        chunks = await chunker.chunk_audio(audio_path, metadata.duration_seconds, sandbox_dir)
        
        converter = FormatConverter()
        raw_items = []
        target_prov = active_keys[0].provider if active_keys else "groq"

        for idx, chunk in enumerate(chunks):
            # Format WAV chunk to optimal payload per provider
            upload_path, content_type = await converter.prepare_for_upload(chunk.path, target_prov, sandbox_dir)
            
            logger.info(f"Transcribing upload chunk {idx+1}/{len(chunks)} via {target_prov}...")
            chunk_items = await asr_service.transcribe(upload_path, keys_pool=active_keys, language="auto")
            
            # Realign chunk timestamps globally
            chunk_items_aligned = apply_chunk_offset(chunk_items, chunk.offset_seconds)
            raw_items.extend(chunk_items_aligned)

        # Clean overlap boundary redundancies
        if len(chunks) > 1:
            raw_items = de_duplicate_overlapping_subtitles(raw_items)

        # Stage 3.5: Music Intelligence & Ground-Truth Lyrics Alignment
        try:
            logger.info(f"Engaging Music Intelligence & Lyrics Grounding for upload: {file.filename}...")
            grounding_res = await LyricsGroundingService.ground_song_pipeline(
                video_path, raw_items
            )
            if grounding_res.is_grounded and grounding_res.subtitles:
                raw_items = grounding_res.subtitles
                logger.info(
                    f"🎵 Lyrics Grounding successfully synced {len(raw_items)} lines from {grounding_res.source}!"
                )
        except Exception as ground_err:
            logger.warning(f"Lyrics Grounding fallback notice (retaining ASR): {ground_err}")
        
        # 4. Translation

        translated_items = await translation_service.translate_subtitles(
            items=raw_items,
            keys_pool=active_keys,
            source_lang="auto",
            target_lang=target_lang,
            glossary=glossary_store
        )
        
        # 5. Export SRT
        is_bilingual = str(bilingual).lower().strip() == "true"
        if is_bilingual:
            srt_content = SubtitleService.export_bilingual_srt(raw_items, translated_items)
        else:
            srt_content = SubtitleService.export_srt(translated_items)
        logger.info(f"Successfully processed SRT subtitles for {file.filename} (mode: {mode}, bilingual: {is_bilingual}).")
        
        # Return the SRT content directly to the frontend
        return {
            "status": "success",
            "srt_content": srt_content,
            "video_url": None
        }
    except Exception as e:
        logger.error(f"Upload processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        media_service.purge_job_sandbox(sandbox_dir)



@router.post("/process/video")
async def process_video_pipeline(req: VideoProcessRequest, background_tasks: BackgroundTasks = None):
    """Starts video ASR + translation background pipeline."""
    video_path = Path(req.video_path)
    if not video_path.is_file():
        raise HTTPException(status_code=400, detail="Specified video file does not exist or is inaccessible.")
        
    media_service = MediaService()
    job_id, sandbox_dir = media_service.create_job_sandbox()

    # Trigger async execution task shielded from GC cancellation
    _bg_task = asyncio.create_task(_run_video_pipeline_background(job_id, sandbox_dir, video_path, req))
    _active_background_tasks.add(_bg_task)
    _bg_task.add_done_callback(_active_background_tasks.discard)

    return {
        "status": "started",
        "job_id": job_id,
        "video_name": video_path.name,
        "websocket_url": f"ws://127.0.0.1:{settings.PORT}/ws/progress/{settings.SESSION_TOKEN}"
    }


class LicenseActivationRequest(BaseModel):
    token: str


@router.get("/license/status")
async def get_license_status():
    """Returns current hardware fingerprint, AES-256-GCM encrypted license status, and support contacts."""
    hwid = HWIDGenerator.generate()
    validator = LicenseValidator()
    result = validator.validate(hwid)
    
    return {
        "hwid": hwid,
        "valid": result.valid,
        "is_authorized": result.is_authorized() if hasattr(result, "is_authorized") else result.valid,
        "message": result.message,
        "data": result.data,
        "support": {
            "whatsapp": settings.CONTACT_WHATSAPP,
            "telegram": settings.CONTACT_TELEGRAM
        }
    }


@router.get("/license/hwid")
async def get_license_hwid():
    """Returns current machine HWID and detailed hardware breakdown."""
    return {
        "hwid": HWIDGenerator.generate(),
        "hardware_components": HWIDGenerator.get_hardware_details()
    }


@router.post("/license/activate", responses={400: {"description": "Invalid or unauthorized license token"}})
async def activate_license(req: LicenseActivationRequest):
    """Verifies Ed25519 signed license token against HWID and stores in AES-256-GCM vault."""
    hwid = HWIDGenerator.generate()
    validator = LicenseValidator()
    
    result = validator.verify_license_string(req.token, hwid)
    if not result.valid or not result.is_authorized():
        raise HTTPException(status_code=400, detail=result.message)
        
    validator.save_license(req.token, hwid)
    return {
        "status": "success",
        "message": "تم التفعيل وحفظ الترخيص المشفر بنجاح",
        "data": result.data
    }


@router.post("/license/reset")
async def reset_license_endpoint():
    """Resets / clears currently saved license cache to test locked state (Debug only)."""
    if not settings.DEBUG:
        raise HTTPException(status_code=403, detail="Reset license is only allowed in DEBUG mode.")
    validator = LicenseValidator()
    if validator.cache_file.exists():
        validator.cache_file.unlink()
    return {"status": "success", "message": "تم حذف الترخيص وإعادة البرنامج لوضع القفل التجريبي بنجاح"}


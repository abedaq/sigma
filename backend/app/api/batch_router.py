"""
SIGMA_ASR_VTT - REST API Batch Router
Developer: أصيل السويدي
"""

import asyncio
from typing import List, Annotated
from fastapi import APIRouter, HTTPException, BackgroundTasks, File, UploadFile, Form

from app.core.models import BatchJobStatus
from app.services.media_service import MediaService
from app.services.batch_service import BatchService
from app.infrastructure.logger import logger
from app.core.config import settings
import shutil
import os
from pathlib import Path
import platform
import subprocess  # nosec B404
from pydantic import BaseModel

# Import the actual video processing logic
from app.api.router import _run_video_pipeline_background, VideoProcessRequest

router = APIRouter(prefix="/api/v1/process")

async def _process_batch_background(job_id: str, batch_service: BatchService, files: List[tuple], req_params: dict):
    """
    files is a list of tuples: (file_id, original_filename, temp_path)
    """
    batch_service.update_job_status(job_id, BatchJobStatus.PROCESSING)
    logger.info(f"Starting batch {job_id} with {len(files)} files.")
    
    # We will process them concurrently but with a limit. Let's use asyncio.Semaphore
    concurrency_limit = 2  # Adjust based on system capabilities or API limits
    semaphore = asyncio.Semaphore(concurrency_limit)
    
    async def process_single_file(file_info):
        file_id, original_filename, file_path = file_info
        async with semaphore:
            batch_service.update_file_status(file_id, BatchJobStatus.PROCESSING, phase="بدء المعالجة")
            logger.info(f"Batch {job_id}: Processing {original_filename}")
            
            try:
                v_req = VideoProcessRequest(
                    video_path=str(file_path),
                    source_language="auto",
                    target_language=req_params["target_lang"],
                    asr_provider="auto",
                    translation_provider=req_params["engine"],
                    embed_subtitles=(req_params["mode"] == "merge"),
                    audio_mode=req_params.get("audio_mode", "enhanced"),
                    enable_vocal_isolation=req_params.get("enable_vocal_isolation", False),
                    auto_detect_media=req_params.get("auto_detect_media", True),
                    enable_lyrics_grounding=req_params.get("enable_lyrics_grounding", True),
                    bilingual=req_params.get("bilingual", False),
                    font_size=req_params.get("font_size", 16),
                    font_color=req_params.get("font_color", "#ffffff")
                )

                
                # Mock a job ID for the underlying pipeline (we use file_id)
                # The pipeline expects job_id to be unique, we use file_id.
                media_service = MediaService()
                _, sandbox_dir = media_service.create_job_sandbox()
                
                # We need to adapt _run_video_pipeline_background to not conflict or we just run it.
                # Actually, _run_video_pipeline_background handles everything, including broadcasting.
                # But it broadcasts using job_id = file_id.
                # Let's call it.
                await _run_video_pipeline_background(file_id, sandbox_dir, file_path, v_req)
                
                # Check if successful by checking if translated SRT exists
                expected_srt = file_path.parent / f"{file_path.stem}_translated.srt"
                expected_original = file_path.parent / f"{file_path.stem}_original.srt"
                expected_merged = file_path.parent / f"{file_path.stem}_merged{file_path.suffix}"
                
                if expected_srt.exists():
                    out_srt = settings.OUTPUT_DIR / expected_srt.name
                    shutil.copy2(expected_srt, out_srt)
                    if expected_original.exists():
                        shutil.copy2(expected_original, settings.OUTPUT_DIR / expected_original.name)
                    
                    final_srt_path = str(out_srt)
                    final_video_path = None
                    
                    if expected_merged.exists():
                        out_vid = settings.OUTPUT_DIR / expected_merged.name
                        shutil.copy2(expected_merged, out_vid)
                        final_video_path = str(out_vid)
                    
                    batch_service.increment_completed_files(job_id, True)
                    batch_service.update_file_status(file_id=file_id, status=BatchJobStatus.COMPLETED, progress=100.0, phase="مكتمل", srt_path=final_srt_path, video_path=final_video_path)
                else:
                    batch_service.increment_completed_files(job_id, False)
                    batch_service.update_file_status(file_id, BatchJobStatus.FAILED, phase="فشل", error="لم يتم العثور على ملف الترجمة الناتج")
                    
            except Exception as e:
                logger.error(f"Batch {job_id}: File {original_filename} failed: {e}")
                batch_service.increment_completed_files(job_id, False)
                batch_service.update_file_status(file_id, BatchJobStatus.FAILED, phase="فشل", error=str(e))

    tasks = [process_single_file(f) for f in files]
    await asyncio.gather(*tasks)
    
    batch_service.update_job_status(job_id, BatchJobStatus.COMPLETED)
    logger.info(f"Batch {job_id} completed.")

@router.post("/batch", responses={500: {"description": "Batch processing failed"}})
async def process_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    target_lang: Annotated[str, Form()] = "ar",
    engine: Annotated[str, Form()] = "gemini",
    keep_srt: Annotated[str, Form()] = "true",
    audio_mode: Annotated[str, Form()] = "standard",
    mode: Annotated[str, Form()] = "merge",
    enable_vocal_isolation: Annotated[str, Form()] = "false",
    auto_detect_media: Annotated[str, Form()] = "true",
    enable_lyrics_grounding: Annotated[str, Form()] = "true",
    bilingual: Annotated[str, Form()] = "false",
    font_size: Annotated[str, Form()] = "16",
    font_color: Annotated[str, Form()] = "#ffffff"
):
    """Handles upload of multiple files and processes them in a batch background job."""
    batch_service = BatchService()
    media_service = MediaService()
    
    # 1. Create Batch Job in DB
    batch_job = batch_service.create_batch_job(
        total_files=len(files),
        target_lang=target_lang,
        engine=engine,
        mode=mode
    )
    
    _, batch_sandbox_dir = media_service.create_job_sandbox()
    
    saved_files = []
    
    for file in files:
        safe_filename = Path(file.filename or "file.tmp").name
        file_path = (batch_sandbox_dir / safe_filename).resolve()
        if not file_path.is_relative_to(batch_sandbox_dir.resolve()):
            raise HTTPException(status_code=400, detail="Invalid filename")
            
        # Add to DB
        batch_file = batch_service.add_file_to_batch(batch_job.job_id, safe_filename)
        
        def _save_upload_sync(f_obj, path):
            import shutil
            with open(path, "wb") as buffer:
                shutil.copyfileobj(f_obj.file, buffer)
                
        await asyncio.to_thread(_save_upload_sync, file, file_path)
        
        saved_files.append((batch_file.file_id, safe_filename, file_path))
        
    req_params = {
        "target_lang": target_lang,
        "engine": engine,
        "mode": mode,
        "keep_srt": keep_srt,
        "audio_mode": audio_mode,
        "bilingual": str(bilingual).lower().strip() == "true",
        "font_size": int(font_size) if str(font_size).isdigit() else 16,
        "font_color": font_color or "#ffffff",
        "enable_vocal_isolation": str(enable_vocal_isolation).lower().strip() == "true",
        "auto_detect_media": str(auto_detect_media).lower().strip() == "true",
        "enable_lyrics_grounding": str(enable_lyrics_grounding).lower().strip() == "true"
    }

    
    background_tasks.add_task(_process_batch_background, batch_job.job_id, batch_service, saved_files, req_params)
    
    return {
        "status": "started",
        "batch_id": batch_job.job_id,
        "total_files": len(files),
        "message": "Batch job started successfully."
    }

@router.get("/batch/{job_id}", responses={404: {"description": "Batch not found"}})
async def get_batch_status(job_id: str):
    """Returns the status and progress of a batch job."""
    from app.infrastructure.database import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM batch_jobs WHERE job_id = ?', (job_id,))
    job_row = cursor.fetchone()
    
    if not job_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Batch job not found")
        
    cursor.execute('SELECT * FROM batch_job_files WHERE job_id = ?', (job_id,))
    file_rows = cursor.fetchall()
    conn.close()
    
    from app.services.audio_analyzer import AudioAnalyzer
    analyzer = AudioAnalyzer()
    enriched_files = []
    for fr in file_rows:
        f_dict = dict(fr)
        m_type, m_label, m_conf = analyzer._classify_media_type(f_dict["original_filename"], 150.0, 2, 5000000)
        f_dict["detected_media_type"] = m_type
        f_dict["detected_media_label"] = m_label
        f_dict["detected_confidence"] = m_conf
        enriched_files.append(f_dict)
    
    return {
        "job_id": job_row["job_id"],
        "status": job_row["status"],
        "total_files": job_row["total_files"],
        "completed_files": job_row["completed_files"],
        "failed_files": job_row["failed_files"],
        "files": enriched_files
    }

class OpenRequest(BaseModel):
    path: str

@router.post("/open")
async def open_file_locally(req: OpenRequest):
    """Opens a file or directory using the OS default application."""
    target = Path(req.path).resolve()
    base_output = settings.OUTPUT_DIR.resolve()
    base_sandbox = settings.SANDBOX_DIR.resolve()

    # OWASP Security: Prevent path traversal outside authorized application workspaces
    if not (target.is_relative_to(base_output) or target.is_relative_to(base_sandbox)):
        logger.warning(f"Security blocked unauthorized open attempt: {req.path}")
        raise HTTPException(status_code=403, detail="Access denied: Path resides outside secure workspace boundaries")

    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        if platform.system() == "Windows":
            os.startfile(str(target))  # nosec B606
        elif platform.system() == "Darwin":
            subprocess.Popen(["/usr/bin/open", str(target)])  # nosec B603
        else:
            subprocess.Popen(["/usr/bin/xdg-open", str(target)])  # nosec B603
        return {"status": "opened"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/open-folder")
async def open_output_folder():
    """Opens the output directory."""
    path = str(settings.OUTPUT_DIR.resolve())
    try:
        if platform.system() == "Windows":
            os.startfile(path)  # nosec B606
        elif platform.system() == "Darwin":
            subprocess.Popen(["/usr/bin/open", path])  # nosec B603
        else:
            subprocess.Popen(["/usr/bin/xdg-open", path])  # nosec B603
        return {"status": "opened"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


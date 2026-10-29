"""
SIGMA_ASR_VTT - Batch Service
Developer: أصيل السويدي
"""
import uuid
from datetime import datetime

from typing import Optional, Callable
from app.core.models import BatchJob, BatchJobFile, BatchJobStatus, ProcessingStage, JobProgress
from app.infrastructure.database import get_db_connection

class BatchService:
    def __init__(self, notifier: Optional[Callable] = None):
        self._notifier = notifier

    def set_notifier(self, notifier: Callable) -> None:
        self._notifier = notifier

    def create_batch_job(self, total_files: int, target_lang: str, engine: str, mode: str) -> BatchJob:
        job_id = f"batch_{uuid.uuid4().hex[:8]}"
        created_at = datetime.now().isoformat()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO batch_jobs (job_id, status, created_at, total_files, target_lang, engine, mode)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (job_id, BatchJobStatus.PENDING, created_at, total_files, target_lang, engine, mode))
        
        conn.commit()
        conn.close()
        
        return BatchJob(
            job_id=job_id,
            status=BatchJobStatus.PENDING,
            created_at=created_at,
            total_files=total_files,
            target_lang=target_lang,
            engine=engine,
            mode=mode,
            files=[]
        )

    def add_file_to_batch(self, job_id: str, original_filename: str) -> BatchJobFile:
        file_id = f"f_{uuid.uuid4().hex[:8]}"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO batch_job_files (file_id, job_id, original_filename, status)
            VALUES (?, ?, ?, ?)
        ''', (file_id, job_id, original_filename, BatchJobStatus.PENDING))
        
        conn.commit()
        conn.close()
        
        return BatchJobFile(
            file_id=file_id,
            job_id=job_id,
            original_filename=original_filename,
            status=BatchJobStatus.PENDING
        )

    def update_job_status(self, job_id: str, status: BatchJobStatus):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if status in [BatchJobStatus.COMPLETED, BatchJobStatus.FAILED]:
            cursor.execute('''
                UPDATE batch_jobs SET status = ?, completed_at = ? WHERE job_id = ?
            ''', (status.value, datetime.now().isoformat(), job_id))
        else:
            cursor.execute('''
                UPDATE batch_jobs SET status = ? WHERE job_id = ?
            ''', (status.value, job_id))
            
        conn.commit()
        conn.close()

    def update_file_status(self, file_id: str, status: BatchJobStatus, progress: float = 0.0, phase: str = "", error: str = None, srt_path: str = None, video_path: str = None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE batch_job_files 
            SET status = ?, progress_percent = ?, current_phase = ?, error_message = ?, result_srt_path = ?, result_video_path = ?
            WHERE file_id = ?
        ''', (status.value, progress, phase, error, srt_path, video_path, file_id))
        
        conn.commit()
        conn.close()

    def increment_completed_files(self, job_id: str, is_success: bool = True):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if is_success:
            cursor.execute('UPDATE batch_jobs SET completed_files = completed_files + 1 WHERE job_id = ?', (job_id,))
        else:
            cursor.execute('UPDATE batch_jobs SET failed_files = failed_files + 1 WHERE job_id = ?', (job_id,))
            
        conn.commit()
        conn.close()

    async def broadcast_batch_progress(self, job_id: str, file_id: str, filename: str, stage: ProcessingStage, progress_percent: float, current_step_description: str, error_message: str = None):
        """Broadcast progress to the frontend via WebSockets."""
        prog = JobProgress(
            job_id=file_id, 
            file_name=filename,
            stage=stage,
            progress_percent=progress_percent,
            current_step_description=current_step_description,
            error_message=error_message
        )
        
        payload = prog.model_dump()
        payload["batch_id"] = job_id
        
        if self._notifier:
            await self._notifier(payload)
        else:
            try:
                from app.api.websocket import ws_manager
                await ws_manager.broadcast(payload)
            except Exception:
                pass

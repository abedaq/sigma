import asyncio
import os
from datetime import datetime, timedelta, timezone
from app.infrastructure.logger import logger
from app.infrastructure.database import get_db_connection

CLEANUP_INTERVAL_SECONDS = 3600  # Check every 1 hour
MAX_AGE_HOURS = 48  # Delete jobs older than 48 hours

async def garbage_collector_task():
    """Background task to periodically clean up old batch jobs and their associated temporary files."""
    logger.info("Garbage Collector task started.")
    # Run immediate cleanup on startup
    try:
        await asyncio.to_thread(cleanup_old_data)
    except Exception as e:
        logger.warning(f"Initial garbage collection error: {e}")

    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            await asyncio.to_thread(cleanup_old_data)
        except asyncio.CancelledError:
            logger.info("Garbage Collector task stopped.")
            break
        except Exception as e:
            logger.error(f"Error in Garbage Collector task: {e}")

def cleanup_old_data():
    """Removes DB records and files for jobs older than MAX_AGE_HOURS."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate the cutoff time
        cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=MAX_AGE_HOURS)).isoformat()
        
        # Find old jobs
        cursor.execute("SELECT job_id FROM batch_jobs WHERE created_at < ?", (cutoff_time,))
        old_jobs = cursor.fetchall()
        
        if not old_jobs:
            logger.info("Garbage Collector: No old jobs to clean up.")
            conn.close()
            return
            
        for job in old_jobs:
            job_id = job["job_id"]
            # Get associated result files to delete from disk
            cursor.execute("SELECT result_srt_path, result_video_path FROM batch_job_files WHERE job_id = ?", (job_id,))
            files = cursor.fetchall()
            
            for file_record in files:
                srt_path = file_record["result_srt_path"]
                vid_path = file_record["result_video_path"]
                
                if srt_path and os.path.exists(srt_path):
                    try:
                        os.remove(srt_path)
                        logger.info(f"Garbage Collector: Deleted old SRT {srt_path}")
                    except Exception as e:
                        logger.error(f"Garbage Collector: Failed to delete {srt_path}: {e}")

                if vid_path and os.path.exists(vid_path):
                    try:
                        os.remove(vid_path)
                        logger.info(f"Garbage Collector: Deleted old Video {vid_path}")
                    except Exception as e:
                        logger.error(f"Garbage Collector: Failed to delete {vid_path}: {e}")
                        
            # Delete DB records (cascading can be done manually here if not set in DB)
            cursor.execute("DELETE FROM batch_job_files WHERE job_id = ?", (job_id,))
            cursor.execute("DELETE FROM batch_jobs WHERE job_id = ?", (job_id,))
            
        conn.commit()
        conn.close()
        logger.info(f"Garbage Collector: Cleaned up {len(old_jobs)} old batch jobs.")
    except Exception as e:
        logger.error(f"Garbage Collector: Cleanup failed: {e}")

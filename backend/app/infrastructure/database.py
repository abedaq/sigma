"""
SIGMA_ASR_VTT - Local SQLite Database Configuration
Developer: أصيل السويدي
"""
import sqlite3
from pathlib import Path
from app.core.config import settings

# DB path relative to the active writable base directory
DB_PATH = settings.BASE_DIR / "app_data.db"

def get_db_connection():
    """Returns a connected SQLite instance with WAL Mode enabled for concurrent batch stability."""
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_db():
    """Initializes the database schema if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table for API Keys
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            provider TEXT NOT NULL,
            encrypted_key TEXT NOT NULL,
            masked_key TEXT NOT NULL,
            priority INTEGER DEFAULT 1,
            status TEXT DEFAULT 'active',
            quota_limit_rpm INTEGER DEFAULT 15,
            current_rpm INTEGER DEFAULT 0,
            remaining_quota_percent REAL DEFAULT 100.0
        )
    ''')
    
    # Table for Glossary
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS glossary (
            term TEXT PRIMARY KEY,
            translation TEXT NOT NULL
        )
    ''')
    
    # Table for Batch Jobs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS batch_jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            total_files INTEGER DEFAULT 0,
            completed_files INTEGER DEFAULT 0,
            failed_files INTEGER DEFAULT 0,
            target_lang TEXT DEFAULT 'ar',
            engine TEXT DEFAULT 'gemini',
            mode TEXT DEFAULT 'merge'
        )
    ''')
    
    # Table for Batch Job Files
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS batch_job_files (
            file_id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            progress_percent REAL DEFAULT 0.0,
            current_phase TEXT DEFAULT '',
            error_message TEXT,
            result_srt_path TEXT,
            result_video_path TEXT,
            FOREIGN KEY(job_id) REFERENCES batch_jobs(job_id)
        )
    ''')

    # Table for Persistent Translation Cache (Saves 100% tokens on repeated lines)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS translation_cache (
            cache_key TEXT PRIMARY KEY,
            source_text TEXT NOT NULL,
            source_lang TEXT NOT NULL,
            target_lang TEXT NOT NULL,
            translated_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table for Cached Ground-Truth Lyrics & Timestamps
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lyrics_cache (
            track_key TEXT PRIMARY KEY,
            artist TEXT,
            title TEXT,
            source TEXT,
            synced_lyrics TEXT,
            plain_lyrics TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()



# Initialize DB on import
init_db()

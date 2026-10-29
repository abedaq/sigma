"""
SIGMA_ASR_VTT - Database Operations
Developer: أصيل السويدي
"""
from typing import Dict, Optional, List
from app.infrastructure.database import get_db_connection
from app.core.models import APIKeyConfig, KeyStatus

def get_all_keys() -> Dict[str, APIKeyConfig]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM api_keys")
    rows = cursor.fetchall()
    conn.close()
    
    keys = {}
    for row in rows:
        key_config = APIKeyConfig(
            id=row['id'],
            name=row['name'],
            provider=row['provider'],
            encrypted_key=row['encrypted_key'],
            masked_key=row['masked_key'],
            priority=row['priority'],
            status=KeyStatus(row['status']),
            quota_limit_rpm=row['quota_limit_rpm'],
            current_rpm=row['current_rpm'],
            remaining_quota_percent=row['remaining_quota_percent']
        )
        keys[row['id']] = key_config
    return keys

def add_or_update_key(key: APIKeyConfig):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO api_keys (id, name, provider, encrypted_key, masked_key, priority, status, quota_limit_rpm, current_rpm, remaining_quota_percent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            provider=excluded.provider,
            encrypted_key=excluded.encrypted_key,
            masked_key=excluded.masked_key,
            priority=excluded.priority,
            status=excluded.status,
            quota_limit_rpm=excluded.quota_limit_rpm,
            current_rpm=excluded.current_rpm,
            remaining_quota_percent=excluded.remaining_quota_percent
    ''', (key.id, key.name, key.provider, key.encrypted_key, key.masked_key, key.priority, key.status.value, key.quota_limit_rpm, key.current_rpm, key.remaining_quota_percent))
    conn.commit()
    conn.close()

def delete_key(key_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
    conn.commit()
    conn.close()

def get_glossary() -> Dict[str, str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM glossary")
    rows = cursor.fetchall()
    conn.close()
    
    return {row['term']: row['translation'] for row in rows}

def update_glossary_item(term: str, translation: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO glossary (term, translation)
        VALUES (?, ?)
        ON CONFLICT(term) DO UPDATE SET translation=excluded.translation
    ''', (term, translation))
    conn.commit()
    conn.close()

import hashlib

def _make_cache_key(text: str, sl: str, tl: str) -> str:
    norm = f"{sl.lower().strip()}_{tl.lower().strip()}_{text.strip().lower()}"
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()

def get_cached_translation(text: str, source_lang: str, target_lang: str) -> Optional[str]:
    """Retrieves cached translation from persistent SQLite disk storage."""
    key = _make_cache_key(text, source_lang, target_lang)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT translated_text FROM translation_cache WHERE cache_key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["translated_text"] if row else None

def set_cached_translation(text: str, source_lang: str, target_lang: str, translated_text: str) -> None:
    """Saves translation to persistent SQLite disk storage."""
    if not text.strip() or not translated_text.strip():
        return
    key = _make_cache_key(text, source_lang, target_lang)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO translation_cache (cache_key, source_text, source_lang, target_lang, translated_text)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(cache_key) DO UPDATE SET translated_text = excluded.translated_text
    ''', (key, text.strip(), source_lang.strip(), target_lang.strip(), translated_text.strip()))
    conn.commit()
    conn.close()


def get_cached_translations_batch(texts: List[str], source_lang: str, target_lang: str) -> Dict[str, str]:
    """Batch retrieves cached translations from SQLite in a single query."""
    if not texts:
        return {}
    key_map = {_make_cache_key(t, source_lang, target_lang): t for t in texts}
    keys = list(key_map.keys())
    results: Dict[str, str] = {}
    conn = get_db_connection()
    cursor = conn.cursor()
    chunk_size = 500
    for i in range(0, len(keys), chunk_size):
        chunk_keys = keys[i:i + chunk_size]
        placeholders = ",".join("?" for _ in chunk_keys)
        cursor.execute(f"SELECT cache_key, translated_text FROM translation_cache WHERE cache_key IN ({placeholders})", chunk_keys)
        for row in cursor.fetchall():
            results[row["cache_key"]] = row["translated_text"]
    conn.close()
    return results


def set_cached_translations_batch(entries: List[tuple[str, str, str, str]]) -> None:
    """Batch inserts translations into SQLite in a single transaction."""
    if not entries:
        return
    records = []
    for text, sl, tl, trans in entries:
        if text.strip() and trans.strip():
            k = _make_cache_key(text, sl, tl)
            records.append((k, text.strip(), sl.strip(), tl.strip(), trans.strip()))
    if not records:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT INTO translation_cache (cache_key, source_text, source_lang, target_lang, translated_text)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(cache_key) DO UPDATE SET translated_text = excluded.translated_text
    ''', records)
    conn.commit()
    conn.close()


def _make_lyrics_cache_key(artist: Optional[str], title: str) -> str:
    art = (artist or "").strip().lower()
    tit = title.strip().lower()
    return hashlib.sha256(f"{art}___{tit}".encode("utf-8")).hexdigest()


def get_cached_lyrics(artist: Optional[str], title: str) -> Optional[dict]:
    """Retrieves cached ground-truth lyrics from SQLite storage."""
    key = _make_lyrics_cache_key(artist, title)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lyrics_cache WHERE track_key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "artist": row["artist"],
            "title": row["title"],
            "source": row["source"],
            "synced_lyrics": row["synced_lyrics"],
            "plain_lyrics": row["plain_lyrics"],
        }
    return None


def set_cached_lyrics(artist: Optional[str], title: str, source: str, synced_lyrics: Optional[str], plain_lyrics: Optional[str]) -> None:
    """Stores fetched lyrics in SQLite storage for zero external calls on replay."""
    key = _make_lyrics_cache_key(artist, title)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO lyrics_cache (track_key, artist, title, source, synced_lyrics, plain_lyrics)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(track_key) DO UPDATE SET
            source = excluded.source,
            synced_lyrics = excluded.synced_lyrics,
            plain_lyrics = excluded.plain_lyrics
    ''', (key, (artist or "").strip(), title.strip(), source, synced_lyrics, plain_lyrics))
    conn.commit()
    conn.close()



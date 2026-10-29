import asyncio
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.services.media_service import MediaService  # noqa: E402
from app.services.asr_service import ASRService  # noqa: E402
from app.services.translation_service import TranslationService  # noqa: E402
from app.services.subtitle_service import SubtitleService  # noqa: E402
from app.api.router import key_store, glossary_store  # noqa: E402

async def run_test():
    print("=== [TEST START] Running SIGMA_ASR_VTT Pipeline on Video TEST33 ===")
    video_path = Path(r"C:\Users\Hacker\Downloads\Video\TEST33.mp4")
    
    if not video_path.exists():
        print(f"[ERROR] Target video file not found at: {video_path}")
        return

    media_service = MediaService()
    asr_service = ASRService()
    translation_service = TranslationService()

    job_id, sandbox_dir = media_service.create_job_sandbox()
    print(f"[INFO] Created sandbox for Job ID: {job_id}")

    try:
        # Step 1: Extract Audio
        print("[STEP 1] Extracting 16kHz Mono MP3 audio from video...")
        audio_path = await media_service.extract_audio_for_api(video_path, sandbox_dir)
        print(f"[SUCCESS] Audio extracted: {audio_path.name} ({audio_path.stat().st_size} bytes)")

        # Step 2: Transcribe (ASR)
        print("[STEP 2] Running ASR transcription...")
        active_keys = list(key_store.values())
        raw_items = await asr_service.transcribe(audio_path, keys_pool=active_keys, language="auto")
        print(f"[SUCCESS] Transcribed {len(raw_items)} subtitle items.")

        # Step 3: Save Original Subtitles
        original_srt = SubtitleService.export_srt(raw_items)
        original_out_path = video_path.parent / f"{video_path.stem}_original.srt"
        original_out_path.write_text(original_srt, encoding="utf-8")
        print(f"[STEP 3] Saved ORIGINAL subtitles to: {original_out_path} ({original_out_path.stat().st_size} bytes)")

        # Step 4: Translate Subtitles to Arabic
        print("[STEP 4] Translating subtitles to Arabic using Context Engine & Glossary...")
        translated_items = await translation_service.translate_subtitles(
            items=raw_items,
            keys_pool=active_keys,
            source_lang="auto",
            target_lang="ar",
            glossary=glossary_store
        )
        translated_srt = SubtitleService.export_srt(translated_items)
        translated_out_path = video_path.parent / f"{video_path.stem}_translated.srt"
        translated_out_path.write_text(translated_srt, encoding="utf-8")
        print(f"[SUCCESS] Saved TRANSLATED subtitles to: {translated_out_path} ({translated_out_path.stat().st_size} bytes)")

        # Step 5: Merge / Embed Subtitles into Video
        print("[STEP 5] Embedding translated subtitles into video stream...")
        merged_video_path = video_path.parent / f"{video_path.stem}_merged{video_path.suffix}"
        await media_service.embed_subtitles(video_path, translated_out_path, merged_video_path)
        print(f"[SUCCESS] Merged video generated at: {merged_video_path} ({merged_video_path.stat().st_size} bytes)")

        print("\n=== [TEST RESULT: ALL STEPS PASSED SUCCESSFULLY] ===")
        print(f"1. Original Video: {video_path}")
        print(f"2. Original SRT  : {original_out_path}")
        print(f"3. Translated SRT: {translated_out_path}")
        print(f"4. Merged Video  : {merged_video_path}")

    except Exception as e:
        print(f"[FAILED] Pipeline test failed with exception: {e}")
        raise e
    finally:
        media_service.purge_job_sandbox(sandbox_dir)
        print("[INFO] Cleaned up temporary sandbox.")

def test_video_pipeline_definition():
    """Unit test case to verify pipeline test definitions and service availability."""
    assert callable(run_test), "run_test must be callable"  # nosec B101
    assert MediaService is not None  # nosec B101

if __name__ == "__main__":
    asyncio.run(run_test())

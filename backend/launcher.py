"""
SIGMA_ASR_VTT - Desktop Launcher & Executable Entrypoint
Developer: أصيل السويدي
"""
import sys
import os
import time
import webbrowser
import threading
from pathlib import Path

# Ensure backend directory is in sys.path
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from app.core.config import settings
import uvicorn

def _open_browser_when_ready(url: str, delay_seconds: float = 1.2):
    """Waits for server socket to initialize then opens default web browser."""
    time.sleep(delay_seconds)
    try:
        webbrowser.open(url)
    except Exception:
        pass

def main():
    print("=" * 65)
    print("           SIGMA VTT - AI Video Translation & Subtitles")
    print("                      المطور: أصيل السويدي")
    print("=" * 65)
    print(f"[*] Starting local server at http://{settings.HOST}:{settings.PORT}")
    print(f"[*] Data directory: {settings.BASE_DIR}")
    print("[*] Press Ctrl+C in this console to stop the server.")
    print("-" * 65)

    # Spawn thread to launch browser once ASGI server is listening
    browser_thread = threading.Thread(
        target=_open_browser_when_ready,
        args=(f"http://{settings.HOST}:{settings.PORT}", 1.5),
        daemon=True
    )
    browser_thread.start()

    # Run Uvicorn ASGI server
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="info" if not settings.DEBUG else "debug",
        access_log=False
    )

if __name__ == "__main__":
    main()

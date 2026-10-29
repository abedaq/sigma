"""
SIGMA_ASR_VTT - Infrastructure Sanitized Logger & Rich Error Diagnostic Engine
Developer: أصيل السويدي
"""

import sys
import json
import logging
import traceback
from datetime import datetime
from typing import List, Dict, Optional
from collections import deque

from rich.traceback import install as install_rich_traceback
from app.core.config import settings
from app.core.security import SensitiveDataRedactor

# Install Rich detailed traceback formatting
install_rich_traceback(show_locals=True, width=120)

# In-memory thread-safe Ring Buffer for AI Agent / Developer live error introspection
_MAX_ERROR_HISTORY = 50
_recent_errors_buffer: deque = deque(maxlen=_MAX_ERROR_HISTORY)

def record_error_event(
    error_type: str,
    message: str,
    module: str = "",
    function: str = "",
    line_no: int = 0,
    traceback_str: str = "",
    context: Optional[dict] = None
) -> Dict:
    """Records structured error event for AI agent diagnostics & developer debugging."""
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "error_type": error_type,
        "message": message,
        "module": module,
        "function": function,
        "line_number": line_no,
        "traceback": traceback_str,
        "context": context or {}
    }
    _recent_errors_buffer.appendleft(event)

    # Append to structured jsonl log file
    try:
        err_log_file = settings.LOGS_DIR / "error_trace.jsonl"
        with open(err_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass

    return event

def get_recent_errors(limit: int = 20) -> List[Dict]:
    """Returns recent error events captured across backend services."""
    return list(_recent_errors_buffer)[:limit]

def clear_error_logs() -> None:
    """Clears in-memory error buffer."""
    _recent_errors_buffer.clear()

def get_logger(name: str = "SIGMA_ASR_VTT") -> logging.Logger:
    """Configures and returns a sanitized logger with automatic key redaction."""
    logger_instance = logging.getLogger(name)
    if logger_instance.handlers:
        return logger_instance

    logger_instance.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Ensure standard streams handle emojis and special UTF-8 characters
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(SensitiveDataRedactor())
    logger_instance.addHandler(console_handler)

    # File Handler
    log_file = settings.LOGS_DIR / "sigma_vtt.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(SensitiveDataRedactor())
    logger_instance.addHandler(file_handler)

    return logger_instance

logger = get_logger()

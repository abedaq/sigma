"""
SIGMA_ASR_VTT - Application Configuration
Developer: أصيل السويدي
"""

import sys
import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Detect standalone frozen binary mode (PyInstaller)
IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    _RESOURCES_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    _DATA_DIR = Path(os.environ.get("LOCALAPPDATA", os.environ.get("APPDATA", str(Path.home())))) / "SIGMA_ASR_VTT"
else:
    _SRC_BASE = Path(__file__).resolve().parent.parent.parent
    _RESOURCES_DIR = _SRC_BASE
    _DATA_DIR = _SRC_BASE

class Settings(BaseSettings):
    PROJECT_NAME: str = "SIGMA_ASR_VTT"
    VERSION: str = "3.0.0"
    DEVELOPER: str = "أصيل السويدي"
    DEBUG: bool = False
    
    # Paths
    BASE_DIR: Path = _DATA_DIR
    RESOURCES_DIR: Path = _RESOURCES_DIR
    TEMP_DIR: Path = _DATA_DIR / "temp"
    SANDBOX_DIR: Path = _DATA_DIR / "temp"
    LOGS_DIR: Path = _DATA_DIR / "logs"
    OUTPUT_DIR: Path = _DATA_DIR / "outputs"
    MODELS_DIR: Path = _RESOURCES_DIR / "models"
    BIN_DIR: Path = _RESOURCES_DIR / "bin"
    KEYS_DIR: Path = _DATA_DIR / "keys"
    LICENSE_FILE_PATH: Path = _DATA_DIR / "license.dat"
    FRONTEND_DIR: Path = (_RESOURCES_DIR / "frontend_dist") if IS_FROZEN else (_DATA_DIR.parent / "frontend" / "dist")
    
    # Security
    VAULT_SECRET_KEY: str = os.getenv("VAULT_SECRET_KEY", "sigma_vtt_default_fernet_key_change_in_prod_32bytes=")
    SESSION_TOKEN: str = ""
    
    # Licensing & Contacts (Yemeni context defaults, customizable via .env)
    CONTACT_WHATSAPP: str = os.getenv("CONTACT_WHATSAPP", "+967777000000")
    CONTACT_TELEGRAM: str = os.getenv("CONTACT_TELEGRAM", "https://t.me/sigma_support")
    
    # Server settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Register portable bundled ffmpeg/ffprobe binary directory in PATH if present
if settings.BIN_DIR.exists():
    _bin_str = str(settings.BIN_DIR)
    if _bin_str not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{_bin_str}{os.pathsep}{os.environ.get('PATH', '')}"

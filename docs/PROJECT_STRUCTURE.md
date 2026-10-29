# SIGMA_ASR_VTT - Project Structure

**Developer & Main Contributor:** أصيل السويدي

```text
SIGMA_ASR_VTT/
├── docs/
│   ├── ARCHITECTURE.md             # System architecture & layer boundaries
│   ├── PROJECT_STRUCTURE.md        # File map & directory responsibilities
│   ├── DEVELOPMENT_RULES.md        # Strict developer rules & prohibitions
│   ├── CODING_STANDARDS.md         # Formatting, typing & SOLID principles
│   ├── SECURITY_RULES.md           # Secure SDLC, OWASP, AES vault & sanitization
│   ├── ASR_PIPELINE.md             # Cloud ASR preparation & hallucination guard
│   ├── TRANSLATION_PIPELINE.md     # Context sliding window, glossary & profiles
│   ├── API_INTEGRATION.md          # Provider pattern, rate limits & failover
│   └── ERROR_HANDLING.md           # Domain exception taxonomy & mapping
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── router.py           # FastAPI REST endpoints
│   │   │   └── websocket.py        # Real-time WebSocket progress broadcaster
│   │   ├── core/
│   │   │   ├── config.py           # Settings & environment configuration
│   │   │   ├── exceptions.py       # Domain exception classes
│   │   │   ├── models.py           # Pydantic schemas & domain contracts
│   │   │   └── security.py         # AES Fernet Key Vault & Log Redactor
│   │   ├── integrations/
│   │   │   ├── base_provider.py    # Abstract Provider Interfaces
│   │   │   ├── gemini.py           # Gemini Audio & Translation Provider
│   │   │   ├── google_translate.py # Google Translate Provider
│   │   │   └── speechmatics.py     # Speechmatics Cloud ASR Provider
│   │   ├── services/
│   │   │   ├── asr_service.py      # ASR Manager & Hallucination Guard
│   │   │   ├── media_service.py    # Safe FFmpeg execution & audio extraction
│   │   │   ├── subtitle_service.py # SRT/VTT/ASS Parser & Validator
│   │   │   └── translation_service.py # Context Translator & Glossary Engine
│   │   └── infrastructure/
│   │       ├── logger.py           # Sanitized logging with level controls
│   │       └── process_manager.py  # Safe Subprocess runner & cancellation
│   ├── tests/                      # Pytest unit & integration tests
│   ├── main.py                     # ASGI Backend entrypoint & token setup
│   └── requirements.txt            # Lightweight Python dependencies
└── frontend/                       # Tauri (Rust) + Vue 3 / Vite / TS Frontend
```

## Module Responsibilities

- **`backend/app/api/`**: Exposes REST and WebSocket endpoints. No business logic.
- **`backend/app/core/`**: Defines application state, models, security encryption, and exceptions.
- **`backend/app/integrations/`**: Encapsulates external cloud API communications.
- **`backend/app/services/`**: Orchestrates pipelines (ASR, Translation, Subtitles, Media).
- **`backend/app/infrastructure/`**: Handles filesystem, process isolation, and logging.

# SIGMA_ASR_VTT - System Architecture

**Developer & Main Contributor:** أصيل السويدي

## Architectural Overview

SIGMA_ASR_VTT is built upon a **Modern Hybrid Architecture** designed to deliver extreme performance, security, and visual elegance for audio/video speech recognition (ASR) and subtitle translation.

```text
+-----------------------------------------------------------------------+
|                       Presentation Layer (Frontend)                   |
|           Tauri (Rust) + Vue 3 (Composition API) + TypeScript          |
|                 Custom Vanilla CSS & Design Tokens (Dark UI)          |
+-----------------------------------------------------------------------+
                                  |
                                  | WebSocket / SSE & REST API
                                  | (Session Security Token Protected)
                                  v
+-----------------------------------------------------------------------+
|                    Application / Communication Layer                  |
|               FastAPI Asynchronous Web Engine & Pydantic              |
+-----------------------------------------------------------------------+
                                  |
                                  v
+-----------------------------------------------------------------------+
|                       Core / Domain Services Layer                    |
|  +-----------------------+  +------------------+  +----------------+  |
|  | Cloud ASR Provider Mgr|  | Translation Serv |  | Subtitle Serv  |  |
|  | (Speechmatics, Gemini)|  | (Context Chunk)  |  | (SRT/VTT/ASS)  |  |
|  +-----------------------+  +------------------+  +----------------+  |
|  +-----------------------+  +------------------+                      |
|  | Media & FFmpeg Exec   |  | AES Key Vault    |                      |
|  | (16kHz Mono MP3 Temp) |  | (Auto Failover)  |                      |
|  +-----------------------+  +------------------+                      |
+-----------------------------------------------------------------------+
                                  |
                                  v
+-----------------------------------------------------------------------+
|                        Infrastructure Layer                           |
|       Sanitized Logger, Temp Directory Manager (UUID Sandbox),       |
|            Subprocess Execution & Magic Byte File Inspector           |
+-----------------------------------------------------------------------+
```

## Layer Responsibilities & Boundaries

### 1. Presentation Layer (`frontend/`)
- Built with Tauri, Vue 3, Vite, and TypeScript.
- Styled using Custom Vanilla CSS for maximum visual excellence, dark themes, and responsive micro-animations.
- **Strict Prohibition:** Contains NO business logic, NO FFmpeg calls, NO ASR/Translation logic, and NO API keys.

### 2. Application & Communication Layer (`backend/app/api/`)
- FastAPI ASGI server exposing asynchronous REST endpoints and real-time WebSocket broadcasting.
- Protected by dynamic One-Time Session Security Tokens.
- Strictly validates all incoming requests using Pydantic schemas.

### 3. Core / Domain & Services Layer (`backend/app/core/` & `backend/app/services/`)
- Encapsulates all domain entities, contracts, and business rules.
- **Cloud ASR Service:** Coordinates 100% cloud-based speech recognition (Speechmatics, Gemini Audio API, etc.). Applies ASR Hallucination Guard.
- **Translation Service:** Manages sliding-window context chunking, Terminology Glossary injection, and Translation Profiles.
- **Subtitle Service:** Handles SRT, VTT, and ASS parsing, timestamp preservation, and structural validation.
- **Media Service:** Executes safe, parameterized FFmpeg audio extraction to 16kHz Mono format.
- **Key Vault:** Manages military-grade AES encryption for API keys, rate limit quotas, and circuit breaker failover.

### 4. Infrastructure Layer (`backend/app/infrastructure/`)
- Provides safe OS process execution, temporary directory sandboxing (UUID lifecycle), sanitized logging (log redaction), and Magic Byte file validation.

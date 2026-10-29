# SIGMA_ASR_VTT - Security Rules & OWASP Compliance

**Developer & Main Contributor:** أصيل السويدي

## Security Architecture & Practices

### 1. API Secret Protection (Data at Rest & Memory)
- All user API keys (Gemini, Speechmatics, etc.) are encrypted using **AES-256 Fernet encryption** before being persisted.
- Keys are masked/redacted in UI views (`AIza**********euvU`).
- **Log Redaction Filter:** A custom logging filter intercepts log records and redacts any key pattern, token, or password before writing to disk or terminal.

### 2. File Security & Validation
- **Magic Byte Inspection:** File extensions are ignored for security checks. The backend reads initial file bytes (Magic Signatures) to verify actual MIME types (e.g. MP4, MKV, WAV).
- **Path Traversal Prevention:** All file paths are resolved and validated to ensure they remain inside allowed user directories or sandboxed temp folders.

### 3. Process Execution & Subprocesses
- **No Shell Execution:** FFmpeg and system commands pass arguments strictly as string lists (`["ffmpeg", "-i", input_path, ...]`).
- **Exit Code Verification:** Subprocess exit codes are checked. Non-zero exit codes raise explicit `FileProcessingError`.

### 4. Sandboxed Temp Directories
- Every job operates in a unique UUID directory (`/tmp/sigma_vtt_<uuid>/`).
- Automatic cleanup purges temporary audio files upon completion or cancellation.

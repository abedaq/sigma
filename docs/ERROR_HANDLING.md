# SIGMA_ASR_VTT - Error Handling & Exception Taxonomy

**Developer & Main Contributor:** أصيل السويدي

## Exception Class Hierarchy

All domain exceptions inherit from the base `SigmaVTTError`:

```text
SigmaVTTError (Base Exception)
├── ValidationError        # Input file, parameter, or schema validation failures
├── ASRError               # Speech recognition service exceptions
├── TranslationError       # Translation service or API exceptions
├── ProviderError          # Integration client failures
│   └── RateLimitError     # Quota exceeded / HTTP 429 exceptions
├── FileProcessingError    # FFmpeg or filesystem operation errors
└── ConfigurationError     # Key vault, settings, or environment errors
```

## Error Handling Directives
1. **User-Friendly Error Messages:** Exceptions expose clean, localized error messages to the frontend UI.
2. **Developer Traceback Logs:** Full sanitized tracebacks (with secrets redacted) are logged for developer diagnostic analysis.
3. **No Exception Swallowing:** Naked `except:` or `except Exception: pass` blocks are strictly banned across the codebase.

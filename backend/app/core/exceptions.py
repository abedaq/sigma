"""
SIGMA_ASR_VTT - Core Exception Hierarchy
Developer: أصيل السويدي
"""

class SigmaVTTError(Exception):
    """Base exception for all domain errors within SIGMA_ASR_VTT."""
    def __init__(self, message: str, details: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.details = details

class ValidationError(SigmaVTTError):
    """Raised when input validation fails (invalid file format, magic byte mismatch, missing parameter)."""
    pass

class ASRError(SigmaVTTError):
    """Raised when speech recognition processing encounters an error."""
    pass

class TranslationError(SigmaVTTError):
    """Raised when translation pipeline encounters an error."""
    pass

class ProviderError(SigmaVTTError):
    """Raised when an external cloud API provider fails."""
    pass

class RateLimitError(ProviderError):
    """Raised when an API provider exceeds rate limits or quota (HTTP 429)."""
    def __init__(self, message: str, provider_name: str, retry_after: int = 60, details: str = "") -> None:
        super().__init__(message, details)
        self.provider_name = provider_name
        self.retry_after = retry_after

class FileProcessingError(SigmaVTTError):
    """Raised when FFmpeg subprocess or filesystem operations fail."""
    pass

class ConfigurationError(SigmaVTTError):
    """Raised when configuration, environment, or key vault initialization fails."""
    pass

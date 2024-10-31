class OmniException(Exception):
    """Base exception for all Omni-related errors."""
    pass

class EdgeProcessingError(OmniException):
    """Raised when there's an error in edge processing."""
    pass

class ResourceInitializationError(OmniException):
    """Raised when resource initialization fails."""
    pass

class ConfigurationError(OmniException):
    """Raised when there's an error in configuration."""
    pass

class SpeechRecognitionError(OmniException):
    """Raised when speech recognition fails."""
    pass

class TTSError(OmniException):
    """Raised when text-to-speech fails."""
    pass

class WakeWordError(OmniException):
    """Raised when wake word detection fails."""
    pass

class AudioDeviceError(OmniException):
    """Raised when there's an issue with audio devices."""
    pass

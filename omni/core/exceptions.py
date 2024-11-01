"""Custom exceptions for the application."""

class OmniError(Exception):
    """Base exception for all application errors."""
    pass

# Resource and Initialization Errors
class ResourceError(OmniError):
    """Base class for resource-related errors."""
    pass

class ResourceInitializationError(ResourceError):
    """Error initializing a resource."""
    pass

class ResourceNotFoundError(ResourceError):
    """Resource not found error."""
    pass

class ResourceUnavailableError(ResourceError):
    """Resource temporarily unavailable."""
    pass

# Configuration Errors
class ConfigError(OmniError):
    """Configuration related errors."""
    pass

class ValidationError(OmniError):
    """Validation related errors."""
    pass

# Service Errors
class ServiceError(OmniError):
    """Service related errors."""
    pass

class APIError(ServiceError):
    """API related errors."""
    pass

class DatabaseError(ServiceError):
    """Database related errors."""
    pass

class NetworkError(ServiceError):
    """Network related errors."""
    pass

# Intent and Processing Errors
class IntentError(OmniError):
    """Intent processing related errors."""
    pass

class HandlerError(ServiceError):
    """Intent handler related errors."""
    pass

class ProcessorError(OmniError):
    """Edge processor related errors."""
    pass

class EdgeProcessingError(ProcessorError):
    """Edge processing related errors."""
    pass

# Parser Errors
class ParserError(OmniError):
    """Base class for parsing related errors."""
    pass

class TimeParserError(ParserError):
    """Time parsing related errors."""
    pass

class LocationParserError(ParserError):
    """Location parsing related errors."""
    pass

# Cache Errors
class CacheError(OmniError):
    """Cache related errors."""
    pass

# Calendar Errors
class CalendarError(ServiceError):
    """Calendar related errors."""
    pass

# Authentication Errors
class AuthError(OmniError):
    """Authentication related errors."""
    pass

# Speech and Audio Errors
class SpeechError(ServiceError):
    """Speech recognition/synthesis related errors."""
    pass

class TTSError(SpeechError):
    """Text-to-speech related errors."""
    pass

class WakeWordError(SpeechError):
    """Wake word detection errors."""
    pass

# State Errors
class StateError(OmniError):
    """Application state related errors."""
    pass

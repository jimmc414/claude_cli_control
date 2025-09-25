"""
Custom exceptions for the replay system
"""


class ReplayError(Exception):
    """Base exception for all replay-related errors"""
    pass


class TapeMissError(ReplayError):
    """Raised when no tape matches the current request"""
    def __init__(self, message: str, context: dict = None):
        super().__init__(message)
        self.context = context or {}


class SchemaError(ReplayError):
    """Raised when tape format is invalid"""
    def __init__(self, message: str, tape_path: str = None):
        super().__init__(message)
        self.tape_path = tape_path


class RedactionError(ReplayError):
    """Raised when secret redaction fails"""
    pass


class RecordingError(ReplayError):
    """Raised when recording fails"""
    pass


class PlaybackError(ReplayError):
    """Raised when playback fails"""
    pass
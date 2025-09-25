"""
Recording and fallback modes for tape management
Mirrors Talkback's mode semantics for record and fallback behavior
"""

from enum import Enum, auto
from typing import Protocol, Any, Callable


class RecordMode(Enum):
    """Recording mode for tape creation and updates"""
    NEW = auto()       # Record only when no match found, keep existing exchanges
    OVERWRITE = auto() # Replace exchange on match
    DISABLED = auto()  # Never write tapes, use fallback mode on miss


class FallbackMode(Enum):
    """Fallback behavior when no tape matches"""
    NOT_FOUND = auto() # Raise TapeMissError when no tape found
    PROXY = auto()     # Run real program and optionally record


# Type for dynamic mode policies
PolicyCallable = Callable[[Any], Any]


class ModePolicy(Protocol):
    """Protocol for dynamic mode selection"""
    def __call__(self, context: Any) -> RecordMode | FallbackMode:
        """Determine mode based on context"""
        ...


def resolve_record_mode(mode: RecordMode | PolicyCallable, context: Any = None) -> RecordMode:
    """Resolve record mode from static enum or dynamic policy"""
    if callable(mode):
        return mode(context) if context else RecordMode.NEW
    return mode


def resolve_fallback_mode(mode: FallbackMode | PolicyCallable, context: Any = None) -> FallbackMode:
    """Resolve fallback mode from static enum or dynamic policy"""
    if callable(mode):
        return mode(context) if context else FallbackMode.NOT_FOUND
    return mode
"""
Record & Replay functionality for ClaudeControl
Talkback-style tapes for CLI session recording and playback
"""

from .modes import RecordMode, FallbackMode
from .model import Tape, Exchange, Chunk, IOInput, IOOutput, TapeMeta
from .store import TapeStore
from .record import Recorder, ChunkSink
from .play import Transport, ReplayTransport
from .exceptions import TapeMissError, SchemaError, RedactionError
from .summary import print_summary

__all__ = [
    # Modes
    'RecordMode',
    'FallbackMode',
    # Models
    'Tape',
    'Exchange',
    'Chunk',
    'IOInput',
    'IOOutput',
    'TapeMeta',
    # Core classes
    'TapeStore',
    'Recorder',
    'ChunkSink',
    'Transport',
    'ReplayTransport',
    # Exceptions
    'TapeMissError',
    'SchemaError',
    'RedactionError',
    # Utilities
    'print_summary',
]
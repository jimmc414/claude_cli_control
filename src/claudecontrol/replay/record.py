"""
Recording infrastructure using pexpect's logfile_read hook
Captures process I/O as timestamped chunks for replay
"""

import time
import base64
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Any, List, Dict
from datetime import datetime

from .model import Tape, TapeMeta, Exchange, IOInput, IOOutput, Chunk
from .modes import RecordMode
from .namegen import DefaultTapeNameGenerator
from .store import TapeStore
from .redact import SecretRedactor
from .decorators import DecoratorSet
from .matchers import MatchingContext


class ChunkSink:
    """
    Capture output chunks with timestamps.
    Implements write/flush interface for pexpect.logfile_read.
    """

    def __init__(self):
        """Initialize chunk sink"""
        self._last_time = time.monotonic()
        self.chunks: List[Chunk] = []
        self.total_bytes = 0

    def write(self, data: bytes | str) -> None:
        """
        Called by pexpect for each chunk of output.
        pexpect may pass strings if encoding is set, or bytes otherwise.
        """
        # Handle both bytes and string input with error handling
        if isinstance(data, str):
            data_bytes = data.encode('utf-8', errors='replace')
        else:
            data_bytes = data

        if not data_bytes:
            return

        # Calculate delay since last chunk
        now = time.monotonic()
        delay_ms = int((now - self._last_time) * 1000)
        self._last_time = now

        # Check if data is valid UTF-8
        is_utf8 = True
        try:
            data_bytes.decode('utf-8', errors='strict')
        except UnicodeDecodeError:
            is_utf8 = False

        # Create chunk
        chunk = Chunk(
            delay_ms=delay_ms,
            data_b64=base64.b64encode(data_bytes).decode('ascii'),
            is_utf8=is_utf8
        )

        self.chunks.append(chunk)
        self.total_bytes += len(data_bytes)

    def flush(self) -> None:
        """Called by pexpect to flush output (no-op for us)"""
        pass

    def to_output(self) -> IOOutput:
        """Convert captured chunks to IOOutput"""
        return IOOutput(chunks=self.chunks.copy())

    def reset(self) -> None:
        """Reset for new exchange"""
        self.chunks.clear()
        self.total_bytes = 0
        self._last_time = time.monotonic()


@dataclass
class Recorder:
    """
    Records CLI sessions to tapes.
    Integrates with Session via logfile_read hook.
    """
    session: Any  # Forward ref to Session
    tapes_path: Path
    mode: RecordMode
    namegen: Any  # TapeNameGenerator
    store: Optional[TapeStore] = None
    redactor: Optional[SecretRedactor] = None
    decorators: Optional[DecoratorSet] = None

    # Internal state
    _sink: Optional[ChunkSink] = field(default=None, init=False)
    _current_tape: Optional[Tape] = field(default=None, init=False)
    _start_time: float = field(default=0, init=False)
    _current_exchange: Optional[Exchange] = field(default=None, init=False)
    _recording_started: bool = field(default=False, init=False)

    def __post_init__(self):
        """Initialize recorder"""
        if self.store is None:
            self.store = TapeStore(self.tapes_path)
        if self.redactor is None:
            self.redactor = SecretRedactor()
        if self.decorators is None:
            self.decorators = DecoratorSet()

    def start(self) -> None:
        """
        Start recording by attaching to session's pexpect spawn.
        Must be called after session.process is created.
        """
        if self._recording_started:
            return

        # Create and attach chunk sink
        self._sink = ChunkSink()

        # Attach to pexpect's logfile_read
        if hasattr(self.session, 'process') and self.session.process:
            self.session.process.logfile_read = self._sink
            self._recording_started = True

        # Initialize tape
        self._init_tape()

    def start_with_composite(self, composite_logfile) -> None:
        """
        Start recording by adding to an existing composite logfile.
        This allows both recording and output capture to work together.
        """
        if self._recording_started:
            return

        # Create chunk sink
        self._sink = ChunkSink()

        # Add to composite logfile
        if hasattr(composite_logfile, 'add_handler'):
            composite_logfile.add_handler(self._sink)
            self._recording_started = True

        # Initialize tape
        self._init_tape()

    def stop(self) -> None:
        """Stop recording and save tape"""
        if not self._recording_started:
            return

        # Detach from pexpect
        if hasattr(self.session, 'process') and self.session.process:
            self.session.process.logfile_read = None

        # Save current exchange if any
        if self._current_exchange:
            self._finalize_exchange()

        # Save tape if it has exchanges
        if self._current_tape and self._current_tape.exchanges:
            self._save_tape()

        self._recording_started = False

    def on_send(self, data: bytes, kind: str = "raw") -> None:
        """Called when input is sent to process"""
        if not self._recording_started or not self._sink:
            return

        # Finalize previous exchange if any
        if self._current_exchange:
            self._finalize_exchange()

        # Start new exchange
        self._start_exchange(data, kind)

    def on_expect_complete(self, patterns: List[str], matched_index: int, exit_info: Optional[Dict] = None) -> None:
        """Called when expect completes (match or timeout)"""
        if not self._recording_started or not self._current_exchange:
            return

        # Update exchange with exit info if process ended
        if exit_info:
            self._current_exchange.exit = exit_info

        # Finalize exchange
        self._finalize_exchange()

    def _init_tape(self) -> None:
        """Initialize a new tape"""
        meta = TapeMeta(
            created_at=datetime.now().isoformat() + 'Z',
            program=getattr(self.session, 'command', 'unknown'),
            args=getattr(self.session, 'args', []),
            env=dict(getattr(self.session, 'env', None) or {}),
            cwd=str(getattr(self.session, 'cwd', Path.cwd())),
            pty={'rows': 24, 'cols': 80}  # Default, can be overridden
        )

        session_info = {
            'platform': 'claude_control',
            'version': '0.1.0',
            'record_mode': self.mode.name
        }

        self._current_tape = Tape(
            meta=meta,
            session=session_info,
            exchanges=[]
        )

    def _start_exchange(self, data: bytes, kind: str) -> None:
        """Start recording a new exchange"""
        # Reset sink for new exchange
        self._sink.reset()

        # Get current prompt (if available)
        prompt = ""
        if hasattr(self.session, 'process') and hasattr(self.session.process, 'before'):
            before = self.session.process.before
            if before:
                if isinstance(before, bytes):
                    prompt = before.decode('utf-8', errors='ignore')
                else:
                    prompt = str(before)

        # Create input
        input_obj = IOInput(kind=kind)
        try:
            input_obj.data_text = data.decode('utf-8')
        except UnicodeDecodeError:
            input_obj.data_b64 = base64.b64encode(data).decode('ascii')

        # Apply input decorator
        ctx = self._build_context(prompt)
        data = self.decorators.decorate_input(ctx, data)

        # Create exchange
        self._current_exchange = Exchange(
            pre={'prompt': prompt},
            input=input_obj,
            output=IOOutput(),
            exit=None,
            dur_ms=0,
            annotations={}
        )

        self._start_time = time.monotonic()

    def _finalize_exchange(self) -> None:
        """Finalize and add current exchange to tape"""
        if not self._current_exchange or not self._sink:
            return

        # Get output from sink
        self._current_exchange.output = self._sink.to_output()

        # Calculate duration
        if self._start_time:
            duration = time.monotonic() - self._start_time
            self._current_exchange.dur_ms = int(duration * 1000)

        # Add to tape
        if self._current_tape:
            self._current_tape.exchanges.append(self._current_exchange)

        self._current_exchange = None

    def _save_tape(self) -> None:
        """Save current tape to disk"""
        if not self._current_tape:
            return

        # Generate tape path
        tape_path = self.namegen(self.session)

        # Apply tape decorator
        ctx = self._build_context("")
        tape_dict = self._current_tape.to_dict()
        tape_dict = self.decorators.decorate_tape(ctx, tape_dict)

        # Create new Tape from decorated dict
        self._current_tape = Tape.from_dict(tape_dict)

        # Save with redaction
        self.store.save_tape(self._current_tape, tape_path, self.redactor)

    def _build_context(self, prompt: str) -> MatchingContext:
        """Build matching context for decorators"""
        return MatchingContext(
            program=getattr(self.session, 'command', 'unknown'),
            args=getattr(self.session, 'args', []),
            env=dict(getattr(self.session, 'env', None) or {}),
            cwd=str(getattr(self.session, 'cwd', Path.cwd())),
            prompt=prompt,
            exchange_index=len(self._current_tape.exchanges) if self._current_tape else 0
        )
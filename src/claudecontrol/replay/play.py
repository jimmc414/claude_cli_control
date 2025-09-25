"""
Replay transport that replaces pexpect spawn for playback
Provides tape-based I/O instead of real process interaction
"""

import re
import base64
import time
import threading
from typing import Optional, Union, List, Any, Dict
from dataclasses import dataclass, field
import queue
import pexpect

from .store import TapeStore
from .model import Tape, Exchange
from .matchers import MatchingContext, CompositeMatcher
from .modes import FallbackMode
from .exceptions import TapeMissError, PlaybackError
from .latency import LatencyPolicy, apply_latency
from .errors import ErrorInjectionPolicy


class Transport:
    """Abstract base for process transports"""

    def send(self, data: bytes) -> int:
        """Send bytes to process"""
        raise NotImplementedError

    def sendline(self, line: str = "") -> int:
        """Send line to process"""
        raise NotImplementedError

    def expect(self, patterns: Union[str, List[str]], timeout: Optional[int] = None) -> int:
        """Wait for patterns in output"""
        raise NotImplementedError

    def expect_exact(self, patterns: Union[str, List[str]], timeout: Optional[int] = None) -> int:
        """Wait for exact strings in output"""
        raise NotImplementedError

    def isalive(self) -> bool:
        """Check if process is alive"""
        raise NotImplementedError

    def close(self, force: bool = False) -> None:
        """Close the transport"""
        raise NotImplementedError

    # pexpect compatibility attributes
    before: Optional[bytes] = None
    after: Optional[bytes] = None
    match: Optional[re.Match] = None
    buffer: bytes = b""
    exitstatus: Optional[int] = None
    signalstatus: Optional[int] = None


@dataclass
class ReplayTransport(Transport):
    """
    Transport that replays recorded tapes instead of running processes.
    Mimics pexpect.spawn interface for seamless integration.
    """
    store: TapeStore
    matcher: CompositeMatcher
    fallback_mode: FallbackMode = FallbackMode.NOT_FOUND
    latency_policy: Optional[LatencyPolicy] = None
    error_policy: Optional[ErrorInjectionPolicy] = None

    # Session context
    program: str = ""
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    cwd: str = "."
    encoding: Optional[str] = None

    # Replay state
    _current_tape: Optional[Tape] = field(default=None, init=False)
    _current_exchange: Optional[Exchange] = field(default=None, init=False)
    _exchange_index: int = field(default=0, init=False)
    _output_queue: queue.Queue = field(default_factory=queue.Queue, init=False)
    _output_thread: Optional[threading.Thread] = field(default=None, init=False)
    _closed: bool = field(default=False, init=False)
    _buffer: bytearray = field(default_factory=bytearray, init=False)
    _buffer_lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    _live_transport: Optional['LiveTransport'] = field(default=None, init=False)

    # pexpect compatibility
    before: Optional[bytes] = field(default=None, init=False)
    after: Optional[bytes] = field(default=None, init=False)
    match: Optional[re.Match] = field(default=None, init=False)
    exitstatus: Optional[int] = field(default=None, init=False)
    signalstatus: Optional[int] = field(default=None, init=False)

    def __post_init__(self):
        """Initialize replay transport"""
        # Load tapes if not already loaded
        if not self.store.tapes:
            self.store.load_all()

        if not self.latency_policy:
            from .latency import LATENCY_REALISTIC
            self.latency_policy = LATENCY_REALISTIC

        if not self.error_policy:
            from .errors import ERROR_NONE
            self.error_policy = ERROR_NONE

    def send(self, data: bytes) -> int:
        """Send data and trigger replay of matching exchange"""
        if self._closed:
            raise PlaybackError("Transport is closed")

        # Clear previous state with thread safety
        with self._buffer_lock:
            self.before = bytes(self._buffer)
        self.after = None
        self.match = None

        # Find matching exchange
        context = self._build_context()
        exchange = self._find_exchange(data, context)

        if not exchange:
            if self.fallback_mode == FallbackMode.NOT_FOUND:
                raise TapeMissError(f"No tape found for input", {'context': context.to_dict()})
            else:
                # PROXY mode - fall back to real process
                self._switch_to_live_transport()
                return self._live_transport.send(data)

        # Start streaming output chunks
        self._stream_output(exchange)

        return len(data)

    def sendline(self, line: str = "") -> int:
        """Send line with newline"""
        data = (line + "\n").encode('utf-8') if self.encoding else (line + "\n").encode()
        return self.send(data)

    def expect(self, patterns: Union[str, List[str]], timeout: Optional[int] = None) -> int:
        """
        Wait for patterns in buffered output.
        Returns index of matched pattern.
        """
        if isinstance(patterns, str):
            patterns = [patterns]

        # Compile patterns
        compiled_patterns = []
        for p in patterns:
            if isinstance(p, str):
                compiled_patterns.append(re.compile(p.encode() if not self.encoding else p))
            else:
                compiled_patterns.append(p)

        # Wait for pattern match
        start_time = time.time()
        timeout = timeout or 30

        while time.time() - start_time < timeout:
            # Check if we switched to live transport
            if self._live_transport:
                return self._live_transport.expect(patterns, timeout - (time.time() - start_time))

            # Check buffer for matches with thread safety
            with self._buffer_lock:
                buffer_str = self._buffer if not self.encoding else self._buffer.decode('utf-8', errors='ignore')

                for i, pattern in enumerate(compiled_patterns):
                    if hasattr(pattern, 'search'):
                        match = pattern.search(buffer_str)
                        if match:
                            # Set pexpect-compatible attributes
                            self.match = match
                            match_end = match.end()
                            if self.encoding:
                                self.before = buffer_str[:match.start()].encode()
                                self.after = buffer_str[match.start():match_end].encode()
                                # Remove matched portion from buffer
                                self._buffer = bytearray(buffer_str[match_end:].encode())
                            else:
                                self.before = bytes(self._buffer[:match.start()])
                                self.after = bytes(self._buffer[match.start():match_end])
                                # Remove matched portion from buffer
                                self._buffer = self._buffer[match_end:]
                            return i

            # Check if process has ended
            if self.exitstatus is not None:
                raise PlaybackError("Process ended before match")

            # Small sleep to avoid busy waiting
            time.sleep(0.01)

        # Timeout
        with self._buffer_lock:
            self.before = bytes(self._buffer)
        raise TimeoutError(f"Timeout waiting for patterns: {patterns}")

    def expect_exact(self, patterns: Union[str, List[str]], timeout: Optional[int] = None) -> int:
        """Wait for exact strings (no regex)"""
        if isinstance(patterns, str):
            patterns = [patterns]

        # Convert to regex with escaped special chars
        escaped = [re.escape(p) for p in patterns]
        return self.expect(escaped, timeout)

    def isalive(self) -> bool:
        """Check if replay is still active"""
        if self._live_transport:
            return self._live_transport.isalive()
        return not self._closed and self.exitstatus is None

    def close(self, force: bool = False) -> None:
        """Close the replay transport"""
        self._closed = True
        if self._output_thread and self._output_thread.is_alive():
            self._output_thread.join(timeout=1)

    def _build_context(self) -> MatchingContext:
        """Build current matching context"""
        prompt = ""
        if self.before:
            prompt = self.before.decode('utf-8', errors='ignore')

        return MatchingContext(
            program=self.program,
            args=self.args,
            env=self.env,
            cwd=self.cwd,
            prompt=prompt,
            exchange_index=self._exchange_index
        )

    def _find_exchange(self, input_data: bytes, context: MatchingContext) -> Optional[Exchange]:
        """Find matching exchange in loaded tapes"""
        # Try to find exact match first
        input_text = input_data.decode('utf-8', errors='ignore')
        result = self.store.find_exchange(
            self.program,
            self.args,
            context.prompt,
            input_text
        )

        if result:
            tape, exchange, path = result
            self._current_tape = tape
            self._current_exchange = exchange
            return exchange

        # Try matcher-based search
        for tape in self.store.tapes:
            for exchange in tape.exchanges:
                if self.matcher.match_exchange(tape, exchange, context, input_data):
                    self._current_tape = tape
                    self._current_exchange = exchange
                    # Mark tape as used
                    if tape in self.store.tapes:
                        idx = self.store.tapes.index(tape)
                        if idx < len(self.store.paths):
                            self.store.mark_used(self.store.paths[idx])
                    return exchange

        return None

    def _stream_output(self, exchange: Exchange) -> None:
        """Stream output chunks from exchange to buffer"""
        def stream_chunks():
            # Check for error injection
            if self.error_policy and self.error_policy.should_fail(self._build_context()):
                truncate_at = self.error_policy.get_truncation_point(len(exchange.output.chunks))
                chunks_to_play = exchange.output.chunks[:truncate_at]
            else:
                chunks_to_play = exchange.output.chunks

            # Stream chunks with latency
            for chunk in chunks_to_play:
                if self._closed:
                    break

                # Apply latency
                delay = self.latency_policy.get_chunk_delay(chunk.delay_ms, self._build_context())
                if delay > 0:
                    time.sleep(delay / 1000.0)

                # Decode and add to buffer with thread safety
                data = base64.b64decode(chunk.data_b64)
                with self._buffer_lock:
                    self._buffer.extend(data)

            # Set exit status if exchange ended process
            if exchange.exit:
                self.exitstatus = exchange.exit.get('code', 0)
                self.signalstatus = exchange.exit.get('signal')

            # Handle error injection
            if self.error_policy and self.error_policy.should_fail(self._build_context()):
                self.exitstatus = self.error_policy.exit_code
                error_msg = f"\n{self.error_policy.error_message}\n"
                with self._buffer_lock:
                    self._buffer.extend(error_msg.encode())

        # Start streaming in background thread
        self._output_thread = threading.Thread(target=stream_chunks, daemon=True)
        self._output_thread.start()

        # Increment exchange index
        self._exchange_index += 1

    def _switch_to_live_transport(self) -> None:
        """Switch from replay to live transport when tape miss occurs in PROXY mode"""
        if self._live_transport:
            return  # Already switched

        # Create live process
        try:
            # Build command from program and args
            cmd = self.program
            if self.args:
                cmd = f"{self.program} {' '.join(self.args)}"

            spawn_obj = pexpect.spawn(
                cmd,
                cwd=self.cwd,
                env=self.env,
                encoding=self.encoding,
                echo=False
            )
            self._live_transport = LiveTransport(spawn_obj)

            # Copy any buffered data to live transport
            with self._buffer_lock:
                if self._buffer:
                    # Send buffered output to live process if needed
                    pass  # Usually we don't need to send old output

        except Exception as e:
            raise PlaybackError(f"Failed to spawn live process for fallback: {e}")


class LiveTransport(Transport):
    """
    Wrapper around pexpect.spawn for live process execution.
    Provides unified interface with ReplayTransport.
    """

    def __init__(self, spawn_obj):
        """Wrap a pexpect spawn object"""
        self.spawn = spawn_obj
        self.before = None
        self.after = None
        self.match = None
        self.exitstatus = None
        self.signalstatus = None

    def send(self, data: bytes) -> int:
        """Send to real process"""
        # If spawn has encoding, it expects strings
        if hasattr(self.spawn, 'encoding') and self.spawn.encoding:
            # Decode bytes to string for pexpect with encoding
            if isinstance(data, bytes):
                data = data.decode(self.spawn.encoding, errors='replace')
        return self.spawn.send(data)

    def sendline(self, line: str = "") -> int:
        """Send line to real process"""
        return self.spawn.sendline(line)

    def expect(self, patterns: Union[str, List[str]], timeout: Optional[int] = None) -> int:
        """Expect from real process"""
        result = self.spawn.expect(patterns, timeout)
        self.before = self.spawn.before
        self.after = self.spawn.after
        self.match = self.spawn.match
        return result

    def expect_exact(self, patterns: Union[str, List[str]], timeout: Optional[int] = None) -> int:
        """Expect exact from real process"""
        result = self.spawn.expect_exact(patterns, timeout)
        self.before = self.spawn.before
        self.after = self.spawn.after
        self.match = self.spawn.match
        return result

    def isalive(self) -> bool:
        """Check if real process is alive"""
        return self.spawn.isalive()

    def close(self, force: bool = False) -> None:
        """Close real process"""
        self.spawn.close(force)
        self.exitstatus = self.spawn.exitstatus
        self.signalstatus = self.spawn.signalstatus
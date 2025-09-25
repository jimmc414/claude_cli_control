"""
Tape storage and indexing for fast lookup
Handles loading, saving, and matching tapes
"""

from pathlib import Path
import threading
from typing import List, Dict, Tuple, Optional, Set, Any
import pyjson5
import portalocker
import tempfile
import shutil

from .model import Tape, TapeMeta, Exchange
from .normalize import Normalizer
from .exceptions import SchemaError, TapeMissError
from .redact import SecretRedactor


class TapeStore:
    """Thread-safe tape storage with index"""

    def __init__(self, root: str | Path):
        """Initialize tape store with root directory"""
        self.root = Path(root)
        self.tapes: List[Tape] = []
        self.paths: List[Path] = []
        self._lock = threading.RLock()
        self.used: Set[Path] = set()
        self.new: Set[Path] = set()
        self._index: Optional[Dict] = None
        self._normalizer = Normalizer()

    def load_all(self) -> None:
        """Load all tapes from directory recursively"""
        with self._lock:
            self.tapes.clear()
            self.paths.clear()

            if not self.root.exists():
                return

            for tape_path in self.root.rglob("*.json5"):
                try:
                    tape = self.load_tape(tape_path)
                    self.tapes.append(tape)
                    self.paths.append(tape_path)
                except Exception as e:
                    print(f"Warning: Failed to load tape {tape_path}: {e}")

            # Build index after loading
            self._build_index()

    def load_tape(self, path: Path) -> Tape:
        """Load a single tape from file"""
        with open(path, 'r', encoding='utf-8') as f:
            data = pyjson5.load(f)

        try:
            return Tape.from_dict(data)
        except Exception as e:
            raise SchemaError(f"Invalid tape format: {e}", str(path))

    def save_tape(self, tape: Tape, path: Path, redactor: Optional[SecretRedactor] = None) -> Path:
        """Save tape to file with atomic write"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict
        tape_dict = tape.to_dict()

        # Apply redaction if configured
        if redactor:
            for exchange in tape_dict.get('exchanges', []):
                from .redact import redact_exchange
                exchange, _ = redact_exchange(exchange, redactor)

        # Atomic write with temp file
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            dir=path.parent,
            suffix='.tmp',
            delete=False
        ) as tmp:
            # pyjson5 doesn't work with TemporaryFileWrapper, write as string
            json_str = pyjson5.dumps(tape_dict, indent=2, trailing_commas=False)
            tmp.write(json_str)
            tmp_path = Path(tmp.name)

        # Use file locking for the rename
        try:
            shutil.move(str(tmp_path), str(path))
        except Exception as e:
            tmp_path.unlink(missing_ok=True)
            raise

        with self._lock:
            self.new.add(path)

        return path

    def mark_used(self, path: Path) -> None:
        """Mark a tape as used during this session"""
        with self._lock:
            self.used.add(path)

    def _build_index(self) -> None:
        """Build normalized index for fast matching"""
        self._index = {}

        for tape_idx, tape in enumerate(self.tapes):
            for exchange_idx, exchange in enumerate(tape.exchanges):
                # Build normalized key
                key = self._build_exchange_key(tape, exchange)
                self._index[key] = (tape_idx, exchange_idx)

    def _build_exchange_key(self, tape: Tape, exchange: Exchange) -> str:
        """Build normalized key for an exchange"""
        parts = [
            tape.meta.program,
            ' '.join(tape.meta.args),
            exchange.pre.get('prompt', ''),
        ]

        # Add input data
        if exchange.input.data_text:
            parts.append(exchange.input.data_text)

        return self._normalizer.build_key(*parts)

    def find_exchange(self,
                     program: str,
                     args: List[str],
                     prompt: str,
                     input_data: str) -> Optional[Tuple[Tape, Exchange, Path]]:
        """Find matching exchange in loaded tapes"""
        # Build search key
        key = self._normalizer.build_key(
            program,
            ' '.join(args),
            prompt,
            input_data
        )

        # Look up in index
        if self._index and key in self._index:
            tape_idx, exchange_idx = self._index[key]
            tape = self.tapes[tape_idx]
            exchange = tape.exchanges[exchange_idx]
            path = self.paths[tape_idx]

            # Mark as used
            self.mark_used(path)

            return (tape, exchange, path)

        return None

    def get_unused_tapes(self) -> List[Path]:
        """Get list of tapes that were loaded but never used"""
        with self._lock:
            return [p for p in self.paths if p not in self.used]

    def get_new_tapes(self) -> List[Path]:
        """Get list of tapes created in this session"""
        with self._lock:
            return list(self.new)
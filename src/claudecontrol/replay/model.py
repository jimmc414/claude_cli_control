"""
Data models for tape recording and replay
JSON5-compatible structures for human-editable tapes
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import base64


@dataclass
class Chunk:
    """A single output chunk with timing information"""
    delay_ms: int
    data_b64: str
    is_utf8: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON5-compatible dict"""
        return {
            "delay_ms": self.delay_ms,
            "dataB64": self.data_b64,
            "isUtf8": self.is_utf8
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Chunk:
        """Create from JSON5 dict"""
        return cls(
            delay_ms=data.get("delay_ms", 0),
            data_b64=data.get("dataB64", ""),
            is_utf8=data.get("isUtf8", True)
        )


@dataclass
class IOInput:
    """Input data sent to the process"""
    kind: str  # "line" or "raw"
    data_text: Optional[str] = None
    data_b64: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON5-compatible dict"""
        return {
            "type": self.kind,
            "dataText": self.data_text,
            "dataBytesB64": self.data_b64
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> IOInput:
        """Create from JSON5 dict"""
        return cls(
            kind=data.get("type", "line"),
            data_text=data.get("dataText"),
            data_b64=data.get("dataBytesB64")
        )


@dataclass
class IOOutput:
    """Output chunks received from the process"""
    chunks: List[Chunk] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON5-compatible dict"""
        return {
            "chunks": [c.to_dict() for c in self.chunks]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> IOOutput:
        """Create from JSON5 dict"""
        chunks = [Chunk.from_dict(c) for c in data.get("chunks", [])]
        return cls(chunks=chunks)


@dataclass
class Exchange:
    """A single exchange: input -> output sequence"""
    pre: Dict[str, Any]  # prompt signature, optional state hash
    input: IOInput
    output: IOOutput
    exit: Optional[Dict[str, Any]] = None  # exit code and signal
    dur_ms: Optional[int] = None
    annotations: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON5-compatible dict"""
        result = {
            "pre": self.pre,
            "input": self.input.to_dict(),
            "output": self.output.to_dict(),
            "exit": self.exit,
            "dur_ms": self.dur_ms,
        }
        if self.annotations:
            result["annotations"] = self.annotations
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Exchange:
        """Create from JSON5 dict"""
        return cls(
            pre=data.get("pre", {}),
            input=IOInput.from_dict(data.get("input", {})),
            output=IOOutput.from_dict(data.get("output", {})),
            exit=data.get("exit"),
            dur_ms=data.get("dur_ms"),
            annotations=data.get("annotations", {})
        )


@dataclass
class TapeMeta:
    """Metadata about the tape recording"""
    created_at: str
    program: str
    args: List[str]
    env: Dict[str, str]
    cwd: str
    pty: Optional[Dict[str, int]] = None
    tag: Optional[str] = None
    latency: Any = 0
    error_rate: Any = 0
    seed: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON5-compatible dict"""
        result = {
            "createdAt": self.created_at,
            "program": self.program,
            "args": self.args,
            "env": self.env,
            "cwd": self.cwd,
        }
        if self.pty:
            result["pty"] = self.pty
        if self.tag:
            result["tag"] = self.tag
        if self.latency:
            result["latency"] = self.latency
        if self.error_rate:
            result["errorRate"] = self.error_rate
        if self.seed is not None:
            result["seed"] = self.seed
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TapeMeta:
        """Create from JSON5 dict"""
        return cls(
            created_at=data.get("createdAt", datetime.now().isoformat()),
            program=data.get("program", ""),
            args=data.get("args", []),
            env=data.get("env", {}),
            cwd=data.get("cwd", "."),
            pty=data.get("pty"),
            tag=data.get("tag"),
            latency=data.get("latency", 0),
            error_rate=data.get("errorRate", 0),
            seed=data.get("seed")
        )


@dataclass
class Tape:
    """A complete tape with metadata and exchanges"""
    meta: TapeMeta
    session: Dict[str, Any]
    exchanges: List[Exchange]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON5-compatible dict"""
        return {
            "meta": self.meta.to_dict(),
            "session": self.session,
            "exchanges": [e.to_dict() for e in self.exchanges]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Tape:
        """Create from JSON5 dict"""
        return cls(
            meta=TapeMeta.from_dict(data.get("meta", {})),
            session=data.get("session", {}),
            exchanges=[Exchange.from_dict(e) for e in data.get("exchanges", [])]
        )

    def encode_data(self, data: bytes) -> tuple[Optional[str], str]:
        """Encode data as text or base64
        Returns: (text, base64)
        """
        try:
            text = data.decode('utf-8')
            return (text, base64.b64encode(data).decode('ascii'))
        except UnicodeDecodeError:
            return (None, base64.b64encode(data).decode('ascii'))

    def decode_data(self, text: Optional[str], b64: Optional[str]) -> bytes:
        """Decode data from text or base64"""
        if text is not None:
            return text.encode('utf-8')
        elif b64 is not None:
            return base64.b64decode(b64)
        else:
            return b''
"""
Tape naming generator for organizing recorded sessions
Pluggable interface for custom naming strategies
"""

from pathlib import Path
import hashlib
import time
import re
from typing import Any, Protocol, Optional
from dataclasses import dataclass


class TapeNameGenerator(Protocol):
    """Protocol for tape name generation"""
    def __call__(self, context: Any) -> Path:
        """Generate a tape file path based on context"""
        ...


@dataclass
class DefaultTapeNameGenerator:
    """Default tape name generator using program/timestamp/hash pattern"""
    root: Path

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def __call__(self, context: Any) -> Path:
        """Generate tape name: {program}/{verb-or-hash}/unnamed-{timestamp}-{hash}.json5"""
        # Extract program name
        if hasattr(context, 'program'):
            program = Path(context.program).name
        elif hasattr(context, 'command'):
            program = Path(context.command).name
        else:
            program = "unknown"

        # Sanitize program name for filesystem
        program = re.sub(r'[^\w\-_]', '_', program)

        # Generate content hash for uniqueness
        key_parts = []
        if hasattr(context, 'program'):
            key_parts.append(context.program)
        if hasattr(context, 'args') and context.args:
            key_parts.extend(context.args)
        if hasattr(context, 'cwd'):
            key_parts.append(context.cwd)
        if hasattr(context, '_cur_input'):
            key_parts.append(str(context._cur_input))

        key = " ".join(str(p) for p in key_parts)
        content_hash = hashlib.sha1(key.encode()).hexdigest()[:8]

        # Generate timestamp
        timestamp = int(time.time() * 1000)

        # Construct path
        tape_dir = self.root / program
        tape_name = f"unnamed-{timestamp}-{content_hash}.json5"

        return tape_dir / tape_name


@dataclass
class SemanticTapeNameGenerator:
    """Generate semantic names based on command patterns"""
    root: Path

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def __call__(self, context: Any) -> Path:
        """Generate semantic tape names when possible"""
        program = Path(context.program).name if hasattr(context, 'program') else "unknown"
        program = re.sub(r'[^\w\-_]', '_', program)

        # Try to extract verb/action from args
        verb = None
        if hasattr(context, 'args') and context.args:
            # Common patterns: git commit, npm install, etc.
            first_arg = str(context.args[0])
            if re.match(r'^[a-z]+$', first_arg):
                verb = first_arg

        # Build directory structure
        if verb:
            tape_dir = self.root / program / verb
        else:
            tape_dir = self.root / program

        # Generate unique name
        timestamp = int(time.time() * 1000)
        key = f"{program} {context.args if hasattr(context, 'args') else ''}"
        content_hash = hashlib.sha1(key.encode()).hexdigest()[:8]

        if verb:
            tape_name = f"{verb}-{timestamp}-{content_hash}.json5"
        else:
            tape_name = f"session-{timestamp}-{content_hash}.json5"

        return tape_dir / tape_name


@dataclass
class TaggedTapeNameGenerator:
    """Generate names with user-provided tags"""
    root: Path
    tag: Optional[str] = None

    def __init__(self, root: str | Path, tag: Optional[str] = None):
        self.root = Path(root)
        self.tag = tag

    def __call__(self, context: Any) -> Path:
        """Generate tape name with optional tag"""
        program = Path(context.program).name if hasattr(context, 'program') else "unknown"
        program = re.sub(r'[^\w\-_]', '_', program)

        # Use tag from context or instance
        tag = None
        if hasattr(context, 'tag'):
            tag = context.tag
        elif self.tag:
            tag = self.tag

        # Sanitize tag
        if tag:
            tag = re.sub(r'[^\w\-_]', '_', tag)

        # Build path
        tape_dir = self.root / program
        timestamp = int(time.time() * 1000)

        if tag:
            tape_name = f"{tag}-{timestamp}.json5"
        else:
            content_hash = hashlib.sha1(str(context).encode()).hexdigest()[:8]
            tape_name = f"unnamed-{timestamp}-{content_hash}.json5"

        return tape_dir / tape_name
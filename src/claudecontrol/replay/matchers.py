"""
Matchers for tape selection during replay
Supports command, environment, prompt, and stdin matching with configurability
"""

from dataclasses import dataclass
from typing import Callable, List, Dict, Optional, Set, Any, Protocol, Union
from pathlib import Path
import re
import os

from .normalize import normalize_for_matching, strip_ansi


@dataclass
class MatchingContext:
    """Context for matching operations"""
    program: str
    args: List[str]
    env: Dict[str, str]
    cwd: str
    prompt: str
    exchange_index: int = 0
    tape_path: Optional[str] = None
    state_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'program': self.program,
            'args': self.args,
            'env': self.env,
            'cwd': self.cwd,
            'prompt': self.prompt,
            'exchange_index': self.exchange_index,
            'tape_path': self.tape_path,
            'state_hash': self.state_hash,
        }


# Type definitions for matcher functions
StdinMatcher = Callable[[bytes, bytes, MatchingContext], bool]
CommandMatcher = Callable[[List[str], List[str], MatchingContext], bool]
EnvMatcher = Callable[[Dict[str, str], Dict[str, str], MatchingContext], bool]
PromptMatcher = Callable[[str, str, MatchingContext], bool]


class MatcherProtocol(Protocol):
    """Protocol for all matcher types"""
    def match(self, recorded: Any, current: Any, ctx: MatchingContext) -> bool:
        """Check if recorded value matches current value"""
        ...


@dataclass
class DefaultStdinMatcher:
    """Default stdin matcher with normalization"""
    normalize: bool = True
    ignore_trailing_newline: bool = True

    def __call__(self, recorded: bytes, current: bytes, ctx: MatchingContext) -> bool:
        """Match stdin data with optional normalization"""
        if self.ignore_trailing_newline:
            recorded = recorded.rstrip(b'\r\n')
            current = current.rstrip(b'\r\n')

        if self.normalize:
            # Convert to string for normalization
            try:
                recorded_str = recorded.decode('utf-8')
                current_str = current.decode('utf-8')
                recorded_str = normalize_for_matching(recorded_str)
                current_str = normalize_for_matching(current_str)
                return recorded_str == current_str
            except UnicodeDecodeError:
                # Fall back to byte comparison
                pass

        return recorded == current


@dataclass
class DefaultCommandMatcher:
    """Default command matcher with path normalization"""
    normalize_paths: bool = True
    ignore_args: Optional[List[Union[int, str]]] = None

    def __call__(self, recorded: List[str], current: List[str], ctx: MatchingContext) -> bool:
        """Match command and args with normalization"""
        # Match program name
        rec_prog = Path(recorded[0]).name if recorded else ""
        cur_prog = Path(current[0]).name if current else ""

        if rec_prog != cur_prog:
            return False

        # Match args
        rec_args = list(recorded[1:] if len(recorded) > 1 else [])
        cur_args = list(current[1:] if len(current) > 1 else [])

        # Apply ignore_args filter
        if self.ignore_args:
            for ignore in self.ignore_args:
                if isinstance(ignore, int):
                    # Remove by index
                    if 0 <= ignore < len(rec_args):
                        rec_args[ignore] = "<IGNORED>"
                    if 0 <= ignore < len(cur_args):
                        cur_args[ignore] = "<IGNORED>"
                elif isinstance(ignore, str):
                    # Remove by prefix
                    rec_args = [a if not a.startswith(ignore) else "<IGNORED>" for a in rec_args]
                    cur_args = [a if not a.startswith(ignore) else "<IGNORED>" for a in cur_args]

        # Normalize paths if requested
        if self.normalize_paths:
            rec_args = [self._normalize_path(a) for a in rec_args]
            cur_args = [self._normalize_path(a) for a in cur_args]

        return rec_args == cur_args

    def _normalize_path(self, arg: str) -> str:
        """Normalize path arguments"""
        if arg.startswith('/') or arg.startswith('~'):
            # Expand and resolve
            try:
                path = Path(arg).expanduser().resolve()
                return str(path)
            except:
                pass
        return arg


@dataclass
class DefaultEnvMatcher:
    """Default environment matcher with allow/ignore lists"""
    allow_env: Optional[List[str]] = None
    ignore_env: Optional[List[str]] = None

    def __post_init__(self):
        # Default ignore list (like Talkback)
        if self.ignore_env is None:
            self.ignore_env = [
                'PWD', 'OLDPWD', 'SHLVL',
                'RANDOM', '_', 'COLUMNS', 'LINES',
                'PS1', 'PS2', 'PS3', 'PS4',
                'HISTSIZE', 'HISTFILESIZE', 'HISTFILE',
                'SSH_CLIENT', 'SSH_CONNECTION', 'SSH_TTY',
                'DISPLAY', 'WINDOWID',
                'TERM_SESSION_ID', 'TERM_PROGRAM',
            ]

    def __call__(self, recorded: Dict[str, str], current: Dict[str, str], ctx: MatchingContext) -> bool:
        """Match environment variables with filtering"""
        # Build effective key set
        if self.allow_env:
            # Only check allowed vars
            keys = set(self.allow_env)
        else:
            # Check all except ignored
            keys = set(recorded.keys()) | set(current.keys())
            if self.ignore_env:
                keys -= set(self.ignore_env)

        # Compare relevant variables
        for key in keys:
            rec_val = recorded.get(key)
            cur_val = current.get(key)
            if rec_val != cur_val:
                return False

        return True


@dataclass
class DefaultPromptMatcher:
    """Default prompt matcher with ANSI handling"""
    strip_ansi: bool = True
    use_regex: bool = False
    normalize: bool = True

    def __call__(self, recorded: str, current: str, ctx: MatchingContext) -> bool:
        """Match prompt strings"""
        if self.strip_ansi:
            recorded = strip_ansi(recorded)
            current = strip_ansi(current)

        if self.normalize:
            recorded = normalize_for_matching(recorded)
            current = normalize_for_matching(current)

        if self.use_regex:
            try:
                pattern = re.compile(recorded)
                return bool(pattern.search(current))
            except re.error:
                # Fall back to exact match
                pass

        return recorded == current


@dataclass
class StateMatcher:
    """Match based on optional state hash"""

    def __call__(self, recorded_state: Optional[str], current_state: Optional[str]) -> bool:
        """Match state hashes"""
        if recorded_state is None or current_state is None:
            # No state tracking
            return True
        return recorded_state == current_state


class CompositeMatcher:
    """Combine multiple matchers for complete exchange matching"""

    def __init__(self,
                 command_matcher: Optional[CommandMatcher] = None,
                 env_matcher: Optional[EnvMatcher] = None,
                 prompt_matcher: Optional[PromptMatcher] = None,
                 stdin_matcher: Optional[StdinMatcher] = None,
                 state_matcher: Optional[StateMatcher] = None):
        self.command_matcher = command_matcher or DefaultCommandMatcher()
        self.env_matcher = env_matcher or DefaultEnvMatcher()
        self.prompt_matcher = prompt_matcher or DefaultPromptMatcher()
        self.stdin_matcher = stdin_matcher or DefaultStdinMatcher()
        self.state_matcher = state_matcher or StateMatcher()

    def match_exchange(self,
                       recorded_tape: Any,
                       recorded_exchange: Any,
                       current_context: MatchingContext,
                       current_input: bytes) -> bool:
        """Match a complete exchange"""
        # Build recorded context
        rec_ctx = MatchingContext(
            program=recorded_tape.meta.program,
            args=recorded_tape.meta.args,
            env=recorded_tape.meta.env,
            cwd=recorded_tape.meta.cwd,
            prompt=recorded_exchange.pre.get('prompt', ''),
            state_hash=recorded_exchange.pre.get('stateHash')
        )

        # Match command
        rec_cmd = [rec_ctx.program] + rec_ctx.args
        cur_cmd = [current_context.program] + current_context.args
        if not self.command_matcher(rec_cmd, cur_cmd, current_context):
            return False

        # Match environment
        if not self.env_matcher(rec_ctx.env, current_context.env, current_context):
            return False

        # Match prompt
        if not self.prompt_matcher(rec_ctx.prompt, current_context.prompt, current_context):
            return False

        # Match stdin
        rec_input = recorded_exchange.input.data_text.encode('utf-8') if recorded_exchange.input.data_text else b''
        if not self.stdin_matcher(rec_input, current_input, current_context):
            return False

        # Match state if present
        if not self.state_matcher(rec_ctx.state_hash, current_context.state_hash):
            return False

        return True


def create_matcher_set(allow_env: Optional[List[str]] = None,
                      ignore_env: Optional[List[str]] = None,
                      ignore_args: Optional[List[Union[int, str]]] = None,
                      ignore_stdin: bool = False,
                      stdin_matcher: Optional[StdinMatcher] = None,
                      command_matcher: Optional[CommandMatcher] = None) -> CompositeMatcher:
    """Factory for creating configured matcher set"""
    return CompositeMatcher(
        command_matcher=command_matcher or DefaultCommandMatcher(ignore_args=ignore_args),
        env_matcher=DefaultEnvMatcher(allow_env=allow_env, ignore_env=ignore_env),
        prompt_matcher=DefaultPromptMatcher(),
        stdin_matcher=(lambda r, c, ctx: True) if ignore_stdin else (stdin_matcher or DefaultStdinMatcher()),
        state_matcher=StateMatcher()
    )
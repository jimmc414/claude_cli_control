"""
Decorators for transforming input, output, and tapes
Mirrors Talkback's decorator concept for request/response/tape modification
"""

from typing import Callable, Any, Dict, Optional
from dataclasses import dataclass

from .matchers import MatchingContext


# Type definitions for decorator functions
InputDecorator = Callable[[MatchingContext, bytes], bytes]
OutputDecorator = Callable[[MatchingContext, bytes], bytes]
TapeDecorator = Callable[[MatchingContext, Dict[str, Any]], Dict[str, Any]]


@dataclass
class DecoratorSet:
    """Collection of decorators for a session"""
    input_decorator: Optional[InputDecorator] = None
    output_decorator: Optional[OutputDecorator] = None
    tape_decorator: Optional[TapeDecorator] = None

    def decorate_input(self, ctx: MatchingContext, data: bytes) -> bytes:
        """Apply input decorator if present"""
        if self.input_decorator:
            return self.input_decorator(ctx, data)
        return data

    def decorate_output(self, ctx: MatchingContext, data: bytes) -> bytes:
        """Apply output decorator if present"""
        if self.output_decorator:
            return self.output_decorator(ctx, data)
        return data

    def decorate_tape(self, ctx: MatchingContext, tape: Dict[str, Any]) -> Dict[str, Any]:
        """Apply tape decorator if present"""
        if self.tape_decorator:
            return self.tape_decorator(ctx, tape)
        return tape


def chain_decorators(*decorators: Callable) -> Callable:
    """Chain multiple decorators together"""
    def chained(ctx: Any, data: Any) -> Any:
        result = data
        for decorator in decorators:
            if decorator:
                result = decorator(ctx, result)
        return result
    return chained


# Example decorators

def timestamp_decorator(ctx: MatchingContext, tape: Dict[str, Any]) -> Dict[str, Any]:
    """Add timestamp metadata to tape"""
    import time
    tape.setdefault('annotations', {})['decorated_at'] = time.time()
    return tape


def tag_decorator(tag: str) -> TapeDecorator:
    """Factory for adding tags to tapes"""
    def decorator(ctx: MatchingContext, tape: Dict[str, Any]) -> Dict[str, Any]:
        if 'meta' in tape:
            tape['meta']['tag'] = tag
        return tape
    return decorator


def env_filter_decorator(allowed_keys: list) -> TapeDecorator:
    """Factory for filtering environment variables"""
    def decorator(ctx: MatchingContext, tape: Dict[str, Any]) -> Dict[str, Any]:
        if 'meta' in tape and 'env' in tape['meta']:
            filtered_env = {k: v for k, v in tape['meta']['env'].items() if k in allowed_keys}
            tape['meta']['env'] = filtered_env
        return tape
    return decorator


def uppercase_input_decorator(ctx: MatchingContext, data: bytes) -> bytes:
    """Example: Transform input to uppercase"""
    try:
        text = data.decode('utf-8')
        return text.upper().encode('utf-8')
    except:
        return data


def prefix_output_decorator(prefix: str) -> OutputDecorator:
    """Factory for adding prefix to output lines"""
    def decorator(ctx: MatchingContext, data: bytes) -> bytes:
        try:
            text = data.decode('utf-8')
            lines = text.splitlines(keepends=True)
            prefixed = ''.join(f"{prefix}{line}" for line in lines)
            return prefixed.encode('utf-8')
        except:
            return data
    return decorator
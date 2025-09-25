"""
Latency policies for realistic replay timing
Supports constant, range, and function-based latency
"""

import random
import time
from typing import Union, Tuple, Callable, Any, Optional


LatencyConfig = Union[int, Tuple[int, int], Callable[[Any], int]]


def resolve_latency(config: LatencyConfig, context: Any = None) -> int:
    """
    Resolve latency configuration to milliseconds.

    Args:
        config: int (constant ms), tuple (min, max), or callable
        context: Context passed to callable configs

    Returns:
        Latency in milliseconds
    """
    if config is None:
        return 0

    if callable(config):
        return int(config(context) if context else config({}))

    if isinstance(config, (tuple, list)) and len(config) == 2:
        min_ms, max_ms = config
        return random.randint(int(min_ms), int(max_ms))

    return int(config)


def apply_latency(latency_ms: int) -> None:
    """Apply latency by sleeping"""
    if latency_ms > 0:
        time.sleep(latency_ms / 1000.0)


class LatencyPolicy:
    """Configurable latency policy for replay"""

    def __init__(self,
                 global_latency: LatencyConfig = 0,
                 chunk_latency: Optional[LatencyConfig] = None,
                 exchange_latency: Optional[LatencyConfig] = None):
        """
        Initialize latency policy.

        Args:
            global_latency: Default latency for all operations
            chunk_latency: Override for inter-chunk delays
            exchange_latency: Override for inter-exchange delays
        """
        self.global_latency = global_latency
        self.chunk_latency = chunk_latency
        self.exchange_latency = exchange_latency

    def get_chunk_delay(self, recorded_delay: int, context: Any = None) -> int:
        """Get delay for output chunk streaming"""
        if self.chunk_latency is not None:
            return resolve_latency(self.chunk_latency, context)
        elif self.global_latency:
            return resolve_latency(self.global_latency, context)
        else:
            return recorded_delay

    def get_exchange_delay(self, context: Any = None) -> int:
        """Get delay before starting new exchange"""
        if self.exchange_latency is not None:
            return resolve_latency(self.exchange_latency, context)
        else:
            return resolve_latency(self.global_latency, context)


# Preset latency policies
LATENCY_REALISTIC = LatencyPolicy()  # Use recorded timings
LATENCY_FAST = LatencyPolicy(global_latency=1)  # Minimal delays
LATENCY_SLOW = LatencyPolicy(global_latency=(50, 200))  # Simulate slow network
LATENCY_VARIABLE = LatencyPolicy(
    chunk_latency=(10, 100),
    exchange_latency=(100, 500)
)  # Variable delays
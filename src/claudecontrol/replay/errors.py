"""
Error injection policies for testing error handling
Supports probabilistic failures and deterministic patterns
"""

import random
from typing import Union, Callable, Any, Optional


ErrorRateConfig = Union[float, Callable[[Any], float]]


def should_inject_error(rate_config: ErrorRateConfig, context: Any = None, seed: Optional[int] = None) -> bool:
    """
    Determine if an error should be injected.

    Args:
        rate_config: 0-100 probability or callable returning probability
        context: Context passed to callable configs
        seed: Random seed for deterministic behavior

    Returns:
        True if error should be injected
    """
    if rate_config is None:
        return False

    # Resolve rate to float
    if callable(rate_config):
        rate = float(rate_config(context) if context else rate_config({}))
    else:
        rate = float(rate_config)

    if rate <= 0:
        return False
    if rate >= 100:
        return True

    # Use seed for determinism if provided
    if seed is not None:
        rng = random.Random(seed)
        return rng.random() * 100 < rate
    else:
        return random.random() * 100 < rate


class ErrorInjectionPolicy:
    """Configurable error injection for testing"""

    def __init__(self,
                 error_rate: ErrorRateConfig = 0,
                 exit_code: int = 1,
                 error_message: str = "Simulated error",
                 truncate_at: float = 0.5,
                 seed: Optional[int] = None):
        """
        Initialize error injection policy.

        Args:
            error_rate: 0-100 probability of error
            exit_code: Exit code to return on error
            error_message: Error message to display
            truncate_at: Fraction of output to show before error (0-1)
            seed: Random seed for deterministic behavior
        """
        self.error_rate = error_rate
        self.exit_code = exit_code
        self.error_message = error_message
        self.truncate_at = max(0.0, min(1.0, truncate_at))
        self.seed = seed

    def should_fail(self, context: Any = None) -> bool:
        """Check if this exchange should fail"""
        return should_inject_error(self.error_rate, context, self.seed)

    def get_truncation_point(self, total_chunks: int) -> int:
        """Get chunk index at which to inject error"""
        if total_chunks <= 0:
            return 0
        return int(total_chunks * self.truncate_at)


# Preset error policies
ERROR_NONE = ErrorInjectionPolicy(error_rate=0)
ERROR_OCCASIONAL = ErrorInjectionPolicy(error_rate=5, error_message="Random failure")
ERROR_FREQUENT = ErrorInjectionPolicy(error_rate=25, error_message="Frequent failure")
ERROR_HALFWAY = ErrorInjectionPolicy(error_rate=50, truncate_at=0.5)
ERROR_IMMEDIATE = ErrorInjectionPolicy(error_rate=100, truncate_at=0.0)
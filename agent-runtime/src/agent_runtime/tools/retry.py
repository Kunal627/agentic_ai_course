
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RetryPolicy:
    """Configures retries for explicitly selected transient errors."""

    max_attempts: int = 1
    initial_delay_seconds: float = 0.5
    backoff_multiplier: float = 2.0
    retryable_errors: tuple[type[Exception], ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        if self.initial_delay_seconds < 0:
            raise ValueError(
                "initial_delay_seconds cannot be negative"
            )

        if self.backoff_multiplier < 1:
            raise ValueError(
                "backoff_multiplier must be at least 1"
            )

        if not all(
            isinstance(error_type, type)
            and issubclass(error_type, Exception)
            for error_type in self.retryable_errors
        ):
            raise ValueError(
                "retryable_errors must contain exception classes"
            )

    def should_retry(
        self,
        error: Exception,
        attempt_number: int,
    ) -> bool:
        """Decide whether another attempt is permitted."""
        if attempt_number >= self.max_attempts:
            return False

        return isinstance(error, self.retryable_errors)

    def delay_for_retry(self, retry_number: int) -> float:
        """Return the delay before a retry, using exponential backoff."""
        if retry_number < 1:
            raise ValueError("retry_number must be at least 1")

        return (
            self.initial_delay_seconds
            * self.backoff_multiplier ** (retry_number - 1)
        )

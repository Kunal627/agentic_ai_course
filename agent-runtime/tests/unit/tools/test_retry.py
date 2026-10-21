
import pytest

from agent_runtime.tools.retry import RetryPolicy


def test_default_policy_disables_retries():
    policy = RetryPolicy()

    assert policy.max_attempts == 1
    assert policy.should_retry(ConnectionError(), 1) is False


def test_retryable_exception_is_retried_within_attempt_limit():
    policy = RetryPolicy(
        max_attempts=3,
        retryable_errors=(ConnectionError,),
    )

    assert policy.should_retry(ConnectionError(), 1) is True
    assert policy.should_retry(ConnectionError(), 2) is True
    assert policy.should_retry(ConnectionError(), 3) is False


def test_non_retryable_exception_is_not_retried():
    policy = RetryPolicy(
        max_attempts=3,
        retryable_errors=(ConnectionError,),
    )

    assert policy.should_retry(ValueError(), 1) is False


def test_exponential_backoff_delays():
    policy = RetryPolicy(
        max_attempts=4,
        initial_delay_seconds=0.5,
        backoff_multiplier=2.0,
    )

    assert policy.delay_for_retry(1) == pytest.approx(0.5)
    assert policy.delay_for_retry(2) == pytest.approx(1.0)
    assert policy.delay_for_retry(3) == pytest.approx(2.0)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_attempts": 0},
        {"initial_delay_seconds": -0.1},
        {"backoff_multiplier": 0.5},
        {"retryable_errors": ("ConnectionError",)},
    ],
)
def test_invalid_retry_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        RetryPolicy(**kwargs)


def test_retry_number_must_be_positive():
    policy = RetryPolicy()

    with pytest.raises(ValueError, match="retry_number"):
        policy.delay_for_retry(0)



import pytest

from agent_runtime.tools.retry import RetryPolicy


class TransientError(Exception):
    pass


class PermanentError(Exception):
    pass


def test_retry_policy_retries_configured_errors() -> None:
    policy = RetryPolicy(
        max_attempts=3,
        retryable_errors=(TransientError,),
    )

    assert policy.should_retry(TransientError(), 1) is True
    assert policy.should_retry(TransientError(), 2) is True
    assert policy.should_retry(TransientError(), 3) is False


def test_retry_policy_does_not_retry_unconfigured_errors() -> None:
    policy = RetryPolicy(
        max_attempts=3,
        retryable_errors=(TransientError,),
    )

    assert policy.should_retry(PermanentError(), 1) is False


def test_retry_policy_calculates_exponential_backoff() -> None:
    policy = RetryPolicy(
        max_attempts=4,
        initial_delay_seconds=0.5,
        backoff_multiplier=2.0,
    )

    assert policy.delay_for_retry(1) == pytest.approx(0.5)
    assert policy.delay_for_retry(2) == pytest.approx(1.0)
    assert policy.delay_for_retry(3) == pytest.approx(2.0)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_attempts": 0},
        {"initial_delay_seconds": -0.1},
        {"backoff_multiplier": 0.5},
        {"retryable_errors": (ValueError(),)},
    ],
)
def test_retry_policy_rejects_invalid_configuration(kwargs) -> None:
    with pytest.raises(ValueError):
        RetryPolicy(**kwargs)


def test_retry_policy_defaults_to_one_attempt() -> None:
    policy = RetryPolicy()

    assert policy.max_attempts == 1
    assert policy.should_retry(TransientError(), 1) is False

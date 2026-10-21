
from agent_runtime.tools.retry import RetryPolicy


policy = RetryPolicy(
    max_attempts=3,
    initial_delay_seconds=0.5,
    backoff_multiplier=2.0,
    retryable_errors=(ConnectionError,),
)

# A transient error can be retried.
error = ConnectionError("Temporary network failure")

assert policy.should_retry(error, attempt_number=1)
assert policy.should_retry(error, attempt_number=2)

# The maximum number of attempts has been reached.
assert not policy.should_retry(error, attempt_number=3)

# An unrelated error is never retried.
assert not policy.should_retry(
    ValueError("Invalid input"),
    attempt_number=1,
)

# Verify exponential backoff.
assert policy.delay_for_retry(1) == 0.5
assert policy.delay_for_retry(2) == 1.0
assert policy.delay_for_retry(3) == 2.0

# Retries are disabled by default.
default_policy = RetryPolicy()
assert default_policy.max_attempts == 1
assert not default_policy.should_retry(error, attempt_number=1)

print("Retry eligibility tests passed.")
print("Backoff delays:", [
    policy.delay_for_retry(n) for n in range(1, 4)
])
print("Retries disabled by default.")

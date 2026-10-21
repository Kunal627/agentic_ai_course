
import pytest

from agent_runtime.core.cost import CostEstimator, TokenPricing


def test_estimates_input_and_output_cost() -> None:
    estimator = CostEstimator(
        TokenPricing(
            input_usd_per_million=2.0,
            output_usd_per_million=8.0,
        )
    )

    cost = estimator.estimate(
        input_tokens=500_000,
        output_tokens=100_000,
    )

    assert cost == pytest.approx(1.8)


def test_local_model_can_have_zero_cost() -> None:
    estimator = CostEstimator(TokenPricing())

    assert estimator.estimate(
        input_tokens=10_000,
        output_tokens=2_000,
    ) == 0.0


@pytest.mark.parametrize(
    ("input_price", "output_price"),
    [(-1.0, 0.0), (0.0, -1.0)],
)
def test_rejects_negative_pricing(
    input_price: float,
    output_price: float,
) -> None:
    with pytest.raises(ValueError):
        TokenPricing(
            input_usd_per_million=input_price,
            output_usd_per_million=output_price,
        )


def test_rejects_negative_token_counts() -> None:
    estimator = CostEstimator(TokenPricing())

    with pytest.raises(ValueError):
        estimator.estimate(input_tokens=-1, output_tokens=0)


from dataclasses import dataclass


@dataclass(frozen=True)
class TokenPricing:
    """Model token prices in USD per one million tokens."""

    input_usd_per_million: float = 0.0
    output_usd_per_million: float = 0.0

    def __post_init__(self) -> None:
        if self.input_usd_per_million < 0:
            raise ValueError("Input token price cannot be negative.")
        if self.output_usd_per_million < 0:
            raise ValueError("Output token price cannot be negative.")


class CostEstimator:
    """Estimates model cost from token usage and configured pricing."""

    def __init__(self, pricing: TokenPricing) -> None:
        self.pricing = pricing

    def estimate(
        self,
        *,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("Token counts cannot be negative.")

        input_cost = (
            input_tokens
            * self.pricing.input_usd_per_million
            / 1_000_000
        )
        output_cost = (
            output_tokens
            * self.pricing.output_usd_per_million
            / 1_000_000
        )

        return input_cost + output_cost

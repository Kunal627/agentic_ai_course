
from pathlib import Path
from typing import Any


from agent_runtime.model_adapters.base import ModelAdapter
from agent_runtime.model_adapters.model_factory import create_model_adapter

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "default.yaml"


def load_config(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    """Load application configuration from a YAML file."""

    path = Path(config_path)

    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    if not isinstance(config, dict):
        raise ValueError(
            f"Configuration must be a YAML mapping: {path}"
        )

    return config



def create_configured_model(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> tuple[dict[str, Any], ModelAdapter]:
    """Load configuration and create the configured model adapter."""

    config = load_config(config_path)

    model_config = config.get("model")
    if not isinstance(model_config, dict):
        raise ValueError(
            "Configuration must contain a 'model' mapping."
        )

    adapter = create_model_adapter(model_config)

    return config, adapter

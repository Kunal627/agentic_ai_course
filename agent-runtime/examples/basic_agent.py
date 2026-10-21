
import asyncio

from agent_runtime.main import create_configured_model
from agent_runtime.models.messages import Message


async def main() -> None:
    config, adapter = create_configured_model()

    model_config = config["model"]

    messages = [
        Message(
            role="user",
            content="Explain what an AI agent is in one sentence.",
        )
    ]

    try:
        response = await adapter.generate(
            messages,
            model=model_config["name"],
            temperature=model_config.get("temperature", 0.0),
        )

        print("\nModel response")
        print("--------------")
        print(response.content or "(No final answer returned)")

        print("\nUsage")
        print("-----")
        print(f"Input tokens:  {response.input_tokens}")
        print(f"Output tokens: {response.output_tokens}")
        print(f"Finish reason: {response.finish_reason}")

    finally:
        await adapter.close()


if __name__ == "__main__":
    asyncio.run(main())


import asyncio

from agent_runtime.main import create_configured_model
from agent_runtime.core.agent import Agent


async def main() -> None:
    config, adapter = create_configured_model()
    model_config = config["model"]

    agent = Agent(
        adapter,
        model=model_config["name"],
        temperature=model_config.get("temperature", 0.0),
        max_steps=5,
    )

    try:
        state = await agent.run(
            "Explain what an AI agent is in one sentence."
        )

        print("\nAgent run")
        print("---------")
        print(f"Run ID:        {state.run_id}")
        print(f"Status:        {state.status}")
        print(f"Steps:         {state.step_count}")
        print(f"Final answer:  {state.final_answer}")
        print(f"Input tokens:  {state.input_tokens}")
        print(f"Output tokens: {state.output_tokens}")
        print(f"Error:         {state.error}")

    finally:
        await adapter.close()


if __name__ == "__main__":
    asyncio.run(main())

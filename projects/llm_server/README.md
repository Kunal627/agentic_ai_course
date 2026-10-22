# Local LLM Server

This project provides a **local, OpenAI-compatible LLM endpoint** for the
`agentic_ai_course` workspace. It is intended to give agents and runtime
components a dependable model server for development, demos, and integration
testing without requiring a hosted cloud model API.

## What this project intends to do

- Serve a local language model through an OpenAI-style API interface.
- Let agent projects connect with a standard `base_url` pattern
	(`/v1/chat/completions`, etc.) so model backends can be swapped more easily.
- Enable repeatable local testing with a fixed model artifact in
	`models/Qwen3-8B-Q4_K_M.gguf`.
- Support offline/controlled-environment experimentation for agent behavior,
	tool-calling flows, and prompt iteration.

## Typical usage in this workspace

The `agent-runtime` project can point its model adapter to this local server
instead of a hosted provider. This helps when you want:

- lower-cost iteration,
- predictable latency in local development,
- and easier debugging of request/response behavior.

## Start

From this folder:

```powershell
docker compose up -d
```

## Stop

```powershell
docker compose down
```

## Endpoint

- Base URL: `http://localhost:8080`

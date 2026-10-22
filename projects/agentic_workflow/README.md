# Agentic Workflow POC

This folder contains a small **Temporal + Python** proof of concept for deterministic, auditable AI-assisted workflow execution.

## Goal of this POC

The goal is to demonstrate a safe workflow pattern where:

1. A protocol payload is validated with strict schema checks.
2. AI review output is treated as untrusted and validated again.
3. Deterministic policy rules decide whether human approval is required.
4. A human can approve or reject through a workflow signal.
5. The workflow returns a final, structured decision payload.

This is intentionally simple and local-first so it is easy to extend.

## What is implemented

- `ProtocolValidationWorkflow` in `src/workflow_poc/workflows.py`
	- Runs validation activity
	- Runs local LLM review activity
	- Applies policy decision logic
	- Waits for human signal when required
- `HelloWorkflow` in `src/workflow_poc/workflows.py` for basic Temporal connectivity check
- Activities in `src/workflow_poc/activities.py`
	- `validate_protocol`
	- `review_protocol` (calls local OpenAI-compatible LLM endpoint and validates strict JSON output)
- Pydantic models in `src/workflow_poc/models.py`
- Decision rules in `src/workflow_poc/policies.py`
- Transition rules in `src/workflow_poc/state_machine.py`

## Prerequisites

- Python `3.12+`
- A running Temporal server reachable at `localhost:7233`
- A running local OpenAI-compatible LLM endpoint reachable at `http://localhost:8080/v1`

> Note: the local `docker-compose.yml` in this folder is currently a placeholder and does not start Temporal services.

## Setup

From `projects/agentic_workflow`:

```powershell
# Optional: create venv if needed
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -e .
```

If you prefer direct install without editable mode:

```powershell
pip install "pydantic>=2,<3" "temporalio>=1,<2" "openai>=1,<2" pytest pytest-asyncio
```

## Local LLM integration in `review_protocol`

The review activity in `src/workflow_poc/activities.py` uses `AsyncOpenAI` with a local base URL, sends protocol data in a structured prompt, requests JSON mode, and validates the response against `AIReviewResult`.

### Runtime config

Set these environment variables before starting the worker:

```powershell
$env:LLM_BASE_URL = "http://localhost:8080/v1"
$env:LLM_MODEL = "Qwen3-8B-Q4_K_M.gguf"
$env:LLM_API_KEY = "not-needed"
```

Defaults in code are already:

- `LLM_BASE_URL=http://localhost:8080/v1`
- `LLM_MODEL=Qwen3-8B-Q4_K_M.gguf`
- `LLM_API_KEY=not-needed`

### Start local LLM server

From `projects/llm_server`:

```powershell
docker compose up -d
```

Stop when done:

```powershell
docker compose down
```

## How to execute

Open a terminal in `projects/agentic_workflow`.

### 1) Start worker

```powershell
python -m src.workflow_poc.worker
```

Expected output includes: `Worker started. Waiting for workflows...`

> Make sure Temporal and the local LLM server are both up before starting the worker.

### 2) Quick smoke test workflow

In a second terminal:

```powershell
python -m src.workflow_poc.client
```

This executes `HelloWorkflow` and prints a completion message.

### 3) Run protocol review workflow

In another terminal:

```powershell
python -m src.workflow_poc.protocol_client
```

This starts a workflow and prints a workflow ID like `protocol-review-...`.

### 4) Submit human approval/rejection signal

Use the workflow ID from step 3:

```powershell
python -m src.workflow_poc.approval_client
```

You will be prompted for:
- workflow ID
- approve/reject (`yes`/`no`)
- reviewer identifier
- comment

The command then waits and prints the final workflow result.

## Running tests

From `projects/agentic_workflow`:

```powershell
pytest -q
```

Or specific tests:

```powershell
pytest -q tests/test_policies.py
pytest -q tests/test_state_machine.py
```

## Troubleshooting

- `ModuleNotFoundError` during tests:
	- Run tests from `projects/agentic_workflow`
	- Keep imports package-relative inside `src/workflow_poc` modules
- Cannot connect to Temporal:
	- Ensure Temporal server is running and reachable at `localhost:7233`
- Cannot connect to local LLM:
	- Ensure `projects/llm_server` is running (`docker compose up -d`)
	- Verify `LLM_BASE_URL` points to `http://localhost:8080/v1`
- LLM output validation failure in `review_protocol`:
	- The activity enforces strict JSON schema via `AIReviewResult`
	- Re-run; malformed model output is treated as activity failure and can be retried
- Workflow waits forever for approval:
	- This is expected when policy requires review until `submit_approval` signal is sent

## Next recommended improvements

- Add temporal service definitions to `docker-compose.yml`
- Add integration tests for end-to-end workflow + signal flow
- Add config/env handling for host, task queue, and thresholds
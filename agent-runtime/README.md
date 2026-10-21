# agent-runtime

Modular, extensible Python agent runtime.

## Prerequisites

- Python 3.12+
- `pip`

## Build agent-runtime

From this folder (`agent-runtime/`):

1. Create and activate a virtual environment

	**PowerShell (Windows):**

	```powershell
	py -3.12 -m venv .venv
	.\.venv\Scripts\Activate.ps1
	```

2. Install project dependencies (including dev tools)

	```powershell
	python -m pip install --upgrade pip build
	pip install -e ".[dev]"
	```

3. Run tests

	```powershell
	pytest
	```

4. Build distributables

	```powershell
	python -m build
	```

5. Find artifacts in:

- `dist/*.whl`
- `dist/*.tar.gz`

## Install for runtime use only

If you do not need dev dependencies:

```powershell
pip install -e .
```

## Common issues

### `No module named build`

Install `build` in the same interpreter used to run the command:

```powershell
python -m pip install build
python -m build
```

If needed, run with explicit interpreter path:

```powershell
.\.venv\Scripts\python.exe -m pip install build
.\.venv\Scripts\python.exe -m build
```

### `ModuleNotFoundError: No module named 'openai'`

`openai` is included in core dependencies. Reinstall package metadata in your active environment:

```powershell
pip install -e .
```

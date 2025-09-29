# LLM Performance Test

A lightweight tool to benchmark latency and token throughput for OpenAI/Azure-compatible LLM chat completions. It collects per-request metrics, aggregates statistics, and can export Markdown summaries.

## Features

- Sequential and concurrent request modes
- Streaming and non-streaming response support
- Per-request metrics: total/prompt/completion/reasoning tokens, total time, tokens/sec, time-to-first-token
- Aggregated stats (mean/median/min/max/std) across runs
- Markdown report output
- Environment-based configuration via `.env` (with optional CLI overrides)
- Flexible dataset loaders for CSV or JSON prompt files

## Requirements

- Python 3.10+
- Packages (install via `pip`):
  - `pydantic`, `pydantic-settings`
  - `aiohttp`

If you keep a requirements file, install it like:

```bash
python3 -m pip install -r llm_perf_test/requirements.txt
```

## Quick start

1) Create a `.env` at the repository root with your settings (see example below).
2) Place your prompt files under the folder referenced by `LLM_TEST_DATASET_DIR`.
3) Run as a module:

```bash
python -m llm_perf_test
```

Or launch from VS Code using a launch configuration that sets `cwd` to the workspace root (see Troubleshooting).

## Configuration (.env)

This project uses Pydantic Settings to load configuration from a `.env` file in the current working directory. Example:

```env
# API connection
LLM_URL=https://your-endpoint.example.com/v1
LLM_API_KEY=sk-your-api-key
LLM_MODEL=your-model-name
LLM_API_VERSION=

# Behavior flags
LLM_VERIFY_SSL=false
LLM_USE_STREAMING=false
LLM_USE_COMMON_PROMPT=false

# Concurrency & timing (seconds)
LLM_CONCURRENT=0
LLM_REQUEST_DELAY_SECONDS=0
LLM_REQUEST_TIMEOUT=600

# Output paths (optional)
# If not provided, results go under CWD/<timestamp>, and analysis Markdown under CWD/analysis
LLM_RESULT_DIR=
LLM_OUTPUT_MARKDOWN_PATH=

# Dataset folder containing your .csv or .json prompt files
LLM_TEST_DATASET_DIR=./llm_perf_test/datasets
```

Notes:
- Booleans are case-insensitive: `true/false`, `1/0`, `yes/no`.
- If `LLM_RESULT_DIR` and `LLM_OUTPUT_MARKDOWN_PATH` are not set, the app creates a timestamped results folder under the current working directory and writes Markdown under `analysis/` in the current working directory.

## Datasets

Set `LLM_TEST_DATASET_DIR` to the folder containing your prompt files.

- CSV loader (`LoadPromptsFromCsv`)
  - Reads all `*.csv` files in the folder
  - Uses the 3rd column (index 2) as the prompt text
  - Skips the first row as a header by default

- JSON loader (`LoadPromptsFromRawPrompts`)
  - Reads all `*.json` files in the folder
  - Expects an OpenAI-style request structure and extracts the first message content:

    ```json
    {
      "messages": [
        { "role": "user", "content": "Your prompt text here" }
      ]
    }
    ```

You can switch between loaders using `LLM_USE_COMMON_PROMPT`:
- `false` → JSON loader
- `true` → CSV loader

## Outputs

- Per-request raw content is saved (when available) under the results directory.
- A Markdown report with per-request and aggregated metrics is written under `analysis/` in the current working directory (or to `LLM_OUTPUT_MARKDOWN_PATH` if provided).

## Running concurrent tests

Set `LLM_CONCURRENT` to a non-zero value to enable a concurrent test run in addition to sequential runs. You can also set `LLM_REQUEST_TIMEOUT` and `LLM_REQUEST_DELAY_SECONDS` (for pacing sequential runs).

## Troubleshooting

- “No module named `llm_perf_test`”
  - Run as a module: `python -m llm_perf_test`
  - Ensure your working directory is the repository root
  - In VS Code launch.json, set `"cwd": "${workspaceFolder}"` (and optionally `"module": "llm_perf_test"`)

- `.env` seems ignored
  - Ensure `.env` lives at the current working directory when you run
  - In VS Code, set `"cwd": "${workspaceFolder}"` and optionally `"envFile": "${workspaceFolder}/.env"`

- Empty prompts
  - Confirm files exist under `LLM_TEST_DATASET_DIR`
  - For CSV, ensure your prompt text is in the 3rd column (index 2)
  - For JSON, ensure `messages[0].content` exists

## Security notes

- Never commit real API keys. `.gitignore` excludes `.env` by default; share a sanitized `.env.example` instead.

## License

This repository is intended for internal benchmarking. Add a license here if you plan to distribute.
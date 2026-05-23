# Webex Bot MCP — Developer Guide

## Project Overview

A Model Context Protocol (MCP) server that bridges AI assistants with the Webex Teams API.
It exposes tools for managing rooms, messages, and memberships, plus resources (contextual
guides) and prompt templates for common workflows.

## Repository Layout

```
src/webex_bot_mcp/
  main.py            — MCP server entry point; registers all tools/resources/prompts
  config.py          — WebexConfig dataclass; loaded via get_config() or WebexConfig.from_env()
  health_check.py    — Standalone diagnostic script; validates env and API connectivity
  tools/
    __init__.py      — Re-exports every tool function
    common.py        — Shared: WebexAPI client, create_error_response, create_success_response,
                       WebexErrorCodes, version constants
    rooms.py         — Room/space CRUD (list, create, update, get, delete) + space aliases
    messages.py      — Message send/list/delete + mention helpers + space aliases +
                       Adaptive Card send/build tools
    memberships.py   — Membership CRUD (list, add, update, delete) + space aliases
    people.py        — get_webex_me, list_webex_people

pyproject.toml       — Project metadata and dependencies (uses uv, src layout)
Dockerfile           — Multi-stage build; non-root user, health checks
docker-compose.yml   — Compose stack with optional Prometheus + Grafana

tests/
  test_messages.py   — Unit tests (85 cases); mocks webexpythonsdk at sys.modules level
```

## Key Conventions

### Tool count
27 tools total: 5 room + 5 space-room aliases + 4 message + 2 space-message aliases +
2 adaptive-card + 1 adaptive-card-space alias + 1 adaptive-card-builder +
4 membership + 2 space-membership aliases + 2 people.
Update `tools_count` in the `server_version` resource (`src/webex_bot_mcp/main.py`) when adding tools.

### Error handling — always use structured responses
Every tool must return via `create_error_response` or `create_success_response` from
`tools/common.py`. Never return a bare `{'success': False, 'error': str(e)}` dict.
Map exceptions with a local `_map_exception_to_error(e)` helper (see any tool module for
the pattern).

Error code ranges:
- `E001–E003` — client/argument errors (do not retry)
- `E401–E404` — auth/access errors (do not retry)
- `E500–E504` — server errors (retry with backoff)
- `E600–E602` — Webex-specific errors

### Response shape
```python
# Error
{'success': False, 'error_code': 'E001', 'message': '...', 'timestamp': '<ISO>', 'server_version': '...'}

# Success
{'success': True, 'data': {...}, 'timestamp': '<ISO>', 'server_version': '...', 'metadata': {...}}
```

### Space aliases
Every room/message/membership tool has a "space" alias that delegates to the room variant
and renames keys in the response (`room` → `space`, `rooms` → `spaces`, etc.).
Aliases live in the same module file as the canonical tool.

### `files` parameter
Always wrap a string URL in a list before sending to the SDK:
```python
params['files'] = [files] if isinstance(files, str) else files
```

## Running the Server

```bash
# stdio (default — for Claude Desktop / MCP clients)
uv run webex-bot-mcp

# HTTP transport
uv run webex-bot-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

Required environment variable: `WEBEX_ACCESS_TOKEN`

## Running Tests

```bash
uv run python -m unittest discover -s tests -v
```

Tests mock `webexpythonsdk` via `sys.modules` so no real credentials are needed.
Must run via `uv run` so the `src/webex_bot_mcp` package is on the Python path.

## Adding a New Tool

1. Implement the function in the appropriate `src/webex_bot_mcp/tools/*.py` module.
2. Use `create_error_response` / `create_success_response` for all returns.
3. Add a `_map_exception_to_error` call in the `except` block.
4. Export from `src/webex_bot_mcp/tools/__init__.py`.
5. Register with `mcp.tool()(your_function)` in `src/webex_bot_mcp/main.py`.
6. Update `tools_count` in the `server_version` resource in `src/webex_bot_mcp/main.py`.
7. Add unit tests in `tests/test_messages.py` (or a new test file).

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `WEBEX_ACCESS_TOKEN` | ✅ | — | Bot token from developer.webex.com |
| `WEBEX_DEBUG` | | `false` | Enable debug logging |
| `WEBEX_RATE_LIMIT_MESSAGES_PER_SECOND` | | `10` | Message rate limit |
| `WEBEX_RATE_LIMIT_API_CALLS_PER_MINUTE` | | `300` | API rate limit |
| `WEBEX_TIMEOUT_SECONDS` | | `30` | HTTP timeout |
| `LOG_LEVEL` | | `INFO` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` |
| `LOG_FORMAT` | | `text` | `text` or `json` |
| `METRICS_ENABLED` | | `false` | Enable metrics endpoint |
| `METRICS_ENDPOINT` | | — | Prometheus push endpoint |

## Dependency Management

Uses `uv`. The declared runtime dependency for dotenv is `python-dotenv>=1.0.0`
(not the unrelated `dotenv` PyPI package). After changing `pyproject.toml` run:
```bash
uv lock && uv sync
```

# Webex Bot MCP — Developer Guide

## Project Overview

A Model Context Protocol (MCP) server that bridges AI assistants with the Webex Teams API.
It exposes tools for managing rooms, messages, and memberships, plus resources (contextual
guides) and prompt templates for common workflows.

## Repository Layout

```
pyproject.toml       — Project metadata, version (single source of truth), and dependencies (uv)
Dockerfile           — Multi-stage build; non-root user, health checks
docker-compose.yml   — Compose stack with optional Prometheus + Grafana

src/webex_bot_mcp/
  __init__.py        — Package init; reads __version__ from importlib.metadata
  __main__.py        — Enables `python -m webex_bot_mcp`
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
    teams.py         — Team tools (list, get, update, delete) + team membership tools
                       Note: create_webex_team is intentionally absent — bots cannot
                       create teams (Webex returns 401); only user/integration tokens can.

tests/
  test_messages.py   — Unit tests (85 cases); mocks webexpythonsdk at sys.modules level
  test_teams.py      — Unit tests (40 cases); same mock pattern

.github/
  workflows/
    publish.yml           — Builds + publishes to TestPyPI then PyPI on tag/workflow_dispatch
    release-please.yml    — Creates release PRs and tags from conventional commits
  release-please-config.json    — release-please package config
  .release-please-manifest.json — Tracks current released version
```

## Key Conventions

### Tool count
34 tools total: 5 room + 5 space-room aliases + 4 message + 2 space-message aliases +
2 adaptive-card + 1 adaptive-card-space alias + 1 adaptive-card-builder +
4 membership + 2 space-membership aliases + 2 people +
4 team + 3 team-membership.
Update `tools_count` in the `server_version` resource (`src/webex_bot_mcp/main.py`) when adding tools.

Note: `create_webex_team` is intentionally not implemented. Bots cannot create teams —
the Webex platform returns 401 for `POST /teams` with bot tokens regardless of scopes.
Only user tokens or OAuth integrations with `spark:teams_write` can create teams.

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
# If installed from PyPI (pip install webex-bot-mcp)
webex-bot-mcp                                          # stdio (default)
webex-bot-mcp --transport streamable-http --port 8000  # HTTP transport

# From source checkout (development)
uv run webex-bot-mcp
uv run python -m webex_bot_mcp --transport streamable-http --host 0.0.0.0 --port 8000

# Health check
webex-bot-mcp-health
```

Required environment variable: `WEBEX_ACCESS_TOKEN`

## Running Tests

```bash
python -m unittest discover -s tests -v
# or, from a source checkout with uv:
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

## Releases & Conventional Commits

Releases are fully automated via **release-please** + **GitHub Actions**. No manual version
bumping or tagging is needed for normal releases.

### How it works

1. Merge commits to `main` using the **conventional commit** format (see below).
2. release-please watches `main` and maintains a "Release PR" that accumulates unreleased
   changes, updating `CHANGELOG.md` and `pyproject.toml` version automatically.
3. When you're ready to release, **merge the Release PR** — release-please creates a GitHub
   tag + release automatically.
4. The `publish.yml` workflow fires on the new tag, builds the wheel, publishes to TestPyPI
   (requires approval from the `testpypi` environment), then publishes to PyPI (requires
   approval from the `pypi` environment).

You can also trigger a publish manually from the GitHub Actions tab via `workflow_dispatch`
(useful if you need to republish without a new tag).

### Conventional commit format

```
<type>(<scope>): <short description>

[optional body]

[optional footer(s)]
```

| Type | Version bump | Use for |
|---|---|---|
| `feat:` | minor | New tool, resource, or user-visible feature |
| `fix:` | patch | Bug fix |
| `feat!:` or `BREAKING CHANGE:` footer | major | Breaking API change |
| `chore:` | none | Build, CI, dependency updates |
| `docs:` | none | Documentation only |
| `refactor:` | none | Code restructure, no behavior change |
| `test:` | none | Test additions or fixes |
| `perf:` | patch | Performance improvement |

**Examples:**
```
feat(messages): add markdown formatting support
fix(rooms): handle 404 when room already deleted
chore(deps): update fastmcp to 2.5.0
docs: add conventional commits guide to CLAUDE.md
feat!: rename list_webex_rooms to list_rooms

BREAKING CHANGE: tool name changed for consistency
```

### Version source of truth

Version lives **only** in `pyproject.toml`. Code reads it at runtime via
`importlib.metadata.version("webex-bot-mcp")`. Never hard-code a version string anywhere
else in the source.

## Dependency Management

Uses `uv`. The declared runtime dependency for dotenv is `python-dotenv>=1.0.0`
(not the unrelated `dotenv` PyPI package). After changing `pyproject.toml` run:
```bash
uv lock && uv sync
```

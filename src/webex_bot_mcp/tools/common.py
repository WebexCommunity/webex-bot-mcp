"""
Common utilities and shared components for Webex Bot MCP tools.
"""
import functools
import json as _json
import logging
import os
import time
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Callable, Dict
from importlib.metadata import version, PackageNotFoundError
from webexpythonsdk import WebexAPI

# Server version information — single source of truth is pyproject.toml
try:
    MCP_SERVER_VERSION = version("webex-bot-mcp")
except PackageNotFoundError:
    MCP_SERVER_VERSION = "unknown"
MCP_SPEC_VERSION = "2024-11-05"

# ---------------------------------------------------------------------------
# Structured logging
# ---------------------------------------------------------------------------

logger = logging.getLogger("webex_bot_mcp")

# kwargs that carry entity IDs worth surfacing in every log line
_TOOL_ID_PARAMS = frozenset({
    "room_id", "space_id", "team_id", "person_id",
    "person_email", "membership_id", "message_id", "webhook_id",
})

# LogRecord fields that belong to the logging framework, not our payload
_LOG_RECORD_BUILTINS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__)


class _JsonFormatter(logging.Formatter):
    """Emit each log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _LOG_RECORD_BUILTINS and key not in ("message", "asctime"):
                data[key] = value
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        return _json.dumps(data)


def setup_logging(log_level: str = "INFO", log_format: str = "text", debug: bool = False) -> None:
    """Configure the webex_bot_mcp logger.

    When debug is True (WEBEX_DEBUG=true) the level is forced to DEBUG so that
    tool request/response traces are emitted.  Otherwise log_level is used.
    Calling this a second time is a no-op (handlers already attached).
    """
    log = logging.getLogger("webex_bot_mcp")

    if log.handlers:
        return  # already configured

    effective_level = logging.DEBUG if debug else getattr(logging, log_level.upper(), logging.INFO)
    log.setLevel(effective_level)
    log.propagate = False

    handler = logging.StreamHandler()
    if log_format == "json":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        ))
    log.addHandler(handler)


def _kv(event: str, fields: Dict[str, Any]) -> str:
    """Render event + fields as 'event key=value …' for human-readable logs."""
    parts = [event]
    for k, v in fields.items():
        parts.append(f"{k}={v!r}" if isinstance(v, str) else f"{k}={v}")
    return " ".join(parts)


def log_tool_call(func: Callable) -> Callable:
    """Decorator that emits structured request/response log lines for a tool.

    Fields logged on every call: tool, any entity ID kwargs present (room_id,
    space_id, …), latency_ms, status, and error_code on failure.

    Request/success lines are emitted at DEBUG (visible only when
    WEBEX_DEBUG=true).  Error lines are emitted at WARNING so they surface in
    production logs regardless of debug mode.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        tool_name = func.__name__
        start = time.monotonic()

        ctx: Dict[str, Any] = {"tool": tool_name}
        for param in _TOOL_ID_PARAMS:
            val = kwargs.get(param)
            if val:
                ctx[param] = val

        logger.debug(_kv("tool_request", ctx), extra=ctx)

        result = func(*args, **kwargs)

        ctx["latency_ms"] = round((time.monotonic() - start) * 1000, 2)

        if isinstance(result, dict) and not result.get("success"):
            ctx["status"] = "error"
            ctx["error_code"] = result.get("error_code", "unknown")
            ctx["error_message"] = result.get("message", "")
            logger.warning(_kv("tool_response", ctx), extra=ctx)
        else:
            ctx["status"] = "success"
            logger.debug(_kv("tool_response", ctx), extra=ctx)

        return result

    return wrapper

# Error codes for structured error handling
class WebexErrorCodes:
    """Standard error codes for Webex MCP operations."""
    
    # Client errors (4xx)
    INVALID_ARGUMENTS = "E001"
    MISSING_REQUIRED_FIELD = "E002"
    INVALID_FIELD_VALUE = "E003"
    UNAUTHORIZED = "E401"
    FORBIDDEN = "E403"
    NOT_FOUND = "E404"
    
    # Server errors (5xx)
    INTERNAL_ERROR = "E500"
    BAD_GATEWAY = "E502"
    RATE_LIMITED = "E503"
    GATEWAY_TIMEOUT = "E504"
    
    # Webex specific errors
    WEBEX_API_ERROR = "E600"
    NETWORK_ERROR = "E601"
    TOKEN_EXPIRED = "E602"


class WebexTokenMissingError(RuntimeError):
    """Raised when no Webex token is available for the current request."""


def create_error_response(
    error_code: str,
    message: str,
    details: Dict[str, Any] = None,
    temporary: bool = False,
    retry_after_seconds: int = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error_code: Error code from WebexErrorCodes
        message: Human-readable error message
        details: Additional error details
        temporary: Whether this is a temporary error that can be retried
        retry_after_seconds: Suggested retry delay for temporary errors
    
    Returns:
        Standardized error response dictionary
    """
    response = {
        'success': False,
        'error_code': error_code,
        'message': message,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'server_version': MCP_SERVER_VERSION
    }
    
    if details:
        response['details'] = details
    
    if temporary:
        response['temporary'] = True
    
    if retry_after_seconds:
        response['retry_after_seconds'] = retry_after_seconds
    
    return response


def create_success_response(data: Dict[str, Any], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data: The main response data
        metadata: Additional metadata about the response
    
    Returns:
        Standardized success response dictionary
    """
    response = {
        'success': True,
        'data': data,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'server_version': MCP_SERVER_VERSION
    }
    
    if metadata:
        response['metadata'] = metadata
    
    return response


@lru_cache(maxsize=64)
def _cached_webex_api(token: str) -> WebexAPI:
    return WebexAPI(access_token=token)


def get_webex_api() -> WebexAPI:
    """Return a WebexAPI client for the current request.

    For HTTP transport, reads the token from the Authorization: Bearer header.
    Falls back to the WEBEX_ACCESS_TOKEN env var (stdio transport).
    """
    from fastmcp.server.dependencies import get_http_headers
    headers = get_http_headers()
    auth = headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        if token:
            return _cached_webex_api(token)
    env_token = os.getenv("WEBEX_ACCESS_TOKEN")
    if env_token:
        return _cached_webex_api(env_token)
    raise WebexTokenMissingError(
        "No Webex token available. Provide an 'Authorization: Bearer <token>' "
        "header (HTTP transport) or set WEBEX_ACCESS_TOKEN (stdio transport)."
    )


# Keep for backward compatibility (health_check.py uses this directly)
webex_access_token = os.getenv("WEBEX_ACCESS_TOKEN")
webex_api = WebexAPI(access_token=webex_access_token) if webex_access_token else None

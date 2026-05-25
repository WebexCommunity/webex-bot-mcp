"""
Diagnostic tools for Webex Bot MCP Server.
"""
import sys
import time
from typing import Any, Dict

from .common import (
    MCP_SERVER_VERSION,
    WebexErrorCodes,
    WebexTokenMissingError,
    create_success_response,
    get_webex_api,
)


def _check_token() -> Dict[str, Any]:
    start = time.time()
    try:
        me = get_webex_api().people.me()
        return {
            "status": "ok",
            "bot_id": me.id,
            "bot_name": me.displayName,
            "bot_email": me.emails[0] if me.emails else None,
            "org_id": me.orgId,
            "duration_ms": round((time.time() - start) * 1000),
        }
    except WebexTokenMissingError as e:
        return {
            "status": "error",
            "error_code": WebexErrorCodes.UNAUTHORIZED,
            "message": str(e),
            "duration_ms": round((time.time() - start) * 1000),
        }
    except Exception as e:
        err = str(e).lower()
        if "unauthorized" in err or "invalid token" in err or "401" in err:
            code = WebexErrorCodes.UNAUTHORIZED
        elif "forbidden" in err or "403" in err:
            code = WebexErrorCodes.FORBIDDEN
        else:
            code = WebexErrorCodes.WEBEX_API_ERROR
        return {
            "status": "error",
            "error_code": code,
            "message": str(e),
            "duration_ms": round((time.time() - start) * 1000),
        }


def _check_rooms(max_rooms: int = 10) -> Dict[str, Any]:
    start = time.time()
    try:
        rooms = list(get_webex_api().rooms.list(max=max_rooms))
        room_types: Dict[str, int] = {}
        for r in rooms:
            rt = getattr(r, "type", "unknown")
            room_types[rt] = room_types.get(rt, 0) + 1
        return {
            "status": "ok",
            "total_visible": len(rooms),
            "room_types": room_types,
            "sample": [
                {"id": r.id, "title": r.title, "type": getattr(r, "type", "unknown")}
                for r in rooms[:3]
            ],
            "duration_ms": round((time.time() - start) * 1000),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "duration_ms": round((time.time() - start) * 1000),
        }


def webex_health_check(include_rooms: bool = True) -> Dict[str, Any]:
    """
    Validate Webex connectivity and return a structured diagnostic status.

    Checks the bot token (identity + API reachability) and, optionally, lists
    visible rooms to confirm room-access permissions. Designed for agents that
    need to self-diagnose before starting a workflow.

    Args:
        include_rooms: When True (default), also verify room-list access.

    Returns:
        Standardized success response whose ``data`` contains:
        - ``overall_status``: "healthy", "degraded", or "unhealthy"
        - ``checks``: per-check result dicts keyed by check name
        - ``duration_ms``: total wall-clock time for all checks
        - ``server_version``: running MCP server version
        - ``python_version``: Python interpreter version string

        ``overall_status`` is "healthy" when all checks pass, "unhealthy" when
        the token check fails, and "degraded" when the token is valid but a
        secondary check (e.g. rooms) errors.
    """
    wall_start = time.time()

    token_check = _check_token()
    checks: Dict[str, Any] = {"token": token_check}

    if include_rooms:
        if token_check["status"] == "ok":
            checks["rooms"] = _check_rooms()
        else:
            checks["rooms"] = {
                "status": "skipped",
                "message": "Token check failed; room check skipped.",
            }

    statuses = [c["status"] for c in checks.values()]
    if any(s == "error" for s in statuses):
        overall = "unhealthy" if token_check["status"] == "error" else "degraded"
    else:
        overall = "healthy"

    return create_success_response(
        data={
            "overall_status": overall,
            "checks": checks,
            "duration_ms": round((time.time() - wall_start) * 1000),
            "server_version": MCP_SERVER_VERSION,
            "python_version": sys.version.split()[0],
        }
    )

"""
Unit tests for webex_health_check tool.

The webexpythonsdk and python-dotenv stubs are set up before any project
module is imported so no real credentials or SDK installation are needed.
"""
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# ── Provide fake env var and SDK before any tools module is imported ──────────
os.environ.setdefault("WEBEX_ACCESS_TOKEN", "test-token")

_sdk_mod = types.ModuleType("webexpythonsdk")
_sdk_mod.WebexAPI = MagicMock(return_value=MagicMock())
sys.modules.setdefault("webexpythonsdk", _sdk_mod)

if "dotenv" not in sys.modules:
    _dotenv_mod = types.ModuleType("dotenv")
    _dotenv_mod.load_dotenv = lambda *a, **kw: None
    sys.modules["dotenv"] = _dotenv_mod

from webex_bot_mcp.tools.diagnostics import webex_health_check  # noqa: E402
from webex_bot_mcp.tools.common import WebexTokenMissingError    # noqa: E402
import webex_bot_mcp.tools.diagnostics as _diag_mod             # noqa: E402


# ── helpers ───────────────────────────────────────────────────────────────────

def _fake_me(**overrides):
    me = MagicMock()
    me.id = "bot-id-123"
    me.displayName = "Test Bot"
    me.emails = ["testbot@example.com"]
    me.orgId = "org-456"
    for k, v in overrides.items():
        setattr(me, k, v)
    return me


def _fake_room(room_id="R1", title="Room One", room_type="group"):
    r = MagicMock()
    r.id = room_id
    r.title = title
    r.type = room_type
    return r


class TestWebexHealthCheckHealthy(unittest.TestCase):
    """All checks pass → overall_status healthy."""

    def setUp(self):
        self.mock_api = MagicMock()
        self.mock_api.people.me.return_value = _fake_me()
        self.mock_api.rooms.list.return_value = iter([
            _fake_room("R1", "Alpha", "group"),
            _fake_room("R2", "Beta", "direct"),
        ])

    def test_overall_status_healthy(self):
        with patch.object(_diag_mod, "get_webex_api", return_value=self.mock_api):
            result = webex_health_check()
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["overall_status"], "healthy")

    def test_token_check_fields(self):
        with patch.object(_diag_mod, "get_webex_api", return_value=self.mock_api):
            result = webex_health_check()
        token = result["data"]["checks"]["token"]
        self.assertEqual(token["status"], "ok")
        self.assertEqual(token["bot_id"], "bot-id-123")
        self.assertEqual(token["bot_name"], "Test Bot")
        self.assertEqual(token["bot_email"], "testbot@example.com")
        self.assertIn("duration_ms", token)

    def test_rooms_check_fields(self):
        with patch.object(_diag_mod, "get_webex_api", return_value=self.mock_api):
            result = webex_health_check()
        rooms = result["data"]["checks"]["rooms"]
        self.assertEqual(rooms["status"], "ok")
        self.assertEqual(rooms["total_visible"], 2)
        self.assertEqual(rooms["room_types"], {"group": 1, "direct": 1})
        self.assertEqual(len(rooms["sample"]), 2)

    def test_top_level_metadata(self):
        with patch.object(_diag_mod, "get_webex_api", return_value=self.mock_api):
            result = webex_health_check()
        data = result["data"]
        self.assertIn("duration_ms", data)
        self.assertIn("server_version", data)
        self.assertIn("python_version", data)
        self.assertIn("timestamp", result)
        self.assertIn("server_version", result)


class TestWebexHealthCheckNoRooms(unittest.TestCase):
    """include_rooms=False skips room check."""

    def setUp(self):
        self.mock_api = MagicMock()
        self.mock_api.people.me.return_value = _fake_me()

    def test_rooms_check_absent(self):
        with patch.object(_diag_mod, "get_webex_api", return_value=self.mock_api):
            result = webex_health_check(include_rooms=False)
        self.assertNotIn("rooms", result["data"]["checks"])

    def test_still_healthy(self):
        with patch.object(_diag_mod, "get_webex_api", return_value=self.mock_api):
            result = webex_health_check(include_rooms=False)
        self.assertEqual(result["data"]["overall_status"], "healthy")

    def test_rooms_list_not_called(self):
        with patch.object(_diag_mod, "get_webex_api", return_value=self.mock_api):
            webex_health_check(include_rooms=False)
        self.mock_api.rooms.list.assert_not_called()


class TestWebexHealthCheckTokenMissing(unittest.TestCase):
    """WebexTokenMissingError → unhealthy, room check skipped."""

    def _raise_missing(self):
        raise WebexTokenMissingError("No token available.")

    def test_overall_status_unhealthy(self):
        with patch.object(_diag_mod, "get_webex_api", side_effect=self._raise_missing):
            result = webex_health_check()
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["overall_status"], "unhealthy")

    def test_token_check_error(self):
        with patch.object(_diag_mod, "get_webex_api", side_effect=self._raise_missing):
            result = webex_health_check()
        token = result["data"]["checks"]["token"]
        self.assertEqual(token["status"], "error")
        self.assertEqual(token["error_code"], "E401")

    def test_rooms_skipped(self):
        with patch.object(_diag_mod, "get_webex_api", side_effect=self._raise_missing):
            result = webex_health_check()
        rooms = result["data"]["checks"]["rooms"]
        self.assertEqual(rooms["status"], "skipped")


class TestWebexHealthCheckTokenAuthError(unittest.TestCase):
    """HTTP 401 from people.me → unhealthy."""

    def setUp(self):
        self.mock_api = MagicMock()
        self.mock_api.people.me.side_effect = Exception("401 Unauthorized")

    def test_overall_status_unhealthy(self):
        with patch.object(_diag_mod, "get_webex_api", return_value=self.mock_api):
            result = webex_health_check()
        self.assertEqual(result["data"]["overall_status"], "unhealthy")

    def test_token_error_code_e401(self):
        with patch.object(_diag_mod, "get_webex_api", return_value=self.mock_api):
            result = webex_health_check()
        self.assertEqual(result["data"]["checks"]["token"]["error_code"], "E401")


class TestWebexHealthCheckRoomError(unittest.TestCase):
    """Token OK but rooms.list fails → degraded."""

    def setUp(self):
        self.mock_api = MagicMock()
        self.mock_api.people.me.return_value = _fake_me()
        self.mock_api.rooms.list.side_effect = Exception("network error")

    def test_overall_status_degraded(self):
        with patch.object(_diag_mod, "get_webex_api", return_value=self.mock_api):
            result = webex_health_check()
        self.assertEqual(result["data"]["overall_status"], "degraded")

    def test_token_still_ok(self):
        with patch.object(_diag_mod, "get_webex_api", return_value=self.mock_api):
            result = webex_health_check()
        self.assertEqual(result["data"]["checks"]["token"]["status"], "ok")

    def test_rooms_status_error(self):
        with patch.object(_diag_mod, "get_webex_api", return_value=self.mock_api):
            result = webex_health_check()
        self.assertEqual(result["data"]["checks"]["rooms"]["status"], "error")


class TestWebexHealthCheckSampleCap(unittest.TestCase):
    """Sample rooms list is capped at 3 entries."""

    def setUp(self):
        self.mock_api = MagicMock()
        self.mock_api.people.me.return_value = _fake_me()
        self.mock_api.rooms.list.return_value = iter([
            _fake_room(f"R{i}", f"Room {i}") for i in range(8)
        ])

    def test_sample_capped_at_three(self):
        with patch.object(_diag_mod, "get_webex_api", return_value=self.mock_api):
            result = webex_health_check()
        self.assertEqual(len(result["data"]["checks"]["rooms"]["sample"]), 3)

    def test_total_visible_is_full_count(self):
        with patch.object(_diag_mod, "get_webex_api", return_value=self.mock_api):
            result = webex_health_check()
        self.assertEqual(result["data"]["checks"]["rooms"]["total_visible"], 8)


if __name__ == "__main__":
    unittest.main()

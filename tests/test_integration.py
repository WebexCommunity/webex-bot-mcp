"""
Integration tests for webex-bot-mcp.

These tests make real Webex API calls and verify that each tool works
end-to-end. They are automatically SKIPPED when WEBEX_ACCESS_TOKEN is
not set, so they are safe to include in CI without credentials.

Run integration tests with an explicit opt-in flag so they are always
skipped during normal `unittest discover` runs:

    # Integration tests only:
    WEBEX_ACCESS_TOKEN=<your-bot-token> WEBEX_INTEGRATION_TESTS=1 \\
        python -m unittest tests/test_integration.py -v

    # With pytest:
    WEBEX_ACCESS_TOKEN=<your-bot-token> WEBEX_INTEGRATION_TESTS=1 \\
        python -m pytest tests/test_integration.py -v

Each test class creates its own Webex resources in setUpClass and
deletes them in tearDownClass, even when individual tests fail.
"""

import os
import sys
import time
import types
import unittest
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Remove any mock modules injected by unit test modules running in the same
# process, so integration tests always use the real SDK and dotenv.
# ---------------------------------------------------------------------------
for _k in list(sys.modules.keys()):
    if _k == "webexpythonsdk" or _k.startswith("webexpythonsdk."):
        _mod = sys.modules[_k]
        if isinstance(getattr(_mod, "WebexAPI", None), MagicMock):
            del sys.modules[_k]
    # The unit-test stub for dotenv only defines load_dotenv; remove it so the
    # real python-dotenv (which also has dotenv_values) is imported instead.
    if (_k == "dotenv" or _k.startswith("dotenv.")) and not hasattr(
        sys.modules[_k], "dotenv_values"
    ):
        del sys.modules[_k]
    # Evict cached tool modules so they re-import against the real SDK
    if _k.startswith("webex_bot_mcp"):
        del sys.modules[_k]

# ---------------------------------------------------------------------------
# Patch FastMCP's get_http_headers so that calling tools directly (outside
# an HTTP request context) falls through to the WEBEX_ACCESS_TOKEN env var.
# ---------------------------------------------------------------------------
try:
    import fastmcp.server.dependencies as _fmcp_deps
    _orig_get_http_headers = _fmcp_deps.get_http_headers
    _fmcp_deps.get_http_headers = lambda: {}
    _FMCP_PATCHED = True
except Exception:
    _FMCP_PATCHED = False
    _orig_get_http_headers = None


def tearDownModule():
    """Restore FastMCP's original get_http_headers."""
    if _FMCP_PATCHED and _orig_get_http_headers is not None:
        import fastmcp.server.dependencies as _deps
        _deps.get_http_headers = _orig_get_http_headers


# ---------------------------------------------------------------------------
# Now import the real tool modules
# ---------------------------------------------------------------------------
from webex_bot_mcp.tools.rooms import (          # noqa: E402
    list_webex_rooms, create_webex_room, get_webex_room,
    update_webex_room, delete_webex_room,
    list_webex_spaces, create_webex_space, get_webex_space,
    update_webex_space, delete_webex_space,
)
from webex_bot_mcp.tools.messages import (       # noqa: E402
    send_webex_message, list_webex_messages, delete_webex_message,
    send_webex_message_with_mentions, update_webex_message,
    send_webex_adaptive_card, build_webex_adaptive_card,
    send_webex_space_message, list_webex_space_messages,
)
from webex_bot_mcp.tools.memberships import (    # noqa: E402
    list_webex_memberships, add_webex_membership,
    update_webex_membership, delete_webex_membership,
    list_webex_space_memberships,
)
from webex_bot_mcp.tools.people import (         # noqa: E402
    get_webex_me, list_webex_people,
)
from webex_bot_mcp.tools.teams import (          # noqa: E402
    list_webex_teams, get_webex_team,
    list_webex_team_memberships,
)
from webex_bot_mcp.tools.common import _cached_webex_api  # noqa: E402

# Clear the LRU token cache so tests start with a fresh client
_cached_webex_api.cache_clear()

# ---------------------------------------------------------------------------
# Skip all tests unless explicitly opted in.
#
# Using WEBEX_INTEGRATION_TESTS=1 prevents unit tests (which inject a fake
# WEBEX_ACCESS_TOKEN=test-token via os.environ.setdefault) from accidentally
# triggering live API calls during a normal test-discovery run.
# ---------------------------------------------------------------------------
TOKEN = os.environ.get("WEBEX_ACCESS_TOKEN", "")
_RUN = os.environ.get("WEBEX_INTEGRATION_TESTS", "").lower() in ("1", "true", "yes")
_SKIP = not (TOKEN and _RUN)
_SKIP_REASON = (
    "Set WEBEX_ACCESS_TOKEN and WEBEX_INTEGRATION_TESTS=1 to run integration tests"
)

# Unique prefix so test resources can be identified in cleanup if needed
_PREFIX = f"[mcp-it-{int(time.time())}]"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(result: dict, label: str = ""):
    """Assert a tool call succeeded, showing the error message on failure."""
    assert result.get("success"), (
        f"{label + ': ' if label else ''}tool call failed — "
        f"error_code={result.get('error_code')} message={result.get('message')}"
    )
    return result["data"]


# ---------------------------------------------------------------------------
# People
# ---------------------------------------------------------------------------

@unittest.skipIf(_SKIP, _SKIP_REASON)
class TestPeopleTools(unittest.TestCase):
    """Verify the bot can retrieve its own identity and search for people."""

    def test_get_webex_me(self):
        r = get_webex_me()
        data = _ok(r, "get_webex_me")
        self.assertIn("id", data)
        self.assertIn("displayName", data)
        self.assertIn(data.get("type"), ("bot", "person"))

    def test_get_me_response_shape(self):
        r = get_webex_me()
        self.assertIn("timestamp", r)
        self.assertIn("server_version", r)

    def test_list_people_by_own_email(self):
        me = _ok(get_webex_me(), "get_webex_me for email lookup")
        email = me.get("emails", [None])[0]
        if not email:
            self.skipTest("Bot has no email address")
        r = list_webex_people(email=email)
        data = _ok(r, "list_webex_people")
        self.assertIn("people", data)
        ids = [p["id"] for p in data["people"]]
        self.assertIn(me["id"], ids)


# ---------------------------------------------------------------------------
# Rooms — full CRUD lifecycle
# ---------------------------------------------------------------------------

@unittest.skipIf(_SKIP, _SKIP_REASON)
class TestRoomsLifecycle(unittest.TestCase):
    """Create → get → list → update → delete a Webex room."""

    room_id: str = ""
    room_title = f"{_PREFIX} rooms-lifecycle"

    @classmethod
    def tearDownClass(cls):
        if cls.room_id:
            try:
                delete_webex_room(cls.room_id)
            except Exception:
                pass

    def test_01_create_room(self):
        r = create_webex_room(title=self.room_title)
        data = _ok(r, "create_webex_room")
        self.assertEqual(data["title"], self.room_title)
        self.assertIn("id", data)
        TestRoomsLifecycle.room_id = data["id"]

    def test_02_get_room(self):
        self.assertTrue(self.room_id, "room not created in test_01")
        r = get_webex_room(self.room_id)
        data = _ok(r, "get_webex_room")
        self.assertEqual(data["id"], self.room_id)
        self.assertEqual(data["title"], self.room_title)

    def test_03_list_rooms_includes_created(self):
        self.assertTrue(self.room_id, "room not created in test_01")
        r = list_webex_rooms(max_results=100)
        data = _ok(r, "list_webex_rooms")
        self.assertIn("rooms", data)
        ids = [room["id"] for room in data["rooms"]]
        self.assertIn(self.room_id, ids)

    def test_04_update_room_title(self):
        self.assertTrue(self.room_id, "room not created in test_01")
        new_title = f"{self.room_title} updated"
        r = update_webex_room(self.room_id, title=new_title)
        data = _ok(r, "update_webex_room")
        self.assertEqual(data["title"], new_title)
        # Verify the update persisted via a fresh GET
        r2 = get_webex_room(self.room_id)
        data2 = _ok(r2, "get_webex_room after update")
        self.assertEqual(data2["title"], new_title)

    def test_05_delete_room(self):
        self.assertTrue(self.room_id, "room not created in test_01")
        r = delete_webex_room(self.room_id)
        _ok(r, "delete_webex_room")
        # Verify deletion — subsequent GET should return an error
        r2 = get_webex_room(self.room_id)
        self.assertFalse(r2["success"])
        self.assertIn(r2["error_code"], ("E404", "E403", "E600"))
        TestRoomsLifecycle.room_id = ""  # prevent tearDownClass from double-deleting


# ---------------------------------------------------------------------------
# Messages — full lifecycle inside a dedicated room
# ---------------------------------------------------------------------------

@unittest.skipIf(_SKIP, _SKIP_REASON)
class TestMessagesLifecycle(unittest.TestCase):
    """Send, list, and delete messages in an integration-test room."""

    room_id: str = ""
    message_ids: list = []

    @classmethod
    def setUpClass(cls):
        cls.message_ids = []
        r = create_webex_room(title=f"{_PREFIX} messages-lifecycle")
        if r["success"]:
            cls.room_id = r["data"]["id"]

    @classmethod
    def tearDownClass(cls):
        for mid in list(cls.message_ids):
            try:
                delete_webex_message(mid)
            except Exception:
                pass
        if cls.room_id:
            try:
                delete_webex_room(cls.room_id)
            except Exception:
                pass

    def test_01_send_text_message(self):
        self.assertTrue(self.room_id, "room not created in setUpClass")
        r = send_webex_message(room_id=self.room_id, text="integration-test plain text")
        data = _ok(r, "send_webex_message text")
        self.assertEqual(data["roomId"], self.room_id)
        self.assertIn("id", data)
        TestMessagesLifecycle.message_ids.append(data["id"])

    def test_02_send_markdown_message(self):
        self.assertTrue(self.room_id, "room not created in setUpClass")
        r = send_webex_message(
            room_id=self.room_id,
            markdown="**integration-test** _markdown_",
            text="integration-test markdown fallback",
        )
        data = _ok(r, "send_webex_message markdown")
        self.assertEqual(data["roomId"], self.room_id)
        TestMessagesLifecycle.message_ids.append(data["id"])

    def test_03_list_messages_contains_sent(self):
        self.assertTrue(self.room_id, "room not created in setUpClass")
        self.assertTrue(self.message_ids, "no messages sent in earlier tests")
        r = list_webex_messages(room_id=self.room_id, max_results=20)
        data = _ok(r, "list_webex_messages")
        self.assertIn("messages", data)
        listed_ids = {m["id"] for m in data["messages"]}
        for mid in self.message_ids:
            self.assertIn(mid, listed_ids, f"message {mid} not found in listing")

    def test_04_list_messages_response_shape(self):
        self.assertTrue(self.room_id, "room not created in setUpClass")
        r = list_webex_messages(room_id=self.room_id, max_results=5)
        data = _ok(r, "list_webex_messages shape")
        for msg in data["messages"]:
            self.assertIn("id", msg)
            self.assertIn("roomId", msg)
            self.assertIn("created", msg)

    def test_05_delete_one_message(self):
        self.assertTrue(self.message_ids, "no messages to delete")
        mid = TestMessagesLifecycle.message_ids.pop()
        r = delete_webex_message(mid)
        _ok(r, "delete_webex_message")
        # Verify deletion — the message should not appear in the listing
        r2 = list_webex_messages(room_id=self.room_id, max_results=50)
        if r2["success"]:
            listed_ids = {m["id"] for m in r2["data"]["messages"]}
            self.assertNotIn(mid, listed_ids)

    def test_06_send_space_message_alias(self):
        """send_webex_space_message delegates to send_webex_message."""
        self.assertTrue(self.room_id, "room not created in setUpClass")
        r = send_webex_space_message(room_id=self.room_id, text="space-alias message")
        data = _ok(r, "send_webex_space_message")
        TestMessagesLifecycle.message_ids.append(data["id"])

    def test_07_list_space_messages_alias(self):
        """list_webex_space_messages delegates to list_webex_messages."""
        self.assertTrue(self.room_id, "room not created in setUpClass")
        r = list_webex_space_messages(room_id=self.room_id, max_results=5)
        data = _ok(r, "list_webex_space_messages")
        self.assertIn("messages", data)


# ---------------------------------------------------------------------------
# Adaptive cards
# ---------------------------------------------------------------------------

@unittest.skipIf(_SKIP, _SKIP_REASON)
class TestAdaptiveCards(unittest.TestCase):
    """Verify card building utility and card send tool."""

    room_id: str = ""

    @classmethod
    def setUpClass(cls):
        r = create_webex_room(title=f"{_PREFIX} adaptive-cards")
        if r["success"]:
            cls.room_id = r["data"]["id"]

    @classmethod
    def tearDownClass(cls):
        if cls.room_id:
            try:
                delete_webex_room(cls.room_id)
            except Exception:
                pass

    def test_build_adaptive_card_basic(self):
        """build_webex_adaptive_card constructs a card without an API call."""
        r = build_webex_adaptive_card(
            title="Test Card",
            text="Hello from integration tests",
        )
        self.assertTrue(r["success"], r.get("message"))
        card = r["data"]
        self.assertIn("type", card)
        self.assertEqual(card["type"], "AdaptiveCard")

    def test_send_adaptive_card(self):
        self.assertTrue(self.room_id, "room not created in setUpClass")
        card = {
            "type": "AdaptiveCard",
            "version": "1.2",
            "body": [{"type": "TextBlock", "text": "Integration test card"}],
        }
        r = send_webex_adaptive_card(room_id=self.room_id, card=card)
        _ok(r, "send_webex_adaptive_card")


# ---------------------------------------------------------------------------
# Memberships
# ---------------------------------------------------------------------------

@unittest.skipIf(_SKIP, _SKIP_REASON)
class TestMembershipsTools(unittest.TestCase):
    """Verify membership listing in a test room the bot created."""

    room_id: str = ""

    @classmethod
    def setUpClass(cls):
        r = create_webex_room(title=f"{_PREFIX} memberships")
        if r["success"]:
            cls.room_id = r["data"]["id"]

    @classmethod
    def tearDownClass(cls):
        if cls.room_id:
            try:
                delete_webex_room(cls.room_id)
            except Exception:
                pass

    def test_list_memberships_not_empty(self):
        self.assertTrue(self.room_id, "room not created in setUpClass")
        r = list_webex_memberships(room_id=self.room_id)
        data = _ok(r, "list_webex_memberships")
        self.assertIn("memberships", data)
        # Bot that created the room must be a member
        self.assertGreater(len(data["memberships"]), 0)

    def test_list_memberships_response_shape(self):
        self.assertTrue(self.room_id, "room not created in setUpClass")
        r = list_webex_memberships(room_id=self.room_id)
        data = _ok(r, "list_webex_memberships shape")
        for m in data["memberships"]:
            self.assertIn("id", m)
            self.assertIn("roomId", m)
            self.assertEqual(m["roomId"], self.room_id)
            self.assertIn("personId", m)

    def test_bot_is_moderator_of_own_room(self):
        """A bot is the moderator of a room it created."""
        self.assertTrue(self.room_id, "room not created in setUpClass")
        me = _ok(get_webex_me(), "get_webex_me")
        r = list_webex_memberships(room_id=self.room_id)
        data = _ok(r, "list_webex_memberships for moderator check")
        bot_memberships = [
            m for m in data["memberships"] if m.get("personId") == me["id"]
        ]
        self.assertEqual(len(bot_memberships), 1, "bot should appear exactly once")
        self.assertTrue(bot_memberships[0].get("isModerator"))

    def test_list_space_memberships_alias(self):
        """list_webex_space_memberships delegates to list_webex_memberships."""
        self.assertTrue(self.room_id, "room not created in setUpClass")
        r = list_webex_space_memberships(room_id=self.room_id)
        data = _ok(r, "list_webex_space_memberships")
        self.assertIn("memberships", data)


# ---------------------------------------------------------------------------
# Space aliases — full CRUD lifecycle mirrors rooms
# ---------------------------------------------------------------------------

@unittest.skipIf(_SKIP, _SKIP_REASON)
class TestSpaceAliases(unittest.TestCase):
    """Verify space-alias tools delegate correctly to room tools."""

    space_id: str = ""
    space_title = f"{_PREFIX} space-aliases"

    @classmethod
    def tearDownClass(cls):
        if cls.space_id:
            try:
                delete_webex_space(cls.space_id)
            except Exception:
                pass

    def test_01_create_space(self):
        r = create_webex_space(title=self.space_title)
        data = _ok(r, "create_webex_space")
        self.assertEqual(data["title"], self.space_title)
        TestSpaceAliases.space_id = data["id"]

    def test_02_get_space(self):
        self.assertTrue(self.space_id, "space not created in test_01")
        r = get_webex_space(self.space_id)
        data = _ok(r, "get_webex_space")
        self.assertEqual(data["id"], self.space_id)

    def test_03_list_spaces_includes_created(self):
        self.assertTrue(self.space_id, "space not created in test_01")
        r = list_webex_spaces(max_results=100)
        data = _ok(r, "list_webex_spaces")
        self.assertIn("spaces", data)
        ids = [s["id"] for s in data["spaces"]]
        self.assertIn(self.space_id, ids)

    def test_04_update_space_title(self):
        self.assertTrue(self.space_id, "space not created in test_01")
        new_title = f"{self.space_title} updated"
        r = update_webex_space(self.space_id, title=new_title)
        data = _ok(r, "update_webex_space")
        self.assertEqual(data["title"], new_title)

    def test_05_delete_space(self):
        self.assertTrue(self.space_id, "space not created in test_01")
        r = delete_webex_space(self.space_id)
        _ok(r, "delete_webex_space")
        r2 = get_webex_space(self.space_id)
        self.assertFalse(r2["success"])
        TestSpaceAliases.space_id = ""


# ---------------------------------------------------------------------------
# Teams — listing only (bots cannot create teams via POST /teams)
# ---------------------------------------------------------------------------

@unittest.skipIf(_SKIP, _SKIP_REASON)
class TestTeamsTools(unittest.TestCase):
    """Verify team-related tools that don't require team creation."""

    def test_list_teams_returns_list(self):
        r = list_webex_teams()
        self.assertTrue(r["success"], r.get("message"))
        self.assertIn("teams", r["data"])
        self.assertIsInstance(r["data"]["teams"], list)

    def test_list_teams_response_shape(self):
        r = list_webex_teams()
        self.assertTrue(r["success"])
        self.assertIn("timestamp", r)
        self.assertIn("server_version", r)

    def test_get_team_invalid_id_returns_error(self):
        r = get_webex_team("NOT-A-REAL-TEAM-ID")
        self.assertFalse(r["success"])
        self.assertIn("error_code", r)
        self.assertIn("message", r)

    def test_list_team_memberships_invalid_team(self):
        r = list_webex_team_memberships("NOT-A-REAL-TEAM-ID")
        self.assertFalse(r["success"])
        self.assertIn("error_code", r)


# ---------------------------------------------------------------------------
# Error handling — verify structured error responses for bad inputs
# ---------------------------------------------------------------------------

@unittest.skipIf(_SKIP, _SKIP_REASON)
class TestErrorHandling(unittest.TestCase):
    """Verify all tools return structured errors (not bare exceptions)."""

    def _assert_error_shape(self, result: dict, label: str):
        self.assertFalse(result.get("success"), f"{label}: expected failure but got success")
        self.assertIn("error_code", result, f"{label}: missing error_code")
        self.assertIn("message", result, f"{label}: missing message")
        self.assertIn("timestamp", result, f"{label}: missing timestamp")
        self.assertIn("server_version", result, f"{label}: missing server_version")

    def test_get_room_invalid_id(self):
        r = get_webex_room("INVALID-ROOM-ID-XXXX")
        self._assert_error_shape(r, "get_webex_room")

    def test_delete_room_invalid_id(self):
        r = delete_webex_room("INVALID-ROOM-ID-XXXX")
        self._assert_error_shape(r, "delete_webex_room")

    def test_update_room_invalid_id(self):
        r = update_webex_room("INVALID-ROOM-ID-XXXX", title="new title")
        self._assert_error_shape(r, "update_webex_room")

    def test_delete_message_invalid_id(self):
        r = delete_webex_message("INVALID-MSG-ID-XXXX")
        self._assert_error_shape(r, "delete_webex_message")

    def test_list_messages_invalid_room(self):
        r = list_webex_messages(room_id="INVALID-ROOM-ID-XXXX")
        self._assert_error_shape(r, "list_webex_messages")

    def test_send_message_missing_destination(self):
        """Sending a message with no room or person target must return E001/E002."""
        r = send_webex_message(text="orphan message with no destination")
        self._assert_error_shape(r, "send_webex_message no destination")
        self.assertIn(r["error_code"], ("E001", "E002", "E003"))

    def test_list_memberships_invalid_room(self):
        r = list_webex_memberships(room_id="INVALID-ROOM-ID-XXXX")
        self._assert_error_shape(r, "list_webex_memberships")

    def test_get_space_invalid_id(self):
        r = get_webex_space("INVALID-SPACE-ID-XXXX")
        self._assert_error_shape(r, "get_webex_space")

    def test_error_codes_are_in_expected_range(self):
        """All error codes from API failures must match the documented E-code scheme."""
        r = get_webex_room("INVALID-ROOM-ID-XXXX")
        code = r.get("error_code", "")
        self.assertRegex(
            code, r"^E\d{3}$",
            f"error_code '{code}' doesn't match E-code format"
        )


if __name__ == "__main__":
    unittest.main()

"""
Unit tests for message tools and shared utilities.

webexpythonsdk is mocked at the sys.modules level so tests can run without
real Webex credentials or the SDK being installed.
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

# ── Also stub python-dotenv if missing ───────────────────────────────────────
if "dotenv" not in sys.modules:
    _dotenv_mod = types.ModuleType("dotenv")
    _dotenv_mod.load_dotenv = lambda *a, **kw: None
    sys.modules["dotenv"] = _dotenv_mod

# Now it's safe to import the tools package
from tools.messages import (                          # noqa: E402
    format_mention_by_email,
    format_mention_by_person_id,
    format_mention_all,
    create_message_with_mentions,
    send_webex_message,
    send_webex_message_with_mentions,
    list_webex_messages,
)
from tools.common import (                            # noqa: E402
    create_error_response,
    create_success_response,
    WebexErrorCodes,
)
from config import WebexConfig                        # noqa: E402
import tools.messages as _msg_mod                    # noqa: E402


# ── helpers ───────────────────────────────────────────────────────────────────

def _fake_message(**overrides):
    m = MagicMock()
    m.id = "msg1"
    m.roomId = "ROOMID"
    m.text = "hello"
    m.personId = "pid"
    m.personEmail = "bot@example.com"
    m.created = "2025-01-01T00:00:00Z"
    for k, v in overrides.items():
        setattr(m, k, v)
    return m


# ── mention formatters ────────────────────────────────────────────────────────

class TestMentionFormatters(unittest.TestCase):
    def test_email_no_display_name(self):
        self.assertEqual(
            format_mention_by_email("alice@example.com"),
            "<@personEmail:alice@example.com>"
        )

    def test_email_with_display_name(self):
        self.assertEqual(
            format_mention_by_email("alice@example.com", "Alice"),
            "<@personEmail:alice@example.com|Alice>"
        )

    def test_person_id_no_display_name(self):
        self.assertEqual(
            format_mention_by_person_id("abc123"),
            "<@personId:abc123>"
        )

    def test_person_id_with_display_name(self):
        self.assertEqual(
            format_mention_by_person_id("abc123", "Bob"),
            "<@personId:abc123|Bob>"
        )

    def test_mention_all(self):
        self.assertEqual(format_mention_all(), "<@all>")


# ── create_message_with_mentions ──────────────────────────────────────────────

class TestCreateMessageWithMentions(unittest.TestCase):
    def test_no_mentions_returns_base(self):
        self.assertEqual(create_message_with_mentions("hello"), "hello")

    def test_empty_list_returns_base(self):
        self.assertEqual(create_message_with_mentions("hello", []), "hello")

    def test_email_mention_prepended(self):
        result = create_message_with_mentions(
            "check this out",
            [{"type": "email", "value": "alice@example.com", "display_name": "Alice"}]
        )
        self.assertIn("<@personEmail:alice@example.com|Alice>", result)
        self.assertTrue(result.endswith("check this out"))

    def test_all_mention_prepended(self):
        result = create_message_with_mentions("hey", [{"type": "all"}])
        self.assertTrue(result.startswith("<@all>"))
        self.assertIn("hey", result)

    def test_person_id_mention(self):
        result = create_message_with_mentions(
            "hi", [{"type": "person_id", "value": "abc123"}]
        )
        self.assertIn("<@personId:abc123>", result)

    def test_unknown_type_skipped(self):
        result = create_message_with_mentions("hi", [{"type": "unknown", "value": "x"}])
        self.assertEqual(result, "hi")

    def test_empty_email_value_skipped(self):
        result = create_message_with_mentions("hi", [{"type": "email", "value": ""}])
        self.assertEqual(result, "hi")

    def test_multiple_mentions_in_order(self):
        result = create_message_with_mentions(
            "msg",
            [
                {"type": "all"},
                {"type": "email", "value": "x@y.com"},
            ]
        )
        all_pos = result.index("<@all>")
        email_pos = result.index("<@personEmail:x@y.com>")
        self.assertLess(all_pos, email_pos)


# ── send_webex_message validation ─────────────────────────────────────────────

class TestSendWebexMessageValidation(unittest.TestCase):
    def _send(self, **kwargs):
        mock_api = MagicMock()
        with patch.object(_msg_mod, 'webex_api', mock_api):
            return send_webex_message(**kwargs)

    def test_missing_destination_is_e001(self):
        r = self._send(text="hello")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_missing_content_is_e002(self):
        r = self._send(room_id="ROOMID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E002')

    def test_text_too_long_is_e003(self):
        r = self._send(room_id="ROOMID", text="x" * 7440)
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E003')

    def test_markdown_too_long_is_e003(self):
        r = self._send(room_id="ROOMID", markdown="x" * 7440)
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E003')

    def test_files_string_wrapped_in_list(self):
        mock_api = MagicMock()
        mock_api.messages.create.return_value = _fake_message()
        with patch.object(_msg_mod, 'webex_api', mock_api):
            send_webex_message(room_id="ROOMID", files="https://example.com/f.pdf")
        call_kwargs = mock_api.messages.create.call_args[1]
        self.assertIsInstance(call_kwargs['files'], list)
        self.assertEqual(call_kwargs['files'], ["https://example.com/f.pdf"])

    def test_success_has_nonempty_timestamp(self):
        mock_api = MagicMock()
        mock_api.messages.create.return_value = _fake_message()
        with patch.object(_msg_mod, 'webex_api', mock_api):
            r = send_webex_message(room_id="ROOMID", text="hello")
        self.assertTrue(r['success'])
        self.assertIn('timestamp', r)
        self.assertNotEqual(r['timestamp'], '')

    def test_room_id_routed_to_roomid_param(self):
        mock_api = MagicMock()
        mock_api.messages.create.return_value = _fake_message()
        with patch.object(_msg_mod, 'webex_api', mock_api):
            send_webex_message(room_id="ROOMID", text="hi")
        self.assertEqual(mock_api.messages.create.call_args[1]['roomId'], "ROOMID")

    def test_person_email_routed_correctly(self):
        mock_api = MagicMock()
        mock_api.messages.create.return_value = _fake_message()
        with patch.object(_msg_mod, 'webex_api', mock_api):
            send_webex_message(to_person_email="user@example.com", text="hi")
        self.assertEqual(
            mock_api.messages.create.call_args[1]['toPersonEmail'], "user@example.com"
        )


# ── send_webex_message_with_mentions ─────────────────────────────────────────

class TestSendWebexMessageWithMentions(unittest.TestCase):
    def _send(self, **kwargs):
        mock_api = MagicMock()
        with patch.object(_msg_mod, 'webex_api', mock_api):
            return send_webex_message_with_mentions(**kwargs)

    def test_missing_destination_is_e001(self):
        r = self._send(text="hello")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_missing_content_is_e002(self):
        r = self._send(room_id="ROOMID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E002')

    def test_mention_prepended_to_markdown(self):
        mock_api = MagicMock()
        mock_api.messages.create.return_value = _fake_message()
        with patch.object(_msg_mod, 'webex_api', mock_api):
            send_webex_message_with_mentions(
                room_id="ROOMID",
                markdown="update",
                mentions=[{"type": "all"}]
            )
        sent_markdown = mock_api.messages.create.call_args[1]['markdown']
        self.assertIn("<@all>", sent_markdown)
        self.assertIn("update", sent_markdown)
        self.assertLess(
            sent_markdown.index("<@all>"),
            sent_markdown.index("update")
        )


# ── list_webex_messages ───────────────────────────────────────────────────────

class TestListWebexMessages(unittest.TestCase):
    def test_returns_structured_data(self):
        mock_api = MagicMock()
        mock_api.messages.list.return_value = [_fake_message()]
        with patch.object(_msg_mod, 'webex_api', mock_api):
            r = list_webex_messages(room_id="ROOMID")
        self.assertTrue(r['success'])
        self.assertIn('messages', r['data'])
        self.assertEqual(r['metadata']['count'], 1)

    def test_empty_room_returns_empty_list(self):
        mock_api = MagicMock()
        mock_api.messages.list.return_value = []
        with patch.object(_msg_mod, 'webex_api', mock_api):
            r = list_webex_messages(room_id="ROOMID")
        self.assertTrue(r['success'])
        self.assertEqual(r['data']['messages'], [])
        self.assertEqual(r['metadata']['count'], 0)


# ── create_error_response / create_success_response ──────────────────────────

class TestResponseBuilders(unittest.TestCase):
    def test_error_has_required_fields(self):
        r = create_error_response(WebexErrorCodes.NOT_FOUND, "not found")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E404')
        self.assertIn('timestamp', r)
        self.assertNotEqual(r['timestamp'], '')
        self.assertIn('server_version', r)

    def test_success_has_required_fields(self):
        r = create_success_response({'key': 'value'})
        self.assertTrue(r['success'])
        self.assertEqual(r['data'], {'key': 'value'})
        self.assertIn('timestamp', r)
        self.assertNotEqual(r['timestamp'], '')

    def test_temporary_error_has_retry_info(self):
        r = create_error_response(
            WebexErrorCodes.RATE_LIMITED, "rate limited",
            temporary=True, retry_after_seconds=60
        )
        self.assertTrue(r['temporary'])
        self.assertEqual(r['retry_after_seconds'], 60)

    def test_non_temporary_error_has_no_retry(self):
        r = create_error_response(WebexErrorCodes.UNAUTHORIZED, "unauthorized")
        self.assertNotIn('temporary', r)
        self.assertNotIn('retry_after_seconds', r)


# ── WebexConfig ───────────────────────────────────────────────────────────────

class TestConfig(unittest.TestCase):
    def test_valid_config_no_issues(self):
        cfg = WebexConfig(access_token="tok")
        self.assertEqual(cfg.validate(), [])

    def test_missing_token_fails(self):
        cfg = WebexConfig(access_token="")
        issues = cfg.validate()
        self.assertTrue(any("WEBEX_ACCESS_TOKEN" in i for i in issues))

    def test_warning_log_level_accepted(self):
        cfg = WebexConfig(access_token="tok", log_level="WARNING")
        self.assertEqual(cfg.validate(), [])

    def test_warn_log_level_rejected(self):
        cfg = WebexConfig(access_token="tok", log_level="WARN")
        issues = cfg.validate()
        self.assertTrue(any("Log level" in i for i in issues))

    def test_negative_rate_limit_fails(self):
        cfg = WebexConfig(access_token="tok", rate_limit_messages_per_second=-1)
        issues = cfg.validate()
        self.assertTrue(any("messages per second" in i for i in issues))

    def test_negative_timeout_fails(self):
        cfg = WebexConfig(access_token="tok", timeout_seconds=-1)
        issues = cfg.validate()
        self.assertTrue(any("Timeout" in i for i in issues))

    def test_to_dict_does_not_expose_raw_token(self):
        cfg = WebexConfig(access_token="supersecret")
        d = cfg.to_dict()
        self.assertNotIn("supersecret", str(d))
        self.assertTrue(d["access_token_configured"])

    def test_from_env_raises_if_token_missing(self):
        env_backup = os.environ.pop("WEBEX_ACCESS_TOKEN", None)
        try:
            with self.assertRaises(ValueError):
                WebexConfig.from_env()
        finally:
            if env_backup:
                os.environ["WEBEX_ACCESS_TOKEN"] = env_backup


if __name__ == '__main__':
    unittest.main()

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
from webex_bot_mcp.tools.messages import (            # noqa: E402
    format_mention_by_email,
    format_mention_by_person_id,
    format_mention_all,
    create_message_with_mentions,
    send_webex_message,
    send_webex_message_with_mentions,
    list_webex_messages,
    send_webex_adaptive_card,
    send_webex_space_adaptive_card,
    build_webex_adaptive_card,
    update_webex_message,
    get_webex_attachment_action,
)
from webex_bot_mcp.tools.common import (              # noqa: E402
    create_error_response,
    create_success_response,
    WebexErrorCodes,
)
from webex_bot_mcp.config import WebexConfig          # noqa: E402
import webex_bot_mcp.tools.messages as _msg_mod      # noqa: E402


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
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
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
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            send_webex_message(room_id="ROOMID", files="https://example.com/f.pdf")
        call_kwargs = mock_api.messages.create.call_args[1]
        self.assertIsInstance(call_kwargs['files'], list)
        self.assertEqual(call_kwargs['files'], ["https://example.com/f.pdf"])

    def test_success_has_nonempty_timestamp(self):
        mock_api = MagicMock()
        mock_api.messages.create.return_value = _fake_message()
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            r = send_webex_message(room_id="ROOMID", text="hello")
        self.assertTrue(r['success'])
        self.assertIn('timestamp', r)
        self.assertNotEqual(r['timestamp'], '')

    def test_room_id_routed_to_roomid_param(self):
        mock_api = MagicMock()
        mock_api.messages.create.return_value = _fake_message()
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            send_webex_message(room_id="ROOMID", text="hi")
        self.assertEqual(mock_api.messages.create.call_args[1]['roomId'], "ROOMID")

    def test_person_email_routed_correctly(self):
        mock_api = MagicMock()
        mock_api.messages.create.return_value = _fake_message()
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            send_webex_message(to_person_email="user@example.com", text="hi")
        self.assertEqual(
            mock_api.messages.create.call_args[1]['toPersonEmail'], "user@example.com"
        )


# ── send_webex_message_with_mentions ─────────────────────────────────────────

class TestSendWebexMessageWithMentions(unittest.TestCase):
    def _send(self, **kwargs):
        mock_api = MagicMock()
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
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
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
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
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_messages(room_id="ROOMID")
        self.assertTrue(r['success'])
        self.assertIn('messages', r['data'])
        self.assertEqual(r['metadata']['count'], 1)

    def test_empty_room_returns_empty_list(self):
        mock_api = MagicMock()
        mock_api.messages.list.return_value = []
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
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

    def test_empty_token_has_no_issues(self):
        # Token is optional in config; HTTP transport receives it per-request
        cfg = WebexConfig(access_token="")
        issues = cfg.validate()
        self.assertFalse(any("WEBEX_ACCESS_TOKEN" in i for i in issues))

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

    def test_from_env_succeeds_without_token(self):
        # Token is optional; HTTP transport receives it per-request via Authorization header
        env_backup = os.environ.pop("WEBEX_ACCESS_TOKEN", None)
        try:
            cfg = WebexConfig.from_env()
            self.assertEqual(cfg.access_token, "")
        finally:
            if env_backup:
                os.environ["WEBEX_ACCESS_TOKEN"] = env_backup


# ── Adaptive card sending ─────────────────────────────────────────────────────

_MINIMAL_BODY = [{"type": "TextBlock", "text": "Hello"}]
_MINIMAL_ACTIONS = [{"type": "Action.OpenUrl", "title": "Open", "url": "https://example.com"}]


def _send_card(**kwargs):
    mock_api = MagicMock()
    mock_api.messages.create.return_value = _fake_message()
    with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
        result = send_webex_adaptive_card(**kwargs)
    return result, mock_api


class TestSendWebexAdaptiveCard(unittest.TestCase):

    # Validation — destination
    def test_missing_destination_returns_e001(self):
        r, _ = _send_card(card_body=_MINIMAL_BODY, fallback_text="hi")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.INVALID_ARGUMENTS)

    # Validation — fallback_text
    def test_missing_fallback_text_returns_e002(self):
        r, _ = _send_card(room_id="R1", card_body=_MINIMAL_BODY)
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.MISSING_REQUIRED_FIELD)

    def test_blank_fallback_text_returns_e002(self):
        r, _ = _send_card(room_id="R1", card_body=_MINIMAL_BODY, fallback_text="   ")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.MISSING_REQUIRED_FIELD)

    # Validation — card_body
    def test_missing_card_body_returns_e002(self):
        r, _ = _send_card(room_id="R1", fallback_text="hi")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.MISSING_REQUIRED_FIELD)

    def test_empty_card_body_returns_e003(self):
        r, _ = _send_card(room_id="R1", fallback_text="hi", card_body=[])
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.INVALID_FIELD_VALUE)

    def test_non_list_card_body_returns_e003(self):
        r, _ = _send_card(room_id="R1", fallback_text="hi", card_body={"type": "TextBlock"})
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.INVALID_FIELD_VALUE)

    def test_card_body_element_missing_type_returns_e003(self):
        r, _ = _send_card(room_id="R1", fallback_text="hi", card_body=[{"text": "no type"}])
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.INVALID_FIELD_VALUE)
        self.assertEqual(r['details']['element_index'], 0)

    # Validation — card_version
    def test_invalid_card_version_returns_e003(self):
        r, _ = _send_card(room_id="R1", fallback_text="hi", card_body=_MINIMAL_BODY, card_version="2.0")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.INVALID_FIELD_VALUE)

    def test_valid_card_versions_all_accepted(self):
        for v in ("1.0", "1.1", "1.2", "1.3"):
            r, _ = _send_card(room_id="R1", fallback_text="hi", card_body=_MINIMAL_BODY, card_version=v)
            self.assertTrue(r['success'], f"version {v} should be accepted")

    # Validation — card_actions
    def test_action_element_missing_type_returns_e003(self):
        r, _ = _send_card(
            room_id="R1", fallback_text="hi", card_body=_MINIMAL_BODY,
            card_actions=[{"title": "No type"}]
        )
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.INVALID_FIELD_VALUE)
        self.assertEqual(r['details']['element_index'], 0)

    # API call structure
    def test_attachments_sent_as_list_of_one(self):
        _, mock_api = _send_card(room_id="R1", fallback_text="hi", card_body=_MINIMAL_BODY)
        call_kwargs = mock_api.messages.create.call_args[1]
        self.assertIsInstance(call_kwargs['attachments'], list)
        self.assertEqual(len(call_kwargs['attachments']), 1)

    def test_attachment_content_type(self):
        _, mock_api = _send_card(room_id="R1", fallback_text="hi", card_body=_MINIMAL_BODY)
        att = mock_api.messages.create.call_args[1]['attachments'][0]
        self.assertEqual(att['contentType'], "application/vnd.microsoft.card.adaptive")

    def test_attachment_schema(self):
        _, mock_api = _send_card(room_id="R1", fallback_text="hi", card_body=_MINIMAL_BODY)
        content = mock_api.messages.create.call_args[1]['attachments'][0]['content']
        self.assertEqual(content['$schema'], "http://adaptivecards.io/schemas/adaptive-card.json")
        self.assertEqual(content['type'], "AdaptiveCard")

    def test_fallback_text_sent_as_text_param(self):
        _, mock_api = _send_card(room_id="R1", fallback_text="Fallback!", card_body=_MINIMAL_BODY)
        self.assertEqual(mock_api.messages.create.call_args[1]['text'], "Fallback!")

    def test_card_body_in_attachment_content(self):
        _, mock_api = _send_card(room_id="R1", fallback_text="hi", card_body=_MINIMAL_BODY)
        content = mock_api.messages.create.call_args[1]['attachments'][0]['content']
        self.assertEqual(content['body'], _MINIMAL_BODY)

    def test_card_actions_in_attachment_when_provided(self):
        _, mock_api = _send_card(
            room_id="R1", fallback_text="hi",
            card_body=_MINIMAL_BODY, card_actions=_MINIMAL_ACTIONS
        )
        content = mock_api.messages.create.call_args[1]['attachments'][0]['content']
        self.assertIn('actions', content)
        self.assertEqual(content['actions'], _MINIMAL_ACTIONS)

    def test_no_actions_key_when_not_provided(self):
        _, mock_api = _send_card(room_id="R1", fallback_text="hi", card_body=_MINIMAL_BODY)
        content = mock_api.messages.create.call_args[1]['attachments'][0]['content']
        self.assertNotIn('actions', content)

    def test_room_id_routes_to_room_id_param(self):
        _, mock_api = _send_card(room_id="ROOM1", fallback_text="hi", card_body=_MINIMAL_BODY)
        self.assertEqual(mock_api.messages.create.call_args[1]['roomId'], "ROOM1")

    def test_to_person_email_routes_correctly(self):
        _, mock_api = _send_card(
            to_person_email="user@example.com", fallback_text="hi", card_body=_MINIMAL_BODY
        )
        self.assertEqual(mock_api.messages.create.call_args[1]['toPersonEmail'], "user@example.com")

    def test_parent_id_included_when_provided(self):
        _, mock_api = _send_card(
            room_id="R1", fallback_text="hi", card_body=_MINIMAL_BODY, parent_id="PARENT"
        )
        self.assertEqual(mock_api.messages.create.call_args[1]['parentId'], "PARENT")

    def test_no_parent_id_when_not_provided(self):
        _, mock_api = _send_card(room_id="R1", fallback_text="hi", card_body=_MINIMAL_BODY)
        self.assertNotIn('parentId', mock_api.messages.create.call_args[1])

    def test_default_card_version_is_1_3(self):
        _, mock_api = _send_card(room_id="R1", fallback_text="hi", card_body=_MINIMAL_BODY)
        content = mock_api.messages.create.call_args[1]['attachments'][0]['content']
        self.assertEqual(content['version'], "1.3")

    def test_custom_card_version_used(self):
        _, mock_api = _send_card(
            room_id="R1", fallback_text="hi", card_body=_MINIMAL_BODY, card_version="1.2"
        )
        content = mock_api.messages.create.call_args[1]['attachments'][0]['content']
        self.assertEqual(content['version'], "1.2")

    # Response shape
    def test_success_response_shape(self):
        r, _ = _send_card(room_id="R1", fallback_text="hi", card_body=_MINIMAL_BODY)
        self.assertTrue(r['success'])
        self.assertIn('data', r)
        self.assertEqual(r['metadata']['operation'], 'send_adaptive_card')
        self.assertEqual(r['metadata']['card_version'], '1.3')
        self.assertFalse(r['metadata']['has_actions'])
        self.assertEqual(r['metadata']['body_element_count'], 1)

    def test_has_actions_true_when_actions_provided(self):
        r, _ = _send_card(
            room_id="R1", fallback_text="hi",
            card_body=_MINIMAL_BODY, card_actions=_MINIMAL_ACTIONS
        )
        self.assertTrue(r['metadata']['has_actions'])

    def test_api_exception_returns_error_response(self):
        mock_api = MagicMock()
        mock_api.messages.create.side_effect = Exception("network error")
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            r = send_webex_adaptive_card(room_id="R1", fallback_text="hi", card_body=_MINIMAL_BODY)
        self.assertFalse(r['success'])
        self.assertIn('error_code', r)


class TestSendWebexSpaceAdaptiveCard(unittest.TestCase):

    def test_delegates_space_id_as_room_id(self):
        mock_api = MagicMock()
        mock_api.messages.create.return_value = _fake_message()
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            r = send_webex_space_adaptive_card(
                space_id="SID", fallback_text="hi", card_body=_MINIMAL_BODY
            )
        self.assertTrue(r['success'])
        self.assertEqual(mock_api.messages.create.call_args[1]['roomId'], "SID")

    def test_missing_destination_returns_e001(self):
        mock_api = MagicMock()
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            r = send_webex_space_adaptive_card(fallback_text="hi", card_body=_MINIMAL_BODY)
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.INVALID_ARGUMENTS)

    def test_to_person_email_passes_through(self):
        mock_api = MagicMock()
        mock_api.messages.create.return_value = _fake_message()
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            r = send_webex_space_adaptive_card(
                to_person_email="u@x.com", fallback_text="hi", card_body=_MINIMAL_BODY
            )
        self.assertTrue(r['success'])
        self.assertEqual(mock_api.messages.create.call_args[1]['toPersonEmail'], "u@x.com")


# ── Card builder ──────────────────────────────────────────────────────────────

class TestBuildWebexAdaptiveCard(unittest.TestCase):

    def test_title_only_returns_single_container(self):
        r = build_webex_adaptive_card(title="Hello")
        self.assertIn('card_body', r)
        self.assertIn('card_actions', r)
        self.assertEqual(len(r['card_body']), 1)
        self.assertEqual(r['card_body'][0]['type'], 'Container')
        items = r['card_body'][0]['items']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['type'], 'TextBlock')
        self.assertEqual(items[0]['text'], 'Hello')
        self.assertEqual(items[0]['weight'], 'Bolder')

    def test_card_actions_empty_when_none_provided(self):
        r = build_webex_adaptive_card(title="Hi")
        self.assertEqual(r['card_actions'], [])

    def test_subtitle_adds_subtle_text_block(self):
        r = build_webex_adaptive_card(title="T", subtitle="Sub")
        items = r['card_body'][0]['items']
        self.assertEqual(len(items), 2)
        subtitle_block = items[1]
        self.assertEqual(subtitle_block['type'], 'TextBlock')
        self.assertEqual(subtitle_block['text'], 'Sub')
        self.assertTrue(subtitle_block['isSubtle'])

    def test_image_url_adds_image_element(self):
        r = build_webex_adaptive_card(title="T", image_url="https://img.example.com/x.png")
        types = [el['type'] for el in r['card_body'][0]['items']]
        self.assertIn('Image', types)

    def test_body_text_adds_text_block(self):
        r = build_webex_adaptive_card(title="T", body_text="Details here")
        types = [el['type'] for el in r['card_body'][0]['items']]
        self.assertIn('TextBlock', types)
        texts = [el['text'] for el in r['card_body'][0]['items'] if el['type'] == 'TextBlock']
        self.assertIn("Details here", texts)

    def test_facts_adds_fact_set(self):
        r = build_webex_adaptive_card(
            title="T", facts=[{"title": "Region", "value": "us-east-1"}]
        )
        types = [el['type'] for el in r['card_body'][0]['items']]
        self.assertIn('FactSet', types)
        fact_set = next(el for el in r['card_body'][0]['items'] if el['type'] == 'FactSet')
        self.assertEqual(fact_set['facts'][0]['title'], 'Region')
        self.assertEqual(fact_set['facts'][0]['value'], 'us-east-1')

    def test_url_action_maps_to_open_url(self):
        r = build_webex_adaptive_card(
            title="T",
            actions=[{"type": "url", "title": "Go", "url": "https://example.com"}]
        )
        self.assertEqual(len(r['card_actions']), 1)
        self.assertEqual(r['card_actions'][0]['type'], 'Action.OpenUrl')
        self.assertEqual(r['card_actions'][0]['url'], 'https://example.com')

    def test_submit_action_maps_to_action_submit(self):
        r = build_webex_adaptive_card(
            title="T",
            actions=[{"type": "submit", "title": "OK", "data": {"action": "confirm"}}]
        )
        self.assertEqual(r['card_actions'][0]['type'], 'Action.Submit')
        self.assertEqual(r['card_actions'][0]['data']['action'], 'confirm')

    def test_style_applied_to_container(self):
        r = build_webex_adaptive_card(title="T", style="good")
        self.assertEqual(r['card_body'][0]['style'], 'good')

    def test_default_style_omits_style_key(self):
        r = build_webex_adaptive_card(title="T", style="default")
        self.assertNotIn('style', r['card_body'][0])

    def test_invalid_style_returns_error(self):
        r = build_webex_adaptive_card(title="T", style="invalid")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.INVALID_FIELD_VALUE)

    def test_missing_title_returns_error(self):
        r = build_webex_adaptive_card(title="")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.MISSING_REQUIRED_FIELD)

    def test_blank_title_returns_error(self):
        r = build_webex_adaptive_card(title="   ")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.MISSING_REQUIRED_FIELD)

    def test_facts_element_missing_value_returns_error(self):
        r = build_webex_adaptive_card(title="T", facts=[{"title": "Key"}])
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.INVALID_FIELD_VALUE)
        self.assertEqual(r['details']['element_index'], 0)

    def test_actions_element_invalid_type_returns_error(self):
        r = build_webex_adaptive_card(title="T", actions=[{"type": "invalid", "title": "X"}])
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.INVALID_FIELD_VALUE)

    def test_actions_element_missing_title_returns_error(self):
        r = build_webex_adaptive_card(title="T", actions=[{"type": "url", "url": "https://x.com"}])
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.INVALID_FIELD_VALUE)

    def test_all_parameters_produce_correct_element_order(self):
        r = build_webex_adaptive_card(
            title="T", subtitle="S", image_url="https://img.x.com/i.png",
            body_text="Body", facts=[{"title": "k", "value": "v"}]
        )
        items = r['card_body'][0]['items']
        element_types = [el['type'] for el in items]
        self.assertEqual(element_types, ['TextBlock', 'TextBlock', 'Image', 'TextBlock', 'FactSet'])

    def test_result_is_directly_usable_with_send(self):
        card = build_webex_adaptive_card(title="Test Card")
        self.assertIn('card_body', card)
        self.assertIn('card_actions', card)
        mock_api = MagicMock()
        mock_api.messages.create.return_value = _fake_message()
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            r = send_webex_adaptive_card(
                room_id="R1", fallback_text="Test Card", **card
            )
        self.assertTrue(r['success'])


# ── update_webex_message ──────────────────────────────────────────────────────

class TestUpdateWebexMessage(unittest.TestCase):

    def _update(self, **kwargs):
        mock_api = MagicMock()
        mock_api.messages.update.return_value = _fake_message()
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            result = update_webex_message(**kwargs)
        return result, mock_api

    def test_missing_message_id_returns_e001(self):
        mock_api = MagicMock()
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            r = update_webex_message(message_id="", text="hi")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.INVALID_ARGUMENTS)

    def test_neither_text_nor_markdown_returns_e002(self):
        mock_api = MagicMock()
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            r = update_webex_message(message_id="MSG1")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.MISSING_REQUIRED_FIELD)
        self.assertIn('required_one_of', r['details'])

    def test_text_only_succeeds(self):
        r, mock_api = self._update(message_id="MSG1", text="updated text")
        self.assertTrue(r['success'])
        call_kwargs = mock_api.messages.update.call_args[1]
        self.assertEqual(call_kwargs['messageId'], "MSG1")
        self.assertEqual(call_kwargs['text'], "updated text")
        self.assertNotIn('markdown', call_kwargs)

    def test_markdown_only_succeeds(self):
        r, mock_api = self._update(message_id="MSG1", markdown="**updated**")
        self.assertTrue(r['success'])
        call_kwargs = mock_api.messages.update.call_args[1]
        self.assertEqual(call_kwargs['messageId'], "MSG1")
        self.assertEqual(call_kwargs['markdown'], "**updated**")
        self.assertNotIn('text', call_kwargs)

    def test_both_text_and_markdown_sends_both(self):
        r, mock_api = self._update(message_id="MSG1", text="plain", markdown="**rich**")
        self.assertTrue(r['success'])
        call_kwargs = mock_api.messages.update.call_args[1]
        self.assertEqual(call_kwargs['text'], "plain")
        self.assertEqual(call_kwargs['markdown'], "**rich**")

    def test_success_response_shape(self):
        r, _ = self._update(message_id="MSG1", text="hello")
        self.assertTrue(r['success'])
        self.assertIn('data', r)
        self.assertEqual(r['metadata']['operation'], 'update_message')
        self.assertEqual(r['metadata']['message_id'], 'MSG1')
        self.assertEqual(r['metadata']['content_type'], 'text')

    def test_markdown_sets_content_type_markdown(self):
        r, _ = self._update(message_id="MSG1", markdown="**hi**")
        self.assertEqual(r['metadata']['content_type'], 'markdown')

    def test_api_exception_returns_error_response(self):
        mock_api = MagicMock()
        mock_api.messages.update.side_effect = Exception("not found")
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            r = update_webex_message(message_id="MSG1", text="hi")
        self.assertFalse(r['success'])
        self.assertIn('error_code', r)

    def test_404_exception_maps_to_e404(self):
        mock_api = MagicMock()
        mock_api.messages.update.side_effect = Exception("404 not found")
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            r = update_webex_message(message_id="MISSING", text="hi")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.NOT_FOUND)

    def test_unauthorized_exception_maps_to_e401(self):
        mock_api = MagicMock()
        mock_api.messages.update.side_effect = Exception("unauthorized")
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            r = update_webex_message(message_id="MSG1", text="hi")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.UNAUTHORIZED)

    def test_response_contains_timestamp(self):
        r, _ = self._update(message_id="MSG1", text="hi")
        self.assertIn('timestamp', r)
        self.assertNotEqual(r['timestamp'], '')


# ── get_webex_attachment_action ───────────────────────────────────────────────

class TestGetWebexAttachmentAction(unittest.TestCase):

    def _fake_action(self, **overrides):
        a = MagicMock()
        a.id = "ACT1"
        a.type = "submit"
        a.messageId = "MSG1"
        a.inputs = {"decision": "approve", "comment": "LGTM"}
        a.roomId = "ROOM1"
        a.personId = "PID1"
        a.created = "2025-01-01T00:00:00Z"
        for k, v in overrides.items():
            setattr(a, k, v)
        return a

    def _get(self, action_id, action_obj=None):
        mock_api = MagicMock()
        mock_api.attachment_actions.get.return_value = (
            action_obj if action_obj is not None else self._fake_action()
        )
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            result = get_webex_attachment_action(action_id)
        return result, mock_api

    def test_missing_action_id_returns_e001(self):
        mock_api = MagicMock()
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_attachment_action("")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.INVALID_ARGUMENTS)

    def test_success_response_shape(self):
        r, _ = self._get("ACT1")
        self.assertTrue(r['success'])
        self.assertIn('data', r)
        self.assertEqual(r['metadata']['operation'], 'get_attachment_action')
        self.assertEqual(r['metadata']['action_id'], 'ACT1')

    def test_sdk_called_with_action_id(self):
        _, mock_api = self._get("ACT1")
        mock_api.attachment_actions.get.assert_called_once_with("ACT1")

    def test_inputs_present_in_data(self):
        r, _ = self._get("ACT1")
        self.assertIn('inputs', r['data'])
        self.assertEqual(r['data']['inputs']['decision'], 'approve')

    def test_message_id_in_data(self):
        r, _ = self._get("ACT1")
        self.assertEqual(r['data']['messageId'], 'MSG1')

    def test_room_id_in_data(self):
        r, _ = self._get("ACT1")
        self.assertEqual(r['data']['roomId'], 'ROOM1')

    def test_person_id_in_data(self):
        r, _ = self._get("ACT1")
        self.assertEqual(r['data']['personId'], 'PID1')

    def test_none_fields_omitted_from_data(self):
        action = self._fake_action(type=None)
        r, _ = self._get("ACT1", action_obj=action)
        self.assertTrue(r['success'])
        self.assertNotIn('type', r['data'])

    def test_datetime_created_converted_to_string(self):
        from datetime import datetime
        action = self._fake_action()
        action.created = datetime(2025, 1, 1, 12, 0, 0)
        r, _ = self._get("ACT1", action_obj=action)
        self.assertTrue(r['success'])
        self.assertIn('2025-01-01', r['data']['created'])

    def test_api_exception_returns_error_response(self):
        mock_api = MagicMock()
        mock_api.attachment_actions.get.side_effect = Exception("network error")
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_attachment_action("ACT1")
        self.assertFalse(r['success'])
        self.assertIn('error_code', r)

    def test_404_exception_maps_to_e404(self):
        mock_api = MagicMock()
        mock_api.attachment_actions.get.side_effect = Exception("404 not found")
        with patch.object(_msg_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_attachment_action("MISSING")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], WebexErrorCodes.NOT_FOUND)

    def test_response_contains_timestamp(self):
        r, _ = self._get("ACT1")
        self.assertIn('timestamp', r)
        self.assertNotEqual(r['timestamp'], '')


if __name__ == '__main__':
    unittest.main()

"""
Unit tests for webhook tools.

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

from webex_bot_mcp.tools.webhooks import (        # noqa: E402
    list_webex_webhooks,
    create_webex_webhook,
    get_webex_webhook,
    update_webex_webhook,
    delete_webex_webhook,
)
import webex_bot_mcp.tools.webhooks as _wh_mod   # noqa: E402


# ── helpers ───────────────────────────────────────────────────────────────────

def _fake_webhook(**overrides):
    w = MagicMock()
    w.id = "wh1"
    w.name = "My Webhook"
    w.targetUrl = "https://example.com/webhook"
    w.resource = "messages"
    w.event = "created"
    w.status = "active"
    w.created = "2025-01-01T00:00:00Z"
    w.filter = None
    w.secret = None
    w.orgId = None
    w.createdBy = None
    w.appId = None
    w.ownedBy = None
    for k, v in overrides.items():
        setattr(w, k, v)
    return w


def _api_with_webhook(webhook=None):
    mock_api = MagicMock()
    mock_api.webhooks.create.return_value = webhook or _fake_webhook()
    mock_api.webhooks.get.return_value = webhook or _fake_webhook()
    mock_api.webhooks.update.return_value = webhook or _fake_webhook()
    mock_api.webhooks.list.return_value = [webhook or _fake_webhook()]
    return mock_api


# ── list_webex_webhooks ───────────────────────────────────────────────────────

class TestListWebexWebhooks(unittest.TestCase):
    def _list(self, **kwargs):
        mock_api = _api_with_webhook()
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            return list_webex_webhooks(**kwargs), mock_api

    def test_success_returns_webhooks_list(self):
        r, _ = self._list()
        self.assertTrue(r['success'])
        self.assertIn('webhooks', r['data'])
        self.assertEqual(len(r['data']['webhooks']), 1)

    def test_metadata_count(self):
        r, _ = self._list()
        self.assertEqual(r['metadata']['count'], 1)

    def test_max_results_passed_as_max(self):
        r, mock_api = self._list(max_results=10)
        mock_api.webhooks.list.assert_called_once_with(max=10)

    def test_no_max_results_omits_param(self):
        r, mock_api = self._list()
        mock_api.webhooks.list.assert_called_once_with()

    def test_webhook_fields_present(self):
        r, _ = self._list()
        wh = r['data']['webhooks'][0]
        for field in ('id', 'name', 'targetUrl', 'resource', 'event', 'status', 'created'):
            self.assertIn(field, wh)

    def test_optional_filter_included_when_set(self):
        mock_api = MagicMock()
        mock_api.webhooks.list.return_value = [_fake_webhook(filter="roomId=abc")]
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_webhooks()
        self.assertIn('filter', r['data']['webhooks'][0])

    def test_exception_returns_error(self):
        mock_api = MagicMock()
        mock_api.webhooks.list.side_effect = Exception("network error")
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_webhooks()
        self.assertFalse(r['success'])

    def test_empty_list(self):
        mock_api = MagicMock()
        mock_api.webhooks.list.return_value = []
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_webhooks()
        self.assertTrue(r['success'])
        self.assertEqual(r['data']['webhooks'], [])
        self.assertEqual(r['metadata']['count'], 0)


# ── create_webex_webhook ──────────────────────────────────────────────────────

class TestCreateWebexWebhook(unittest.TestCase):
    def _create(self, **kwargs):
        mock_api = _api_with_webhook()
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            return create_webex_webhook(**kwargs), mock_api

    def test_success_basic(self):
        r, _ = self._create(
            name="Test", target_url="https://example.com/wh",
            resource="messages", event="created"
        )
        self.assertTrue(r['success'])
        self.assertIn('webhook', r['data'])

    def test_missing_name_is_e001(self):
        r, _ = self._create(
            name="", target_url="https://example.com/wh",
            resource="messages", event="created"
        )
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_missing_target_url_is_e001(self):
        r, _ = self._create(
            name="Test", target_url="",
            resource="messages", event="created"
        )
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_missing_resource_is_e001(self):
        r, _ = self._create(
            name="Test", target_url="https://example.com/wh",
            resource="", event="created"
        )
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_missing_event_is_e001(self):
        r, _ = self._create(
            name="Test", target_url="https://example.com/wh",
            resource="messages", event=""
        )
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_sdk_called_with_correct_params(self):
        r, mock_api = self._create(
            name="Test", target_url="https://example.com/wh",
            resource="messages", event="created"
        )
        call_kwargs = mock_api.webhooks.create.call_args[1]
        self.assertEqual(call_kwargs['name'], "Test")
        self.assertEqual(call_kwargs['targetUrl'], "https://example.com/wh")
        self.assertEqual(call_kwargs['resource'], "messages")
        self.assertEqual(call_kwargs['event'], "created")

    def test_optional_filter_passed_to_sdk(self):
        r, mock_api = self._create(
            name="Test", target_url="https://example.com/wh",
            resource="messages", event="created", filter="roomId=abc"
        )
        call_kwargs = mock_api.webhooks.create.call_args[1]
        self.assertEqual(call_kwargs['filter'], "roomId=abc")

    def test_optional_secret_passed_to_sdk(self):
        r, mock_api = self._create(
            name="Test", target_url="https://example.com/wh",
            resource="messages", event="created", secret="mysecret"
        )
        call_kwargs = mock_api.webhooks.create.call_args[1]
        self.assertEqual(call_kwargs['secret'], "mysecret")

    def test_filter_omitted_when_none(self):
        r, mock_api = self._create(
            name="Test", target_url="https://example.com/wh",
            resource="messages", event="created"
        )
        call_kwargs = mock_api.webhooks.create.call_args[1]
        self.assertNotIn('filter', call_kwargs)

    def test_secret_omitted_when_none(self):
        r, mock_api = self._create(
            name="Test", target_url="https://example.com/wh",
            resource="messages", event="created"
        )
        call_kwargs = mock_api.webhooks.create.call_args[1]
        self.assertNotIn('secret', call_kwargs)

    def test_exception_returns_error(self):
        mock_api = MagicMock()
        mock_api.webhooks.create.side_effect = Exception("403 Forbidden")
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            r = create_webex_webhook(
                name="Test", target_url="https://example.com/wh",
                resource="messages", event="created"
            )
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E403')

    def test_404_maps_to_not_found(self):
        mock_api = MagicMock()
        mock_api.webhooks.create.side_effect = Exception("404 not found")
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            r = create_webex_webhook(
                name="Test", target_url="https://example.com/wh",
                resource="messages", event="created"
            )
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E404')

    def test_response_has_timestamp(self):
        r, _ = self._create(
            name="Test", target_url="https://example.com/wh",
            resource="messages", event="created"
        )
        self.assertIn('timestamp', r)
        self.assertTrue(r['timestamp'])


# ── get_webex_webhook ─────────────────────────────────────────────────────────

class TestGetWebexWebhook(unittest.TestCase):
    def _get(self, webhook_id="wh1"):
        mock_api = _api_with_webhook()
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            return get_webex_webhook(webhook_id=webhook_id), mock_api

    def test_success_returns_webhook(self):
        r, _ = self._get()
        self.assertTrue(r['success'])
        self.assertIn('webhook', r['data'])
        self.assertEqual(r['data']['webhook']['id'], 'wh1')

    def test_sdk_called_with_webhook_id(self):
        r, mock_api = self._get("whXYZ")
        mock_api.webhooks.get.assert_called_once_with(webhookId="whXYZ")

    def test_missing_webhook_id_is_e001(self):
        mock_api = MagicMock()
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_webhook(webhook_id="")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_404_maps_to_not_found(self):
        mock_api = MagicMock()
        mock_api.webhooks.get.side_effect = Exception("404 not found")
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_webhook(webhook_id="missing")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E404')

    def test_metadata_contains_webhook_id(self):
        r, _ = self._get("wh1")
        self.assertEqual(r['metadata']['webhook_id'], 'wh1')


# ── update_webex_webhook ──────────────────────────────────────────────────────

class TestUpdateWebexWebhook(unittest.TestCase):
    def _update(self, webhook_id="wh1", name="Updated", target_url="https://example.com/wh", **kwargs):
        mock_api = _api_with_webhook()
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            return update_webex_webhook(
                webhook_id=webhook_id, name=name, target_url=target_url, **kwargs
            ), mock_api

    def test_success_returns_webhook(self):
        r, _ = self._update()
        self.assertTrue(r['success'])
        self.assertIn('webhook', r['data'])

    def test_sdk_called_with_required_params(self):
        r, mock_api = self._update(webhook_id="wh1", name="New Name", target_url="https://new.example.com")
        call_kwargs = mock_api.webhooks.update.call_args[1]
        self.assertEqual(call_kwargs['webhookId'], 'wh1')
        self.assertEqual(call_kwargs['name'], 'New Name')
        self.assertEqual(call_kwargs['targetUrl'], 'https://new.example.com')

    def test_missing_webhook_id_is_e001(self):
        mock_api = MagicMock()
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            r = update_webex_webhook(
                webhook_id="", name="Name", target_url="https://example.com"
            )
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_missing_name_is_e001(self):
        mock_api = MagicMock()
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            r = update_webex_webhook(
                webhook_id="wh1", name="", target_url="https://example.com"
            )
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_missing_target_url_is_e001(self):
        mock_api = MagicMock()
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            r = update_webex_webhook(
                webhook_id="wh1", name="Name", target_url=""
            )
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_optional_secret_passed_to_sdk(self):
        r, mock_api = self._update(secret="newsecret")
        call_kwargs = mock_api.webhooks.update.call_args[1]
        self.assertEqual(call_kwargs['secret'], 'newsecret')

    def test_optional_status_passed_to_sdk(self):
        r, mock_api = self._update(status="inactive")
        call_kwargs = mock_api.webhooks.update.call_args[1]
        self.assertEqual(call_kwargs['status'], 'inactive')

    def test_secret_omitted_when_none(self):
        r, mock_api = self._update()
        call_kwargs = mock_api.webhooks.update.call_args[1]
        self.assertNotIn('secret', call_kwargs)

    def test_status_omitted_when_none(self):
        r, mock_api = self._update()
        call_kwargs = mock_api.webhooks.update.call_args[1]
        self.assertNotIn('status', call_kwargs)

    def test_metadata_contains_webhook_id(self):
        r, _ = self._update(webhook_id="wh1")
        self.assertEqual(r['metadata']['webhook_id'], 'wh1')

    def test_404_maps_to_not_found(self):
        mock_api = MagicMock()
        mock_api.webhooks.update.side_effect = Exception("404 not found")
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            r = update_webex_webhook(
                webhook_id="missing", name="Name", target_url="https://example.com"
            )
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E404')


# ── delete_webex_webhook ──────────────────────────────────────────────────────

class TestDeleteWebexWebhook(unittest.TestCase):
    def _delete(self, webhook_id="wh1"):
        mock_api = MagicMock()
        mock_api.webhooks.delete.return_value = None
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            return delete_webex_webhook(webhook_id=webhook_id), mock_api

    def test_success_returns_deleted_true(self):
        r, _ = self._delete()
        self.assertTrue(r['success'])
        self.assertTrue(r['data']['deleted'])

    def test_success_returns_webhook_id(self):
        r, _ = self._delete("wh1")
        self.assertEqual(r['data']['webhook_id'], 'wh1')

    def test_sdk_called_with_webhook_id(self):
        r, mock_api = self._delete("whABC")
        mock_api.webhooks.delete.assert_called_once_with(webhookId="whABC")

    def test_missing_webhook_id_is_e001(self):
        mock_api = MagicMock()
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_webhook(webhook_id="")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_404_maps_to_not_found(self):
        mock_api = MagicMock()
        mock_api.webhooks.delete.side_effect = Exception("404 not found")
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_webhook(webhook_id="missing")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E404')

    def test_unauthorized_maps_to_e401(self):
        mock_api = MagicMock()
        mock_api.webhooks.delete.side_effect = Exception("unauthorized")
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_webhook(webhook_id="wh1")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E401')

    def test_rate_limit_maps_to_e503(self):
        mock_api = MagicMock()
        mock_api.webhooks.delete.side_effect = Exception("rate limit exceeded")
        with patch.object(_wh_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_webhook(webhook_id="wh1")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E503')
        self.assertTrue(r.get('temporary'))

    def test_response_has_timestamp(self):
        r, _ = self._delete()
        self.assertIn('timestamp', r)
        self.assertTrue(r['timestamp'])


if __name__ == '__main__':
    unittest.main()

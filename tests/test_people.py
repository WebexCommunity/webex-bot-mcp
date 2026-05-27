"""
Unit tests for Webex People management tools.

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

import webex_bot_mcp.tools.people as _people_mod  # noqa: E402
from webex_bot_mcp.tools.people import (           # noqa: E402
    get_webex_me,
    list_webex_people,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _fake_person(**overrides):
    p = MagicMock()
    p.id = "PERSONID"
    p.emails = ["user@example.com"]
    p.displayName = "Test User"
    p.nickName = "Test"
    p.firstName = "Test"
    p.lastName = "User"
    p.avatar = "https://avatar.example.com/avatar.jpg"
    p.orgId = "ORGID"
    p.created = "2025-01-01T00:00:00Z"
    p.status = "active"
    p.type = "person"
    # Optional attributes — must be falsy so they are not included by default
    p.userName = None
    p.lastModified = None
    p.roles = None
    p.licenses = None
    p.phoneNumbers = None
    p.extension = None
    p.locationId = None
    p.addresses = None
    p.timezone = None
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


# ── get_webex_me ──────────────────────────────────────────────────────────────

class TestGetWebexMe(unittest.TestCase):
    def test_success_returns_user(self):
        mock_api = MagicMock()
        mock_api.people.me.return_value = _fake_person()
        with patch.object(_people_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_me()
        self.assertTrue(r['success'])
        self.assertIn('user', r['data'])

    def test_no_parameters_passed_to_sdk(self):
        mock_api = MagicMock()
        mock_api.people.me.return_value = _fake_person()
        with patch.object(_people_mod, 'get_webex_api', return_value=mock_api):
            get_webex_me()
        mock_api.people.me.assert_called_once_with()

    def test_user_dict_has_required_fields(self):
        mock_api = MagicMock()
        mock_api.people.me.return_value = _fake_person()
        with patch.object(_people_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_me()
        user = r['data']['user']
        for field in ('id', 'emails', 'displayName', 'nickName', 'firstName',
                      'lastName', 'orgId', 'created', 'status', 'type'):
            self.assertIn(field, user)

    def test_optional_fields_absent_when_none(self):
        mock_api = MagicMock()
        mock_api.people.me.return_value = _fake_person()
        with patch.object(_people_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_me()
        user = r['data']['user']
        for field in ('userName', 'roles', 'licenses', 'phoneNumbers', 'timezone'):
            self.assertNotIn(field, user)

    def test_optional_timezone_included_when_set(self):
        mock_api = MagicMock()
        mock_api.people.me.return_value = _fake_person(timezone="America/New_York")
        with patch.object(_people_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_me()
        self.assertEqual(r['data']['user']['timezone'], "America/New_York")

    def test_optional_roles_included_when_set(self):
        mock_api = MagicMock()
        mock_api.people.me.return_value = _fake_person(roles=["admin"])
        with patch.object(_people_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_me()
        self.assertEqual(r['data']['user']['roles'], ["admin"])

    def test_has_timestamp(self):
        mock_api = MagicMock()
        mock_api.people.me.return_value = _fake_person()
        with patch.object(_people_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_me()
        self.assertIn('timestamp', r)

    def test_has_server_version(self):
        mock_api = MagicMock()
        mock_api.people.me.return_value = _fake_person()
        with patch.object(_people_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_me()
        self.assertIn('server_version', r)

    def test_unauthorized_returns_error(self):
        mock_api = MagicMock()
        mock_api.people.me.side_effect = Exception("unauthorized")
        with patch.object(_people_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_me()
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E401')

    def test_network_error_is_temporary(self):
        mock_api = MagicMock()
        mock_api.people.me.side_effect = Exception("network connection refused")
        with patch.object(_people_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_me()
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E601')
        self.assertTrue(r.get('temporary'))

    def test_forbidden_returns_error(self):
        mock_api = MagicMock()
        mock_api.people.me.side_effect = Exception("forbidden")
        with patch.object(_people_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_me()
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E403')


# ── list_webex_people ─────────────────────────────────────────────────────────

class TestListWebexPeople(unittest.TestCase):
    def _call(self, **kwargs):
        mock_api = MagicMock()
        mock_api.people.list.return_value = []
        with patch.object(_people_mod, 'get_webex_api', return_value=mock_api):
            return mock_api, list_webex_people(**kwargs)

    def test_returns_people_list(self):
        mock_api = MagicMock()
        mock_api.people.list.return_value = [_fake_person(), _fake_person(id="PID2")]
        with patch.object(_people_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_people()
        self.assertTrue(r['success'])
        self.assertEqual(len(r['data']['people']), 2)

    def test_empty_list(self):
        mock_api, r = self._call()
        self.assertTrue(r['success'])
        self.assertEqual(r['data']['people'], [])

    def test_metadata_count_matches(self):
        mock_api = MagicMock()
        mock_api.people.list.return_value = [_fake_person(), _fake_person()]
        with patch.object(_people_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_people()
        self.assertEqual(r['metadata']['count'], 2)

    def test_email_filter_passed(self):
        mock_api, _ = self._call(email="user@example.com")
        mock_api.people.list.assert_called_once_with(email="user@example.com")

    def test_display_name_filter_passed(self):
        mock_api, _ = self._call(display_name="Test User")
        mock_api.people.list.assert_called_once_with(displayName="Test User")

    def test_person_id_filter_passed(self):
        mock_api, _ = self._call(person_id="PID")
        mock_api.people.list.assert_called_once_with(id="PID")

    def test_org_id_filter_passed(self):
        mock_api, _ = self._call(org_id="OID")
        mock_api.people.list.assert_called_once_with(orgId="OID")

    def test_calling_data_filter_passed(self):
        mock_api, _ = self._call(calling_data=True)
        mock_api.people.list.assert_called_once_with(callingData=True)

    def test_location_id_filter_passed(self):
        mock_api, _ = self._call(location_id="LID")
        mock_api.people.list.assert_called_once_with(locationId="LID")

    def test_max_results_passed(self):
        mock_api, _ = self._call(max_results=50)
        mock_api.people.list.assert_called_once_with(max=50)

    def test_no_filters_calls_list_with_no_args(self):
        mock_api, _ = self._call()
        mock_api.people.list.assert_called_once_with()

    def test_multiple_filters_combined(self):
        mock_api, _ = self._call(email="u@e.com", org_id="OID", max_results=10)
        mock_api.people.list.assert_called_once_with(email="u@e.com", orgId="OID", max=10)

    def test_person_dict_has_required_fields(self):
        mock_api = MagicMock()
        mock_api.people.list.return_value = [_fake_person()]
        with patch.object(_people_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_people()
        person = r['data']['people'][0]
        for field in ('id', 'emails', 'displayName', 'nickName',
                      'firstName', 'lastName', 'orgId', 'created', 'status', 'type'):
            self.assertIn(field, person)

    def test_filters_applied_in_metadata(self):
        mock_api, r = self._call(email="u@e.com")
        self.assertIn('filters_applied', r['metadata'])
        self.assertEqual(r['metadata']['filters_applied']['email'], 'u@e.com')

    def test_unauthorized_error(self):
        mock_api = MagicMock()
        mock_api.people.list.side_effect = Exception("unauthorized")
        with patch.object(_people_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_people()
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E401')

    def test_not_found_error(self):
        mock_api = MagicMock()
        mock_api.people.list.side_effect = Exception("not found")
        with patch.object(_people_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_people()
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E404')

    def test_rate_limit_error_is_temporary(self):
        mock_api = MagicMock()
        mock_api.people.list.side_effect = Exception("rate limit exceeded")
        with patch.object(_people_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_people()
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E503')
        self.assertTrue(r.get('temporary'))

    def test_has_timestamp(self):
        mock_api, r = self._call()
        self.assertIn('timestamp', r)


if __name__ == '__main__':
    unittest.main()

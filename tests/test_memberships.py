"""
Unit tests for Webex Membership management tools.

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

import webex_bot_mcp.tools.memberships as _memberships_mod  # noqa: E402
from webex_bot_mcp.tools.memberships import (                 # noqa: E402
    list_webex_memberships,
    add_webex_membership,
    update_webex_membership,
    delete_webex_membership,
    list_webex_space_memberships,
    add_webex_space_membership,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _fake_membership(**overrides):
    m = MagicMock()
    m.id = "MEMBERSHIPID"
    m.roomId = "ROOMID"
    m.personId = "PERSONID"
    m.personEmail = "user@example.com"
    m.personDisplayName = "Test User"
    m.personOrgId = "ORGID"
    m.isModerator = False
    m.isMonitor = False
    m.created = "2025-01-01T00:00:00Z"
    m.roomType = None  # optional
    for k, v in overrides.items():
        setattr(m, k, v)
    return m


# ── list_webex_memberships ────────────────────────────────────────────────────

class TestListWebexMemberships(unittest.TestCase):
    def _call(self, **kwargs):
        mock_api = MagicMock()
        mock_api.memberships.list.return_value = []
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            return mock_api, list_webex_memberships(**kwargs)

    def test_returns_memberships_list(self):
        mock_api = MagicMock()
        mock_api.memberships.list.return_value = [_fake_membership(), _fake_membership(id="MID2")]
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_memberships()
        self.assertTrue(r['success'])
        self.assertEqual(len(r['data']['memberships']), 2)

    def test_empty_list(self):
        mock_api, r = self._call()
        self.assertTrue(r['success'])
        self.assertEqual(r['data']['memberships'], [])

    def test_metadata_count_matches(self):
        mock_api = MagicMock()
        mock_api.memberships.list.return_value = [_fake_membership()]
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_memberships()
        self.assertEqual(r['metadata']['count'], 1)

    def test_room_id_filter_passed(self):
        mock_api, _ = self._call(room_id="ROOMID")
        mock_api.memberships.list.assert_called_once_with(roomId="ROOMID")

    def test_person_id_filter_passed(self):
        mock_api, _ = self._call(person_id="PID")
        mock_api.memberships.list.assert_called_once_with(personId="PID")

    def test_person_email_filter_passed(self):
        mock_api, _ = self._call(person_email="user@example.com")
        mock_api.memberships.list.assert_called_once_with(personEmail="user@example.com")

    def test_max_results_passed(self):
        mock_api, _ = self._call(max_results=25)
        mock_api.memberships.list.assert_called_once_with(max=25)

    def test_no_filters_calls_list_with_no_args(self):
        mock_api, _ = self._call()
        mock_api.memberships.list.assert_called_once_with()

    def test_membership_dict_has_required_fields(self):
        mock_api = MagicMock()
        mock_api.memberships.list.return_value = [_fake_membership()]
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_memberships()
        m = r['data']['memberships'][0]
        for field in ('id', 'roomId', 'personId', 'personEmail',
                      'personDisplayName', 'isModerator', 'isMonitor', 'created'):
            self.assertIn(field, m)

    def test_optional_room_type_included_when_set(self):
        mock_api = MagicMock()
        mock_api.memberships.list.return_value = [_fake_membership(roomType="group")]
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_memberships()
        self.assertEqual(r['data']['memberships'][0]['roomType'], "group")

    def test_room_type_absent_when_none(self):
        mock_api = MagicMock()
        mock_api.memberships.list.return_value = [_fake_membership()]
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_memberships()
        self.assertNotIn('roomType', r['data']['memberships'][0])

    def test_unauthorized_error(self):
        mock_api = MagicMock()
        mock_api.memberships.list.side_effect = Exception("unauthorized")
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_memberships()
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E401')

    def test_not_found_error(self):
        mock_api = MagicMock()
        mock_api.memberships.list.side_effect = Exception("not found")
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_memberships()
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E404')

    def test_rate_limit_error_is_temporary(self):
        mock_api = MagicMock()
        mock_api.memberships.list.side_effect = Exception("rate limit exceeded")
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_memberships()
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E503')
        self.assertTrue(r.get('temporary'))


# ── add_webex_membership ──────────────────────────────────────────────────────

class TestAddWebexMembership(unittest.TestCase):
    def _call(self, **kwargs):
        mock_api = MagicMock()
        mock_api.memberships.create.return_value = _fake_membership()
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            return mock_api, add_webex_membership(**kwargs)

    def test_missing_person_id_and_email_returns_error(self):
        _, r = self._call(room_id="ROOMID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_success_with_person_id(self):
        _, r = self._call(room_id="ROOMID", person_id="PID")
        self.assertTrue(r['success'])

    def test_success_with_person_email(self):
        _, r = self._call(room_id="ROOMID", person_email="user@example.com")
        self.assertTrue(r['success'])

    def test_person_id_passed_when_both_given(self):
        mock_api, _ = self._call(room_id="ROOMID", person_id="PID", person_email="u@e.com")
        call_kwargs = mock_api.memberships.create.call_args[1]
        self.assertIn('personId', call_kwargs)
        self.assertNotIn('personEmail', call_kwargs)

    def test_email_used_when_no_person_id(self):
        mock_api, _ = self._call(room_id="ROOMID", person_email="user@example.com")
        call_kwargs = mock_api.memberships.create.call_args[1]
        self.assertIn('personEmail', call_kwargs)
        self.assertNotIn('personId', call_kwargs)

    def test_is_moderator_passed(self):
        mock_api, _ = self._call(room_id="ROOMID", person_id="PID", is_moderator=True)
        call_kwargs = mock_api.memberships.create.call_args[1]
        self.assertTrue(call_kwargs['isModerator'])

    def test_room_id_always_passed(self):
        mock_api, _ = self._call(room_id="ROOMID", person_id="PID")
        call_kwargs = mock_api.memberships.create.call_args[1]
        self.assertEqual(call_kwargs['roomId'], "ROOMID")

    def test_returns_membership_in_data(self):
        _, r = self._call(room_id="ROOMID", person_id="PID")
        self.assertIn('membership', r['data'])

    def test_operation_in_metadata(self):
        _, r = self._call(room_id="ROOMID", person_id="PID")
        self.assertEqual(r['metadata']['operation'], 'add_membership')

    def test_forbidden_returns_error(self):
        mock_api = MagicMock()
        mock_api.memberships.create.side_effect = Exception("forbidden")
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = add_webex_membership(room_id="ROOMID", person_id="PID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E403')

    def test_has_timestamp(self):
        _, r = self._call(room_id="ROOMID", person_id="PID")
        self.assertIn('timestamp', r)


# ── update_webex_membership ───────────────────────────────────────────────────

class TestUpdateWebexMembership(unittest.TestCase):
    def _call(self, **kwargs):
        mock_api = MagicMock()
        mock_api.memberships.update.return_value = _fake_membership()
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            return mock_api, update_webex_membership(**kwargs)

    def test_no_fields_returns_error(self):
        _, r = self._call(membership_id="MID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_success_with_is_moderator(self):
        _, r = self._call(membership_id="MID", is_moderator=True)
        self.assertTrue(r['success'])

    def test_success_with_is_monitor(self):
        _, r = self._call(membership_id="MID", is_monitor=False)
        self.assertTrue(r['success'])

    def test_is_moderator_passed_to_sdk(self):
        mock_api, _ = self._call(membership_id="MID", is_moderator=True)
        call_kwargs = mock_api.memberships.update.call_args[1]
        self.assertTrue(call_kwargs['isModerator'])

    def test_is_monitor_passed_to_sdk(self):
        mock_api, _ = self._call(membership_id="MID", is_monitor=True)
        call_kwargs = mock_api.memberships.update.call_args[1]
        self.assertTrue(call_kwargs['isMonitor'])

    def test_membership_id_passed_to_sdk(self):
        mock_api, _ = self._call(membership_id="MID123", is_moderator=False)
        call_kwargs = mock_api.memberships.update.call_args[1]
        self.assertEqual(call_kwargs['membershipId'], "MID123")

    def test_operation_in_metadata(self):
        _, r = self._call(membership_id="MID", is_moderator=True)
        self.assertEqual(r['metadata']['operation'], 'update_membership')

    def test_returns_membership_in_data(self):
        _, r = self._call(membership_id="MID", is_moderator=False)
        self.assertIn('membership', r['data'])

    def test_not_found_returns_error(self):
        mock_api = MagicMock()
        mock_api.memberships.update.side_effect = Exception("not found")
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = update_webex_membership(membership_id="MID", is_moderator=True)
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E404')

    def test_forbidden_returns_error(self):
        mock_api = MagicMock()
        mock_api.memberships.update.side_effect = Exception("forbidden")
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = update_webex_membership(membership_id="MID", is_moderator=True)
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E403')


# ── delete_webex_membership ───────────────────────────────────────────────────

class TestDeleteWebexMembership(unittest.TestCase):
    def test_success_returns_deleted_true(self):
        mock_api = MagicMock()
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_membership(membership_id="MID")
        self.assertTrue(r['success'])
        self.assertTrue(r['data']['deleted'])

    def test_membership_id_in_response(self):
        mock_api = MagicMock()
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_membership(membership_id="MID")
        self.assertEqual(r['data']['membership_id'], "MID")

    def test_membership_id_passed_to_sdk(self):
        mock_api = MagicMock()
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            delete_webex_membership(membership_id="DELID")
        mock_api.memberships.delete.assert_called_once_with(membershipId="DELID")

    def test_empty_membership_id_returns_error(self):
        mock_api = MagicMock()
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_membership(membership_id="")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_not_found_returns_error(self):
        mock_api = MagicMock()
        mock_api.memberships.delete.side_effect = Exception("not found")
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_membership(membership_id="MID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E404')

    def test_unauthorized_returns_error(self):
        mock_api = MagicMock()
        mock_api.memberships.delete.side_effect = Exception("unauthorized")
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_membership(membership_id="MID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E401')

    def test_operation_in_metadata(self):
        mock_api = MagicMock()
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_membership(membership_id="MID")
        self.assertEqual(r['metadata']['operation'], 'delete_membership')

    def test_has_timestamp(self):
        mock_api = MagicMock()
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_membership(membership_id="MID")
        self.assertIn('timestamp', r)


# ── list_webex_space_memberships (alias) ──────────────────────────────────────

class TestListWebexSpaceMemberships(unittest.TestCase):
    def test_delegates_to_list_memberships(self):
        mock_api = MagicMock()
        mock_api.memberships.list.return_value = [_fake_membership()]
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_space_memberships(space_id="SID")
        mock_api.memberships.list.assert_called_once_with(roomId="SID")
        self.assertTrue(r['success'])

    def test_all_filters_forwarded(self):
        mock_api = MagicMock()
        mock_api.memberships.list.return_value = []
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            list_webex_space_memberships(
                space_id="SID", person_id="PID", person_email="u@e.com", max_results=10
            )
        mock_api.memberships.list.assert_called_once_with(
            roomId="SID", personId="PID", personEmail="u@e.com", max=10
        )

    def test_error_passthrough(self):
        mock_api = MagicMock()
        mock_api.memberships.list.side_effect = Exception("forbidden")
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_space_memberships(space_id="SID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E403')


# ── add_webex_space_membership (alias) ────────────────────────────────────────

class TestAddWebexSpaceMembership(unittest.TestCase):
    def test_delegates_to_add_membership(self):
        mock_api = MagicMock()
        mock_api.memberships.create.return_value = _fake_membership()
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            r = add_webex_space_membership(space_id="SID", person_id="PID")
        mock_api.memberships.create.assert_called_once_with(roomId="SID", personId="PID")
        self.assertTrue(r['success'])

    def test_validation_still_enforced(self):
        r = add_webex_space_membership(space_id="SID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_moderator_flag_forwarded(self):
        mock_api = MagicMock()
        mock_api.memberships.create.return_value = _fake_membership()
        with patch.object(_memberships_mod, 'get_webex_api', return_value=mock_api):
            add_webex_space_membership(space_id="SID", person_email="u@e.com", is_moderator=True)
        call_kwargs = mock_api.memberships.create.call_args[1]
        self.assertTrue(call_kwargs['isModerator'])


if __name__ == '__main__':
    unittest.main()

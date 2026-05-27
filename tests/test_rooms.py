"""
Unit tests for Webex Room/Space management tools.

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

import webex_bot_mcp.tools.rooms as _rooms_mod  # noqa: E402
from webex_bot_mcp.tools.rooms import (          # noqa: E402
    list_webex_rooms,
    create_webex_room,
    update_webex_room,
    get_webex_room,
    delete_webex_room,
    list_webex_spaces,
    create_webex_space,
    update_webex_space,
    get_webex_space,
    delete_webex_space,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _fake_room(**overrides):
    r = MagicMock()
    r.id = "ROOMID"
    r.title = "Test Room"
    r.type = "group"
    r.isLocked = False
    r.lastActivity = "2025-01-01T00:00:00Z"
    r.created = "2025-01-01T00:00:00Z"
    r.creatorId = "CREATORID"
    # Optional attributes must be None so getattr(..., None) returns None
    r.teamId = None
    r.sipAddress = None
    r.description = None
    r.isPublic = None
    r.isAnnouncementOnly = None
    r.ownerId = None
    r.classificationId = None
    for k, v in overrides.items():
        setattr(r, k, v)
    return r


# ── list_webex_rooms ──────────────────────────────────────────────────────────

class TestListWebexRooms(unittest.TestCase):
    def _call(self, **kwargs):
        mock_api = MagicMock()
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            return mock_api, list_webex_rooms(**kwargs)

    def test_returns_rooms_list(self):
        mock_api = MagicMock()
        mock_api.rooms.list.return_value = [_fake_room(), _fake_room(id="ROOMID2", title="Room 2")]
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_rooms()
        self.assertTrue(r['success'])
        self.assertEqual(len(r['data']['rooms']), 2)

    def test_empty_list(self):
        mock_api, r = self._call()
        mock_api.rooms.list.return_value = []
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_rooms()
        self.assertTrue(r['success'])
        self.assertEqual(r['data']['rooms'], [])

    def test_metadata_count_matches(self):
        mock_api = MagicMock()
        mock_api.rooms.list.return_value = [_fake_room(), _fake_room()]
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_rooms()
        self.assertEqual(r['metadata']['count'], 2)

    def test_team_id_filter_passed(self):
        mock_api = MagicMock()
        mock_api.rooms.list.return_value = []
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            list_webex_rooms(team_id="TEAMID")
        mock_api.rooms.list.assert_called_once_with(teamId="TEAMID")

    def test_room_type_filter_passed(self):
        mock_api = MagicMock()
        mock_api.rooms.list.return_value = []
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            list_webex_rooms(room_type="direct")
        mock_api.rooms.list.assert_called_once_with(type="direct")

    def test_sort_by_filter_passed(self):
        mock_api = MagicMock()
        mock_api.rooms.list.return_value = []
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            list_webex_rooms(sort_by="lastactivity")
        mock_api.rooms.list.assert_called_once_with(sortBy="lastactivity")

    def test_max_results_passed(self):
        mock_api = MagicMock()
        mock_api.rooms.list.return_value = []
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            list_webex_rooms(max_results=50)
        mock_api.rooms.list.assert_called_once_with(max=50)

    def test_no_filters_calls_list_with_no_args(self):
        mock_api = MagicMock()
        mock_api.rooms.list.return_value = []
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            list_webex_rooms()
        mock_api.rooms.list.assert_called_once_with()

    def test_room_dict_has_required_fields(self):
        mock_api = MagicMock()
        mock_api.rooms.list.return_value = [_fake_room()]
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_rooms()
        room = r['data']['rooms'][0]
        for field in ('id', 'title', 'type', 'isLocked', 'lastActivity', 'created', 'creatorId'):
            self.assertIn(field, room)

    def test_optional_team_id_included_when_set(self):
        mock_api = MagicMock()
        mock_api.rooms.list.return_value = [_fake_room(teamId="TEAMID123")]
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_rooms()
        self.assertEqual(r['data']['rooms'][0]['teamId'], "TEAMID123")

    def test_optional_fields_absent_when_none(self):
        mock_api = MagicMock()
        mock_api.rooms.list.return_value = [_fake_room()]
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_rooms()
        room = r['data']['rooms'][0]
        self.assertNotIn('teamId', room)
        self.assertNotIn('description', room)

    def test_unauthorized_error(self):
        mock_api = MagicMock()
        mock_api.rooms.list.side_effect = Exception("unauthorized")
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_rooms()
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E401')

    def test_not_found_error(self):
        mock_api = MagicMock()
        mock_api.rooms.list.side_effect = Exception("not found")
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_rooms()
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E404')

    def test_rate_limit_error_is_temporary(self):
        mock_api = MagicMock()
        mock_api.rooms.list.side_effect = Exception("rate limit exceeded")
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_rooms()
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E503')
        self.assertTrue(r.get('temporary'))

    def test_filters_applied_in_metadata(self):
        mock_api = MagicMock()
        mock_api.rooms.list.return_value = []
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_rooms(room_type="group")
        self.assertIn('filters_applied', r['metadata'])
        self.assertEqual(r['metadata']['filters_applied']['type'], 'group')


# ── create_webex_room ─────────────────────────────────────────────────────────

class TestCreateWebexRoom(unittest.TestCase):
    def _call(self, **kwargs):
        mock_api = MagicMock()
        mock_api.rooms.create.return_value = _fake_room()
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            return mock_api, create_webex_room(**kwargs)

    def test_success_returns_room(self):
        _, r = self._call(title="New Room")
        self.assertTrue(r['success'])
        self.assertIn('room', r['data'])

    def test_title_passed_to_sdk(self):
        mock_api, _ = self._call(title="My Room")
        call_kwargs = mock_api.rooms.create.call_args[1]
        self.assertEqual(call_kwargs['title'], "My Room")

    def test_is_locked_and_is_moderated_conflict_returns_error(self):
        _, r = self._call(title="R", is_locked=True, is_moderated=True)
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_is_moderated_used_when_is_locked_absent(self):
        mock_api, r = self._call(title="R", is_moderated=True)
        self.assertTrue(r['success'])
        call_kwargs = mock_api.rooms.create.call_args[1]
        self.assertTrue(call_kwargs['isLocked'])

    def test_is_locked_used_when_is_moderated_absent(self):
        mock_api, r = self._call(title="R", is_locked=False)
        self.assertTrue(r['success'])
        call_kwargs = mock_api.rooms.create.call_args[1]
        self.assertFalse(call_kwargs['isLocked'])

    def test_team_id_passed(self):
        mock_api, _ = self._call(title="R", team_id="TID")
        call_kwargs = mock_api.rooms.create.call_args[1]
        self.assertEqual(call_kwargs['teamId'], "TID")

    def test_description_passed(self):
        mock_api, _ = self._call(title="R", description="A room")
        call_kwargs = mock_api.rooms.create.call_args[1]
        self.assertEqual(call_kwargs['description'], "A room")

    def test_is_public_passed(self):
        mock_api, _ = self._call(title="R", is_public=True)
        call_kwargs = mock_api.rooms.create.call_args[1]
        self.assertTrue(call_kwargs['isPublic'])

    def test_is_announcement_only_passed(self):
        mock_api, _ = self._call(title="R", is_announcement_only=True)
        call_kwargs = mock_api.rooms.create.call_args[1]
        self.assertTrue(call_kwargs['isAnnouncementOnly'])

    def test_classification_id_passed(self):
        mock_api, _ = self._call(title="R", classification_id="CID")
        call_kwargs = mock_api.rooms.create.call_args[1]
        self.assertEqual(call_kwargs['classificationId'], "CID")

    def test_operation_in_metadata(self):
        _, r = self._call(title="R")
        self.assertEqual(r['metadata']['operation'], 'create_room')

    def test_sdk_exception_returns_error(self):
        mock_api = MagicMock()
        mock_api.rooms.create.side_effect = Exception("forbidden")
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = create_webex_room(title="R")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E403')

    def test_has_timestamp(self):
        _, r = self._call(title="R")
        self.assertIn('timestamp', r)


# ── update_webex_room ─────────────────────────────────────────────────────────

class TestUpdateWebexRoom(unittest.TestCase):
    def _call(self, **kwargs):
        mock_api = MagicMock()
        mock_api.rooms.update.return_value = _fake_room()
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            return mock_api, update_webex_room(**kwargs)

    def test_success_returns_room(self):
        _, r = self._call(room_id="RID", title="New Title")
        self.assertTrue(r['success'])
        self.assertIn('room', r['data'])

    def test_no_fields_returns_error(self):
        _, r = self._call(room_id="RID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_is_locked_and_is_moderated_conflict_returns_error(self):
        _, r = self._call(room_id="RID", is_locked=True, is_moderated=False)
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_title_passed_to_sdk(self):
        mock_api, _ = self._call(room_id="RID", title="Updated")
        call_kwargs = mock_api.rooms.update.call_args[1]
        self.assertEqual(call_kwargs['title'], "Updated")

    def test_room_id_passed_to_sdk(self):
        mock_api, _ = self._call(room_id="RID123", title="T")
        call_kwargs = mock_api.rooms.update.call_args[1]
        self.assertEqual(call_kwargs['roomId'], "RID123")

    def test_description_passed(self):
        mock_api, _ = self._call(room_id="RID", description="New desc")
        call_kwargs = mock_api.rooms.update.call_args[1]
        self.assertEqual(call_kwargs['description'], "New desc")

    def test_is_public_passed(self):
        mock_api, _ = self._call(room_id="RID", is_public=False)
        call_kwargs = mock_api.rooms.update.call_args[1]
        self.assertFalse(call_kwargs['isPublic'])

    def test_operation_in_metadata(self):
        _, r = self._call(room_id="RID", title="T")
        self.assertEqual(r['metadata']['operation'], 'update_room')

    def test_not_found_returns_error(self):
        mock_api = MagicMock()
        mock_api.rooms.update.side_effect = Exception("not found")
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = update_webex_room(room_id="RID", title="T")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E404')

    def test_is_moderated_maps_to_is_locked(self):
        mock_api, _ = self._call(room_id="RID", is_moderated=True)
        call_kwargs = mock_api.rooms.update.call_args[1]
        self.assertTrue(call_kwargs['isLocked'])


# ── get_webex_room ────────────────────────────────────────────────────────────

class TestGetWebexRoom(unittest.TestCase):
    def test_success_returns_room(self):
        mock_api = MagicMock()
        mock_api.rooms.get.return_value = _fake_room()
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_room(room_id="ROOMID")
        self.assertTrue(r['success'])
        self.assertIn('room', r['data'])

    def test_room_id_passed_to_sdk(self):
        mock_api = MagicMock()
        mock_api.rooms.get.return_value = _fake_room()
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            get_webex_room(room_id="RID123")
        mock_api.rooms.get.assert_called_once_with(roomId="RID123")

    def test_metadata_has_room_id(self):
        mock_api = MagicMock()
        mock_api.rooms.get.return_value = _fake_room()
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_room(room_id="ROOMID")
        self.assertEqual(r['metadata']['room_id'], "ROOMID")

    def test_not_found_returns_error(self):
        mock_api = MagicMock()
        mock_api.rooms.get.side_effect = Exception("404 not found")
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_room(room_id="MISSING")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E404')

    def test_unauthorized_returns_error(self):
        mock_api = MagicMock()
        mock_api.rooms.get.side_effect = Exception("unauthorized")
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_room(room_id="ROOMID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E401')


# ── delete_webex_room ─────────────────────────────────────────────────────────

class TestDeleteWebexRoom(unittest.TestCase):
    def test_success_returns_deleted_true(self):
        mock_api = MagicMock()
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_room(room_id="ROOMID")
        self.assertTrue(r['success'])
        self.assertTrue(r['data']['deleted'])

    def test_room_id_in_response(self):
        mock_api = MagicMock()
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_room(room_id="ROOMID")
        self.assertEqual(r['data']['room_id'], "ROOMID")

    def test_room_id_passed_to_sdk(self):
        mock_api = MagicMock()
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            delete_webex_room(room_id="DELID")
        mock_api.rooms.delete.assert_called_once_with(roomId="DELID")

    def test_empty_room_id_returns_error(self):
        mock_api = MagicMock()
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_room(room_id="")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_not_found_returns_error(self):
        mock_api = MagicMock()
        mock_api.rooms.delete.side_effect = Exception("not found")
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_room(room_id="ROOMID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E404')

    def test_unauthorized_returns_error(self):
        mock_api = MagicMock()
        mock_api.rooms.delete.side_effect = Exception("unauthorized")
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_room(room_id="ROOMID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E401')

    def test_operation_in_metadata(self):
        mock_api = MagicMock()
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_room(room_id="ROOMID")
        self.assertEqual(r['metadata']['operation'], 'delete_room')


# ── list_webex_spaces (alias) ─────────────────────────────────────────────────

class TestListWebexSpaces(unittest.TestCase):
    def test_returns_spaces_key_not_rooms(self):
        mock_api = MagicMock()
        mock_api.rooms.list.return_value = [_fake_room()]
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_spaces()
        self.assertTrue(r['success'])
        self.assertIn('spaces', r['data'])
        self.assertNotIn('rooms', r['data'])

    def test_delegates_space_type_as_room_type(self):
        mock_api = MagicMock()
        mock_api.rooms.list.return_value = []
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            list_webex_spaces(space_type="group")
        mock_api.rooms.list.assert_called_once_with(type="group")

    def test_error_passthrough(self):
        mock_api = MagicMock()
        mock_api.rooms.list.side_effect = Exception("unauthorized")
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_spaces()
        self.assertFalse(r['success'])


# ── create_webex_space (alias) ────────────────────────────────────────────────

class TestCreateWebexSpace(unittest.TestCase):
    def test_returns_space_key_not_room(self):
        mock_api = MagicMock()
        mock_api.rooms.create.return_value = _fake_room()
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = create_webex_space(title="My Space")
        self.assertTrue(r['success'])
        self.assertIn('space', r['data'])
        self.assertNotIn('room', r['data'])

    def test_error_passthrough(self):
        mock_api = MagicMock()
        mock_api.rooms.create.side_effect = Exception("forbidden")
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = create_webex_space(title="S")
        self.assertFalse(r['success'])

    def test_conflict_validation_still_works(self):
        r = create_webex_space(title="S", is_locked=True, is_moderated=True)
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')


# ── update_webex_space (alias) ────────────────────────────────────────────────

class TestUpdateWebexSpace(unittest.TestCase):
    def test_returns_space_key_not_room(self):
        mock_api = MagicMock()
        mock_api.rooms.update.return_value = _fake_room()
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = update_webex_space(space_id="SID", title="New Title")
        self.assertTrue(r['success'])
        self.assertIn('space', r['data'])
        self.assertNotIn('room', r['data'])

    def test_no_fields_error_propagated(self):
        r = update_webex_space(space_id="SID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')


# ── get_webex_space (alias) ───────────────────────────────────────────────────

class TestGetWebexSpace(unittest.TestCase):
    def test_returns_space_key_not_room(self):
        mock_api = MagicMock()
        mock_api.rooms.get.return_value = _fake_room()
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_space(space_id="SID")
        self.assertTrue(r['success'])
        self.assertIn('space', r['data'])
        self.assertNotIn('room', r['data'])

    def test_space_id_passed_to_sdk(self):
        mock_api = MagicMock()
        mock_api.rooms.get.return_value = _fake_room()
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            get_webex_space(space_id="SID123")
        mock_api.rooms.get.assert_called_once_with(roomId="SID123")


# ── delete_webex_space (alias) ────────────────────────────────────────────────

class TestDeleteWebexSpace(unittest.TestCase):
    def test_delegates_to_delete_room(self):
        mock_api = MagicMock()
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_space(space_id="SID")
        self.assertTrue(r['success'])
        mock_api.rooms.delete.assert_called_once_with(roomId="SID")

    def test_empty_space_id_returns_error(self):
        mock_api = MagicMock()
        with patch.object(_rooms_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_space(space_id="")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')


if __name__ == '__main__':
    unittest.main()

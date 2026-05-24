"""
Unit tests for Webex Teams management tools.

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

import webex_bot_mcp.tools.teams as _teams_mod  # noqa: E402
from webex_bot_mcp.tools.teams import (          # noqa: E402
    list_webex_teams,
    create_webex_team,
    get_webex_team,
    update_webex_team,
    delete_webex_team,
    list_webex_team_memberships,
    add_webex_team_membership,
    delete_webex_team_membership,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _fake_team(**overrides):
    t = MagicMock()
    t.id = "TEAMID"
    t.name = "Test Team"
    t.description = "A test team"
    t.creatorId = "CREATORID"
    t.created = "2025-01-01T00:00:00Z"
    for k, v in overrides.items():
        setattr(t, k, v)
    return t


def _fake_team_membership(**overrides):
    m = MagicMock()
    m.id = "MEMBERSHIPID"
    m.teamId = "TEAMID"
    m.personId = "PERSONID"
    m.personEmail = "user@example.com"
    m.personDisplayName = "Test User"
    m.personOrgId = "ORGID"
    m.isModerator = False
    m.created = "2025-01-01T00:00:00Z"
    for k, v in overrides.items():
        setattr(m, k, v)
    return m


# ── list_webex_teams ──────────────────────────────────────────────────────────

class TestListWebexTeams(unittest.TestCase):
    def _call(self, **kwargs):
        mock_api = MagicMock()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            return mock_api, list_webex_teams(**kwargs)

    def test_returns_teams_list(self):
        mock_api = MagicMock()
        mock_api.teams.list.return_value = [_fake_team(), _fake_team(id="TEAMID2", name="Team 2")]
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_teams()
        self.assertTrue(r['success'])
        self.assertEqual(len(r['data']['teams']), 2)

    def test_metadata_count_matches(self):
        mock_api = MagicMock()
        mock_api.teams.list.return_value = [_fake_team()]
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_teams()
        self.assertEqual(r['metadata']['count'], 1)

    def test_display_name_filter_passed(self):
        mock_api = MagicMock()
        mock_api.teams.list.return_value = []
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            list_webex_teams(display_name="My Team")
        mock_api.teams.list.assert_called_once_with(displayName="My Team")

    def test_max_results_passed(self):
        mock_api = MagicMock()
        mock_api.teams.list.return_value = []
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            list_webex_teams(max_results=10)
        mock_api.teams.list.assert_called_once_with(max=10)

    def test_no_filters_calls_list_with_no_args(self):
        mock_api = MagicMock()
        mock_api.teams.list.return_value = []
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            list_webex_teams()
        mock_api.teams.list.assert_called_once_with()

    def test_team_dict_has_expected_keys(self):
        mock_api = MagicMock()
        mock_api.teams.list.return_value = [_fake_team()]
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_teams()
        team = r['data']['teams'][0]
        for key in ('id', 'name', 'creatorId', 'created'):
            self.assertIn(key, team)

    def test_error_propagated_as_structured_response(self):
        mock_api = MagicMock()
        mock_api.teams.list.side_effect = Exception("network error")
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_teams()
        self.assertFalse(r['success'])
        self.assertIn('error_code', r)

    def test_has_timestamp(self):
        mock_api = MagicMock()
        mock_api.teams.list.return_value = []
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_teams()
        self.assertIn('timestamp', r)
        self.assertNotEqual(r['timestamp'], '')


# ── create_webex_team ─────────────────────────────────────────────────────────

class TestCreateWebexTeam(unittest.TestCase):
    def test_creates_team_with_name(self):
        mock_api = MagicMock()
        mock_api.teams.create.return_value = _fake_team()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = create_webex_team(name="My Team")
        self.assertTrue(r['success'])
        mock_api.teams.create.assert_called_once_with(name="My Team")

    def test_creates_team_with_description(self):
        mock_api = MagicMock()
        mock_api.teams.create.return_value = _fake_team()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = create_webex_team(name="My Team", description="A description")
        self.assertTrue(r['success'])
        call_kwargs = mock_api.teams.create.call_args[1]
        self.assertEqual(call_kwargs['description'], "A description")

    def test_returns_team_in_data(self):
        mock_api = MagicMock()
        mock_api.teams.create.return_value = _fake_team(name="Created Team")
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = create_webex_team(name="Created Team")
        self.assertIn('team', r['data'])
        self.assertEqual(r['data']['team']['name'], "Created Team")

    def test_api_error_returns_structured_error(self):
        mock_api = MagicMock()
        mock_api.teams.create.side_effect = Exception("unauthorized")
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = create_webex_team(name="Fail")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E401')


# ── get_webex_team ────────────────────────────────────────────────────────────

class TestGetWebexTeam(unittest.TestCase):
    def test_returns_team_details(self):
        mock_api = MagicMock()
        mock_api.teams.get.return_value = _fake_team()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_team("TEAMID")
        self.assertTrue(r['success'])
        self.assertEqual(r['data']['team']['id'], "TEAMID")

    def test_passes_team_id_to_api(self):
        mock_api = MagicMock()
        mock_api.teams.get.return_value = _fake_team()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            get_webex_team("TEAMID")
        mock_api.teams.get.assert_called_once_with(teamId="TEAMID")

    def test_not_found_returns_e404(self):
        mock_api = MagicMock()
        mock_api.teams.get.side_effect = Exception("404 not found")
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_team("BADID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E404')

    def test_metadata_contains_team_id(self):
        mock_api = MagicMock()
        mock_api.teams.get.return_value = _fake_team()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = get_webex_team("TEAMID")
        self.assertEqual(r['metadata']['team_id'], "TEAMID")


# ── update_webex_team ─────────────────────────────────────────────────────────

class TestUpdateWebexTeam(unittest.TestCase):
    def test_no_fields_returns_e001(self):
        mock_api = MagicMock()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = update_webex_team("TEAMID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_update_name(self):
        mock_api = MagicMock()
        mock_api.teams.update.return_value = _fake_team(name="New Name")
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = update_webex_team("TEAMID", name="New Name")
        self.assertTrue(r['success'])
        self.assertEqual(r['data']['team']['name'], "New Name")

    def test_update_name_passed_to_api(self):
        mock_api = MagicMock()
        mock_api.teams.update.return_value = _fake_team()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            update_webex_team("TEAMID", name="Updated")
        call_kwargs = mock_api.teams.update.call_args[1]
        self.assertEqual(call_kwargs['name'], "Updated")
        self.assertEqual(call_kwargs['teamId'], "TEAMID")

    def test_update_description_only_fetches_current_name(self):
        mock_api = MagicMock()
        mock_api.teams.get.return_value = _fake_team(name="Existing Name")
        mock_api.teams.update.return_value = _fake_team(name="Existing Name")
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = update_webex_team("TEAMID", description="New Desc")
        self.assertTrue(r['success'])
        mock_api.teams.get.assert_called_once_with(teamId="TEAMID")
        call_kwargs = mock_api.teams.update.call_args[1]
        self.assertEqual(call_kwargs['name'], "Existing Name")
        self.assertEqual(call_kwargs['description'], "New Desc")

    def test_update_both_name_and_description(self):
        mock_api = MagicMock()
        mock_api.teams.update.return_value = _fake_team()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            update_webex_team("TEAMID", name="N", description="D")
        call_kwargs = mock_api.teams.update.call_args[1]
        self.assertEqual(call_kwargs['name'], "N")
        self.assertEqual(call_kwargs['description'], "D")

    def test_api_error_returns_structured_error(self):
        mock_api = MagicMock()
        mock_api.teams.update.side_effect = Exception("forbidden")
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = update_webex_team("TEAMID", name="X")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E403')


# ── delete_webex_team ─────────────────────────────────────────────────────────

class TestDeleteWebexTeam(unittest.TestCase):
    def test_deletes_team(self):
        mock_api = MagicMock()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_team("TEAMID")
        self.assertTrue(r['success'])
        self.assertTrue(r['data']['deleted'])
        self.assertEqual(r['data']['team_id'], "TEAMID")

    def test_passes_team_id_to_api(self):
        mock_api = MagicMock()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            delete_webex_team("TEAMID")
        mock_api.teams.delete.assert_called_once_with(teamId="TEAMID")

    def test_not_found_returns_e404(self):
        mock_api = MagicMock()
        mock_api.teams.delete.side_effect = Exception("not found")
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_team("BADID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E404')

    def test_rate_limited_returns_e503(self):
        mock_api = MagicMock()
        mock_api.teams.delete.side_effect = Exception("rate limit exceeded")
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_team("TEAMID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E503')


# ── list_webex_team_memberships ───────────────────────────────────────────────

class TestListWebexTeamMemberships(unittest.TestCase):
    def test_returns_memberships(self):
        mock_api = MagicMock()
        mock_api.team_memberships.list.return_value = [_fake_team_membership()]
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_team_memberships("TEAMID")
        self.assertTrue(r['success'])
        self.assertEqual(len(r['data']['memberships']), 1)

    def test_team_id_passed_to_api(self):
        mock_api = MagicMock()
        mock_api.team_memberships.list.return_value = []
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            list_webex_team_memberships("TEAMID")
        mock_api.team_memberships.list.assert_called_once_with(teamId="TEAMID")

    def test_max_results_passed(self):
        mock_api = MagicMock()
        mock_api.team_memberships.list.return_value = []
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            list_webex_team_memberships("TEAMID", max_results=50)
        mock_api.team_memberships.list.assert_called_once_with(teamId="TEAMID", max=50)

    def test_metadata_has_count_and_team_id(self):
        mock_api = MagicMock()
        mock_api.team_memberships.list.return_value = [_fake_team_membership()]
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_team_memberships("TEAMID")
        self.assertEqual(r['metadata']['count'], 1)
        self.assertEqual(r['metadata']['team_id'], "TEAMID")

    def test_membership_dict_has_expected_keys(self):
        mock_api = MagicMock()
        mock_api.team_memberships.list.return_value = [_fake_team_membership()]
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_team_memberships("TEAMID")
        m = r['data']['memberships'][0]
        for key in ('id', 'teamId', 'personId', 'personEmail', 'isModerator', 'created'):
            self.assertIn(key, m)

    def test_api_error_returns_structured_error(self):
        mock_api = MagicMock()
        mock_api.team_memberships.list.side_effect = Exception("not found")
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = list_webex_team_memberships("BADTEAM")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E404')


# ── add_webex_team_membership ─────────────────────────────────────────────────

class TestAddWebexTeamMembership(unittest.TestCase):
    def test_missing_person_returns_e001(self):
        mock_api = MagicMock()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = add_webex_team_membership("TEAMID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E001')

    def test_add_by_person_id(self):
        mock_api = MagicMock()
        mock_api.team_memberships.create.return_value = _fake_team_membership()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = add_webex_team_membership("TEAMID", person_id="PERSONID")
        self.assertTrue(r['success'])
        call_kwargs = mock_api.team_memberships.create.call_args[1]
        self.assertEqual(call_kwargs['personId'], "PERSONID")
        self.assertEqual(call_kwargs['teamId'], "TEAMID")

    def test_add_by_person_email(self):
        mock_api = MagicMock()
        mock_api.team_memberships.create.return_value = _fake_team_membership()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = add_webex_team_membership("TEAMID", person_email="user@example.com")
        self.assertTrue(r['success'])
        call_kwargs = mock_api.team_memberships.create.call_args[1]
        self.assertEqual(call_kwargs['personEmail'], "user@example.com")

    def test_person_id_takes_precedence_over_email(self):
        mock_api = MagicMock()
        mock_api.team_memberships.create.return_value = _fake_team_membership()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            add_webex_team_membership("TEAMID", person_id="PID", person_email="user@example.com")
        call_kwargs = mock_api.team_memberships.create.call_args[1]
        self.assertIn('personId', call_kwargs)
        self.assertNotIn('personEmail', call_kwargs)

    def test_is_moderator_flag_passed(self):
        mock_api = MagicMock()
        mock_api.team_memberships.create.return_value = _fake_team_membership(isModerator=True)
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            add_webex_team_membership("TEAMID", person_id="PID", is_moderator=True)
        call_kwargs = mock_api.team_memberships.create.call_args[1]
        self.assertTrue(call_kwargs['isModerator'])

    def test_returns_membership_in_data(self):
        mock_api = MagicMock()
        mock_api.team_memberships.create.return_value = _fake_team_membership()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = add_webex_team_membership("TEAMID", person_email="u@example.com")
        self.assertIn('membership', r['data'])

    def test_api_error_returns_structured_error(self):
        mock_api = MagicMock()
        mock_api.team_memberships.create.side_effect = Exception("403 forbidden")
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = add_webex_team_membership("TEAMID", person_id="PID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E403')


# ── delete_webex_team_membership ──────────────────────────────────────────────

class TestDeleteWebexTeamMembership(unittest.TestCase):
    def test_deletes_membership(self):
        mock_api = MagicMock()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_team_membership("MEMBERSHIPID")
        self.assertTrue(r['success'])
        self.assertTrue(r['data']['deleted'])
        self.assertEqual(r['data']['membership_id'], "MEMBERSHIPID")

    def test_passes_membership_id_to_api(self):
        mock_api = MagicMock()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            delete_webex_team_membership("MEMBERSHIPID")
        mock_api.team_memberships.delete.assert_called_once_with(membershipId="MEMBERSHIPID")

    def test_not_found_returns_e404(self):
        mock_api = MagicMock()
        mock_api.team_memberships.delete.side_effect = Exception("404 not found")
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_team_membership("BADID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E404')

    def test_network_error_returns_e601(self):
        mock_api = MagicMock()
        mock_api.team_memberships.delete.side_effect = Exception("connection refused")
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_team_membership("MEMBERSHIPID")
        self.assertFalse(r['success'])
        self.assertEqual(r['error_code'], 'E601')

    def test_has_timestamp(self):
        mock_api = MagicMock()
        with patch.object(_teams_mod, 'get_webex_api', return_value=mock_api):
            r = delete_webex_team_membership("MEMBERSHIPID")
        self.assertIn('timestamp', r)
        self.assertNotEqual(r['timestamp'], '')


if __name__ == '__main__':
    unittest.main()

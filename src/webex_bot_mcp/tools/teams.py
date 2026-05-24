"""
Webex Teams management tools.
"""
from typing import Optional, Dict, Any
from .common import get_webex_api, create_error_response, create_success_response, WebexErrorCodes, WebexTokenMissingError


def _map_exception_to_error(e: Exception) -> Dict[str, Any]:
    if isinstance(e, WebexTokenMissingError):
        return create_error_response(WebexErrorCodes.UNAUTHORIZED, str(e))
    error_str = str(e).lower()
    if 'unauthorized' in error_str or 'invalid token' in error_str:
        return create_error_response(WebexErrorCodes.UNAUTHORIZED,
                                     "Invalid or expired bot token.")
    if 'not found' in error_str or '404' in error_str:
        return create_error_response(WebexErrorCodes.NOT_FOUND,
                                     "Team or membership not found.")
    if 'forbidden' in error_str or '403' in error_str:
        return create_error_response(WebexErrorCodes.FORBIDDEN,
                                     "Bot lacks permission for this operation. "
                                     "Ensure the bot has moderator privileges.")
    if 'rate limit' in error_str or 'too many requests' in error_str:
        return create_error_response(WebexErrorCodes.RATE_LIMITED,
                                     "API rate limit exceeded. Please retry after delay.",
                                     temporary=True, retry_after_seconds=60)
    if 'network' in error_str or 'connection' in error_str:
        return create_error_response(WebexErrorCodes.NETWORK_ERROR,
                                     "Network connectivity issue. Please retry.",
                                     temporary=True, retry_after_seconds=30)
    return create_error_response(WebexErrorCodes.WEBEX_API_ERROR,
                                 f"Webex API error: {e}",
                                 temporary=True, details={'original_error': str(e)})


def _team_to_dict(t) -> Dict[str, Any]:
    d: Dict[str, Any] = {
        'id': t.id,
        'name': t.name,
        'creatorId': t.creatorId,
        'created': t.created,
    }
    if getattr(t, 'description', None):
        d['description'] = t.description
    return d


def _team_membership_to_dict(m) -> Dict[str, Any]:
    d: Dict[str, Any] = {
        'id': m.id,
        'teamId': m.teamId,
        'personId': m.personId,
        'personEmail': m.personEmail,
        'personDisplayName': m.personDisplayName,
        'personOrgId': m.personOrgId,
        'isModerator': m.isModerator,
        'created': m.created,
    }
    return d


def list_webex_teams(
    display_name: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    """
    List Webex teams the authenticated bot belongs to.

    Args:
        display_name: Filter teams by display name (optional)
        max_results: Maximum number of teams to return (default 100, max 1000)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        params: Dict[str, Any] = {}
        if display_name:
            params['displayName'] = display_name
        if max_results:
            params['max'] = max_results

        teams = [_team_to_dict(t) for t in get_webex_api().teams.list(**params)]
        return create_success_response(
            data={'teams': teams},
            metadata={'count': len(teams), 'filters_applied': params}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def create_webex_team(
    name: str,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new Webex team.

    Args:
        name: Name of the team (required)
        description: Description of the team (optional)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        params: Dict[str, Any] = {'name': name}
        if description:
            params['description'] = description

        team = get_webex_api().teams.create(**params)
        return create_success_response(
            data={'team': _team_to_dict(team)},
            metadata={'operation': 'create_team', 'parameters_used': params}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def get_webex_team(team_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific Webex team.

    Args:
        team_id: Team ID to get details for (required)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        team = get_webex_api().teams.get(teamId=team_id)
        return create_success_response(
            data={'team': _team_to_dict(team)},
            metadata={'team_id': team_id}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def update_webex_team(
    team_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing Webex team's name and/or description.

    Args:
        team_id: Team ID to update (required)
        name: New name for the team (optional)
        description: New description for the team (optional)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        if name is None and description is None:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="Must specify at least one field to update (name or description)"
            )

        # The SDK requires name; fetch current value if not provided.
        if name is None:
            current = get_webex_api().teams.get(teamId=team_id)
            name = current.name

        params: Dict[str, Any] = {'name': name}
        if description is not None:
            params['description'] = description

        team = get_webex_api().teams.update(teamId=team_id, **params)
        return create_success_response(
            data={'team': _team_to_dict(team)},
            metadata={'operation': 'update_team', 'team_id': team_id,
                      'parameters_used': params}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def delete_webex_team(team_id: str) -> Dict[str, Any]:
    """
    Delete a Webex team.

    Args:
        team_id: Team ID to delete (required)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        if not team_id:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="team_id is required"
            )
        get_webex_api().teams.delete(teamId=team_id)
        return create_success_response(
            data={'deleted': True, 'team_id': team_id},
            metadata={'operation': 'delete_team'}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def list_webex_team_memberships(
    team_id: str,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    """
    List members of a Webex team.

    Args:
        team_id: Team ID to list members for (required)
        max_results: Maximum number of memberships to return (default 100, max 1000)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        params: Dict[str, Any] = {'teamId': team_id}
        if max_results:
            params['max'] = max_results

        memberships = [_team_membership_to_dict(m) for m in get_webex_api().team_memberships.list(**params)]
        return create_success_response(
            data={'memberships': memberships},
            metadata={'count': len(memberships), 'team_id': team_id}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def add_webex_team_membership(
    team_id: str,
    person_id: Optional[str] = None,
    person_email: Optional[str] = None,
    is_moderator: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Add a person to a Webex team.

    Args:
        team_id: Team ID to add person to (required)
        person_id: Person ID to add (use this OR person_email)
        person_email: Person email to add (use this OR person_id)
        is_moderator: Whether to make the person a team moderator (optional)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        if not (person_id or person_email):
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="Must specify either person_id or person_email",
                details={"required_one_of": ["person_id", "person_email"]}
            )

        params: Dict[str, Any] = {'teamId': team_id}
        if person_id:
            params['personId'] = person_id
        elif person_email:
            params['personEmail'] = person_email
        if is_moderator is not None:
            params['isModerator'] = is_moderator

        membership = get_webex_api().team_memberships.create(**params)
        return create_success_response(
            data={'membership': _team_membership_to_dict(membership)},
            metadata={'operation': 'add_team_membership', 'parameters_used': params}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def delete_webex_team_membership(membership_id: str) -> Dict[str, Any]:
    """
    Remove a person from a Webex team by deleting their team membership.

    Args:
        membership_id: Team membership ID to delete (required). Use
                       list_webex_team_memberships to find the membership ID.

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        if not membership_id:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="membership_id is required"
            )
        get_webex_api().team_memberships.delete(membershipId=membership_id)
        return create_success_response(
            data={'deleted': True, 'membership_id': membership_id},
            metadata={'operation': 'delete_team_membership'}
        )
    except Exception as e:
        return _map_exception_to_error(e)

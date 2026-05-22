"""
Webex Membership management tools.
"""
from typing import Optional, Dict, Any
from .common import webex_api, create_error_response, create_success_response, WebexErrorCodes


def _map_exception_to_error(e: Exception) -> Dict[str, Any]:
    error_str = str(e).lower()
    if 'unauthorized' in error_str or 'invalid token' in error_str:
        return create_error_response(WebexErrorCodes.UNAUTHORIZED,
                                     "Invalid or expired bot token.")
    if 'not found' in error_str or '404' in error_str:
        return create_error_response(WebexErrorCodes.NOT_FOUND,
                                     "Membership, room, or person not found.")
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


def _membership_to_dict(m) -> Dict[str, Any]:
    d: Dict[str, Any] = {
        'id': m.id,
        'roomId': m.roomId,
        'personId': m.personId,
        'personEmail': m.personEmail,
        'personDisplayName': m.personDisplayName,
        'personOrgId': m.personOrgId,
        'isModerator': m.isModerator,
        'isMonitor': m.isMonitor,
        'created': m.created,
    }
    if getattr(m, 'roomType', None):
        d['roomType'] = m.roomType
    return d


def list_webex_memberships(
    room_id: Optional[str] = None,
    person_id: Optional[str] = None,
    person_email: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    """
    List memberships for a room or person.

    Args:
        room_id: Room ID to get memberships for
        person_id: Person ID to get memberships for
        person_email: Person email to get memberships for
        max_results: Maximum number of memberships to return (default 100, max 1000)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        params: Dict[str, Any] = {}
        if room_id:
            params['roomId'] = room_id
        if person_id:
            params['personId'] = person_id
        if person_email:
            params['personEmail'] = person_email
        if max_results:
            params['max'] = max_results

        memberships = [_membership_to_dict(m) for m in webex_api.memberships.list(**params)]
        return create_success_response(
            data={'memberships': memberships},
            metadata={'count': len(memberships), 'filters_applied': params}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def add_webex_membership(
    room_id: str,
    person_id: Optional[str] = None,
    person_email: Optional[str] = None,
    is_moderator: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Add a person to a Webex room.

    Args:
        room_id: Room ID to add person to (required)
        person_id: Person ID to add (use this OR person_email)
        person_email: Person email to add (use this OR person_id)
        is_moderator: Whether to make the person a moderator (optional)

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

        params: Dict[str, Any] = {'roomId': room_id}
        if person_id:
            params['personId'] = person_id
        elif person_email:
            params['personEmail'] = person_email
        if is_moderator is not None:
            params['isModerator'] = is_moderator

        membership = webex_api.memberships.create(**params)
        return create_success_response(
            data={'membership': _membership_to_dict(membership)},
            metadata={'operation': 'add_membership', 'parameters_used': params}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def update_webex_membership(
    membership_id: str,
    is_moderator: Optional[bool] = None,
    is_monitor: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Update an existing Webex membership (change moderator/monitor status).

    Args:
        membership_id: Membership ID to update (required)
        is_moderator: Whether the person should be a moderator (optional)
        is_monitor: Whether the person should be a monitor (optional)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        params: Dict[str, Any] = {}
        if is_moderator is not None:
            params['isModerator'] = is_moderator
        if is_monitor is not None:
            params['isMonitor'] = is_monitor

        if not params:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="Must specify at least one field to update (is_moderator or is_monitor)"
            )

        membership = webex_api.memberships.update(membershipId=membership_id, **params)
        return create_success_response(
            data={'membership': _membership_to_dict(membership)},
            metadata={'operation': 'update_membership', 'membership_id': membership_id,
                      'parameters_used': params}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def delete_webex_membership(membership_id: str) -> Dict[str, Any]:
    """
    Remove a person from a Webex room by deleting their membership.

    Args:
        membership_id: Membership ID to delete (required). Use list_webex_memberships
                       to find the membership ID for a person in a room.

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        if not membership_id:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="membership_id is required"
            )
        webex_api.memberships.delete(membershipId=membership_id)
        return create_success_response(
            data={'deleted': True, 'membership_id': membership_id},
            metadata={'operation': 'delete_membership'}
        )
    except Exception as e:
        return _map_exception_to_error(e)


# Space membership aliases — "room" and "space" are synonymous in Webex

def list_webex_space_memberships(
    space_id: Optional[str] = None,
    person_id: Optional[str] = None,
    person_email: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    """
    List memberships for a space or person.
    Note: This is an alias for list_webex_memberships — "room" and "space" are synonymous in Webex.

    Args:
        space_id: Space ID to get memberships for
        person_id: Person ID to get memberships for
        person_email: Person email to get memberships for
        max_results: Maximum number of memberships to return (default 100, max 1000)

    Returns:
        Standardized response dictionary with success/error information
    """
    return list_webex_memberships(
        room_id=space_id, person_id=person_id,
        person_email=person_email, max_results=max_results
    )


def add_webex_space_membership(
    space_id: str,
    person_id: Optional[str] = None,
    person_email: Optional[str] = None,
    is_moderator: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Add a person to a Webex space.
    Note: This is an alias for add_webex_membership — "room" and "space" are synonymous in Webex.

    Args:
        space_id: Space ID to add person to (required)
        person_id: Person ID to add (use this OR person_email)
        person_email: Person email to add (use this OR person_id)
        is_moderator: Whether to make the person a moderator (optional)

    Returns:
        Standardized response dictionary with success/error information
    """
    return add_webex_membership(
        room_id=space_id, person_id=person_id,
        person_email=person_email, is_moderator=is_moderator
    )

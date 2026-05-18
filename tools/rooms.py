"""
Webex Room/Space management tools.
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
                                     "Room not found. Verify the room ID is correct.")
    if 'forbidden' in error_str or '403' in error_str:
        return create_error_response(WebexErrorCodes.FORBIDDEN,
                                     "Bot lacks permission for this operation.")
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


def _room_to_dict(room) -> Dict[str, Any]:
    d: Dict[str, Any] = {
        'id': room.id,
        'title': room.title,
        'type': room.type,
        'isLocked': room.isLocked,
        'lastActivity': room.lastActivity,
        'created': room.created,
        'creatorId': room.creatorId,
    }
    for attr in ('teamId', 'sipAddress', 'description', 'isPublic',
                 'isAnnouncementOnly', 'ownerId', 'classificationId'):
        val = getattr(room, attr, None)
        if val is not None:
            d[attr] = val
    return d


def list_webex_rooms(
    team_id: Optional[str] = None,
    room_type: Optional[str] = None,
    sort_by: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    """
    List Webex rooms that the authenticated bot belongs to.

    Args:
        team_id: Optional team ID to filter rooms by team
        room_type: Optional room type filter ('direct' or 'group')
        sort_by: Optional sort order ('id', 'lastactivity', 'created')
        max_results: Optional maximum number of rooms to return (default 100, max 1000)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        params: Dict[str, Any] = {}
        if team_id:
            params['teamId'] = team_id
        if room_type:
            params['type'] = room_type
        if sort_by:
            params['sortBy'] = sort_by
        if max_results:
            params['max'] = max_results

        rooms_list = [_room_to_dict(r) for r in webex_api.rooms.list(**params)]
        return create_success_response(
            data={'rooms': rooms_list},
            metadata={'count': len(rooms_list), 'filters_applied': params}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def create_webex_room(
    title: str,
    team_id: Optional[str] = None,
    classification_id: Optional[str] = None,
    is_locked: Optional[bool] = None,
    is_moderated: Optional[bool] = None,
    is_public: Optional[bool] = None,
    is_announcement_only: Optional[bool] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new Webex room.

    Args:
        title: Title of the room (required)
        team_id: Team ID to create room in (optional)
        classification_id: Classification for the room (optional)
        is_locked: Whether the room is locked (optional; same property as is_moderated)
        is_moderated: Whether the room is moderated (optional; same property as is_locked)
        is_public: Whether the room is public (optional)
        is_announcement_only: Whether only moderators can post (optional)
        description: Description of the room (optional)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        if is_moderated is not None and is_locked is not None:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="Cannot specify both is_locked and is_moderated — they are the same property."
            )

        final_is_locked = is_moderated if is_moderated is not None else is_locked

        params: Dict[str, Any] = {'title': title}
        if team_id:
            params['teamId'] = team_id
        if classification_id:
            params['classificationId'] = classification_id
        if final_is_locked is not None:
            params['isLocked'] = final_is_locked
        if is_public is not None:
            params['isPublic'] = is_public
        if is_announcement_only is not None:
            params['isAnnouncementOnly'] = is_announcement_only
        if description:
            params['description'] = description

        room = webex_api.rooms.create(**params)
        return create_success_response(
            data={'room': _room_to_dict(room)},
            metadata={'operation': 'create_room', 'parameters_used': params}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def update_webex_room(
    room_id: str,
    title: Optional[str] = None,
    classification_id: Optional[str] = None,
    is_locked: Optional[bool] = None,
    is_moderated: Optional[bool] = None,
    is_public: Optional[bool] = None,
    is_announcement_only: Optional[bool] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing Webex room.

    Args:
        room_id: Room ID to update (required)
        title: New title for the room (optional)
        classification_id: New classification for the room (optional)
        is_locked: Whether the room should be locked (optional; same property as is_moderated)
        is_moderated: Whether the room should be moderated (optional; same property as is_locked)
        is_public: Whether the room should be public (optional)
        is_announcement_only: Whether only moderators can post (optional)
        description: New description for the room (optional)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        if is_moderated is not None and is_locked is not None:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="Cannot specify both is_locked and is_moderated — they are the same property."
            )

        final_is_locked = is_moderated if is_moderated is not None else is_locked

        params: Dict[str, Any] = {}
        if title is not None:
            params['title'] = title
        if classification_id is not None:
            params['classificationId'] = classification_id
        if final_is_locked is not None:
            params['isLocked'] = final_is_locked
        if is_public is not None:
            params['isPublic'] = is_public
        if is_announcement_only is not None:
            params['isAnnouncementOnly'] = is_announcement_only
        if description is not None:
            params['description'] = description

        if not params:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="Must specify at least one field to update."
            )

        room = webex_api.rooms.update(roomId=room_id, **params)
        return create_success_response(
            data={'room': _room_to_dict(room)},
            metadata={'operation': 'update_room', 'room_id': room_id, 'parameters_used': params}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def get_webex_room(room_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific Webex room.

    Args:
        room_id: Room ID to get details for (required)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        room = webex_api.rooms.get(roomId=room_id)
        return create_success_response(
            data={'room': _room_to_dict(room)},
            metadata={'room_id': room_id}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def delete_webex_room(room_id: str) -> Dict[str, Any]:
    """
    Delete a Webex room.

    Args:
        room_id: Room ID to delete (required)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        if not room_id:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="room_id is required"
            )
        webex_api.rooms.delete(roomId=room_id)
        return create_success_response(
            data={'deleted': True, 'room_id': room_id},
            metadata={'operation': 'delete_room'}
        )
    except Exception as e:
        return _map_exception_to_error(e)


# Space aliases — "room" and "space" are synonymous in Webex

def list_webex_spaces(
    team_id: Optional[str] = None,
    space_type: Optional[str] = None,
    sort_by: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    """
    List Webex spaces that the authenticated bot belongs to.
    Note: This is an alias for list_webex_rooms — "room" and "space" are synonymous in Webex.

    Args:
        team_id: Optional team ID to filter spaces by team
        space_type: Optional space type filter ('direct' or 'group')
        sort_by: Optional sort order ('id', 'lastactivity', 'created')
        max_results: Optional maximum number of spaces to return (default 100, max 1000)

    Returns:
        Standardized response dictionary with success/error information
    """
    result = list_webex_rooms(
        team_id=team_id, room_type=space_type, sort_by=sort_by, max_results=max_results
    )
    if result.get('success') and 'data' in result:
        result['data']['spaces'] = result['data'].pop('rooms', [])
    return result


def create_webex_space(
    title: str,
    team_id: Optional[str] = None,
    classification_id: Optional[str] = None,
    is_locked: Optional[bool] = None,
    is_moderated: Optional[bool] = None,
    is_public: Optional[bool] = None,
    is_announcement_only: Optional[bool] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new Webex space.
    Note: This is an alias for create_webex_room — "room" and "space" are synonymous in Webex.

    Args:
        title: Title of the space (required)
        team_id: Team ID to create space in (optional)
        classification_id: Classification for the space (optional)
        is_locked: Whether the space is locked (optional; same property as is_moderated)
        is_moderated: Whether the space is moderated (optional; same property as is_locked)
        is_public: Whether the space is public (optional)
        is_announcement_only: Whether only moderators can post (optional)
        description: Description of the space (optional)

    Returns:
        Standardized response dictionary with success/error information
    """
    result = create_webex_room(
        title=title, team_id=team_id, classification_id=classification_id,
        is_locked=is_locked, is_moderated=is_moderated, is_public=is_public,
        is_announcement_only=is_announcement_only, description=description
    )
    if result.get('success') and 'data' in result:
        result['data']['space'] = result['data'].pop('room', None)
    return result


def update_webex_space(
    space_id: str,
    title: Optional[str] = None,
    classification_id: Optional[str] = None,
    is_locked: Optional[bool] = None,
    is_moderated: Optional[bool] = None,
    is_public: Optional[bool] = None,
    is_announcement_only: Optional[bool] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing Webex space.
    Note: This is an alias for update_webex_room — "room" and "space" are synonymous in Webex.

    Args:
        space_id: Space ID to update (required)
        title: New title for the space (optional)
        classification_id: New classification for the space (optional)
        is_locked: Whether the space should be locked (optional; same property as is_moderated)
        is_moderated: Whether the space should be moderated (optional; same property as is_locked)
        is_public: Whether the space should be public (optional)
        is_announcement_only: Whether only moderators can post (optional)
        description: New description for the space (optional)

    Returns:
        Standardized response dictionary with success/error information
    """
    result = update_webex_room(
        room_id=space_id, title=title, classification_id=classification_id,
        is_locked=is_locked, is_moderated=is_moderated, is_public=is_public,
        is_announcement_only=is_announcement_only, description=description
    )
    if result.get('success') and 'data' in result:
        result['data']['space'] = result['data'].pop('room', None)
    return result


def get_webex_space(space_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific Webex space.
    Note: This is an alias for get_webex_room — "room" and "space" are synonymous in Webex.

    Args:
        space_id: Space ID to get details for (required)

    Returns:
        Standardized response dictionary with success/error information
    """
    result = get_webex_room(room_id=space_id)
    if result.get('success') and 'data' in result:
        result['data']['space'] = result['data'].pop('room', None)
    return result


def delete_webex_space(space_id: str) -> Dict[str, Any]:
    """
    Delete a Webex space.
    Note: This is an alias for delete_webex_room — "room" and "space" are synonymous in Webex.

    Args:
        space_id: Space ID to delete (required)

    Returns:
        Standardized response dictionary with success/error information
    """
    return delete_webex_room(room_id=space_id)

"""
Webex Room/Space management tools.
"""
from typing import Optional, Dict, Any
from .common import webex_api


def list_webex_rooms(
    team_id: Optional[str] = None,
    room_type: Optional[str] = None,
    sort_by: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    """
    List Webex rooms that the authenticated user belongs to.
    
    Args:
        team_id: Optional team ID to filter rooms by team
        room_type: Optional room type filter ('direct' or 'group')  
        sort_by: Optional sort order ('id', 'lastactivity', 'created')
        max_results: Optional maximum number of rooms to return (default 100, max 1000)
    
    Returns:
        Dictionary containing the list of rooms and metadata
    """
    try:
        # Build parameters dict, only including non-None values
        params = {}
        if team_id:
            params['teamId'] = team_id
        if room_type:
            params['type'] = room_type
        if sort_by:
            params['sortBy'] = sort_by
        if max_results:
            params['max'] = max_results
        
        # Call the Webex API
        rooms_response = webex_api.rooms.list(**params)
        
        # Convert the response to a list of dictionaries
        rooms_list = []
        for room in rooms_response:
            room_dict = {
                'id': room.id,
                'title': room.title,
                'type': room.type,
                'isLocked': room.isLocked,
                'lastActivity': room.lastActivity,
                'created': room.created,
                'creatorId': room.creatorId
            }
            
            # Add optional fields if they exist
            if hasattr(room, 'teamId') and room.teamId:
                room_dict['teamId'] = room.teamId
            if hasattr(room, 'sipAddress') and room.sipAddress:
                room_dict['sipAddress'] = room.sipAddress
            if hasattr(room, 'description') and room.description:
                room_dict['description'] = room.description
                
            rooms_list.append(room_dict)
        
        return {
            'success': True,
            'rooms': rooms_list,
            'count': len(rooms_list),
            'filters_applied': params
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'rooms': [],
            'count': 0
        }


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
        is_locked: Whether the room is locked (optional, same as is_moderated)
        is_moderated: Whether the room is moderated (optional, same as is_locked)
        is_public: Whether the room is public (optional)
        is_announcement_only: Whether the room is announcement-only (only moderators can post) (optional)
        description: Description of the room (optional)
    
    Returns:
        Dictionary containing the created room details
    """
    try:
        # Handle the is_moderated alias - both is_locked and is_moderated refer to the same Webex property
        if is_moderated is not None and is_locked is not None:
            return {
                'success': False,
                'error': 'Cannot specify both is_locked and is_moderated - they are the same property. Use either one.',
                'room': None
            }
        
        # Use is_moderated if provided, otherwise use is_locked
        final_is_locked = is_moderated if is_moderated is not None else is_locked
        
        # Build parameters dict
        params = {'title': title}
        
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
        
        # Call the Webex API
        room_response = webex_api.rooms.create(**params)
        
        # Convert the response to a dictionary
        room_dict = {
            'id': room_response.id,
            'title': room_response.title,
            'type': room_response.type,
            'isLocked': room_response.isLocked,
            'lastActivity': room_response.lastActivity,
            'created': room_response.created,
            'creatorId': room_response.creatorId
        }
        
        # Add optional fields if they exist
        if hasattr(room_response, 'teamId') and room_response.teamId:
            room_dict['teamId'] = room_response.teamId
        if hasattr(room_response, 'description') and room_response.description:
            room_dict['description'] = room_response.description
        if hasattr(room_response, 'sipAddress') and room_response.sipAddress:
            room_dict['sipAddress'] = room_response.sipAddress
        if hasattr(room_response, 'isPublic') and room_response.isPublic is not None:
            room_dict['isPublic'] = room_response.isPublic
        if hasattr(room_response, 'isAnnouncementOnly') and room_response.isAnnouncementOnly is not None:
            room_dict['isAnnouncementOnly'] = room_response.isAnnouncementOnly
        
        return {
            'success': True,
            'room': room_dict,
            'parameters_used': params
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'room': None
        }


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
        is_locked: Whether the room should be locked (optional, same as is_moderated)
        is_moderated: Whether the room should be moderated (optional, same as is_locked)
        is_public: Whether the room should be public (optional)
        is_announcement_only: Whether the room should be announcement-only (only moderators can post) (optional)
        description: New description for the room (optional)
    
    Returns:
        Dictionary containing the updated room details
    """
    try:
        # Handle the is_moderated alias - both is_locked and is_moderated refer to the same Webex property
        if is_moderated is not None and is_locked is not None:
            return {
                'success': False,
                'error': 'Cannot specify both is_locked and is_moderated - they are the same property. Use either one.',
                'room': None
            }
        
        # Use is_moderated if provided, otherwise use is_locked
        final_is_locked = is_moderated if is_moderated is not None else is_locked
        
        # Build parameters dict - only include fields that are being updated
        params = {}
        
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
        
        # Validate that at least one field is being updated
        if not params:
            return {
                'success': False,
                'error': 'Must specify at least one field to update (title, classification_id, is_locked/is_moderated, is_public, is_announcement_only, or description)',
                'room': None
            }
        
        # Call the Webex API
        room_response = webex_api.rooms.update(roomId=room_id, **params)
        
        # Convert the response to a dictionary
        room_dict = {
            'id': room_response.id,
            'title': room_response.title,
            'type': room_response.type,
            'isLocked': room_response.isLocked,
            'lastActivity': room_response.lastActivity,
            'created': room_response.created,
            'creatorId': room_response.creatorId
        }
        
        # Add optional fields if they exist
        if hasattr(room_response, 'teamId') and room_response.teamId:
            room_dict['teamId'] = room_response.teamId
        if hasattr(room_response, 'description') and room_response.description:
            room_dict['description'] = room_response.description
        if hasattr(room_response, 'sipAddress') and room_response.sipAddress:
            room_dict['sipAddress'] = room_response.sipAddress
        if hasattr(room_response, 'isPublic') and room_response.isPublic is not None:
            room_dict['isPublic'] = room_response.isPublic
        if hasattr(room_response, 'isAnnouncementOnly') and room_response.isAnnouncementOnly is not None:
            room_dict['isAnnouncementOnly'] = room_response.isAnnouncementOnly
        
        return {
            'success': True,
            'room': room_dict,
            'room_id': room_id,
            'parameters_used': params
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'room': None
        }


def get_webex_room(
    room_id: str
) -> Dict[str, Any]:
    """
    Get detailed information about a specific Webex room.
    
    Args:
        room_id: Room ID to get details for (required)
    
    Returns:
        Dictionary containing the room details
    """
    try:
        # Call the Webex API
        room_response = webex_api.rooms.get(roomId=room_id)
        
        # Convert the response to a dictionary
        room_dict = {
            'id': room_response.id,
            'title': room_response.title,
            'type': room_response.type,
            'isLocked': room_response.isLocked,
            'lastActivity': room_response.lastActivity,
            'created': room_response.created,
            'creatorId': room_response.creatorId
        }
        
        # Add optional fields if they exist
        if hasattr(room_response, 'teamId') and room_response.teamId:
            room_dict['teamId'] = room_response.teamId
        if hasattr(room_response, 'description') and room_response.description:
            room_dict['description'] = room_response.description
        if hasattr(room_response, 'sipAddress') and room_response.sipAddress:
            room_dict['sipAddress'] = room_response.sipAddress
        if hasattr(room_response, 'isPublic') and room_response.isPublic is not None:
            room_dict['isPublic'] = room_response.isPublic
        if hasattr(room_response, 'isAnnouncementOnly') and room_response.isAnnouncementOnly is not None:
            room_dict['isAnnouncementOnly'] = room_response.isAnnouncementOnly
        if hasattr(room_response, 'ownerId') and room_response.ownerId:
            room_dict['ownerId'] = room_response.ownerId
        if hasattr(room_response, 'classificationId') and room_response.classificationId:
            room_dict['classificationId'] = room_response.classificationId
        
        return {
            'success': True,
            'room': room_dict,
            'room_id': room_id
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'room': None
        }


# Space aliases - these provide the same functionality as room tools but with "space" terminology
# This allows users to use either "room" or "space" interchangeably

def list_webex_spaces(
    team_id: Optional[str] = None,
    space_type: Optional[str] = None,
    sort_by: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    """
    List Webex spaces that the authenticated user belongs to.
    Note: This is an alias for list_webex_rooms - "room" and "space" are synonymous in Webex.
    
    Args:
        team_id: Optional team ID to filter spaces by team
        space_type: Optional space type filter ('direct' or 'group')  
        sort_by: Optional sort order ('id', 'lastactivity', 'created')
        max_results: Optional maximum number of spaces to return (default 100, max 1000)
    
    Returns:
        Dictionary containing the list of spaces and metadata
    """
    # Call the underlying room function with mapped parameters
    result = list_webex_rooms(
        team_id=team_id,
        room_type=space_type,  # Map space_type to room_type
        sort_by=sort_by,
        max_results=max_results
    )
    
    # Update the response to use "space" terminology
    if result.get('success'):
        result['spaces'] = result.pop('rooms', [])
    
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
    Note: This is an alias for create_webex_room - "room" and "space" are synonymous in Webex.
    
    Args:
        title: Title of the space (required)
        team_id: Team ID to create space in (optional)
        classification_id: Classification for the space (optional)
        is_locked: Whether the space is locked (optional, same as is_moderated)
        is_moderated: Whether the space is moderated (optional, same as is_locked)
        is_public: Whether the space is public (optional)
        is_announcement_only: Whether the space is announcement-only (only moderators can post) (optional)
        description: Description of the space (optional)
    
    Returns:
        Dictionary containing the created space details
    """
    # Call the underlying room function
    result = create_webex_room(
        title=title,
        team_id=team_id,
        classification_id=classification_id,
        is_locked=is_locked,
        is_moderated=is_moderated,
        is_public=is_public,
        is_announcement_only=is_announcement_only,
        description=description
    )
    
    # Update the response to use "space" terminology
    if result.get('success'):
        result['space'] = result.pop('room', None)
    
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
    Note: This is an alias for update_webex_room - "room" and "space" are synonymous in Webex.
    
    Args:
        space_id: Space ID to update (required)
        title: New title for the space (optional)
        classification_id: New classification for the space (optional)
        is_locked: Whether the space should be locked (optional, same as is_moderated)
        is_moderated: Whether the space should be moderated (optional, same as is_locked)
        is_public: Whether the space should be public (optional)
        is_announcement_only: Whether the space should be announcement-only (only moderators can post) (optional)
        description: New description for the space (optional)
    
    Returns:
        Dictionary containing the updated space details
    """
    # Call the underlying room function with mapped parameters
    result = update_webex_room(
        room_id=space_id,  # Map space_id to room_id
        title=title,
        classification_id=classification_id,
        is_locked=is_locked,
        is_moderated=is_moderated,
        is_public=is_public,
        is_announcement_only=is_announcement_only,
        description=description
    )
    
    # Update the response to use "space" terminology
    if result.get('success'):
        result['space'] = result.pop('room', None)
        result['space_id'] = result.pop('room_id', None)
    
    return result


def get_webex_space(
    space_id: str
) -> Dict[str, Any]:
    """
    Get detailed information about a specific Webex space.
    Note: This is an alias for get_webex_room - "room" and "space" are synonymous in Webex.
    
    Args:
        space_id: Space ID to get details for (required)
    
    Returns:
        Dictionary containing the space details
    """
    # Call the underlying room function with mapped parameters
    result = get_webex_room(room_id=space_id)  # Map space_id to room_id
    
    # Update the response to use "space" terminology
    if result.get('success'):
        result['space'] = result.pop('room', None)
        result['space_id'] = result.pop('room_id', None)
    
    return result

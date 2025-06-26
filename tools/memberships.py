"""
Webex Membership management tools.
"""
from typing import Optional, Dict, Any
from .common import webex_api


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
        Dictionary containing the list of memberships and metadata
    """
    try:
        # Build parameters dict
        params = {}
        if room_id:
            params['roomId'] = room_id
        if person_id:
            params['personId'] = person_id
        if person_email:
            params['personEmail'] = person_email
        if max_results:
            params['max'] = max_results
        
        # Call the Webex API
        memberships_response = webex_api.memberships.list(**params)
        
        # Convert the response to a list of dictionaries
        memberships_list = []
        for membership in memberships_response:
            membership_dict = {
                'id': membership.id,
                'roomId': membership.roomId,
                'personId': membership.personId,
                'personEmail': membership.personEmail,
                'personDisplayName': membership.personDisplayName,
                'personOrgId': membership.personOrgId,
                'isModerator': membership.isModerator,
                'isMonitor': membership.isMonitor,
                'created': membership.created
            }
            
            # Add optional fields if they exist
            if hasattr(membership, 'roomType') and membership.roomType:
                membership_dict['roomType'] = membership.roomType
                
            memberships_list.append(membership_dict)
        
        return {
            'success': True,
            'memberships': memberships_list,
            'count': len(memberships_list),
            'filters_applied': params
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'memberships': [],
            'count': 0
        }


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
        Dictionary containing the created membership details
    """
    try:
        # Validate required parameters
        if not (person_id or person_email):
            return {
                'success': False,
                'error': 'Must specify either person_id or person_email',
                'membership': None
            }
        
        # Build parameters dict
        params = {'roomId': room_id}
        
        if person_id:
            params['personId'] = person_id
        elif person_email:
            params['personEmail'] = person_email
        
        if is_moderator is not None:
            params['isModerator'] = is_moderator
        
        # Call the Webex API
        membership_response = webex_api.memberships.create(**params)
        
        # Convert the response to a dictionary
        membership_dict = {
            'id': membership_response.id,
            'roomId': membership_response.roomId,
            'personId': membership_response.personId,
            'personEmail': membership_response.personEmail,
            'personDisplayName': membership_response.personDisplayName,
            'personOrgId': membership_response.personOrgId,
            'isModerator': membership_response.isModerator,
            'isMonitor': membership_response.isMonitor,
            'created': membership_response.created
        }
        
        # Add optional fields if they exist
        if hasattr(membership_response, 'roomType') and membership_response.roomType:
            membership_dict['roomType'] = membership_response.roomType
        
        return {
            'success': True,
            'membership': membership_dict,
            'parameters_used': params
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'membership': None
        }


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
        Dictionary containing the updated membership details
    """
    try:
        # Build parameters dict - only include fields that are being updated
        params = {}
        
        if is_moderator is not None:
            params['isModerator'] = is_moderator
        if is_monitor is not None:
            params['isMonitor'] = is_monitor
        
        # Validate that at least one field is being updated
        if not params:
            return {
                'success': False,
                'error': 'Must specify at least one field to update (is_moderator or is_monitor)',
                'membership': None
            }
        
        # Call the Webex API
        membership_response = webex_api.memberships.update(membershipId=membership_id, **params)
        
        # Convert the response to a dictionary
        membership_dict = {
            'id': membership_response.id,
            'roomId': membership_response.roomId,
            'personId': membership_response.personId,
            'personEmail': membership_response.personEmail,
            'personDisplayName': membership_response.personDisplayName,
            'personOrgId': membership_response.personOrgId,
            'isModerator': membership_response.isModerator,
            'isMonitor': membership_response.isMonitor,
            'created': membership_response.created
        }
        
        # Add optional fields if they exist
        if hasattr(membership_response, 'roomType') and membership_response.roomType:
            membership_dict['roomType'] = membership_response.roomType
        
        return {
            'success': True,
            'membership': membership_dict,
            'membership_id': membership_id,
            'parameters_used': params
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'membership': None
        }


# Space membership aliases - these provide the same functionality but with "space" terminology

def list_webex_space_memberships(
    space_id: Optional[str] = None,
    person_id: Optional[str] = None,
    person_email: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    """
    List memberships for a space or person.
    Note: This is an alias for list_webex_memberships - "room" and "space" are synonymous in Webex.
    
    Args:
        space_id: Space ID to get memberships for
        person_id: Person ID to get memberships for
        person_email: Person email to get memberships for
        max_results: Maximum number of memberships to return (default 100, max 1000)
    
    Returns:
        Dictionary containing the list of memberships and metadata
    """
    # Call the underlying memberships function with mapped parameters
    return list_webex_memberships(
        room_id=space_id,  # Map space_id to room_id
        person_id=person_id,
        person_email=person_email,
        max_results=max_results
    )


def add_webex_space_membership(
    space_id: str,
    person_id: Optional[str] = None,
    person_email: Optional[str] = None,
    is_moderator: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Add a person to a Webex space.
    Note: This is an alias for add_webex_membership - "room" and "space" are synonymous in Webex.
    
    Args:
        space_id: Space ID to add person to (required)
        person_id: Person ID to add (use this OR person_email)
        person_email: Person email to add (use this OR person_id)
        is_moderator: Whether to make the person a moderator (optional)
    
    Returns:
        Dictionary containing the created membership details
    """
    # Call the underlying membership function with mapped parameters
    return add_webex_membership(
        room_id=space_id,  # Map space_id to room_id
        person_id=person_id,
        person_email=person_email,
        is_moderator=is_moderator
    )

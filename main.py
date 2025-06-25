import os   
import argparse
from dotenv import load_dotenv
from fastmcp import FastMCP
from webexpythonsdk import WebexAPI
from typing import Optional, Dict, Any


# Load environment variables from .env file
load_dotenv()

# Initialize Webex SDK
webex_access_token = os.getenv("WEBEX_ACCESS_TOKEN")
if not webex_access_token:
    raise ValueError("WEBEX_ACCESS_TOKEN environment variable is required")

webex_api = WebexAPI(access_token=webex_access_token)

# Initialize FastMCP with a name for the bot
mcp = FastMCP("Webex Bot MCP")

@mcp.tool()
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

@mcp.tool()
def send_webex_message(
    room_id: Optional[str] = None,
    to_person_id: Optional[str] = None,
    to_person_email: Optional[str] = None,
    text: Optional[str] = None,
    markdown: Optional[str] = None,
    html: Optional[str] = None,
    files: Optional[str] = None,
    parent_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a message to a Webex room or person.
    
    Args:
        room_id: Room ID to send the message to (use this OR to_person_id/to_person_email)
        to_person_id: Person ID to send a direct message to
        to_person_email: Person email to send a direct message to
        text: Plain text message content
        markdown: Markdown formatted message content
        html: HTML formatted message content (for buttons/cards)
        files: URL or file path to attach (single file as string)
        parent_id: Parent message ID for threaded replies
    
    Returns:
        Dictionary containing the sent message details and metadata
    """
    try:
        # Validate required parameters
        if not (room_id or to_person_id or to_person_email):
            return {
                'success': False,
                'error': 'Must specify either room_id, to_person_id, or to_person_email',
                'message': None
            }
        
        if not (text or markdown or html or files):
            return {
                'success': False,
                'error': 'Must specify at least one of: text, markdown, html, or files',
                'message': None
            }
        
        # Build parameters dict, only including non-None values
        params = {}
        
        # Destination parameters (mutually exclusive)
        if room_id:
            params['roomId'] = room_id
        elif to_person_id:
            params['toPersonId'] = to_person_id
        elif to_person_email:
            params['toPersonEmail'] = to_person_email
        
        # Content parameters
        if text:
            params['text'] = text
        if markdown:
            params['markdown'] = markdown
        if html:
            params['html'] = html
        if files:
            params['files'] = [files] if isinstance(files, str) else files
        if parent_id:
            params['parentId'] = parent_id
        
        # Call the Webex API
        message_response = webex_api.messages.create(**params)
        
        # Convert the response to a dictionary
        message_dict = {
            'id': message_response.id,
            'roomId': message_response.roomId,
            'roomType': message_response.roomType,
            'text': message_response.text,
            'personId': message_response.personId,
            'personEmail': message_response.personEmail,
            'created': message_response.created
        }
        
        # Add optional fields if they exist
        if hasattr(message_response, 'markdown') and message_response.markdown:
            message_dict['markdown'] = message_response.markdown
        if hasattr(message_response, 'html') and message_response.html:
            message_dict['html'] = message_response.html
        if hasattr(message_response, 'files') and message_response.files:
            message_dict['files'] = message_response.files
        if hasattr(message_response, 'parentId') and message_response.parentId:
            message_dict['parentId'] = message_response.parentId
        if hasattr(message_response, 'mentionedPeople') and message_response.mentionedPeople:
            message_dict['mentionedPeople'] = message_response.mentionedPeople
        if hasattr(message_response, 'mentionedGroups') and message_response.mentionedGroups:
            message_dict['mentionedGroups'] = message_response.mentionedGroups
        
        return {
            'success': True,
            'message': message_dict,
            'parameters_used': params
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': None
        }

@mcp.tool()
def get_webex_me() -> Dict[str, Any]:
    """
    Get information about the authenticated Webex user.
    
    Returns:
        Dictionary containing the authenticated user's information
    """
    try:
        # Call the Webex API to get user info
        me_response = webex_api.people.me()
        
        # Convert the response to a dictionary
        me_dict = {
            'id': me_response.id,
            'emails': me_response.emails,
            'displayName': me_response.displayName,
            'nickName': me_response.nickName,
            'firstName': me_response.firstName,
            'lastName': me_response.lastName,
            'avatar': me_response.avatar,
            'orgId': me_response.orgId,
            'created': me_response.created,
            'lastModified': me_response.lastModified,
            'status': me_response.status,
            'type': me_response.type
        }
        
        # Add optional fields if they exist
        if hasattr(me_response, 'userName') and me_response.userName:
            me_dict['userName'] = me_response.userName
        if hasattr(me_response, 'roles') and me_response.roles:
            me_dict['roles'] = me_response.roles
        if hasattr(me_response, 'licenses') and me_response.licenses:
            me_dict['licenses'] = me_response.licenses
        if hasattr(me_response, 'phoneNumbers') and me_response.phoneNumbers:
            me_dict['phoneNumbers'] = me_response.phoneNumbers
        if hasattr(me_response, 'extension') and me_response.extension:
            me_dict['extension'] = me_response.extension
        if hasattr(me_response, 'locationId') and me_response.locationId:
            me_dict['locationId'] = me_response.locationId
        if hasattr(me_response, 'addresses') and me_response.addresses:
            me_dict['addresses'] = me_response.addresses
        if hasattr(me_response, 'timezone') and me_response.timezone:
            me_dict['timezone'] = me_response.timezone
        
        return {
            'success': True,
            'user': me_dict
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'user': None
        }

@mcp.tool()
def list_webex_messages(
    room_id: str,
    mentioned_people: Optional[str] = None,
    before: Optional[str] = None,
    before_message: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    """
    List messages from a Webex room.
    
    Args:
        room_id: Room ID to get messages from (required)
        mentioned_people: Person ID to filter messages that mention them
        before: Get messages before this date (ISO 8601 format)
        before_message: Get messages before this message ID
        max_results: Maximum number of messages to return (default 50, max 1000)
    
    Returns:
        Dictionary containing the list of messages and metadata
    """
    try:
        # Build parameters dict
        params = {'roomId': room_id}
        
        if mentioned_people:
            params['mentionedPeople'] = mentioned_people
        if before:
            params['before'] = before
        if before_message:
            params['beforeMessage'] = before_message
        if max_results:
            params['max'] = max_results
        
        # Call the Webex API
        messages_response = webex_api.messages.list(**params)
        
        # Convert the response to a list of dictionaries
        messages_list = []
        for message in messages_response:
            message_dict = {
                'id': message.id,
                'roomId': message.roomId,
                'roomType': message.roomType,
                'text': message.text,
                'personId': message.personId,
                'personEmail': message.personEmail,
                'created': message.created
            }
            
            # Add optional fields if they exist
            if hasattr(message, 'markdown') and message.markdown:
                message_dict['markdown'] = message.markdown
            if hasattr(message, 'html') and message.html:
                message_dict['html'] = message.html
            if hasattr(message, 'files') and message.files:
                message_dict['files'] = message.files
            if hasattr(message, 'parentId') and message.parentId:
                message_dict['parentId'] = message.parentId
            if hasattr(message, 'mentionedPeople') and message.mentionedPeople:
                message_dict['mentionedPeople'] = message.mentionedPeople
            if hasattr(message, 'mentionedGroups') and message.mentionedGroups:
                message_dict['mentionedGroups'] = message.mentionedGroups
                
            messages_list.append(message_dict)
        
        return {
            'success': True,
            'messages': messages_list,
            'count': len(messages_list),
            'room_id': room_id,
            'filters_applied': params
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'messages': [],
            'count': 0
        }

@mcp.tool()
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

@mcp.tool()
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

@mcp.tool()
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

@mcp.tool()
def list_webex_people(
    email: Optional[str] = None,
    display_name: Optional[str] = None,
    id: Optional[str] = None,
    org_id: Optional[str] = None,
    calling_data: Optional[bool] = None,
    location_id: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    """
    List people in the organization or search for specific people.
    
    Args:
        email: Email address to search for
        display_name: Display name to search for
        id: Person ID to get specific person
        org_id: Organization ID to filter by
        calling_data: Include calling data in response
        location_id: Location ID to filter by
        max_results: Maximum number of people to return (default 100, max 1000)
    
    Returns:
        Dictionary containing the list of people and metadata
    """
    try:
        # Build parameters dict
        params = {}
        if email:
            params['email'] = email
        if display_name:
            params['displayName'] = display_name
        if id:
            params['id'] = id
        if org_id:
            params['orgId'] = org_id
        if calling_data is not None:
            params['callingData'] = calling_data
        if location_id:
            params['locationId'] = location_id
        if max_results:
            params['max'] = max_results
        
        # Call the Webex API
        people_response = webex_api.people.list(**params)
        
        # Convert the response to a list of dictionaries
        people_list = []
        for person in people_response:
            person_dict = {
                'id': person.id,
                'emails': person.emails,
                'displayName': person.displayName,
                'nickName': person.nickName,
                'firstName': person.firstName,
                'lastName': person.lastName,
                'avatar': person.avatar,
                'orgId': person.orgId,
                'created': person.created,
                'status': person.status,
                'type': person.type
            }
            
            # Add optional fields if they exist
            if hasattr(person, 'userName') and person.userName:
                person_dict['userName'] = person.userName
            if hasattr(person, 'lastModified') and person.lastModified:
                person_dict['lastModified'] = person.lastModified
            if hasattr(person, 'roles') and person.roles:
                person_dict['roles'] = person.roles
            if hasattr(person, 'licenses') and person.licenses:
                person_dict['licenses'] = person.licenses
            if hasattr(person, 'phoneNumbers') and person.phoneNumbers:
                person_dict['phoneNumbers'] = person.phoneNumbers
            if hasattr(person, 'extension') and person.extension:
                person_dict['extension'] = person.extension
            if hasattr(person, 'locationId') and person.locationId:
                person_dict['locationId'] = person.locationId
            if hasattr(person, 'addresses') and person.addresses:
                person_dict['addresses'] = person.addresses
            if hasattr(person, 'timezone') and person.timezone:
                person_dict['timezone'] = person.timezone
                
            people_list.append(person_dict)
        
        return {
            'success': True,
            'people': people_list,
            'count': len(people_list),
            'filters_applied': params
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'people': [],
            'count': 0
        }

@mcp.tool()
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

@mcp.tool()
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

@mcp.tool()
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

@mcp.tool()
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

@mcp.tool()
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

@mcp.tool()
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

@mcp.tool()
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

@mcp.tool()
def send_webex_space_message(
    space_id: Optional[str] = None,
    to_person_id: Optional[str] = None,
    to_person_email: Optional[str] = None,
    text: Optional[str] = None,
    markdown: Optional[str] = None,
    html: Optional[str] = None,
    files: Optional[str] = None,
    parent_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a message to a Webex space or person.
    Note: This is an alias for send_webex_message - "room" and "space" are synonymous in Webex.
    
    Args:
        space_id: Space ID to send the message to (use this OR to_person_id/to_person_email)
        to_person_id: Person ID to send a direct message to
        to_person_email: Person email to send a direct message to
        text: Plain text message content
        markdown: Markdown formatted message content
        html: HTML formatted message content (for buttons/cards)
        files: URL or file path to attach (single file as string)
        parent_id: Parent message ID for threaded replies
    
    Returns:
        Dictionary containing the sent message details and metadata
    """
    # Call the underlying message function with mapped parameters
    return send_webex_message(
        room_id=space_id,  # Map space_id to room_id
        to_person_id=to_person_id,
        to_person_email=to_person_email,
        text=text,
        markdown=markdown,
        html=html,
        files=files,
        parent_id=parent_id
    )

@mcp.tool()
def list_webex_space_messages(
    space_id: str,
    mentioned_people: Optional[str] = None,
    before: Optional[str] = None,
    before_message: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    """
    List messages from a Webex space.
    Note: This is an alias for list_webex_messages - "room" and "space" are synonymous in Webex.
    
    Args:
        space_id: Space ID to get messages from (required)
        mentioned_people: Person ID to filter messages that mention them
        before: Get messages before this date (ISO 8601 format)
        before_message: Get messages before this message ID
        max_results: Maximum number of messages to return (default 50, max 1000)
    
    Returns:
        Dictionary containing the list of messages and metadata
    """
    # Call the underlying messages function with mapped parameters
    result = list_webex_messages(
        room_id=space_id,  # Map space_id to room_id
        mentioned_people=mentioned_people,
        before=before,
        before_message=before_message,
        max_results=max_results
    )
    
    # Update the response to use "space" terminology
    if result.get('success'):
        result['space_id'] = result.pop('room_id', None)
    
    return result

@mcp.tool()
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

@mcp.tool()
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

if __name__ == "__main__":
    # Parse command line arguments for transport type
    parser = argparse.ArgumentParser(description="Webex Bot MCP Server")
    parser.add_argument(
        "--transport", 
        choices=["stdio", "streamable-http"], 
        default="stdio",
        help="Transport type to use (default: stdio)"
    )
    parser.add_argument(
        "--host",
        default="localhost", 
        help="Host to bind to for streamable-http transport (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to for streamable-http transport (default: 8000)"
    )
    
    args = parser.parse_args()
    
    if args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        mcp.run()


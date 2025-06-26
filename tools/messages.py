"""
Webex Message management tools.
"""
from typing import Optional, Dict, Any
from .common import webex_api


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


# Space message aliases - these provide the same functionality but with "space" terminology

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

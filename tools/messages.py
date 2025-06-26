"""
Webex Message management tools.
"""
from typing import Optional, Dict, Any, List
from .common import webex_api


def format_mention_by_email(email: str, display_name: Optional[str] = None) -> str:
    """
    Format a mention by email address for Webex messages.
    
    Args:
        email: Email address of the person to mention
        display_name: Optional display name to show in the mention
    
    Returns:
        Properly formatted mention string
    """
    if display_name:
        return f"<@personEmail:{email}|{display_name}>"
    else:
        return f"<@personEmail:{email}>"


def format_mention_by_person_id(person_id: str, display_name: Optional[str] = None) -> str:
    """
    Format a mention by person ID for Webex messages.
    
    Args:
        person_id: Person ID to mention
        display_name: Optional display name to show in the mention
    
    Returns:
        Properly formatted mention string
    """
    if display_name:
        return f"<@personId:{person_id}|{display_name}>"
    else:
        return f"<@personId:{person_id}>"


def format_mention_all() -> str:
    """
    Format a mention for all people in a room.
    
    Returns:
        Properly formatted @all mention string
    """
    return "<@all>"


def create_message_with_mentions(
    base_message: str,
    mentions: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Create a message with properly formatted mentions.
    
    Args:
        base_message: The base message text
        mentions: List of mention dictionaries with keys:
                 - type: "email", "person_id", or "all"
                 - value: email address or person ID (not needed for "all")
                 - display_name: optional display name
    
    Returns:
        Message with properly formatted mentions
    """
    if not mentions:
        return base_message
    
    message_parts = [base_message]
    
    for mention in mentions:
        mention_type = mention.get('type', '').lower()
        
        if mention_type == 'email':
            email = mention.get('value', '')
            display_name = mention.get('display_name')
            if email:
                formatted_mention = format_mention_by_email(email, display_name)
                message_parts.append(formatted_mention)
        
        elif mention_type == 'person_id':
            person_id = mention.get('value', '')
            display_name = mention.get('display_name')
            if person_id:
                formatted_mention = format_mention_by_person_id(person_id, display_name)
                message_parts.append(formatted_mention)
        
        elif mention_type == 'all':
            formatted_mention = format_mention_all()
            message_parts.append(formatted_mention)
    
    return ' '.join(message_parts)


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


def send_webex_message_with_mentions(
    room_id: Optional[str] = None,
    to_person_id: Optional[str] = None,
    to_person_email: Optional[str] = None,
    text: Optional[str] = None,  
    markdown: Optional[str] = None,
    html: Optional[str] = None,
    files: Optional[str] = None,
    parent_id: Optional[str] = None,
    mentions: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Send a message to a Webex room or person with proper mention support.
    
    Args:
        room_id: Room ID to send the message to (use this OR to_person_id/to_person_email)
        to_person_id: Person ID to send a direct message to
        to_person_email: Person email to send a direct message to
        text: Plain text message content
        markdown: Markdown formatted message content
        html: HTML formatted message content (for buttons/cards)
        files: URL or file path to attach (single file as string)
        parent_id: Parent message ID for threaded replies
        mentions: List of mention dictionaries with keys:
                 - type: "email", "person_id", or "all"
                 - value: email address or person ID (not needed for "all")
                 - display_name: optional display name
    
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
        
        # Process mentions and update content accordingly
        if mentions:
            if markdown:
                # Add mentions to markdown content
                mention_strings = []
                for mention in mentions:
                    mention_type = mention.get('type', '').lower()
                    
                    if mention_type == 'email':
                        email = mention.get('value', '')
                        display_name = mention.get('display_name')
                        if email:
                            mention_strings.append(format_mention_by_email(email, display_name))
                    
                    elif mention_type == 'person_id':
                        person_id = mention.get('value', '')
                        display_name = mention.get('display_name')
                        if person_id:
                            mention_strings.append(format_mention_by_person_id(person_id, display_name))
                    
                    elif mention_type == 'all':
                        mention_strings.append(format_mention_all())
                
                # Prepend mentions to the markdown content
                if mention_strings:
                    params['markdown'] = ' '.join(mention_strings) + ' ' + markdown
                else:
                    params['markdown'] = markdown
            
            elif text:
                # Add mentions to text content
                mention_strings = []
                for mention in mentions:
                    mention_type = mention.get('type', '').lower()
                    
                    if mention_type == 'email':
                        email = mention.get('value', '')
                        display_name = mention.get('display_name')
                        if email:
                            mention_strings.append(format_mention_by_email(email, display_name))
                    
                    elif mention_type == 'person_id':
                        person_id = mention.get('value', '')
                        display_name = mention.get('display_name')
                        if person_id:
                            mention_strings.append(format_mention_by_person_id(person_id, display_name))
                    
                    elif mention_type == 'all':
                        mention_strings.append(format_mention_all())
                
                # Prepend mentions to the text content
                if mention_strings:
                    params['text'] = ' '.join(mention_strings) + ' ' + text
                else:
                    params['text'] = text
        else:
            # No mentions, use original content
            if text:
                params['text'] = text
            if markdown:
                params['markdown'] = markdown
        
        # Add other content parameters
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
            'parameters_used': params,
            'mentions_processed': mentions or []
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

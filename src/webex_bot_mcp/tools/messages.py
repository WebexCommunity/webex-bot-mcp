"""
Webex Message management tools.
"""
from typing import Optional, Dict, Any, List
from .common import webex_api, create_error_response, create_success_response, WebexErrorCodes


def format_mention_by_email(email: str, display_name: Optional[str] = None) -> str:
    if display_name:
        return f"<@personEmail:{email}|{display_name}>"
    return f"<@personEmail:{email}>"


def format_mention_by_person_id(person_id: str, display_name: Optional[str] = None) -> str:
    if display_name:
        return f"<@personId:{person_id}|{display_name}>"
    return f"<@personId:{person_id}>"


def format_mention_all() -> str:
    return "<@all>"


def _build_mention_strings(mentions: List[Dict[str, str]]) -> List[str]:
    """Convert a mentions list into formatted mention strings."""
    result = []
    for mention in mentions:
        mention_type = mention.get('type', '').lower()
        display_name = mention.get('display_name')
        if mention_type == 'email':
            email = mention.get('value', '')
            if email:
                result.append(format_mention_by_email(email, display_name))
        elif mention_type == 'person_id':
            person_id = mention.get('value', '')
            if person_id:
                result.append(format_mention_by_person_id(person_id, display_name))
        elif mention_type == 'all':
            result.append(format_mention_all())
    return result


def create_message_with_mentions(
    base_message: str,
    mentions: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Create a message with properly formatted mentions prepended.

    Args:
        base_message: The base message text
        mentions: List of mention dicts with keys:
                 - type: "email", "person_id", or "all"
                 - value: email address or person ID (not needed for "all")
                 - display_name: optional display name

    Returns:
        Message with properly formatted mentions
    """
    if not mentions:
        return base_message
    strings = _build_mention_strings(mentions)
    if strings:
        return ' '.join(strings) + ' ' + base_message
    return base_message


def _map_exception_to_error(e: Exception) -> Dict[str, Any]:
    """Map a caught exception to a structured error response."""
    error_str = str(e).lower()
    if 'rate limit' in error_str or 'too many requests' in error_str:
        return create_error_response(
            error_code=WebexErrorCodes.RATE_LIMITED,
            message="API rate limit exceeded. Please retry after delay.",
            temporary=True,
            retry_after_seconds=60
        )
    if 'unauthorized' in error_str or 'invalid token' in error_str:
        return create_error_response(
            error_code=WebexErrorCodes.UNAUTHORIZED,
            message="Invalid or expired bot token. Please check WEBEX_ACCESS_TOKEN."
        )
    if 'not found' in error_str or '404' in error_str:
        return create_error_response(
            error_code=WebexErrorCodes.NOT_FOUND,
            message="Room or person not found. Please verify the ID/email is correct."
        )
    if 'forbidden' in error_str or '403' in error_str:
        return create_error_response(
            error_code=WebexErrorCodes.FORBIDDEN,
            message="Bot lacks permission for this operation. Ensure bot is added to the room."
        )
    if 'network' in error_str or 'connection' in error_str:
        return create_error_response(
            error_code=WebexErrorCodes.NETWORK_ERROR,
            message="Network connectivity issue. Please retry.",
            temporary=True,
            retry_after_seconds=30
        )
    return create_error_response(
        error_code=WebexErrorCodes.WEBEX_API_ERROR,
        message=f"Webex API error: {e}",
        temporary=True,
        details={'original_error': str(e)}
    )


def _build_message_params(
    room_id: Optional[str],
    to_person_id: Optional[str],
    to_person_email: Optional[str],
    text: Optional[str],
    markdown: Optional[str],
    html: Optional[str],
    files: Optional[str],
    parent_id: Optional[str],
) -> Dict[str, Any]:
    """Assemble the keyword-argument dict for webex_api.messages.create."""
    params: Dict[str, Any] = {}
    if room_id:
        params['roomId'] = room_id
    elif to_person_id:
        params['toPersonId'] = to_person_id
    elif to_person_email:
        params['toPersonEmail'] = to_person_email
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
    return params


def _message_to_dict(message) -> Dict[str, Any]:
    """Convert a Webex SDK message object to a plain dict."""
    d: Dict[str, Any] = {
        'id': message.id,
        'roomId': message.roomId,
        'text': message.text,
        'personId': message.personId,
        'personEmail': message.personEmail,
        'created': (
            message.created.isoformat()
            if hasattr(message.created, 'isoformat')
            else str(message.created)
        ),
    }
    for attr in ('roomType', 'markdown', 'html', 'files', 'parentId',
                 'mentionedPeople', 'mentionedGroups'):
        val = getattr(message, attr, None)
        if val:
            d[attr] = val
    return d


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
        files: URL to attach (single file URL as a string)
        parent_id: Parent message ID for threaded replies

    Returns:
        Standardized response dictionary with success/error information

    Examples:
        # Send to room
        result = send_webex_message(
            room_id="Y2lzY29zcGFyazovL3VzL1JPT00vYmJjZWIx",
            text="Hello team!"
        )

        # Send direct message
        result = send_webex_message(
            to_person_email="user@company.com",
            markdown="**Important update:** Please review the report"
        )
    """
    try:
        if not (room_id or to_person_id or to_person_email):
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="Must specify either room_id, to_person_id, or to_person_email",
                details={"required_one_of": ["room_id", "to_person_id", "to_person_email"]}
            )

        if not (text or markdown or html or files):
            return create_error_response(
                error_code=WebexErrorCodes.MISSING_REQUIRED_FIELD,
                message="Must specify at least one of: text, markdown, html, or files",
                details={"required_one_of": ["text", "markdown", "html", "files"]}
            )

        if text and len(text) > 7439:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_FIELD_VALUE,
                message=f"Text content exceeds maximum length of 7439 characters (provided: {len(text)})",
                details={"field": "text", "max_length": 7439, "provided_length": len(text)}
            )

        if markdown and len(markdown) > 7439:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_FIELD_VALUE,
                message=f"Markdown content exceeds maximum length of 7439 characters (provided: {len(markdown)})",
                details={"field": "markdown", "max_length": 7439, "provided_length": len(markdown)}
            )

        params = _build_message_params(
            room_id, to_person_id, to_person_email,
            text, markdown, html, files, parent_id
        )
        message = webex_api.messages.create(**params)

        return create_success_response(
            data=_message_to_dict(message),
            metadata={
                'operation': 'send_message',
                'destination_type': 'room' if room_id else 'direct',
                'content_type': 'markdown' if markdown else 'html' if html else 'text',
                'has_files': bool(files),
                'is_threaded': bool(parent_id)
            }
        )

    except Exception as e:
        return _map_exception_to_error(e)


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
        files: URL to attach (single file URL as a string)
        parent_id: Parent message ID for threaded replies
        mentions: List of mention dicts with keys:
                 - type: "email", "person_id", or "all"
                 - value: email address or person ID (not needed for "all")
                 - display_name: optional display name

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        if not (room_id or to_person_id or to_person_email):
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="Must specify either room_id, to_person_id, or to_person_email",
                details={"required_one_of": ["room_id", "to_person_id", "to_person_email"]}
            )

        if not (text or markdown or html or files):
            return create_error_response(
                error_code=WebexErrorCodes.MISSING_REQUIRED_FIELD,
                message="Must specify at least one of: text, markdown, html, or files",
                details={"required_one_of": ["text", "markdown", "html", "files"]}
            )

        # Apply mentions to the primary content field
        if mentions:
            if markdown:
                markdown = create_message_with_mentions(markdown, mentions)
            elif text:
                text = create_message_with_mentions(text, mentions)

        params = _build_message_params(
            room_id, to_person_id, to_person_email,
            text, markdown, html, files, parent_id
        )
        message = webex_api.messages.create(**params)

        return create_success_response(
            data=_message_to_dict(message),
            metadata={
                'operation': 'send_message_with_mentions',
                'destination_type': 'room' if room_id else 'direct',
                'content_type': 'markdown' if markdown else 'html' if html else 'text',
                'has_files': bool(files),
                'is_threaded': bool(parent_id),
                'mentions_processed': mentions or []
            }
        )

    except Exception as e:
        return _map_exception_to_error(e)


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
        Standardized response dictionary with success/error information
    """
    try:
        params: Dict[str, Any] = {'roomId': room_id}
        if mentioned_people:
            params['mentionedPeople'] = mentioned_people
        if before:
            params['before'] = before
        if before_message:
            params['beforeMessage'] = before_message
        if max_results:
            params['max'] = max_results

        messages_response = webex_api.messages.list(**params)
        messages_list = [_message_to_dict(m) for m in messages_response]

        return create_success_response(
            data={'messages': messages_list, 'room_id': room_id},
            metadata={'count': len(messages_list), 'filters_applied': params}
        )

    except Exception as e:
        return _map_exception_to_error(e)


def delete_webex_message(message_id: str) -> Dict[str, Any]:
    """
    Delete a Webex message.

    Args:
        message_id: ID of the message to delete (required)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        if not message_id:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="message_id is required"
            )
        webex_api.messages.delete(messageId=message_id)
        return create_success_response(
            data={'deleted': True, 'message_id': message_id},
            metadata={'operation': 'delete_message'}
        )
    except Exception as e:
        return _map_exception_to_error(e)


# Space message aliases — "room" and "space" are synonymous in Webex

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
    Note: This is an alias for send_webex_message — "room" and "space" are synonymous in Webex.

    Args:
        space_id: Space ID to send the message to (use this OR to_person_id/to_person_email)
        to_person_id: Person ID to send a direct message to
        to_person_email: Person email to send a direct message to
        text: Plain text message content
        markdown: Markdown formatted message content
        html: HTML formatted message content (for buttons/cards)
        files: URL to attach (single file URL as a string)
        parent_id: Parent message ID for threaded replies

    Returns:
        Standardized response dictionary with success/error information
    """
    return send_webex_message(
        room_id=space_id,
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
    Note: This is an alias for list_webex_messages — "room" and "space" are synonymous in Webex.

    Args:
        space_id: Space ID to get messages from (required)
        mentioned_people: Person ID to filter messages that mention them
        before: Get messages before this date (ISO 8601 format)
        before_message: Get messages before this message ID
        max_results: Maximum number of messages to return (default 50, max 1000)

    Returns:
        Standardized response dictionary with success/error information
    """
    return list_webex_messages(
        room_id=space_id,
        mentioned_people=mentioned_people,
        before=before,
        before_message=before_message,
        max_results=max_results
    )

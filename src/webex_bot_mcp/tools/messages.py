"""
Webex Message management tools.
"""
from typing import Optional, Dict, Any, List
from .common import get_webex_api, create_error_response, create_success_response, WebexErrorCodes, WebexTokenMissingError


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
    if isinstance(e, WebexTokenMissingError):
        return create_error_response(WebexErrorCodes.UNAUTHORIZED, str(e))
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


_SUPPORTED_CARD_VERSIONS = {"1.0", "1.1", "1.2", "1.3"}
_SUPPORTED_CARD_STYLES = {"default", "emphasis", "good", "warning", "attention"}


def _build_adaptive_card_attachment(
    card_body: List[Dict[str, Any]],
    card_actions: Optional[List[Dict[str, Any]]],
    card_version: str,
) -> Dict[str, Any]:
    """Build the Webex-compatible attachment envelope for an Adaptive Card."""
    content: Dict[str, Any] = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": card_version,
        "body": card_body,
    }
    if card_actions:
        content["actions"] = card_actions
    return {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": content,
    }


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
    """Assemble the keyword-argument dict for get_webex_api().messages.create."""
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
        message = get_webex_api().messages.create(**params)

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
        message = get_webex_api().messages.create(**params)

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
        max_limit = max_results if max_results is not None else 50
        messages_response = get_webex_api().messages.list(**params)[:max_limit]
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
        get_webex_api().messages.delete(messageId=message_id)
        return create_success_response(
            data={'deleted': True, 'message_id': message_id},
            metadata={'operation': 'delete_message'}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def send_webex_adaptive_card(
    room_id: Optional[str] = None,
    to_person_id: Optional[str] = None,
    to_person_email: Optional[str] = None,
    card_body: Optional[List[Dict[str, Any]]] = None,
    fallback_text: Optional[str] = None,
    card_actions: Optional[List[Dict[str, Any]]] = None,
    card_version: str = "1.3",
    parent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send an Adaptive Card message to a Webex room or person.

    Adaptive Cards are rich, interactive message attachments. Clients that do not
    support cards will display fallback_text instead.

    IMPORTANT — Webhook limitation: Card action submissions (Action.Submit) are
    delivered to the bot only if a webhook is registered for the
    "attachmentActions" resource on the Webex platform. Without that webhook,
    submissions are silently dropped and the bot never receives them. Inform the
    user of this limitation whenever the card includes interactive actions. To
    receive submissions, a webhook must be created at developer.webex.com or via
    the Webex Webhooks API targeting the bot's public HTTPS endpoint.

    Args:
        room_id: Room ID to send the card to (use this OR to_person_id/to_person_email)
        to_person_id: Person ID to send a direct card to
        to_person_email: Person email to send a direct card to
        card_body: List of Adaptive Card body elements (required, non-empty). Each element
                   must have a "type" field (e.g. "TextBlock", "Image", "ColumnSet").
                   Use build_webex_adaptive_card to generate this from high-level inputs.
        fallback_text: Plain-text fallback shown to clients that do not support cards (required)
        card_actions: Optional list of action objects (Action.OpenUrl, Action.Submit, etc.)
        card_version: Adaptive Card schema version — one of "1.0", "1.1", "1.2", "1.3" (default "1.3")
        parent_id: Parent message ID for threaded replies

    Returns:
        Standardized response dictionary with success/error information

    Examples:
        result = send_webex_adaptive_card(
            room_id="Y2lzY29zcGFyazovL3VzL1JPT00v...",
            fallback_text="Build passed",
            card_body=[
                {"type": "TextBlock", "text": "Build Passed", "weight": "Bolder", "size": "Medium"},
                {"type": "TextBlock", "text": "All 42 tests green", "color": "Good"},
            ],
            card_actions=[
                {"type": "Action.OpenUrl", "title": "View Logs", "url": "https://ci.example.com"}
            ],
        )
    """
    try:
        if not (room_id or to_person_id or to_person_email):
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="Must specify either room_id, to_person_id, or to_person_email",
                details={"required_one_of": ["room_id", "to_person_id", "to_person_email"]}
            )

        if not fallback_text or not fallback_text.strip():
            return create_error_response(
                error_code=WebexErrorCodes.MISSING_REQUIRED_FIELD,
                message="fallback_text is required and must not be blank (displayed to clients that do not support cards)",
                details={"field": "fallback_text"}
            )

        if card_body is None:
            return create_error_response(
                error_code=WebexErrorCodes.MISSING_REQUIRED_FIELD,
                message="card_body is required",
                details={"field": "card_body"}
            )

        if not isinstance(card_body, list) or len(card_body) == 0:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_FIELD_VALUE,
                message="card_body must be a non-empty list of card element dicts",
                details={"field": "card_body"}
            )

        for i, element in enumerate(card_body):
            if not isinstance(element, dict) or "type" not in element:
                return create_error_response(
                    error_code=WebexErrorCodes.INVALID_FIELD_VALUE,
                    message=f"card_body element at index {i} must be a dict with a 'type' field",
                    details={"field": "card_body", "element_index": i}
                )

        if card_version not in _SUPPORTED_CARD_VERSIONS:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_FIELD_VALUE,
                message=f"card_version must be one of {sorted(_SUPPORTED_CARD_VERSIONS)}",
                details={"field": "card_version", "provided": card_version,
                         "allowed": sorted(_SUPPORTED_CARD_VERSIONS)}
            )

        if card_actions:
            for i, action in enumerate(card_actions):
                if not isinstance(action, dict) or "type" not in action:
                    return create_error_response(
                        error_code=WebexErrorCodes.INVALID_FIELD_VALUE,
                        message=f"card_actions element at index {i} must be a dict with a 'type' field",
                        details={"field": "card_actions", "element_index": i}
                    )

        params: Dict[str, Any] = {}
        if room_id:
            params['roomId'] = room_id
        elif to_person_id:
            params['toPersonId'] = to_person_id
        elif to_person_email:
            params['toPersonEmail'] = to_person_email

        params['text'] = fallback_text
        params['attachments'] = [_build_adaptive_card_attachment(card_body, card_actions, card_version)]
        if parent_id:
            params['parentId'] = parent_id

        message = get_webex_api().messages.create(**params)

        return create_success_response(
            data=_message_to_dict(message),
            metadata={
                'operation': 'send_adaptive_card',
                'destination_type': 'room' if room_id else 'direct',
                'card_version': card_version,
                'body_element_count': len(card_body),
                'has_actions': bool(card_actions),
                'is_threaded': bool(parent_id),
            }
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


def send_webex_space_adaptive_card(
    space_id: Optional[str] = None,
    to_person_id: Optional[str] = None,
    to_person_email: Optional[str] = None,
    card_body: Optional[List[Dict[str, Any]]] = None,
    fallback_text: Optional[str] = None,
    card_actions: Optional[List[Dict[str, Any]]] = None,
    card_version: str = "1.3",
    parent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send an Adaptive Card to a Webex space or person.
    Note: This is an alias for send_webex_adaptive_card — "room" and "space" are synonymous in Webex.

    IMPORTANT — Webhook limitation: Card action submissions (Action.Submit) are
    delivered to the bot only if a webhook is registered for the
    "attachmentActions" resource on the Webex platform. Without that webhook,
    submissions are silently dropped and the bot never receives them. Inform the
    user of this limitation whenever the card includes interactive actions.

    Args:
        space_id: Space ID to send the card to (use this OR to_person_id/to_person_email)
        to_person_id: Person ID to send a direct card to
        to_person_email: Person email to send a direct card to
        card_body: List of Adaptive Card body elements (required, non-empty)
        fallback_text: Plain-text fallback for clients that do not support cards (required)
        card_actions: Optional list of action objects
        card_version: Adaptive Card schema version — "1.0", "1.1", "1.2", or "1.3" (default "1.3")
        parent_id: Parent message ID for threaded replies

    Returns:
        Standardized response dictionary with success/error information
    """
    return send_webex_adaptive_card(
        room_id=space_id,
        to_person_id=to_person_id,
        to_person_email=to_person_email,
        card_body=card_body,
        fallback_text=fallback_text,
        card_actions=card_actions,
        card_version=card_version,
        parent_id=parent_id,
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


def build_webex_adaptive_card(
    title: str,
    body_text: Optional[str] = None,
    subtitle: Optional[str] = None,
    image_url: Optional[str] = None,
    facts: Optional[List[Dict[str, str]]] = None,
    actions: Optional[List[Dict[str, Any]]] = None,
    style: str = "default",
) -> Dict[str, Any]:
    """
    Build an Adaptive Card from high-level inputs without hand-crafting the schema.

    Returns card_body and card_actions ready to pass directly to send_webex_adaptive_card.
    Makes no API calls — pure construction only.

    Args:
        title: Card title displayed as bold text (required)
        body_text: Optional body paragraph displayed below the title/subtitle
        subtitle: Optional subtitle displayed below the title in muted text
        image_url: Optional image URL displayed in the card
        facts: Optional list of {"title": "...", "value": "..."} key-value pairs
               displayed as a FactSet table
        actions: Optional list of action dicts. Each must have "type" ("url" or "submit")
                 and "title". URL actions also need "url"; submit actions accept optional "data".
                 Example: [{"type": "url", "title": "Open", "url": "https://example.com"}]
        style: Container accent color — "default", "emphasis", "good", "warning", or "attention"

    Returns:
        Dict with "card_body" and "card_actions" keys ready for send_webex_adaptive_card,
        or a standardized error response dict if validation fails.

    Examples:
        card = build_webex_adaptive_card(
            title="Deployment Complete",
            subtitle="Production • v2.3.1",
            body_text="All health checks passed.",
            facts=[{"title": "Region", "value": "us-east-1"}, {"title": "Duration", "value": "4m 12s"}],
            actions=[{"type": "url", "title": "View Dashboard", "url": "https://dash.example.com"}],
            style="good",
        )
        result = send_webex_adaptive_card(room_id="...", fallback_text="Deployment Complete", **card)
    """
    if not title or not title.strip():
        return create_error_response(
            error_code=WebexErrorCodes.MISSING_REQUIRED_FIELD,
            message="title is required and must not be blank",
            details={"field": "title"}
        )

    if style not in _SUPPORTED_CARD_STYLES:
        return create_error_response(
            error_code=WebexErrorCodes.INVALID_FIELD_VALUE,
            message=f"style must be one of {sorted(_SUPPORTED_CARD_STYLES)}",
            details={"field": "style", "provided": style, "allowed": sorted(_SUPPORTED_CARD_STYLES)}
        )

    if facts:
        for i, fact in enumerate(facts):
            if not isinstance(fact, dict) or "title" not in fact or "value" not in fact:
                return create_error_response(
                    error_code=WebexErrorCodes.INVALID_FIELD_VALUE,
                    message=f"facts element at index {i} must be a dict with 'title' and 'value' keys",
                    details={"field": "facts", "element_index": i}
                )

    if actions:
        for i, action in enumerate(actions):
            if not isinstance(action, dict) or action.get("type") not in {"url", "submit"}:
                return create_error_response(
                    error_code=WebexErrorCodes.INVALID_FIELD_VALUE,
                    message=f"actions element at index {i} must have 'type' of 'url' or 'submit'",
                    details={"field": "actions", "element_index": i, "allowed_types": ["url", "submit"]}
                )
            if not action.get("title"):
                return create_error_response(
                    error_code=WebexErrorCodes.INVALID_FIELD_VALUE,
                    message=f"actions element at index {i} is missing required 'title'",
                    details={"field": "actions", "element_index": i}
                )

    body: List[Dict[str, Any]] = []

    body.append({"type": "TextBlock", "text": title, "weight": "Bolder", "size": "Medium", "wrap": True})

    if subtitle:
        body.append({"type": "TextBlock", "text": subtitle, "isSubtle": True, "spacing": "None", "wrap": True})

    if image_url:
        body.append({"type": "Image", "url": image_url, "size": "Medium"})

    if body_text:
        body.append({"type": "TextBlock", "text": body_text, "wrap": True})

    if facts:
        body.append({
            "type": "FactSet",
            "facts": [{"title": f["title"], "value": f["value"]} for f in facts]
        })

    container: Dict[str, Any] = {"type": "Container", "items": body}
    if style != "default":
        container["style"] = style

    card_actions: List[Dict[str, Any]] = []
    for a in (actions or []):
        if a["type"] == "url":
            card_actions.append({"type": "Action.OpenUrl", "title": a["title"], "url": a["url"]})
        elif a["type"] == "submit":
            card_actions.append({"type": "Action.Submit", "title": a["title"], "data": a.get("data", {})})

    return {"card_body": [container], "card_actions": card_actions}

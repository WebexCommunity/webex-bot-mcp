"""
Webex Webhook management tools.
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
                                     "Webhook not found.")
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


def _webhook_to_dict(w) -> Dict[str, Any]:
    d: Dict[str, Any] = {
        'id': w.id,
        'name': w.name,
        'targetUrl': w.targetUrl,
        'resource': w.resource,
        'event': w.event,
        'status': w.status,
        'created': w.created,
    }
    if getattr(w, 'filter', None):
        d['filter'] = w.filter
    if getattr(w, 'secret', None):
        d['secret'] = w.secret
    if getattr(w, 'orgId', None):
        d['orgId'] = w.orgId
    if getattr(w, 'createdBy', None):
        d['createdBy'] = w.createdBy
    if getattr(w, 'appId', None):
        d['appId'] = w.appId
    if getattr(w, 'ownedBy', None):
        d['ownedBy'] = w.ownedBy
    return d


def list_webex_webhooks(max_results: Optional[int] = None) -> Dict[str, Any]:
    """
    List all webhooks registered to the bot.

    Args:
        max_results: Maximum number of webhooks to return (default 100, max 100)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        params: Dict[str, Any] = {}
        if max_results:
            params['max'] = max_results

        webhooks = [_webhook_to_dict(w) for w in get_webex_api().webhooks.list(**params)]
        return create_success_response(
            data={'webhooks': webhooks},
            metadata={'count': len(webhooks)}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def create_webex_webhook(
    name: str,
    target_url: str,
    resource: str,
    event: str,
    filter: Optional[str] = None,
    secret: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Register a new webhook with the Webex API.

    Args:
        name: A user-friendly name for the webhook (required)
        target_url: The URL that receives POST requests from Webex (required).
                    Must be a publicly reachable HTTPS endpoint.
        resource: The Webex resource type to watch (required). Valid values:
                  - "messages"           — message events in a room
                  - "rooms"              — room created/updated/deleted
                  - "memberships"        — room membership changes
                  - "attachmentActions"  — Adaptive Card form submissions
                  - "meetings"           — meeting lifecycle events
        event: The event type to listen for (required). Valid values:
               - "created"  — resource was created
               - "updated"  — resource was updated
               - "deleted"  — resource was deleted
               - "all"      — all event types for the resource
        filter: Optional filter expression to narrow the events received,
                e.g. "roomId=<id>" for message events in a specific room
        secret: Optional secret used by Webex to sign webhook payloads
                (X-Spark-Signature header). Use this to verify authenticity.

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        if not name:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="name is required"
            )
        if not target_url:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="target_url is required"
            )
        if not resource:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="resource is required"
            )
        if not event:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="event is required"
            )

        params: Dict[str, Any] = {
            'name': name,
            'targetUrl': target_url,
            'resource': resource,
            'event': event,
        }
        if filter is not None:
            params['filter'] = filter
        if secret is not None:
            params['secret'] = secret

        webhook = get_webex_api().webhooks.create(**params)
        return create_success_response(
            data={'webhook': _webhook_to_dict(webhook)},
            metadata={'operation': 'create_webhook'}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def get_webex_webhook(webhook_id: str) -> Dict[str, Any]:
    """
    Get details for a specific webhook.

    Args:
        webhook_id: The webhook ID to retrieve (required)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        if not webhook_id:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="webhook_id is required"
            )
        webhook = get_webex_api().webhooks.get(webhookId=webhook_id)
        return create_success_response(
            data={'webhook': _webhook_to_dict(webhook)},
            metadata={'webhook_id': webhook_id}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def update_webex_webhook(
    webhook_id: str,
    name: str,
    target_url: str,
    secret: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update an existing webhook.

    The Webex API requires both name and target_url on every update, even when
    only one field is changing.

    Args:
        webhook_id: The webhook ID to update (required)
        name: Updated display name for the webhook (required by Webex API)
        target_url: Updated HTTPS target URL (required by Webex API)
        secret: Updated signing secret (optional); pass an empty string to clear it
        status: Updated status — "active" to re-enable or "inactive" to disable (optional)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        if not webhook_id:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="webhook_id is required"
            )
        if not name:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="name is required"
            )
        if not target_url:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="target_url is required"
            )

        params: Dict[str, Any] = {
            'name': name,
            'targetUrl': target_url,
        }
        if secret is not None:
            params['secret'] = secret
        if status is not None:
            params['status'] = status

        webhook = get_webex_api().webhooks.update(webhookId=webhook_id, **params)
        return create_success_response(
            data={'webhook': _webhook_to_dict(webhook)},
            metadata={'operation': 'update_webhook', 'webhook_id': webhook_id}
        )
    except Exception as e:
        return _map_exception_to_error(e)


def delete_webex_webhook(webhook_id: str) -> Dict[str, Any]:
    """
    Delete a webhook by ID.

    Args:
        webhook_id: The webhook ID to delete (required). Use list_webex_webhooks
                    to find the webhook ID.

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        if not webhook_id:
            return create_error_response(
                error_code=WebexErrorCodes.INVALID_ARGUMENTS,
                message="webhook_id is required"
            )
        get_webex_api().webhooks.delete(webhookId=webhook_id)
        return create_success_response(
            data={'deleted': True, 'webhook_id': webhook_id},
            metadata={'operation': 'delete_webhook'}
        )
    except Exception as e:
        return _map_exception_to_error(e)

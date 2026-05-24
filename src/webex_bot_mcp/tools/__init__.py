"""
Webex Bot MCP Tools Package

This package contains all the MCP tools organized by functionality area.
"""

from .rooms import (
    list_webex_rooms, create_webex_room, update_webex_room, get_webex_room, delete_webex_room,
    list_webex_spaces, create_webex_space, update_webex_space, get_webex_space, delete_webex_space,
)

from .messages import (
    send_webex_message, send_webex_message_with_mentions,
    list_webex_messages, delete_webex_message,
    send_webex_space_message, list_webex_space_messages,
    send_webex_adaptive_card, send_webex_space_adaptive_card,
    build_webex_adaptive_card,
)

from .memberships import (
    list_webex_memberships, add_webex_membership, update_webex_membership, delete_webex_membership,
    list_webex_space_memberships, add_webex_space_membership,
)

from .people import (
    get_webex_me, list_webex_people,
)

from .teams import (
    list_webex_teams, get_webex_team,
    update_webex_team, delete_webex_team,
    list_webex_team_memberships, add_webex_team_membership,
    delete_webex_team_membership,
)

from .diagnostics import (
    webex_health_check,
)

from .webhooks import (
    list_webex_webhooks, create_webex_webhook, get_webex_webhook,
    update_webex_webhook, delete_webex_webhook,
)

__all__ = [
    # Room functions
    'list_webex_rooms', 'create_webex_room', 'update_webex_room',
    'get_webex_room', 'delete_webex_room',
    # Space aliases
    'list_webex_spaces', 'create_webex_space', 'update_webex_space',
    'get_webex_space', 'delete_webex_space',
    # Message functions
    'send_webex_message', 'send_webex_message_with_mentions',
    'list_webex_messages', 'delete_webex_message',
    # Space message aliases
    'send_webex_space_message', 'list_webex_space_messages',
    # Adaptive card tools
    'send_webex_adaptive_card', 'send_webex_space_adaptive_card',
    'build_webex_adaptive_card',
    # Membership functions
    'list_webex_memberships', 'add_webex_membership',
    'update_webex_membership', 'delete_webex_membership',
    # Space membership aliases
    'list_webex_space_memberships', 'add_webex_space_membership',
    # People functions
    'get_webex_me', 'list_webex_people',
    # Team functions
    'list_webex_teams', 'get_webex_team',
    'update_webex_team', 'delete_webex_team',
    'list_webex_team_memberships', 'add_webex_team_membership',
    'delete_webex_team_membership',
    # Diagnostic tools
    'webex_health_check',
    # Webhook functions
    'list_webex_webhooks', 'create_webex_webhook', 'get_webex_webhook',
    'update_webex_webhook', 'delete_webex_webhook',
]

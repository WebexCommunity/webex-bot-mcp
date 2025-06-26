"""
Webex Bot MCP Tools Package

This package contains all the MCP tools organized by functionality area.
"""

# Import all tool functions to make them available from the package
from .rooms import (
    list_webex_rooms, create_webex_room, update_webex_room, get_webex_room,
    list_webex_spaces, create_webex_space, update_webex_space, get_webex_space
)

from .messages import (
    send_webex_message, list_webex_messages, send_webex_message_with_mentions,
    send_webex_space_message, list_webex_space_messages
)

from .memberships import (
    list_webex_memberships, add_webex_membership, update_webex_membership,
    list_webex_space_memberships, add_webex_space_membership
)

from .people import (
    get_webex_me, list_webex_people
)

__all__ = [
    # Room functions
    'list_webex_rooms', 'create_webex_room', 'update_webex_room', 'get_webex_room',
    # Space aliases
    'list_webex_spaces', 'create_webex_space', 'update_webex_space', 'get_webex_space',
    # Message functions
    'send_webex_message', 'list_webex_messages', 'send_webex_message_with_mentions',
    # Space message aliases
    'send_webex_space_message', 'list_webex_space_messages',
    # Membership functions
    'list_webex_memberships', 'add_webex_membership', 'update_webex_membership',
    # Space membership aliases
    'list_webex_space_memberships', 'add_webex_space_membership',
    # People functions
    'get_webex_me', 'list_webex_people'
]

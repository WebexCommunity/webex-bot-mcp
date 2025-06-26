# Webex Bot MCP - Tool Structure

This document describes the refactored structure of the Webex Bot MCP tools.

## Project Structure

```
webex-bot-mcp/
├── main.py                    # Main MCP server entry point
├── main_original.py          # Backup of original monolithic main.py
├── tools/                    # Tool modules organized by functionality
│   ├── __init__.py           # Package initialization and exports
│   ├── common.py             # Shared utilities and Webex API initialization
│   ├── rooms.py              # Room/space management tools
│   ├── messages.py           # Message management tools
│   ├── memberships.py        # Membership management tools
│   └── people.py             # People management tools
├── pyproject.toml
├── uv.lock
└── README.md
```

## Tool Organization

### 1. Rooms Module (`tools/rooms.py`)
Handles room and space management (rooms and spaces are synonymous in Webex):

**Room Functions:**
- `list_webex_rooms()` - List rooms with filtering options
- `create_webex_room()` - Create a new room
- `update_webex_room()` - Update room properties
- `get_webex_room()` - Get detailed room information

**Space Aliases:**
- `list_webex_spaces()` - Alias for list_webex_rooms
- `create_webex_space()` - Alias for create_webex_room
- `update_webex_space()` - Alias for update_webex_room
- `get_webex_space()` - Alias for get_webex_room

### 2. Messages Module (`tools/messages.py`)
Handles message sending and retrieval:

**Message Functions:**
- `send_webex_message()` - Send messages to rooms or people
- `list_webex_messages()` - List messages from a room

**Space Message Aliases:**
- `send_webex_space_message()` - Alias for send_webex_message
- `list_webex_space_messages()` - Alias for list_webex_messages

### 3. Memberships Module (`tools/memberships.py`)
Handles room/space membership management:

**Membership Functions:**
- `list_webex_memberships()` - List memberships for rooms or people
- `add_webex_membership()` - Add people to rooms
- `update_webex_membership()` - Update membership properties (moderator/monitor status)

**Space Membership Aliases:**
- `list_webex_space_memberships()` - Alias for list_webex_memberships
- `add_webex_space_membership()` - Alias for add_webex_membership

### 4. People Module (`tools/people.py`)
Handles people and user management:

**People Functions:**
- `get_webex_me()` - Get authenticated user information
- `list_webex_people()` - Search and list people in the organization

### 5. Common Module (`tools/common.py`)
Contains shared utilities and the Webex API client initialization:
- Environment variable loading
- Webex API client setup
- Shared constants and utilities

## Benefits of This Structure

1. **Modularity**: Each functional area is in its own module, making the code easier to navigate and maintain.

2. **Separation of Concerns**: Related functionality is grouped together, making it easier to understand and modify.

3. **Reusability**: Functions can be imported and used independently of the MCP server.

4. **Maintainability**: Changes to specific functionality only affect the relevant module.

5. **Scalability**: New tool categories can be added as separate modules without affecting existing code.

6. **Testing**: Each module can be tested independently.

## Usage

The refactored structure maintains the same external API. All tools are still registered with the MCP server and work exactly as before. The main difference is that the implementation is now spread across multiple focused modules instead of being in one large file.

To run the server:

```bash
python main.py
```

Or with HTTP transport:

```bash
python main.py --transport streamable-http --host localhost --port 8000
```

## Migration Notes

- The original `main.py` has been backed up as `main_original.py`
- All existing functionality is preserved
- Tool function signatures and behavior remain unchanged
- Environment variable requirements are the same
- Dependencies remain the same

"""
Webex Bot MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with Webex APIs.
This server allows you to manage Webex rooms/spaces, send messages, manage memberships, and work with people.

The tools are organized into separate modules:
- rooms: Room/space management (create, update, list, get)
- messages: Message sending and listing
- memberships: Membership management (add, update, list)
- people: People management (get user info, list people)
"""

import os
import argparse
from dotenv import load_dotenv
from fastmcp import FastMCP

# Import all tool functions from the tools package
from tools import (
    # Room functions
    list_webex_rooms, create_webex_room, update_webex_room, get_webex_room,
    # Space aliases  
    list_webex_spaces, create_webex_space, update_webex_space, get_webex_space,
    # Message functions
    send_webex_message, list_webex_messages, send_webex_message_with_mentions,
    # Space message aliases
    send_webex_space_message, list_webex_space_messages,
    # Membership functions
    list_webex_memberships, add_webex_membership, update_webex_membership,
    # Space membership aliases
    list_webex_space_memberships, add_webex_space_membership,
    # People functions
    get_webex_me, list_webex_people
)

# Load environment variables from .env file
load_dotenv()

# Validate required environment variables
webex_access_token = os.getenv("WEBEX_ACCESS_TOKEN")
if not webex_access_token:
    raise ValueError("WEBEX_ACCESS_TOKEN environment variable is required")

# Initialize FastMCP with a name for the bot
mcp = FastMCP("Webex Bot MCP")

# Register all tools with FastMCP
# Room management tools
mcp.tool()(list_webex_rooms)
mcp.tool()(create_webex_room)
mcp.tool()(update_webex_room)
mcp.tool()(get_webex_room)

# Space aliases (same functionality as rooms but with "space" terminology)
mcp.tool()(list_webex_spaces)
mcp.tool()(create_webex_space)
mcp.tool()(update_webex_space)
mcp.tool()(get_webex_space)

# Message management tools
mcp.tool()(send_webex_message)
mcp.tool()(send_webex_message_with_mentions)
mcp.tool()(list_webex_messages)

# Space message aliases
mcp.tool()(send_webex_space_message)
mcp.tool()(list_webex_space_messages)

# Membership management tools
mcp.tool()(list_webex_memberships)
mcp.tool()(add_webex_membership)
mcp.tool()(update_webex_membership)

# Space membership aliases
mcp.tool()(list_webex_space_memberships)
mcp.tool()(add_webex_space_membership)

# People management tools
mcp.tool()(get_webex_me)
mcp.tool()(list_webex_people)


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

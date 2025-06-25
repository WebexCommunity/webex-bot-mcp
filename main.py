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


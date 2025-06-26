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
import json
from datetime import datetime
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


# ========== RESOURCES ==========
# Resources provide contextual information that AI assistants can read

@mcp.resource("webex://help/getting-started")
def webex_getting_started():
    """Getting started guide for Webex Bot MCP"""
    return f"""# Webex Bot MCP - Getting Started Guide

## Overview
This MCP server provides comprehensive Webex Teams integration through a bot account.

## Authentication Status
- Bot Token: {"✅ Configured" if webex_access_token else "❌ Missing"}
- Bot Access: The bot can only interact with rooms/spaces where it has been added as a member

## Quick Start Workflow
1. **List your rooms**: Use `list_webex_rooms()` to see available rooms
2. **Send a message**: Use `send_webex_message()` with room_id and your message
3. **Manage memberships**: Use membership tools to add/remove people from rooms

## Important Notes
- Bots must be added to rooms before they can send messages
- Use either "room" or "space" terminology (they're synonymous in Webex)
- For direct messages, use `to_person_email` instead of `room_id`

## Rate Limits
- Webex API allows up to 10 messages per second
- Consider this when sending bulk messages

Generated at: {datetime.now().isoformat()}
"""

@mcp.resource("webex://help/message-formatting")
def webex_message_formatting():
    """Guide for formatting Webex messages"""
    return """# Webex Message Formatting Guide

## Supported Formats
1. **Plain Text**: Simple text messages
2. **Markdown**: Rich formatting with markdown syntax
3. **HTML**: Advanced formatting for cards and buttons

## Markdown Examples
```markdown
**Bold Text**
*Italic Text*
`Code snippets`
[Links](https://example.com)
- Bullet points
1. Numbered lists
```

## Mentions
- Use `@all` to mention everyone in a room
- Use `@person@example.com` to mention specific people
- Or use the `send_webex_message_with_mentions()` function for proper mention handling

## File Attachments
- Provide URLs to files in the `files` parameter
- Supported: Images, documents, videos (up to 100MB)

## Best Practices
- Keep messages concise and actionable
- Use markdown for better readability
- Test messages in a small room first
- Consider timezone differences for your audience
"""

@mcp.resource("webex://config/current")
def webex_current_config():
    """Current Webex bot configuration and status"""
    # Get basic bot info (this would normally make an API call)
    config_data = {
        "bot_status": "active" if webex_access_token else "unconfigured",
        "token_configured": bool(webex_access_token),
        "available_tools": [
            "Room Management", "Message Sending", "Membership Management", "People Management"
        ],
        "supported_message_formats": ["text", "markdown", "html"],
        "rate_limits": {
            "messages_per_second": 10,
            "api_calls_per_minute": 300
        }
    }
    
    return f"""# Current Webex Bot Configuration

```json
{json.dumps(config_data, indent=2)}
```

## Environment
- WEBEX_ACCESS_TOKEN: {"✅ Set" if webex_access_token else "❌ Not Set"}

## Capabilities
- ✅ Send messages to rooms and individuals
- ✅ Create and manage rooms/spaces
- ✅ Manage room memberships
- ✅ List and search people in organization
- ✅ Support for mentions and file attachments

## Next Steps
{("- Add bot to rooms where you want to send messages" if webex_access_token else "- Configure WEBEX_ACCESS_TOKEN environment variable")}
"""

@mcp.resource("webex://help/troubleshooting")
def webex_troubleshooting():
    """Common issues and troubleshooting guide"""
    return """# Webex Bot Troubleshooting Guide

## Common Issues & Solutions

### 🚫 "Bot not found" or "Unauthorized" Errors
- **Cause**: Invalid or expired bot token
- **Solution**: 
  1. Check your bot token in Webex Developer Portal
  2. Regenerate token if needed
  3. Update WEBEX_ACCESS_TOKEN environment variable

### 📵 "Cannot send message to room" 
- **Cause**: Bot is not a member of the target room
- **Solution**:
  1. Add bot to room manually via Webex app
  2. Use `list_webex_rooms()` to verify bot's room access
  3. Check room permissions (private vs public)

### ⚡ Rate Limiting Issues
- **Cause**: Exceeding Webex API limits (10 msg/sec, 300 calls/min)
- **Solution**:
  1. Add delays between bulk operations
  2. Use exponential backoff for retries
  3. Monitor API response headers for rate limit info

### 👥 Membership Management Failures
- **Cause**: Insufficient permissions or user already exists
- **Solution**:
  1. Ensure bot has moderator privileges for member management
  2. Check if user is already in room before adding
  3. Verify email addresses are valid

### 🔍 "Person not found" Errors
- **Cause**: User not in organization or incorrect email
- **Solution**:
  1. Use `list_webex_people()` to search for users
  2. Verify email format and domain
  3. Check if user has Webex account

### 📁 File Attachment Issues
- **Cause**: File size, format, or URL accessibility
- **Solution**:
  1. Ensure files are < 100MB
  2. Use publicly accessible URLs
  3. Supported formats: images, docs, videos

## Debug Mode
Set environment variable `WEBEX_DEBUG=true` for detailed logging.

## Getting Help
1. Check bot status in Webex Developer Portal
2. Review API documentation at developer.webex.com
3. Test with simple operations first
"""

@mcp.resource("webex://best-practices/security")
def webex_security_best_practices():
    """Security best practices for Webex bot deployment"""
    return """# Webex Bot Security Best Practices

## 🔐 Token Management
- **Never commit tokens to version control**
- Store WEBEX_ACCESS_TOKEN in secure environment variables
- Use separate bots for dev/staging/production

## 🛡️ Access Control
- **Principle of Least Privilege**: Only add bot to necessary rooms
- Regularly audit bot memberships: `list_webex_memberships()`
- Remove bot from unused or archived rooms
- Monitor bot activity logs

## 🔒 Data Protection
- **Message Content**: Be mindful of sensitive data in messages
- **File Sharing**: Validate file content before sharing
- **PII Handling**: Follow data protection regulations (GDPR, etc.)
- **Logging**: Avoid logging sensitive message content

## 🚨 Incident Response
- **Token Compromise**: Immediately regenerate token and update env vars
- **Unauthorized Access**: Review and remove suspicious room memberships
- **Spam Prevention**: Implement rate limiting in your application
- **Monitoring**: Set up alerts for unusual bot activity

## 🔧 Deployment Security
- Use secure hosting (HTTPS only for HTTP transport)
- Implement proper firewall rules
- Keep dependencies updated
- Use container security scanning if containerized

## 📋 Compliance Checklist
- [ ] Bot token stored securely
- [ ] Regular security audits scheduled
- [ ] Access logging implemented
- [ ] Incident response plan documented
- [ ] Data retention policies defined
- [ ] User privacy policies updated
"""

@mcp.resource("webex://examples/use-cases")
def webex_use_cases():
    """Real-world use cases and implementation examples"""
    return """# Webex Bot Use Cases & Examples

## 🚨 Alert & Notification Systems
**Use Case**: Send automated alerts to operations teams
```python
# Emergency alert to operations room
send_webex_message(
    room_id="ops_room_id",
    markdown="🚨 **CRITICAL ALERT** 🚨\\n\\nProduction server CPU > 90%\\n\\n**Actions Required:**\\n- Check server metrics\\n- Scale if needed\\n- Update incident channel",
    mentions=[{"type": "all"}]
)
```

## 📊 Status Updates & Reports
**Use Case**: Daily/weekly automated reports
```python
# Weekly team status update
send_webex_message(
    room_id="team_room_id",
    markdown="## Weekly Team Report\\n\\n✅ **Completed:**\\n- Feature X deployed\\n- Bug fixes released\\n\\n🔄 **In Progress:**\\n- Feature Y development\\n- Performance optimization"
)
```

## 🎫 Help Desk & Support
**Use Case**: Create support rooms for incidents
```python
# Create incident response room
room = create_webex_room(
    title="Incident INC-001 - Database Issues",
    description="Emergency response for database connectivity issues"
)
# Add relevant team members
add_webex_membership(room_id=room['id'], person_email="dba@company.com")
add_webex_membership(room_id=room['id'], person_email="sre@company.com")
```

## 📅 Meeting & Event Management
**Use Case**: Automated meeting coordination
```python
# Pre-meeting room setup
create_webex_room(
    title="Project Alpha - Sprint Planning",
    description="Sprint planning meeting for Project Alpha team"
)
# Send agenda and materials
send_webex_message(
    room_id=room_id,
    markdown="## Sprint Planning Agenda\\n\\n1. Review previous sprint\\n2. Plan upcoming work\\n3. Capacity planning\\n\\n**Materials:** [Sprint Board](link)"
)
```

## 🔄 CI/CD Integration
**Use Case**: Build and deployment notifications
```python
# Deployment success notification
send_webex_message(
    room_id="devops_room",
    markdown="🚀 **Deployment Successful**\\n\\n**Environment:** Production\\n**Version:** v2.1.3\\n**Duration:** 5m 32s\\n\\n[View Metrics](dashboard_link)"
)
```

## 👥 Onboarding & Training
**Use Case**: New employee onboarding automation
```python
# Create onboarding room for new hire
room = create_webex_room(
    title=f"Welcome {new_hire_name} - Onboarding",
    description="Onboarding room for new team member"
)
# Add buddy and HR
add_webex_membership(room_id=room['id'], person_email=buddy_email)
add_webex_membership(room_id=room['id'], person_email="hr@company.com")
```

## 📈 Business Intelligence
**Use Case**: Automated KPI reporting
```python
# Daily metrics to leadership team
send_webex_message(
    room_id="leadership_room",
    markdown="## Daily Business Metrics\\n\\n📊 **Revenue:** $X (+Y% vs yesterday)\\n👥 **Active Users:** X,XXX\\n🎯 **Conversion Rate:** X.X%\\n\\n[Detailed Dashboard](link)"
)
"""


# ========== PROMPTS ==========
# Prompts provide pre-built templates for common use cases

@mcp.prompt("webex-send-announcement")
def webex_send_announcement_prompt():
    """Send an announcement to a Webex room"""
    return {
        "name": "Send Webex Announcement",
        "description": "Create and send a professional announcement message to a Webex room",
        "arguments": [
            {
                "name": "room_name",
                "description": "Name or description of the target room",
                "required": True
            },
            {
                "name": "subject",
                "description": "Subject or title of the announcement",
                "required": True
            },
            {
                "name": "message",
                "description": "Main content of the announcement",
                "required": True
            },
            {
                "name": "urgency",
                "description": "Urgency level (low, medium, high)",
                "required": False
            }
        ],
        "template": """I need to send an announcement to a Webex room. Here are the details:

**Target**: {room_name}
**Subject**: {subject}
**Urgency**: {urgency or "medium"}

**Message Content**:
{message}

Please help me:
1. Find the appropriate room ID for "{room_name}"
2. Format this as a professional announcement with proper markdown
3. Send the message to the room
4. Confirm delivery

Use appropriate formatting like headers, emphasis, and structure to make the announcement clear and professional."""
    }

@mcp.prompt("webex-create-team-room")
def webex_create_team_room_prompt():
    """Create a new team room with proper setup"""
    return {
        "name": "Create Team Room",
        "description": "Create a new Webex team room and set it up with members",
        "arguments": [
            {
                "name": "room_name",
                "description": "Name for the new room",
                "required": True
            },
            {
                "name": "description",
                "description": "Purpose or description of the room",
                "required": False
            },
            {
                "name": "members",
                "description": "List of email addresses to add as members",
                "required": False
            },
            {
                "name": "is_public",
                "description": "Whether the room should be public (true/false)",
                "required": False
            }
        ],
        "template": """I want to create a new Webex team room with the following specifications:

**Room Name**: {room_name}
**Description**: {description or "Team collaboration space"}
**Visibility**: {("Public" if is_public else "Private") if is_public is not None else "Private (default)"}
**Initial Members**: {members or "None specified - will add manually"}

Please help me:
1. Create the room with the specified settings
2. {"Add the specified members to the room" if members else "Provide guidance on adding members later"}
3. Send a welcome message to introduce the room's purpose
4. Provide the room ID and details for future reference

Make sure to follow Webex best practices for room naming and setup."""
    }

@mcp.prompt("webex-bulk-message")
def webex_bulk_message_prompt():
    """Send messages to multiple rooms or people"""
    return {
        "name": "Bulk Message Campaign",
        "description": "Send the same message to multiple Webex rooms or people",
        "arguments": [
            {
                "name": "message_content",
                "description": "The message to send",
                "required": True
            },
            {
                "name": "targets",
                "description": "List of room names or email addresses",
                "required": True
            },
            {
                "name": "message_type",
                "description": "Type of message (announcement, update, reminder, etc.)",
                "required": False
            },
            {
                "name": "delay_between_sends",
                "description": "Seconds to wait between each message (to respect rate limits)",
                "required": False
            }
        ],
        "template": """I need to send a bulk message to multiple Webex destinations:

**Message Type**: {message_type or "General Message"}
**Content**: {message_content}
**Targets**: {targets}
**Rate Limiting**: {delay_between_sends or "Use default (1 second between sends)"}

Please help me:
1. Validate that all target rooms/people exist and are accessible
2. Format the message appropriately for bulk sending
3. Send the message to each target with proper rate limiting
4. Provide a summary of successful and failed deliveries
5. Handle any errors gracefully

Important: Respect Webex rate limits (max 10 messages/second) and ensure the bot has access to all target rooms."""
    }

@mcp.prompt("webex-room-management")
def webex_room_management_prompt():
    """Comprehensive room management workflow"""
    return {
        "name": "Room Management Workflow",
        "description": "Manage Webex room settings, members, and organization",
        "arguments": [
            {
                "name": "room_identifier",
                "description": "Room name or ID to manage",
                "required": True
            },
            {
                "name": "action",
                "description": "Action to perform (audit, cleanup, reorganize, archive)",
                "required": True
            },
            {
                "name": "parameters",
                "description": "Additional parameters for the action",
                "required": False
            }
        ],
        "template": """I need to perform room management tasks for: {room_identifier}

**Action**: {action}
**Parameters**: {parameters or "None specified"}

Please help me with a comprehensive room management workflow:

1. **Room Analysis**:
   - Get current room details and settings
   - List current members and their roles
   - Check recent activity levels

2. **Action Execution** (based on '{action}'):
   - **audit**: Review room health, inactive members, settings
   - **cleanup**: Remove inactive members, update settings
   - **reorganize**: Restructure membership, update description/title
   - **archive**: Prepare room for archival, export important data

3. **Reporting**:
   - Provide before/after comparison
   - List all changes made
   - Suggest follow-up actions

4. **Best Practices**:
   - Ensure proper moderation settings
   - Verify appropriate member permissions
   - Check compliance with organization policies

Focus on maintaining room health and member engagement."""
    }

@mcp.prompt("webex-incident-response")
def webex_incident_response_prompt():
    """Create incident response room and coordinate team response"""
    return {
        "name": "Incident Response Setup",
        "description": "Quickly set up incident response coordination in Webex",
        "arguments": [
            {
                "name": "incident_id",
                "description": "Incident identifier (e.g., INC-001, ALERT-2024-001)",
                "required": True
            },
            {
                "name": "severity",
                "description": "Incident severity (P1-Critical, P2-High, P3-Medium, P4-Low)",
                "required": True
            },
            {
                "name": "description",
                "description": "Brief description of the incident",
                "required": True
            },
            {
                "name": "affected_systems",
                "description": "Comma-separated list of affected systems/services",
                "required": False
            },
            {
                "name": "response_team",
                "description": "Comma-separated list of email addresses for response team",
                "required": False
            }
        ],
        "template": """🚨 INCIDENT RESPONSE ACTIVATION 🚨

**Incident ID**: {incident_id}
**Severity**: {severity}
**Description**: {description}
**Affected Systems**: {affected_systems or "To be determined"}
**Response Team**: {response_team or "Will be assigned"}

Please help me set up incident response coordination:

1. **Create Incident Room**:
   - Title: "🚨 {incident_id} - {description}"
   - Add incident response team members
   - Set up as announcement-only initially

2. **Send Initial Alert**:
   - Notify relevant stakeholders
   - Include incident details and severity
   - Provide status page and monitoring links

3. **Set Up Communication**:
   - Pin important messages (status updates, action items)
   - Create structured update format
   - Establish escalation procedures

4. **Coordinate Response**:
   - Assign incident commander if P1/P2
   - Set up regular status updates schedule
   - Track action items and owners

Follow incident response best practices and ensure proper documentation."""
    }

@mcp.prompt("webex-bot-health-check")
def webex_bot_health_check_prompt():
    """Comprehensive bot health and capability assessment"""
    return {
        "name": "Bot Health Check",
        "description": "Perform comprehensive health check of Webex bot configuration and capabilities",
        "arguments": [
            {
                "name": "check_type",
                "description": "Type of health check (quick, full, security, performance)",
                "required": False
            }
        ],
        "template": """I need to perform a health check on my Webex bot. 

**Check Type**: {check_type or "full"}

Please help me assess the following:

1. **Authentication & Access**:
   - Verify bot token is valid and active
   - Check bot profile information
   - Validate API connectivity

2. **Room Access Audit**:
   - List all rooms bot has access to
   - Identify unused or stale room memberships
   - Check for proper permissions in each room

3. **Message Capabilities**:
   - Test basic message sending
   - Verify markdown and HTML formatting work
   - Test file attachment capabilities
   - Check mention functionality

4. **Rate Limiting Assessment**:
   - Review current API usage patterns
   - Check for any rate limit violations
   - Recommend optimization strategies

5. **Security Review**:
   - Audit room access (remove from unnecessary rooms)
   - Check for overprivileged memberships
   - Review message content guidelines compliance

6. **Performance Metrics**:
   - Message delivery success rates
   - API response times
   - Error rate analysis

Please provide a comprehensive report with actionable recommendations for improvement."""
    }

@mcp.prompt("webex-compliance-audit")
def webex_compliance_audit_prompt():
    """Audit bot usage for compliance and governance"""
    return {
        "name": "Compliance Audit",
        "description": "Audit Webex bot for compliance with organizational policies and regulations",
        "arguments": [
            {
                "name": "audit_scope",
                "description": "Scope of audit (data-retention, access-control, security, full)",
                "required": True
            },
            {
                "name": "compliance_framework",
                "description": "Relevant compliance framework (GDPR, SOX, HIPAA, etc.)",
                "required": False
            },
            {
                "name": "time_period",
                "description": "Time period to audit (last 30 days, 90 days, etc.)",
                "required": False
            }
        ],
        "template": """I need to perform a compliance audit for my Webex bot.

**Audit Scope**: {audit_scope}
**Compliance Framework**: {compliance_framework or "General best practices"}
**Time Period**: {time_period or "Last 90 days"}

Please help me audit the following areas:

1. **Data Handling & Retention**:
   - Review message content policies
   - Check data retention settings
   - Audit file sharing practices
   - Verify PII handling procedures

2. **Access Control & Permissions**:
   - Audit bot room memberships
   - Review user access patterns
   - Check for unauthorized access attempts
   - Validate permission levels

3. **Security Controls**:
   - Token management practices
   - Audit logging capabilities
   - Incident response procedures
   - Vulnerability assessments

4. **Operational Compliance**:
   - Change management documentation
   - Approval workflows for bot modifications
   - Monitoring and alerting setup
   - Business continuity planning

5. **Documentation & Governance**:
   - Policy documentation completeness
   - Training record maintenance
   - Audit trail availability
   - Risk assessment documentation

Provide a compliance report with findings, risk ratings, and remediation recommendations."""
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

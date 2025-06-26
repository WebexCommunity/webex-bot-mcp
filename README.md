# Webex Bot MCP

A comprehensive Model Context Protocol (MCP) server that provides tools, resources, and prompts for interacting with Webex APIs using a Webex bot. This server enables automated messaging, room management, and team collaboration through the Webex platform.

> **Powered by**: This MCP server is built on top of the excellent [Webex Python SDK](https://github.com/WebexCommunity/WebexPythonSDK) by the Webex Community. The SDK provides the robust foundation for all Webex API interactions in this project.

## Features

### 🛠️ Tools (26 available)
- **Room Management**: Create, update, list, and manage Webex rooms/spaces
- **Message Operations**: Send messages with text, markdown, HTML, files, and mentions
- **Membership Management**: Add, remove, and update room memberships
- **People Management**: Search and manage organization users
- **Dual Terminology**: Full support for both "room" and "space" terminology

### 📚 Resources (6 available)
- **Getting Started Guide**: Dynamic setup and authentication status
- **Message Formatting**: Comprehensive formatting examples and best practices
- **Current Configuration**: Live bot status and capabilities
- **Troubleshooting Guide**: Common issues and solutions
- **Security Best Practices**: Production deployment security guidelines
- **Use Cases & Examples**: Real-world implementation patterns

### 🎯 Prompts (7 available)
- **Send Announcement**: Professional announcement templates
- **Create Team Room**: Guided room setup with member management
- **Bulk Message Campaign**: Multi-target messaging with rate limiting
- **Room Management Workflow**: Comprehensive room audit and maintenance
- **Incident Response Setup**: Emergency response coordination
- **Bot Health Check**: Comprehensive bot assessment
- **Compliance Audit**: Governance and policy compliance checking

### 🚀 Production Features
- **Health Monitoring**: Built-in health check endpoints
- **Configuration Management**: Environment-based configuration
- **Container Support**: Docker and Kubernetes deployment ready
- **Security**: Token management, rate limiting, audit logging
- **Observability**: Structured logging and metrics support

## Prerequisites

Before setting up this MCP server, you'll need to create a Webex bot and obtain its access token.

### Creating a Webex Bot

1. **Go to the Webex Developer Portal**:
   - Visit https://developer.webex.com
   - Sign in with your Webex account (create one if you don't have it)

2. **Create a New Bot**:
   - Click on "My Webex Apps" in the top navigation
   - Click "Create a New App"
   - Select "Create a Bot"

3. **Configure Your Bot**:
   - **Bot Name**: Choose a descriptive name (e.g., "Notification Bot", "Alert Bot")
   - **Bot Username**: This will be the bot's unique identifier (e.g., "notificationbot")
   - **Icon**: Upload an icon for your bot (optional but recommended)
   - **Description**: Describe what your bot does
   - Click "Add Bot"

4. **Get Your Bot Access Token**:
   - After creating the bot, you'll see the bot details page
   - **Important**: Copy the "Bot Access Token" immediately - this won't be shown again
   - The token starts with something like `Y2lzY29zcGFyazovL3VzL0FQUExJQ0FUSU9O...`
   - Store this token securely - you'll use it as your `WEBEX_ACCESS_TOKEN`

5. **Bot Limitations to Know**:
   - Bots can only see messages in rooms where they are explicitly added
   - To send messages to a room, the bot must be a member of that room
   - Bots cannot see messages in 1:1 spaces unless the other person messages the bot first
   - Bots have rate limits (typically 10 messages per second)

### Adding Your Bot to Rooms

For your bot to send messages to rooms, it must be added as a member:

1. **For Group Rooms**:
   - Go to the Webex app
   - Open the room where you want the bot to send messages
   - Click the room name at the top
   - Click "People"
   - Click "Add People"
   - Search for your bot's username (e.g., "@notificationbot")
   - Add the bot to the room

2. **For Direct Messages**:
   - Users can start a 1:1 conversation with your bot by searching for its username
   - Or you can send direct messages using the user's email address

## Installing uv

This project uses [uv](https://docs.astral.sh/uv/) for Python package management. You'll need to install uv first.

### Install uv

**macOS and Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Alternative installation methods:**
- **Homebrew (macOS)**: `brew install uv`
- **pip**: `pip install uv`
- **pipx**: `pipx install uv`

### Find uv Path for Claude Desktop

For Claude Desktop configuration, you may need the full path to uv. You can find it using:

```bash
which uv
```

This will return something like:
- **macOS/Linux**: `/Users/username/.cargo/bin/uv` or `/usr/local/bin/uv`
- **Windows**: `C:\Users\username\.cargo\bin\uv.exe`

If `which uv` doesn't work, try:
```bash
whereis uv
```

**Note**: If you installed uv via the official installer, it's typically located at:
- **macOS/Linux**: `~/.cargo/bin/uv`
- **Windows**: `%USERPROFILE%\.cargo\bin\uv.exe`

You can use either the full path or just `uv` in your Claude Desktop configuration if uv is in your system PATH.

## Setup

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Webex bot access token:
   ```
   WEBEX_ACCESS_TOKEN=your_bot_access_token_here
   ```

3. **Test Your Bot Token**:
   You can verify your bot token works by testing it:
   ```bash
   curl -H "Authorization: Bearer YOUR_BOT_TOKEN" \
        https://webexapis.com/v1/people/me
   ```
   This should return your bot's information.

## Common Use Cases for Bot Notifications

This MCP server is particularly useful for:

### System Monitoring & Alerts
- Send server status updates to operations teams
- Alert on system failures or performance issues  
- Notify about backup completion or failures
- Monitor application health and send alerts

### CI/CD Pipeline Notifications
- Notify teams about build successes/failures
- Alert on deployment completions
- Send code review reminders
- Report test results

### Business Process Notifications
- Customer support ticket alerts
- Sales pipeline updates
- Meeting reminders and follow-ups
- Report generation completion

### Integration Examples
- Connect to monitoring tools (Prometheus, Grafana)
- Integrate with ticketing systems (Jira, ServiceNow)
- Hook into CI/CD platforms (Jenkins, GitHub Actions)
- Connect to business applications (Salesforce, HubSpot)

### Best Practices
- Use markdown formatting for better message readability
- Include relevant context and action items in notifications
- Use threaded replies to keep conversations organized
- Set up different bots for different types of notifications
- Test your bot in a dedicated testing room first

## Running the MCP Server

The server supports two transport types: stdio (default) and streamable-http.

### Stdio Transport (Default)

```bash
uv run main.py
```

### Streamable HTTP Transport

```bash
uv run main.py --transport streamable-http
```

You can also customize the host and port for HTTP transport:

```bash
uv run main.py --transport streamable-http --host 0.0.0.0 --port 9000
```

### Command Line Options

- `--transport`: Choose transport type (`stdio` or `streamable-http`, default: `stdio`)
- `--host`: Host to bind to for streamable-http transport (default: `localhost`)
- `--port`: Port to bind to for streamable-http transport (default: `8000`)

Use `--help` to see all available options:

```bash
uv run main.py --help
```

## Claude Desktop Integration

To use this MCP server with Claude Desktop, you'll need to add the server configuration to your Claude Desktop config file.

### Configuration File Location

The Claude Desktop configuration file is located at:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Standard Configuration (Stdio Transport)

Add this configuration to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "webex-bot-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/your/webex-bot-mcp",
        "run",
        "main.py"
      ],
      "env": {
        "WEBEX_ACCESS_TOKEN": "your_webex_bot_access_token_here"
      }
    }
  }
}
```

**Note**: If `uv` is not in your system PATH, replace `"uv"` with the full path to uv (e.g., `"/Users/username/.cargo/bin/uv"` on macOS/Linux or `"C:\\Users\\username\\.cargo\\bin\\uv.exe"` on Windows). See the [Installing uv](#installing-uv) section above for how to find the full path.

### Setup Steps

1. **Replace the placeholder**: Change `your_webex_bot_access_token_here` to your actual Webex bot access token
2. **Update the path**: Change `/path/to/your/webex-bot-mcp` to match your actual project directory location
3. **Copy the configuration**: Add the configuration to your Claude Desktop config file
4. **Restart Claude Desktop**: Close and reopen Claude Desktop to load the new configuration
5. **Test the MCP server**: You can now use the MCP server in Claude Desktop to interact with Webex rooms and send messages

## Sample Prompts for AI Agents

This MCP server enables AI agents to interact with Webex messaging through natural language prompts. Here are practical examples of how agents can utilize the Webex bot:

### Incident Management & Operations

**"Create an incident room and notify the on-call team"**
```
Create a new Webex room called "INCIDENT-2025-001-Database-Outage" and send a message to it with:
- Incident severity: P1
- Affected service: Customer Database
- Initial symptoms: Connection timeouts
- Next steps: Investigating root cause
Then send direct messages to the on-call engineers:
- john.doe@company.com
- jane.smith@company.com
- ops-lead@company.com
Alert them about the new incident room and ask them to join immediately.
```

**"Send maintenance notifications to multiple teams"**
```
Send a maintenance notification to the following Webex rooms:
- "Engineering Team"
- "Customer Support" 
- "Operations"
- "QA Team"

Message should include:
- Maintenance window: Tonight 11 PM - 2 AM EST
- Affected services: Payment processing, user authentication
- Expected downtime: 15 minutes
- Contact person: DevOps team for questions
```

### Automated Monitoring & Alerts

**"Send system health updates to operations rooms"**
```
Check our monitoring dashboard and send a daily health summary to the "Operations" room including:
- Server uptime status
- Database performance metrics
- API response times
- Any alerts or warnings from the last 24 hours
Format it nicely with markdown for easy reading.
```

**"Alert about CI/CD pipeline failures"**
```
The build pipeline for project "customer-portal" just failed on the main branch.
Send an alert to the "Engineering Team" room with:
- Build ID: #2045
- Failed stage: Integration Tests
- Error summary: Database connection timeout
- Assigned to: @backend-team
- Link to build logs: [provide the link]
```

### Customer Support & Communication

**"Escalate support tickets to engineering"**
```
We have a P1 customer issue that needs engineering attention.
Create a room called "CUSTOMER-ISSUE-Netflix-Streaming" and invite:
- support-manager@company.com
- engineering-lead@company.com
- customer-success@company.com

Send the initial context:
- Customer: Netflix
- Issue: Streaming service integration failing
- Impact: 50,000+ users affected
- Ticket ID: SUP-12345
- Customer contact: tech-contact@netflix.com
```

**"Send release notes to stakeholders"**
```
We just deployed version 3.2.1 to production. Send release notes to:
- "Product Team" room
- "Customer Success" room
- "Executive Updates" room

Include:
- New features: Advanced analytics dashboard, mobile push notifications
- Bug fixes: 12 critical issues resolved
- Performance improvements: 30% faster page load times
- Breaking changes: None
- Rollback plan: Available if needed
```

### Team Coordination & Project Management

**"Coordinate cross-team project updates"**
```
Send a weekly project status update to the "Project Alpha" room and individual updates to:
- engineering-manager@company.com
- product-owner@company.com
- design-lead@company.com

Status should include:
- Completed this week: User authentication module
- In progress: Payment integration
- Blocked: Waiting for security review
- Next week's goals: Complete checkout flow
- Risks: Potential delay in third-party API integration
```

**"Schedule and announce team meetings"**
```
Send meeting invitations to the "Architecture Review" room for next Tuesday at 2 PM EST.
Agenda:
- Review microservices communication patterns
- Discuss database sharding strategy
- Plan for Q3 scalability improvements
- Action items from last meeting

Also send individual reminders to:
- senior-architect@company.com
- database-admin@company.com
- platform-engineer@company.com
```

### Compliance & Security Alerts

**"Send security incident notifications"**
```
We detected a potential security incident. Send immediate alerts to:
- "Security Team" room
- "IT Leadership" room
- Direct messages to CISO and IT Director

Include:
- Incident type: Unusual login patterns detected
- Affected systems: Customer portal
- Action taken: Accounts temporarily locked
- Investigation status: In progress
- Next steps: Full security audit initiated
```

**"Compliance audit reminders"**
```
Send SOC 2 audit preparation reminders to compliance stakeholders:
- "Compliance Team" room
- "Engineering Leadership" room
- Individual messages to department heads

Reminder should include:
- Audit date: Next Friday
- Required documentation: Security policies, access logs, change management records
- Point of contact: compliance-officer@company.com
- Preparation checklist: [attach file]
```

### Integration & Automation Examples

**"Multi-channel deployment notifications"**
```
After a successful production deployment, automatically send notifications to:
1. "Engineering Team" room - Technical details and metrics
2. "Product Team" room - Feature summary and user impact
3. "Customer Support" room - What to expect and how to help customers
4. Direct message to release manager with detailed deployment log
```

**"Escalation workflows"**
```
If a P1 incident isn't acknowledged within 15 minutes:
1. Send escalation alert to "Critical Incidents" room
2. Page the on-call manager directly
3. Create a conference bridge and share details
4. Notify executive team if incident exceeds 1 hour
5. Update incident status in all relevant rooms
```

These examples demonstrate how AI agents can use natural language to orchestrate complex Webex messaging workflows, making incident response, team coordination, and operational communications more efficient and automated.

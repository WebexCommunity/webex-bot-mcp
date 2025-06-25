# Webex Bot MCP

A Model Context Protocol (MCP) server that provides tools for interacting with Webex APIs using a Webex bot. This server enables automated messaging and room management through the Webex Teams platform via a bot account.

## Features

- **List Webex Rooms**: Get a list of Webex rooms that the bot has access to, with optional filtering and sorting.
- **Send Webex Messages**: Send messages to Webex rooms or direct messages to users as a bot, with support for text, markdown, HTML, and file attachments.

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

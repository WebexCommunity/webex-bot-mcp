"""Webex Bot MCP — Model Context Protocol server for Webex Teams."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("webex-bot-mcp")
except PackageNotFoundError:
    __version__ = "unknown"

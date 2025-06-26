"""
Common utilities and shared components for Webex Bot MCP tools.
"""
import os
from dotenv import load_dotenv
from webexpythonsdk import WebexAPI

# Load environment variables from .env file
load_dotenv()

# Initialize Webex SDK
webex_access_token = os.getenv("WEBEX_ACCESS_TOKEN")
if not webex_access_token:
    raise ValueError("WEBEX_ACCESS_TOKEN environment variable is required")

webex_api = WebexAPI(access_token=webex_access_token)

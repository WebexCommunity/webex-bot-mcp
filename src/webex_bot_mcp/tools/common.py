"""
Common utilities and shared components for Webex Bot MCP tools.
"""
import os
from datetime import datetime, timezone
from typing import Dict, Any
from webexpythonsdk import WebexAPI

# Server version information
MCP_SERVER_VERSION = "0.1.0"
MCP_SPEC_VERSION = "2024-11-05"

# Error codes for structured error handling
class WebexErrorCodes:
    """Standard error codes for Webex MCP operations."""
    
    # Client errors (4xx)
    INVALID_ARGUMENTS = "E001"
    MISSING_REQUIRED_FIELD = "E002"
    INVALID_FIELD_VALUE = "E003"
    UNAUTHORIZED = "E401"
    FORBIDDEN = "E403"
    NOT_FOUND = "E404"
    
    # Server errors (5xx)
    INTERNAL_ERROR = "E500"
    BAD_GATEWAY = "E502"
    RATE_LIMITED = "E503"
    GATEWAY_TIMEOUT = "E504"
    
    # Webex specific errors
    WEBEX_API_ERROR = "E600"
    NETWORK_ERROR = "E601"
    TOKEN_EXPIRED = "E602"


def create_error_response(
    error_code: str,
    message: str,
    details: Dict[str, Any] = None,
    temporary: bool = False,
    retry_after_seconds: int = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error_code: Error code from WebexErrorCodes
        message: Human-readable error message
        details: Additional error details
        temporary: Whether this is a temporary error that can be retried
        retry_after_seconds: Suggested retry delay for temporary errors
    
    Returns:
        Standardized error response dictionary
    """
    response = {
        'success': False,
        'error_code': error_code,
        'message': message,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'server_version': MCP_SERVER_VERSION
    }
    
    if details:
        response['details'] = details
    
    if temporary:
        response['temporary'] = True
    
    if retry_after_seconds:
        response['retry_after_seconds'] = retry_after_seconds
    
    return response


def create_success_response(data: Dict[str, Any], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data: The main response data
        metadata: Additional metadata about the response
    
    Returns:
        Standardized success response dictionary
    """
    response = {
        'success': True,
        'data': data,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'server_version': MCP_SERVER_VERSION
    }
    
    if metadata:
        response['metadata'] = metadata
    
    return response


class _MissingTokenAPI:
    """Sentinel that gives a clear error when tools are called without a token."""
    def __getattr__(self, name: str):
        raise RuntimeError(
            "WEBEX_ACCESS_TOKEN environment variable is not set. "
            "Set it before using any Webex tools."
        )


webex_access_token = os.getenv("WEBEX_ACCESS_TOKEN")
webex_api = WebexAPI(access_token=webex_access_token) if webex_access_token else _MissingTokenAPI()

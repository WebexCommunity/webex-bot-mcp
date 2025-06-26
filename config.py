"""
Configuration management for Webex Bot MCP Server
Handles environment variables and default settings
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class WebexConfig:
    """Configuration class for Webex Bot MCP Server"""
    
    # Required settings
    access_token: str
    
    # Optional settings with defaults
    debug: bool = False
    rate_limit_messages_per_second: int = 10
    rate_limit_api_calls_per_minute: int = 300
    default_room_type: str = "group"
    default_message_format: str = "markdown"
    org_domain: Optional[str] = None
    validate_ssl: bool = True
    timeout_seconds: int = 30
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "text"
    
    # Monitoring settings
    metrics_enabled: bool = False
    metrics_endpoint: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'WebexConfig':
        """Create configuration from environment variables"""
        
        # Required settings
        access_token = os.getenv("WEBEX_ACCESS_TOKEN")
        if not access_token:
            raise ValueError("WEBEX_ACCESS_TOKEN environment variable is required")
        
        # Optional settings
        return cls(
            access_token=access_token,
            debug=os.getenv("WEBEX_DEBUG", "false").lower() == "true",
            rate_limit_messages_per_second=int(os.getenv("WEBEX_RATE_LIMIT_MESSAGES_PER_SECOND", "10")),
            rate_limit_api_calls_per_minute=int(os.getenv("WEBEX_RATE_LIMIT_API_CALLS_PER_MINUTE", "300")),
            default_room_type=os.getenv("WEBEX_DEFAULT_ROOM_TYPE", "group"),
            default_message_format=os.getenv("WEBEX_DEFAULT_MESSAGE_FORMAT", "markdown"),
            org_domain=os.getenv("WEBEX_ORG_DOMAIN"),
            validate_ssl=os.getenv("WEBEX_VALIDATE_SSL", "true").lower() == "true",
            timeout_seconds=int(os.getenv("WEBEX_TIMEOUT_SECONDS", "30")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_format=os.getenv("LOG_FORMAT", "text"),
            metrics_enabled=os.getenv("METRICS_ENABLED", "false").lower() == "true",
            metrics_endpoint=os.getenv("METRICS_ENDPOINT")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "access_token_configured": bool(self.access_token),
            "debug": self.debug,
            "rate_limits": {
                "messages_per_second": self.rate_limit_messages_per_second,
                "api_calls_per_minute": self.rate_limit_api_calls_per_minute
            },
            "defaults": {
                "room_type": self.default_room_type,
                "message_format": self.default_message_format,
                "org_domain": self.org_domain
            },
            "security": {
                "validate_ssl": self.validate_ssl,
                "timeout_seconds": self.timeout_seconds
            },
            "logging": {
                "level": self.log_level,
                "format": self.log_format
            },
            "monitoring": {
                "metrics_enabled": self.metrics_enabled,
                "metrics_endpoint": self.metrics_endpoint
            }
        }
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        if not self.access_token:
            issues.append("WEBEX_ACCESS_TOKEN is required")
        
        if self.rate_limit_messages_per_second <= 0:
            issues.append("Rate limit for messages per second must be positive")
        
        if self.rate_limit_api_calls_per_minute <= 0:
            issues.append("Rate limit for API calls per minute must be positive")
        
        if self.timeout_seconds <= 0:
            issues.append("Timeout seconds must be positive")
        
        if self.log_level not in ["DEBUG", "INFO", "WARN", "ERROR"]:
            issues.append("Log level must be one of: DEBUG, INFO, WARN, ERROR")
        
        if self.log_format not in ["text", "json"]:
            issues.append("Log format must be 'text' or 'json'")
        
        return issues


def get_config() -> WebexConfig:
    """Get validated configuration from environment"""
    config = WebexConfig.from_env()
    issues = config.validate()
    
    if issues:
        raise ValueError(f"Configuration validation failed: {', '.join(issues)}")
    
    return config

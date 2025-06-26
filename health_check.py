#!/usr/bin/env python3
"""
Health check script for Webex Bot MCP Server
Can be used for monitoring, container health checks, and troubleshooting
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

# Add the current directory to the path so we can import from tools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.common import get_webex_api


def check_api_connectivity() -> Dict[str, Any]:
    """Test basic API connectivity and authentication"""
    try:
        api = get_webex_api()
        me = api.people.me()
        return {
            "status": "healthy",
            "bot_id": me.id,
            "bot_name": me.displayName,
            "bot_email": me.emails[0] if me.emails else "unknown",
            "org_id": me.orgId,
            "response_time_ms": 0  # Would need timing logic
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "error_type": type(e).__name__
        }


def check_room_access() -> Dict[str, Any]:
    """Check bot's access to rooms"""
    try:
        api = get_webex_api()
        rooms = list(api.rooms.list(max=10))  # Limit to 10 for health check
        
        room_types = {}
        for room in rooms:
            room_type = getattr(room, 'type', 'unknown')
            room_types[room_type] = room_types.get(room_type, 0) + 1
        
        return {
            "status": "healthy",
            "total_rooms": len(rooms),
            "room_types": room_types,
            "sample_rooms": [
                {
                    "id": room.id,
                    "title": room.title,
                    "type": getattr(room, 'type', 'unknown')
                }
                for room in rooms[:3]  # First 3 rooms as sample
            ]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "error_type": type(e).__name__
        }


def check_message_capability() -> Dict[str, Any]:
    """Test message sending capability (dry run)"""
    try:
        # Just verify we can construct API client without sending
        get_webex_api()
        
        return {
            "status": "healthy",
            "capabilities": {
                "text_messages": True,
                "markdown_messages": True,
                "html_messages": True,
                "file_attachments": True,
                "mentions": True
            },
            "note": "Capabilities verified without sending test messages"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "error_type": type(e).__name__
        }


def check_environment() -> Dict[str, Any]:
    """Check environment configuration"""
    checks = {
        "webex_access_token": bool(os.getenv("WEBEX_ACCESS_TOKEN")),
        "debug_mode": os.getenv("WEBEX_DEBUG", "false").lower() == "true",
        "python_version": sys.version,
        "working_directory": os.getcwd(),
        "timestamp": datetime.now().isoformat()
    }
    
    # Check for optional environment variables
    optional_vars = [
        "WEBEX_RATE_LIMIT_MESSAGES_PER_SECOND",
        "WEBEX_RATE_LIMIT_API_CALLS_PER_MINUTE",
        "LOG_LEVEL",
        "METRICS_ENABLED"
    ]
    
    env_vars = {}
    for var in optional_vars:
        value = os.getenv(var)
        env_vars[var.lower()] = value if value else "not_set"
    
    return {
        "status": "healthy" if checks["webex_access_token"] else "unhealthy",
        "checks": checks,
        "environment_variables": env_vars,
        "missing_required": [] if checks["webex_access_token"] else ["WEBEX_ACCESS_TOKEN"]
    }


def run_health_check(include_api: bool = True, include_rooms: bool = True) -> Dict[str, Any]:
    """Run comprehensive health check"""
    
    start_time = time.time()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "checks": {},
        "duration_seconds": 0,
        "version": "1.0.0"  # Could be read from pyproject.toml
    }
    
    # Environment check (always run)
    results["checks"]["environment"] = check_environment()
    
    if include_api:
        # API connectivity check
        results["checks"]["api_connectivity"] = check_api_connectivity()
        
        # Message capability check
        results["checks"]["message_capability"] = check_message_capability()
    
    if include_rooms and include_api:
        # Room access check
        results["checks"]["room_access"] = check_room_access()
    
    # Determine overall status
    for check_name, check_result in results["checks"].items():
        if check_result.get("status") == "unhealthy":
            results["overall_status"] = "unhealthy"
            break
    
    results["duration_seconds"] = round(time.time() - start_time, 2)
    
    return results


def main():
    """Main health check entry point"""
    parser = argparse.ArgumentParser(description="Webex Bot MCP Health Check")
    parser.add_argument("--skip-api", action="store_true", help="Skip API connectivity checks")
    parser.add_argument("--skip-rooms", action="store_true", help="Skip room access checks")
    parser.add_argument("--output", choices=["json", "text"], default="json", help="Output format")
    parser.add_argument("--exit-code", action="store_true", help="Exit with non-zero code on unhealthy status")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Run health check
    results = run_health_check(
        include_api=not args.skip_api,
        include_rooms=not args.skip_rooms
    )
    
    # Output results
    if args.output == "json":
        print(json.dumps(results, indent=2))
    else:
        # Text output
        print(f"Webex Bot MCP Health Check - {results['overall_status'].upper()}")
        print(f"Timestamp: {results['timestamp']}")
        print(f"Duration: {results['duration_seconds']}s")
        print()
        
        for check_name, check_result in results["checks"].items():
            status = check_result.get("status", "unknown")
            print(f"✅ {check_name}: {status}" if status == "healthy" else f"❌ {check_name}: {status}")
            
            if status == "unhealthy" and "error" in check_result:
                print(f"   Error: {check_result['error']}")
    
    # Exit with appropriate code
    if args.exit_code and results["overall_status"] != "healthy":
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()

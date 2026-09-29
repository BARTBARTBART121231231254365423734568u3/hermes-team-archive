#!/usr/bin/env python3
"""
System Health Watchdog - Daily security check
Runs daily at midnight UTC and posts to Discord #security channel
"""

import subprocess
import json
import sys
from datetime import datetime

# The prompt for the health check
PROMPT = """System Health Check — report ONLY critical issues to #security.

1. Kanban: Any tasks stuck in "blocked" status? List them.
2. Cron: Any jobs with recent failures? List them.
3. Projects: Any secret leaks in open branches? List them.
4. Deployments: Any services crashed/offline? List them.
5. Gateway: One `hermes gateway run` process running? Confirm or alert.

If all clear, say: ✅ All systems healthy.
If issues found, list only the critical ones — no lengthy explanations."""

def run_health_check():
    """Run the system health check via hermes-agent"""
    try:
        # Run using hermes-agent with the security profile
        result = subprocess.run(
            ['hermes-agent', 'run', '--profile', 'security', '--prompt', PROMPT],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            print(f"Error running health check: {result.stderr}", file=sys.stderr)
            return False
        
        # Output will be posted to Discord by hermes-agent
        print(result.stdout)
        return True
        
    except subprocess.TimeoutExpired:
        print("Health check timed out after 5 minutes", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Failed to run health check: {e}", file=sys.stderr)
        return False

if __name__ == '__main__':
    timestamp = datetime.utcnow().isoformat()
    print(f"[{timestamp}] Running System Health Watchdog...", file=sys.stderr)
    success = run_health_check()
    sys.exit(0 if success else 1)

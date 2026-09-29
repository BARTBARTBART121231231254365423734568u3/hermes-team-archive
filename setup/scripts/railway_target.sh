#!/usr/bin/env bash
# Source this before running any `railway` command against a project OTHER
# than hermes-agent-railway itself:
#
#   source ~/.hermes/scripts/railway_target.sh <project-id> [service-name]
#
# Why this exists: Railway auto-injects RAILWAY_PROJECT_ID, RAILWAY_SERVICE_ID,
# and RAILWAY_ENVIRONMENT_ID into this container's own environment (describing
# hermes-agent-railway itself, since that's what's running). Those env vars
# silently override any `railway link` selection or --project/--service flag
# you pass — `railway status`/`railway variable set`/etc. will target
# hermes-agent-railway even after linking somewhere else, with no error, no
# warning. This is exactly what caused a real production outage: an agent
# meant to set variables on the AuthList bot service, but they landed on
# hermes-agent-railway instead, crash-looping the whole gateway for hours
# before anyone noticed.
#
# This script unsets those vars, links to the requested project/service, and
# then prints `railway status` back to you so the target is visually
# confirmed before you run anything that mutates state. Read that output
# before proceeding — if it doesn't say the project/service you meant, stop.

set -e

if [ -z "$1" ]; then
  echo "Usage: source railway_target.sh <project-id> [service-name]" >&2
  return 1 2>/dev/null || exit 1
fi

unset RAILWAY_PROJECT_ID RAILWAY_ENVIRONMENT_ID RAILWAY_SERVICE_ID \
      RAILWAY_SERVICE_NAME RAILWAY_ENVIRONMENT_NAME RAILWAY_ENVIRONMENT

if [ -n "$2" ]; then
  railway link -p "$1" -s "$2"
else
  railway link -p "$1"
fi

echo ""
echo "=== VERIFY THIS IS THE RIGHT TARGET BEFORE PROCEEDING ==="
railway status
echo "=========================================================="

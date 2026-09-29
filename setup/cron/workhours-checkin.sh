#!/bin/bash
# Work-hours check-in reminder (9am-5pm UTC, weekdays only)
# Runs via cron on scheduler profile

HOUR=$(date -u +%H)
DAY_OF_WEEK=$(date -u +%u)  # 1=Monday, 7=Sunday

# Only run Mon-Fri (1-5) and 9am-5pm UTC (09-16)
if [[ $DAY_OF_WEEK -ge 1 && $DAY_OF_WEEK -le 5 && $HOUR -ge 9 && $HOUR -lt 17 ]]; then
  echo "Work-hours check-in reminder"
  echo ""
  echo "Time to sync up—quick standup on current priorities:"
  echo "  • What's active right now?"
  echo "  • Any blockers to escalate?"
  echo "  • On track for today's goals?"
else
  exit 0  # Outside business hours, silent
fi

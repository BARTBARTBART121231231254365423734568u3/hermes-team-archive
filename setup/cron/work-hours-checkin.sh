#!/bin/bash
# Work-hours check-in reminder
# Runs weekdays during work hours (9am-5pm UTC)

HOUR=$(date -u +%-H)  # %-H avoids leading zeros
DAY=$(date -u +%u)    # 1=Monday, 7=Sunday

# Only run weekdays (1-5) during work hours (9-17)
if [[ $DAY -gt 5 ]] || [[ $HOUR -lt 9 ]] || [[ $HOUR -ge 17 ]]; then
  exit 0
fi

# Brief work-hours check-in
echo "✓ Work-hours check-in: How's progress?"

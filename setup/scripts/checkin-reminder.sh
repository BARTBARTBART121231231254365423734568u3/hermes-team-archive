#!/bin/bash

# Work-hours check-in reminder script
# Runs during business hours (9am-5pm UTC, weekdays)

# Get current time in UTC
HOUR=$(date -u +%H)
DAY=$(date -u +%u)  # 1=Monday, 7=Sunday

# Only run weekdays (Mon-Fri = 1-5)
if [[ $DAY -lt 1 || $DAY -gt 5 ]]; then
  exit 0
fi

# Only run 9am-5pm UTC
if [[ $HOUR -lt 9 || $HOUR -gt 16 ]]; then
  exit 0
fi

echo "⏰ Work-hours check-in reminder"
echo "Review your progress and adjust priorities as needed."

#!/usr/bin/env bash
# railway-probe.sh — capability probe for the Railway CLI.
# Run before claiming "I don't have Railway access".
# Exit codes: 0 = working, 1 = CLI missing, 2 = CLI present but token unauthorized, 3 = other

set +e

echo "=== Railway capability probe ==="
echo ""

# 1. Find the binary
RAILWAY_BIN=""
for candidate in "$(command -v railway)" "$HOME/.railway/bin/railway" "$HOME/.local/bin/railway" "/usr/local/bin/railway"; do
  if [ -x "$candidate" ]; then
    RAILWAY_BIN="$candidate"
    break
  fi
done

if [ -z "$RAILWAY_BIN" ]; then
  echo "FAIL: railway CLI not found in PATH or ~/.railway/bin/"
  echo "Install: npm install -g @railway/cli"
  exit 1
fi

echo "CLI: $RAILWAY_BIN ($("$RAILWAY_BIN" --version 2>&1))"

# 2. Check token presence (no value leakage)
if [ -n "$RAILWAY_TOKEN" ]; then
  echo "RAILWAY_TOKEN: set (len=${#RAILWAY_TOKEN}, prefix=${RAILWAY_TOKEN:0:6}...)"
elif [ -n "$RAILWAY_API_TOKEN" ]; then
  echo "RAILWAY_API_TOKEN: set (len=${#RAILWAY_API_TOKEN})"
else
  echo "WARN: no RAILWAY_TOKEN or RAILWAY_API_TOKEN in env"
fi

# 3. Check ~/.railway config dir
if [ -d "$HOME/.railway" ]; then
  echo "~/.railway/: present"
fi

# 4. Probe with whoami
echo ""
echo "=== whoami probe ==="
WHOAMI_OUT=$("$RAILWAY_BIN" whoami 2>&1)
echo "$WHOAMI_OUT"

if echo "$WHOAMI_OUT" | grep -qiE "unauthorized|not authorized|invalid railway_token"; then
  echo ""
  echo "DIAGNOSIS: Token exists but is unauthorized."
  echo "  - Likely cause: token was created with 'My Projects' scope, not 'No workspace'."
  echo "  - Fix: regenerate at https://railway.app/account/tokens with Workspace='No workspace'."
  exit 2
fi

# 5. If whoami returned something with an @, we're good
if echo "$WHOAMI_OUT" | grep -qE "@"; then
  echo ""
  echo "OK: authenticated."
  exit 0
fi

echo ""
echo "DIAGNOSIS: whoami returned no usable identity. See output above."
exit 3

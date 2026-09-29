#!/usr/bin/env bash
set -euo pipefail

# Upgrades are reviewed builds, never mutable git pulls during startup.
if [ "${AUTO_UPDATE:-false}" = "true" ]; then
  echo "AUTO_UPDATE ignored: deploy a reviewed upstream version instead."
fi

cd /root
mkdir -p /root/.hermes/{cron,sessions,logs,memories,skills,pairing,hooks,image_cache,audio_cache}
python /opt/hermes-ops/provision_profiles.py

git config --global user.email "${HERMES_GIT_EMAIL:-bartbartbart2002@gmail.com}"
git config --global user.name "${HERMES_GIT_NAME:-Thomas}"
if [ -s /root/.hermes/gh-config/hosts.yml ]; then
  unset GH_TOKEN GITHUB_TOKEN
  gh auth setup-git --hostname github.com
fi

exec python /auth_proxy.py

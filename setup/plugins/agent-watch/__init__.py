"""Agent Watch unified plugin package.

The package intentionally exposes no model-facing tools. Its FastAPI backend is
loaded from dashboard/plugin_api.py and its UI from desktop/plugin.js.
"""


def register(ctx):
    """Register no agent capabilities; Agent Watch is a read-only desktop UI."""
    del ctx

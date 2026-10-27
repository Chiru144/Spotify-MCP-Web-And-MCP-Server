from tools.core import mcp, SPOTIFY_SCOPES, get_spotify_client
from tools.registry import register_active_toolsets, get_active_toolsets
from tools.web_app_internal import start_background_web_app
from tools import prompts
import os
import sys

# Register active modular toolsets on-demand (e.g. --toolsets=core)
active_toolsets = get_active_toolsets()
registered_tools = register_active_toolsets(mcp, active_toolsets)

# ASGI application for Cloud Run / Uvicorn HTTP & SSE transport
app = mcp.sse_app()

if __name__ == "__main__":
    import threading
    auto_open = os.getenv("OPEN_BROWSER", "true").strip().lower() not in ("0", "false", "no")
    start_background_web_app(default_port=8000, open_browser=auto_open)
    print(f"Spotify MCP Server active toolsets: {', '.join(active_toolsets)} ({len(registered_tools)} tools registered)", file=sys.stderr)
    try:
        mcp.run()
    except KeyboardInterrupt:
        pass

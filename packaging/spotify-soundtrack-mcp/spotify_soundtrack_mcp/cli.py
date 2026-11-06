"""
cli.py — Entry points for the spotify-soundtrack-mcp package.

Three console scripts are installed:
  spotify-mcp        → run_mcp()        Stdio MCP runner (Claude Desktop, Cursor)
  spotify-soundtrack-mcp → run_server()     SSE server by default; `--transport stdio` runs the stdio server
                                             (the command MCP Registry clients run, e.g. via uvx)
  spotify-mcp-auth   → run_auth()       One-click Spotify PKCE auth helper
"""

import os
import sys
from pathlib import Path


def _setup_env():
    """Load .env from cwd or home config dir; print a hint if missing."""
    from dotenv import load_dotenv

    cwd_env = Path.cwd() / ".env"
    home_env = Path.home() / ".spotify-mcp" / ".env"

    if cwd_env.exists():
        load_dotenv(dotenv_path=cwd_env)
    elif home_env.exists():
        load_dotenv(dotenv_path=home_env)
    else:
        load_dotenv()  # fall back to environment variables

    client_id = os.getenv("SPOTIPY_CLIENT_ID") or os.getenv("SPOTIFY_CLIENT_ID")
    if not client_id:
        print(
            "\n[spotify-mcp] ⚠️  No SPOTIPY_CLIENT_ID found.\n"
            "Create a .env file in your working directory. Example:\n\n"
            "  SPOTIPY_CLIENT_ID=your_client_id_here\n"
            "  SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback\n"
            "  TMDB_API_KEY=your_tmdb_key_here   # optional\n\n"
            "Get your Spotify Client ID at https://developer.spotify.com/dashboard\n",
            file=sys.stderr,
        )


def run_mcp():
    """
    Console script: `spotify-mcp`
    Launches the MCP server over stdio — suitable for Claude Desktop, Cursor,
    and any other MCP client that connects via stdio transport.
    """
    _setup_env()

    from spotify_soundtrack_mcp.tools.core import mcp
    from spotify_soundtrack_mcp.tools.registry import register_active_toolsets, get_active_toolsets
    from spotify_soundtrack_mcp.tools.web_app_internal import start_background_web_app
    from spotify_soundtrack_mcp.tools import prompts  # noqa: F401  registers MCP prompts

    active_toolsets = get_active_toolsets()
    registered_tools = register_active_toolsets(mcp, active_toolsets)

    auto_open = os.getenv("OPEN_BROWSER", "false").strip().lower() in ("1", "true", "yes")
    start_background_web_app(default_port=8000, open_browser=auto_open)

    print(
        f"[spotify-mcp] Starting MCP server — toolsets: {', '.join(active_toolsets)} "
        f"({len(registered_tools)} tools registered)",
        file=sys.stderr,
    )

    try:
        mcp.run()
    except KeyboardInterrupt:
        pass


_TRANSPORTS = ("stdio", "sse")


def get_transport(argv=None, env=None) -> str:
    """Return the transport requested with `--transport X`, `--transport=X` or MCP_TRANSPORT (default sse)."""
    argv = sys.argv[1:] if argv is None else argv
    env = os.environ if env is None else env
    value = None
    for i, arg in enumerate(argv):
        if arg.startswith("--transport="):
            value = arg.split("=", 1)[1]
        elif arg == "--transport" and i + 1 < len(argv):
            value = argv[i + 1]
    value = (value or env.get("MCP_TRANSPORT") or "sse").strip().lower()
    if value not in _TRANSPORTS:
        raise SystemExit(f"[spotify-soundtrack-mcp] Unknown transport '{value}'. Use one of: {', '.join(_TRANSPORTS)}.")
    return value


def run_server():
    """
    Console script: `spotify-soundtrack-mcp`
    Launches a FastAPI/Uvicorn server over HTTP with SSE transport (the default),
    suitable for remote/web-based MCP connections. With `--transport stdio` it
    runs the stdio server instead, exactly like `spotify-mcp`.
    """
    if "--version" in sys.argv[1:]:
        from spotify_soundtrack_mcp import __version__
        print(f"spotify-soundtrack-mcp {__version__}")
        return

    if get_transport() == "stdio":
        run_mcp()
        return

    _setup_env()

    import uvicorn
    from spotify_soundtrack_mcp.tools.core import mcp
    from spotify_soundtrack_mcp.tools.registry import register_active_toolsets, get_active_toolsets
    from spotify_soundtrack_mcp.tools import prompts  # noqa: F401  registers MCP prompts

    active_toolsets = get_active_toolsets()
    registered_tools = register_active_toolsets(mcp, active_toolsets)

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))

    print(
        f"[spotify-soundtrack-mcp] Starting SSE server on {host}:{port} — "
        f"toolsets: {', '.join(active_toolsets)} ({len(registered_tools)} tools)",
        file=sys.stderr,
    )

    app = mcp.sse_app()
    uvicorn.run(app, host=host, port=port)


def run_auth():
    """
    Console script: `spotify-mcp-auth`
    Interactive Spotify PKCE OAuth helper — opens the browser, waits for
    the callback, and saves the token to ~/.spotify-mcp/.spotipyoauthcache
    (or SPOTIFY_MCP_CACHE_PATH).
    """
    _setup_env()

    from spotify_soundtrack_mcp.tools.core import get_spotify_client

    print("=" * 65)
    print(" Spotify MCP — Account Authorization Helper")
    print("=" * 65)
    print("\nStarting Spotify authentication flow...")
    print("Your browser should open automatically.")
    print("If it does not, copy the link shown and paste it into your browser.\n")

    try:
        sp = get_spotify_client(allow_interactive=True)
        user = sp.current_user()
        print("=" * 65)
        print(" [SUCCESS] Successfully authenticated with Spotify!")
        print("=" * 65)
        print(f" Logged in as: {user.get('display_name')} (ID: {user.get('id')})")
        print(f" Email:        {user.get('email', 'N/A')}")
        print(f" Product:      {user.get('product', 'free/premium')}")
        print(f" Country:      {user.get('country', 'N/A')}")
        print("=" * 65)
        print("\nToken saved. Your MCP server is ready to use!\n")
    except Exception as e:
        print("\n" + "!" * 65)
        print(f" [ERROR] Authentication failed: {e}")
        print("!" * 65)
        print("\nTroubleshooting:")
        print("1. Check Spotify Developer Dashboard (https://developer.spotify.com/dashboard)")
        print("   - Under 'Settings' → 'Redirect URIs', ensure:")
        print("     http://127.0.0.1:8888/callback  is added.")
        print("2. If app is in 'Development Mode', add your Spotify email under 'User Management'.\n")
        sys.exit(1)

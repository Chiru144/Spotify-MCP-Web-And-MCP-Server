import os
import re
import threading
import urllib.parse
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Prevent local mcp.py from shadowing the installed 'mcp' package
import sys
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
removed_current = False
if current_dir in sys.path:
    sys.path.remove(current_dir)
    removed_current = True
if '' in sys.path:
    sys.path.remove('')

from mcp.server.mcpserver import MCPServer as FastMCP
from mcp.types import ToolAnnotations

if removed_current and current_dir not in sys.path:
    sys.path.append(current_dir)

# Load environment variables from .env file located alongside server.py
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize FastMCP server
mcp = FastMCP("Spotify Actor Filmography MCP")

# Smart tool decorator: allows modular toolsets to control registration
_orig_tool = mcp.tool

def _smart_tool(*args, **kwargs):
    if os.getenv("MCP_DIRECT_REGISTRATION", "false").lower() in ("1", "true"):
        return _orig_tool(*args, **kwargs)
    if len(args) == 1 and callable(args[0]) and not kwargs:
        return args[0]
    return lambda fn: fn

mcp.tool = _smart_tool

# Define Spotify Scopes needed for playlist creation and playback control
SPOTIFY_SCOPES = [
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
    "user-read-recently-played",
    "user-top-read",
    "user-library-read",
    "user-library-modify",
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-public",
    "playlist-modify-private",
    "user-read-private",
    "user-read-email",
]

TMDB_BASE_URL = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")


def get_spotify_client(allow_interactive: bool = False):
    """Initialize and return an authenticated Spotipy client using PKCE OAuth (no client secret needed).
    In MCP server mode (allow_interactive=False), it never blocks on stdin. If unauthenticated,
    it raises a clean PermissionError containing the authorization URL.
    """
    import spotipy
    from spotipy.oauth2 import SpotifyPKCE

    client_id = os.getenv("SPOTIPY_CLIENT_ID") or os.getenv("SPOTIFY_CLIENT_ID")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI") or os.getenv("SPOTIFY_REDIRECT_URI") or "http://127.0.0.1:8888/callback"

    if not client_id or "your_spotify_client_id" in client_id:
        raise ValueError("Missing SPOTIPY_CLIENT_ID in .env. Please configure your Spotify Client ID.")

    cache_file = Path(__file__).parent.parent / ".spotipyoauthcache"
    cache_path = str(cache_file)

    auth_manager = SpotifyPKCE(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=" ".join(SPOTIFY_SCOPES),
        cache_path=cache_path,
        open_browser=allow_interactive,
    )

    # Auto-healing: If cached token is expired and refresh token is rejected, clear cache
    cached = auth_manager.cache_handler.get_cached_token()
    token = None
    if cached:
        try:
            token = auth_manager.validate_token(cached)
        except Exception:
            token = None
            if cache_file.exists():
                try:
                    cache_file.unlink()
                except Exception:
                    pass

    if not token and not allow_interactive:
        auth_url = auth_manager.get_authorize_url()
        raise PermissionError(
            f"Spotify authentication required. Please connect your account by opening:\n{auth_url}\n"
            f"Or visit http://127.0.0.1:8000 and click 'Connect to Spotify'."
        )



    return spotipy.Spotify(auth_manager=auth_manager)


def _clean_spotify_id(raw_id: str, id_type: str = "") -> str:
    """Extract a bare Spotify ID from a URI, URL, or raw ID string."""
    val = (raw_id or "").strip()
    if "/" in val:
        val = val.split(f"/{id_type}/")[-1] if id_type and f"/{id_type}/" in val else val.split("/")[-1]
    if ":" in val:
        val = val.split(":")[-1]
    return val.split("?")[0].strip()


def _format_duration(ms: int) -> str:
    """Format milliseconds as a M:SS string."""
    sec = (ms or 0) // 1000
    return f"{sec // 60}:{sec % 60:02d}"

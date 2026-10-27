import os
import re
import threading
import urllib.parse
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests
from bs4 import BeautifulSoup
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
import spotipy
from spotipy.oauth2 import SpotifyPKCE

# Import DuckDuckGo Search (support both ddgs and duckduckgo_search packages)
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

# Load environment variables from .env file located alongside server.py
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize FastMCP server
mcp = FastMCP("Spotify Actor Filmography MCP")

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


def get_spotify_client() -> spotipy.Spotify:
    """Initialize and return an authenticated Spotipy client using PKCE OAuth (no client secret needed)."""
    client_id = os.getenv("SPOTIPY_CLIENT_ID") or os.getenv("SPOTIFY_CLIENT_ID")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI") or os.getenv("SPOTIFY_REDIRECT_URI") or "http://127.0.0.1:8888/callback"

    if not client_id or "your_spotify_client_id" in client_id:
        raise ValueError("Missing SPOTIPY_CLIENT_ID in .env. Please configure your Spotify Client ID.")

    cache_path = str(Path(__file__).parent.parent / ".spotipyoauthcache")

    auth_manager = SpotifyPKCE(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=" ".join(SPOTIFY_SCOPES),
        cache_path=cache_path,
        open_browser=True,
    )
    return spotipy.Spotify(auth_manager=auth_manager)



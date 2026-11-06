"""
spotify-soundtrack-mcp
==================
A FastMCP server exposing 115 Spotify + TMDB tools for AI agents.

Quick start::

    # 1. Copy .env.sample to .env and fill in your credentials
    # 2. Authenticate
    spotify-mcp-auth

    # 3. Run the MCP server (stdio – for Claude Desktop / Cursor)
    spotify-mcp

    # 4. Or run the FastAPI/SSE server (web transport)
    spotify-soundtrack-mcp
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("spotify-soundtrack-mcp")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["__version__"]

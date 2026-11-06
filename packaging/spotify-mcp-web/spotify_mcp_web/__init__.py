"""
spotify-mcp-web
===============
Soundtrack Curator & Staging Studio — self-hosted FastAPI web app.

Quick start::

    pip install spotify-mcp-web
    soundtrack-studio
    # → Opens http://127.0.0.1:8000 in your browser
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("spotify-mcp-web")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["__version__"]

"""
app.py — FastAPI application factory for the Soundtrack Studio.

This module wraps the existing mcp-soundtrack-app/server.py logic,
resolving template paths relative to the installed package rather than
the source tree.
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve template directory: prefer the package-bundled templates,
# then fall back to a user-provided path via env var.
# ---------------------------------------------------------------------------
_PKG_DIR = Path(__file__).parent
_TEMPLATES_DIR = _PKG_DIR / "templates"

if not _TEMPLATES_DIR.exists():
    # Allow overriding with SOUNDTRACK_TEMPLATES_DIR env var
    _env_dir = os.getenv("SOUNDTRACK_TEMPLATES_DIR")
    if _env_dir:
        _TEMPLATES_DIR = Path(_env_dir)
    else:
        raise RuntimeError(
            f"[spotify-mcp-web] Templates directory not found at {_TEMPLATES_DIR}.\n"
            "Reinstall the package or set SOUNDTRACK_TEMPLATES_DIR to your templates folder."
        )

# Make the templates path available to the server module
os.environ.setdefault("SOUNDTRACK_TEMPLATES_DIR", str(_TEMPLATES_DIR))


def create_app():
    """
    Create and return the Soundtrack Curator & Staging Studio FastAPI application.

    The app is loaded from the bundled server module. Template paths are
    resolved relative to this installed package.
    """
    import importlib.util

    server_path = _PKG_DIR / "server.py"
    spec = importlib.util.spec_from_file_location("spotify_mcp_web_server", server_path)
    if not spec or not spec.loader:
        raise RuntimeError(f"[spotify-mcp-web] Could not load server module from {server_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    app = getattr(module, "app", None)
    if app is None:
        raise RuntimeError("[spotify-mcp-web] 'app' not found in bundled server module.")

    return app

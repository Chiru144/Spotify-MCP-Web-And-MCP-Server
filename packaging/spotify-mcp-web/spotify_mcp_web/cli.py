"""
cli.py — Entry point for the spotify-mcp-web package.

Console script: `soundtrack-studio`
Launches the Soundtrack Curator & Staging Studio FastAPI app with Uvicorn.
"""

import os
import sys
import webbrowser
import threading
import time
from pathlib import Path


def _setup_env():
    """Load .env from cwd or home config dir."""
    from dotenv import load_dotenv

    cwd_env = Path.cwd() / ".env"
    home_env = Path.home() / ".spotify-mcp" / ".env"

    if cwd_env.exists():
        load_dotenv(dotenv_path=cwd_env)
    elif home_env.exists():
        load_dotenv(dotenv_path=home_env)
    else:
        load_dotenv()

    client_id = os.getenv("SPOTIPY_CLIENT_ID") or os.getenv("SPOTIFY_CLIENT_ID")
    if not client_id:
        print(
            "\n[soundtrack-studio] ⚠️  No SPOTIPY_CLIENT_ID found.\n"
            "Create a .env file in your working directory:\n\n"
            "  SPOTIPY_CLIENT_ID=your_client_id_here\n"
            "  SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback\n\n"
            "Get yours at https://developer.spotify.com/dashboard\n",
            file=sys.stderr,
        )


def run():
    """
    Console script: `soundtrack-studio`

    Starts the Soundtrack Curator & Staging Studio web application on
    http://127.0.0.1:8000 (or the port specified by the PORT env var)
    and opens it in your default browser.
    """
    _setup_env()

    import uvicorn
    from spotify_mcp_web.app import create_app

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    open_browser = os.getenv("OPEN_BROWSER", "true").strip().lower() not in ("0", "false", "no")

    app = create_app()

    url = f"http://{host}:{port}"
    print(f"\n[Soundtrack Studio] Starting at {url}\n", file=sys.stderr)

    if open_browser:
        def _open():
            time.sleep(1.2)
            try:
                webbrowser.open(url)
            except Exception:
                pass
        threading.Thread(target=_open, daemon=True).start()

    uvicorn.run(app, host=host, port=port, log_level="warning", access_log=False)

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import spotipy

SERVER_PATH = Path(__file__).resolve().parent.parent / "mcp-soundtrack-app" / "server.py"


@pytest.fixture(scope="module")
def studio():
    spec = importlib.util.spec_from_file_location("soundtrack_studio_under_test", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def no_client_secret(monkeypatch):
    monkeypatch.delenv("SPOTIPY_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("SPOTIFY_CLIENT_SECRET", raising=False)


def forbidden(*args, **kwargs):
    raise spotipy.SpotifyException(403, -1, "https://api.spotify.com/v1/playlists/x: Forbidden")


def test_shuffle_reports_403_without_client_secret(studio, no_client_secret):
    user_client = MagicMock()
    user_client.playlist_items.side_effect = forbidden

    with patch.object(studio, "_get_valid_user_client", return_value=user_client):
        result = studio.shuffle_playlist(studio.PlaylistShuffleRequest(playlist_id="37i9dQZF1DXcBWIGoYBM5M"))

    assert result == {"success": False, "error": "Spotify refused access (403 Forbidden). This playlist is either private to another user or completely restricted."}


def test_shuffle_reports_403_on_playlist_details_without_client_secret(studio, no_client_secret):
    user_client = MagicMock()
    user_client.playlist_items.return_value = {"items": [{"track": {"uri": "spotify:track:1"}}], "next": None}
    user_client.playlist.side_effect = forbidden

    with patch.object(studio, "_get_valid_user_client", return_value=user_client):
        result = studio.shuffle_playlist(studio.PlaylistShuffleRequest(playlist_id="37i9dQZF1DXcBWIGoYBM5M"))

    assert result["success"] is False
    assert "403 Forbidden" in result["error"]
    assert "client_secret" not in result["error"]

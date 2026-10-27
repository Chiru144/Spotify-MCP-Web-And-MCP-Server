import pytest
from unittest.mock import patch, MagicMock

from tools import library


@pytest.fixture(autouse=True)
def mock_clients():
    with patch("tools.library.get_spotify_client") as sp:
        yield sp


def test_library_tools(mock_clients):
    sp_mock = mock_clients.return_value
    sp_mock.current_user_saved_tracks.return_value = {
        "total": 1,
        "items": [{
            "added_at": "2026-10-26T12:00:00Z",
            "track": {
                "id": "t1", "name": "Liked Song 1", "artists": [{"name": "Artist 1"}],
                "album": {"name": "Album 1"}, "duration_ms": 180000,
                "popularity": 85, "uri": "spotify:track:t1"
            }
        }]
    }
    sp_mock.current_user_saved_tracks_add.return_value = None
    sp_mock.current_user_saved_tracks_delete.return_value = None
    sp_mock.current_user_saved_tracks_contains.return_value = [True, False]

    sp_mock.current_user_saved_albums.return_value = {
        "total": 1,
        "items": [{
            "added_at": "2026-10-26T12:00:00Z",
            "album": {
                "id": "alb1", "name": "Saved Album 1", "artists": [{"name": "Artist 1"}],
                "release_date": "2024-05-01", "total_tracks": 10,
                "popularity": 78, "uri": "spotify:album:alb1"
            }
        }]
    }
    sp_mock.current_user_saved_albums_add.return_value = None
    sp_mock.current_user_saved_albums_delete.return_value = None
    sp_mock.current_user_saved_albums_contains.return_value = [True]

    # 1. spotify_get_saved_tracks
    res_tracks = library.spotify_get_saved_tracks(limit=10)
    assert "Spotify Liked Songs Library" in res_tracks
    assert "Liked Song 1" in res_tracks

    # 2. spotify_save_tracks
    res_save_t = library.spotify_save_tracks(["spotify:track:t1", "t2"])
    assert "Successfully saved 2 track(s)" in res_save_t

    # 3. spotify_remove_saved_tracks
    res_rem_t = library.spotify_remove_saved_tracks(["spotify:track:t1"])
    assert "Successfully removed 1 track(s)" in res_rem_t

    # 4. spotify_check_saved_tracks
    res_check_t = library.spotify_check_saved_tracks(["t1", "t2"])
    assert "Liked Songs Verification" in res_check_t
    assert "🟢 Liked" in res_check_t
    assert "⚪ Not Liked" in res_check_t

    # 5. spotify_get_saved_albums
    res_albums = library.spotify_get_saved_albums(limit=10)
    assert "Spotify Saved Albums Library" in res_albums
    assert "Saved Album 1" in res_albums

    # 6. spotify_save_albums
    res_save_a = library.spotify_save_albums(["spotify:album:alb1"])
    assert "Successfully saved 1 album(s)" in res_save_a

    # 7. spotify_remove_saved_albums
    res_rem_a = library.spotify_remove_saved_albums(["alb1"])
    assert "Successfully removed 1 album(s)" in res_rem_a

    # 8. spotify_check_saved_albums
    res_check_a = library.spotify_check_saved_albums(["alb1"])
    assert "Saved Albums Verification" in res_check_a
    assert "🟢 Saved" in res_check_a

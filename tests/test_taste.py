import pytest
from unittest.mock import patch, MagicMock

from tools import taste

@pytest.fixture(autouse=True)
def mock_clients():
    with patch("tools.taste.get_spotify_client") as sp:
        yield sp

def test_taste_tools(mock_clients):
    sp_mock = mock_clients.return_value
    sp_mock.current_user_top_tracks.return_value = {"items": []}
    sp_mock.current_user_top_artists.return_value = {"items": []}
    sp_mock.audio_features.return_value = []
    sp_mock.search.return_value = {"artists": {"items": [{"id": "1", "name": "Artist"}]}}
    sp_mock.artist_related_artists.return_value = {"artists": []}
    sp_mock.current_user_saved_tracks.return_value = {"items": []}

    taste.get_user_top_tracks()
    taste.get_user_top_songs()
    taste.get_user_top_artists()
    taste.get_audio_features(["spotify:track:123"])
    taste.get_artist_network("Artist Name")
    taste.get_saved_tracks()
    sp_mock.recommendations.return_value = {"tracks": [{"name": "Song 1", "artists": [{"name": "Artist 1"}], "uri": "spotify:track:1"}]}
    taste.get_recommendations(limit=5, seed_genres=["rock"])


def test_stats_analytics_tools(mock_clients):
    sp_mock = mock_clients.return_value
    sp_mock.current_user_top_tracks.return_value = {
        "items": [{
            "id": "t1", "name": "Track 1", "artists": [{"name": "Artist 1"}],
            "album": {"name": "Album 1", "release_date": "2024-01-01"},
            "duration_ms": 200000, "popularity": 80, "uri": "spotify:track:t1", "explicit": False
        }]
    }
    sp_mock.current_user_top_artists.return_value = {
        "items": [{
            "id": "a1", "name": "Artist 1", "genres": ["indie rock", "post-punk"],
            "popularity": 75, "followers": {"total": 500000}, "uri": "spotify:artist:a1"
        }]
    }
    sp_mock.current_user_recently_played.return_value = {
        "items": [{
            "played_at": "2026-10-26T14:30:00.000Z",
            "track": {
                "id": "t1", "name": "Track 1", "artists": [{"name": "Artist 1"}],
                "duration_ms": 200000, "uri": "spotify:track:t1"
            }
        }]
    }
    sp_mock.playlist.return_value = {
        "id": "p1", "name": "Playlist 1", "owner": {"display_name": "User"},
        "tracks": {"total": 1}
    }
    sp_mock.playlist_items.return_value = {
        "items": [{
            "added_at": "2026-10-20T12:00:00Z",
            "track": {"id": "t1", "duration_ms": 200000, "popularity": 80, "explicit": False}
        }]
    }
    sp_mock.audio_features.return_value = [{
        "id": "t1", "energy": 0.8, "valence": 0.6, "danceability": 0.7,
        "acousticness": 0.2, "instrumentalness": 0.1, "tempo": 120.0
    }]
    sp_mock.current_user_playlists.return_value = {
        "items": [{
            "id": "p1", "name": "Playlist 1", "tracks": {"total": 1}
        }]
    }

    # 1. spotify_top_tracks
    res_tracks = taste.spotify_top_tracks(time_range="short_term", limit=5)
    assert "Spotify Top Tracks" in res_tracks
    assert "Track 1" in res_tracks

    # 2. spotify_top_artists
    res_artists = taste.spotify_top_artists(time_range="medium_term", limit=5)
    assert "Spotify Top Artists" in res_artists
    assert "Artist 1" in res_artists

    # 3. spotify_recently_played
    res_recent = taste.spotify_recently_played(limit=5)
    assert "Spotify Recently Played History" in res_recent
    assert "Track 1" in res_recent

    # 4. spotify_listening_patterns
    res_patterns = taste.spotify_listening_patterns()
    assert "Listening Patterns" in res_patterns

    # 5. spotify_taste_profile
    res_taste = taste.spotify_taste_profile()
    assert "Archetype" in res_taste

    # 6. spotify_playlist_compare
    res_compare = taste.spotify_playlist_compare(playlist_ids=["spotify:playlist:p1", "spotify:playlist:p2"])
    assert "Playlist Audio Feature Comparison" in res_compare

    # 7. spotify_playlist_freshness
    res_fresh = taste.spotify_playlist_freshness(limit=10, stale_days_threshold=60)
    assert "Freshness Audit" in res_fresh

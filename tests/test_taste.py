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
    assert "no longer provides audio features" in taste.get_audio_features(["spotify:track:123"])
    assert "Artist" in taste.get_artist_network("Artist Name")
    taste.get_saved_tracks()
    sp_mock.search.return_value = {"tracks": {"items": [{"name": "Song 1", "artists": [{"name": "Artist 1"}], "uri": "spotify:track:1"}]}}
    res = taste.get_recommendations(limit=5, seed_genres=["rock"], target_energy=0.5)
    assert "Song 1" in res
    assert "ignored" in res
    assert sp_mock.search.call_args.kwargs["q"] == 'genre:"rock"'

    # Spotify (2026) switched these off for Development Mode apps; no tool may call them
    for name in ["artist_related_artists", "recommendations", "audio_features"]:
        getattr(sp_mock, name).assert_not_called()


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
    assert "Listener Type" in res_taste
    assert "Indie Rock" in res_taste
    assert "2020s" in res_taste

    # 6. spotify_playlist_compare (no audio features any more)
    res_compare = taste.spotify_playlist_compare(playlist_ids=["spotify:playlist:p1", "spotify:playlist:p2"])
    assert "Multi-Playlist Comparison" in res_compare
    assert "Songs in every playlist: 1" in res_compare
    sp_mock.audio_features.assert_not_called()

    # 7. spotify_playlist_freshness
    res_fresh = taste.spotify_playlist_freshness(limit=10, stale_days_threshold=60)
    assert "Freshness Audit" in res_fresh


def test_taste_profile_without_genres_or_popularity(mock_clients):
    """Spotify now returns null genres and popularity for Development Mode apps."""
    sp_mock = mock_clients.return_value
    sp_mock.current_user_top_artists.return_value = {"items": [{"name": "A", "genres": None, "popularity": None}]}
    sp_mock.current_user_top_tracks.return_value = {"items": [
        {"name": f"T{i}", "artists": [{"name": "A"}], "album": {"release_date": "1999"}, "popularity": None} for i in range(4)
    ]}
    res = taste.spotify_taste_profile()
    assert "Devoted Fan" in res
    assert "Mainstream Index" not in res
    assert "Top Musical Genres" not in res
    assert "A (4 songs)" in res


def test_playlist_compare_skips_unreadable_playlists(mock_clients):
    import spotipy
    sp_mock = mock_clients.return_value
    sp_mock.playlist.side_effect = [
        {"name": "Mine", "tracks": {"total": 1}},
        spotipy.SpotifyException(403, -1, "Forbidden"),
    ]
    sp_mock.playlist_items.return_value = {"items": []}
    res = taste.spotify_playlist_compare(["p1", "p2"])
    assert "Could not read at least 2" in res
    assert "not your playlist" in res

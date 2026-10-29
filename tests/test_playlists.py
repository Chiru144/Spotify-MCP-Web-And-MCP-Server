import json
import pytest
from unittest.mock import patch, MagicMock

from tools import playlists

@pytest.fixture(autouse=True)
def mock_clients():
    with patch("tools.core.get_spotify_client") as sp, \
         patch("tools.playlists.get_actor_filmography") as mock_film, \
         patch("tools.playlists.fetch_tracks_for_movie") as mock_movie_tracks:
        mock_film.return_value = {
            "source": "TMDB", "actor_name": "Tom Hanks",
            "movies": [{"title": "Forrest Gump", "release_date": "1994", "character": "Forrest"}]
        }
        mock_movie_tracks.return_value = [
            {"title": "Track 1", "artists": "Artist 1", "uri": "spotify:track:1", "album": "Album 1"}
        ]
        yield sp

def test_playlists_tools(mock_clients):
    sp_mock = mock_clients.return_value
    sp_mock.current_user.return_value = {"id": "test_user"}
    sp_mock.user_playlist_create.return_value = {"id": "new_id"}
    sp_mock.playlist_tracks.return_value = {"items": [], "next": None}
    
    playlists.create_actor_playlist("Tom Hanks")
    playlists.create_playlist("Test Playlist")
    playlists.shuffle_playlist("playlist_id")
    playlists.add_tracks_to_playlist("playlist_id", ["spotify:track:123"])
    playlists.combine_playlists(["id1", "id2"])
    playlists.dedupe_playlist("playlist_id")
    playlists.add_songs_to_playlist("playlist_id", ["spotify:track:123"])
    playlists.add_movie_songs_to_playlist("playlist_id", "Inception")
    playlists.get_user_playlists()
    playlists.update_playlist("playlist_id", name="New Name")
    playlists.get_playlist_tracks("playlist_id")
    playlists.remove_tracks_from_playlist("playlist_id", ["spotify:track:123"])
    assert "no longer provides audio features" in playlists.reorder_playlist_by_audio_features("playlist_id")

    # Test the 12 standard spotify_* playlist tools
    sp_mock.current_user_playlists.return_value = {"items": [], "total": 0}
    sp_mock.playlist.return_value = {"id": "p1", "name": "P1", "tracks": {"total": 0}, "owner": {"display_name": "User"}}
    sp_mock.playlist_items.return_value = {"items": [], "total": 0}
    sp_mock.playlist_reorder_items.return_value = {"snapshot_id": "snap_1"}
    sp_mock.playlist_cover_image.return_value = [{"url": "http://cover.jpg"}]
    sp_mock.playlist_is_following.return_value = [True, False]

    playlists.spotify_get_my_playlists()
    playlists.spotify_get_playlist("p1")
    playlists.spotify_get_playlist_tracks("p1")
    playlists.spotify_create_playlist("New Playlist")
    playlists.spotify_add_to_playlist("p1", ["spotify:track:123"])
    playlists.spotify_remove_from_playlist("p1", ["spotify:track:123"])
    playlists.spotify_reorder_playlist("p1", range_start=0, insert_before=1)
    playlists.spotify_update_playlist("p1", name="Updated")
    playlists.spotify_follow_playlist("p1")
    playlists.spotify_unfollow_playlist("p1")
    playlists.spotify_get_playlist_cover("p1")
    playlists.spotify_check_playlist_followers("p1", ["user1", "user2"])

    # Test the 8 Playlist Power Tools
    sample_tracks = {
        "items": [
            {
                "track": {
                    "id": "t1",
                    "name": "Song 1",
                    "uri": "spotify:track:1",
                    "artists": [{"name": "Artist A"}],
                    "album": {"name": "Album A", "release_date": "2020"},
                    "duration_ms": 180000,
                    "popularity": 50,
                    "explicit": False
                },
                "added_at": "2023-01-01T00:00:00Z"
            },
            {
                "track": {
                    "id": "t2",
                    "name": "Song 2",
                    "uri": "spotify:track:2",
                    "artists": [{"name": "Artist A"}],
                    "album": {"name": "Album A", "release_date": "2020"},
                    "duration_ms": 200000,
                    "popularity": 60,
                    "explicit": False
                },
                "added_at": "2023-01-02T00:00:00Z"
            }
        ],
        "total": 2,
        "next": None
    }
    sp_mock.playlist_items.return_value = sample_tracks
    sp_mock.current_user_playlists.return_value = {
        "items": [
            {"id": "p1", "name": "Rock Classics"},
            {"id": "p2", "name": "Rock Favorites"}
        ],
        "total": 2
    }

    playlists.spotify_merge_playlists(["p1", "p2"])
    playlists.spotify_merge_playlists(["p1", "p2"], target_playlist_id="p1")
    playlists.spotify_split_playlist_by_artist("p1", min_tracks_per_artist=2, create_playlists=False)
    playlists.spotify_split_playlist_by_artist("p1", min_tracks_per_artist=2, create_playlists=True)
    playlists.spotify_deduplicate_playlist("p1", strategy="uri", dry_run=True)
    playlists.spotify_deduplicate_playlist("p1", strategy="uri", dry_run=False)
    playlists.spotify_export_playlist("p1", include_audio_features=True)
    playlists.spotify_playlist_diff("p1", "p2")
    playlists.spotify_find_playlist_overlaps(limit=20, min_overlap=1)
    playlists.spotify_find_playlist_subsets(limit=20, threshold=0.5)
    playlists.spotify_absorb_playlist("p1", "p2")


def test_playlist_tools_without_removed_endpoints():
    """Spotify (2026) blocks audio features and other users' follower checks for Development Mode apps."""
    sp_mock = MagicMock()
    sp_mock.me.return_value = {"id": "user1"}
    sp_mock.playlist_is_following.return_value = [True]
    sp_mock.playlist.return_value = {"id": "p1", "name": "P1", "owner": {"id": "user1"}, "followers": None}
    with patch("tools.playlists.get_spotify_client", return_value=sp_mock), \
         patch("tools.playlists._fetch_all_playlist_tracks", return_value=[
             {"track": {"id": "t1", "name": "Song 1", "uri": "spotify:track:1", "artists": [], "album": {}}}
         ]):
        assert "no longer provides audio features" in playlists.reorder_playlist_by_audio_features("p1")
        sp_mock.playlist_replace_items.assert_not_called()

        assert "Follows this playlist" in playlists.spotify_check_playlist_followers("p1", ["user1"])
        sp_mock.playlist_is_following.reset_mock()
        assert "no longer provides" in playlists.spotify_check_playlist_followers("p1", ["user1", "user2"])
        sp_mock.playlist_is_following.assert_not_called()

        exported = json.loads(playlists.spotify_export_playlist("p1", include_audio_features=True))
        assert [t["name"] for t in exported["tracks"]] == ["Song 1"]
        assert exported["playlist"]["followers"] == 0
        assert "no longer provides" in exported["audio_features"]

    sp_mock.audio_features.assert_not_called()



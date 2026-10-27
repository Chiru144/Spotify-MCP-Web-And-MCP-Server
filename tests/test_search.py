import pytest
from unittest.mock import patch, MagicMock

from tools import search

@pytest.fixture(autouse=True)
def mock_clients():
    with patch("tools.search.get_spotify_client") as sp, \
         patch("tools.core.get_spotify_client") as core_sp, \
         patch("tools.tmdb_helpers.requests.get") as req, \
         patch("tools.tmdb_helpers.DDGS") as ddgs, \
         patch("tools.search.DDGS") as search_ddgs:
        yield sp, req, ddgs, search_ddgs

def test_search_tools(mock_clients):
    sp_mock = mock_clients[0].return_value
    sp_mock.search.return_value = {"tracks": {"items": []}, "artists": {"items": []}, "playlists": {"items": []}}

    search.search_spotify("query")
    search.search_actor_movies("Tom Hanks")
    search.search_movie_tmdb("Inception")
    search.search_duckduckgo("query")
    search.get_movie_songs("Inception")
    search.get_actor_tmdb_profile("Tom Hanks")
    search.fetch_soundtrack_tracks("Inception")
    search.search_singers("Coldplay")
    search.search_songs("Fix You")


def test_spotify_search_discovery_tools(mock_clients):
    sp_mock = mock_clients[0].return_value
    
    # 1. spotify_search
    sp_mock.search.return_value = {
        "tracks": {"items": [{"id": "trk_1", "name": "Track A", "artists": [{"id": "art_1", "name": "Artist A"}], "album": {"name": "Album A"}, "duration_ms": 180000, "popularity": 80, "uri": "spotify:track:1"}]},
        "artists": {"items": [{"id": "art_1", "name": "Artist A", "genres": ["rock"], "followers": {"total": 50000}, "uri": "spotify:artist:1"}]},
        "albums": {"items": [{"name": "Album A", "artists": [{"name": "Artist A"}], "release_date": "2020", "total_tracks": 10, "uri": "spotify:album:1"}]},
        "playlists": {"items": [{"name": "Playlist A", "owner": {"display_name": "Curator"}, "tracks": {"total": 25}, "uri": "spotify:playlist:1"}]}
    }
    res_search = search.spotify_search("test query", types=["track", "artist", "album", "playlist"], limit=5)
    assert "Spotify Search Results" in res_search
    assert "Track A" in res_search

    # 2. spotify_related_artists
    sp_mock.artist.return_value = {"id": "art_1", "name": "Artist 1", "genres": ["rock"], "followers": {"total": 10000}, "uri": "spotify:artist:art_1"}
    sp_mock.artist_related_artists.return_value = {
        "artists": [{"id": "rel_1", "name": "Related 1", "genres": ["indie"], "popularity": 70, "followers": {"total": 5000}, "uri": "spotify:artist:rel_1"}]
    }
    res_rel = search.spotify_related_artists("spotify:artist:art_1")
    assert "Related Artists for 'Artist 1'" in res_rel
    assert "Related 1" in res_rel

    # 3. spotify_discover_by_artist
    sp_mock.recommendations.return_value = {
        "tracks": [{"name": "Rec Track 1", "artists": [{"name": "Peer 1"}], "album": {"name": "Album P"}, "duration_ms": 200000, "uri": "spotify:track:rec_1"}]
    }
    sp_mock.artist_top_tracks.return_value = {
        "tracks": [{"name": "Top Track 1", "uri": "spotify:track:top_1"}]
    }
    res_disc_art = search.spotify_discover_by_artist("spotify:artist:art_1", limit=10, include_artist_top_tracks=True)
    assert "Artist Network Discovery" in res_disc_art
    assert "Rec Track 1" in res_disc_art
    assert "Top Track 1" in res_disc_art

    # 4. spotify_discover_by_mood
    res_mood = search.spotify_discover_by_mood(mood="chill", target_valence=0.5, target_energy=0.3, limit=10)
    assert "Mood Discovery Results" in res_mood

    # 5. spotify_genre_explorer
    sp_mock.recommendation_genre_seeds.return_value = {"genres": ["ambient", "lo-fi", "synthwave", "rock", "pop", "jazz"]}
    res_genres_all = search.spotify_genre_explorer()
    assert "Spotify Recommendation Genre Seeds" in res_genres_all
    
    res_genres_sample = search.spotify_genre_explorer(genres=["synthwave", "lo-fi"], limit=5)
    assert "Genre Explorer: Sample tracks" in res_genres_sample

    # 6. spotify_discover_deep_cuts
    sp_mock.artist_albums.return_value = {"items": [{"id": "alb_1", "name": "Deep Album"}]}
    sp_mock.album_tracks.return_value = {"items": [{"id": "deep_trk_1", "uri": "spotify:track:deep_1"}]}
    sp_mock.tracks.return_value = {
        "tracks": [{"id": "deep_trk_1", "name": "Hidden Gem", "artists": [{"name": "Artist 1"}], "popularity": 25, "duration_ms": 210000, "uri": "spotify:track:deep_1"}]
    }
    res_deep = search.spotify_discover_deep_cuts("spotify:artist:art_1", max_popularity=40, limit=10)
    assert "Deep Cut Gems" in res_deep
    assert "Hidden Gem" in res_deep

    # 7. spotify_get_recommendations
    sp_mock.recommendations.return_value = {
        "tracks": [{"name": "Smart Rec 1", "artists": [{"name": "Rec Artist"}], "album": {"name": "Rec Album"}, "popularity": 75, "duration_ms": 190000, "uri": "spotify:track:srec_1"}]
    }
    res_recs = search.spotify_get_recommendations(seed_genres=["jazz"], target_energy=0.4, limit=10)
    assert "Spotify Recommendations" in res_recs
    assert "Smart Rec 1" in res_recs


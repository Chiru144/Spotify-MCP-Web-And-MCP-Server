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

    # Spotify (2026) switched these off for Development Mode apps; no tool may call them
    removed = ["artist_related_artists", "recommendations", "recommendation_genre_seeds",
               "artist_top_tracks", "audio_features"]
    seed = {"id": "art_1", "name": "Artist 1", "uri": "spotify:artist:art_1"}
    peer = {"id": "rel_1", "name": "Related 1", "uri": "spotify:artist:rel_1"}
    tracks_by = {
        "Artist 1": [
            {"name": "Top Track 1", "uri": "spotify:track:top_1", "artists": [seed, peer], "album": {"name": "Duets"}, "duration_ms": 200000},
            {"name": "Top Track 2", "uri": "spotify:track:top_2", "artists": [seed], "album": {"name": "Solo"}, "duration_ms": 200000},
        ],
        "Related 1": [
            {"name": "Rec Track 1", "uri": "spotify:track:rec_1", "artists": [peer], "album": {"name": "Album P"}, "duration_ms": 200000},
        ],
    }

    def fake_search(q, type="track", limit=10, **kwargs):
        if type == "artist":
            return {"artists": {"items": [seed]}}
        if type == "album":
            return {"albums": {"items": [{"id": "alb_1", "name": "Deep Album"}]}}
        items = tracks_by.get(q) or [{"name": f"Genre Song {q}", "uri": f"spotify:track:{q}", "artists": [peer], "album": {"name": "G"}, "duration_ms": 1000}]
        return {"tracks": {"items": items}}

    sp_mock.search.side_effect = fake_search
    sp_mock.artist.return_value = seed
    sp_mock.track.return_value = tracks_by["Artist 1"][0]

    # 2. spotify_related_artists -> collaborators
    res_rel = search.spotify_related_artists("spotify:artist:art_1")
    assert "Related Artists for 'Artist 1'" in res_rel
    assert "Related 1" in res_rel
    assert "Shared songs: 1" in res_rel

    # 3. spotify_discover_by_artist -> collaborators' songs plus own search hits
    res_disc_art = search.spotify_discover_by_artist("spotify:artist:art_1", limit=10, include_artist_top_tracks=True)
    assert "Artist Network Discovery" in res_disc_art
    assert "Rec Track 1" in res_disc_art
    assert "Top Track 1" in res_disc_art

    # 4. spotify_discover_by_mood -> genre search; audio targets are reported as ignored
    res_mood = search.spotify_discover_by_mood(mood="chill", target_valence=0.5, target_energy=0.3, limit=10)
    assert "Mood Discovery Results" in res_mood
    assert "chill, lo-fi" in res_mood
    assert "ignored" in res_mood
    assert any('genre:"chill"' in c.kwargs.get("q", "") for c in sp_mock.search.call_args_list)

    # 5. spotify_genre_explorer -> built-in genre list, then genre search
    res_genres_all = search.spotify_genre_explorer()
    assert "Suggested Genres" in res_genres_all
    assert "synthwave" in res_genres_all

    res_genres_sample = search.spotify_genre_explorer(genres=["synthwave", "lo-fi"], limit=5)
    assert "Genre Explorer: Sample tracks" in res_genres_sample

    # 6. spotify_discover_deep_cuts -> album tracks outside the top search results
    sp_mock.artist_albums.return_value = {"items": [{"id": "alb_1", "name": "Deep Album"}]}
    sp_mock.album_tracks.return_value = {"items": [
        {"id": "top_1", "name": "Top Track 1", "uri": "spotify:track:top_1", "artists": [seed]},
        {"id": "deep_1", "name": "Hidden Gem", "uri": "spotify:track:deep_1", "artists": [seed], "duration_ms": 210000},
    ]}
    res_deep = search.spotify_discover_deep_cuts("spotify:artist:art_1", max_popularity=40, limit=10)
    assert "Deep Cut Gems" in res_deep
    assert "Hidden Gem" in res_deep
    assert "Top Track 1" not in res_deep

    # 7. spotify_get_recommendations -> collaborators and genres
    res_recs = search.spotify_get_recommendations(seed_artists=["spotify:artist:art_1"], seed_genres=["jazz"], target_energy=0.4, limit=10)
    assert "Spotify Recommendations" in res_recs
    assert "Rec Track 1" in res_recs
    assert "Genre Song" in res_recs
    assert "ignored" in res_recs

    for name in removed:
        getattr(sp_mock, name).assert_not_called()


def test_search_tools_handle_null_artist_stats(mock_clients):
    """Spotify now returns null popularity, followers and genres for Development Mode apps."""
    sp_mock = mock_clients[0].return_value
    sp_mock.search.return_value = {
        "artists": {"items": [{"id": "a", "name": "Null Stats", "genres": None, "followers": None, "popularity": None, "uri": "spotify:artist:a"}]},
        "tracks": {"items": [{"name": "T", "artists": [{"name": "Null Stats"}], "album": {"name": "A"}, "duration_ms": 1000, "popularity": None, "uri": "spotify:track:t"}]},
    }
    res = search.spotify_search("x", types=["artist", "track"])
    assert "Null Stats" in res and "None/100" not in res and "Error" not in res
    assert "Null Stats" in search.search_singers("x")
    assert "None/100" not in search.search_songs("x")
    assert "Null Stats" in search.search_spotify("x", search_type="artist")


def test_fetch_tracks_for_movie_uses_soundtrack_album(mock_clients):
    from tools import tmdb_helpers
    sp = MagicMock()
    sp.search.side_effect = lambda q, type, limit: (
        {"albums": {"items": [{"id": "A1", "name": "Inception (Music from the Motion Picture)"}]}}
        if type == "album" else {"tracks": {"items": []}}
    )
    sp.album_tracks.return_value = {"items": [
        {"name": "Time", "uri": "spotify:track:1", "artists": [{"name": "Hans Zimmer", "id": "hz"}]}
    ]}

    tracks = tmdb_helpers.fetch_tracks_for_movie(sp, "Inception", max_songs=3)

    assert sp.album_tracks.called
    assert [t["uri"] for t in tracks] == ["spotify:track:1"]


@pytest.mark.parametrize("movie, spotify_name, allow_plain, expected", [
    ("Pushpa 2 - The Rule", "Pushpa 2 The Rule [TELUGU]", True, True),
    ("Pushpa: The Rise", 'Srivalli (From "Pushpa - The Rise")(Telugu)', False, True),
    ("Desamuduru", "Desamudhuru", True, True),
    ("Sye Raa Narasimha Reddy", "Syeraa Narasimha Reddy (Telugu)", True, True),
    ("96", 'Kaathalae Kaathalae (From "96")', False, True),
    ("Happy", "Happy New Year", True, False),
    ("Happy", "The Pursuit of Happyness (Original Motion Picture Soundtrack)", True, False),
    ("Happy", "Happy", False, False),
    ("Vikram", 'Yaanji (From "Vikram Vedha")', False, False),
    ("Master", "Masterpiece (Original Motion Picture Soundtrack)", True, False),
    ("Petta", "Naan Petta Makan (Original Motion Picture Soundtrack)", True, False),
])
def test_soundtrack_title_matches(movie, spotify_name, allow_plain, expected):
    from tools.tmdb_helpers import soundtrack_title_matches
    assert soundtrack_title_matches(movie, spotify_name, allow_plain=allow_plain) is expected


def test_soundtrack_title_matches_rejects_dubbed_language():
    from tools.tmdb_helpers import soundtrack_title_matches
    assert not soundtrack_title_matches("Petta", "Petta (Hindi) [Original Motion Picture Soundtrack]", language="Tamil")
    assert soundtrack_title_matches("Petta", "Petta (Original Motion Picture Soundtrack)", language="Tamil")


HAPPY_ALBUM = {
    "id": "1cIg99EUr991CKfuNiw3yG", "name": "Happy (Original Motion Picture Soundtrack)",
    "album_type": "album", "total_tracks": 2, "release_date": "2006-03-01",
    "tracks": {"items": [
        {"name": "Oka Maaru", "uri": "spotify:track:h1", "artists": [{"name": "Yuvan Shankar Raja", "id": "y"}]},
        {"name": "Happy Happy", "uri": "spotify:track:h2", "artists": [{"name": "Yuvan Shankar Raja", "id": "y"}]},
    ]},
}
HAPPY_WEB_RESULT = [{
    "title": "Happy (Original Motion Picture Soundtrack) - EP by Yuvan ... | Spotify",
    "href": "https://open.spotify.com/album/1cIg99EUr991CKfuNiw3yG", "body": "",
}]


def test_fetch_tracks_for_movie_falls_back_to_web_search(mock_clients):
    from tools import tmdb_helpers
    sp = MagicMock()
    sp.search.side_effect = lambda q, type, limit: (
        {"albums": {"items": [{"id": "x", "name": "Happy New Year", "album_type": "album", "release_date": "2014"}]}}
        if type == "album" else {"tracks": {"items": []}}
    )
    sp.album.return_value = HAPPY_ALBUM

    with patch("tools.tmdb_helpers.ddg_web_search", return_value=HAPPY_WEB_RESULT):
        tracks = tmdb_helpers.fetch_tracks_for_movie(sp, "Happy", max_songs=3, release_year="2006")

    sp.album.assert_called_once_with("1cIg99EUr991CKfuNiw3yG", market=None)
    assert [t["uri"] for t in tracks] == ["spotify:track:h1", "spotify:track:h2"]
    assert tracks[0]["album"] == "Happy (Original Motion Picture Soundtrack)"


def test_fetch_tracks_for_movie_prefers_full_album_over_single_and_score(mock_clients):
    from tools import tmdb_helpers
    sp = MagicMock()
    sp.search.return_value = {"albums": {"items": [
        {"id": "single", "name": 'Marana Mass (From "Petta")', "album_type": "single", "total_tracks": 1},
        {"id": "score", "name": "Petta (Original Background Score)", "album_type": "album", "total_tracks": 30},
        {"id": "ost", "name": "Petta (Original Motion Picture Soundtrack)", "album_type": "album", "total_tracks": 8},
    ]}}
    sp.album_tracks.side_effect = lambda album_id, limit: {"items": [{"name": album_id, "uri": f"spotify:track:{album_id}", "artists": []}]}

    with patch("tools.tmdb_helpers.ddg_web_search") as web:
        tracks = tmdb_helpers.fetch_tracks_for_movie(sp, "Petta", max_songs=3)

    web.assert_not_called()
    assert [t["uri"] for t in tracks] == ["spotify:track:ost", "spotify:track:single", "spotify:track:score"]


def test_studio_soundtrack_lookup_uses_web_search_when_spotify_search_misses(mock_clients):
    sp = MagicMock()
    sp.me.return_value = {"country": "IN"}
    sp.search.side_effect = lambda q, type, limit, market: (
        {"albums": {"items": [{"id": "p", "name": "The Pursuit of Happyness (Original Motion Picture Soundtrack)",
                               "album_type": "album", "release_date": "2006-12-12"}]}}
        if type == "album" else {"tracks": {"items": []}}
    )
    sp.album.return_value = HAPPY_ALBUM
    sp.album_tracks.return_value = HAPPY_ALBUM["tracks"]

    with patch("tools.tmdb_helpers.ddg_web_search", return_value=HAPPY_WEB_RESULT):
        tracks = search.fetch_soundtrack_tracks_with_client("Happy", language_name="Telugu", release_year="2006", sp=sp)

    sp.album_tracks.assert_called_once_with("1cIg99EUr991CKfuNiw3yG", limit=20, market="IN")
    assert {t["album_name"] for t in tracks} == {"Happy (Original Motion Picture Soundtrack)"}

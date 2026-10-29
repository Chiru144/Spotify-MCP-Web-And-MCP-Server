import pytest
from unittest.mock import patch, MagicMock

import asyncio
import server

def test_all_tools_registered():
    tools = asyncio.run(server.mcp.list_tools())
    registered_names = [t.name for t in tools]
    assert len(registered_names) > 30

    # Ensure all 7 Search & Discovery tools are registered
    expected_tools = [
        "spotify_search",
        "spotify_related_artists",
        "spotify_discover_by_artist",
        "spotify_discover_by_mood",
        "spotify_genre_explorer",
        "spotify_discover_deep_cuts",
        "spotify_get_recommendations",
        "spotify_get_track",
        "spotify_get_album",
        "spotify_get_artist",
        "spotify_get_artist_albums",
        "spotify_get_user",
        "fetch_soundtrack_tracks",
        "search_singers",
        "search_songs",
    ]
    for tool_name in expected_tools:
        assert tool_name in registered_names, f"{tool_name} should be registered in MCP"


def test_search_discovery_endpoints():
    import importlib.util
    from pathlib import Path
    from fastapi.testclient import TestClient

    app_server_path = Path(__file__).parent.parent / "mcp-soundtrack-app" / "server.py"
    spec = importlib.util.spec_from_file_location("fastapi_soundtrack_server", str(app_server_path))
    web_server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(web_server)

    client = TestClient(web_server.app)

    with patch.object(web_server, "_get_valid_user_client") as mock_user_client:
        sp_mock = MagicMock()
        mock_user_client.return_value = sp_mock

        # 1. /api/spotify/search
        sp_mock.search.return_value = {
            "tracks": {"items": [{"id": "t1", "name": "Song 1", "artists": [{"name": "Art 1"}], "album": {"name": "Alb 1"}, "duration_ms": 180000, "popularity": 70, "uri": "spotify:track:t1"}]},
            "artists": {"items": [{"id": "a1", "name": "Art 1", "genres": ["pop"], "followers": {"total": 1000}, "uri": "spotify:artist:a1"}]},
            "albums": {"items": [{"id": "alb1", "name": "Alb 1", "artists": [{"name": "Art 1"}], "uri": "spotify:album:alb1"}]},
            "playlists": {"items": [{"id": "p1", "name": "Play 1", "owner": {"display_name": "Curator"}, "uri": "spotify:playlist:p1"}]}
        }
        res = client.get("/api/spotify/search?query=test&types=track,artist,album,playlist&limit=5")
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert len(d["tracks"]) == 1

        # 2. /api/artist/related (collaborators found through search: Spotify removed related-artists)
        sp_mock.artist.return_value = {"id": "a1", "name": "Art 1", "genres": ["pop"], "followers": {"total": 1000}, "uri": "spotify:artist:a1"}
        sp_mock.search.return_value = {
            "tracks": {"items": [
                {"id": "t2", "name": "Duet", "artists": [{"id": "a1", "name": "Art 1"}, {"id": "rel1", "name": "Related 1"}], "album": {"name": "Alb"}, "uri": "spotify:track:t2"},
                {"id": "t3", "name": "Solo", "artists": [{"id": "rel1", "name": "Related 1"}], "album": {"name": "Alb"}, "uri": "spotify:track:t3"},
            ]},
            "artists": {"items": [{"id": "a1", "name": "Art 1"}]},
        }
        res = client.get("/api/artist/related?artist=spotify:artist:a1")
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert [(a["name"], a["shared_tracks"]) for a in d["related_artists"]] == [("Related 1", 1)]

        # 3. /api/discover/by_artist (songs by collaborators, excluding the artist's own hits)
        res = client.get("/api/discover/by_artist?artist=spotify:artist:a1&limit=10")
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert [t["uri"] for t in d["tracks"]] == ["spotify:track:t3"]
        assert [t["uri"] for t in d["top_tracks"]] == ["spotify:track:t2"]

        # 4. /api/discover/by_mood
        res = client.post("/api/discover/by_mood", json={"mood": "chill", "target_valence": 0.5, "limit": 10})
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True

        # 5. /api/genres/explore
        res = client.get("/api/genres/explore")
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert "jazz" in d["all_genres"]

        # 6. /api/discover/deep_cuts
        sp_mock.artist_albums.return_value = {"items": [{"id": "alb_deep", "name": "Deep Album"}]}
        sp_mock.album_tracks.return_value = {"items": [{"id": "deep_trk_1", "name": "Deep Cut", "artists": [{"id": "a1", "name": "Art 1"}], "uri": "spotify:track:deep_1"}]}
        res = client.get("/api/discover/deep_cuts?artist_or_album=Art+1&max_popularity=35&limit=10")
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert len(d["tracks"]) == 1

        # 7. /api/recommendations
        res = client.post("/api/recommendations", json={"seed_genres": ["jazz"], "target_energy": 0.4, "limit": 10})
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True


def test_stats_analytics_registered():
    tools = asyncio.run(server.mcp.list_tools())
    registered_names = [t.name for t in tools]

    expected_tools = [
        "spotify_top_tracks",
        "spotify_top_artists",
        "spotify_recently_played",
        "spotify_listening_patterns",
        "spotify_taste_profile",
        "spotify_playlist_compare",
        "spotify_playlist_freshness",
    ]
    for tool_name in expected_tools:
        assert tool_name in registered_names, f"{tool_name} should be registered in MCP"


def test_stats_analytics_endpoints():
    import importlib.util
    from pathlib import Path
    from fastapi.testclient import TestClient

    app_server_path = Path(__file__).parent.parent / "mcp-soundtrack-app" / "server.py"
    spec = importlib.util.spec_from_file_location("fastapi_soundtrack_server", str(app_server_path))
    web_server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(web_server)

    client = TestClient(web_server.app)

    with patch.object(web_server, "_get_valid_user_client") as mock_user_client:
        sp_mock = MagicMock()
        mock_user_client.return_value = sp_mock

        # Setup mock returns
        sp_mock.current_user_top_tracks.return_value = {
            "items": [{
                "id": "t1", "name": "Song 1", "artists": [{"name": "Art 1"}],
                "album": {"name": "Alb 1", "release_date": "2024"}, "duration_ms": 180000,
                "popularity": 75, "uri": "spotify:track:t1"
            }]
        }
        sp_mock.current_user_top_artists.return_value = {
            "items": [{
                "id": "a1", "name": "Art 1", "genres": ["indie rock"],
                "popularity": 70, "followers": {"total": 5000}, "uri": "spotify:artist:a1"
            }]
        }
        sp_mock.current_user_recently_played.return_value = {
            "items": [{
                "played_at": "2026-10-26T12:00:00Z",
                "track": {
                    "id": "t1", "name": "Song 1", "artists": [{"name": "Art 1"}],
                    "album": {"name": "Alb 1"}, "duration_ms": 180000, "uri": "spotify:track:t1"
                }
            }]
        }
        sp_mock.playlist.return_value = {
            "id": "p1", "name": "Chill List", "owner": {"display_name": "Curator"},
            "tracks": {"total": 1}
        }
        sp_mock.playlist_items.return_value = {
            "items": [{
                "added_at": "2026-10-01T12:00:00Z",
                "track": {"id": "t1", "duration_ms": 180000, "popularity": 75, "explicit": False}
            }]
        }
        sp_mock.audio_features.return_value = [{
            "id": "t1", "energy": 0.65, "valence": 0.55, "danceability": 0.7,
            "acousticness": 0.25, "instrumentalness": 0.05, "tempo": 115.0
        }]
        sp_mock.current_user_playlists.return_value = {
            "items": [{
                "id": "p1", "name": "Chill List", "tracks": {"total": 1}
            }]
        }

        # 1. /api/stats/top_tracks
        res = client.get("/api/stats/top_tracks?time_range=short_term&limit=10")
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert len(d["tracks"]) == 1

        # 2. /api/stats/top_artists
        res = client.get("/api/stats/top_artists?time_range=medium_term&limit=10")
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert len(d["artists"]) == 1

        # 3. /api/stats/recently_played
        res = client.get("/api/stats/recently_played?limit=10")
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert len(d["history"]) == 1

        # 4. /api/stats/listening_patterns
        res = client.get("/api/stats/listening_patterns?limit=20")
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert "peak_hour" in d

        # 5. /api/stats/taste_profile
        res = client.get("/api/stats/taste_profile?time_range=medium_term")
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert "archetype" in d

        # 6. /api/playlist/compare (POST & GET)
        res = client.post("/api/playlist/compare", json={"playlist_ids": ["p1", "p2"]})
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True

        res_get = client.get("/api/playlist/compare?playlist_ids=p1,p2")
        assert res_get.status_code == 200
        d_get = res_get.json()
        assert d_get["success"] is True

        # 7. /api/playlist/freshness
        res = client.get("/api/playlist/freshness?limit=10&stale_days_threshold=60")
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert "fresh_count" in d


def test_library_tools_registered():
    tools = asyncio.run(server.mcp.list_tools())
    registered_names = [t.name for t in tools]

    expected_tools = [
        "spotify_get_saved_tracks",
        "spotify_save_tracks",
        "spotify_remove_saved_tracks",
        "spotify_check_saved_tracks",
        "spotify_get_saved_albums",
        "spotify_save_albums",
        "spotify_remove_saved_albums",
        "spotify_check_saved_albums",
    ]
    for tool_name in expected_tools:
        assert tool_name in registered_names, f"{tool_name} should be registered in MCP"


def test_library_endpoints():
    import importlib.util
    from pathlib import Path
    from fastapi.testclient import TestClient

    app_server_path = Path(__file__).parent.parent / "mcp-soundtrack-app" / "server.py"
    spec = importlib.util.spec_from_file_location("fastapi_soundtrack_server", str(app_server_path))
    web_server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(web_server)

    client = TestClient(web_server.app)

    with patch.object(web_server, "_get_valid_user_client") as mock_user_client:
        sp_mock = MagicMock()
        mock_user_client.return_value = sp_mock

        # Setup mock returns
        sp_mock.current_user_saved_tracks.return_value = {
            "total": 1,
            "items": [{
                "added_at": "2026-10-26T12:00:00Z",
                "track": {
                    "id": "t1", "name": "Song 1", "artists": [{"name": "Art 1"}],
                    "album": {"name": "Alb 1"}, "duration_ms": 180000,
                    "popularity": 80, "uri": "spotify:track:t1"
                }
            }]
        }
        sp_mock.current_user_saved_tracks_add.return_value = None
        sp_mock.current_user_saved_tracks_delete.return_value = None
        sp_mock.current_user_saved_tracks_contains.return_value = [True]

        sp_mock.current_user_saved_albums.return_value = {
            "total": 1,
            "items": [{
                "added_at": "2026-10-26T12:00:00Z",
                "album": {
                    "id": "alb1", "name": "Alb 1", "artists": [{"name": "Art 1"}],
                    "release_date": "2024", "total_tracks": 10,
                    "popularity": 75, "uri": "spotify:album:alb1"
                }
            }]
        }
        sp_mock.current_user_saved_albums_add.return_value = None
        sp_mock.current_user_saved_albums_delete.return_value = None
        sp_mock.current_user_saved_albums_contains.return_value = [True]

        # 1. /api/library/tracks (GET)
        res = client.get("/api/library/tracks?limit=10&offset=0")
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert len(d["tracks"]) == 1

        # 2. /api/library/tracks (POST)
        res = client.post("/api/library/tracks", json={"track_ids": ["spotify:track:t1"]})
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert d["saved_count"] == 1

        # 3. /api/library/tracks (DELETE)
        res = client.request("DELETE", "/api/library/tracks", json={"track_ids": ["spotify:track:t1"]})
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert d["removed_count"] == 1

        # 4. /api/library/tracks/check (POST & GET)
        res = client.post("/api/library/tracks/check", json={"track_ids": ["t1"]})
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert d["results"][0]["is_saved"] is True

        res_get = client.get("/api/library/tracks/check?track_ids=t1")
        assert res_get.status_code == 200
        d_get = res_get.json()
        assert d_get["success"] is True

        # 5. /api/library/albums (GET)
        res = client.get("/api/library/albums?limit=10&offset=0")
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert len(d["albums"]) == 1

        # 6. /api/library/albums (POST)
        res = client.post("/api/library/albums", json={"album_ids": ["spotify:album:alb1"]})
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert d["saved_count"] == 1

        # 7. /api/library/albums (DELETE)
        res = client.request("DELETE", "/api/library/albums", json={"album_ids": ["spotify:album:alb1"]})
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert d["removed_count"] == 1

        # 8. /api/library/albums/check (POST & GET)
        res = client.post("/api/library/albums/check", json={"album_ids": ["alb1"]})
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert d["results"][0]["is_saved"] is True

        res_get = client.get("/api/library/albums/check?album_ids=alb1")
        assert res_get.status_code == 200
        d_get = res_get.json()
        assert d_get["success"] is True


def test_browse_endpoints():
    import importlib.util
    from pathlib import Path
    from fastapi.testclient import TestClient

    app_server_path = Path(__file__).parent.parent / "mcp-soundtrack-app" / "server.py"
    spec = importlib.util.spec_from_file_location("fastapi_soundtrack_server", str(app_server_path))
    web_server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(web_server)

    client = TestClient(web_server.app)

    with patch.object(web_server, "_get_valid_user_client") as mock_user_client:
        sp_mock = MagicMock()
        mock_user_client.return_value = sp_mock

        # 1. /api/browse/track
        sp_mock.track.return_value = {
            "id": "t1", "name": "Track One", "artists": [{"name": "Queen"}],
            "album": {"id": "alb1", "name": "Album One", "release_date": "1975-11-21"},
            "duration_ms": 354000, "popularity": 90, "explicit": False,
            "track_number": 1, "disc_number": 1,
            "external_ids": {"isrc": "GBUM71029606"},
            "preview_url": "https://example.com/prev.mp3",
            "uri": "spotify:track:t1",
            "external_urls": {"spotify": "https://open.spotify.com/track/t1"}
        }
        res = client.get("/api/browse/track?track_id=spotify:track:t1")
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert d["track"]["name"] == "Track One"
        assert d["track"]["isrc"] == "GBUM71029606"

        # 2. /api/browse/album
        sp_mock.album.return_value = {
            "id": "alb1", "name": "Album One", "artists": [{"name": "Queen"}],
            "release_date": "1975-11-21", "total_tracks": 1, "label": "EMI",
            "popularity": 85, "genres": ["rock"],
            "copyrights": [{"text": "1975 EMI"}],
            "uri": "spotify:album:alb1",
            "external_urls": {"spotify": "https://open.spotify.com/album/alb1"},
            "tracks": {"items": [{"id": "t1", "name": "Track One", "track_number": 1, "duration_ms": 354000, "artists": [{"name": "Queen"}]}]}
        }
        res = client.get("/api/browse/album?album_id=spotify:album:alb1")
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert d["album"]["name"] == "Album One"
        assert len(d["album"]["tracks"]) == 1

        # 3. /api/browse/artist
        sp_mock.artist.return_value = {
            "id": "art1", "name": "Queen",
            "followers": {"total": 50000000}, "popularity": 92,
            "genres": ["classic rock"], "images": [{"url": "https://example.com/art.jpg"}],
            "uri": "spotify:artist:art1",
            "external_urls": {"spotify": "https://open.spotify.com/artist/art1"}
        }
        res = client.get("/api/browse/artist?artist_id=spotify:artist:art1")
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert d["artist"]["name"] == "Queen"
        assert d["artist"]["followers"] == 50000000

        # 4. /api/browse/artist/albums
        sp_mock.artist_albums.return_value = {
            "total": 1,
            "items": [{
                "id": "alb1", "name": "Album One", "album_group": "album",
                "release_date": "1975-11-21", "total_tracks": 12,
                "uri": "spotify:album:alb1"
            }]
        }
        res = client.get("/api/browse/artist/albums?artist_id=art1&include_groups=album&limit=10")
        assert res.status_code == 200
        d = res.json()
        assert d["success"] is True
        assert len(d["albums"]) == 1

        # 5. /api/browse/user was removed: Spotify blocks other users' profiles (403)
        assert client.get("/api/browse/user?user_id=user1").status_code == 404


def test_additional_tool_endpoints():
    import importlib.util
    from pathlib import Path
    from fastapi.testclient import TestClient

    app_server_path = Path(__file__).parent.parent / "mcp-soundtrack-app" / "server.py"
    spec = importlib.util.spec_from_file_location("fastapi_soundtrack_server", str(app_server_path))
    web_server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(web_server)

    client = TestClient(web_server.app)

    with patch.object(web_server, "_get_valid_user_client") as mock_user_client, \
         patch("tools.playlists.create_actor_playlist") as mock_create_actor, \
         patch("tools.playlists.add_movie_songs_to_playlist") as mock_add_movie, \
         patch("tools.search.get_actor_tmdb_profile") as mock_actor_prof, \
         patch("tools.tmdb_helpers.tmdb_search_person") as mock_tmdb_person, \
         patch("tools.tmdb_helpers.ddg_web_search") as mock_ddg, \
         patch("tools.search.search_duckduckgo") as mock_search_ddg:

        sp_mock = MagicMock()
        mock_user_client.return_value = sp_mock

        # 1. /api/playlist/create_actor
        mock_create_actor.return_value = "Created playlist for Tom Hanks"
        res = client.post("/api/playlist/create_actor", json={"actor_name": "Tom Hanks"})
        assert res.status_code == 200
        assert res.json()["success"] is True

        # 2. /api/playlist/add_movie_songs
        mock_add_movie.return_value = "Added 3 songs from Inception"
        res = client.post("/api/playlist/add_movie_songs", json={"playlist_id": "p1", "movie_name": "Inception"})
        assert res.status_code == 200
        assert res.json()["success"] is True

        # 3. /api/playlist/reorder_by_features was removed: Spotify blocks audio features (403)
        assert client.post("/api/playlist/reorder_by_features", json={"playlist_id": "p1", "feature": "energy"}).status_code == 404

        # 4. /api/actor/profile
        mock_actor_prof.return_value = "TMDB Profile: Tom Hanks"
        mock_tmdb_person.return_value = {"id": 31, "name": "Tom Hanks"}
        res = client.get("/api/actor/profile?actor_name=Tom Hanks")
        assert res.status_code == 200
        assert res.json()["success"] is True

        # 5. /api/search/duckduckgo
        mock_ddg.return_value = [{"title": "DDG Result", "href": "https://example.com", "body": "Snippet"}]
        mock_search_ddg.return_value = "DuckDuckGo search results"
        res = client.get("/api/search/duckduckgo?query=Soundtracks")
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert len(res.json()["results"]) == 1

        # 6. /api/tracks/audio_features was removed: Spotify blocks audio features (403)
        assert client.get("/api/tracks/audio_features?track_ids=t1").status_code == 404

        # 7. /api/artist/network
        sp_mock.search.side_effect = lambda q, type, limit: (
            {"artists": {"items": [{"id": "art1", "name": "Queen"}]}} if type == "artist" else
            {"tracks": {"items": [{"uri": "u1", "artists": [{"id": "art1", "name": "Queen"}, {"id": "rel1", "name": "David Bowie"}]}]}}
        )
        res = client.get("/api/artist/network?artist=Queen")
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert [a["name"] for a in res.json()["related_artists"]] == ["David Bowie"]
        assert "David Bowie" in res.json()["summary"]






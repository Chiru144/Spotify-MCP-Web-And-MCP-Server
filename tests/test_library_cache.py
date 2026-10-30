import json
import pytest
from unittest.mock import patch, MagicMock

from tools import discovery, generators, library_cache

ME = {"id": "me"}
EDM_ARTIST = {"id": "dj", "name": "DJ Loud"}
FOLK_ARTIST = {"id": "folk", "name": "Quiet Folk"}


def track(uri, name, artist, year="2019", album="Album"):
    return {"id": uri, "uri": f"spotify:track:{uri}", "name": name, "type": "track", "artists": [artist],
            "album": {"name": album, "release_date": f"{year}-01-01"}, "duration_ms": 200000, "explicit": False}


@pytest.fixture
def sp(tmp_path, monkeypatch):
    monkeypatch.setenv("SPOTIFY_MCP_LIBRARY_PATH", str(tmp_path / "library.json"))
    sp = MagicMock()
    sp.me.return_value = ME
    sp.next.return_value = None
    sp.current_user_saved_tracks.return_value = {"items": [
        {"added_at": "2021-03-01T00:00:00Z", "track": track("t1", "Bangers", EDM_ARTIST, "2015")},
        {"added_at": "2022-05-01T00:00:00Z", "track": track("t2", "Campfire", FOLK_ARTIST, "1998")},
    ], "next": None}
    sp.current_user_playlists.return_value = {"items": [
        {"id": "p1", "name": "Mine", "owner": ME},
        {"id": "p2", "name": "Someone Else's", "owner": {"id": "other"}},
    ], "next": None}
    sp.playlist_items.return_value = {"items": [
        {"added_at": "2021-07-01T00:00:00Z", "track": track("t3", "Acoustic Session", FOLK_ARTIST, "2005")},
        {"added_at": "2021-07-02T00:00:00Z", "track": track("t1", "Bangers", EDM_ARTIST, "2015")},
    ], "next": None}
    with patch("tools.library_cache.get_spotify_client", return_value=sp), \
         patch("tools.generators.get_spotify_client", return_value=sp):
        yield sp


def test_sync_writes_cache_and_skips_other_users_playlists(sp, tmp_path):
    res = library_cache.spotify_sync_library()
    assert "Unique tracks: 3" in res
    sp.playlist_items.assert_called_once_with("p1", limit=100)  # p2 isn't the user's: Spotify returns 403

    data = json.loads((tmp_path / "library.json").read_text(encoding="utf-8"))
    bangers = next(t for t in data["tracks"] if t["name"] == "Bangers")
    assert bangers["sources"] == ["liked", "playlist:Mine"]
    assert bangers["added_at"] == "2021-03-01T00:00:00Z"


def test_stats_and_query_use_cache_only(sp):
    assert "isn't cached yet" in library_cache.spotify_query_library(query="x")
    library_cache.spotify_sync_library()
    sp.reset_mock()

    assert "Unique tracks: 3" in library_cache.spotify_library_stats()
    res = library_cache.spotify_query_library(year_from=1990, year_to=2006)
    assert "Campfire" in res and "Acoustic Session" in res and "Bangers" not in res
    assert "Bangers" in library_cache.spotify_query_library(artist="dj loud")
    assert "Campfire" not in library_cache.spotify_query_library(source="Mine")
    assert not sp.method_calls  # no Spotify calls


def test_vibe_helpers():
    assert discovery.vibe_target("workout") == discovery.MOOD_VIBES["workout"]
    assert discovery.vibe_target("chill", energy=0.9) == (0.9, discovery.MOOD_VIBES["chill"][1])
    assert discovery.vibe_target(None) is None
    assert discovery.vibe_genres((0.95, 0.25), count=1) == ["metal"]
    assert discovery.name_genres({"name": "Song (Unplugged)", "album": "Live"}) == ["acoustic"]
    # Cached tracks also take hints from the names of the user's playlists that hold them
    assert discovery.name_genres({"name": "Song", "album": "X", "sources": ["liked", "playlist:Gym Hits"]}) == ["workout"]
    assert discovery.estimate_vibe(["edm", "unknown"]) == discovery.GENRE_VIBES["edm"]


def test_vibe_playlist_from_library(sp):
    library_cache.spotify_sync_library()
    # Genre searches: EDM artist shows up under edm-like genres, nobody else does
    sp.search.side_effect = lambda q, type, limit: {"tracks": {"items": (
        [track("x", "Other", EDM_ARTIST)] if any(g in q for g in ("edm", "workout", "drum and bass", "house")) else [])}}

    res = generators.spotify_vibe_playlist(mood="workout")
    assert "Bangers" in res and "Campfire" not in res
    assert "Preview only" in res
    sp.current_user_playlist_create.assert_not_called()

    # The folk track has no genre match, but its name hints at acoustic
    res = generators.spotify_vibe_playlist(target_energy=0.3, target_valence=0.5)
    assert "Acoustic Session" in res and "Bangers" not in res


def test_generators_create_playlists(sp):
    library_cache.spotify_sync_library()
    sp.current_user_playlist_create.return_value = {"id": "new", "name": "90s", "external_urls": {"spotify": "url"}}

    res = generators.spotify_era_playlist(1990, 1999, from_library=True, create=True, name="90s")
    assert "Created playlist '90s'" in res and "Campfire" in res
    sp.playlist_add_items.assert_called_once_with("new", ["spotify:track:t2"])

    res = generators.spotify_time_capsule_playlist(year=2021)
    assert res.index("Bangers") < res.index("Acoustic Session")  # oldest first
    assert "Campfire" not in res

    sp.search.return_value = {"tracks": {"items": [track("e1", "Nineties", FOLK_ARTIST, "1994")]}}
    res = generators.spotify_era_playlist(1990, 1999, genres=["rock"])
    assert "Nineties" in res
    assert sp.search.call_args.kwargs["q"] == 'year:1990-1999 genre:"rock"'


def test_radio_playlist_mixes_artist_and_collaborators(sp):
    peer = {"id": "peer", "name": "Peer"}
    seed = {"id": "dj", "name": "DJ Loud"}
    by_query = {
        "DJ Loud": [track("s1", "Own Hit", seed), track("s2", "Duet", {"id": "dj", "name": "DJ Loud"}) | {"artists": [seed, peer]}],
        "Peer": [track("p1", "Peer Song", peer)],
    }
    sp.search.side_effect = lambda q, type, limit: (
        {"artists": {"items": [seed]}} if type == "artist" else {"tracks": {"items": by_query.get(q, [])}})
    res = generators.spotify_radio_playlist("DJ Loud", limit=6)
    assert "DJ Loud Radio" in res and "Peer Song" in res and "Collaborators: Peer" in res
    for removed in ("artist_related_artists", "recommendations", "artist_top_tracks"):
        getattr(sp, removed).assert_not_called()

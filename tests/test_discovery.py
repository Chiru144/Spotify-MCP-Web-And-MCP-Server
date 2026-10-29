from unittest.mock import MagicMock

from tools import discovery

ARIJIT = {"id": "arijit", "name": "Arijit Singh"}


def track(uri, *artist_ids, album=None):
    t = {"uri": uri, "name": uri, "type": "track", "artists": [{"id": a, "name": a.title()} for a in artist_ids]}
    if album:
        t["album"] = album
    return t


def test_artist_tracks_keeps_only_songs_the_artist_performs_on():
    sp = MagicMock()
    sp.search.return_value = {"tracks": {"items": [track("a", "arijit"), track("b", "someone"), None, track("c", "pritam", "arijit")]}}
    assert [t["uri"] for t in discovery.artist_tracks(sp, ARIJIT)] == ["a", "c"]


def test_collaborators_ranks_artists_by_shared_songs():
    tracks = [track("1", "arijit", "pritam"), track("2", "arijit", "pritam", "shreya"), track("3", "arijit", "shreya"),
              track("4", "arijit", "pritam")]
    result = discovery.collaborators(MagicMock(), ARIJIT, tracks)
    assert [(a["id"], a["shared_tracks"]) for a in result] == [("pritam", 3), ("shreya", 2)]


def test_genre_tracks_falls_back_to_plain_search():
    sp = MagicMock()
    sp.search.side_effect = lambda q, type, limit: {"tracks": {"items": [] if q.startswith("genre:") else [track("x", "dj")]}}
    assert [t["uri"] for t in discovery.genre_tracks(sp, ["obscure-genre"], limit=5)] == ["x"]


def test_mood_uses_mapped_genres_unless_genres_given():
    sp = MagicMock()
    sp.search.return_value = {"tracks": {"items": []}}
    discovery.mood_tracks(sp, "romantic", limit=4)
    genre_queries = [c.kwargs["q"] for c in sp.search.call_args_list if c.kwargs["q"].startswith("genre:")]
    assert genre_queries == ['genre:"romantic"', 'genre:"r&b"']
    sp.search.reset_mock()
    discovery.mood_tracks(sp, "romantic", ["bollywood"], limit=4)
    assert sp.search.call_args_list[0].kwargs["q"] == 'genre:"bollywood"'


def test_deep_cuts_skip_the_artists_hits():
    sp = MagicMock()
    sp.search.side_effect = lambda q, type, limit: (
        {"artists": {"items": [ARIJIT]}} if type == "artist" else {"tracks": {"items": [track("hit", "arijit")]}}
    )
    sp.artist_albums.return_value = {"items": [{"id": "alb", "name": "Album"}]}
    sp.album_tracks.return_value = {"items": [track("hit", "arijit"), track("gem", "arijit"), track("other", "someone")]}

    result = discovery.deep_cuts(sp, "Arijit Singh")

    assert result["name"] == "Arijit Singh"
    assert [t["uri"] for t in result["tracks"]] == ["gem"]
    assert result["tracks"][0]["album"]["name"] == "Album"

import pytest
from unittest.mock import patch, MagicMock

from tools import browse


@pytest.fixture(autouse=True)
def mock_clients():
    with patch("tools.browse.get_spotify_client") as sp:
        yield sp


def test_spotify_get_track(mock_clients):
    sp_mock = mock_clients.return_value
    sp_mock.track.return_value = {
        "id": "4cOdK2wGLETKBW3PvgPWqT",
        "name": "Bohemian Rhapsody",
        "artists": [{"name": "Queen"}],
        "album": {
            "name": "A Night at the Opera",
            "release_date": "1975-11-21"
        },
        "duration_ms": 354320,
        "popularity": 88,
        "explicit": False,
        "track_number": 11,
        "disc_number": 1,
        "external_ids": {"isrc": "GBUM71029606"},
        "preview_url": "https://p.scdn.co/mp3-preview/sample.mp3",
        "uri": "spotify:track:4cOdK2wGLETKBW3PvgPWqT",
        "external_urls": {"spotify": "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT"}
    }

    res = browse.spotify_get_track("spotify:track:4cOdK2wGLETKBW3PvgPWqT")
    assert "Bohemian Rhapsody" in res
    assert "Queen" in res
    assert "GBUM71029606" in res
    assert "88/100" in res


def test_spotify_get_track_search_fallback(mock_clients):
    sp_mock = mock_clients.return_value
    sp_mock.search.return_value = {
        "tracks": {
            "items": [{
                "id": "track123",
                "name": "Search Result Track",
                "artists": [{"name": "Artist Name"}],
                "album": {"name": "Album Name", "release_date": "2020-01-01"},
                "duration_ms": 200000,
                "popularity": 70,
                "explicit": True,
                "track_number": 1,
                "disc_number": 1,
                "external_ids": {"isrc": "US1234567890"},
                "preview_url": None,
                "uri": "spotify:track:track123",
                "external_urls": {"spotify": "https://open.spotify.com/track/track123"}
            }]
        }
    }

    res = browse.spotify_get_track("Search Result Track")
    assert "Search Result Track" in res
    assert "US1234567890" in res
    assert "Yes ⚠️" in res


def test_spotify_get_album(mock_clients):
    sp_mock = mock_clients.return_value
    sp_mock.album.return_value = {
        "id": "4aawyAB9vmqN3uQ7FjRGTy",
        "name": "OK Computer",
        "artists": [{"name": "Radiohead"}],
        "release_date": "1997-05-21",
        "total_tracks": 12,
        "label": "XL Recordings",
        "popularity": 82,
        "genres": ["alternative rock"],
        "copyrights": [{"text": "1997 XL Recordings Ltd"}],
        "uri": "spotify:album:4aawyAB9vmqN3uQ7FjRGTy",
        "external_urls": {"spotify": "https://open.spotify.com/album/4aawyAB9vmqN3uQ7FjRGTy"},
        "tracks": {
            "items": [
                {
                    "track_number": 1,
                    "name": "Airbag",
                    "artists": [{"name": "Radiohead"}],
                    "duration_ms": 284000,
                    "explicit": False
                },
                {
                    "track_number": 2,
                    "name": "Paranoid Android",
                    "artists": [{"name": "Radiohead"}],
                    "duration_ms": 387000,
                    "explicit": False
                }
            ]
        }
    }

    res = browse.spotify_get_album("spotify:album:4aawyAB9vmqN3uQ7FjRGTy")
    assert "OK Computer" in res
    assert "XL Recordings" in res
    assert "Airbag" in res
    assert "Paranoid Android" in res


def test_spotify_get_artist(mock_clients):
    sp_mock = mock_clients.return_value
    sp_mock.artist.return_value = {
        "id": "4Z8W4fKeB5YxbusRsdQVPb",
        "name": "Radiohead",
        "followers": {"total": 8500000},
        "popularity": 84,
        "genres": ["art rock", "alternative rock"],
        "images": [{"url": "https://i.scdn.co/image/art.jpg"}],
        "uri": "spotify:artist:4Z8W4fKeB5YxbusRsdQVPb",
        "external_urls": {"spotify": "https://open.spotify.com/artist/4Z8W4fKeB5YxbusRsdQVPb"}
    }

    res = browse.spotify_get_artist("spotify:artist:4Z8W4fKeB5YxbusRsdQVPb")
    assert "Radiohead" in res
    assert "8,500,000" in res
    assert "art rock" in res


def test_spotify_get_artist_albums(mock_clients):
    sp_mock = mock_clients.return_value
    sp_mock.search.return_value = {
        "artists": {
            "items": [{"id": "art1", "name": "Daft Punk"}]
        }
    }
    sp_mock.artist.return_value = {"id": "art1", "name": "Daft Punk"}
    sp_mock.artist_albums.return_value = {
        "total": 2,
        "items": [
            {
                "name": "Discovery",
                "album_group": "album",
                "release_date": "2001-03-12",
                "total_tracks": 14,
                "uri": "spotify:album:discovery"
            },
            {
                "name": "One More Time",
                "album_group": "single",
                "release_date": "2000-11-13",
                "total_tracks": 3,
                "uri": "spotify:album:onemoretime"
            }
        ]
    }

    res = browse.spotify_get_artist_albums("Daft Punk", include_groups="album,single", limit=10)
    assert "Discography for Daft Punk" in res
    assert "Discovery" in res
    assert "One More Time" in res


def test_spotify_get_user(mock_clients):
    sp_mock = mock_clients.return_value
    sp_mock.user.return_value = {
        "id": "wizzler",
        "display_name": "Matt Ogle",
        "followers": {"total": 4500},
        "images": [{"url": "https://i.scdn.co/image/user.jpg"}],
        "external_urls": {"spotify": "https://open.spotify.com/user/wizzler"}
    }
    sp_mock.user_playlists.return_value = {
        "items": [
            {
                "name": "Morning Coffee",
                "tracks": {"total": 50},
                "uri": "spotify:playlist:coffee"
            }
        ]
    }

    res = browse.spotify_get_user("wizzler")
    assert "Matt Ogle" in res
    assert "4,500" in res
    assert "Morning Coffee" in res

import http.server
import json
import threading
import time

from unittest.mock import patch

import pytest
import spotipy

from tools.spotify_client import FailFastSpotify, SpotifyRateLimitError, _restore_legacy_fields


@pytest.fixture
def fake_spotify():
    """Local HTTP server that replies with the queued (status, Retry-After) responses."""
    replies = []
    hits = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            hits.append(self.path)
            status, retry_after = replies.pop(0) if replies else (200, None)
            body = json.dumps({"ok": True} if status == 200 else {"error": {"status": status, "message": "API rate limit exceeded"}}).encode()
            self.send_response(status)
            if retry_after is not None:
                self.send_header("Retry-After", str(retry_after))
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    sp = FailFastSpotify(auth="test-token")
    sp.prefix = f"http://127.0.0.1:{server.server_address[1]}/"
    yield sp, replies, hits
    server.shutdown()


def test_long_rate_limit_fails_fast_with_clear_error(fake_spotify):
    sp, replies, hits = fake_spotify
    replies.append((429, 84485))

    start = time.monotonic()
    with pytest.raises(SpotifyRateLimitError) as exc_info:
        sp.search("Petta")

    assert time.monotonic() - start < 5
    assert len(hits) == 1
    assert exc_info.value.http_status == 429
    assert exc_info.value.retry_after == 84485
    assert "wait 23h 28m" in str(exc_info.value)


def test_short_rate_limit_is_still_retried(fake_spotify):
    sp, replies, hits = fake_spotify
    replies.append((429, 1))

    assert sp.search("Petta") == {"ok": True}
    assert len(hits) == 2


def test_search_over_10_is_fetched_in_pages_of_10():
    pages = []

    def fake_search(self, q, limit=10, offset=0, type="track", market=None):
        pages.append((limit, offset))
        items = [{"uri": f"spotify:track:{offset + i}"} for i in range(limit)]
        return {"tracks": {"items": items, "next": "more", "limit": limit}}

    with patch.object(spotipy.Spotify, "search", fake_search):
        result = FailFastSpotify(auth="t").search("Kesariya", limit=25)

    assert pages == [(10, 0), (10, 10), (5, 20)]
    assert len(result["tracks"]["items"]) == 25
    assert result["tracks"]["limit"] == 25


def test_search_stops_when_spotify_runs_out_of_results():
    def fake_search(self, q, limit=10, offset=0, type="track", market=None):
        count = 10 if offset == 0 else 3
        return {"tracks": {"items": [{"uri": f"u{offset + i}"} for i in range(count)], "next": None if offset else "more"}}

    with patch.object(spotipy.Spotify, "search", fake_search) as _:
        result = FailFastSpotify(auth="t").search("rare song", limit=50)

    assert len(result["tracks"]["items"]) == 13


def test_restores_legacy_playlist_field_names():
    response = {"items": [
        {"type": "playlist", "tracks": None, "items": {"href": "x/items", "total": 45}},
        {"added_at": "2026-01-01", "item": {"uri": "spotify:track:1"}},
    ]}
    restored = _restore_legacy_fields(response)
    assert restored["items"][0]["tracks"]["total"] == 45
    assert restored["items"][1]["track"]["uri"] == "spotify:track:1"


def test_playlist_is_following_uses_library_check_for_current_user():
    sp = FailFastSpotify(auth="t")
    with patch.object(sp, "me", return_value={"id": "me"}), \
         patch.object(sp, "current_user_saved_items", return_value=[True]) as saved, \
         patch.object(sp, "_get") as legacy:
        assert sp.playlist_is_following("37i9dQZF1DXcBWIGoYBM5M", ["me"]) == [True]
    saved.assert_called_once_with(["spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"])
    legacy.assert_not_called()

import http.server
import json
import threading
import time

import pytest

from tools.spotify_client import FailFastSpotify, SpotifyRateLimitError


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

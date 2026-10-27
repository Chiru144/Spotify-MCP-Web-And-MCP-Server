import os
from datetime import datetime, timedelta

import requests
import spotipy
from spotipy.util import Retry

# Longest Spotify Retry-After (seconds) worth sleeping through; longer waits fail immediately.
MAX_RETRY_WAIT = int(os.getenv("SPOTIFY_MAX_RETRY_WAIT", "60"))


class SpotifyRateLimitError(spotipy.SpotifyException):
    """Spotify asked this app to wait longer than MAX_RETRY_WAIT before retrying."""

    def __init__(self, retry_after: int, headers=None):
        self.retry_after = retry_after
        hours, rest = divmod(retry_after, 3600)
        wait = f"{hours}h {rest // 60}m" if hours else f"{rest // 60}m {rest % 60}s"
        until = datetime.now() + timedelta(seconds=retry_after)
        super().__init__(
            429, -1,
            f"Spotify rate limit reached: Spotify asks this app to wait {wait} "
            f"(until about {until:%Y-%m-%d %H:%M}). Spotify requests will fail until then.",
            headers=headers,
        )

    def __str__(self):
        return self.msg


class _FailFastRetry(Retry):
    """spotipy's Retry, except a long Retry-After raises instead of sleeping for hours."""

    def increment(self, method=None, url=None, response=None, error=None, _pool=None, _stacktrace=None):
        if response is not None and response.status == 429:
            # Read the header directly: urllib3 clamps parse_retry_after() to 6 hours
            header = (response.headers.get("Retry-After") or "0").strip()
            try:
                wait = int(header) if header.isdigit() else self.parse_retry_after(header)
            except Exception:
                wait = 0
            if wait > MAX_RETRY_WAIT:
                response.drain_conn()
                raise SpotifyRateLimitError(int(wait), headers=dict(response.headers))
        return super().increment(method, url, response=response, error=error,
                                 _pool=_pool, _stacktrace=_stacktrace)


class FailFastSpotify(spotipy.Spotify):
    """spotipy.Spotify that raises SpotifyRateLimitError on long rate limits instead of hanging."""

    def _build_session(self):
        super()._build_session()
        retry = _FailFastRetry(
            total=self.retries,
            connect=None,
            read=False,
            allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE"]),
            status=self.status_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=self.status_forcelist,
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

import os
from datetime import datetime, timedelta

import requests
import spotipy
from spotipy.util import Retry

# Longest Spotify Retry-After (seconds) worth sleeping through; longer waits fail immediately.
MAX_RETRY_WAIT = int(os.getenv("SPOTIFY_MAX_RETRY_WAIT", "60"))

# Largest `limit` Spotify accepts for /search since its 2026 Web API changes ("Invalid limit" above it).
SEARCH_PAGE_LIMIT = 10


def _restore_legacy_fields(obj):
    """Spotify (2026) renamed a playlist's `tracks` to `items`, and each playlist entry's
    `track` to `item`. Add the old names back so code written for either shape works."""
    if isinstance(obj, dict):
        if obj.get("type") == "playlist" and obj.get("tracks") is None and isinstance(obj.get("items"), dict):
            obj["tracks"] = obj["items"]
        if "added_at" in obj and obj.get("track") is None and isinstance(obj.get("item"), dict):
            obj["track"] = obj["item"]
        for value in list(obj.values()):
            _restore_legacy_fields(value)
    elif isinstance(obj, list):
        for value in obj:
            _restore_legacy_fields(value)
    return obj


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
    """spotipy.Spotify that raises SpotifyRateLimitError on long rate limits instead of hanging,
    and smooths over Spotify's 2026 Web API changes (see the overrides below)."""

    def _internal_call(self, method, url, payload, params):
        return _restore_legacy_fields(super()._internal_call(method, url, payload, params))

    def search(self, q, limit=10, offset=0, type="track", market=None):
        """Spotify rejects search limits above 10; fetch larger requests 10 at a time."""
        if limit <= SEARCH_PAGE_LIMIT:
            return super().search(q, limit=limit, offset=offset, type=type, market=market)
        merged = {}
        fetched = 0
        while fetched < limit:
            size = min(SEARCH_PAGE_LIMIT, limit - fetched)
            page = super().search(q, limit=size, offset=offset + fetched, type=type, market=market)
            for key, result in page.items():
                if key in merged:
                    merged[key]["items"].extend(result.get("items", []))
                    merged[key]["next"] = result.get("next")
                else:
                    merged[key] = result
            fetched += size
            if all(len(r.get("items", [])) < size or not r.get("next") for r in page.values()):
                break
        for result in merged.values():
            result["limit"] = limit
        return merged

    def playlist_is_following(self, playlist_id, user_ids):
        """Spotify now only answers this for the current user (via /me/library/contains);
        asking about other users returns 403. spotipy's own version also crashes on a bad
        deprecation warning before sending the request."""
        uri = f"spotify:playlist:{self._get_id('playlist', playlist_id)}"
        me = self.me()["id"]
        if all(user_id == me for user_id in user_ids):
            return self.current_user_saved_items([uri]) * len(user_ids)
        return self._get(f"playlists/{self._get_id('playlist', playlist_id)}/followers/contains?ids={','.join(user_ids)}")

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

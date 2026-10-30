"""Local cache of the user's library (Liked Songs and their own playlists) as a JSON file.

Tools can answer "songs I already like" questions from the cache instead of searching Spotify,
which is faster and saves Spotify calls (this app has been rate-limited before).
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from mcp.types import ToolAnnotations
from tools.core import mcp, get_spotify_client, _format_duration


def library_cache_path() -> Path:
    """~/.cache/spotify-mcp/library.json (%LOCALAPPDATA%\\spotify-mcp\\library.json on Windows).
    Override with SPOTIFY_MCP_LIBRARY_PATH."""
    override = os.getenv("SPOTIFY_MCP_LIBRARY_PATH")
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32" and os.getenv("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "spotify-mcp" / "library.json"
    return Path.home() / ".cache" / "spotify-mcp" / "library.json"


def load_library() -> Optional[Dict[str, Any]]:
    """The cached library, or None if it has not been synced yet."""
    path = library_cache_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _slim_track(t: Dict[str, Any]) -> Dict[str, Any]:
    album = t.get("album") or {}
    return {
        "id": t.get("id"),
        "uri": t.get("uri"),
        "name": t.get("name"),
        "artists": [{"id": a.get("id"), "name": a.get("name")} for a in t.get("artists", [])],
        "album": album.get("name"),
        "release_date": album.get("release_date") or "",
        "duration_ms": t.get("duration_ms") or 0,
        "explicit": bool(t.get("explicit")),
        "sources": [],
    }


def sync_library(sp, include_playlists: bool = True, max_liked: int = 2000,
                 max_playlists: int = 25) -> Dict[str, Any]:
    """Download Liked Songs and the user's own playlists into the cache file and return it."""
    tracks: Dict[str, Dict[str, Any]] = {}

    def add(t, source, added_at=None):
        if not t or not t.get("uri") or t.get("type", "track") != "track":
            return
        entry = tracks.setdefault(t["uri"], _slim_track(t))
        if source not in entry["sources"]:
            entry["sources"].append(source)
        if added_at and (not entry.get("added_at") or added_at < entry["added_at"]):
            entry["added_at"] = added_at

    liked = 0
    res = sp.current_user_saved_tracks(limit=50)
    while res and liked < max_liked:
        for item in res.get("items", []):
            add(item.get("track"), "liked", item.get("added_at"))
            liked += 1
        res = sp.next(res) if res.get("next") and liked < max_liked else None

    me = sp.me().get("id")
    playlists = []
    if include_playlists:
        res = sp.current_user_playlists(limit=50)
        while res and len(playlists) < max_playlists:
            for p in res.get("items", []):
                # Spotify (2026) returns 403 for playlists the user doesn't own, so only their own are cached
                if p and (p.get("owner") or {}).get("id") == me and len(playlists) < max_playlists:
                    playlists.append(p)
            res = sp.next(res) if res.get("next") and len(playlists) < max_playlists else None

    playlist_info = []
    for p in playlists:
        count = 0
        res = sp.playlist_items(p["id"], limit=100)
        while res:
            for item in res.get("items", []):
                add(item.get("track"), f"playlist:{p.get('name')}", item.get("added_at"))
                count += 1
            res = sp.next(res) if res.get("next") else None
        playlist_info.append({"id": p["id"], "name": p.get("name"), "tracks": count})

    library = {
        "version": 1,
        "synced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "user_id": me,
        "liked_count": liked,
        "playlists": playlist_info,
        "tracks": list(tracks.values()),
    }
    path = library_cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(library), encoding="utf-8")
    return library


def query_tracks(library: Dict[str, Any], query: Optional[str] = None, artist: Optional[str] = None,
                 year_from: Optional[int] = None, year_to: Optional[int] = None,
                 source: Optional[str] = None, explicit: Optional[bool] = None) -> List[Dict[str, Any]]:
    """Cached tracks matching every filter given (no Spotify calls)."""
    q, art, src = (query or "").lower(), (artist or "").lower(), (source or "").lower()
    out = []
    for t in library.get("tracks", []):
        names = " ".join(a.get("name") or "" for a in t.get("artists", [])).lower()
        year = int(t["release_date"][:4]) if t.get("release_date", "")[:4].isdigit() else None
        if q and q not in f"{t.get('name', '')} {t.get('album', '')} {names}".lower():
            continue
        if art and art not in names:
            continue
        if year_from is not None and (year is None or year < year_from):
            continue
        if year_to is not None and (year is None or year > year_to):
            continue
        if src and not any(src == s.lower() or (src == "playlists" and s.startswith("playlist:"))
                           or (src not in ("liked", "playlists") and src in s.lower()) for s in t.get("sources", [])):
            continue
        if explicit is not None and t.get("explicit") != explicit:
            continue
        out.append(t)
    return out


def _not_synced() -> str:
    return "Your library isn't cached yet. Run spotify_sync_library first (it downloads your Liked Songs and playlists once)."


def _track_line(idx: int, t: Dict[str, Any]) -> str:
    artists = ", ".join(a.get("name") or "Unknown" for a in t.get("artists", []))
    year = (t.get("release_date") or "")[:4]
    return f"{idx}. {t.get('name')} - {artists} [{t.get('album')}{', ' + year if year else ''}] ({_format_duration(t.get('duration_ms'))}, URI: {t.get('uri')})"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_sync_library(
    include_playlists: bool = True,
    max_liked_songs: int = 2000,
    max_playlists: int = 25
) -> str:
    """Download your Liked Songs and your own playlists into a local cache file, so other tools can answer
    "songs I already like" requests without searching Spotify. Run it once, then again when your library changes.

    Args:
        include_playlists: Also cache the tracks of playlists you own (default: True).
        max_liked_songs: Most Liked Songs to cache (default: 2000; 50 per Spotify call).
        max_playlists: Most of your own playlists to cache (default: 25).
    """
    try:
        sp = get_spotify_client()
        library = sync_library(sp, include_playlists, max(1, max_liked_songs), max(0, max_playlists))
        return (
            f"Library cached to {library_cache_path()}\n"
            f"• Liked Songs: {library['liked_count']}\n"
            f"• Playlists: {len(library['playlists'])}\n"
            f"• Unique tracks: {len(library['tracks'])}\n"
            f"• Synced at: {library['synced_at']}"
        )
    except Exception as e:
        return f"Error syncing library: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False))
def spotify_library_stats() -> str:
    """Summarize the locally cached library: size, top artists, decades and playlists. Makes no Spotify calls."""
    library = load_library()
    if not library:
        return _not_synced()
    tracks = library.get("tracks", [])
    artists = Counter(a.get("name") for t in tracks for a in t.get("artists", [])[:1] if a.get("name"))
    decades = Counter(f"{t['release_date'][:3]}0s" for t in tracks if t.get("release_date", "")[:4].isdigit())
    hours = sum(t.get("duration_ms") or 0 for t in tracks) / 3_600_000
    lines = [
        f"Cached Library ({library_cache_path()}):",
        f"• Synced at: {library.get('synced_at')}",
        f"• Unique tracks: {len(tracks)} ({hours:.1f} hours)",
        f"• Liked Songs: {library.get('liked_count', 0)}",
        f"• Playlists cached: {len(library.get('playlists', []))}",
        f"• Explicit tracks: {sum(1 for t in tracks if t.get('explicit'))}",
        "\nTop Artists:",
    ]
    lines.extend(f"  {i}. {name} ({n} tracks)" for i, (name, n) in enumerate(artists.most_common(10), 1))
    if decades:
        lines.append("\nDecades:")
        lines.extend(f"  {d}: {n} tracks" for d, n in sorted(decades.items()))
    if library.get("playlists"):
        lines.append("\nPlaylists:")
        lines.extend(f"  • {p['name']} ({p['tracks']} tracks)" for p in library["playlists"])
    return "\n".join(lines)


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False))
def spotify_query_library(
    query: Optional[str] = None,
    artist: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    source: Optional[str] = None,
    explicit: Optional[bool] = None,
    limit: int = 50
) -> str:
    """Search your locally cached library (Liked Songs and your playlists) without calling Spotify.

    Args:
        query: Optional text matched against track, album and artist names.
        artist: Optional artist name (partial match).
        year_from: Optional earliest release year.
        year_to: Optional latest release year.
        source: Optional 'liked', 'playlists', or part of a playlist name.
        explicit: Optional True/False to keep only explicit or clean tracks.
        limit: Maximum tracks to return (default: 50).
    """
    library = load_library()
    if not library:
        return _not_synced()
    matches = query_tracks(library, query, artist, year_from, year_to, source, explicit)
    if not matches:
        return "No cached tracks match those filters."
    shown = matches[:max(1, limit)]
    lines = [f"Cached Library Matches ({len(matches)} found, showing {len(shown)}; synced {library.get('synced_at')}):"]
    lines.extend(_track_line(i, t) for i, t in enumerate(shown, 1))
    return "\n".join(lines)

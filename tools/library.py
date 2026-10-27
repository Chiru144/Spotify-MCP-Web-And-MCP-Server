from typing import Optional, List, Dict, Any
from mcp.types import ToolAnnotations
from tools.core import mcp, get_spotify_client
import spotipy


def _clean_spotify_id(raw_id: str, id_type: str = "") -> str:
    val = (raw_id or "").strip()
    if "/" in val:
        val = val.split(f"/{id_type}/")[-1] if id_type and f"/{id_type}/" in val else val.split("/")[-1]
    if ":" in val:
        val = val.split(":")[-1]
    return val.split("?")[0].strip()


def _format_duration(ms: int) -> str:
    sec = (ms or 0) // 1000
    return f"{sec // 60}:{sec % 60:02d}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_get_saved_tracks(
    limit: int = 20,
    offset: int = 0,
    market: Optional[str] = None
) -> str:
    """List tracks saved in the current user's Liked Songs library.
    
    Args:
        limit: Number of tracks to return (default: 20, max: 50).
        offset: Index of the first item to return (default: 0).
        market: An ISO 3166-1 alpha-2 country code.
    """
    try:
        sp = get_spotify_client()
        limit = max(1, min(limit, 50))
        offset = max(0, offset)
        results = sp.current_user_saved_tracks(limit=limit, offset=offset, market=market)
        items = results.get("items", [])
        total = results.get("total", len(items))

        if not items:
            return "No Liked Songs found in your Spotify library."

        lines = [
            f"Spotify Liked Songs Library ({total} total tracks, showing {len(items)} from offset {offset}):",
        ]
        for idx, it in enumerate(items, offset + 1):
            t = it.get("track", {})
            added_at = it.get("added_at", "")[:10]
            artists = ", ".join(a.get("name", "Unknown") for a in t.get("artists", []))
            album = t.get("album", {}).get("name", "Unknown Album")
            dur = _format_duration(t.get("duration_ms", 0))
            pop = t.get("popularity", 0)
            added_str = f" [Saved: {added_at}]" if added_at else ""
            lines.append(f"{idx}. {t.get('name')} - {artists} ({dur}) [Album: {album}] (Pop: {pop}/100{added_str}, URI: {t.get('uri')})")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing Liked Songs: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_save_tracks(track_ids: List[str]) -> str:
    """Save one or more tracks to the current user's Liked Songs library.
    
    Args:
        track_ids: List of Spotify track IDs, URIs, or URLs to save.
    """
    try:
        sp = get_spotify_client()
        cleaned = [_clean_spotify_id(t, "track") for t in (track_ids or []) if t]
        if not cleaned:
            return "Error: Please provide at least one valid track ID or URI to save."

        # Spotify API accepts up to 50 tracks per batch
        for i in range(0, len(cleaned), 50):
            batch = cleaned[i:i + 50]
            sp.current_user_saved_tracks_add(tracks=batch)

        return f"Successfully saved {len(cleaned)} track(s) to your Liked Songs library."
    except Exception as e:
        return f"Error saving tracks to Liked Songs: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=True))
def spotify_remove_saved_tracks(track_ids: List[str]) -> str:
    """Remove one or more tracks from the current user's Liked Songs library.
    
    Args:
        track_ids: List of Spotify track IDs, URIs, or URLs to remove.
    """
    try:
        sp = get_spotify_client()
        cleaned = [_clean_spotify_id(t, "track") for t in (track_ids or []) if t]
        if not cleaned:
            return "Error: Please provide at least one valid track ID or URI to remove."

        for i in range(0, len(cleaned), 50):
            batch = cleaned[i:i + 50]
            sp.current_user_saved_tracks_delete(tracks=batch)

        return f"Successfully removed {len(cleaned)} track(s) from your Liked Songs library."
    except Exception as e:
        return f"Error removing tracks from Liked Songs: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_check_saved_tracks(track_ids: List[str]) -> str:
    """Verify whether specific tracks exist in the current user's Liked Songs library.
    
    Args:
        track_ids: List of Spotify track IDs, URIs, or URLs to check (max: 50).
    """
    try:
        sp = get_spotify_client()
        cleaned = [_clean_spotify_id(t, "track") for t in (track_ids or []) if t]
        if not cleaned:
            return "Error: Please provide at least one valid track ID or URI to check."

        cleaned = cleaned[:50]
        results = sp.current_user_saved_tracks_contains(tracks=cleaned)

        lines = [f"Liked Songs Verification ({len(cleaned)} tracks inspected):"]
        for tid, is_saved in zip(cleaned, results):
            status = "🟢 Liked (In Library)" if is_saved else "⚪ Not Liked"
            lines.append(f"• {status} - Track ID: {tid}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error checking Liked Songs status: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_get_saved_albums(
    limit: int = 20,
    offset: int = 0,
    market: Optional[str] = None
) -> str:
    """Fetch albums saved in the current user's library.
    
    Args:
        limit: Number of albums to return (default: 20, max: 50).
        offset: Index of the first album to return (default: 0).
        market: An ISO 3166-1 alpha-2 country code.
    """
    try:
        sp = get_spotify_client()
        limit = max(1, min(limit, 50))
        offset = max(0, offset)
        results = sp.current_user_saved_albums(limit=limit, offset=offset, market=market)
        items = results.get("items", [])
        total = results.get("total", len(items))

        if not items:
            return "No saved albums found in your Spotify library."

        lines = [
            f"Spotify Saved Albums Library ({total} total albums, showing {len(items)} from offset {offset}):",
        ]
        for idx, it in enumerate(items, offset + 1):
            alb = it.get("album", {})
            added_at = it.get("added_at", "")[:10]
            artists = ", ".join(a.get("name", "Unknown") for a in alb.get("artists", []))
            release = alb.get("release_date", "Unknown Date")
            total_tracks = alb.get("total_tracks", 0)
            pop = alb.get("popularity", 0)
            added_str = f" [Saved: {added_at}]" if added_at else ""
            lines.append(f"{idx}. {alb.get('name')} by {artists} ({release}, {total_tracks} tracks) [Pop: {pop}/100{added_str}, URI: {alb.get('uri')}]")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing saved albums: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_save_albums(album_ids: List[str]) -> str:
    """Save one or more albums to the current user's library.
    
    Args:
        album_ids: List of Spotify album IDs, URIs, or URLs to save.
    """
    try:
        sp = get_spotify_client()
        cleaned = [_clean_spotify_id(a, "album") for a in (album_ids or []) if a]
        if not cleaned:
            return "Error: Please provide at least one valid album ID or URI to save."

        for i in range(0, len(cleaned), 50):
            batch = cleaned[i:i + 50]
            sp.current_user_saved_albums_add(albums=batch)

        return f"Successfully saved {len(cleaned)} album(s) to your Spotify library."
    except Exception as e:
        return f"Error saving albums: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=True))
def spotify_remove_saved_albums(album_ids: List[str]) -> str:
    """Remove one or more albums from the current user's library.
    
    Args:
        album_ids: List of Spotify album IDs, URIs, or URLs to remove.
    """
    try:
        sp = get_spotify_client()
        cleaned = [_clean_spotify_id(a, "album") for a in (album_ids or []) if a]
        if not cleaned:
            return "Error: Please provide at least one valid album ID or URI to remove."

        for i in range(0, len(cleaned), 50):
            batch = cleaned[i:i + 50]
            sp.current_user_saved_albums_delete(albums=batch)

        return f"Successfully removed {len(cleaned)} album(s) from your Spotify library."
    except Exception as e:
        return f"Error removing albums: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_check_saved_albums(album_ids: List[str]) -> str:
    """Verify whether specific albums exist in the current user's library.
    
    Args:
        album_ids: List of Spotify album IDs, URIs, or URLs to check (max: 50).
    """
    try:
        sp = get_spotify_client()
        cleaned = [_clean_spotify_id(a, "album") for a in (album_ids or []) if a]
        if not cleaned:
            return "Error: Please provide at least one valid album ID or URI to check."

        cleaned = cleaned[:50]
        results = sp.current_user_saved_albums_contains(albums=cleaned)

        lines = [f"Saved Albums Verification ({len(cleaned)} albums inspected):"]
        for aid, is_saved in zip(cleaned, results):
            status = "🟢 Saved (In Library)" if is_saved else "⚪ Not Saved"
            lines.append(f"• {status} - Album ID: {aid}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error checking saved albums status: {str(e)}"

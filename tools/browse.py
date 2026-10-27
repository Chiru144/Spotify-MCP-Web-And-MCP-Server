from typing import Optional, List, Dict, Any
from mcp.types import ToolAnnotations
from tools.core import mcp, get_spotify_client, _clean_spotify_id, _format_duration
import spotipy



@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_get_track(track_id: str, market: Optional[str] = None) -> str:
    """Inspect full track metadata including ISRC, popularity, audio preview URL, and album details.
    
    Args:
        track_id: Spotify track ID, URI, or URL (e.g. 'spotify:track:4cOdK2wGLETKBW3PvgPWqT').
        market: Optional ISO 3166-1 alpha-2 country code.
    """
    try:
        sp = get_spotify_client()
        clean_id = _clean_spotify_id(track_id, "track")
        if not clean_id or (len(clean_id) != 22 and not track_id.startswith("spotify:track:")):
            # If user passed a song title instead of ID, search for it
            search_res = sp.search(q=track_id, type="track", limit=1)
            items = search_res.get("tracks", {}).get("items", [])
            if not items:
                return f"Error: Track '{track_id}' not found."
            t = items[0]
        else:
            t = sp.track(clean_id, market=market)

        if not t:
            return f"Error: Track '{track_id}' not found."

        artists = ", ".join(a.get("name", "Unknown") for a in t.get("artists", []))
        album = t.get("album", {})
        album_name = album.get("name", "Unknown Album")
        release_date = album.get("release_date", "Unknown Date")
        dur = _format_duration(t.get("duration_ms", 0))
        pop = t.get("popularity", 0)
        explicit = "Yes ⚠️" if t.get("explicit") else "No"
        track_num = t.get("track_number", 1)
        disc_num = t.get("disc_number", 1)
        
        ext_ids = t.get("external_ids", {})
        isrc = ext_ids.get("isrc", "N/A")
        ean = ext_ids.get("ean", "N/A")
        upc = ext_ids.get("upc", "N/A")
        preview = t.get("preview_url") or "No preview available"
        spotify_url = t.get("external_urls", {}).get("spotify", "")

        lines = [
            f"🎵 Track Metadata: {t.get('name')}",
            f"• Artist(s): {artists}",
            f"• Album: {album_name} ({release_date})",
            f"• Duration: {dur} ({t.get('duration_ms', 0):,} ms)",
            f"• Popularity: {pop}/100",
            f"• Explicit: {explicit}",
            f"• Position: Track {track_num}, Disc {disc_num}",
            f"• ISRC: {isrc}",
        ]
        if ean != "N/A": lines.append(f"• EAN: {ean}")
        if upc != "N/A": lines.append(f"• UPC: {upc}")
        lines.extend([
            f"• Preview URL: {preview}",
            f"• URI: {t.get('uri')}",
            f"• Spotify Link: {spotify_url}"
        ])
        return "\n".join(lines)
    except Exception as e:
        return f"Error inspecting track '{track_id}': {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_get_album(album_id: str, market: Optional[str] = None) -> str:
    """Inspect full album details including copyrights, label, release date, and complete tracklist.
    
    Args:
        album_id: Spotify album ID, URI, or URL (e.g. 'spotify:album:4aawyAB9vmqN3uQ7FjRGTy').
        market: Optional ISO 3166-1 alpha-2 country code.
    """
    try:
        sp = get_spotify_client()
        clean_id = _clean_spotify_id(album_id, "album")
        if not clean_id or len(clean_id) != 22 and not album_id.startswith("spotify:album:"):
            search_res = sp.search(q=album_id, type="album", limit=1)
            items = search_res.get("albums", {}).get("items", [])
            if not items:
                return f"Error: Album '{album_id}' not found."
            alb = sp.album(items[0]["id"], market=market)
        else:
            alb = sp.album(clean_id, market=market)

        if not alb:
            return f"Error: Album '{album_id}' not found."

        artists = ", ".join(a.get("name", "Unknown") for a in alb.get("artists", []))
        total_tracks = alb.get("total_tracks", 0)
        release_date = alb.get("release_date", "Unknown Date")
        label = alb.get("label", "Unknown Label")
        pop = alb.get("popularity", 0)
        genres = ", ".join(alb.get("genres", [])) or "None listed"
        copyrights = ", ".join(c.get("text", "") for c in alb.get("copyrights", [])) or "None listed"
        spotify_url = alb.get("external_urls", {}).get("spotify", "")

        tracks_items = alb.get("tracks", {}).get("items", [])
        
        lines = [
            f"💿 Album: {alb.get('name')} by {artists}",
            f"• Released: {release_date} | Total Tracks: {total_tracks}",
            f"• Label: {label}",
            f"• Copyrights: {copyrights}",
            f"• Popularity: {pop}/100 | Genres: {genres}",
            f"• URI: {alb.get('uri')}",
            f"• Spotify Link: {spotify_url}\n",
            f"Tracklist ({len(tracks_items)} tracks):"
        ]

        for t in tracks_items:
            track_num = t.get("track_number", 1)
            dur = _format_duration(t.get("duration_ms", 0))
            t_artists = ", ".join(a.get("name", "") for a in t.get("artists", []))
            exp_flag = " [Explicit]" if t.get("explicit") else ""
            lines.append(f"  {track_num:02d}. {t.get('name')} - {t_artists} ({dur}){exp_flag}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error inspecting album '{album_id}': {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_get_artist(artist_id: str) -> str:
    """Inspect artist details including genres, follower count, popularity, and profile images.
    
    Args:
        artist_id: Spotify artist ID, URI, URL, or artist name (e.g. 'Radiohead' or 'spotify:artist:4Z8W4fKeB5YxbusRsdQVPb').
    """
    try:
        sp = get_spotify_client()
        clean_id = _clean_spotify_id(artist_id, "artist")
        if not clean_id or len(clean_id) != 22 and not artist_id.startswith("spotify:artist:"):
            search_res = sp.search(q=artist_id, type="artist", limit=1)
            items = search_res.get("artists", {}).get("items", [])
            if not items:
                return f"Error: Artist '{artist_id}' not found."
            a = items[0]
        else:
            a = sp.artist(clean_id)

        if not a:
            return f"Error: Artist '{artist_id}' not found."

        genres = ", ".join(a.get("genres", [])) or "None listed"
        followers = a.get("followers", {}).get("total", 0)
        pop = a.get("popularity", 0)
        spotify_url = a.get("external_urls", {}).get("spotify", "")
        images = a.get("images", [])
        image_url = images[0].get("url") if images else "None"

        lines = [
            f"🎤 Artist Profile: {a.get('name')}",
            f"• Followers: {followers:,}",
            f"• Popularity: {pop}/100",
            f"• Genres: {genres}",
            f"• Profile Image: {image_url}",
            f"• URI: {a.get('uri')}",
            f"• Spotify Link: {spotify_url}"
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error inspecting artist '{artist_id}': {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_get_artist_albums(
    artist_id: str,
    include_groups: Optional[str] = "album,single",
    limit: int = 20,
    offset: int = 0,
    country: Optional[str] = None
) -> str:
    """Get all albums, singles, and compilations released by a specific artist.
    
    Args:
        artist_id: Spotify artist ID, URI, URL, or artist name.
        include_groups: Comma-separated list of groups ('album', 'single', 'appears_on', 'compilation'). Default: 'album,single'.
        limit: Number of items to return (default: 20, max: 50).
        offset: Index of the first item to return (default: 0).
        country: Optional ISO 3166-1 alpha-2 country code.
    """
    try:
        sp = get_spotify_client()
        clean_id = _clean_spotify_id(artist_id, "artist")
        artist_name = artist_id

        if not clean_id or len(clean_id) != 22 and not artist_id.startswith("spotify:artist:"):
            search_res = sp.search(q=artist_id, type="artist", limit=1)
            items = search_res.get("artists", {}).get("items", [])
            if not items:
                return f"Error: Artist '{artist_id}' not found."
            clean_id = items[0]["id"]
            artist_name = items[0].get("name", artist_id)
        else:
            try:
                artist_meta = sp.artist(clean_id)
                artist_name = artist_meta.get("name", artist_id)
            except Exception:
                pass

        limit = max(1, min(limit, 50))
        offset = max(0, offset)
        groups = include_groups or "album,single"

        results = sp.artist_albums(clean_id, include_groups=groups, limit=limit, offset=offset, country=country)
        items = results.get("items", [])
        total = results.get("total", len(items))

        if not items:
            return f"No discography items found for artist '{artist_name}' (groups: {groups})."

        lines = [
            f"💿 Discography for {artist_name} ({total} total releases, showing {len(items)} from offset {offset}):",
        ]
        for idx, alb in enumerate(items, offset + 1):
            rel_date = alb.get("release_date", "Unknown Date")
            total_tracks = alb.get("total_tracks", 0)
            group = alb.get("album_group", alb.get("album_type", "album")).upper()
            lines.append(f"{idx}. [{group}] {alb.get('name')} ({rel_date}, {total_tracks} tracks) - URI: {alb.get('uri')}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching albums for artist '{artist_id}': {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_get_user(user_id: str) -> str:
    """Fetch public profile information and public playlists for any Spotify user.
    
    Args:
        user_id: Spotify user ID, URI, or profile URL (e.g. 'spotify:user:wizzler' or 'wizzler').
    """
    try:
        sp = get_spotify_client()
        clean_id = _clean_spotify_id(user_id, "user")
        if not clean_id:
            return "Error: Please provide a valid user ID or URI."

        user = sp.user(clean_id)
        if not user:
            return f"Error: User profile '{clean_id}' not found."

        display_name = user.get("display_name") or clean_id
        followers = user.get("followers", {}).get("total", 0)
        spotify_url = user.get("external_urls", {}).get("spotify", "")
        images = user.get("images", [])
        image_url = images[0].get("url") if images else "None"

        # Try fetching public playlists
        playlists = []
        try:
            pl_res = sp.user_playlists(clean_id, limit=15)
            playlists = pl_res.get("items", [])
        except Exception:
            pass

        lines = [
            f"👤 Spotify User Profile: {display_name}",
            f"• User ID: {clean_id}",
            f"• Followers: {followers:,}",
            f"• Avatar URL: {image_url}",
            f"• Profile Link: {spotify_url}\n",
            f"Public Playlists ({len(playlists)} found):"
        ]

        if not playlists:
            lines.append("  (No public playlists available or user library is private)")
        else:
            for idx, p in enumerate(playlists, 1):
                tracks_count = p.get("tracks", {}).get("total", 0)
                lines.append(f"  {idx}. {p.get('name')} ({tracks_count} tracks) - URI: {p.get('uri')}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching profile for user '{user_id}': {str(e)}"

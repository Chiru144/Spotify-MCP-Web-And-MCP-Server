from typing import Optional, List, Dict, Any, Tuple, Set
import json
from mcp.types import ToolAnnotations
from tools.core import mcp, get_spotify_client
import spotipy

from tools.tmdb_helpers import *

@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True))
def create_actor_playlist(
    actor_name: str,
    playlist_name: Optional[str] = None,
    max_movies: int = 10,
    max_songs_per_movie: int = 3,
    specific_movies: Optional[str] = None,
    sort_by: str = "popularity",
    public: bool = True
) -> str:
    """End-to-End Pipeline: Discover an actor's filmography via TMDB/DDG, locate songs on Spotify,
    create a new playlist, and add all tracks.
    
    Args:
        actor_name: Name of the actor (e.g., 'Cillian Murphy', 'Shah Rukh Khan', 'Keanu Reeves')
        playlist_name: Optional custom name for the playlist
        max_movies: Number of movies to pull songs from (default: 10)
        max_songs_per_movie: Number of songs to add per movie (default: 3)
        specific_movies: Optional comma-separated list of specific movies to use (e.g. 'Inception, Dunkirk, Oppenheimer')
        sort_by: Filmography sort order ('popularity' or 'release_date', default: 'popularity')
        public: Whether the created playlist is public (default: True)
    """
    try:
        sp = get_spotify_client()
        user_info = sp.current_user()
        user_id = user_info["id"]

        # Step 1: Discover movies
        source_note = ""
        movie_years: Dict[str, str] = {}
        if specific_movies:
            movie_list = [m.strip() for m in specific_movies.split(",") if m.strip()]
            source_note = "User-specified list"
        else:
            film_data = get_actor_filmography(actor_name, limit=max_movies, sort_by=sort_by)
            source_note = f"Discovered via {film_data.get('source', 'Web')}"
            movies = film_data.get("movies", [])
            if not movies:
                return f"Could not find any movies online for actor '{actor_name}'."
            movie_list = [m["title"] for m in movies[:max_movies]]
            movie_years = {m["title"]: (m.get("release_date") or "")[:4] for m in movies[:max_movies]}

        # Step 2: Fetch tracks for each movie
        all_tracks: List[Dict[str, str]] = []
        track_breakdown: List[str] = []

        for movie in movie_list:
            m_tracks = fetch_tracks_for_movie(sp, movie, max_songs=max_songs_per_movie,
                                              release_year=movie_years.get(movie) or None)
            if m_tracks:
                all_tracks.extend(m_tracks)
                song_titles = ", ".join(f"'{t['title']}'" for t in m_tracks)
                track_breakdown.append(f"• {movie}: {len(m_tracks)} song(s) ({song_titles})")
            else:
                track_breakdown.append(f"• {movie}: (no tracks found on Spotify)")

        if not all_tracks:
            return f"Found movies for '{actor_name}', but could not locate matching songs on Spotify."

        # Step 3: Create the Spotify playlist
        p_name = playlist_name or f"{actor_name} - Filmography Soundtracks"
        description = f"Curated filmography soundtracks for {actor_name}. Generated via TMDB, DuckDuckGo & Spotify MCP."
        playlist = sp.current_user_playlist_create(
            name=p_name,
            public=public,
            description=description
        )
        playlist_id = playlist["id"]
        playlist_url = playlist.get("external_urls", {}).get("spotify", "")

        # Step 4: Batch add tracks (Spotify allows max 100 per call)
        track_uris = [t["uri"] for t in all_tracks]
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i:i + 100]
            sp.playlist_add_items(playlist_id=playlist_id, items=batch)

        result_lines = [
            f"Successfully created playlist '{p_name}' for {actor_name}!",
            f"Playlist Link: {playlist_url}",
            f"Playlist ID: {playlist_id}",
            f"Source: {source_note}",
            f"Total Songs Added: {len(all_tracks)} across {len(movie_list)} movies.",
            "\nBreakdown by movie:",
            *track_breakdown
        ]
        return "\n".join(result_lines)

    except Exception as e:
        return f"Error creating actor playlist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True))
def create_playlist(name: str, description: str = "", public: bool = True) -> str:
    """Create a new Spotify playlist for the user.
    
    Args:
        name: Name of the playlist
        description: Description of the playlist
        public: Whether the playlist is public (default: True)
    """
    try:
        sp = get_spotify_client()
        playlist = sp.current_user_playlist_create(
            name=name,
            public=public,
            description=description
        )
        url = playlist.get("external_urls", {}).get("spotify", "")
        return f"Playlist '{name}' created successfully!\nID: {playlist['id']}\nURL: {url}"
    except Exception as e:
        return f"Error creating playlist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True))
def shuffle_playlist(playlist_id: str) -> str:
    """Mix and shuffle all songs in a Spotify playlist into a completely new random order.
    
    Args:
        playlist_id: The Spotify ID, URI, or URL of the playlist to shuffle
    """
    try:
        import random
        sp = get_spotify_client()
        pid = playlist_id.split(":")[-1].split("/")[-1].split("?")[0]
        
        # Fetch all songs from the playlist
        items = []
        res = sp.playlist_items(pid, limit=100)
        while res:
            items.extend(res.get("items", []))
            if res.get("next"):
                res = sp.next(res)
            else:
                break
                
        valid_tracks = [it["track"] for it in items if it.get("track") and it["track"].get("uri")]
        if not valid_tracks:
            return f"No songs found in playlist {pid} to shuffle."
            
        total_songs = len(valid_tracks)
        shuffled = list(valid_tracks)
        random.shuffle(shuffled)
        
        shuffled_uris = [t["uri"] for t in shuffled if t.get("uri", "").startswith("spotify:track:")]
        if shuffled_uris:
            sp.playlist_replace_items(pid, shuffled_uris[:100])
            for i in range(100, len(shuffled_uris), 100):
                sp.playlist_add_items(pid, shuffled_uris[i:i+100])
                
        preview_lines = [f"{idx}. {t['name']} - {', '.join(a['name'] for a in t.get('artists', []))}" for idx, t in enumerate(shuffled[:5], 1)]
        preview_text = "\n".join(preview_lines)
        more_text = f"\n... and {total_songs - 5} more songs" if total_songs > 5 else ""
        
        return f"Successfully mixed and shuffled all {total_songs} songs in playlist {pid} in a new random order!\n\nNew song order preview (first {min(5, total_songs)} of {total_songs} songs):\n{preview_text}{more_text}"
    except Exception as e:
        return f"Error shuffling playlist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True))
def add_tracks_to_playlist(playlist_id: str, track_uris: List[str]) -> str:
    """Add a list of Spotify song URIs to an existing playlist.
    
    Args:
        playlist_id: The Spotify ID or URI of the playlist
        track_uris: List of Spotify song URIs (e.g. ['spotify:track:...', ...])
    """
    try:
        sp = get_spotify_client()
        pid = playlist_id.split(":")[-1].split("/")[-1].split("?")[0]
        total_added = 0
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i:i + 100]
            sp.playlist_add_items(playlist_id=pid, items=batch)
            total_added += len(batch)
        return f"Successfully added {total_added} song(s) to playlist {pid}."
    except Exception as e:
        return f"Error adding songs to playlist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True))
def combine_playlists(playlist_ids: List[str], new_name: str = "Combined Playlist", description: str = "Combined playlist from multiple sources.") -> str:
    """Combines multiple Spotify playlists into a single new playlist.
    
    Args:
        playlist_ids: A list of Spotify playlist IDs, URIs, or URLs to combine.
        new_name: The name for the newly created combined playlist.
        description: The description for the new playlist.
    """
    try:
        sp = get_spotify_client()
        user_id = sp.me()["id"]
        
        all_uris = []
        for playlist_url in playlist_ids:
            pid = playlist_url.split(":")[-1].split("/")[-1].split("?")[0]
            items = []
            res = sp.playlist_items(pid, limit=100)
            while res:
                items.extend(res.get("items", []))
                if res.get("next"):
                    res = sp.next(res)
                else:
                    break
            uris = [it["track"]["uri"] for it in items if it.get("track") and it["track"].get("uri") and it["track"]["uri"].startswith("spotify:track:")]
            all_uris.extend(uris)
            
        if not all_uris:
            return "No valid songs found in the provided playlists to combine."
            
        # Deduplicate
        seen = set()
        deduped_uris = [uri for uri in all_uris if not (uri in seen or seen.add(uri))]
        
        new_playlist = sp.user_playlist_create(
            user=user_id,
            name=new_name,
            public=False,
            description=description
        )
        new_pid = new_playlist["id"]
        
        for i in range(0, len(deduped_uris), 100):
            sp.playlist_add_items(new_pid, deduped_uris[i:i+100])
            
        return f"Successfully combined {len(playlist_ids)} playlists into '{new_name}' with {len(deduped_uris)} unique songs! New Playlist ID: {new_pid}"
    except Exception as e:
        return f"Error combining playlists: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=True))
def dedupe_playlist(playlist_id: str) -> str:
    """Removes all duplicate songs from a Spotify playlist, keeping only the first occurrence of each song.
    
    Args:
        playlist_id: The Spotify ID, URI, or URL of the playlist to deduplicate.
    """
    try:
        sp = get_spotify_client()
        pid = playlist_id.split(":")[-1].split("/")[-1].split("?")[0]
        
        # Fetch all songs
        items = []
        res = sp.playlist_items(pid, limit=100)
        while res:
            items.extend(res.get("items", []))
            if res.get("next"):
                res = sp.next(res)
            else:
                break
                
        valid_items = [it for it in items if it.get("track") and it["track"].get("uri")]
        if not valid_items:
            return f"No songs found in playlist {pid}."
            
        seen_uris = set()
        deduped_uris = []
        duplicates = 0
        
        for it in valid_items:
            uri = it["track"]["uri"]
            if not uri.startswith("spotify:track:"): continue
            
            if uri in seen_uris:
                duplicates += 1
            else:
                seen_uris.add(uri)
                deduped_uris.append(uri)
                
        if duplicates == 0:
            return f"Playlist {pid} has no duplicate songs. It is already clean!"
            
        # Replace the entire playlist with the deduped list
        if deduped_uris:
            sp.playlist_replace_items(pid, deduped_uris[:100])
            for i in range(100, len(deduped_uris), 100):
                sp.playlist_add_items(pid, deduped_uris[i:i+100])
        else:
            sp.playlist_replace_items(pid, [])
            
        return f"Successfully removed {duplicates} duplicate songs from playlist {pid}! The playlist now has {len(deduped_uris)} unique songs."
    except Exception as e:
        return f"Error deduplicating playlist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True))
def add_songs_to_playlist(playlist_id: str, song_uris: List[str]) -> str:
    """Add a list of Spotify song URIs to an existing playlist.
    
    Args:
        playlist_id: The Spotify ID or URI of the playlist
        song_uris: List of Spotify song URIs (e.g. ['spotify:track:...', ...])
    """
    return add_tracks_to_playlist(playlist_id, song_uris)


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True))
def add_movie_songs_to_playlist(playlist_id: str, movie_name: str, max_songs: int = 5) -> str:
    """Find songs for a specific movie on Spotify and add them directly to an existing playlist.
    
    Args:
        playlist_id: The Spotify ID of the existing playlist
        movie_name: Title of the movie
        max_songs: Maximum number of songs to add (default: 5)
    """
    try:
        sp = get_spotify_client()
        pid = playlist_id.split(":")[-1].split("/")[-1].split("?")[0]
        tracks = fetch_tracks_for_movie(sp, movie_name, max_songs=max_songs)
        if not tracks:
            return f"No songs found on Spotify for movie '{movie_name}'."

        uris = [t["uri"] for t in tracks]
        sp.playlist_add_items(playlist_id=pid, items=uris)
        titles = ", ".join(f"'{t['title']}'" for t in tracks)
        return f"Added {len(uris)} song(s) from '{movie_name}' to playlist {pid} (Total songs added: {len(uris)}): {titles}"
    except Exception as e:
        return f"Error adding movie songs to playlist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def get_user_playlists(limit: int = 10) -> str:
    """Get the current user's playlists with song counts.
    
    Args:
        limit: Number of playlists to fetch (default 10, max 50)
    """
    try:
        sp = get_spotify_client()
        results = sp.current_user_playlists(limit=min(limit, 50))
        items = results.get("items", [])
        if not items:
            return "No playlists found."
        lines = [f"User Playlists (Total found: {len(items)}):"]
        for p in items:
            song_count = p.get('tracks', {}).get('total', 0)
            lines.append(f"- {p['name']} ({song_count} songs) [URI: {p['uri']}]")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching playlists: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True))
def reorder_playlist_by_audio_features(playlist_id: str, feature: str = 'energy', order: str = 'desc', ascending: Optional[bool] = None) -> str:
    """Smart Reorder: Sorts a user's playlist by a given audio feature (energy, valence, danceability, etc).
    
    Args:
        playlist_id: Spotify playlist ID or URI.
        feature: The audio feature to sort by (e.g., 'energy', 'valence', 'danceability', 'tempo').
        order: 'asc' for ascending, 'desc' for descending.
        ascending: Optional boolean (True for 'asc', False for 'desc'). Overrides order if provided.
    """
    if ascending is not None:
        order = 'asc' if ascending else 'desc'
    if feature not in ['energy', 'valence', 'danceability', 'tempo', 'acousticness', 'instrumentalness', 'liveness', 'speechiness']:
        return "Unsupported feature. Use energy, valence, danceability, tempo, etc."
    try:
        sp = get_spotify_client()
        # get all tracks
        results = sp.playlist_tracks(playlist_id)
        tracks = results['items']
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])
            
        # extract valid tracks
        track_uris = [item['track']['uri'] for item in tracks if item.get('track') and item['track']['uri']]
        if not track_uris:
            return "No tracks found in playlist."
            
        # fetch features in chunks of 100
        features = []
        for i in range(0, len(track_uris), 100):
            batch = sp.audio_features(track_uris[i:i+100])
            features.extend(batch)
            
        # pair and sort
        track_data = []
        for i, feat in enumerate(features):
            if feat is not None:
                track_data.append({'uri': track_uris[i], 'val': feat.get(feature, 0)})
            else:
                track_data.append({'uri': track_uris[i], 'val': 0})
                
        track_data.sort(key=lambda x: x['val'], reverse=(order == 'desc'))
        sorted_uris = [t['uri'] for t in track_data]
        
        # apply changes by replacing entire playlist tracks in batches of 100
        if sorted_uris:
            sp.playlist_replace_items(playlist_id, sorted_uris[:100])
            for i in range(100, len(sorted_uris), 100):
                sp.playlist_add_items(playlist_id, sorted_uris[i:i+100])
                
        return f"Playlist successfully reordered by {feature} in {order}ending order."
    except Exception as e:
        return f"Error reordering playlist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def update_playlist(playlist_id: str, name: Optional[str] = None, description: Optional[str] = None, public: Optional[bool] = None) -> str:
    """Update a playlist's name, description, or public status."""
    try:
        sp = get_spotify_client()
        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description
        if public is not None:
            kwargs["public"] = public
        sp.playlist_change_details(playlist_id, **kwargs)
        return f"Successfully updated playlist {playlist_id}."
    except Exception as e:
        return f"Error updating playlist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def get_playlist_tracks(playlist_id: str, limit: int = 100, offset: int = 0) -> str:
    """Get the tracks currently inside a specific playlist."""
    try:
        sp = get_spotify_client()
        results = sp.playlist_items(playlist_id, limit=limit, offset=offset)
        items = results.get("items", [])
        if not items:
            return "No tracks found in this playlist."
        output = [f"Playlist tracks (offset {offset}):"]
        for i, item in enumerate(items, 1):
            t = item.get("track", {})
            if not t:
                continue
            artists = ", ".join([a.get("name", "Unknown") for a in t.get("artists", [])])
            output.append(f"{i}. {t.get('name')} by {artists} (URI: {t.get('uri')})")
        return "\n".join(output)
    except Exception as e:
        return f"Error fetching playlist tracks: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=True))
def remove_tracks_from_playlist(playlist_id: str, uris: list[str]) -> str:
    """Remove one or more tracks from a playlist by their URIs."""
    try:
        sp = get_spotify_client()
        # Spotify API accepts up to 100 tracks per request
        for i in range(0, len(uris), 100):
            batch = uris[i:i+100]
            sp.playlist_remove_all_occurrences_of_items(playlist_id, batch)
        return f"Successfully removed {len(uris)} tracks from playlist {playlist_id}."
    except Exception as e:
        return f"Error removing tracks from playlist: {str(e)}"


# =====================================================================
# Standard Playlist Operations Tools (spotify_*)
# =====================================================================

@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_get_my_playlists(limit: int = 50, offset: int = 0) -> str:
    """List user's created and saved playlists.
    
    Args:
        limit: The maximum number of items to return (default: 50, max: 50).
        offset: The index of the first playlist to return (default: 0).
    """
    try:
        sp = get_spotify_client()
        limit = max(1, min(limit, 50))
        results = sp.current_user_playlists(limit=limit, offset=offset)
        items = results.get("items", [])
        total = results.get("total", len(items))
        
        if not items:
            return "No playlists found in your library."

        output = [f"Your Playlists (Total: {total}, showing {offset + 1} - {offset + len(items)}):"]
        for idx, p in enumerate(items, offset + 1):
            name = p.get("name", "Untitled")
            p_id = p.get("id", "")
            tracks_cnt = p.get("tracks", {}).get("total", 0)
            is_public = "Public" if p.get("public") else "Private"
            is_collab = " (Collaborative)" if p.get("collaborative") else ""
            owner = p.get("owner", {}).get("display_name", "Unknown")
            output.append(f"{idx}. {name} [{is_public}{is_collab}] - {tracks_cnt} tracks (ID: {p_id}, Owner: {owner})")
            
        return "\n".join(output)
    except Exception as e:
        return f"Error listing user playlists: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_get_playlist(playlist_id: str, fields: Optional[str] = None) -> str:
    """Fetch details and tracks of a specific playlist.
    
    Args:
        playlist_id: Spotify playlist ID or URI.
        fields: Optional filter for specific fields (e.g., 'name,description,followers,tracks.total').
    """
    try:
        sp = get_spotify_client()
        p = sp.playlist(playlist_id, fields=fields)
        if not p:
            return f"Playlist '{playlist_id}' not found."

        name = p.get("name", "Untitled")
        desc = p.get("description") or "(No description)"
        owner = p.get("owner", {}).get("display_name", "Unknown")
        followers = p.get("followers", {}).get("total", 0)
        tracks_total = p.get("tracks", {}).get("total", 0)
        is_public = "Public" if p.get("public") else "Private"
        url = p.get("external_urls", {}).get("spotify", "")
        images = p.get("images", [])
        cover_url = images[0].get("url") if images else "N/A"

        return (
            f"Playlist: {name}\n"
            f"ID: {p.get('id', playlist_id)}\n"
            f"Owner: {owner}\n"
            f"Status: {is_public}\n"
            f"Followers: {followers:,}\n"
            f"Total Tracks: {tracks_total}\n"
            f"Description: {desc}\n"
            f"Cover Image: {cover_url}\n"
            f"Link: {url}"
        )
    except Exception as e:
        return f"Error fetching playlist details: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_get_playlist_tracks(playlist_id: str, limit: int = 50, offset: int = 0) -> str:
    """Paginate through tracks in a playlist.
    
    Args:
        playlist_id: Spotify playlist ID or URI.
        limit: Number of tracks to return (default: 50, max: 100).
        offset: Index of the first track to return (default: 0).
    """
    try:
        sp = get_spotify_client()
        limit = max(1, min(limit, 100))
        results = sp.playlist_items(playlist_id, limit=limit, offset=offset)
        items = results.get("items", [])
        total = results.get("total", len(items))

        if not items:
            return f"No tracks found in playlist (offset: {offset})."

        output = [f"Tracks for Playlist '{playlist_id}' (Total: {total}, showing {offset + 1} - {offset + len(items)}):"]
        for idx, item in enumerate(items, offset + 1):
            t = item.get("track")
            if not t:
                continue
            name = t.get("name", "Unknown Track")
            artists = ", ".join(a.get("name", "Unknown") for a in t.get("artists", []))
            album = t.get("album", {}).get("name", "Unknown Album")
            uri = t.get("uri", "")
            duration_ms = t.get("duration_ms", 0)
            sec = duration_ms // 1000
            dur_str = f"{sec // 60}:{sec % 60:02d}"
            output.append(f"{idx}. {name} - {artists} ({dur_str}) [Album: {album}] (URI: {uri})")

        return "\n".join(output)
    except Exception as e:
        return f"Error fetching playlist tracks: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True))
def spotify_create_playlist(
    name: str,
    description: str = "",
    public: bool = True,
    collaborative: bool = False
) -> str:
    """Create a new empty playlist.
    
    Args:
        name: The name of the new playlist.
        description: Optional description for the playlist.
        public: Whether the playlist should be public (default: True).
        collaborative: Whether the playlist should be collaborative (default: False).
    """
    try:
        sp = get_spotify_client()
        user_info = sp.current_user()
        user_id = user_info["id"]

        if collaborative:
            public = False

        playlist = sp.user_playlist_create(
            user=user_id,
            name=name,
            public=public,
            collaborative=collaborative,
            description=description
        )
        p_id = playlist.get("id")
        p_url = playlist.get("external_urls", {}).get("spotify", "")
        return f"Successfully created playlist '{name}'!\nID: {p_id}\nURL: {p_url}"
    except Exception as e:
        return f"Error creating playlist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True))
def spotify_add_to_playlist(
    playlist_id: str,
    uris: List[str],
    position: Optional[int] = None
) -> str:
    """Append tracks to an existing playlist.
    
    Args:
        playlist_id: Spotify playlist ID or URI.
        uris: List of Spotify track URIs to add (e.g. ['spotify:track:...']).
        position: Optional zero-based position to insert the tracks at.
    """
    try:
        sp = get_spotify_client()
        valid_uris = [u for u in uris if u and (u.startswith("spotify:track:") or u.startswith("spotify:episode:"))]
        if not valid_uris:
            return "No valid Spotify track URIs provided."

        added = 0
        for i in range(0, len(valid_uris), 100):
            batch = valid_uris[i:i + 100]
            pos = (position + i) if position is not None else None
            sp.playlist_add_items(playlist_id, items=batch, position=pos)
            added += len(batch)

        return f"Successfully added {added} track(s) to playlist {playlist_id}."
    except Exception as e:
        return f"Error adding tracks to playlist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=True))
def spotify_remove_from_playlist(
    playlist_id: str,
    uris: List[str],
    snapshot_id: Optional[str] = None
) -> str:
    """Remove specific tracks from a playlist.
    
    Args:
        playlist_id: Spotify playlist ID or URI.
        uris: List of Spotify track URIs to remove.
        snapshot_id: Optional playlist snapshot ID to protect against concurrent modifications.
    """
    try:
        sp = get_spotify_client()
        valid_uris = [u for u in uris if u]
        if not valid_uris:
            return "No track URIs provided for removal."

        removed = 0
        for i in range(0, len(valid_uris), 100):
            batch = valid_uris[i:i + 100]
            sp.playlist_remove_all_occurrences_of_items(playlist_id, items=batch, snapshot_id=snapshot_id)
            removed += len(batch)

        return f"Successfully removed {removed} track(s) from playlist {playlist_id}."
    except Exception as e:
        return f"Error removing tracks from playlist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_reorder_playlist(
    playlist_id: str,
    range_start: int,
    insert_before: int,
    range_length: int = 1,
    snapshot_id: Optional[str] = None
) -> str:
    """Move or reorder track positions in a playlist.
    
    Args:
        playlist_id: Spotify playlist ID or URI.
        range_start: The zero-based index of the first track to be moved.
        insert_before: The zero-based index of where the tracks should be inserted.
        range_length: The amount of tracks to be moved (default: 1).
        snapshot_id: Optional playlist snapshot ID.
    """
    try:
        sp = get_spotify_client()
        res = sp.playlist_reorder_items(
            playlist_id=playlist_id,
            range_start=range_start,
            insert_before=insert_before,
            range_length=range_length,
            snapshot_id=snapshot_id
        )
        new_snapshot = res.get("snapshot_id", "updated")
        return f"Successfully reordered track(s) in playlist {playlist_id} (New snapshot ID: {new_snapshot})."
    except Exception as e:
        return f"Error reordering playlist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_update_playlist(
    playlist_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    public: Optional[bool] = None,
    collaborative: Optional[bool] = None
) -> str:
    """Modify playlist name, description, or privacy settings.
    
    Args:
        playlist_id: Spotify playlist ID or URI.
        name: Optional new name for the playlist.
        description: Optional new description.
        public: Optional public/private status.
        collaborative: Optional collaborative status.
    """
    try:
        sp = get_spotify_client()
        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description
        if public is not None:
            kwargs["public"] = public
        if collaborative is not None:
            kwargs["collaborative"] = collaborative

        if not kwargs:
            return "No update parameters provided."

        sp.playlist_change_details(playlist_id, **kwargs)
        updates = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        return f"Successfully updated playlist {playlist_id} ({updates})."
    except Exception as e:
        return f"Error updating playlist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_follow_playlist(playlist_id: str, public: bool = True) -> str:
    """Add a playlist to the user's library (Follow).
    
    Args:
        playlist_id: Spotify playlist ID or URI to follow.
        public: Whether to include the followed playlist in the user's public profile (default: True).
    """
    try:
        sp = get_spotify_client()
        sp.current_user_follow_playlist(playlist_id)
        return f"Successfully added playlist {playlist_id} to your Spotify library (Followed)."
    except Exception as e:
        return f"Error following playlist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=True))
def spotify_unfollow_playlist(playlist_id: str) -> str:
    """Remove a playlist from the user's library (Unfollow/Delete).
    
    Args:
        playlist_id: Spotify playlist ID or URI to unfollow.
    """
    try:
        sp = get_spotify_client()
        sp.current_user_unfollow_playlist(playlist_id)
        return f"Successfully removed playlist {playlist_id} from your Spotify library (Unfollowed)."
    except Exception as e:
        return f"Error unfollowing playlist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_get_playlist_cover(playlist_id: str) -> str:
    """Get the image URL for a playlist cover.
    
    Args:
        playlist_id: Spotify playlist ID or URI.
    """
    try:
        sp = get_spotify_client()
        images = sp.playlist_cover_image(playlist_id)
        if not images:
            return f"No cover images found for playlist {playlist_id}."

        lines = [f"Cover image(s) for playlist {playlist_id}:"]
        for idx, img in enumerate(images, 1):
            dim = f"{img.get('width', '?')}x{img.get('height', '?')}" if img.get('width') else "Standard"
            lines.append(f"{idx}. {dim}: {img.get('url')}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching playlist cover: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_check_playlist_followers(playlist_id: str, user_ids: List[str]) -> str:
    """Check if specific users follow a playlist.
    
    Args:
        playlist_id: Spotify playlist ID or URI.
        user_ids: List of Spotify user IDs to check (e.g. ['user1', 'user2']).
    """
    try:
        sp = get_spotify_client()
        if not user_ids:
            return "No user IDs provided to check."

        results = sp.playlist_is_following(playlist_id, user_ids)
        lines = [f"Follower check for playlist {playlist_id}:"]
        for uid, is_following in zip(user_ids, results):
            status = "Follows this playlist" if is_following else "Does NOT follow this playlist"
            lines.append(f"• User '{uid}': {status}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error checking playlist followers: {str(e)}"


# ==============================================================================
# PLAYLIST POWER TOOLS
# ==============================================================================

def _clean_playlist_id(pid: str) -> str:
    pid = (pid or "").strip()
    if "playlist/" in pid:
        pid = pid.split("playlist/")[1]
    elif "spotify:playlist:" in pid:
        pid = pid.split("spotify:playlist:")[1]
    return pid.split("?")[0].split("/")[0]


def _fetch_all_playlist_tracks(sp, playlist_id: str) -> List[Dict[str, Any]]:
    clean_id = _clean_playlist_id(playlist_id)
    items = []
    res = sp.playlist_items(clean_id, limit=100)
    while res:
        items.extend(res.get("items", []))
        if res.get("next"):
            res = sp.next(res)
        else:
            break
    return items


def _get_track_key(track: Dict[str, Any], strategy: str = "uri") -> str:
    if strategy == "name_and_artist":
        name = (track.get("name") or "").strip().lower()
        artists = ", ".join((a.get("name") or "").strip().lower() for a in track.get("artists", []))
        return f"{name}::{artists}"
    return track.get("uri") or ""


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True))
def spotify_merge_playlists(
    playlist_ids: List[str],
    target_playlist_id: Optional[str] = None,
    new_name: Optional[str] = "Merged Playlist",
    description: Optional[str] = "Merged playlist created via Spotify MCP Power Tools",
    public: bool = False,
    deduplicate: bool = True
) -> str:
    """Combine multiple playlists into a single new or existing playlist.
    
    Args:
        playlist_ids: List of Spotify playlist IDs, URIs, or URLs to merge.
        target_playlist_id: Optional existing playlist ID or URL to append to. If not provided, creates a new playlist.
        new_name: Name for the newly created playlist (if target_playlist_id is not provided).
        description: Description for the new playlist.
        public: Whether the newly created playlist should be public (default: False).
        deduplicate: Whether to remove duplicate tracks across playlists (default: True).
    """
    try:
        sp = get_spotify_client()
        if not playlist_ids:
            return "No playlist IDs provided to merge."

        all_uris: List[str] = []
        source_names: List[str] = []

        for raw_pid in playlist_ids:
            pid = _clean_playlist_id(raw_pid)
            if not pid:
                continue
            try:
                p_info = sp.playlist(pid, fields="name")
                source_names.append(p_info.get("name", pid))
            except Exception:
                source_names.append(pid)

            items = _fetch_all_playlist_tracks(sp, pid)
            for it in items:
                t = it.get("track")
                if t and t.get("uri") and t["uri"].startswith("spotify:track:"):
                    all_uris.append(t["uri"])

        if not all_uris:
            return "No valid tracks found across the specified playlists to merge."

        if deduplicate:
            seen = set()
            unique_uris = []
            for u in all_uris:
                if u not in seen:
                    seen.add(u)
                    unique_uris.append(u)
            final_uris = unique_uris
        else:
            final_uris = all_uris

        if target_playlist_id:
            tgt_id = _clean_playlist_id(target_playlist_id)
            tgt_info = sp.playlist(tgt_id, fields="name,external_urls")
            tgt_name = tgt_info.get("name", tgt_id)
            tgt_url = tgt_info.get("external_urls", {}).get("spotify", "")

            for i in range(0, len(final_uris), 100):
                sp.playlist_add_items(tgt_id, final_uris[i:i + 100])

            return (
                f"Successfully merged {len(playlist_ids)} playlists into existing playlist '{tgt_name}'!\n"
                f"Target ID: {tgt_id}\n"
                f"Target URL: {tgt_url}\n"
                f"Tracks Added: {len(final_uris)} (Deduplicated: {deduplicate})\n"
                f"Sources: {', '.join(source_names)}"
            )
        else:
            user_info = sp.current_user()
            user_id = user_info["id"]
            name = new_name or "Merged Playlist"
            desc = description or "Merged playlist created via Spotify MCP Power Tools"
            new_pl = sp.user_playlist_create(user_id, name=name, public=public, description=desc)
            new_pid = new_pl["id"]
            new_url = new_pl.get("external_urls", {}).get("spotify", "")

            for i in range(0, len(final_uris), 100):
                sp.playlist_add_items(new_pid, final_uris[i:i + 100])

            return (
                f"Successfully merged {len(playlist_ids)} playlists into brand new playlist '{name}'!\n"
                f"New Playlist ID: {new_pid}\n"
                f"New Playlist URL: {new_url}\n"
                f"Total Tracks: {len(final_uris)} (Deduplicated: {deduplicate})\n"
                f"Sources: {', '.join(source_names)}"
            )
    except Exception as e:
        return f"Error merging playlists: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True))
def spotify_split_playlist_by_artist(
    playlist_id: str,
    min_tracks_per_artist: int = 2,
    create_playlists: bool = False,
    public: bool = False
) -> str:
    """Separate tracks in a playlist into sub-playlists by artist.
    
    Args:
        playlist_id: Spotify playlist ID, URI, or URL.
        min_tracks_per_artist: Minimum number of tracks an artist must have to get their own sub-playlist (default: 2).
        create_playlists: If True, creates the new sub-playlists on Spotify. If False (default), returns a preview breakdown.
        public: Whether created sub-playlists should be public (default: False).
    """
    try:
        sp = get_spotify_client()
        pid = _clean_playlist_id(playlist_id)
        pl = sp.playlist(pid, fields="name")
        orig_name = pl.get("name", "Playlist")

        items = _fetch_all_playlist_tracks(sp, pid)
        if not items:
            return f"Playlist '{orig_name}' has no tracks to split."

        artist_map: Dict[str, List[Dict[str, Any]]] = {}
        for it in items:
            t = it.get("track")
            if not t or not t.get("uri") or not t["uri"].startswith("spotify:track:"):
                continue
            art_list = t.get("artists", [])
            p_artist = art_list[0].get("name", "Unknown Artist") if art_list else "Unknown Artist"
            artist_map.setdefault(p_artist, []).append(t)

        qualifying = {art: tracks for art, tracks in artist_map.items() if len(tracks) >= min_tracks_per_artist}
        other_tracks = [t for art, tracks in artist_map.items() if len(tracks) < min_tracks_per_artist for t in tracks]

        sorted_artists = sorted(qualifying.items(), key=lambda x: len(x[1]), reverse=True)

        if not create_playlists:
            lines = [
                f"Split Preview for Playlist '{orig_name}' (Total Tracks: {len(items)}, Min Tracks: {min_tracks_per_artist}):",
                f"Qualifying Artists ({len(sorted_artists)}):"
            ]
            for art, tracks in sorted_artists:
                sample = ", ".join(f"'{t.get('name')}'" for t in tracks[:3])
                suffix = "..." if len(tracks) > 3 else ""
                lines.append(f"• {art}: {len(tracks)} track(s) ({sample}{suffix})")

            if other_tracks:
                lines.append(f"• Other / Various Artists: {len(other_tracks)} track(s) (artists with < {min_tracks_per_artist} songs)")

            lines.append("\nTo create these sub-playlists in your library, call this tool with create_playlists=True.")
            return "\n".join(lines)
        else:
            user_info = sp.current_user()
            user_id = user_info["id"]
            created = []

            for art, tracks in sorted_artists:
                sub_name = f"{orig_name} - {art}"
                sub_desc = f"Artist split of '{orig_name}' containing songs by {art}. Created by Spotify MCP."
                sub_pl = sp.user_playlist_create(user_id, name=sub_name, public=public, description=sub_desc)
                sub_id = sub_pl["id"]
                sub_url = sub_pl.get("external_urls", {}).get("spotify", "")
                uris = [t["uri"] for t in tracks]
                for i in range(0, len(uris), 100):
                    sp.playlist_add_items(sub_id, uris[i:i + 100])
                created.append(f"• '{sub_name}': {len(tracks)} tracks (ID: {sub_id}) - {sub_url}")

            if other_tracks:
                sub_name = f"{orig_name} - Various Artists"
                sub_desc = f"Remaining tracks from '{orig_name}' with fewer than {min_tracks_per_artist} songs per artist. Created by Spotify MCP."
                sub_pl = sp.user_playlist_create(user_id, name=sub_name, public=public, description=sub_desc)
                sub_id = sub_pl["id"]
                sub_url = sub_pl.get("external_urls", {}).get("spotify", "")
                uris = [t["uri"] for t in other_tracks]
                for i in range(0, len(uris), 100):
                    sp.playlist_add_items(sub_id, uris[i:i + 100])
                created.append(f"• '{sub_name}': {len(other_tracks)} tracks (ID: {sub_id}) - {sub_url}")

            return f"Successfully created {len(created)} sub-playlists from '{orig_name}':\n" + "\n".join(created)
    except Exception as e:
        return f"Error splitting playlist by artist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=True))
def spotify_deduplicate_playlist(
    playlist_id: str,
    strategy: str = "uri",
    dry_run: bool = False
) -> str:
    """Scan and strip out duplicate tracks from a playlist.
    
    Args:
        playlist_id: Spotify playlist ID, URI, or URL.
        strategy: Matching strategy - 'uri' (exact Spotify track URI) or 'name_and_artist' (normalized song title + artist name). Default: 'uri'.
        dry_run: If True, only scans and returns found duplicates without modifying the playlist. Default: False.
    """
    try:
        sp = get_spotify_client()
        pid = _clean_playlist_id(playlist_id)
        pl = sp.playlist(pid, fields="name")
        p_name = pl.get("name", pid)

        items = _fetch_all_playlist_tracks(sp, pid)
        if not items:
            return f"Playlist '{p_name}' ({pid}) has no tracks."

        seen = set()
        duplicates: List[Dict[str, Any]] = []
        unique_uris: List[str] = []

        for idx, it in enumerate(items, 1):
            t = it.get("track")
            if not t or not t.get("uri") or not t["uri"].startswith("spotify:track:"):
                continue
            key = _get_track_key(t, strategy=strategy)
            if key in seen:
                artists = ", ".join(a.get("name", "Unknown") for a in t.get("artists", []))
                duplicates.append({
                    "position": idx,
                    "name": t.get("name"),
                    "artist": artists,
                    "uri": t.get("uri")
                })
            else:
                seen.add(key)
                unique_uris.append(t["uri"])

        if not duplicates:
            return f"Playlist '{p_name}' ({pid}) contains no duplicate tracks ({len(items)} tracks checked, strategy='{strategy}'). It is already clean!"

        if dry_run:
            lines = [
                f"Scan Complete: Found {len(duplicates)} duplicate track(s) in playlist '{p_name}' (Total tracks: {len(items)}, Unique: {len(unique_uris)}, Strategy: {strategy}):"
            ]
            for d in duplicates[:20]:
                lines.append(f"• Pos {d['position']}: '{d['name']}' by {d['artist']}")
            if len(duplicates) > 20:
                lines.append(f"... and {len(duplicates) - 20} more duplicate(s).")
            lines.append("\nSet dry_run=False to remove these duplicate tracks from the playlist.")
            return "\n".join(lines)
        else:
            if unique_uris:
                sp.playlist_replace_items(pid, unique_uris[:100])
                for i in range(100, len(unique_uris), 100):
                    sp.playlist_add_items(pid, unique_uris[i:i + 100])
            else:
                sp.playlist_replace_items(pid, [])

            return (
                f"Successfully deduplicated playlist '{p_name}' ({pid})!\n"
                f"Removed: {len(duplicates)} duplicate track(s).\n"
                f"Remaining Unique Tracks: {len(unique_uris)}.\n"
                f"Strategy: {strategy}."
            )
    except Exception as e:
        return f"Error deduplicating playlist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_export_playlist(
    playlist_id: str,
    include_audio_features: bool = False
) -> str:
    """Export full playlist data, track metadata, and audio features to structured JSON.
    
    Args:
        playlist_id: Spotify playlist ID, URI, or URL.
        include_audio_features: Whether to include audio features (tempo, energy, valence, danceability, etc.). Default: False.
    """
    try:
        sp = get_spotify_client()
        pid = _clean_playlist_id(playlist_id)
        p = sp.playlist(pid)

        items = _fetch_all_playlist_tracks(sp, pid)
        tracks_data = []
        track_ids = []

        for idx, it in enumerate(items, 1):
            t = it.get("track")
            if not t:
                continue
            tid = t.get("id")
            album = t.get("album", {})
            entry = {
                "position": idx,
                "id": tid,
                "name": t.get("name"),
                "artists": [a.get("name") for a in t.get("artists", [])],
                "album": album.get("name"),
                "release_date": album.get("release_date"),
                "duration_ms": t.get("duration_ms"),
                "popularity": t.get("popularity"),
                "explicit": t.get("explicit"),
                "uri": t.get("uri"),
                "added_at": it.get("added_at")
            }
            tracks_data.append(entry)
            if tid:
                track_ids.append(tid)

        if include_audio_features and track_ids:
            features_map = {}
            for i in range(0, len(track_ids), 100):
                batch_ids = track_ids[i:i + 100]
                try:
                    feat_res = sp.audio_features(batch_ids)
                    for f in feat_res or []:
                        if f and f.get("id"):
                            features_map[f["id"]] = {
                                "danceability": f.get("danceability"),
                                "energy": f.get("energy"),
                                "key": f.get("key"),
                                "loudness": f.get("loudness"),
                                "mode": f.get("mode"),
                                "speechiness": f.get("speechiness"),
                                "acousticness": f.get("acousticness"),
                                "instrumentalness": f.get("instrumentalness"),
                                "liveness": f.get("liveness"),
                                "valence": f.get("valence"),
                                "tempo": f.get("tempo")
                            }
                except Exception:
                    pass

            for entry in tracks_data:
                entry["audio_features"] = features_map.get(entry.get("id"))

        owner = p.get("owner", {})
        images = p.get("images", [])
        export_payload = {
            "playlist": {
                "id": p.get("id", pid),
                "name": p.get("name"),
                "description": p.get("description"),
                "owner": owner.get("display_name"),
                "owner_id": owner.get("id"),
                "followers": p.get("followers", {}).get("total", 0),
                "public": p.get("public"),
                "collaborative": p.get("collaborative"),
                "cover_url": images[0].get("url") if images else None,
                "spotify_url": p.get("external_urls", {}).get("spotify"),
                "total_tracks": len(tracks_data)
            },
            "tracks": tracks_data
        }
        return json.dumps(export_payload, indent=2)
    except Exception as e:
        return f"Error exporting playlist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_playlist_diff(
    playlist_id_a: str,
    playlist_id_b: str,
    strategy: str = "uri"
) -> str:
    """Compare two playlists to find unique and shared tracks.
    
    Args:
        playlist_id_a: First Spotify playlist ID, URI, or URL.
        playlist_id_b: Second Spotify playlist ID, URI, or URL.
        strategy: Matching strategy - 'uri' or 'name_and_artist' (default: 'uri').
    """
    try:
        sp = get_spotify_client()
        pid_a = _clean_playlist_id(playlist_id_a)
        pid_b = _clean_playlist_id(playlist_id_b)

        p_a = sp.playlist(pid_a, fields="name")
        p_b = sp.playlist(pid_b, fields="name")
        name_a = p_a.get("name", pid_a)
        name_b = p_b.get("name", pid_b)

        items_a = _fetch_all_playlist_tracks(sp, pid_a)
        items_b = _fetch_all_playlist_tracks(sp, pid_b)

        tracks_a: Dict[str, Dict[str, Any]] = {}
        tracks_b: Dict[str, Dict[str, Any]] = {}

        for it in items_a:
            t = it.get("track")
            if t and t.get("uri"):
                k = _get_track_key(t, strategy)
                if k not in tracks_a:
                    tracks_a[k] = t

        for it in items_b:
            t = it.get("track")
            if t and t.get("uri"):
                k = _get_track_key(t, strategy)
                if k not in tracks_b:
                    tracks_b[k] = t

        keys_a = set(tracks_a.keys())
        keys_b = set(tracks_b.keys())

        shared_keys = keys_a & keys_b
        only_a_keys = keys_a - keys_b
        only_b_keys = keys_b - keys_a
        union_keys = keys_a | keys_b

        similarity = (len(shared_keys) / len(union_keys) * 100) if union_keys else 0.0

        lines = [
            f"Playlist Comparison (Strategy: {strategy}):",
            f"• Playlist A: '{name_a}' ({len(tracks_a)} tracks)",
            f"• Playlist B: '{name_b}' ({len(tracks_b)} tracks)",
            f"• Similarity Index: {similarity:.1f}%",
            f"• Shared Tracks: {len(shared_keys)}",
            f"• Unique to '{name_a}': {len(only_a_keys)}",
            f"• Unique to '{name_b}': {len(only_b_keys)}",
            "\nShared Track Examples:"
        ]
        for k in list(shared_keys)[:5]:
            t = tracks_a[k]
            art = ", ".join(a.get("name", "") for a in t.get("artists", []))
            lines.append(f"  - '{t.get('name')}' by {art}")
        if not shared_keys:
            lines.append("  (No shared tracks found)")

        lines.append(f"\nUnique to '{name_a}' Examples:")
        for k in list(only_a_keys)[:5]:
            t = tracks_a[k]
            art = ", ".join(a.get("name", "") for a in t.get("artists", []))
            lines.append(f"  - '{t.get('name')}' by {art}")
        if not only_a_keys:
            lines.append("  (None)")

        lines.append(f"\nUnique to '{name_b}' Examples:")
        for k in list(only_b_keys)[:5]:
            t = tracks_b[k]
            art = ", ".join(a.get("name", "") for a in t.get("artists", []))
            lines.append(f"  - '{t.get('name')}' by {art}")
        if not only_b_keys:
            lines.append("  (None)")

        return "\n".join(lines)
    except Exception as e:
        return f"Error comparing playlists: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_find_playlist_overlaps(
    limit: int = 20,
    min_overlap: int = 2
) -> str:
    """Scan all user playlists to identify cross-playlist overlaps.
    
    Args:
        limit: Number of user playlists to scan (default: 20, max: 50).
        min_overlap: Minimum shared tracks between two playlists to report (default: 2).
    """
    try:
        sp = get_spotify_client()
        limit = max(2, min(limit, 50))
        res = sp.current_user_playlists(limit=limit)
        items = res.get("items", [])
        if len(items) < 2:
            return "Need at least 2 user playlists to analyze overlaps."

        playlists_data = []
        for p in items:
            pid = p["id"]
            p_name = p.get("name", pid)
            tracks = _fetch_all_playlist_tracks(sp, pid)
            uris = set()
            uri_to_name = {}
            for it in tracks:
                t = it.get("track")
                if t and t.get("uri") and t["uri"].startswith("spotify:track:"):
                    uris.add(t["uri"])
                    uri_to_name[t["uri"]] = f"'{t.get('name')}' by {', '.join(a.get('name','') for a in t.get('artists', []))}"
            playlists_data.append({
                "id": pid,
                "name": p_name,
                "uris": uris,
                "uri_map": uri_to_name
            })

        overlap_pairs = []
        for i in range(len(playlists_data)):
            for j in range(i + 1, len(playlists_data)):
                p1 = playlists_data[i]
                p2 = playlists_data[j]
                shared = p1["uris"] & p2["uris"]
                if len(shared) >= min_overlap:
                    min_len = min(len(p1["uris"]), len(p2["uris"])) or 1
                    overlap_pct = (len(shared) / min_len) * 100
                    overlap_pairs.append({
                        "p1": p1["name"],
                        "p1_len": len(p1["uris"]),
                        "p2": p2["name"],
                        "p2_len": len(p2["uris"]),
                        "shared_count": len(shared),
                        "overlap_pct": overlap_pct,
                        "sample_shared": [p1["uri_map"].get(u) for u in list(shared)[:3] if p1["uri_map"].get(u)]
                    })

        overlap_pairs.sort(key=lambda x: x["shared_count"], reverse=True)

        if not overlap_pairs:
            return f"Scanned {len(playlists_data)} playlists. No pairs found with at least {min_overlap} shared tracks."

        lines = [
            f"Cross-Playlist Overlap Scan (Scanned {len(playlists_data)} playlists, Min Overlap: {min_overlap} tracks):",
            f"Found {len(overlap_pairs)} overlapping playlist pair(s):\n"
        ]
        for idx, pair in enumerate(overlap_pairs, 1):
            lines.append(f"{idx}. '{pair['p1']}' ({pair['p1_len']} tracks) ✕ '{pair['p2']}' ({pair['p2_len']} tracks)")
            lines.append(f"   Shared: {pair['shared_count']} tracks ({pair['overlap_pct']:.1f}% overlap of smaller playlist)")
            if pair['sample_shared']:
                lines.append(f"   Samples: {', '.join(pair['sample_shared'])}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error scanning playlist overlaps: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_find_playlist_subsets(
    limit: int = 20,
    threshold: float = 1.0
) -> str:
    """Detect if any user playlists are complete or near-complete subsets of another playlist.
    
    Args:
        limit: Number of user playlists to scan (default: 20, max: 50).
        threshold: Containment threshold between 0.5 and 1.0 (default: 1.0 = 100% complete subset).
    """
    try:
        sp = get_spotify_client()
        limit = max(2, min(limit, 50))
        threshold = max(0.5, min(threshold, 1.0))

        res = sp.current_user_playlists(limit=limit)
        items = res.get("items", [])
        if len(items) < 2:
            return "Need at least 2 user playlists to analyze subsets."

        playlists_data = []
        for p in items:
            pid = p["id"]
            p_name = p.get("name", pid)
            tracks = _fetch_all_playlist_tracks(sp, pid)
            uris = set()
            for it in tracks:
                t = it.get("track")
                if t and t.get("uri") and t["uri"].startswith("spotify:track:"):
                    uris.add(t["uri"])
            playlists_data.append({
                "id": pid,
                "name": p_name,
                "uris": uris
            })

        subsets = []
        for i in range(len(playlists_data)):
            for j in range(len(playlists_data)):
                if i == j:
                    continue
                p_sub = playlists_data[i]
                p_super = playlists_data[j]
                if not p_sub["uris"]:
                    continue
                shared = p_sub["uris"] & p_super["uris"]
                ratio = len(shared) / len(p_sub["uris"])
                if ratio >= threshold:
                    subsets.append({
                        "sub_name": p_sub["name"],
                        "sub_id": p_sub["id"],
                        "sub_len": len(p_sub["uris"]),
                        "super_name": p_super["name"],
                        "super_id": p_super["id"],
                        "super_len": len(p_super["uris"]),
                        "ratio": ratio,
                        "shared_count": len(shared)
                    })

        subsets.sort(key=lambda x: (x["ratio"], -x["sub_len"]), reverse=True)

        if not subsets:
            pct_str = f"{threshold * 100:.0f}%"
            return f"Scanned {len(playlists_data)} playlists. No subsets found meeting the {pct_str} containment threshold."

        lines = [
            f"Playlist Subset Detection (Scanned {len(playlists_data)} playlists, Threshold: {threshold * 100:.0f}%):",
            f"Detected {len(subsets)} subset relation(s):\n"
        ]
        for idx, s in enumerate(subsets, 1):
            is_exact = s["ratio"] >= 0.999
            tag = "COMPLETE SUBSET (100%)" if is_exact else f"NEAR SUBSET ({s['ratio'] * 100:.1f}%)"
            lines.append(f"{idx}. [{tag}]")
            lines.append(f"   '{s['sub_name']}' ({s['sub_len']} tracks) ⊆ '{s['super_name']}' ({s['super_len']} tracks)")
            lines.append(f"   Shared Tracks: {s['shared_count']} of {s['sub_len']}")
            if is_exact:
                lines.append(f"   💡 Recommendation: '{s['sub_name']}' is fully redundant and contained in '{s['super_name']}'.")

        return "\n".join(lines)
    except Exception as e:
        return f"Error detecting playlist subsets: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True))
def spotify_absorb_playlist(
    source_playlist_id: str,
    target_playlist_id: str,
    strategy: str = "uri"
) -> str:
    """Pull only missing/unique tracks from a source playlist into a destination playlist.
    
    Args:
        source_playlist_id: Spotify playlist ID, URI, or URL to pull missing tracks from.
        target_playlist_id: Destination Spotify playlist ID, URI, or URL to receive the new tracks.
        strategy: Matching strategy - 'uri' or 'name_and_artist' (default: 'uri').
    """
    try:
        sp = get_spotify_client()
        src_id = _clean_playlist_id(source_playlist_id)
        tgt_id = _clean_playlist_id(target_playlist_id)

        p_src = sp.playlist(src_id, fields="name")
        p_tgt = sp.playlist(tgt_id, fields="name,external_urls")
        src_name = p_src.get("name", src_id)
        tgt_name = p_tgt.get("name", tgt_id)
        tgt_url = p_tgt.get("external_urls", {}).get("spotify", "")

        src_items = _fetch_all_playlist_tracks(sp, src_id)
        tgt_items = _fetch_all_playlist_tracks(sp, tgt_id)

        existing_keys = set()
        for it in tgt_items:
            t = it.get("track")
            if t and t.get("uri"):
                existing_keys.add(_get_track_key(t, strategy))

        missing_uris: List[str] = []
        missing_names: List[str] = []
        skipped_count = 0

        for it in src_items:
            t = it.get("track")
            if not t or not t.get("uri") or not t["uri"].startswith("spotify:track:"):
                continue
            k = _get_track_key(t, strategy)
            if k in existing_keys:
                skipped_count += 1
            else:
                existing_keys.add(k)
                missing_uris.append(t["uri"])
                art = ", ".join(a.get("name", "") for a in t.get("artists", []))
                missing_names.append(f"'{t.get('name')}' by {art}")

        if not missing_uris:
            return (
                f"Destination playlist '{tgt_name}' already contains all tracks from '{src_name}'!\n"
                f"Checked {len(src_items)} source tracks (Strategy: {strategy}). None needed to be absorbed."
            )

        for i in range(0, len(missing_uris), 100):
            sp.playlist_add_items(tgt_id, missing_uris[i:i + 100])

        new_total = len(tgt_items) + len(missing_uris)
        lines = [
            f"Successfully absorbed {len(missing_uris)} missing track(s) from '{src_name}' into '{tgt_name}'!",
            f"Destination URL: {tgt_url}",
            f"Tracks Absorbed: {len(missing_uris)}",
            f"Already Present (Skipped): {skipped_count}",
            f"New Destination Total: {new_total} tracks (Strategy: {strategy})",
            "\nSample Absorbed Tracks:"
        ]
        for name in missing_names[:5]:
            lines.append(f"• {name}")
        if len(missing_names) > 5:
            lines.append(f"... and {len(missing_names) - 5} more.")

        return "\n".join(lines)
    except Exception as e:
        return f"Error absorbing playlist: {str(e)}"





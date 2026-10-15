from typing import Optional, List, Dict, Any
from mcp.types import ToolAnnotations
from tools.core import mcp, get_spotify_client
import spotipy

@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def get_user_top_tracks(limit: int = 10, time_range: str = "medium_term") -> str:
    """Get the current user's top songs over a specified period.
    
    Args:
        limit: Number of songs (default 10, max 50)
        time_range: Over what time frame ('short_term' = ~4 weeks, 'medium_term' = ~6 months, 'long_term' = years)
    """
    try:
        sp = get_spotify_client()
        results = sp.current_user_top_tracks(limit=min(limit, 50), time_range=time_range)
        items = results.get("items", [])
        if not items:
            return "No top songs found."
        lines = [f"Top Songs ({time_range}) - Total count: {len(items)}:"]
        for idx, t in enumerate(items, 1):
            artists = ", ".join(a["name"] for a in t["artists"])
            lines.append(f"{idx}. {t['name']} - {artists} (URI: {t['uri']})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching top songs: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def get_user_top_songs(limit: int = 10, time_range: str = "medium_term") -> str:
    """Get the current user's top songs over a specified period."""
    return get_user_top_tracks(limit=limit, time_range=time_range)


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def get_user_top_artists(limit: int = 10, time_range: str = "medium_term") -> str:
    """Get the current user's top artists over a specified period.
    
    Args:
        limit: Number of artists (default 10, max 50)
        time_range: Over what time frame ('short_term', 'medium_term', 'long_term')
    """
    try:
        sp = get_spotify_client()
        results = sp.current_user_top_artists(limit=min(limit, 50), time_range=time_range)
        items = results.get("items", [])
        if not items:
            return "No top artists found."
        lines = [f"Top Artists ({time_range}) - Total count: {len(items)}:"]
        for idx, a in enumerate(items, 1):
            lines.append(f"{idx}. {a['name']} (URI: {a['uri']})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching top artists: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def get_audio_features(track_uris: list[str]) -> str:
    """Get audio features (danceability, energy, valence, etc) for multiple tracks.
    
    Args:
        track_uris: List of Spotify track URIs (max 100).
    """
    try:
        sp = get_spotify_client()
        features = sp.audio_features(tracks=track_uris[:100])
        lines = ["Audio Features:"]
        for i, feat in enumerate(features):
            if not feat:
                lines.append(f"Track {i+1}: Features not found")
                continue
            lines.append(f"Track URI: {feat.get('uri')}")
            lines.append(f"  Danceability: {feat.get('danceability')} | Energy: {feat.get('energy')} | Valence: {feat.get('valence')}")
            lines.append(f"  Tempo: {feat.get('tempo')} BPM | Key: {feat.get('key')} | Mode: {'Major' if feat.get('mode') == 1 else 'Minor'}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching audio features: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def get_artist_network(artist_name_or_id: str) -> str:
    """Map an artist's network by fetching related artists.
    
    Args:
        artist_name_or_id: Name or Spotify ID of the artist.
    """
    try:
        sp = get_spotify_client()
        # Search if not an ID/URI
        artist_id = artist_name_or_id
        if not artist_id.startswith('spotify:artist:') and len(artist_id) != 22:
            results = sp.search(q=artist_name_or_id, type='artist', limit=1)
            if not results['artists']['items']:
                return "Artist not found."
            artist_id = results['artists']['items'][0]['id']
            artist_name = results['artists']['items'][0]['name']
        else:
            artist_name = sp.artist(artist_id)['name']

        related = sp.artist_related_artists(artist_id)
        items = related.get('artists', [])
        if not items:
            return f"No related artists found for {artist_name}."
        
        lines = [f"Related Artists for {artist_name} (Network):"]
        for a in items:
            lines.append(f"- {a['name']} (URI: {a['uri']}, Genres: {', '.join(a.get('genres', [])[:3])})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error mapping artist network: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def get_saved_tracks(limit: int = 50, offset: int = 0) -> str:
    """Get tracks from the user's Library (Saved Tracks)."""
    try:
        sp = get_spotify_client()
        results = sp.current_user_saved_tracks(limit=limit, offset=offset)
        items = results.get("items", [])
        if not items:
            return "No saved tracks found in your library."
        output = [f"Found {len(items)} saved tracks (offset {offset}):"]
        for i, item in enumerate(items, 1):
            t = item.get("track", {})
            artists = ", ".join([a.get("name", "Unknown") for a in t.get("artists", [])])
            output.append(f"{i}. {t.get('name')} by {artists} (URI: {t.get('uri')})")
        return "\n".join(output)
    except Exception as e:
        return f"Error fetching saved tracks: {str(e)}"

@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def get_recommendations(
    limit: int = 10,
    seed_tracks: Optional[List[str]] = None,
    seed_artists: Optional[List[str]] = None,
    seed_genres: Optional[List[str]] = None,
    target_energy: Optional[float] = None,
    target_valence: Optional[float] = None,
    target_danceability: Optional[float] = None,
    target_acousticness: Optional[float] = None,
    target_instrumentalness: Optional[float] = None,
    target_tempo: Optional[float] = None
) -> str:
    """Get track recommendations based on seeds and audio features.
    
    Args:
        limit: Number of recommendations to return (default: 10, max: 100).
        seed_tracks: List of Spotify track IDs or URIs.
        seed_artists: List of Spotify artist IDs or URIs.
        seed_genres: List of genres (e.g., 'synthwave', 'indie-pop').
        target_energy: Target energy (0.0 to 1.0).
        target_valence: Target valence (0.0 to 1.0).
        target_danceability: Target danceability (0.0 to 1.0).
        target_acousticness: Target acousticness (0.0 to 1.0).
        target_instrumentalness: Target instrumentalness (0.0 to 1.0).
        target_tempo: Target tempo in BPM.
    """
    try:
        sp = get_spotify_client()
        
        # Ensure total seeds do not exceed 5
        num_seeds = (len(seed_tracks) if seed_tracks else 0) + \
                    (len(seed_artists) if seed_artists else 0) + \
                    (len(seed_genres) if seed_genres else 0)
        
        if num_seeds == 0:
            return "Error: You must provide at least one seed (track, artist, or genre)."
        if num_seeds > 5:
            return f"Error: Up to 5 seed values may be provided in any combination of seed_tracks, seed_artists, and seed_genres. You provided {num_seeds}."
            
        kwargs = {}
        if target_energy is not None: kwargs["target_energy"] = target_energy
        if target_valence is not None: kwargs["target_valence"] = target_valence
        if target_danceability is not None: kwargs["target_danceability"] = target_danceability
        if target_acousticness is not None: kwargs["target_acousticness"] = target_acousticness
        if target_instrumentalness is not None: kwargs["target_instrumentalness"] = target_instrumentalness
        if target_tempo is not None: kwargs["target_tempo"] = target_tempo

        results = sp.recommendations(
            seed_tracks=seed_tracks,
            seed_artists=seed_artists,
            seed_genres=seed_genres,
            limit=min(limit, 100),
            **kwargs
        )
        
        tracks = results.get("tracks", [])
        if not tracks:
            return "No recommendations found for the given seeds and targets."
            
        output = [f"Found {len(tracks)} recommendations:"]
        for i, t in enumerate(tracks, 1):
            artists = ", ".join([a.get("name", "Unknown") for a in t.get("artists", [])])
            output.append(f"{i}. {t.get('name')} by {artists} (URI: {t.get('uri')})")
        return "\n".join(output)
    except Exception as e:
        return f"Error fetching recommendations: {str(e)}"



from typing import Optional, List, Dict, Any
from mcp.types import ToolAnnotations
from tools.core import mcp, get_spotify_client, _clean_spotify_id, _format_duration, _stats
from tools import discovery
import spotipy
import difflib
import re
import sys

from tools.tmdb_helpers import *

@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def search_actor_movies(actor_name: str, limit: int = 30, sort_by: str = "popularity") -> str:
    """Discover the full filmography for an actor using TMDB (with DDG and Wikipedia fallbacks).
    
    Args:
        actor_name: Name of the actor (e.g. 'Cillian Murphy', 'Shah Rukh Khan', 'Tom Cruise')
        limit: Maximum number of movies to return (default: 30)
        sort_by: Ordering for movies ('popularity' or 'release_date', default: 'popularity')
    """
    try:
        data = get_actor_filmography(actor_name, limit=limit, sort_by=sort_by)
        movies = data.get("movies", [])
        source = data.get("source", "Unknown")

        if not movies:
            return f"No movies found for actor '{actor_name}' across TMDB, DuckDuckGo, and Wikipedia."

        lines = [
            f"Filmography for {data.get('actor_name', actor_name)} (Source: {source}):",
            f"Total found: {len(movies)} (sorted by {sort_by})"
        ]

        for idx, m in enumerate(movies, 1):
            title = m.get("title", "Unknown")
            year = m.get("release_date", "")[:4] if m.get("release_date") else ""
            char = m.get("character")
            year_str = f" ({year})" if year else ""
            char_str = f" - Role: '{char}'" if char else ""
            rating_str = f" [Rating: {m.get('vote_average')}/10]" if m.get("vote_average") else ""
            lines.append(f"{idx}. {title}{year_str}{char_str}{rating_str}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error searching movies for {actor_name}: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def get_actor_tmdb_profile(actor_name: str) -> str:
    """Get rich biographical and career profile details for an actor from TMDB.
    
    Args:
        actor_name: Name of the actor (e.g. 'Robert Downey Jr.', 'Zendaya')
    """
    try:
        person = tmdb_search_person(actor_name)
        if not person:
            return f"Actor '{actor_name}' not found on TMDB."

        person_id = person["id"]
        profile = tmdb_get_person_profile(person_id) or person
        credits = tmdb_get_actor_movie_credits(person_id, sort_by="popularity")

        bio = profile.get("biography", "").strip()
        if len(bio) > 400:
            bio = bio[:400] + "..."

        top_movies = [c["title"] for c in credits[:5]]

        lines = [
            f"TMDB Profile: {profile.get('name', actor_name)}",
            f"Known For: {profile.get('known_for_department', 'Acting')}",
            f"Birthday: {profile.get('birthday', 'N/A')}",
            f"Place of Birth: {profile.get('place_of_birth', 'N/A')}",
            f"TMDB Popularity Score: {profile.get('popularity', 'N/A')}",
            f"TMDB ID: {person_id}",
            f"\nTop Known Movies: {', '.join(top_movies) if top_movies else 'N/A'}",
            f"\nBiography:\n{bio if bio else 'No biography available.'}"
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving TMDB profile for {actor_name}: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def search_movie_tmdb(movie_name: str, limit: int = 5) -> str:
    """Search TMDB for movie information, release year, ratings, and overview.
    
    Args:
        movie_name: Title of the movie to search (e.g. 'Inception', 'Interstellar')
        limit: Maximum results to return (default: 5)
    """
    try:
        results = tmdb_search_movie_details(movie_name, limit=limit)
        if not results:
            return f"No movie matching '{movie_name}' found on TMDB."

        lines = [f"TMDB Movies found for '{movie_name}':"]
        for idx, m in enumerate(results, 1):
            title = m.get("title", "Unknown")
            year = m.get("release_date", "")[:4] or "N/A"
            rating = m.get("vote_average", "N/A")
            votes = m.get("vote_count", 0)
            overview = m.get("overview", "")
            if len(overview) > 150:
                overview = overview[:150] + "..."
            lines.append(f"\n{idx}. {title} ({year}) - Rating: {rating}/10 ({votes:,} votes) [ID: {m.get('id')}]")
            if overview:
                lines.append(f"   Overview: {overview}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error searching TMDB for movie '{movie_name}': {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def search_duckduckgo(query: str, max_results: int = 5) -> str:
    """Perform a web search using DuckDuckGo to look up movie news, filmographies, or sound tracks.
    
    Args:
        query: Search query string
        max_results: Maximum results to return (default: 5)
    """
    try:
        results = ddg_web_search(query, max_results=max_results)
        if not results:
            return f"No DuckDuckGo results found for '{query}'."

        lines = [f"DuckDuckGo search results for '{query}':"]
        for idx, r in enumerate(results, 1):
            lines.append(f"\n{idx}. {r['title']}")
            lines.append(f"   Link: {r['href']}")
            lines.append(f"   Snippet: {r['body']}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error searching DuckDuckGo: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def get_movie_songs(movie_name: str, limit: int = 10) -> str:
    """Search Spotify for soundtrack albums and songs from a movie with DuckDuckGo fallback assistance.
    
    Args:
        movie_name: Title of the movie (e.g. 'Inception', 'Darr', 'Top Gun')
        limit: Maximum number of songs to return (default: 10)
    """
    try:
        sp = get_spotify_client()
        tracks = fetch_tracks_for_movie(sp, movie_name, max_songs=limit)
        if not tracks:
            return f"No songs found on Spotify for movie '{movie_name}'."

        lines = [f"Songs found for '{movie_name}':"]
        for idx, t in enumerate(tracks, 1):
            album_info = f" [Album: {t['album']}]" if t['album'] else ""
            lines.append(f"{idx}. {t['title']} - {t['artists']}{album_info} (URI: {t['uri']})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving songs for movie '{movie_name}': {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def search_spotify(query: str, search_type: str = "track", limit: int = 5) -> str:
    """Search for songs, albums, artists, or playlists on Spotify.
    
    Args:
        query: Search keywords
        search_type: Types to search for (comma-separated: 'track', 'album', 'artist', 'playlist')
        limit: Number of results (default 5, max 20)
    """
    try:
        sp = get_spotify_client()
        results = sp.search(q=query, type=search_type, limit=min(limit, 20))
        lines = [f"Search results for '{query}':"]

        if "tracks" in results and results["tracks"]["items"]:
            items = results["tracks"]["items"]
            lines.append(f"\nSongs (Total count: {len(items)}):")
            for t in items:
                artists = ", ".join(a["name"] for a in t["artists"])
                lines.append(f"- {t['name']} by {artists} (URI: {t['uri']})")

        if "albums" in results and results["albums"]["items"]:
            items = results["albums"]["items"]
            lines.append(f"\nAlbums (Total count: {len(items)}):")
            for a in items:
                artists = ", ".join(art["name"] for art in a["artists"])
                lines.append(f"- {a['name']} by {artists} (URI: {a['uri']})")

        if "artists" in results and results["artists"]["items"]:
            items = results["artists"]["items"]
            lines.append(f"\nArtists (Total count: {len(items)}):")
            for art in items:
                lines.append(f"- {art['name']} (URI: {art['uri']}{_stats(art)})")

        if "playlists" in results and results["playlists"]["items"]:
            items = [p for p in results["playlists"]["items"] if p]
            lines.append(f"\nPlaylists (Total count: {len(items)}):")
            for p in items:
                lines.append(f"- {p['name']} by {p.get('owner', {}).get('display_name', 'Unknown')} (URI: {p['uri']})")

        return "\n".join(lines)
    except Exception as e:
        return f"Error searching Spotify: {str(e)}"


# ==============================================================================
# SEARCH, RECOMMENDATIONS & DISCOVERY TOOLS
# ==============================================================================


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_search(
    query: str,
    types: Optional[List[str]] = None,
    limit: int = 10,
    market: Optional[str] = None
) -> str:
    """Search Spotify catalog for tracks, artists, albums, or playlists.
    
    Args:
        query: Search keywords or query syntax (e.g. 'Daft Punk', 'track:Get Lucky', 'artist:Queen').
        types: List of Spotify item types to search for (options: 'track', 'artist', 'album', 'playlist'). Default: ['track', 'artist', 'album', 'playlist'].
        limit: Number of results to return per type (default: 10, max: 50).
        market: Optional ISO 3166-1 alpha-2 country code (e.g. 'US', 'GB').
    """
    try:
        sp = get_spotify_client()
        valid_types = ["track", "artist", "album", "playlist"]
        if types:
            if isinstance(types, str):
                types = [t.strip().lower() for t in types.split(",") if t.strip()]
            resolved_types = [t.lower() for t in types if t.lower() in valid_types]
        else:
            resolved_types = valid_types

        if not resolved_types:
            resolved_types = ["track"]

        type_str = ",".join(resolved_types)
        limit = max(1, min(limit, 50))
        results = sp.search(q=query, type=type_str, limit=limit, market=market)

        output = [f"Spotify Search Results for '{query}' (Types: {', '.join(resolved_types)}):"]

        if "tracks" in results and results["tracks"]["items"]:
            items = results["tracks"]["items"]
            output.append(f"\n🎵 Tracks ({len(items)}):")
            for idx, t in enumerate(items, 1):
                artists = ", ".join(a.get("name", "Unknown") for a in t.get("artists", []))
                album = t.get("album", {}).get("name", "Unknown Album")
                dur = _format_duration(t.get("duration_ms", 0))
                output.append(f"{idx}. {t.get('name')} - {artists} ({dur}) [Album: {album}] (URI: {t.get('uri')}{_stats(t)})")

        if "artists" in results and results["artists"]["items"]:
            items = results["artists"]["items"]
            output.append(f"\n🎤 Artists ({len(items)}):")
            for idx, a in enumerate(items, 1):
                genres = ", ".join((a.get("genres") or [])[:3]) or "No genres listed"
                output.append(f"{idx}. {a.get('name')} [Genres: {genres}] (URI: {a.get('uri')}{_stats(a)})")

        if "albums" in results and results["albums"]["items"]:
            items = results["albums"]["items"]
            output.append(f"\n💿 Albums ({len(items)}):")
            for idx, alb in enumerate(items, 1):
                artists = ", ".join(art.get("name", "Unknown") for art in alb.get("artists", []))
                rel = alb.get("release_date", "N/A")
                tracks_count = alb.get("total_tracks", 0)
                output.append(f"{idx}. {alb.get('name')} by {artists} ({rel}, {tracks_count} tracks) (URI: {alb.get('uri')})")

        if "playlists" in results and results["playlists"]["items"]:
            items = [p for p in results["playlists"]["items"] if p]
            output.append(f"\n📁 Playlists ({len(items)}):")
            for idx, pl in enumerate(items, 1):
                owner = pl.get("owner", {}).get("display_name", "Unknown")
                tracks_count = pl.get("tracks", {}).get("total", 0)
                output.append(f"{idx}. {pl.get('name')} by {owner} ({tracks_count} tracks) (URI: {pl.get('uri')})")

        return "\n".join(output)
    except Exception as e:
        return f"Error searching Spotify catalog: {str(e)}"


def _track_line(idx: int, t: Dict[str, Any]) -> str:
    artists = ", ".join(a.get("name", "Unknown") for a in t.get("artists", []))
    album = (t.get("album") or {}).get("name", "Unknown Album")
    dur = _format_duration(t.get("duration_ms", 0))
    return f"{idx}. {t.get('name')} - {artists} ({dur}) [Album: {album}] (URI: {t.get('uri')})"


def _as_list(value) -> List[str]:
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return [v for v in (value or []) if v]


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_related_artists(artist: str) -> str:
    """Find artists connected to a target artist (the artists who share the most songs with them).

    Args:
        artist: Artist name, Spotify artist ID, or Spotify artist URI (e.g. 'Hans Zimmer', 'spotify:artist:0YC192cP3KPCRWx8zr8MfZ').
    """
    try:
        sp = get_spotify_client()
        target_artist = discovery.find_artist(sp, artist)
        if not target_artist:
            return f"Artist '{artist}' not found on Spotify."

        artist_name = target_artist.get("name", artist)
        # Spotify removed related-artists: use the artists who share the most songs with them
        related_items = discovery.collaborators(sp, target_artist)
        if not related_items:
            return f"No collaborating artists found on Spotify for '{artist_name}'."

        lines = [
            f"Related Artists for '{artist_name}':",
            f"Found {len(related_items)} artists who share songs with them:\n"
        ]
        for idx, a in enumerate(related_items, 1):
            lines.append(f"{idx}. {a.get('name')} [Shared songs: {a.get('shared_tracks', 0)}]")
            lines.append(f"   URI: {a.get('uri')}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error finding related artists: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_discover_by_artist(
    artist: str,
    limit: int = 15,
    include_artist_top_tracks: bool = True
) -> str:
    """Recommend songs by the artists a seed artist collaborates with.

    Args:
        artist: Seed artist name, ID, or URI.
        limit: Number of recommended tracks to return (default: 15, max: 50).
        include_artist_top_tracks: Whether to include the seed artist's own top search results (default: True).
    """
    try:
        sp = get_spotify_client()
        seed_artist = discovery.find_artist(sp, artist)
        if not seed_artist:
            return f"Artist '{artist}' not found on Spotify."

        artist_name = seed_artist.get("name", artist)
        limit = max(1, min(limit, 50))
        # Spotify removed related-artists, recommendations and top-tracks: recommend songs by the
        # artist's collaborators, and use their own search hits as "top tracks"
        own_tracks = discovery.artist_tracks(sp, seed_artist)
        related_artists = discovery.collaborators(sp, seed_artist, own_tracks, limit=4)
        per_artist = max(1, -(-limit // max(1, len(related_artists))))
        rec_tracks = discovery.tracks_by_artists(sp, related_artists, per_artist=per_artist,
                                                 exclude=[t["uri"] for t in own_tracks])[:limit]

        lines = [
            f"Artist Network Discovery for '{artist_name}':",
            f"Collaborator Seeds: {', '.join(a.get('name', 'Unknown') for a in related_artists) or 'None'}\n",
            f"Recommended Tracks ({len(rec_tracks)}):"
        ]
        lines.extend(_track_line(idx, t) for idx, t in enumerate(rec_tracks, 1))

        if include_artist_top_tracks and own_tracks:
            lines.append(f"\nTop Tracks by Seed Artist '{artist_name}':")
            for t in own_tracks[:3]:
                lines.append(f"• {t.get('name')} (URI: {t.get('uri')})")

        return "\n".join(lines)
    except Exception as e:
        return f"Error discovering tracks by artist: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_discover_by_mood(
    mood: Optional[str] = None,
    seed_genres: Optional[List[str]] = None,
    target_valence: Optional[float] = None,
    target_energy: Optional[float] = None,
    target_danceability: Optional[float] = None,
    target_acousticness: Optional[float] = None,
    target_tempo: Optional[float] = None,
    limit: int = 20
) -> str:
    """Discover tracks for a mood preset, a set of genres, or energy/valence targets.

    Args:
        mood: Optional mood preset ('happy', 'sad', 'chill', 'energetic', 'focus', 'party', 'dark', 'romantic', 'workout').
        seed_genres: Optional list of genres (e.g. ['pop', 'indie', 'electronic']). Max 5. Overrides the mood and targets.
        target_valence: Optional positivity 0.0-1.0. Matched against estimated genre vibes (Spotify no longer provides per-track audio features).
        target_energy: Optional intensity 0.0-1.0, matched the same way.
        target_danceability: Ignored. Spotify no longer provides audio features for Development Mode apps.
        target_acousticness: Ignored (see target_danceability).
        target_tempo: Ignored (see target_danceability).
        limit: Number of tracks to discover (default: 20, max: 100).
    """
    try:
        sp = get_spotify_client()
        genres = _as_list(seed_genres)
        mood_key = (mood or "").lower().strip()
        vibe_used = not genres and (target_energy is not None or target_valence is not None)
        if vibe_used:
            # Spotify removed audio features: pick the genres whose estimated vibe is closest
            genres = discovery.vibe_genres(discovery.vibe_target(mood, target_energy, target_valence))
        used_genres = (genres or discovery.MOOD_GENRES.get(mood_key) or [mood_key or "pop"])[:5]
        # Spotify removed /recommendations and audio features: moods are matched through genres
        tracks = discovery.mood_tracks(sp, mood, genres, max(1, min(limit, 100)))
        if not tracks:
            return f"No tracks discovered for mood '{mood}' with genres {used_genres}."

        lines = [f"Mood Discovery Results (Mood: '{mood or 'custom'}', Genres: {', '.join(used_genres)}):"]
        if vibe_used:
            lines.append("Energy/valence targets were matched to genres with similar estimated vibes (Spotify no longer provides per-track audio features).")
        if any(v is not None for v in [target_danceability, target_acousticness, target_tempo]):
            lines.append("Note: danceability, acousticness and tempo targets were ignored; Spotify no longer provides audio features for Development Mode apps.")
        lines.append(f"\nDiscovered Tracks ({len(tracks)}):")
        lines.extend(_track_line(idx, t) for idx, t in enumerate(tracks, 1))
        return "\n".join(lines)
    except Exception as e:
        return f"Error discovering tracks by mood: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_genre_explorer(
    genres: Optional[List[str]] = None,
    limit: int = 15,
    market: Optional[str] = None
) -> str:
    """Sample tracks across specific genres, or list suggested genres.

    Args:
        genres: Optional list of genre keywords (e.g. ['synthwave', 'indie pop', 'jazz']). If None or empty, returns the suggested genre list.
        limit: Number of tracks to sample (default: 15, max: 50).
        market: Unused; kept for compatibility.
    """
    try:
        genres = _as_list(genres)
        if not genres:
            # Spotify removed the genre-seeds endpoint; these genres work with search's genre: filter
            lines = [
                f"Suggested Genres (Total: {len(discovery.GENRES)}):",
                "Any of these work with genre discovery and mood discovery:\n"
            ]
            lines.extend(", ".join(discovery.GENRES[i:i + 6]) for i in range(0, len(discovery.GENRES), 6))
            lines.append("\nTip: Pass specific genres to this tool (e.g. genres=['ambient', 'lo-fi']) to sample tracks.")
            return "\n".join(lines)

        sp = get_spotify_client()
        tracks = discovery.genre_tracks(sp, genres, max(1, min(limit, 50)))
        if not tracks:
            return f"No tracks found for genres: {', '.join(genres)}."

        lines = [f"Genre Explorer: Sample tracks for {', '.join(genres[:5])} (Total: {len(tracks)}):"]
        lines.extend(_track_line(idx, t) for idx, t in enumerate(tracks, 1))
        return "\n".join(lines)
    except Exception as e:
        return f"Error exploring genres: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_discover_deep_cuts(
    artist_or_album: str,
    max_popularity: int = 40,
    limit: int = 15
) -> str:
    """Discover album tracks from an artist or album that are not among their best-known songs.

    Args:
        artist_or_album: Name, ID, or URI of an artist or album (e.g. 'Radiohead', 'The Dark Side of the Moon').
        max_popularity: Ignored. Spotify no longer returns track popularity, so deep cuts are album tracks outside the top search results.
        limit: Maximum number of deep cuts to return (default: 15, max: 50).
    """
    try:
        sp = get_spotify_client()
        result = discovery.deep_cuts(sp, artist_or_album.strip(), max(1, min(limit, 50)))
        target_name = result.get("name")
        if not target_name:
            return f"Could not find artist or album '{artist_or_album}' on Spotify."
        cuts = result.get("tracks", [])
        if not cuts:
            return f"No deep cuts found for '{target_name}'."

        lines = [
            f"Deep Cut Gems for '{target_name}':",
            f"Found {len(cuts)} album tracks outside their top search results:\n"
        ]
        for idx, cut in enumerate(cuts, 1):
            artists = ", ".join(a.get("name", "Unknown") for a in cut.get("artists", []))
            album = (cut.get("album") or {}).get("name", "Album")
            dur = _format_duration(cut.get("duration_ms", 0))
            lines.append(f"{idx}. '{cut.get('name')}' - {artists} [Album: {album}] ({dur}, URI: {cut.get('uri')})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error discovering deep cuts: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_get_recommendations(
    limit: int = 20,
    seed_tracks: Optional[List[str]] = None,
    seed_artists: Optional[List[str]] = None,
    seed_genres: Optional[List[str]] = None,
    target_energy: Optional[float] = None,
    target_valence: Optional[float] = None,
    target_danceability: Optional[float] = None,
    target_acousticness: Optional[float] = None,
    target_instrumentalness: Optional[float] = None,
    target_tempo: Optional[float] = None,
    min_popularity: Optional[int] = None,
    max_popularity: Optional[int] = None,
    market: Optional[str] = None
) -> str:
    """Recommend tracks from seed tracks, artists and genres (songs by the seeds' collaborators plus genre picks).

    Args:
        limit: Number of recommendations to return (default: 20, max: 100).
        seed_tracks: List of Spotify track IDs or URIs (max 5 combined seeds).
        seed_artists: List of Spotify artist IDs or URIs.
        seed_genres: List of genres (e.g. ['pop', 'rock', 'synthwave']).
        target_energy: Optional intensity 0.0-1.0. If no seed genres are given, adds the genres whose estimated vibe is closest (Spotify no longer provides per-track audio features).
        target_valence: Optional positivity 0.0-1.0, used the same way.
        target_danceability: Ignored. Spotify no longer provides audio features for Development Mode apps.
        target_acousticness: Ignored (see target_danceability).
        target_instrumentalness: Ignored (see target_danceability).
        target_tempo: Ignored (see target_danceability).
        min_popularity: Ignored. Spotify no longer returns track popularity.
        max_popularity: Ignored (see min_popularity).
        market: Unused; kept for compatibility.
    """
    try:
        sp = get_spotify_client()
        clean_tracks = [_clean_spotify_id(t, "track") for t in _as_list(seed_tracks)]
        clean_artists = [_clean_spotify_id(a, "artist") for a in _as_list(seed_artists)]
        clean_genres = [g.strip().lower() for g in _as_list(seed_genres)]
        vibe_used = not clean_genres and (target_energy is not None or target_valence is not None)
        if vibe_used:
            clean_genres = discovery.vibe_genres(discovery.vibe_target(None, target_energy, target_valence))
        if not (clean_tracks or clean_artists or clean_genres):
            clean_genres = ["pop"]

        # Spotify removed /recommendations: build them from the seeds' collaborators and genres
        tracks = discovery.recommend(sp, clean_artists, clean_tracks, clean_genres, max(1, min(limit, 100)))
        if not tracks:
            return "No recommendations found for the provided seeds."

        seeds_desc = []
        if clean_tracks: seeds_desc.append(f"Tracks: {len(clean_tracks)}")
        if clean_artists: seeds_desc.append(f"Artists: {len(clean_artists)}")
        if clean_genres: seeds_desc.append(f"Genres: {', '.join(clean_genres)}")

        lines = [f"Spotify Recommendations (Seeds: {', '.join(seeds_desc)}):"]
        if vibe_used:
            lines.append("Energy/valence targets were matched to genres with similar estimated vibes (Spotify no longer provides per-track audio features).")
        ignored = [target_danceability, target_acousticness, target_instrumentalness, target_tempo,
                   min_popularity, max_popularity]
        if any(v is not None for v in ignored):
            lines.append("Note: danceability, acousticness, instrumentalness, tempo and popularity targets were ignored; Spotify no longer provides them for Development Mode apps.")
        lines.append(f"Found {len(tracks)} track recommendations:\n")
        lines.extend(_track_line(idx, t) for idx, t in enumerate(tracks, 1))
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching Spotify recommendations: {str(e)}"


def fetch_soundtrack_tracks_with_client(
    movie_title: str,
    language_name: Optional[str] = None,
    release_year: Optional[str] = None,
    actor_name: Optional[str] = None,
    sp: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """Searches Spotify for movie soundtrack tracks using client credentials or user client.
    
    Args:
        movie_title: Title of the movie
        language_name: Optional language filter (e.g. 'Hindi', 'Telugu', 'English')
        release_year: Optional movie release year (e.g. '2023')
        actor_name: Optional actor name to narrow down soundtrack
        sp: Optional spotipy.Spotify client instance
    """
    client = sp
    if not client:
        try:
            client = get_spotify_client()
        except Exception:
            client = None
    if not client:
        return []

    try:
        clean_title = movie_title.strip()
        search_title = clean_title
        if actor_name:
            search_title = f"{clean_title} {actor_name}"
        elif language_name:
            search_title = f"{clean_title} {language_name}"
            
        year_filter = ""
        if release_year and len(str(release_year)) >= 4:
            year_filter = f" year:{str(release_year)[:4]}"
            
        def is_year_match(spotify_date: str, target_year: str) -> bool:
            if not target_year or not spotify_date:
                return True
            try:
                s_y = int(spotify_date[:4])
                t_y = int(str(target_year)[:4])
                return abs(s_y - t_y) <= 5
            except Exception:
                return True

        def is_fuzzy_match(movie: str, target: str, lang: str = None) -> bool:
            return soundtrack_title_matches(movie, target, language=lang)

        def format_track(t: Dict[str, Any], album: Dict[str, Any], popularity: int) -> Dict[str, Any]:
            return {
                "name": t.get("name"),
                "artist": ", ".join(a.get("name", "Unknown") for a in t.get("artists", [])),
                "artist_ids": [a.get("id") for a in t.get("artists", []) if a.get("id")],
                "uri": t.get("uri"),
                "duration_ms": t.get("duration_ms", 0),
                "popularity": popularity,
                "release_date": album.get("release_date", ""),
                "spotify_url": t.get("external_urls", {}).get("spotify"),
                "album_name": album.get("name", clean_title),
                "album_cover": album.get("images", [{}])[0].get("url") if album.get("images") else None
            }
            
            if lang:
                lang_lower = lang.lower()
                common_langs = {"hindi", "telugu", "tamil", "malayalam", "kannada", "english"}
                target_words = set(t_norm.split())
                for cl in common_langs:
                    if cl != lang_lower and cl in target_words and lang_lower not in target_words:
                        return False
            
            if m_norm == t_norm:
                return True
            if re.search(rf'\b{re.escape(m_norm)}\b', t_norm):
                return True
            
            m_solid = m_norm.replace(" ", "")
            t_solid = t_norm.replace(" ", "")
            if len(m_solid) > 4 and m_solid in t_solid:
                return True
            
            if difflib.SequenceMatcher(None, m_solid, t_solid).ratio() > 0.85:
                return True
            return False
            
        market = "US"
        try:
            me = client.me()
            if me and me.get('country'):
                market = me.get('country')
        except Exception:
            pass

        albums = []
        queries = [
            f"album:{search_title} soundtrack{year_filter}",
            f"{search_title} soundtrack{year_filter}",
            f"{search_title} ost{year_filter}",
            f"{search_title}{year_filter}"
        ]
        
        if language_name or actor_name:
            queries.extend([
                f"album:{clean_title} soundtrack{year_filter}",
                f"{clean_title} soundtrack{year_filter}",
                f"{clean_title} ost{year_filter}",
                f"{clean_title}{year_filter}"
            ])

        if year_filter:
            queries.extend([
                f"album:{search_title} soundtrack",
                f"{search_title} soundtrack",
                f"{search_title} ost",
                search_title
            ])
            if language_name or actor_name:
                queries.extend([
                    f"album:{clean_title} soundtrack",
                    f"{clean_title} soundtrack",
                    f"{clean_title} ost",
                    clean_title
                ])
            
        for q in queries:
            res = client.search(q=q, type="album", limit=3, market=market)
            found = res.get("albums", {}).get("items", [])
            albums += [
                album for album in found
                if is_fuzzy_match(clean_title, album.get("name", ""), language_name)
                and is_year_match(album.get("release_date", ""), release_year)
                and album.get("id") not in {a.get("id") for a in albums}
            ]
            if any(is_full_soundtrack_album(a) for a in albums):
                break
        albums.sort(key=soundtrack_album_rank)

        # No full soundtrack album on Spotify search: look for its Spotify page via web search
        web = {"album": None, "tracks": []}
        if not albums or not is_full_soundtrack_album(albums[0]):
            web = web_find_spotify_soundtrack(client, clean_title, release_year=release_year,
                                              language=language_name, market=market)
            if web["album"]:
                albums.insert(0, web["album"])

        if albums:
            album = albums[0]
            album_id = album["id"]
            album_name = album.get("name", clean_title)
            album_cover = album.get("images", [{}])[0].get("url") if album.get("images") else None
            album_release = album.get("release_date", "")

            tracks_res = client.album_tracks(album_id, limit=20, market=market)
            formatted = []
            for t in tracks_res.get("items", []):
                if hasattr(t, "get") and t.get("is_playable") is False:
                    continue
                artists = ", ".join(a.get("name", "Unknown") for a in t.get("artists", []))
                artist_ids = [a.get("id") for a in t.get("artists", []) if a.get("id")]
                formatted.append({
                    "name": t.get("name"),
                    "artist": artists,
                    "artist_ids": artist_ids,
                    "uri": t.get("uri"),
                    "duration_ms": t.get("duration_ms", 0),
                    "popularity": 50,
                    "release_date": album_release,
                    "spotify_url": t.get("external_urls", {}).get("spotify"),
                    "album_name": album_name,
                    "album_cover": album_cover
                })
            if formatted:
                return formatted

        web_tracks = [format_track(t, t.get("album", {}), t.get("popularity", 0)) for t in web["tracks"]]
        if web_tracks:
            return web_tracks

        fallback_queries = [
            f"{search_title} soundtrack{year_filter}",
            f"{search_title} theme{year_filter}",
            f"{search_title}{year_filter}"
        ]
        
        if language_name or actor_name:
            fallback_queries.extend([
                f"{clean_title} soundtrack{year_filter}",
                f"{clean_title} theme{year_filter}",
                f"{clean_title}{year_filter}"
            ])
            
        if year_filter:
            fallback_queries.extend([
                f"{search_title} soundtrack", 
                f"{search_title} theme", 
                search_title
            ])
            if language_name or actor_name:
                fallback_queries.extend([
                    f"{clean_title} soundtrack", 
                    f"{clean_title} theme", 
                    clean_title
                ])
        tracks_list = []
        seen_uris = set()
        for fq in fallback_queries:
            fallback = client.search(q=fq, type="track", limit=10, market=market)
            for t in fallback.get("tracks", {}).get("items", []):
                if hasattr(t, "get") and t.get("is_playable") is False:
                    continue
                uri = t.get("uri")
                track_name = t.get("name", "").lower()
                album_name = t.get("album", {}).get("name", "").lower()
                
                if (not soundtrack_title_matches(clean_title, track_name, allow_plain=False, language=language_name)
                        and not is_fuzzy_match(clean_title, album_name, language_name)):
                    continue
                    
                if not is_year_match(t.get("album", {}).get("release_date", ""), release_year):
                    continue
                    
                if uri and uri not in seen_uris:
                    seen_uris.add(uri)
                    artist_ids = [a.get("id") for a in t.get("artists", []) if a.get("id")]
                    tracks_list.append({
                        "name": t.get("name"),
                        "artist": ", ".join(a.get("name", "Unknown") for a in t.get("artists", [])),
                        "artist_ids": artist_ids,
                        "uri": uri,
                        "duration_ms": t.get("duration_ms", 0),
                        "popularity": t.get("popularity", 0),
                        "release_date": t.get("album", {}).get("release_date", ""),
                        "spotify_url": t.get("external_urls", {}).get("spotify"),
                        "album_name": t.get("album", {}).get("name", clean_title),
                        "album_cover": t.get("album", {}).get("images", [{}])[0].get("url") if t.get("album", {}).get("images") else None
                    })
            if len(tracks_list) >= 8:
                break
        return tracks_list
    except Exception as e:
        print(f"Error fetching soundtrack for {movie_title}: {e}", file=sys.stderr)
        return []


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def fetch_soundtrack_tracks(
    movie_title: str,
    language_name: Optional[str] = None,
    release_year: Optional[str] = None,
    actor_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Searches Spotify for movie soundtrack tracks using titles, language, release year, or actor name with fuzzy matching.
    
    Args:
        movie_title: Title of the movie
        language_name: Optional language filter (e.g. 'Hindi', 'Telugu', 'English')
        release_year: Optional movie release year (e.g. '2023')
        actor_name: Optional actor name to narrow down soundtrack
    """
    return fetch_soundtrack_tracks_with_client(
        movie_title=movie_title,
        language_name=language_name,
        release_year=release_year,
        actor_name=actor_name
    )


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def search_singers(query: str, limit: int = 10) -> str:
    """Search for singers, musical artists, or bands on Spotify.
    
    Args:
        query: Name of singer, artist, or band to search
        limit: Maximum number of artists to return (default: 10)
    """
    try:
        sp = get_spotify_client()
        res = sp.search(q=query, type="artist", limit=min(limit, 50))
        items = res.get("artists", {}).get("items", [])
        if not items:
            return f"No singers or artists found for '{query}'."

        lines = [f"Singers & Artists found for '{query}':"]
        for idx, a in enumerate(items, 1):
            genres = ", ".join(a.get("genres") or []) or "None specified"
            lines.append(f"{idx}. {a.get('name')} (Genres: {genres}, URI: {a.get('uri')}{_stats(a)})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error searching singers: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def search_songs(query: str, limit: int = 10) -> str:
    """Search for songs or tracks on Spotify with detailed track metadata.
    
    Args:
        query: Song name or keywords to search
        limit: Maximum number of songs to return (default: 10)
    """
    try:
        sp = get_spotify_client()
        res = sp.search(q=query, type="track", limit=min(limit, 50))
        items = res.get("tracks", {}).get("items", [])
        if not items:
            return f"No songs found for '{query}'."

        lines = [f"Songs found for '{query}':"]
        for idx, t in enumerate(items, 1):
            artists = ", ".join(a.get("name", "Unknown") for a in t.get("artists", []))
            album = t.get("album", {}).get("name", "Unknown Album")
            dur = _format_duration(t.get("duration_ms", 0))
            lines.append(f"{idx}. {t.get('name')} - {artists} ({dur}) [Album: {album}] (URI: {t.get('uri')}{_stats(t)})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error searching songs: {str(e)}"





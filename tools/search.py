from typing import Optional, List, Dict, Any
from mcp.types import ToolAnnotations
from tools.core import mcp, get_spotify_client, _clean_spotify_id, _format_duration
import spotipy
import difflib
import re

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
                lines.append(f"- {art['name']} (URI: {art['uri']}, Followers: {art.get('followers', {}).get('total', 0):,})")

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
                pop = t.get("popularity", 0)
                output.append(f"{idx}. {t.get('name')} - {artists} ({dur}) [Album: {album}] (Popularity: {pop}/100, URI: {t.get('uri')})")

        if "artists" in results and results["artists"]["items"]:
            items = results["artists"]["items"]
            output.append(f"\n🎤 Artists ({len(items)}):")
            for idx, a in enumerate(items, 1):
                genres = ", ".join(a.get("genres", [])[:3]) or "No genres listed"
                followers = a.get("followers", {}).get("total", 0)
                output.append(f"{idx}. {a.get('name')} [Genres: {genres}] ({followers:,} followers, URI: {a.get('uri')})")

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


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_related_artists(artist: str) -> str:
    """Find artists similar to a target artist.
    
    Args:
        artist: Artist name, Spotify artist ID, or Spotify artist URI (e.g. 'Hans Zimmer', 'spotify:artist:0YC192cP3KPCRWx8zr8MfZ').
    """
    try:
        sp = get_spotify_client()
        clean_id = _clean_spotify_id(artist, "artist")

        is_uri_or_id = artist.startswith("spotify:") or "spotify.com" in artist or len(clean_id) == 22
        if not is_uri_or_id:
            search_res = sp.search(q=artist, type="artist", limit=1)
            items = search_res.get("artists", {}).get("items", [])
            if not items:
                return f"Artist '{artist}' not found on Spotify."
            target_artist = items[0]
            artist_id = target_artist.get("id", clean_id)
        else:
            target_artist = sp.artist(clean_id)
            artist_id = target_artist.get("id", clean_id)

        artist_name = target_artist.get("name", artist)
        related_data = sp.artist_related_artists(artist_id)
        related_items = related_data.get("artists", [])

        if not related_items:
            return f"No related artists found on Spotify for '{artist_name}'."

        genres = ", ".join(target_artist.get("genres", [])[:4]) or "N/A"
        followers = target_artist.get("followers", {}).get("total", 0)
        lines = [
            f"Related Artists for '{artist_name}' (Followers: {followers:,}, Genres: {genres}):",
            f"Found {len(related_items)} similar artists on Spotify:\n"
        ]

        for idx, a in enumerate(related_items, 1):
            a_genres = ", ".join(a.get("genres", [])[:3]) or "N/A"
            a_followers = a.get("followers", {}).get("total", 0)
            a_pop = a.get("popularity", 0)
            lines.append(f"{idx}. {a.get('name')} [Popularity: {a_pop}/100, Followers: {a_followers:,}]")
            lines.append(f"   Genres: {a_genres}")
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
    """Generate track recommendations derived from related artist networks.
    
    Args:
        artist: Seed artist name, ID, or URI.
        limit: Number of recommended tracks to return (default: 15, max: 50).
        include_artist_top_tracks: Whether to include top tracks from the seed artist (default: True).
    """
    try:
        sp = get_spotify_client()
        clean_id = _clean_spotify_id(artist, "artist")

        is_uri_or_id = artist.startswith("spotify:") or "spotify.com" in artist or len(clean_id) == 22
        if not is_uri_or_id:
            search_res = sp.search(q=artist, type="artist", limit=1)
            items = search_res.get("artists", {}).get("items", [])
            if not items:
                return f"Artist '{artist}' not found on Spotify."
            seed_artist = items[0]
            artist_id = seed_artist.get("id", clean_id)
        else:
            seed_artist = sp.artist(clean_id)
            artist_id = seed_artist.get("id", clean_id)

        artist_name = seed_artist.get("name", artist)
        related_res = sp.artist_related_artists(artist_id)
        related_artists = related_res.get("artists", [])

        seed_pool = [artist_id]
        related_names = []
        for a in related_artists[:4]:
            if a.get("id"):
                seed_pool.append(a["id"])
                related_names.append(a.get("name", "Unknown"))

        rec_limit = max(1, min(limit, 50))
        recs = sp.recommendations(seed_artists=seed_pool[:5], limit=rec_limit)
        rec_tracks = recs.get("tracks", [])

        lines = [
            f"Artist Network Discovery for '{artist_name}':",
            f"Related Artist Seeds: {', '.join(related_names) if related_names else 'None'}\n",
            f"Recommended Tracks ({len(rec_tracks)}):"
        ]

        for idx, t in enumerate(rec_tracks, 1):
            artists = ", ".join(a.get("name", "Unknown") for a in t.get("artists", []))
            album = t.get("album", {}).get("name", "Unknown Album")
            dur = _format_duration(t.get("duration_ms", 0))
            lines.append(f"{idx}. {t.get('name')} - {artists} ({dur}) [Album: {album}] (URI: {t.get('uri')})")

        if include_artist_top_tracks:
            top_res = sp.artist_top_tracks(artist_id)
            top_tracks = top_res.get("tracks", [])[:3]
            if top_tracks:
                lines.append(f"\nTop Tracks by Seed Artist '{artist_name}':")
                for idx, t in enumerate(top_tracks, 1):
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
    """Discover tracks using target audio parameters (valence, energy, tempo, etc.) or mood presets.
    
    Args:
        mood: Optional mood preset ('happy', 'sad', 'chill', 'energetic', 'focus', 'party', 'dark', 'romantic', 'workout').
        seed_genres: Optional list of seed genres (e.g. ['pop', 'indie', 'electronic']). Max 5 combined seeds.
        target_valence: Musical positiveness ($0.0$ to $1.0$).
        target_energy: Intensity and activity ($0.0$ to $1.0$).
        target_danceability: Suitability for dancing ($0.0$ to $1.0$).
        target_acousticness: Confidence measure from $0.0$ to $1.0$ of whether track is acoustic.
        target_tempo: Target tempo in BPM (beats per minute).
        limit: Number of tracks to discover (default: 20, max: 100).
    """
    try:
        sp = get_spotify_client()
        mood_presets = {
            "happy": {"target_valence": 0.85, "target_energy": 0.75, "genres": ["pop", "happy"]},
            "sad": {"target_valence": 0.18, "target_energy": 0.25, "target_acousticness": 0.70, "genres": ["sad", "acoustic"]},
            "chill": {"target_valence": 0.50, "target_energy": 0.30, "target_acousticness": 0.50, "genres": ["chill", "ambient"]},
            "energetic": {"target_valence": 0.75, "target_energy": 0.90, "target_danceability": 0.75, "genres": ["dance", "electronic"]},
            "focus": {"target_valence": 0.40, "target_energy": 0.30, "target_instrumentalness": 0.80, "genres": ["ambient", "study"]},
            "party": {"target_valence": 0.80, "target_energy": 0.85, "target_danceability": 0.85, "genres": ["dance", "party"]},
            "dark": {"target_valence": 0.20, "target_energy": 0.75, "genres": ["metal", "industrial"]},
            "romantic": {"target_valence": 0.60, "target_energy": 0.40, "target_acousticness": 0.60, "genres": ["r-n-b", "romance"]},
            "workout": {"target_valence": 0.70, "target_energy": 0.95, "target_tempo": 135.0, "genres": ["work-out"]}
        }

        active_preset = mood_presets.get((mood or "").lower().strip(), {})
        kwargs = {}

        v = target_valence if target_valence is not None else active_preset.get("target_valence")
        e = target_energy if target_energy is not None else active_preset.get("target_energy")
        d = target_danceability if target_danceability is not None else active_preset.get("target_danceability")
        a = target_acousticness if target_acousticness is not None else active_preset.get("target_acousticness")
        t = target_tempo if target_tempo is not None else active_preset.get("target_tempo")

        if v is not None: kwargs["target_valence"] = max(0.0, min(1.0, float(v)))
        if e is not None: kwargs["target_energy"] = max(0.0, min(1.0, float(e)))
        if d is not None: kwargs["target_danceability"] = max(0.0, min(1.0, float(d)))
        if a is not None: kwargs["target_acousticness"] = max(0.0, min(1.0, float(a)))
        if t is not None: kwargs["target_tempo"] = float(t)
        if "target_instrumentalness" in active_preset:
            kwargs["target_instrumentalness"] = active_preset["target_instrumentalness"]

        genres = seed_genres or active_preset.get("genres", ["pop"])
        if isinstance(genres, str):
            genres = [g.strip() for g in genres.split(",") if g.strip()]

        rec_limit = max(1, min(limit, 100))
        results = sp.recommendations(seed_genres=genres[:5], limit=rec_limit, **kwargs)
        tracks = results.get("tracks", [])

        if not tracks:
            return f"No tracks discovered for mood '{mood}' with seeds {genres}."

        params_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        lines = [
            f"Mood Discovery Results (Mood: '{mood or 'custom'}', Seeds: {', '.join(genres[:5])}):",
            f"Active Audio Targets: {params_str or 'None'}\n",
            f"Discovered Tracks ({len(tracks)}):"
        ]

        for idx, trk in enumerate(tracks, 1):
            artists = ", ".join(art.get("name", "Unknown") for art in trk.get("artists", []))
            album = trk.get("album", {}).get("name", "Unknown Album")
            dur = _format_duration(trk.get("duration_ms", 0))
            lines.append(f"{idx}. {trk.get('name')} - {artists} ({dur}) [Album: {album}] (URI: {trk.get('uri')})")

        return "\n".join(lines)
    except Exception as e:
        return f"Error discovering tracks by mood: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_genre_explorer(
    genres: Optional[List[str]] = None,
    limit: int = 15,
    market: Optional[str] = None
) -> str:
    """Browse and sample tracks across specific seed genres or list all available genre seeds.
    
    Args:
        genres: Optional list of genre seed keywords (e.g. ['synthwave', 'indie-pop', 'jazz']). If None or empty, returns all available Spotify genre seeds.
        limit: Number of tracks to sample (default: 15, max: 50).
        market: Optional ISO country code.
    """
    try:
        sp = get_spotify_client()
        available_genres = sp.recommendation_genre_seeds().get("genres", [])

        if not genres:
            lines = [
                f"Spotify Recommendation Genre Seeds (Total: {len(available_genres)}):",
                "You can use any of these seeds in recommendations and mood discovery:\n"
            ]
            cols = [", ".join(available_genres[i:i + 6]) for i in range(0, len(available_genres), 6)]
            lines.extend(cols)
            lines.append("\nTip: Pass specific genres to this tool (e.g. genres=['ambient', 'lo-fi']) to sample tracks.")
            return "\n".join(lines)

        if isinstance(genres, str):
            genres = [g.strip() for g in genres.split(",") if g.strip()]

        rec_limit = max(1, min(limit, 50))
        results = sp.recommendations(seed_genres=genres[:5], limit=rec_limit, market=market)
        tracks = results.get("tracks", [])

        if not tracks:
            return f"No tracks found for genre seeds: {', '.join(genres)}."

        lines = [
            f"Genre Explorer: Sample tracks for {', '.join(genres[:5])} (Total: {len(tracks)}):"
        ]
        for idx, t in enumerate(tracks, 1):
            artists = ", ".join(a.get("name", "Unknown") for a in t.get("artists", []))
            album = t.get("album", {}).get("name", "Unknown Album")
            dur = _format_duration(t.get("duration_ms", 0))
            lines.append(f"{idx}. {t.get('name')} - {artists} ({dur}) [Album: {album}] (URI: {t.get('uri')})")

        return "\n".join(lines)
    except Exception as e:
        return f"Error exploring genres: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_discover_deep_cuts(
    artist_or_album: str,
    max_popularity: int = 40,
    limit: int = 15
) -> str:
    """Discover non-single, album-only deep cut tracks from an artist or album.
    
    Args:
        artist_or_album: Name, ID, or URI of an artist or album (e.g. 'Radiohead', 'The Dark Side of the Moon').
        max_popularity: Maximum popularity threshold (0-100, default: 40). Tracks with popularity <= this threshold are considered deep cuts.
        limit: Maximum number of deep cuts to return (default: 15).
    """
    try:
        sp = get_spotify_client()
        clean_input = artist_or_album.strip()
        limit = max(1, min(limit, 50))

        # Check if artist
        artist_res = sp.search(q=clean_input, type="artist", limit=1)
        artist_items = artist_res.get("artists", {}).get("items", [])

        deep_cuts = []
        target_name = clean_input

        if artist_items:
            artist = artist_items[0]
            artist_id = artist.get("id", clean_input)
            target_name = artist.get("name", clean_input)

            # Get artist's top tracks to exclude popular singles
            top_tracks_res = sp.artist_top_tracks(artist_id)
            top_track_uris = {t["uri"] for t in top_tracks_res.get("tracks", [])}

            # Fetch studio albums
            albums_res = sp.artist_albums(artist_id, album_type="album", limit=8)
            albums = albums_res.get("items", [])

            track_ids = []
            track_album_map = {}

            for alb in albums:
                alb_id = alb.get("id")
                if not alb_id:
                    continue
                alb_tracks = sp.album_tracks(alb_id, limit=30).get("items", [])
                for t in alb_tracks:
                    if t.get("uri") not in top_track_uris and t.get("id"):
                        track_ids.append(t["id"])
                        track_album_map[t["id"]] = alb.get("name", "Album")

            # Batch retrieve tracks with popularity
            for i in range(0, min(len(track_ids), 100), 50):
                batch = track_ids[i:i + 50]
                detailed_tracks = sp.tracks(batch).get("tracks", [])
                for dt in detailed_tracks:
                    if dt and dt.get("popularity", 100) <= max_popularity:
                        deep_cuts.append({
                            "name": dt.get("name"),
                            "artist": ", ".join(a.get("name") for a in dt.get("artists", [])),
                            "album": track_album_map.get(dt.get("id"), "Album"),
                            "popularity": dt.get("popularity", 0),
                            "duration_ms": dt.get("duration_ms", 0),
                            "uri": dt.get("uri")
                        })
        else:
            # Fallback to album search
            album_res = sp.search(q=clean_input, type="album", limit=1)
            alb_items = album_res.get("albums", {}).get("items", [])
            if not alb_items:
                return f"Could not find artist or album '{artist_or_album}' on Spotify."
            alb = alb_items[0]
            target_name = alb.get("name", clean_input)
            alb_tracks = sp.album_tracks(alb.get("id", clean_input), limit=50).get("items", [])
            t_ids = [t["id"] for t in alb_tracks if t.get("id")]
            if t_ids:
                detailed = sp.tracks(t_ids[:50]).get("tracks", [])
                for dt in detailed:
                    if dt and dt.get("popularity", 100) <= max_popularity:
                        deep_cuts.append({
                            "name": dt.get("name"),
                            "artist": ", ".join(a.get("name") for a in dt.get("artists", [])),
                            "album": alb.get("name"),
                            "popularity": dt.get("popularity", 0),
                            "duration_ms": dt.get("duration_ms", 0),
                            "uri": dt.get("uri")
                        })

        deep_cuts.sort(key=lambda x: x["popularity"])
        selected_cuts = deep_cuts[:limit]

        if not selected_cuts:
            return f"No deep cuts found for '{target_name}' with popularity <= {max_popularity}. Try raising max_popularity."

        lines = [
            f"Deep Cut Gems for '{target_name}' (Max Popularity Threshold: {max_popularity}/100):",
            f"Found {len(selected_cuts)} album-only hidden tracks:\n"
        ]
        for idx, cut in enumerate(selected_cuts, 1):
            dur = _format_duration(cut["duration_ms"])
            lines.append(f"{idx}. '{cut['name']}' - {cut['artist']} [Album: {cut['album']}] (Popularity: {cut['popularity']}/100, {dur}, URI: {cut['uri']})")

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
    """Direct wrapper for Spotify Recommendations API using seeds and target audio features.
    
    Args:
        limit: Number of recommendations to return (default: 20, max: 100).
        seed_tracks: List of Spotify track IDs or URIs (max 5 combined seeds).
        seed_artists: List of Spotify artist IDs or URIs.
        seed_genres: List of seed genres (e.g. ['pop', 'rock', 'synthwave']).
        target_energy: Target energy (0.0 to 1.0).
        target_valence: Target valence (0.0 to 1.0).
        target_danceability: Target danceability (0.0 to 1.0).
        target_acousticness: Target acousticness (0.0 to 1.0).
        target_instrumentalness: Target instrumentalness (0.0 to 1.0).
        target_tempo: Target tempo in BPM.
        min_popularity: Minimum track popularity (0-100).
        max_popularity: Maximum track popularity (0-100).
        market: Optional ISO 3166-1 alpha-2 country code.
    """
    try:
        sp = get_spotify_client()

        clean_tracks = [_clean_spotify_id(t, "track") for t in (seed_tracks or []) if t]
        clean_artists = [_clean_spotify_id(a, "artist") for a in (seed_artists or []) if a]
        clean_genres = [g.strip().lower() for g in (seed_genres or []) if g]

        num_seeds = len(clean_tracks) + len(clean_artists) + len(clean_genres)
        if num_seeds == 0:
            clean_genres = ["pop"]
            num_seeds = 1

        if num_seeds > 5:
            total = [("track", t) for t in clean_tracks] + [("artist", a) for a in clean_artists] + [("genre", g) for g in clean_genres]
            total = total[:5]
            clean_tracks = [x[1] for x in total if x[0] == "track"]
            clean_artists = [x[1] for x in total if x[0] == "artist"]
            clean_genres = [x[1] for x in total if x[0] == "genre"]

        kwargs = {}
        if target_energy is not None: kwargs["target_energy"] = max(0.0, min(1.0, float(target_energy)))
        if target_valence is not None: kwargs["target_valence"] = max(0.0, min(1.0, float(target_valence)))
        if target_danceability is not None: kwargs["target_danceability"] = max(0.0, min(1.0, float(target_danceability)))
        if target_acousticness is not None: kwargs["target_acousticness"] = max(0.0, min(1.0, float(target_acousticness)))
        if target_instrumentalness is not None: kwargs["target_instrumentalness"] = max(0.0, min(1.0, float(target_instrumentalness)))
        if target_tempo is not None: kwargs["target_tempo"] = float(target_tempo)
        if min_popularity is not None: kwargs["min_popularity"] = max(0, min(100, int(min_popularity)))
        if max_popularity is not None: kwargs["max_popularity"] = max(0, min(100, int(max_popularity)))

        rec_limit = max(1, min(limit, 100))
        results = sp.recommendations(
            seed_tracks=clean_tracks or None,
            seed_artists=clean_artists or None,
            seed_genres=clean_genres or None,
            limit=rec_limit,
            market=market,
            **kwargs
        )

        tracks = results.get("tracks", [])
        if not tracks:
            return "No recommendations found for the provided seeds and parameters."

        seeds_desc = []
        if clean_tracks: seeds_desc.append(f"Tracks: {len(clean_tracks)}")
        if clean_artists: seeds_desc.append(f"Artists: {len(clean_artists)}")
        if clean_genres: seeds_desc.append(f"Genres: {', '.join(clean_genres)}")

        lines = [
            f"Spotify Recommendations (Seeds: {', '.join(seeds_desc)}):",
            f"Found {len(tracks)} track recommendations:\n"
        ]

        for idx, t in enumerate(tracks, 1):
            artists = ", ".join(a.get("name", "Unknown") for a in t.get("artists", []))
            album = t.get("album", {}).get("name", "Unknown Album")
            dur = _format_duration(t.get("duration_ms", 0))
            pop = t.get("popularity", 0)
            lines.append(f"{idx}. {t.get('name')} - {artists} ({dur}) [Album: {album}] (Popularity: {pop}/100, URI: {t.get('uri')})")

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
            m_norm = re.sub(r'[^a-z0-9\s]', '', movie.lower()).strip()
            t_norm = re.sub(r'[^a-z0-9\s]', '', target.lower()).strip()
            if not m_norm or not t_norm:
                return False
            
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
            for album in found:
                if is_fuzzy_match(clean_title, album.get("name", ""), language_name):
                    if is_year_match(album.get("release_date", ""), release_year):
                        albums = [album]
                        break
            if albums:
                break

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
                
                if not is_fuzzy_match(clean_title, track_name, language_name) and not is_fuzzy_match(clean_title, album_name, language_name):
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
        print(f"Error fetching soundtrack for {movie_title}: {e}")
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
            genres = ", ".join(a.get("genres", [])) or "None specified"
            followers = a.get("followers", {}).get("total", 0)
            pop = a.get("popularity", 0)
            lines.append(f"{idx}. {a.get('name')} (Followers: {followers:,}, Popularity: {pop}/100, Genres: {genres}, URI: {a.get('uri')})")
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
            pop = t.get("popularity", 0)
            lines.append(f"{idx}. {t.get('name')} - {artists} ({dur}) [Album: {album}] (Popularity: {pop}/100, URI: {t.get('uri')})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error searching songs: {str(e)}"





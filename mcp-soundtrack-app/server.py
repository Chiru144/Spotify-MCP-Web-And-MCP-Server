import os
import sys
import random
from datetime import datetime, timezone
from collections import Counter
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
import spotipy
from spotipy.oauth2 import SpotifyPKCE
import http.server
import socketserver
import threading
import urllib.parse

# Ensure tools package from root directory is always importable
BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Spotify client that reports long rate limits instead of sleeping through them
from tools.spotify_client import FailFastSpotify

# Load environment variables (check root folder as primary single source of truth)
env_parent = BASE_DIR.parent / ".env"
env_local = BASE_DIR / ".env"
if env_parent.exists():
    load_dotenv(dotenv_path=env_parent)
if env_local.exists():
    load_dotenv(dotenv_path=env_local, override=False)
if not env_parent.exists() and not env_local.exists():
    load_dotenv()

recently_modified_counts = {}

app = FastAPI(title="Soundtrack Curator & Staging Studio")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_READ_ACCESS_TOKEN = os.getenv("TMDB_READ_ACCESS_TOKEN")

# Helper to get valid non-placeholder credentials
def _get_credential(key1: str, key2: str) -> str:
    v1 = os.getenv(key1, "").strip()
    v2 = os.getenv(key2, "").strip()
    if v1 and "your_" not in v1 and not v1.startswith("your_"):
        return v1
    if v2 and "your_" not in v2 and not v2.startswith("your_"):
        return v2
    return v1 or v2

SPOTIFY_CLIENT_ID = _get_credential("SPOTIFY_CLIENT_ID", "SPOTIPY_CLIENT_ID")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI") or os.getenv("SPOTIPY_REDIRECT_URI") or "http://127.0.0.1:8888/callback"

SCOPES = [
    "playlist-modify-public",
    "playlist-modify-private",
    "playlist-read-private",
    "playlist-read-collaborative",
    "user-modify-playback-state",
    "user-read-playback-state",
    "user-read-currently-playing",
    "user-read-recently-played",
    "user-top-read",
    "user-library-read",
    "user-library-modify",
    "user-read-private",
    "user-read-email",
]

public_sp = None


# User OAuth Manager for authenticated actions (using shared root cache via PKCE)
_cache_file = BASE_DIR.parent / ".spotipyoauthcache"
if not _cache_file.exists() and (BASE_DIR / ".spotipyoauthcache").exists():
    _cache_file = BASE_DIR / ".spotipyoauthcache"

oauth_manager = SpotifyPKCE(
    client_id=SPOTIFY_CLIENT_ID,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=" ".join(SCOPES),
    cache_path=str(_cache_file),
    open_browser=True
)


class OAuth8888Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Silence stderr to keep console clean

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        code = qs.get("code", [None])[0]
        error = qs.get("error", [None])[0]

        if code:
            try:
                oauth_manager.get_access_token(code)
                self.send_response(302)
                self.send_header("Location", "http://127.0.0.1:8000/?connected=true")
                self.end_headers()
                return
            except Exception as e:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html = f"""<!DOCTYPE html>
<html>
<head><title>Spotify Authorization</title><meta http-equiv="refresh" content="2;url=http://127.0.0.1:8000/?connected=true"></head>
<body style="background:#090c10;color:#fff;font-family:sans-serif;padding:50px;text-align:center;">
  <h2 style="color:#1db954;">Spotify Authorization Handled!</h2>
  <p>{e}</p>
  <p><a href="http://127.0.0.1:8000/?connected=true" style="color:#1db954;font-size:18px;">Return to Soundtrack Curator Studio</a></p>
</body>
</html>"""
                self.wfile.write(html.encode("utf-8"))
                return

        self.send_response(302)
        self.send_header("Location", f"http://127.0.0.1:8000/?auth_error={error or 'cancelled'}")
        self.end_headers()


_oauth_server_started = False
def start_oauth_callback_server(port: int = 8888):
    global _oauth_server_started
    if _oauth_server_started:
        return
    try:
        class ReusableTCPServer(socketserver.TCPServer):
            allow_reuse_address = True

        server_8888 = ReusableTCPServer(("127.0.0.1", port), OAuth8888Handler)
        t = threading.Thread(target=server_8888.serve_forever, daemon=True, name="OAuth8888Listener")
        t.start()
        _oauth_server_started = True
        print(f"[OAuth Helper] Callback listener active on http://127.0.0.1:{port}/callback", file=sys.stderr)
    except Exception as e:
        print(f"[OAuth Helper] Note: Port {port} listener not started: {e}", file=sys.stderr)

# Automatically start background listener on port 8888
start_oauth_callback_server(8888)


def _get_valid_user_client() -> Optional[spotipy.Spotify]:
    """Returns authenticated spotipy.Spotify if valid token exists in cache, else None (never blocks)."""
    token_info = oauth_manager.cache_handler.get_cached_token()
    if not token_info:
        return None
    if oauth_manager.is_token_expired(token_info):
        try:
            token_info = oauth_manager.refresh_access_token(token_info.get("refresh_token"))
        except Exception:
            token_info = None
    if token_info and token_info.get("access_token"):
        return FailFastSpotify(auth=token_info["access_token"])
    return None





def _get_tmdb_headers_and_params(extra_params: dict = None) -> tuple[dict, dict]:
    params = (extra_params or {}).copy()
    headers = {"accept": "application/json"}
    
    token = (os.getenv("TMDB_READ_ACCESS_TOKEN") or TMDB_READ_ACCESS_TOKEN or "").strip()
    api_key = (os.getenv("TMDB_API_KEY") or TMDB_API_KEY or "").strip()
    if "your_" in token:
        token = ""
    if "your_" in api_key:
        api_key = ""

    # Detect whether provided credential is a Bearer JWT or standard v3 key
    bearer = None
    v3 = None
    for val in (token, api_key):
        if not val:
            continue
        if len(val) > 40 or val.startswith("eyJ"):
            if not bearer:
                bearer = val
        else:
            if not v3:
                v3 = val

    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    elif v3:
        params["api_key"] = v3

    return headers, params


def fetch_soundtrack_tracks(movie_title: str, language_name: str = None, release_year: str = None, actor_name: str = None) -> list[dict]:
    """Searches Spotify for movie soundtrack tracks using client credentials or user client (delegated to tools.search)."""
    client = _get_valid_user_client() or public_sp
    from tools.search import fetch_soundtrack_tracks_with_client
    return fetch_soundtrack_tracks_with_client(
        movie_title=movie_title,
        language_name=language_name,
        release_year=release_year,
        actor_name=actor_name,
        sp=client
    )


@app.get("/api/movie/tracks")
def get_movie_soundtracks(
    movie_title: str = Query(..., description="Movie Title"),
    lang: Optional[str] = Query(None, description="Language filter"),
    release_year: Optional[str] = Query(None, description="Release year of the movie"),
    actor_name: Optional[str] = Query(None, description="Actor name")
):
    """Fetches official soundtrack tracks on demand when a movie card is clicked."""
    lang_map = {"en": "English", "hi": "Hindi", "te": "Telugu", "ta": "Tamil", "kn": "Kannada", "ml": "Malayalam"}
    tracks = fetch_soundtrack_tracks(movie_title, language_name=lang_map.get(lang), release_year=release_year, actor_name=actor_name)
    return {"movie_title": movie_title, "tracks": tracks}


# =====================================================================
# API Endpoints
# =====================================================================

@app.get("/login")
def login_redirect():
    """Redirect to Spotify OAuth authorize page."""
    auth_url = oauth_manager.get_authorize_url()
    return RedirectResponse(auth_url)


@app.get("/callback")
def oauth_callback(code: Optional[str] = None, error: Optional[str] = None):
    """Handle callback from Spotify OAuth redirect."""
    if error:
        return RedirectResponse(f"/?auth_error={error}")
    if code:
        try:
            oauth_manager.get_access_token(code)
            return RedirectResponse("/?connected=true")
        except Exception as e:
            return RedirectResponse(f"/?auth_error={urllib.parse.quote(str(e))}")
    return RedirectResponse("/")


class CodeExchangeRequest(BaseModel):
    code_or_url: str


@app.post("/api/auth/exchange_code")
def exchange_oauth_code(payload: CodeExchangeRequest):
    """Manual or fallback endpoint to exchange a redirect URL or code for a Spotify token."""
    raw = payload.code_or_url.strip()
    if not raw:
        return {"success": False, "error": "No code or URL provided."}
    
    code = raw
    if "code=" in raw:
        try:
            parsed = urllib.parse.urlparse(raw)
            qs = urllib.parse.parse_qs(parsed.query)
            code = qs.get("code", [raw])[0]
        except Exception:
            code = raw
            
    try:
        token_info = oauth_manager.get_access_token(code)
        if token_info:
            user_client = _get_valid_user_client()
            user_data = user_client.me() if user_client else {}
            return {
                "success": True,
                "display_name": user_data.get("display_name") or user_data.get("id", "Spotify User"),
                "id": user_data.get("id")
            }
        return {"success": False, "error": "Could not validate access token."}
    except Exception as e:
        return {"success": False, "error": str(e)}



@app.get("/api/me")
def get_user_profile():
    """Returns connected Spotify account info without blocking on terminal stdin."""
    try:
        user_client = _get_valid_user_client()
        if not user_client:
            auth_url = oauth_manager.get_authorize_url()
            return {"authenticated": False, "auth_url": auth_url}

        user = user_client.me()
        token_info = oauth_manager.cache_handler.get_cached_token()
        token_scope = token_info.get("scope", "") if token_info else ""
        has_playlist_read = "playlist-read-private" in token_scope
        return {
            "authenticated": True,
            "id": user.get("id"),
            "display_name": user.get("display_name") or user.get("id"),
            "images": user.get("images", []),
            "product": user.get("product", "unknown"),
            "has_playlist_read": has_playlist_read,
            "auth_url": oauth_manager.get_authorize_url() if not has_playlist_read else None
        }
    except Exception as e:
        return {"authenticated": False, "error": str(e), "auth_url": oauth_manager.get_authorize_url()}


@app.get("/api/search/movies")
def search_movies_only(
    query: str = Query(..., description="Movie title"),
    limit: int = Query(25, description="Number of items to show"),
    sort_by: str = Query("date_desc", description="Sort rank: date_desc, date_asc, popularity, rating, title"),
    lang: Optional[str] = Query(None, description="Language filter")
):
    """Dedicated Movie Search: searches TMDB specifically for movies and loads soundtrack songs."""
    lang_map = {"en": "English", "hi": "Hindi", "te": "Telugu", "ta": "Tamil", "kn": "Kannada", "ml": "Malayalam"}
    lang_name = lang_map.get(lang)
    headers, params = _get_tmdb_headers_and_params({
        "query": query,
        "include_adult": "false",
        "language": "en-US",
        "page": "1"
    })
    
    movie_search_url = "https://api.tmdb.org/3/search/movie"
    movies_raw = []
    try:
        m_res = requests.get(movie_search_url, headers=headers, params=params, timeout=4).json()
        movies_raw = m_res.get("results", [])
    except Exception as e:
        print(f"Movie search error: {e}", file=sys.stderr)
        
    if not movies_raw:
        # Fallback if TMDB is blocked/down
        movies_raw = [{
            "title": query.title(),
            "release_date": "N/A",
            "overview": "Could not connect to the movie database, but searching Spotify directly for soundtracks...",
            "popularity": 100,
            "vote_average": 0
        }]

    # Sorting
    if sort_by == "date_desc":
        movies_raw.sort(key=lambda x: x.get("release_date") or "0000-00-00", reverse=True)
    elif sort_by == "date_asc":
        movies_raw.sort(key=lambda x: x.get("release_date") or "9999-99-99")
    elif sort_by == "popularity":
        movies_raw.sort(key=lambda x: x.get("popularity", 0), reverse=True)
    elif sort_by == "rating":
        movies_raw.sort(key=lambda x: x.get("vote_average", 0), reverse=True)
    elif sort_by == "title":
        movies_raw.sort(key=lambda x: (x.get("title") or "").lower())

    total_found = len(movies_raw)
    selection = movies_raw[:limit]

    output = []
    soundtrack_fetch_limit = 0 # Disabled synchronous fetching for faster loads
    total_songs_count = 0
    for idx, m in enumerate(selection):
        title = m.get("title")
        release_date = m.get("release_date")
        overview = m.get("overview", "")
        poster = f"https://image.tmdb.org/t/p/w300{m.get('poster_path')}" if m.get("poster_path") else None
        backdrop = f"https://image.tmdb.org/t/p/w780{m.get('backdrop_path')}" if m.get("backdrop_path") else None
        vote_average = m.get("vote_average", 0)
        popularity = m.get("popularity", 0)

        songs = fetch_soundtrack_tracks(title, language_name=lang_name) if idx < soundtrack_fetch_limit else []
        total_songs_count += len(songs)

        output.append({
            "title": title,
            "release_date": release_date,
            "overview": overview[:180] + "..." if len(overview) > 180 else overview,
            "character": "",
            "vote_average": round(vote_average, 1),
            "popularity": round(popularity, 1),
            "poster": poster,
            "backdrop": backdrop,
            "tracks": songs,
            "song_count": len(songs)
        })

    return {
        "mode": "movies",
        "search_type": "movie",
        "query": query,
        "display_name": query,
        "total_results": total_found,
        "shown": len(output),
        "total_songs": total_songs_count,
        "movies": output
    }


@app.get("/api/search/actors")
def search_actors_only(
    query: str = Query(..., description="Actor or actress name"),
    limit: int = Query(25, description="Number of items to show"),
    sort_by: str = Query("popularity", description="Sort rank: popularity, date_desc, date_asc, rating, title"),
    lang: Optional[str] = Query(None, description="Language filter")
):
    """Dedicated Actor Search: searches TMDB for actors, their career filmography, and soundtrack songs."""
    lang_map = {"en": "English", "hi": "Hindi", "te": "Telugu", "ta": "Tamil", "kn": "Kannada", "ml": "Malayalam"}
    lang_name = lang_map.get(lang)
    
    import re
    clean_query = query.lower()
    for word in ["kannada", "telugu", "tamil", "hindi", "malayalam", "english", "bollywood", "tollywood", "kollywood", "sandalwood", "actor", "actress", "singer", "director"]:
        clean_query = re.sub(rf"\b{word}\b", "", clean_query)
    clean_query = clean_query.strip() or query

    headers, params = _get_tmdb_headers_and_params({
        "query": clean_query,
        "include_adult": "false",
        "language": "en-US",
        "page": "1"
    })
    
    person_search_url = "https://api.tmdb.org/3/search/person"
    actor_data = None
    movies_raw = []

    try:
        person_res = requests.get(person_search_url, headers=headers, params=params, timeout=4).json()
        person_results = person_res.get("results", [])
        
        if person_results:
            person = person_results[0]
            person_id = person["id"]
            actor_name = person.get("name", query)
            
            # Fetch profile details
            p_headers, p_params = _get_tmdb_headers_and_params()
            try:
                prof_res = requests.get(f"https://api.tmdb.org/3/person/{person_id}", headers=p_headers, params=p_params, timeout=4).json()
            except Exception:
                prof_res = person

            credits_url = f"https://api.tmdb.org/3/person/{person_id}/movie_credits"
            credits = requests.get(credits_url, headers=p_headers, params=p_params, timeout=4).json()
            cast = credits.get("cast", [])
            if lang:
                movies_raw = [m for m in cast if m.get("title") and m.get("original_language") == lang]
            else:
                movies_raw = [m for m in cast if m.get("title")]

            actor_data = {
                "id": person_id,
                "name": actor_name,
                "biography": prof_res.get("biography", ""),
                "birthday": prof_res.get("birthday"),
                "place_of_birth": prof_res.get("place_of_birth"),
                "popularity": prof_res.get("popularity", person.get("popularity", 0)),
                "profile_path": f"https://image.tmdb.org/t/p/w300{person.get('profile_path')}" if person.get("profile_path") else None,
                "known_for_department": prof_res.get("known_for_department", "Acting")
            }
    except Exception as e:
        print(f"Actor search error: {e}", file=sys.stderr)

    if not movies_raw:
        # Fallback if TMDB is blocked
        movies_raw = [{
            "title": f"{query.title()} Movies",
            "release_date": "N/A",
            "overview": "Could not connect to the movie database, but searching Spotify directly for soundtracks...",
            "popularity": 100,
            "vote_average": 0
        }]
        actor_data = {"name": query.title()}

    # Sorting
    if sort_by == "popularity":
        movies_raw.sort(key=lambda x: x.get("popularity", 0), reverse=True)
    elif sort_by == "date_desc":
        movies_raw.sort(key=lambda x: x.get("release_date") or "0000-00-00", reverse=True)
    elif sort_by == "date_asc":
        movies_raw.sort(key=lambda x: x.get("release_date") or "9999-99-99")
    elif sort_by == "rating":
        movies_raw.sort(key=lambda x: x.get("vote_average", 0), reverse=True)
    elif sort_by == "title":
        movies_raw.sort(key=lambda x: (x.get("title") or "").lower())

    total_found = len(movies_raw)
    selection = movies_raw[:limit]

    output = []
    soundtrack_fetch_limit = 0 # Disabled synchronous fetching for faster loads
    total_songs_count = 0
    for idx, m in enumerate(selection):
        title = m.get("title")
        release_date = m.get("release_date")
        overview = m.get("overview", "")
        poster = f"https://image.tmdb.org/t/p/w300{m.get('poster_path')}" if m.get("poster_path") else None
        backdrop = f"https://image.tmdb.org/t/p/w780{m.get('backdrop_path')}" if m.get("backdrop_path") else None
        character = m.get("character", "")
        vote_average = m.get("vote_average", 0)
        popularity = m.get("popularity", 0)

        songs = fetch_soundtrack_tracks(title, language_name=lang_name) if idx < soundtrack_fetch_limit else []
        total_songs_count += len(songs)

        output.append({
            "title": title,
            "release_date": release_date,
            "overview": overview[:180] + "..." if len(overview) > 180 else overview,
            "character": character,
            "vote_average": round(vote_average, 1),
            "popularity": round(popularity, 1),
            "poster": poster,
            "backdrop": backdrop,
            "tracks": songs,
            "song_count": len(songs)
        })

    return {
        "mode": "actors",
        "search_type": "actor",
        "query": query,
        "display_name": actor_data["name"] if actor_data else query,
        "actor": actor_data,
        "total_results": total_found,
        "shown": len(output),
        "total_songs": total_songs_count,
        "movies": output
    }


@app.get("/api/search")
def search_movies(
    query: str = Query(..., description="Actor name or movie title"),
    limit: int = Query(25, description="Number of items to show"),
    sort_by: str = Query("date_desc", description="Sort rank: date_desc, date_asc, popularity, rating, title"),
    search_type: Optional[str] = Query(None, description="'movie' or 'actor'"),
    lang: Optional[str] = Query(None, description="Language filter")
):
    """Unified search endpoint routing to movie or actor search."""
    if search_type == "movie":
        return search_movies_only(query=query, limit=limit, sort_by=sort_by, lang=lang)
    if search_type == "actor":
        return search_actors_only(query=query, limit=limit, sort_by=sort_by, lang=lang)
    
    # Auto-detection fallback
    headers, params = _get_tmdb_headers_and_params({"query": query})
    try:
        person_res = requests.get("https://api.tmdb.org/3/search/person", headers=headers, params=params, timeout=2).json()
        person_results = person_res.get("results", [])
        if person_results and (person_results[0].get("name", "").lower() in query.lower() or query.lower() in person_results[0].get("name", "").lower()):
            return search_actors_only(query=query, limit=limit, sort_by=sort_by, lang=lang)
    except Exception:
        pass
    return search_movies_only(query=query, limit=limit, sort_by=sort_by, lang=lang)


@app.get("/api/search/songs")
def search_songs(
    query: str = Query(..., description="Song title, soundtrack, or artist"),
    limit: int = Query(25, description="Number of songs to show: 10, 25, 50, 100, 200, 500, 1000"),
    sort_by: str = Query("popularity", description="Sort rank: popularity, date_desc, date_asc, duration_desc, duration_asc, name, artist"),
    lang: Optional[str] = Query(None, description="Language filter")
):
    """Direct Spotify Song & Soundtrack Search with limit and ranking filters."""
    lang_map = {"en": "English", "hi": "Hindi", "te": "Telugu", "ta": "Tamil", "kn": "Kannada", "ml": "Malayalam"}
    if lang and lang in lang_map:
        query = f"{query} {lang_map[lang]}"
        
    client = _get_valid_user_client() or public_sp
    if not client:
        return {"error": "Spotify client not configured", "songs": []}

    try:
        fetch_limit = min(limit, 50)
        all_tracks = []

        res = client.search(q=query, type="track", limit=fetch_limit, offset=0)
        items = res.get("tracks", {}).get("items", [])
        total_available = res.get("tracks", {}).get("total", len(items))
        all_tracks.extend(items)

        max_batch = min(limit, 200, total_available)
        offset = fetch_limit
        while offset < max_batch and len(all_tracks) < limit:
            batch_size = min(50, limit - len(all_tracks))
            batch_res = client.search(q=query, type="track", limit=batch_size, offset=offset)
            batch_items = batch_res.get("tracks", {}).get("items", [])
            if not batch_items:
                break
            all_tracks.extend(batch_items)
            offset += len(batch_items)

        formatted = []
        for t in all_tracks:
            album = t.get("album", {})
            artists = t.get("artists", [])
            artist_names = ", ".join([a.get("name", "") for a in artists]) or "Unknown"
            artist_ids = [a.get("id") for a in artists if a.get("id")]

            formatted.append({
                "id": t.get("id"),
                "name": t.get("name"),
                "artist": artist_names,
                "artist_ids": artist_ids,
                "album_name": album.get("name", ""),
                "album_cover": album.get("images", [{}])[0].get("url") if album.get("images") else None,
                "release_date": album.get("release_date", ""),
                "popularity": t.get("popularity", 0),
                "duration_ms": t.get("duration_ms", 0),
                "uri": t.get("uri"),
                "spotify_url": t.get("external_urls", {}).get("spotify"),
                "preview_url": t.get("preview_url")
            })

        if sort_by == "popularity":
            formatted.sort(key=lambda x: x.get("popularity", 0), reverse=True)
        elif sort_by == "date_desc":
            formatted.sort(key=lambda x: x.get("release_date") or "0000", reverse=True)
        elif sort_by == "date_asc":
            formatted.sort(key=lambda x: x.get("release_date") or "9999")
        elif sort_by == "duration_desc":
            formatted.sort(key=lambda x: x.get("duration_ms", 0), reverse=True)
        elif sort_by == "duration_asc":
            formatted.sort(key=lambda x: x.get("duration_ms", 0))
        elif sort_by == "name":
            formatted.sort(key=lambda x: x.get("name", "").lower())
        elif sort_by == "artist":
            formatted.sort(key=lambda x: x.get("artist", "").lower())

        
        return {
            "mode": "songs",
            "query": query,
            "total_results": total_available,
            "shown": len(formatted),
            "songs": formatted
        }
    except Exception as e:
        print(f"Song search error: {e}", file=sys.stderr)
        return {"error": str(e), "songs": [], "total_results": 0}


@app.get("/api/search/track")
def search_direct_track(query: str = Query(..., description="Track search query")):
    """Quick lookup to add custom songs into the Send Box."""
    client = _get_valid_user_client() or public_sp
    if not client:
        return {"error": "Spotify client not initialized", "tracks": []}

    try:
        res = client.search(q=query, type="track", limit=6)
        items = res.get("tracks", {}).get("items", [])
        results = []
        for t in items:
            results.append({
                "name": t.get("name"),
                "artist": t.get("artists", [{}])[0].get("name", "Unknown"),
                "uri": t.get("uri"),
                "album_name": t.get("album", {}).get("name", ""),
                "album_cover": t.get("album", {}).get("images", [{}])[0].get("url") if t.get("album", {}).get("images") else None,
                "spotify_url": t.get("external_urls", {}).get("spotify"),
            })
        return {"tracks": results}
    except Exception as e:
        return {"error": str(e), "tracks": []}


@app.get("/api/search/singers")
def search_singers(
    query: str = Query(..., description="Singer or music artist name"),
    limit: int = Query(25, description="Number of tracks to show"),
    sort_by: str = Query("popularity", description="Sort order: popularity, date_desc, date_asc, name"),
    lang: Optional[str] = Query(None, description="Language filter")
):
    """Searches for singers/artists and returns their discography and songs."""
    lang_map = {"en": "English", "hi": "Hindi", "te": "Telugu", "ta": "Tamil", "kn": "Kannada", "ml": "Malayalam"}
    if lang and lang in lang_map:
        query = f"{query} {lang_map[lang]}"
    client = _get_valid_user_client() or public_sp
    if not client:
        return {"error": "Spotify credentials not configured", "artist": None, "tracks": []}
    
    try:
        # Search for artist
        artist_res = client.search(q=query, type="artist", limit=3)
        artists = artist_res.get("artists", {}).get("items", [])
        top_artist = artists[0] if artists else None

        # Search tracks by artist
        search_q = f"artist:{top_artist['name']}" if top_artist else f"artist:{query}"
        track_res = client.search(q=search_q, type="track", limit=min(limit, 50))
        items = track_res.get("tracks", {}).get("items", [])
        if not items:
            track_res = client.search(q=query, type="track", limit=min(limit, 50))
            items = track_res.get("tracks", {}).get("items", [])

        formatted = []
        for t in items:
            formatted.append({
                "name": t.get("name"),
                "artist": ", ".join(a["name"] for a in t.get("artists", [])) or "Unknown",
                "uri": t.get("uri"),
                "duration_ms": t.get("duration_ms", 0),
                "popularity": t.get("popularity", 50),
                "release_date": t.get("album", {}).get("release_date", ""),
                "spotify_url": t.get("external_urls", {}).get("spotify"),
                "album_name": t.get("album", {}).get("name", ""),
                "album_cover": t.get("album", {}).get("images", [{}])[0].get("url") if t.get("album", {}).get("images") else None,
                "singer_name": top_artist["name"] if top_artist else query
            })

        if sort_by == "popularity":
            formatted.sort(key=lambda x: x.get("popularity", 0), reverse=True)
        elif sort_by == "date_desc":
            formatted.sort(key=lambda x: x.get("release_date") or "0000", reverse=True)
        elif sort_by == "date_asc":
            formatted.sort(key=lambda x: x.get("release_date") or "9999")
        elif sort_by == "name":
            formatted.sort(key=lambda x: (x.get("name") or "").lower())

        artist_data = None
        if top_artist:
            artist_data = {
                "name": top_artist.get("name"),
                "id": top_artist.get("id"),
                "image": top_artist.get("images", [{}])[0].get("url") if top_artist.get("images") else None,
                "genres": top_artist.get("genres", [])[:4],
                "followers": top_artist.get("followers", {}).get("total", 0),
                "popularity": top_artist.get("popularity", 0),
                "spotify_url": top_artist.get("external_urls", {}).get("spotify")
            }

        return {
            "mode": "singers",
            "query": query,
            "artist": artist_data,
            "total_results": len(formatted),
            "tracks": formatted[:limit]
        }
    except Exception as e:
        return {"error": str(e), "artist": None, "tracks": [], "total_results": 0}


class PlaylistCreateRequest(BaseModel):
    name: str
    description: Optional[str] = "Curated with Soundtrack Curator"
    public: Optional[bool] = False
    track_uris: List[str]


@app.post("/api/playlist/create")
def create_playlist(payload: PlaylistCreateRequest):
    """Creates a Spotify playlist with the chosen name and staged tracks."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {
            "success": False,
            "need_auth": True,
            "auth_url": oauth_manager.get_authorize_url(),
            "error": "Spotify authorization required. Click 'Connect Spotify' in the top right to link your account."
        }

    try:
        playlist_name = payload.name.strip() or "Curated Soundtracks"
        # Use current_user_playlist_create (POST /v1/me/playlists) which is the modern Spotify endpoint
        playlist = user_client.current_user_playlist_create(
            name=playlist_name,
            public=bool(payload.public),
            description=payload.description or "Curated with Soundtrack Curator Studio"
        )
        valid_uris = [u for u in payload.track_uris if u and u.startswith("spotify:track:")]
        if valid_uris:
            for i in range(0, len(valid_uris), 100):
                user_client.playlist_add_items(playlist_id=playlist["id"], items=valid_uris[i:i+100])

        return {
            "success": True,
            "playlist_id": playlist["id"],
            "playlist_name": playlist.get("name"),
            "playlist_url": playlist.get("external_urls", {}).get("spotify"),
            "track_count": len(valid_uris),
            "song_count": len(valid_uris)
        }
    except Exception as e:
        err_msg = str(e)
        if "403" in err_msg or "Insufficient client scope" in err_msg:
            return {
                "success": False,
                "need_auth": True,
                "auth_url": oauth_manager.get_authorize_url(),
                "error": "Spotify permission issue (403). Click 'Connect Spotify' in the top right to grant playlist creation permissions."
            }
        return {"success": False, "error": str(e)}


@app.get("/api/user/playlists")
def get_user_playlists():
    """Returns the authenticated user's Spotify playlists for fetching/appending."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {
            "authenticated": False,
            "playlists": [],
            "error": "Spotify authorization required."
        }
    try:
        current_user = user_client.me()
        current_user_id = current_user.get("id")
        
        playlists_data = user_client.current_user_playlists(limit=50)
        items = playlists_data.get("items", [])
        results = []
        for p in items:
            if not p:
                continue
            
            # Filter to only show playlists owned by the user (not followed/restricted ones)
            owner_id = p.get("owner", {}).get("id")
            if owner_id != current_user_id:
                continue
                
            images = p.get("images") or []
            cover = images[0].get("url") if images else None
            
            pid = p.get("id")
            total = p.get("tracks", p.get("items", {})).get("total", 0)
            if pid in recently_modified_counts:
                total = recently_modified_counts[pid]
                
            results.append({
                "id": pid,
                "name": p.get("name", "Untitled Playlist"),
                "description": p.get("description", ""),
                "total_tracks": total,
                "cover_url": cover,
                "owner": p.get("owner", {}).get("display_name") or p.get("owner", {}).get("id", "Unknown"),
                "spotify_url": p.get("external_urls", {}).get("spotify"),
                "uri": p.get("uri")
            })
        return {"authenticated": True, "playlists": results}
    except Exception as e:
        err_msg = str(e)
        if "Insufficient client scope" in err_msg or "403" in err_msg:
            return {
                "authenticated": True,
                "need_scope": True,
                "auth_url": oauth_manager.get_authorize_url(),
                "playlists": [],
                "error": "Additional Spotify permissions needed to view your playlists. Click 'Connect Spotify' to grant playlist reading permissions."
            }
        return {"authenticated": True, "playlists": [], "error": str(e)}


@app.get("/api/playlist/fetch")
def fetch_playlist_tracks(query: str = Query(..., description="Spotify Playlist URL, URI, or ID")):
    """Fetches full track list and details for any Spotify playlist."""
    cleaned = query.strip()
    playlist_id = cleaned
    if "playlist/" in cleaned:
        playlist_id = cleaned.split("playlist/")[1]
    elif "spotify:playlist:" in cleaned:
        playlist_id = cleaned.split("spotify:playlist:")[1]
    
    playlist_id = playlist_id.split("?")[0].split("/")[0]

    client = _get_valid_user_client() or public_sp
    if not client:
        return {"success": False, "error": "Spotify credentials not configured."}

    try:
        pl = client.playlist(playlist_id)
        name = pl.get("name", "Spotify Playlist")
        desc = pl.get("description", "")
        images = pl.get("images") or []
        cover = images[0].get("url") if images else None
        owner = pl.get("owner", {}).get("display_name") or pl.get("owner", {}).get("id", "Unknown")
        spotify_url = pl.get("external_urls", {}).get("spotify")
        total_tracks = pl.get("tracks", pl.get("items", {})).get("total", 0)

        tracks = []
        try:
            items_res = client.playlist_items(playlist_id, limit=100)
            while items_res:
                items = items_res.get("items", [])
                for it in items:
                    t = it.get("track") or it.get("item")
                    if not t or not t.get("uri"):
                        continue
                    artists = ", ".join(a.get("name", "Unknown") for a in t.get("artists", []))
                    album_imgs = t.get("album", {}).get("images") or []
                    track_cover = album_imgs[0].get("url") if album_imgs else cover
                    tracks.append({
                        "name": t.get("name"),
                        "artist": artists,
                        "uri": t.get("uri"),
                        "duration_ms": t.get("duration_ms", 0),
                        "popularity": t.get("popularity", 50),
                        "album_name": t.get("album", {}).get("name", ""),
                        "album_cover": track_cover,
                        "spotify_url": t.get("external_urls", {}).get("spotify"),
                        "source_playlist": name
                    })
                if items_res.get("next"):
                    items_res = client.next(items_res)
                else:
                    break
        except Exception as te:
            print(f"Error reading playlist items: {te}", file=sys.stderr)

        return {
            "success": True,
            "playlist": {
                "id": playlist_id,
                "name": name,
                "description": desc,
                "cover_url": cover,
                "owner": owner,
                "spotify_url": spotify_url,
                "track_count": total_tracks if total_tracks > 0 else len(tracks)
            },
            "tracks": tracks
        }
    except Exception as e:
        return {"success": False, "error": f"Could not fetch playlist: {str(e)}"}


class PlaylistAppendRequest(BaseModel):
    playlist_id: str
    track_uris: List[str]


@app.post("/api/playlist/append")
def append_to_playlist(payload: PlaylistAppendRequest):
    """Appends staged tracks to an existing Spotify playlist."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {
            "success": False,
            "need_auth": True,
            "auth_url": oauth_manager.get_authorize_url(),
            "error": "Spotify authorization required. Click 'Connect Spotify' in the top right to link your account."
        }

    try:
        pid = payload.playlist_id.strip()
        if "playlist/" in pid:
            pid = pid.split("playlist/")[1]
        elif "spotify:playlist:" in pid:
            pid = pid.split("spotify:playlist:")[1]
            
        pid = pid.split("?")[0].split("/")[0]

        valid_uris = [u for u in payload.track_uris if u and u.startswith("spotify:track:")]
        if not valid_uris:
            return {"success": False, "error": "No valid track URIs provided."}

        for i in range(0, len(valid_uris), 100):
            user_client.playlist_add_items(playlist_id=pid, items=valid_uris[i:i+100])

        return {
            "success": True,
            "playlist_id": pid,
            "added_count": len(valid_uris),
            "song_count": len(valid_uris),
            "message": f"Added {len(valid_uris)} song(s) to playlist."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


from typing import Optional

class PlaylistShuffleRequest(BaseModel):
    playlist_id: str
    in_place: bool = False
    new_name: Optional[str] = None


@app.post("/api/playlist/shuffle")
def shuffle_playlist(payload: PlaylistShuffleRequest):
    """Mixes and shuffles all songs in a Spotify playlist into a completely new random order."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {
            "success": False,
            "need_auth": True,
            "auth_url": oauth_manager.get_authorize_url(),
            "error": "Spotify authorization required. Click 'Connect Spotify' in the top right to link your account."
        }

    try:
        pid = payload.playlist_id.strip()
        if "playlist/" in pid:
            pid = pid.split("playlist/")[1]
        elif "spotify:playlist:" in pid:
            pid = pid.split("spotify:playlist:")[1]
            
        pid = pid.split("?")[0].split("/")[0]

        # Fetch all songs (handle paging)
        items = []
        try:
            res = user_client.playlist_items(pid, limit=100)
            while res:
                items.extend(res.get("items", []))
                if res.get("next"):
                    res = user_client.next(res)
                else:
                    break
        except Exception as e:
            if "403" in str(e):
                return {"success": False, "error": "Spotify refused access (403 Forbidden). This playlist is either private to another user or completely restricted."}
            raise e

        valid_tracks = [it.get("track") or it.get("item") for it in items if (it.get("track") or it.get("item")) and (it.get("track") or it.get("item")).get("uri")]
        if not valid_tracks:
            return {"success": False, "error": "No songs found in this playlist to shuffle."}

        total_songs = len(valid_tracks)
        # Mix/shuffle all the songs into a different order
        shuffled = list(valid_tracks)
        random.shuffle(shuffled)

        try:
            playlist = user_client.playlist(pid)
        except Exception as e:
            if "403" in str(e):
                return {"success": False, "error": "Spotify refused access (403 Forbidden). This playlist is either private to another user or completely restricted."}
            raise e
        
        original_name = playlist.get("name", "Shuffled Playlist")
        
        shuffled_uris = [t["uri"] for t in shuffled if t.get("uri", "").startswith("spotify:track:")]
        if not shuffled_uris:
            return {"success": False, "error": "No valid tracks to shuffle."}
            
        if payload.in_place:
            current_user = user_client.me().get("id")
            owner_id = playlist.get("owner", {}).get("id")
            if current_user != owner_id:
                return {"success": False, "error": "You cannot shuffle a playlist in-place if you are not the owner. Please use 'Create New Shuffled' instead."}
                
            new_pid = pid
            user_client.playlist_replace_items(new_pid, shuffled_uris[:100])
            for i in range(100, len(shuffled_uris), 100):
                user_client.playlist_add_items(new_pid, shuffled_uris[i:i+100])
            msg = f"Successfully shuffled {total_songs} songs in-place!"
        else:
            final_name = payload.new_name.strip() if payload.new_name and payload.new_name.strip() else original_name
            new_playlist = user_client.current_user_playlist_create(
                name=final_name,
                public=playlist.get("public", False),
                description=f"Shuffled version of {original_name}"
            )
            new_pid = new_playlist["id"]
            user_client.playlist_add_items(new_pid, shuffled_uris[:100])
            for i in range(100, len(shuffled_uris), 100):
                user_client.playlist_add_items(new_pid, shuffled_uris[i:i+100])
            msg = f"Successfully mixed and shuffled {total_songs} songs into '{final_name}'!"

        formatted_songs = []
        for t in shuffled:
            artists = ", ".join(a.get("name", "Unknown") for a in t.get("artists", []))
            album_imgs = t.get("album", {}).get("images") or []
            cover = album_imgs[0].get("url") if album_imgs else None
            formatted_songs.append({
                "name": t.get("name"),
                "artist": artists,
                "uri": t.get("uri"),
                "duration_ms": t.get("duration_ms", 0),
                "popularity": t.get("popularity", 50),
                "album_name": t.get("album", {}).get("name", ""),
                "album_cover": cover,
                "spotify_url": t.get("external_urls", {}).get("spotify")
            })

        return {
            "success": True,
            "playlist_id": new_pid,
            "song_count": total_songs,
            "message": msg,
            "tracks": formatted_songs
        }
    except Exception as e:
        return {"success": False, "error": str(e)}



class PlaylistDedupeRequest(BaseModel):
    playlist_id: str

@app.post("/api/playlist/dedupe")
def dedupe_playlist(payload: PlaylistDedupeRequest):
    """Removes duplicate songs (same name and artist) from a playlist in-place."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {
            "success": False,
            "need_auth": True,
            "auth_url": oauth_manager.get_authorize_url(),
            "error": "Spotify authorization required. Click 'Connect Spotify' in the top right to link your account."
        }

    try:
        pid = payload.playlist_id.strip()
        if "playlist/" in pid:
            pid = pid.split("playlist/")[1]
        elif "spotify:playlist:" in pid:
            pid = pid.split("spotify:playlist:")[1]
        pid = pid.split("?")[0].split("/")[0]

        pl = user_client.playlist(pid, fields="snapshot_id")
        snapshot_id = pl.get("snapshot_id")

        items = []
        res = user_client.playlist_items(pid, limit=100)
        while res:
            items.extend(res.get("items", []))
            if res.get("next"):
                res = user_client.next(res)
            else:
                break

        seen = set()
        removals = []

        for idx, it in enumerate(items):
            t = it.get("track") or it.get("item")
            if not t or not t.get("uri"):
                continue
                
            uri = t.get("uri")
            name = t.get("name", "").strip().lower()
            artists = ", ".join(a.get("name", "").strip().lower() for a in t.get("artists", []))
            
            key = f"{name}::{artists}"
            
            if key in seen:
                removals.append((idx, uri))
            else:
                seen.add(key)
                
        if not removals:
            return {"success": True, "removed_count": 0, "message": "No duplicates found! Your playlist is clean."}
            
        removals.sort(key=lambda x: x[0], reverse=True)
        remove_payload = [{"uri": uri, "positions": [idx]} for idx, uri in removals]
            
        # Process in batches of 100
        for i in range(0, len(remove_payload), 100):
            batch = remove_payload[i:i+100]
            del_res = user_client.playlist_remove_specific_occurrences_of_items(pid, batch, snapshot_id)
            if del_res and "snapshot_id" in del_res:
                snapshot_id = del_res["snapshot_id"]
                
        # Update our local live cache
        original_total = len(items)
        recently_modified_counts[pid] = original_total - len(removals)
            
        return {"success": True, "removed_count": len(removals), "message": f"Successfully removed {len(removals)} duplicate song(s)."}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


class PlaylistCombineRequest(BaseModel):
    playlist_ids: List[str]
    new_name: str

@app.post("/api/playlist/combine")
def combine_playlists(payload: PlaylistCombineRequest):
    """Combines multiple playlists into a single new playlist."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "error": "Spotify authorization required."}
        
    try:
        if not payload.playlist_ids:
            return {"success": False, "error": "No playlists selected."}
            
        all_uris = []
        for pid in payload.playlist_ids:
            pid = pid.strip()
            if "playlist/" in pid:
                pid = pid.split("playlist/")[1]
            elif "spotify:playlist:" in pid:
                pid = pid.split("spotify:playlist:")[1]
            pid = pid.split("?")[0].split("/")[0]
            
            items = []
            try:
                res = user_client.playlist_items(pid, limit=100)
                while res:
                    items.extend(res.get("items", []))
                    if res.get("next"):
                        res = user_client.next(res)
                    else:
                        break
            except Exception as e:
                if "403" in str(e):
                    return {"success": False, "error": "Spotify refused access to one of the playlists (403 Forbidden)."}
                raise e
                    
            for it in items:
                t = it.get("track") or it.get("item")
                if t and t.get("uri") and t.get("uri").startswith("spotify:track:"):
                    all_uris.append(t.get("uri"))
                    
        if not all_uris:
            return {"success": False, "error": "No valid tracks found to combine."}
            
        new_playlist = user_client.current_user_playlist_create(
            name=payload.new_name or "Combined Playlist",
            public=False,
            description="Combined playlist from multiple sources."
        )
        new_pid = new_playlist["id"]
        
        for i in range(0, len(all_uris), 100):
            user_client.playlist_add_items(new_pid, all_uris[i:i+100])
            
        recently_modified_counts[new_pid] = len(all_uris)
        
        return {
            "success": True,
            "playlist_id": new_pid,
            "song_count": len(all_uris),
            "message": f"Successfully combined {len(payload.playlist_ids)} playlists into '{payload.new_name}' with {len(all_uris)} songs!"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _clean_playlist_id(pid: str) -> str:
    pid = (pid or "").strip()
    if "playlist/" in pid:
        pid = pid.split("playlist/")[1]
    elif "spotify:playlist:" in pid:
        pid = pid.split("spotify:playlist:")[1]
    return pid.split("?")[0].split("/")[0]


class PlaylistRemoveTracksRequest(BaseModel):
    playlist_id: str
    track_uris: List[str]
    snapshot_id: Optional[str] = None

class PlaylistReorderRequest(BaseModel):
    playlist_id: str
    range_start: int
    insert_before: int
    range_length: int = 1
    snapshot_id: Optional[str] = None

class PlaylistUpdateRequest(BaseModel):
    playlist_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    public: Optional[bool] = None
    collaborative: Optional[bool] = None

class PlaylistFollowRequest(BaseModel):
    playlist_id: str
    public: bool = True

class PlaylistUnfollowRequest(BaseModel):
    playlist_id: str

class PlaylistCheckFollowersRequest(BaseModel):
    playlist_id: str
    user_ids: List[str]


@app.get("/api/playlist/details")
def get_playlist_details(playlist_id: str = Query(..., description="Spotify playlist ID or link")):
    """Fetches full metadata and cover for a specific playlist."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        pid = _clean_playlist_id(playlist_id)
        p = user_client.playlist(pid)
        images = p.get("images", [])
        cover_url = images[0].get("url") if images else None
        owner = p.get("owner", {})
        followers = p.get("followers", {}).get("total", 0)
        tracks_total = p.get("tracks", {}).get("total", 0)

        # Check if current user is following this playlist
        is_following = False
        try:
            curr_user = user_client.current_user()
            if curr_user and curr_user.get("id"):
                check_res = user_client.playlist_is_following(pid, [curr_user["id"]])
                is_following = bool(check_res and check_res[0])
        except Exception:
            pass

        return {
            "success": True,
            "id": p.get("id", pid),
            "name": p.get("name"),
            "description": p.get("description"),
            "owner": owner.get("display_name", "Unknown"),
            "owner_id": owner.get("id"),
            "is_owner": owner.get("id") == (user_client.current_user().get("id") if user_client else None),
            "is_following": is_following,
            "followers": followers,
            "tracks_total": tracks_total,
            "public": p.get("public", False),
            "collaborative": p.get("collaborative", False),
            "cover_url": cover_url,
            "spotify_url": p.get("external_urls", {}).get("spotify", "")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/playlist/tracks")
def get_playlist_tracks_endpoint(
    playlist_id: str = Query(..., description="Spotify playlist ID or link"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Paginates through tracks in a specific playlist."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        pid = _clean_playlist_id(playlist_id)
        res = user_client.playlist_items(pid, limit=limit, offset=offset)
        items = res.get("items", [])
        total = res.get("total", 0)

        tracks = []
        for idx, it in enumerate(items, offset + 1):
            t = it.get("track")
            if not t:
                continue
            images = t.get("album", {}).get("images", [])
            cover = images[0].get("url") if images else None
            tracks.append({
                "position": idx,
                "name": t.get("name"),
                "artist": ", ".join(a.get("name", "Unknown") for a in t.get("artists", [])),
                "album": t.get("album", {}).get("name"),
                "cover_url": cover,
                "duration_ms": t.get("duration_ms", 0),
                "uri": t.get("uri"),
                "spotify_url": t.get("external_urls", {}).get("spotify", "")
            })

        return {
            "success": True,
            "playlist_id": pid,
            "total": total,
            "limit": limit,
            "offset": offset,
            "tracks": tracks
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/playlist/remove")
def remove_playlist_tracks(payload: PlaylistRemoveTracksRequest):
    """Removes specific tracks from a playlist."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        pid = _clean_playlist_id(payload.playlist_id)
        valid_uris = [u for u in payload.track_uris if u]
        if not valid_uris:
            return {"success": False, "error": "No tracks provided for removal."}

        for i in range(0, len(valid_uris), 100):
            batch = valid_uris[i:i+100]
            user_client.playlist_remove_all_occurrences_of_items(pid, items=batch, snapshot_id=payload.snapshot_id)

        return {"success": True, "removed": len(valid_uris)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/playlist/reorder")
def reorder_playlist_tracks(payload: PlaylistReorderRequest):
    """Moves tracks within a playlist."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        pid = _clean_playlist_id(payload.playlist_id)
        res = user_client.playlist_reorder_items(
            playlist_id=pid,
            range_start=payload.range_start,
            insert_before=payload.insert_before,
            range_length=payload.range_length,
            snapshot_id=payload.snapshot_id
        )
        return {"success": True, "snapshot_id": res.get("snapshot_id")}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/playlist/update")
def update_playlist_details(payload: PlaylistUpdateRequest):
    """Modifies playlist name, description, or privacy settings."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        pid = _clean_playlist_id(payload.playlist_id)
        kwargs = {}
        if payload.name is not None:
            kwargs["name"] = payload.name
        if payload.description is not None:
            kwargs["description"] = payload.description
        if payload.public is not None:
            kwargs["public"] = payload.public
        if payload.collaborative is not None:
            kwargs["collaborative"] = payload.collaborative

        if not kwargs:
            return {"success": False, "error": "No fields to update."}

        user_client.playlist_change_details(pid, **kwargs)
        return {"success": True, "updated": kwargs}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/playlist/follow")
def follow_playlist_endpoint(payload: PlaylistFollowRequest):
    """Adds a playlist to the user's Spotify library."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        pid = _clean_playlist_id(payload.playlist_id)
        user_client.current_user_follow_playlist(pid)
        return {"success": True, "playlist_id": pid}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/playlist/unfollow")
def unfollow_playlist_endpoint(payload: PlaylistUnfollowRequest):
    """Removes a playlist from the user's Spotify library."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        pid = _clean_playlist_id(payload.playlist_id)
        user_client.current_user_unfollow_playlist(pid)
        return {"success": True, "playlist_id": pid}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/playlist/cover")
def get_playlist_cover_endpoint(playlist_id: str = Query(...)):
    """Fetches high-res cover image URL(s) for a playlist."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        pid = _clean_playlist_id(playlist_id)
        images = user_client.playlist_cover_image(pid)
        return {"success": True, "images": images}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/playlist/check_followers")
def check_playlist_followers_endpoint(payload: PlaylistCheckFollowersRequest):
    """Checks whether specific user IDs follow a playlist."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        pid = _clean_playlist_id(payload.playlist_id)
        if not payload.user_ids:
            return {"success": False, "error": "No user IDs provided."}
        res = user_client.playlist_is_following(pid, payload.user_ids)
        result_map = {uid: bool(f) for uid, f in zip(payload.user_ids, res)}
        return {"success": True, "results": result_map}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ------------------------------------------------------------------------------
# PLAYLIST POWER TOOLS ENDPOINTS
# ------------------------------------------------------------------------------

class PlaylistMergeRequest(BaseModel):
    playlist_ids: List[str]
    target_playlist_id: Optional[str] = None
    new_name: Optional[str] = "Merged Playlist"
    description: Optional[str] = "Merged playlist created via Spotify MCP Power Tools"
    public: bool = False
    deduplicate: bool = True

@app.post("/api/playlist/merge")
def merge_playlists_endpoint(payload: PlaylistMergeRequest):
    """Combines multiple playlists into a new or existing target playlist."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        if not payload.playlist_ids:
            return {"success": False, "error": "No playlist IDs provided."}

        all_uris = []
        source_names = []
        for raw_pid in payload.playlist_ids:
            pid = _clean_playlist_id(raw_pid)
            if not pid: continue
            try:
                pl = user_client.playlist(pid, fields="name")
                source_names.append(pl.get("name", pid))
            except Exception:
                source_names.append(pid)

            items = []
            res = user_client.playlist_items(pid, limit=100)
            while res:
                items.extend(res.get("items", []))
                if res.get("next"):
                    res = user_client.next(res)
                else:
                    break
            for it in items:
                t = it.get("track")
                if t and t.get("uri") and t["uri"].startswith("spotify:track:"):
                    all_uris.append(t["uri"])

        if not all_uris:
            return {"success": False, "error": "No valid tracks found in the selected playlists."}

        if payload.deduplicate:
            seen = set()
            final_uris = []
            for u in all_uris:
                if u not in seen:
                    seen.add(u)
                    final_uris.append(u)
        else:
            final_uris = all_uris

        if payload.target_playlist_id:
            tgt_id = _clean_playlist_id(payload.target_playlist_id)
            tgt_pl = user_client.playlist(tgt_id, fields="name,external_urls")
            for i in range(0, len(final_uris), 100):
                user_client.playlist_add_items(tgt_id, final_uris[i:i+100])
            return {
                "success": True,
                "playlist_id": tgt_id,
                "name": tgt_pl.get("name", tgt_id),
                "tracks_added": len(final_uris),
                "spotify_url": tgt_pl.get("external_urls", {}).get("spotify", ""),
                "message": f"Successfully merged {len(final_uris)} tracks into '{tgt_pl.get('name')}'!"
            }
        else:
            user_info = user_client.current_user()
            new_pl = user_client.user_playlist_create(
                user_info["id"],
                name=payload.new_name or "Merged Playlist",
                public=payload.public,
                description=payload.description or "Merged playlist created via Spotify MCP Power Tools"
            )
            new_pid = new_pl["id"]
            for i in range(0, len(final_uris), 100):
                user_client.playlist_add_items(new_pid, final_uris[i:i+100])
            return {
                "success": True,
                "playlist_id": new_pid,
                "name": new_pl.get("name"),
                "tracks_added": len(final_uris),
                "spotify_url": new_pl.get("external_urls", {}).get("spotify", ""),
                "message": f"Successfully merged {len(final_uris)} tracks into new playlist '{new_pl.get('name')}'!"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


class PlaylistSplitArtistRequest(BaseModel):
    playlist_id: str
    min_tracks_per_artist: int = 2
    create_playlists: bool = False
    public: bool = False

@app.post("/api/playlist/split_by_artist")
def split_playlist_by_artist_endpoint(payload: PlaylistSplitArtistRequest):
    """Separates tracks in a playlist into sub-playlists by artist."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        pid = _clean_playlist_id(payload.playlist_id)
        pl = user_client.playlist(pid, fields="name")
        orig_name = pl.get("name", "Playlist")

        items = []
        res = user_client.playlist_items(pid, limit=100)
        while res:
            items.extend(res.get("items", []))
            if res.get("next"):
                res = user_client.next(res)
            else:
                break

        artist_map = {}
        for it in items:
            t = it.get("track")
            if not t or not t.get("uri") or not t["uri"].startswith("spotify:track:"):
                continue
            art_list = t.get("artists", [])
            p_art = art_list[0].get("name", "Unknown Artist") if art_list else "Unknown Artist"
            artist_map.setdefault(p_art, []).append({
                "name": t.get("name"),
                "uri": t.get("uri"),
                "artist": p_art
            })

        qualifying = {art: tracks for art, tracks in artist_map.items() if len(tracks) >= payload.min_tracks_per_artist}
        other_tracks = [t for art, tracks in artist_map.items() if len(tracks) < payload.min_tracks_per_artist for t in tracks]
        sorted_artists = sorted(qualifying.items(), key=lambda x: len(x[1]), reverse=True)

        if not payload.create_playlists:
            preview_artists = []
            for art, tracks in sorted_artists:
                preview_artists.append({
                    "artist": art,
                    "count": len(tracks),
                    "sample": [t["name"] for t in tracks[:3]]
                })
            return {
                "success": True,
                "preview_mode": True,
                "playlist_name": orig_name,
                "total_tracks": len(items),
                "qualifying_artists": preview_artists,
                "other_count": len(other_tracks)
            }
        else:
            user_info = user_client.current_user()
            user_id = user_info["id"]
            created = []
            for art, tracks in sorted_artists:
                sub_name = f"{orig_name} - {art}"
                sub_desc = f"Artist split of '{orig_name}' with {art} songs."
                new_pl = user_client.user_playlist_create(user_id, name=sub_name, public=payload.public, description=sub_desc)
                sub_id = new_pl["id"]
                uris = [t["uri"] for t in tracks]
                for i in range(0, len(uris), 100):
                    user_client.playlist_add_items(sub_id, uris[i:i+100])
                created.append({
                    "name": sub_name,
                    "id": sub_id,
                    "count": len(tracks),
                    "spotify_url": new_pl.get("external_urls", {}).get("spotify", "")
                })

            if other_tracks:
                sub_name = f"{orig_name} - Various Artists"
                sub_desc = f"Remaining tracks from '{orig_name}' with fewer than {payload.min_tracks_per_artist} songs."
                new_pl = user_client.user_playlist_create(user_id, name=sub_name, public=payload.public, description=sub_desc)
                sub_id = new_pl["id"]
                uris = [t["uri"] for t in other_tracks]
                for i in range(0, len(uris), 100):
                    user_client.playlist_add_items(sub_id, uris[i:i+100])
                created.append({
                    "name": sub_name,
                    "id": sub_id,
                    "count": len(other_tracks),
                    "spotify_url": new_pl.get("external_urls", {}).get("spotify", "")
                })

            return {
                "success": True,
                "preview_mode": False,
                "playlist_name": orig_name,
                "created_playlists": created,
                "message": f"Successfully created {len(created)} sub-playlists from '{orig_name}'!"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


class PlaylistDeduplicateRequest(BaseModel):
    playlist_id: str
    strategy: str = "uri"
    dry_run: bool = False

@app.post("/api/playlist/deduplicate")
def deduplicate_playlist_endpoint(payload: PlaylistDeduplicateRequest):
    """Scans and strips duplicate tracks from a playlist."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        pid = _clean_playlist_id(payload.playlist_id)
        pl = user_client.playlist(pid, fields="name")
        p_name = pl.get("name", pid)

        items = []
        res = user_client.playlist_items(pid, limit=100)
        while res:
            items.extend(res.get("items", []))
            if res.get("next"):
                res = user_client.next(res)
            else:
                break

        seen = set()
        duplicates = []
        unique_uris = []

        for idx, it in enumerate(items, 1):
            t = it.get("track")
            if not t or not t.get("uri") or not t["uri"].startswith("spotify:track:"):
                continue
            if payload.strategy == "name_and_artist":
                tname = (t.get("name") or "").strip().lower()
                tart = ", ".join((a.get("name") or "").strip().lower() for a in t.get("artists", []))
                key = f"{tname}::{tart}"
            else:
                key = t.get("uri")

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

        if payload.dry_run:
            return {
                "success": True,
                "dry_run": True,
                "playlist_name": p_name,
                "total_tracks": len(items),
                "unique_tracks": len(unique_uris),
                "duplicate_count": len(duplicates),
                "duplicates": duplicates[:50]
            }
        else:
            if duplicates:
                user_client.playlist_replace_items(pid, unique_uris[:100])
                for i in range(100, len(unique_uris), 100):
                    user_client.playlist_add_items(pid, unique_uris[i:i+100])

            return {
                "success": True,
                "dry_run": False,
                "playlist_name": p_name,
                "duplicate_count": len(duplicates),
                "unique_tracks": len(unique_uris),
                "message": f"Successfully removed {len(duplicates)} duplicate tracks from '{p_name}'!" if duplicates else "No duplicates found. Playlist is clean!"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/playlist/export")
def export_playlist_endpoint(
    playlist_id: str = Query(...),
    include_audio_features: bool = Query(False)
):
    """Exports full playlist metadata and track details to JSON."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        pid = _clean_playlist_id(playlist_id)
        p = user_client.playlist(pid)

        items = []
        res = user_client.playlist_items(pid, limit=100)
        while res:
            items.extend(res.get("items", []))
            if res.get("next"):
                res = user_client.next(res)
            else:
                break

        tracks_data = []
        track_ids = []
        for idx, it in enumerate(items, 1):
            t = it.get("track")
            if not t: continue
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
            if tid: track_ids.append(tid)

        if include_audio_features and track_ids:
            features_map = {}
            for i in range(0, len(track_ids), 100):
                batch_ids = track_ids[i:i+100]
                try:
                    feat_res = user_client.audio_features(batch_ids)
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
        return {
            "success": True,
            "export": {
                "playlist": {
                    "id": p.get("id", pid),
                    "name": p.get("name"),
                    "description": p.get("description"),
                    "owner": owner.get("display_name"),
                    "followers": p.get("followers", {}).get("total", 0),
                    "public": p.get("public"),
                    "collaborative": p.get("collaborative"),
                    "cover_url": images[0].get("url") if images else None,
                    "spotify_url": p.get("external_urls", {}).get("spotify"),
                    "total_tracks": len(tracks_data)
                },
                "tracks": tracks_data
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


class PlaylistDiffRequest(BaseModel):
    playlist_id_a: str
    playlist_id_b: str
    strategy: str = "uri"

@app.post("/api/playlist/diff")
def diff_playlists_endpoint(payload: PlaylistDiffRequest):
    """Compares two playlists to find unique and shared tracks."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        pid_a = _clean_playlist_id(payload.playlist_id_a)
        pid_b = _clean_playlist_id(payload.playlist_id_b)

        p_a = user_client.playlist(pid_a, fields="name")
        p_b = user_client.playlist(pid_b, fields="name")

        def _fetch_tracks(pid):
            items = []
            res = user_client.playlist_items(pid, limit=100)
            while res:
                items.extend(res.get("items", []))
                if res.get("next"):
                    res = user_client.next(res)
                else:
                    break
            track_map = {}
            for it in items:
                t = it.get("track")
                if not t or not t.get("uri"): continue
                if payload.strategy == "name_and_artist":
                    tname = (t.get("name") or "").strip().lower()
                    tart = ", ".join((a.get("name") or "").strip().lower() for a in t.get("artists", []))
                    key = f"{tname}::{tart}"
                else:
                    key = t.get("uri")
                if key not in track_map:
                    track_map[key] = {
                        "name": t.get("name"),
                        "artist": ", ".join(a.get("name", "") for a in t.get("artists", [])),
                        "album": t.get("album", {}).get("name"),
                        "cover_url": t.get("album", {}).get("images", [{}])[0].get("url") if t.get("album", {}).get("images") else None,
                        "uri": t.get("uri")
                    }
            return track_map

        map_a = _fetch_tracks(pid_a)
        map_b = _fetch_tracks(pid_b)

        keys_a = set(map_a.keys())
        keys_b = set(map_b.keys())

        shared_keys = keys_a & keys_b
        only_a_keys = keys_a - keys_b
        only_b_keys = keys_b - keys_a
        union_keys = keys_a | keys_b

        similarity = (len(shared_keys) / len(union_keys) * 100) if union_keys else 0.0

        return {
            "success": True,
            "playlist_a": {"id": pid_a, "name": p_a.get("name", pid_a), "count": len(keys_a)},
            "playlist_b": {"id": pid_b, "name": p_b.get("name", pid_b), "count": len(keys_b)},
            "similarity_pct": round(similarity, 1),
            "shared_count": len(shared_keys),
            "only_a_count": len(only_a_keys),
            "only_b_count": len(only_b_keys),
            "shared_tracks": [map_a[k] for k in list(shared_keys)[:50]],
            "only_a_tracks": [map_a[k] for k in list(only_a_keys)[:50]],
            "only_b_tracks": [map_b[k] for k in list(only_b_keys)[:50]]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/playlist/overlaps")
def find_overlaps_endpoint(
    limit: int = Query(20, ge=2, le=50),
    min_overlap: int = Query(2, ge=1)
):
    """Scans user playlists to find overlapping track sets."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        res = user_client.current_user_playlists(limit=limit)
        items = res.get("items", [])
        if len(items) < 2:
            return {"success": False, "error": "Need at least 2 playlists to find overlaps."}

        playlists_data = []
        for p in items:
            pid = p["id"]
            p_items = []
            r = user_client.playlist_items(pid, limit=100)
            while r:
                p_items.extend(r.get("items", []))
                if r.get("next") and len(p_items) < 200:
                    r = user_client.next(r)
                else:
                    break
            uris = set()
            for it in p_items:
                t = it.get("track")
                if t and t.get("uri") and t["uri"].startswith("spotify:track:"):
                    uris.add(t["uri"])
            playlists_data.append({
                "id": pid,
                "name": p.get("name", pid),
                "uris": uris
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
                        "p1_id": p1["id"],
                        "p1_name": p1["name"],
                        "p1_len": len(p1["uris"]),
                        "p2_id": p2["id"],
                        "p2_name": p2["name"],
                        "p2_len": len(p2["uris"]),
                        "shared_count": len(shared),
                        "overlap_pct": round(overlap_pct, 1)
                    })

        overlap_pairs.sort(key=lambda x: x["shared_count"], reverse=True)
        return {
            "success": True,
            "scanned_count": len(playlists_data),
            "overlaps": overlap_pairs
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/playlist/subsets")
def find_subsets_endpoint(
    limit: int = Query(20, ge=2, le=50),
    threshold: float = Query(1.0, ge=0.5, le=1.0)
):
    """Detects if any playlists are complete or near-complete subsets of another."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        res = user_client.current_user_playlists(limit=limit)
        items = res.get("items", [])
        if len(items) < 2:
            return {"success": False, "error": "Need at least 2 playlists to check subsets."}

        playlists_data = []
        for p in items:
            pid = p["id"]
            p_items = []
            r = user_client.playlist_items(pid, limit=100)
            while r:
                p_items.extend(r.get("items", []))
                if r.get("next") and len(p_items) < 200:
                    r = user_client.next(r)
                else:
                    break
            uris = set()
            for it in p_items:
                t = it.get("track")
                if t and t.get("uri") and t["uri"].startswith("spotify:track:"):
                    uris.add(t["uri"])
            playlists_data.append({
                "id": pid,
                "name": p.get("name", pid),
                "uris": uris
            })

        subsets = []
        for i in range(len(playlists_data)):
            for j in range(len(playlists_data)):
                if i == j: continue
                p_sub = playlists_data[i]
                p_super = playlists_data[j]
                if not p_sub["uris"]: continue
                shared = p_sub["uris"] & p_super["uris"]
                ratio = len(shared) / len(p_sub["uris"])
                if ratio >= threshold:
                    subsets.append({
                        "sub_id": p_sub["id"],
                        "sub_name": p_sub["name"],
                        "sub_len": len(p_sub["uris"]),
                        "super_id": p_super["id"],
                        "super_name": p_super["name"],
                        "super_len": len(p_super["uris"]),
                        "shared_count": len(shared),
                        "ratio": round(ratio * 100, 1),
                        "is_complete": ratio >= 0.999
                    })

        subsets.sort(key=lambda x: (x["ratio"], -x["sub_len"]), reverse=True)
        return {
            "success": True,
            "scanned_count": len(playlists_data),
            "subsets": subsets
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


class PlaylistAbsorbRequest(BaseModel):
    source_playlist_id: str
    target_playlist_id: str
    strategy: str = "uri"

@app.post("/api/playlist/absorb")
def absorb_playlist_endpoint(payload: PlaylistAbsorbRequest):
    """Pulls only missing tracks from source playlist into destination playlist."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        src_id = _clean_playlist_id(payload.source_playlist_id)
        tgt_id = _clean_playlist_id(payload.target_playlist_id)

        p_src = user_client.playlist(src_id, fields="name")
        p_tgt = user_client.playlist(tgt_id, fields="name,external_urls")

        def _get_items(pid):
            items = []
            res = user_client.playlist_items(pid, limit=100)
            while res:
                items.extend(res.get("items", []))
                if res.get("next"):
                    res = user_client.next(res)
                else:
                    break
            return items

        src_items = _get_items(src_id)
        tgt_items = _get_items(tgt_id)

        existing_keys = set()
        for it in tgt_items:
            t = it.get("track")
            if not t or not t.get("uri"): continue
            if payload.strategy == "name_and_artist":
                tname = (t.get("name") or "").strip().lower()
                tart = ", ".join((a.get("name") or "").strip().lower() for a in t.get("artists", []))
                existing_keys.add(f"{tname}::{tart}")
            else:
                existing_keys.add(t.get("uri"))

        missing_uris = []
        skipped = 0
        for it in src_items:
            t = it.get("track")
            if not t or not t.get("uri") or not t["uri"].startswith("spotify:track:"):
                continue
            if payload.strategy == "name_and_artist":
                tname = (t.get("name") or "").strip().lower()
                tart = ", ".join((a.get("name") or "").strip().lower() for a in t.get("artists", []))
                k = f"{tname}::{tart}"
            else:
                k = t.get("uri")

            if k in existing_keys:
                skipped += 1
            else:
                existing_keys.add(k)
                missing_uris.append(t["uri"])

        if not missing_uris:
            return {
                "success": True,
                "absorbed_count": 0,
                "skipped_count": skipped,
                "message": f"Target playlist '{p_tgt.get('name')}' already contains all tracks from '{p_src.get('name')}'!"
            }

        for i in range(0, len(missing_uris), 100):
            user_client.playlist_add_items(tgt_id, missing_uris[i:i+100])

        return {
            "success": True,
            "absorbed_count": len(missing_uris),
            "skipped_count": skipped,
            "target_name": p_tgt.get("name"),
            "new_total": len(tgt_items) + len(missing_uris),
            "message": f"Successfully absorbed {len(missing_uris)} new tracks from '{p_src.get('name')}' into '{p_tgt.get('name')}'!"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


class QueueRequest(BaseModel):
    track_uri: Optional[str] = None
    track_uris: Optional[List[str]] = None
    device_id: Optional[str] = None


@app.post("/api/player/queue")
def queue_tracks(payload: QueueRequest):
    """Sends track(s) to the active Spotify playback queue."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {
            "success": False,
            "need_auth": True,
            "auth_url": oauth_manager.get_authorize_url(),
            "error": "Spotify authorization required. Click 'Connect Spotify' in the top right to link your account."
        }

    try:
        uris = []
        if payload.track_uris:
            uris.extend(payload.track_uris)
        if payload.track_uri:
            uris.append(payload.track_uri)

        valid_uris = [u for u in uris if u and (u.startswith("spotify:track:") or u.startswith("spotify:episode:"))]
        if not valid_uris:
            return {"success": False, "error": "No valid track URIs provided."}

        queued = 0
        errors = []
        for uri in valid_uris:
            try:
                user_client.add_to_queue(uri=uri, device_id=payload.device_id)
                queued += 1
            except spotipy.exceptions.SpotifyException as q_err:
                errors.append(str(q_err.msg or q_err))
            except Exception as q_err:
                errors.append(str(q_err))

        return {
            "success": queued > 0,
            "queued": queued,
            "total": len(valid_uris),
            "errors": errors[:2]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


class PlayRequest(BaseModel):
    track_uri: str

@app.post("/api/player/play")
def play_track(payload: PlayRequest):
    """Plays a specific track instantly on the active device."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {
            "success": False,
            "need_auth": True,
            "auth_url": oauth_manager.get_authorize_url(),
            "error": "Spotify authorization required to control playback."
        }
    try:
        # First ensure we have an active device or fallback device
        devices = user_client.devices().get('devices', [])
        fallback_id = None
        for d in devices:
            if d.get('is_active'):
                fallback_id = d.get('id')
                break
        if not fallback_id and devices:
            fallback_id = next((d.get('id') for d in devices if d.get('type') == 'Computer'), devices[0].get('id'))

        if not fallback_id:
            return {"success": False, "error": "No Spotify devices found. Please open the Spotify app."}

        try:
            # Add the track to the queue on the target device
            user_client.add_to_queue(payload.track_uri, device_id=fallback_id)
            # Skip to the newly queued track
            user_client.next_track(device_id=fallback_id)
            # Ensure it is actually playing (sometimes next_track leaves it paused)
            user_client.start_playback(device_id=fallback_id)
            return {"success": True}
        except spotipy.exceptions.SpotifyException as e:
            # If start_playback fails, it might already be playing. Ignore 403 on start_playback.
            if e.http_status == 403 or e.http_status == 404:
                return {"success": True}
            raise e
    except spotipy.exceptions.SpotifyException as e:
        return {"success": False, "error": f"Could not play track: {e.msg}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

class VolumeRequest(BaseModel):
    volume_percent: int
    device_id: Optional[str] = None

@app.post("/api/player/volume")
def set_volume_endpoint(payload: VolumeRequest):
    """Sets the volume on the active device."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        user_client.volume(payload.volume_percent, device_id=payload.device_id)
        return {"success": True, "volume": payload.volume_percent}
    except spotipy.exceptions.SpotifyException as e:
        return {"success": False, "error": str(e.msg)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/player/state")
def get_player_state():
    """Gets the current playback state with full metadata, shuffle, repeat, and active device."""
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        state = user_client.current_playback()
        user = None
        try:
            user = user_client.current_user()
        except Exception:
            pass

        if not state or not state.get("item"):
            return {
                "success": True,
                "is_playing": False,
                "track": None,
                "user": user.get("display_name") if user else None,
                "user_id": user.get("id") if user else None
            }
        
        item = state.get("item")
        device = state.get("device") or {}
        return {
            "success": True,
            "is_playing": state.get("is_playing", False),
            "shuffle_state": state.get("shuffle_state", False),
            "repeat_state": state.get("repeat_state", "off"),
            "progress_ms": state.get("progress_ms", 0),
            "duration_ms": item.get("duration_ms", 0),
            "device": {
                "id": device.get("id"),
                "name": device.get("name"),
                "type": device.get("type"),
                "is_active": device.get("is_active", True),
                "volume_percent": device.get("volume_percent")
            },
            "user": user.get("display_name") if user else None,
            "user_id": user.get("id") if user else None,
            "track": {
                "name": item.get("name"),
                "artist": ", ".join(a.get("name", "Unknown") for a in item.get("artists", [])),
                "album": item.get("album", {}).get("name"),
                "album_cover": item.get("album", {}).get("images", [{}])[0].get("url") if item.get("album", {}).get("images") else None,
                "uri": item.get("uri")
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/player/pause")
def pause_playback():
    user_client = _get_valid_user_client()
    if not user_client: return {"success": False}
    try:
        user_client.pause_playback()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/player/resume")
def resume_playback():
    user_client = _get_valid_user_client()
    if not user_client: return {"success": False}
    try:
        user_client.start_playback()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/player/next")
def next_track():
    user_client = _get_valid_user_client()
    if not user_client: return {"success": False}
    try:
        user_client.next_track()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

class SeekRequest(BaseModel):
    position_ms: int

@app.post("/api/player/seek")
def seek_track(payload: SeekRequest):
    user_client = _get_valid_user_client()
    if not user_client: return {"success": False, "need_auth": True}
    try:
        user_client.seek_track(payload.position_ms)
        return {"success": True}
    except spotipy.exceptions.SpotifyException as e:
        return {"success": False, "error": str(e.msg)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/player/previous")
def prev_track():
    user_client = _get_valid_user_client()
    if not user_client: return {"success": False}
    try:
        user_client.previous_track()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


class VolumeRequest(BaseModel):
    volume_percent: int
    device_id: Optional[str] = None

class RepeatRequest(BaseModel):
    state: str  # 'track', 'context', or 'off'
    device_id: Optional[str] = None

class ShuffleRequest(BaseModel):
    state: Optional[bool] = None
    device_id: Optional[str] = None

class TransferRequest(BaseModel):
    device_id: str
    play: bool = False

@app.get("/api/player/status")
def api_player_status():
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        user = user_client.current_user()
        playback = user_client.current_playback()
        return {
            "success": True,
            "user": user.get("display_name"),
            "user_id": user.get("id"),
            "playback": playback
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/player/devices")
def api_get_devices():
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "devices": []}
    try:
        devices = user_client.devices().get("devices", [])
        return {"success": True, "devices": devices}
    except Exception as e:
        return {"success": False, "error": str(e), "devices": []}

@app.get("/api/player/queue")
def api_get_queue():
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "queue": []}
    try:
        q = user_client.queue()
        return {"success": True, "currently_playing": q.get("currently_playing"), "queue": q.get("queue", [])}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/player/repeat")
def api_set_repeat(payload: RepeatRequest):
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        user_client.repeat(payload.state, device_id=payload.device_id)
        return {"success": True, "repeat": payload.state}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/player/shuffle")
def api_set_shuffle(payload: ShuffleRequest):
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        state = payload.state
        if state is None:
            pb = user_client.current_playback()
            state = not (pb.get("shuffle_state", False) if pb else False)
        user_client.shuffle(state, device_id=payload.device_id)
        return {"success": True, "shuffle": state}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/player/transfer")
def api_transfer_playback(payload: TransferRequest):
    user_client = _get_valid_user_client()
    if not user_client:
        return {"success": False, "need_auth": True}
    try:
        user_client.transfer_playback(payload.device_id, force_play=payload.play)
        return {"success": True, "device_id": payload.device_id}
    except Exception as e:
        return {"success": False, "error": str(e)}



def _clean_spotify_id(raw_id: str, id_type: str = "") -> str:
    val = (raw_id or "").strip()
    if "/" in val:
        val = val.split(f"/{id_type}/")[-1] if id_type and f"/{id_type}/" in val else val.split("/")[-1]
    if ":" in val:
        val = val.split(":")[-1]
    return val.split("?")[0].strip()


def _format_track_item(t: dict) -> dict:
    if not t:
        return {}
    album = t.get("album", {})
    artists = t.get("artists", [])
    artist_names = ", ".join([a.get("name", "") for a in artists]) or "Unknown"
    return {
        "id": t.get("id"),
        "name": t.get("name"),
        "artist": artist_names,
        "artist_ids": [a.get("id") for a in artists if a.get("id")],
        "album_name": album.get("name", ""),
        "album_cover": album.get("images", [{}])[0].get("url") if album.get("images") else None,
        "release_date": album.get("release_date", ""),
        "popularity": t.get("popularity", 0),
        "duration_ms": t.get("duration_ms", 0),
        "uri": t.get("uri"),
        "spotify_url": t.get("external_urls", {}).get("spotify"),
        "preview_url": t.get("preview_url")
    }


# ==============================================================================
# SEARCH, RECOMMENDATIONS & DISCOVERY ENDPOINTS
# ==============================================================================

@app.get("/api/spotify/search")
@app.get("/api/search/catalog")
def api_spotify_search(
    query: str = Query(..., description="Search query"),
    types: str = Query("track,artist,album,playlist", description="Comma-separated types: track,artist,album,playlist"),
    limit: int = Query(10, ge=1, le=50, description="Results limit per type"),
    market: Optional[str] = Query(None, description="ISO country code")
):
    """Search Spotify catalog for tracks, artists, albums, or playlists."""
    client = _get_valid_user_client() or public_sp
    if not client:
        return {"success": False, "error": "Spotify client not initialized"}
    try:
        resolved_types = [t.strip().lower() for t in types.split(",") if t.strip().lower() in ["track", "artist", "album", "playlist"]]
        if not resolved_types:
            resolved_types = ["track"]
        res = client.search(q=query, type=",".join(resolved_types), limit=limit, market=market)
        
        output = {"success": True, "query": query, "types": resolved_types}
        if "tracks" in res:
            output["tracks"] = [_format_track_item(t) for t in res["tracks"].get("items", []) if t]
        if "artists" in res:
            artists_list = []
            for a in res["artists"].get("items", []):
                if not a: continue
                artists_list.append({
                    "id": a.get("id"),
                    "name": a.get("name"),
                    "genres": a.get("genres", []),
                    "popularity": a.get("popularity", 0),
                    "followers": a.get("followers", {}).get("total", 0),
                    "image": a.get("images", [{}])[0].get("url") if a.get("images") else None,
                    "uri": a.get("uri"),
                    "spotify_url": a.get("external_urls", {}).get("spotify")
                })
            output["artists"] = artists_list
        if "albums" in res:
            albums_list = []
            for alb in res["albums"].get("items", []):
                if not alb: continue
                albums_list.append({
                    "id": alb.get("id"),
                    "name": alb.get("name"),
                    "artists": ", ".join(art.get("name", "") for art in alb.get("artists", [])),
                    "release_date": alb.get("release_date", ""),
                    "total_tracks": alb.get("total_tracks", 0),
                    "image": alb.get("images", [{}])[0].get("url") if alb.get("images") else None,
                    "uri": alb.get("uri"),
                    "spotify_url": alb.get("external_urls", {}).get("spotify")
                })
            output["albums"] = albums_list
        if "playlists" in res:
            playlists_list = []
            for p in res["playlists"].get("items", []):
                if not p: continue
                playlists_list.append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "owner": p.get("owner", {}).get("display_name", "Unknown"),
                    "total_tracks": p.get("tracks", {}).get("total", 0),
                    "image": p.get("images", [{}])[0].get("url") if p.get("images") else None,
                    "uri": p.get("uri"),
                    "spotify_url": p.get("external_urls", {}).get("spotify")
                })
            output["playlists"] = playlists_list
        return output
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/artist/related")
@app.get("/api/spotify/related_artists")
def api_related_artists(artist: str = Query(..., description="Artist name, ID, or URI")):
    """Find artists similar to a target artist."""
    client = _get_valid_user_client() or public_sp
    if not client:
        return {"success": False, "error": "Spotify client not initialized"}
    try:
        clean_id = _clean_spotify_id(artist, "artist")
        is_uri_or_id = artist.startswith("spotify:") or "spotify.com" in artist or len(clean_id) == 22
        if not is_uri_or_id:
            search_res = client.search(q=artist, type="artist", limit=1)
            items = search_res.get("artists", {}).get("items", [])
            if not items:
                return {"success": False, "error": f"Artist '{artist}' not found on Spotify."}
            target_artist = items[0]
            artist_id = target_artist.get("id", clean_id)
        else:
            target_artist = client.artist(clean_id)
            artist_id = target_artist.get("id", clean_id)
        
        related_data = client.artist_related_artists(artist_id)
        related_items = []
        for a in related_data.get("artists", []):
            if not a: continue
            related_items.append({
                "id": a.get("id"),
                "name": a.get("name"),
                "genres": a.get("genres", []),
                "popularity": a.get("popularity", 0),
                "followers": a.get("followers", {}).get("total", 0),
                "image": a.get("images", [{}])[0].get("url") if a.get("images") else None,
                "uri": a.get("uri"),
                "spotify_url": a.get("external_urls", {}).get("spotify")
            })
        
        return {
            "success": True,
            "artist": {
                "id": target_artist.get("id"),
                "name": target_artist.get("name"),
                "genres": target_artist.get("genres", []),
                "popularity": target_artist.get("popularity", 0),
                "followers": target_artist.get("followers", {}).get("total", 0),
                "image": target_artist.get("images", [{}])[0].get("url") if target_artist.get("images") else None,
                "uri": target_artist.get("uri")
            },
            "related_artists": related_items
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/discover/by_artist")
def api_discover_by_artist(
    artist: str = Query(..., description="Artist name, ID, or URI"),
    limit: int = Query(15, ge=1, le=50),
    include_artist_top_tracks: bool = Query(True)
):
    """Generate track recommendations derived from related artist networks."""
    client = _get_valid_user_client() or public_sp
    if not client:
        return {"success": False, "error": "Spotify client not initialized"}
    try:
        clean_id = _clean_spotify_id(artist, "artist")
        is_uri_or_id = artist.startswith("spotify:") or "spotify.com" in artist or (len(clean_id) == 22 and " " not in clean_id)
        if not is_uri_or_id:
            search_res = client.search(q=artist, type="artist", limit=1)
            items = search_res.get("artists", {}).get("items", [])
            if not items:
                return {"success": False, "error": f"Artist '{artist}' not found on Spotify."}
            seed_artist = items[0]
            artist_id = seed_artist.get("id", clean_id)
        else:
            seed_artist = client.artist(clean_id)
            artist_id = seed_artist.get("id", clean_id)
        
        artist_name = seed_artist.get("name", artist)
        related_res = client.artist_related_artists(artist_id)
        related_artists = related_res.get("artists", [])
        
        seed_pool = [artist_id]
        related_seeds = []
        for a in related_artists[:4]:
            if a.get("id"):
                seed_pool.append(a["id"])
                related_seeds.append({"id": a["id"], "name": a.get("name")})
            
        recs = client.recommendations(seed_artists=seed_pool[:5], limit=limit)
        rec_tracks = [_format_track_item(t) for t in recs.get("tracks", []) if t]
        
        top_tracks = []
        if include_artist_top_tracks:
            top_res = client.artist_top_tracks(artist_id)
            top_tracks = [_format_track_item(t) for t in top_res.get("tracks", [])[:5] if t]
            
        return {
            "success": True,
            "seed_artist": {
                "id": seed_artist.get("id"),
                "name": seed_artist.get("name"),
                "image": seed_artist.get("images", [{}])[0].get("url") if seed_artist.get("images") else None,
                "genres": seed_artist.get("genres", [])
            },
            "related_seeds": related_seeds,
            "tracks": rec_tracks,
            "top_tracks": top_tracks
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


class MoodDiscoveryRequest(BaseModel):
    mood: Optional[str] = None
    seed_genres: Optional[Union[List[str], str]] = None
    target_valence: Optional[float] = None
    target_energy: Optional[float] = None
    target_danceability: Optional[float] = None
    target_acousticness: Optional[float] = None
    target_tempo: Optional[float] = None
    limit: int = 20


def _handle_discover_by_mood(
    mood: Optional[str] = None,
    seed_genres: Optional[List[str]] = None,
    target_valence: Optional[float] = None,
    target_energy: Optional[float] = None,
    target_danceability: Optional[float] = None,
    target_acousticness: Optional[float] = None,
    target_tempo: Optional[float] = None,
    limit: int = 20
):
    client = _get_valid_user_client() or public_sp
    if not client:
        return {"success": False, "error": "Spotify client not initialized"}
    try:
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
        results = client.recommendations(seed_genres=genres[:5], limit=rec_limit, **kwargs)
        tracks = [_format_track_item(trk) for trk in results.get("tracks", []) if trk]

        return {
            "success": True,
            "mood": mood or "custom",
            "seed_genres": genres[:5],
            "applied_targets": kwargs,
            "tracks": tracks
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/discover/by_mood")
def api_discover_by_mood_post(payload: MoodDiscoveryRequest):
    """Discover tracks using target audio parameters or mood presets (POST)."""
    return _handle_discover_by_mood(
        mood=payload.mood,
        seed_genres=payload.seed_genres,
        target_valence=payload.target_valence,
        target_energy=payload.target_energy,
        target_danceability=payload.target_danceability,
        target_acousticness=payload.target_acousticness,
        target_tempo=payload.target_tempo,
        limit=payload.limit
    )


@app.get("/api/discover/by_mood")
def api_discover_by_mood_get(
    mood: Optional[str] = Query(None),
    seed_genres: Optional[str] = Query(None),
    target_valence: Optional[float] = Query(None),
    target_energy: Optional[float] = Query(None),
    target_danceability: Optional[float] = Query(None),
    target_acousticness: Optional[float] = Query(None),
    target_tempo: Optional[float] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """Discover tracks using target audio parameters or mood presets (GET)."""
    genres = [g.strip() for g in seed_genres.split(",") if g.strip()] if seed_genres else None
    return _handle_discover_by_mood(
        mood=mood,
        seed_genres=genres,
        target_valence=target_valence,
        target_energy=target_energy,
        target_danceability=target_danceability,
        target_acousticness=target_acousticness,
        target_tempo=target_tempo,
        limit=limit
    )


@app.get("/api/genres/explore")
def api_genre_explorer(
    genres: Optional[str] = Query(None, description="Comma-separated genres"),
    limit: int = Query(15, ge=1, le=50),
    market: Optional[str] = Query(None)
):
    """Browse and sample tracks across specific seed genres or list all available genre seeds."""
    client = _get_valid_user_client() or public_sp
    if not client:
        return {"success": False, "error": "Spotify client not initialized"}
    try:
        available_genres = client.recommendation_genre_seeds().get("genres", [])
        
        selected = []
        if genres:
            selected = [g.strip().lower() for g in genres.split(",") if g.strip()]
            
        tracks = []
        if selected:
            rec_limit = max(1, min(limit, 50))
            results = client.recommendations(seed_genres=selected[:5], limit=rec_limit, market=market)
            tracks = [_format_track_item(t) for t in results.get("tracks", []) if t]
            
        return {
            "success": True,
            "all_genres": available_genres,
            "selected_genres": selected[:5],
            "tracks": tracks
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/discover/deep_cuts")
def api_discover_deep_cuts(
    artist_or_album: str = Query(..., description="Artist or album name, ID, or URI"),
    max_popularity: int = Query(40, ge=0, le=100),
    limit: int = Query(15, ge=1, le=50)
):
    """Discover non-single, album-only deep cut tracks from an artist or album."""
    client = _get_valid_user_client() or public_sp
    if not client:
        return {"success": False, "error": "Spotify client not initialized"}
    try:
        clean_input = artist_or_album.strip()
        limit = max(1, min(limit, 50))

        artist_res = client.search(q=clean_input, type="artist", limit=1)
        artist_items = artist_res.get("artists", {}).get("items", [])

        deep_cuts = []
        target_name = clean_input
        target_image = None

        if artist_items:
            artist = artist_items[0]
            artist_id = artist.get("id", clean_input)
            target_name = artist.get("name", clean_input)
            target_image = artist.get("images", [{}])[0].get("url") if artist.get("images") else None

            top_tracks_res = client.artist_top_tracks(artist_id)
            top_track_uris = {t["uri"] for t in top_tracks_res.get("tracks", [])}

            albums_res = client.artist_albums(artist_id, album_type="album", limit=8)
            albums = albums_res.get("items", [])

            track_ids = []
            track_album_map = {}

            for alb in albums:
                alb_id = alb.get("id")
                if not alb_id:
                    continue
                alb_tracks = client.album_tracks(alb_id, limit=30).get("items", [])
                for t in alb_tracks:
                    if t.get("uri") not in top_track_uris and t.get("id"):
                        track_ids.append(t["id"])
                        track_album_map[t["id"]] = alb.get("name", "Album")

            for i in range(0, min(len(track_ids), 100), 50):
                batch = track_ids[i:i + 50]
                detailed_tracks = client.tracks(batch).get("tracks", [])
                for dt in detailed_tracks:
                    if dt and dt.get("popularity", 100) <= max_popularity:
                        item = _format_track_item(dt)
                        if item:
                            item["album_name"] = track_album_map.get(dt.get("id"), item.get("album_name"))
                            deep_cuts.append(item)
        else:
            album_res = client.search(q=clean_input, type="album", limit=1)
            alb_items = album_res.get("albums", {}).get("items", [])
            if not alb_items:
                return {"success": False, "error": f"Could not find artist or album '{artist_or_album}' on Spotify."}
            alb = alb_items[0]
            target_name = alb.get("name", clean_input)
            target_image = alb.get("images", [{}])[0].get("url") if alb.get("images") else None
            alb_tracks = client.album_tracks(alb.get("id", clean_input), limit=50).get("items", [])
            t_ids = [t["id"] for t in alb_tracks if t.get("id")]
            if t_ids:
                detailed = client.tracks(t_ids[:50]).get("tracks", [])
                for dt in detailed:
                    if dt and dt.get("popularity", 100) <= max_popularity:
                        item = _format_track_item(dt)
                        if item:
                            item["album_name"] = alb.get("name")
                            deep_cuts.append(item)

        deep_cuts.sort(key=lambda x: x.get("popularity", 0))
        selected_cuts = deep_cuts[:limit]

        return {
            "success": True,
            "target_name": target_name,
            "target_image": target_image,
            "max_popularity": max_popularity,
            "total_found": len(selected_cuts),
            "tracks": selected_cuts
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


class RecommendationsRequest(BaseModel):
    limit: int = 20
    seed_tracks: Optional[List[str]] = None
    seed_artists: Optional[List[str]] = None
    seed_genres: Optional[List[str]] = None
    target_energy: Optional[float] = None
    target_valence: Optional[float] = None
    target_danceability: Optional[float] = None
    target_acousticness: Optional[float] = None
    target_instrumentalness: Optional[float] = None
    target_tempo: Optional[float] = None
    min_popularity: Optional[int] = None
    max_popularity: Optional[int] = None
    market: Optional[str] = None


@app.post("/api/recommendations")
def api_get_recommendations(payload: RecommendationsRequest):
    """Direct wrapper for Spotify Recommendations API using seeds and target audio features (POST)."""
    client = _get_valid_user_client() or public_sp
    if not client:
        return {"success": False, "error": "Spotify credentials not configured", "recommendations": [], "tracks": []}
    
    try:
        kwargs = {}
        if payload.target_energy is not None: kwargs["target_energy"] = max(0.0, min(1.0, float(payload.target_energy)))
        if payload.target_valence is not None: kwargs["target_valence"] = max(0.0, min(1.0, float(payload.target_valence)))
        if payload.target_danceability is not None: kwargs["target_danceability"] = max(0.0, min(1.0, float(payload.target_danceability)))
        if payload.target_acousticness is not None: kwargs["target_acousticness"] = max(0.0, min(1.0, float(payload.target_acousticness)))
        if payload.target_instrumentalness is not None: kwargs["target_instrumentalness"] = max(0.0, min(1.0, float(payload.target_instrumentalness)))
        if payload.target_tempo is not None: kwargs["target_tempo"] = float(payload.target_tempo)
        if payload.min_popularity is not None: kwargs["min_popularity"] = max(0, min(100, int(payload.min_popularity)))
        if payload.max_popularity is not None: kwargs["max_popularity"] = max(0, min(100, int(payload.max_popularity)))
        
        seed_tracks = [_clean_spotify_id(t, "track") for t in (payload.seed_tracks or []) if t]
        seed_artists = [_clean_spotify_id(a, "artist") for a in (payload.seed_artists or []) if a]
        seed_genres = [g.strip().lower() for g in (payload.seed_genres or []) if g]
        
        num_seeds = len(seed_tracks) + len(seed_artists) + len(seed_genres)
        if num_seeds == 0:
            seed_genres = ["pop"]
            num_seeds = 1
            
        if num_seeds > 5:
            total = [("track", t) for t in seed_tracks] + [("artist", a) for a in seed_artists] + [("genre", g) for g in seed_genres]
            total = total[:5]
            seed_tracks = [item[1] for item in total if item[0] == "track"]
            seed_artists = [item[1] for item in total if item[0] == "artist"]
            seed_genres = [item[1] for item in total if item[0] == "genre"]

        results = client.recommendations(
            seed_tracks=seed_tracks or None,
            seed_artists=seed_artists or None,
            seed_genres=seed_genres or None,
            limit=max(1, min(payload.limit, 100)),
            market=payload.market,
            **kwargs
        )
        
        formatted = [_format_track_item(t) for t in results.get("tracks", []) if t]
        return {
            "success": True,
            "recommendations": formatted,
            "tracks": formatted,
            "seeds": {
                "tracks": seed_tracks,
                "artists": seed_artists,
                "genres": seed_genres
            }
        }
    except spotipy.exceptions.SpotifyException as e:
        return {"success": False, "error": str(e.msg), "recommendations": [], "tracks": []}
    except Exception as e:
        return {"success": False, "error": str(e), "recommendations": [], "tracks": []}


@app.get("/api/recommendations")
def api_get_recommendations_get(
    seed_tracks: Optional[str] = Query(None, description="Comma-separated track IDs/URIs"),
    seed_artists: Optional[str] = Query(None, description="Comma-separated artist IDs/URIs"),
    seed_genres: Optional[str] = Query(None, description="Comma-separated genres"),
    target_energy: Optional[float] = Query(None),
    target_valence: Optional[float] = Query(None),
    target_danceability: Optional[float] = Query(None),
    target_acousticness: Optional[float] = Query(None),
    target_instrumentalness: Optional[float] = Query(None),
    target_tempo: Optional[float] = Query(None),
    min_popularity: Optional[int] = Query(None),
    max_popularity: Optional[int] = Query(None),
    market: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """Direct wrapper for Spotify Recommendations API using seeds and target audio features (GET)."""
    t_seeds = [t.strip() for t in seed_tracks.split(",") if t.strip()] if seed_tracks else None
    a_seeds = [a.strip() for a in seed_artists.split(",") if a.strip()] if seed_artists else None
    g_seeds = [g.strip() for g in seed_genres.split(",") if g.strip()] if seed_genres else None
    req = RecommendationsRequest(
        limit=limit,
        seed_tracks=t_seeds,
        seed_artists=a_seeds,
        seed_genres=g_seeds,
        target_energy=target_energy,
        target_valence=target_valence,
        target_danceability=target_danceability,
        target_acousticness=target_acousticness,
        target_instrumentalness=target_instrumentalness,
        target_tempo=target_tempo,
        min_popularity=min_popularity,
        max_popularity=max_popularity,
        market=market
    )
    return api_get_recommendations(req)


# ==============================================================================
# STATS, ANALYTICS & INSIGHTS ENDPOINTS
# ==============================================================================

@app.get("/api/stats/top_tracks")
def api_get_top_tracks(
    time_range: str = Query("medium_term", description="short_term (4 weeks), medium_term (6 months), long_term (all time)"),
    limit: int = Query(20, ge=1, le=50)
):
    """Fetch user's top tracks over short, medium, or long term."""
    client = _get_valid_user_client()
    if not client:
        return {"success": False, "error": "Not authenticated with Spotify. Please connect your account.", "tracks": []}
    try:
        valid_ranges = ["short_term", "medium_term", "long_term"]
        if time_range not in valid_ranges:
            time_range = "medium_term"
        
        limit = max(1, min(limit, 50))
        results = client.current_user_top_tracks(limit=limit, time_range=time_range)
        items = results.get("items", [])
        
        tracks = []
        for rank, t in enumerate(items, 1):
            if not t:
                continue
            item = _format_track_item(t)
            item["rank"] = rank
            dur_ms = t.get("duration_ms", 0)
            sec = dur_ms // 1000
            item["duration"] = f"{sec // 60}:{sec % 60:02d}"
            tracks.append(item)
            
        return {
            "success": True,
            "time_range": time_range,
            "count": len(tracks),
            "tracks": tracks
        }
    except Exception as e:
        return {"success": False, "error": str(e), "tracks": []}


@app.get("/api/stats/top_artists")
def api_get_top_artists(
    time_range: str = Query("medium_term", description="short_term, medium_term, long_term"),
    limit: int = Query(20, ge=1, le=50)
):
    """Fetch user's top artists over short, medium, or long term."""
    client = _get_valid_user_client()
    if not client:
        return {"success": False, "error": "Not authenticated with Spotify. Please connect your account.", "artists": []}
    try:
        valid_ranges = ["short_term", "medium_term", "long_term"]
        if time_range not in valid_ranges:
            time_range = "medium_term"
            
        limit = max(1, min(limit, 50))
        results = client.current_user_top_artists(limit=limit, time_range=time_range)
        items = results.get("items", [])
        
        artists = []
        for rank, a in enumerate(items, 1):
            if not a:
                continue
            artists.append({
                "rank": rank,
                "id": a.get("id"),
                "name": a.get("name"),
                "genres": a.get("genres", []),
                "popularity": a.get("popularity", 0),
                "followers": a.get("followers", {}).get("total", 0),
                "image": a.get("images", [{}])[0].get("url") if a.get("images") else None,
                "uri": a.get("uri"),
                "spotify_url": a.get("external_urls", {}).get("spotify")
            })
            
        return {
            "success": True,
            "time_range": time_range,
            "count": len(artists),
            "artists": artists
        }
    except Exception as e:
        return {"success": False, "error": str(e), "artists": []}


@app.get("/api/stats/recently_played")
def api_get_recently_played(
    limit: int = Query(50, ge=1, le=50)
):
    """Fetch recent track listening history."""
    client = _get_valid_user_client()
    if not client:
        return {"success": False, "error": "Not authenticated with Spotify. Please connect your account.", "history": []}
    try:
        limit = max(1, min(limit, 50))
        results = client.current_user_recently_played(limit=limit)
        raw_items = results.get("items", [])
        
        history = []
        for item in raw_items:
            t = item.get("track")
            if not t:
                continue
            played_at_iso = item.get("played_at", "")
            played_at_fmt = played_at_iso
            try:
                dt = datetime.fromisoformat(played_at_iso.replace("Z", "+00:00"))
                played_at_fmt = dt.strftime("%Y-%m-%d %H:%M UTC")
            except Exception:
                pass
                
            formatted_track = _format_track_item(t)
            dur_ms = t.get("duration_ms", 0)
            sec = dur_ms // 1000
            formatted_track["duration"] = f"{sec // 60}:{sec % 60:02d}"
            formatted_track["played_at"] = played_at_iso
            formatted_track["played_at_formatted"] = played_at_fmt
            history.append(formatted_track)
            
        return {
            "success": True,
            "count": len(history),
            "history": history
        }
    except Exception as e:
        return {"success": False, "error": str(e), "history": []}


@app.get("/api/stats/listening_patterns")
def api_get_listening_patterns(
    limit: int = Query(50, ge=10, le=50)
):
    """Analyze listening volume distributions across hours and days."""
    client = _get_valid_user_client()
    if not client:
        return {"success": False, "error": "Not authenticated with Spotify. Please connect your account."}
    try:
        limit = max(10, min(limit, 50))
        results = client.current_user_recently_played(limit=limit)
        items = results.get("items", [])
        if not items:
            return {"success": False, "error": "No recent playback history found to analyze patterns."}
            
        hour_counts = {h: 0 for h in range(24)}
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_counts = {d: 0 for d in day_names}
        track_counts = Counter()
        
        for item in items:
            played_at = item.get("played_at")
            t = item.get("track")
            if t and t.get("name"):
                artists = ", ".join(a.get("name", "") for a in t.get("artists", []))
                track_counts[f"{t['name']} — {artists}"] += 1
            if played_at:
                try:
                    dt = datetime.fromisoformat(played_at.replace("Z", "+00:00"))
                    hour_counts[dt.hour] += 1
                    day_counts[day_names[dt.weekday()]] += 1
                except Exception:
                    pass
                    
        peak_hour = max(hour_counts.items(), key=lambda x: x[1])
        peak_day = max(day_counts.items(), key=lambda x: x[1])
        top_repeated = [{"track": name, "plays": count} for name, count in track_counts.most_common(5) if count > 1]
        
        return {
            "success": True,
            "total_samples": len(items),
            "peak_hour": f"{peak_hour[0]:02d}:00 UTC ({peak_hour[1]} plays)",
            "peak_day": f"{peak_day[0]} ({peak_day[1]} plays)",
            "hourly_distribution": [{"hour": h, "label": f"{h:02d}:00", "plays": hour_counts[h]} for h in range(24)],
            "daily_distribution": [{"day": d, "plays": day_counts[d]} for d in day_names],
            "top_repeated_tracks": top_repeated
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/stats/taste_profile")
def api_get_taste_profile(
    time_range: str = Query("medium_term", description="short_term, medium_term, long_term")
):
    """Generate an overview of genre diversity and niche artist affinity."""
    client = _get_valid_user_client()
    if not client:
        return {"success": False, "error": "Not authenticated with Spotify. Please connect your account."}
    try:
        artists_res = client.current_user_top_artists(limit=50, time_range=time_range)
        artists = artists_res.get("items", [])
        
        genre_counter = Counter()
        popularities = []
        niche_artists = []
        mainstream_artists = []
        
        for a in artists:
            if not a:
                continue
            pops = a.get("popularity", 50)
            popularities.append(pops)
            for g in a.get("genres", []):
                genre_counter[g] += 1
            if pops < 45:
                niche_artists.append({"name": a.get("name"), "popularity": pops, "genres": a.get("genres", [])[:2]})
            elif pops >= 75:
                mainstream_artists.append({"name": a.get("name"), "popularity": pops, "genres": a.get("genres", [])[:2]})
                
        avg_pop = sum(popularities) / max(1, len(popularities))
        obscurity_score = round(100 - avg_pop, 1)
        
        # Determine archetype
        if obscurity_score >= 60:
            archetype = "Underground Explorer"
            description = "You actively explore indie, emerging, and niche artists off the beaten path."
        elif obscurity_score <= 35:
            archetype = "Mainstream Trendsetter"
            description = "You enjoy high-energy top charts, global pop hits, and iconic superstars."
        else:
            archetype = "Eclectic Connoisseur"
            description = "You strike a balanced equilibrium between chart-toppers and underground gems."
            
        top_genres = [{"genre": g, "count": c} for g, c in genre_counter.most_common(10)]
        
        return {
            "success": True,
            "time_range": time_range,
            "artists_analyzed": len(artists),
            "archetype": archetype,
            "description": description,
            "obscurity_score": obscurity_score,
            "average_popularity": round(avg_pop, 1),
            "top_genres": top_genres,
            "niche_artists": niche_artists[:6],
            "mainstream_artists": mainstream_artists[:6]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


class PlaylistCompareRequest(BaseModel):
    playlist_ids: List[str]


@app.post("/api/playlist/compare")
def api_compare_playlists(payload: PlaylistCompareRequest):
    """Compare multi-playlist audio feature distributions side-by-side (POST)."""
    client = _get_valid_user_client() or public_sp
    if not client:
        return {"success": False, "error": "Spotify credentials not configured"}
    try:
        pids = [_clean_spotify_id(pid, "playlist") for pid in (payload.playlist_ids or []) if pid]
        if len(pids) < 2:
            return {"success": False, "error": "Please provide at least 2 playlists to compare."}
            
        comparison = []
        for pid in pids[:5]:  # limit to max 5 for performance
            try:
                p_meta = client.playlist(pid, fields="id,name,description,images,owner.display_name,tracks.total")
            except Exception:
                continue
                
            p_name = p_meta.get("name", "Unknown Playlist")
            total_tracks = p_meta.get("tracks", {}).get("total", 0)
            image = p_meta.get("images", [{}])[0].get("url") if p_meta.get("images") else None
            owner = p_meta.get("owner", {}).get("display_name", "")
            
            items_res = client.playlist_items(pid, limit=100, fields="items(track(id,duration_ms,explicit,popularity))")
            items = items_res.get("items", [])
            
            track_ids = []
            durations = []
            popularities = []
            explicit_count = 0
            
            for it in items:
                t = it.get("track")
                if t and t.get("id"):
                    track_ids.append(t["id"])
                    if t.get("duration_ms"):
                        durations.append(t["duration_ms"])
                    if t.get("popularity") is not None:
                        popularities.append(t["popularity"])
                    if t.get("explicit"):
                        explicit_count += 1
                        
            # Audio features
            features = []
            if track_ids:
                for chunk_start in range(0, min(len(track_ids), 100), 50):
                    chunk = track_ids[chunk_start:chunk_start + 50]
                    feats = client.audio_features(chunk)
                    features.extend([f for f in feats if f])
                    
            def _avg(attr):
                vals = [f[attr] for f in features if f and f.get(attr) is not None]
                return round(sum(vals) / len(vals), 3) if vals else 0.0
                
            avg_energy = _avg("energy")
            avg_valence = _avg("valence")
            avg_dance = _avg("danceability")
            avg_acoustic = _avg("acousticness")
            avg_instrumental = _avg("instrumentalness")
            avg_tempo = round(_avg("tempo"), 1)
            avg_pop = round(sum(popularities) / len(popularities), 1) if popularities else 0.0
            avg_duration_sec = (sum(durations) // len(durations) // 1000) if durations else 0
            
            comparison.append({
                "id": pid,
                "name": p_name,
                "owner": owner,
                "image": image,
                "total_tracks": total_tracks,
                "analyzed_tracks": len(features),
                "avg_energy": avg_energy,
                "avg_valence": avg_valence,
                "avg_danceability": avg_dance,
                "avg_acousticness": avg_acoustic,
                "avg_instrumentalness": avg_instrumental,
                "avg_tempo": avg_tempo,
                "avg_popularity": avg_pop,
                "avg_duration": f"{avg_duration_sec // 60}:{avg_duration_sec % 60:02d}",
                "explicit_percentage": round((explicit_count / max(1, len(track_ids))) * 100, 1)
            })
            
        return {
            "success": True,
            "count": len(comparison),
            "comparison": comparison
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/playlist/compare")
def api_compare_playlists_get(
    playlist_ids: str = Query(..., description="Comma-separated playlist IDs/URIs")
):
    """Compare multi-playlist audio feature distributions side-by-side (GET)."""
    p_ids = [p.strip() for p in playlist_ids.split(",") if p.strip()]
    return api_compare_playlists(PlaylistCompareRequest(playlist_ids=p_ids))


@app.get("/api/playlist/freshness")
def api_get_playlist_freshness(
    limit: int = Query(25, ge=1, le=50),
    stale_days_threshold: int = Query(60, ge=7)
):
    """Sort playlists by last update timestamp to identify stale lists."""
    client = _get_valid_user_client()
    if not client:
        return {"success": False, "error": "Not authenticated with Spotify. Please connect your account."}
    try:
        limit = max(1, min(limit, 50))
        pl_res = client.current_user_playlists(limit=limit)
        playlists = pl_res.get("items", [])
        
        now = datetime.now(timezone.utc)
        analyzed = []
        
        for p in playlists:
            if not p:
                continue
            pid = p.get("id")
            pname = p.get("name", "Untitled")
            total = p.get("tracks", {}).get("total", 0)
            image = p.get("images", [{}])[0].get("url") if p.get("images") else None
            
            if total == 0:
                analyzed.append({
                    "id": pid,
                    "name": pname,
                    "image": image,
                    "total": 0,
                    "days": 9999,
                    "last_updated": "Never (Empty)",
                    "status": "🔴 Empty"
                })
                continue
                
            offset = max(0, total - 1)
            last_item_res = client.playlist_items(pid, limit=1, offset=offset, fields="items(added_at)")
            last_items = last_item_res.get("items", [])
            
            if last_items and last_items[0].get("added_at"):
                added_at_str = last_items[0]["added_at"]
                try:
                    dt = datetime.fromisoformat(added_at_str.replace("Z", "+00:00"))
                    days_ago = (now - dt).days
                    if days_ago < 30:
                        status = "🟢 Fresh"
                    elif days_ago <= stale_days_threshold:
                        status = "🟡 Aging"
                    else:
                        status = "🔴 Stale"
                    analyzed.append({
                        "id": pid,
                        "name": pname,
                        "image": image,
                        "total": total,
                        "days": days_ago,
                        "last_updated": f"{days_ago} days ago ({added_at_str[:10]})",
                        "status": status
                    })
                except Exception:
                    analyzed.append({
                        "id": pid, "name": pname, "image": image, "total": total, "days": 0, "last_updated": "Unknown", "status": "⚪ Active"
                    })
            else:
                analyzed.append({
                    "id": pid, "name": pname, "image": image, "total": total, "days": 0, "last_updated": "Unknown", "status": "⚪ Active"
                })
                
        analyzed.sort(key=lambda x: x["days"], reverse=True)
        stale_count = sum(1 for a in analyzed if "🔴" in a["status"])
        aging_count = sum(1 for a in analyzed if "🟡" in a["status"])
        fresh_count = sum(1 for a in analyzed if "🟢" in a["status"])
        
        return {
            "success": True,
            "total_inspected": len(analyzed),
            "fresh_count": fresh_count,
            "aging_count": aging_count,
            "stale_count": stale_count,
            "playlists": analyzed
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==============================================================================
# LIBRARY & SAVED MEDIA (LIKED SONGS & ALBUMS) ENDPOINTS
# ==============================================================================

class SaveTracksPayload(BaseModel):
    track_ids: List[str]


class RemoveTracksPayload(BaseModel):
    track_ids: List[str]


class CheckTracksPayload(BaseModel):
    track_ids: List[str]


class SaveAlbumsPayload(BaseModel):
    album_ids: List[str]


class RemoveAlbumsPayload(BaseModel):
    album_ids: List[str]


class CheckAlbumsPayload(BaseModel):
    album_ids: List[str]


@app.get("/api/library/tracks")
def api_get_saved_tracks(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    market: Optional[str] = Query(None)
):
    """List tracks saved in the current user's Liked Songs library."""
    client = _get_valid_user_client()
    if not client:
        return {"success": False, "error": "Not authenticated with Spotify. Please connect your account.", "tracks": []}
    try:
        limit = max(1, min(limit, 50))
        offset = max(0, offset)
        results = client.current_user_saved_tracks(limit=limit, offset=offset, market=market)
        items = results.get("items", [])
        total = results.get("total", len(items))

        tracks = []
        for idx, it in enumerate(items, offset + 1):
            t = it.get("track", {})
            if not t:
                continue
            item = _format_track_item(t)
            item["rank"] = idx
            item["added_at"] = it.get("added_at", "")
            dur_ms = t.get("duration_ms", 0)
            sec = dur_ms // 1000
            item["duration"] = f"{sec // 60}:{sec % 60:02d}"
            tracks.append(item)

        return {
            "success": True,
            "total": total,
            "offset": offset,
            "count": len(tracks),
            "tracks": tracks
        }
    except Exception as e:
        return {"success": False, "error": str(e), "tracks": []}


@app.post("/api/library/tracks")
def api_save_tracks(payload: SaveTracksPayload):
    """Save one or more tracks to the current user's Liked Songs library."""
    client = _get_valid_user_client()
    if not client:
        return {"success": False, "error": "Not authenticated with Spotify. Please connect your account."}
    try:
        cleaned = [_clean_spotify_id(t, "track") for t in (payload.track_ids or []) if t]
        if not cleaned:
            return {"success": False, "error": "No valid track IDs provided."}

        for i in range(0, len(cleaned), 50):
            batch = cleaned[i:i + 50]
            client.current_user_saved_tracks_add(tracks=batch)

        return {
            "success": True,
            "message": f"Successfully saved {len(cleaned)} track(s) to Liked Songs.",
            "saved_count": len(cleaned),
            "track_ids": cleaned
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.delete("/api/library/tracks")
def api_remove_saved_tracks(payload: RemoveTracksPayload):
    """Remove one or more tracks from the current user's Liked Songs library."""
    client = _get_valid_user_client()
    if not client:
        return {"success": False, "error": "Not authenticated with Spotify. Please connect your account."}
    try:
        cleaned = [_clean_spotify_id(t, "track") for t in (payload.track_ids or []) if t]
        if not cleaned:
            return {"success": False, "error": "No valid track IDs provided."}

        for i in range(0, len(cleaned), 50):
            batch = cleaned[i:i + 50]
            client.current_user_saved_tracks_delete(tracks=batch)

        return {
            "success": True,
            "message": f"Successfully removed {len(cleaned)} track(s) from Liked Songs.",
            "removed_count": len(cleaned),
            "track_ids": cleaned
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/library/tracks/check")
def api_check_saved_tracks_get(
    track_ids: str = Query(..., description="Comma-separated track IDs or URIs")
):
    """Verify whether specific tracks exist in the current user's Liked Songs (GET)."""
    t_ids = [t.strip() for t in track_ids.split(",") if t.strip()]
    return api_check_saved_tracks(CheckTracksPayload(track_ids=t_ids))


@app.post("/api/library/tracks/check")
def api_check_saved_tracks(payload: CheckTracksPayload):
    """Verify whether specific tracks exist in the current user's Liked Songs (POST)."""
    client = _get_valid_user_client()
    if not client:
        return {"success": False, "error": "Not authenticated with Spotify. Please connect your account."}
    try:
        cleaned = [_clean_spotify_id(t, "track") for t in (payload.track_ids or []) if t]
        if not cleaned:
            return {"success": False, "error": "No valid track IDs provided."}

        cleaned = cleaned[:50]
        results = client.current_user_saved_tracks_contains(tracks=cleaned)

        status_list = []
        for tid, is_saved in zip(cleaned, results):
            status_list.append({
                "track_id": tid,
                "is_saved": bool(is_saved),
                "status": "Liked" if is_saved else "Not Liked"
            })

        return {
            "success": True,
            "count": len(status_list),
            "results": status_list
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/library/albums")
def api_get_saved_albums(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    market: Optional[str] = Query(None)
):
    """Fetch albums saved in the current user's library."""
    client = _get_valid_user_client()
    if not client:
        return {"success": False, "error": "Not authenticated with Spotify. Please connect your account.", "albums": []}
    try:
        limit = max(1, min(limit, 50))
        offset = max(0, offset)
        results = client.current_user_saved_albums(limit=limit, offset=offset, market=market)
        items = results.get("items", [])
        total = results.get("total", len(items))

        albums = []
        for idx, it in enumerate(items, offset + 1):
            alb = it.get("album", {})
            if not alb:
                continue
            artists = ", ".join(a.get("name", "Unknown") for a in alb.get("artists", []))
            albums.append({
                "rank": idx,
                "id": alb.get("id"),
                "name": alb.get("name"),
                "artists": artists,
                "release_date": alb.get("release_date", ""),
                "total_tracks": alb.get("total_tracks", 0),
                "popularity": alb.get("popularity", 0),
                "image": alb.get("images", [{}])[0].get("url") if alb.get("images") else None,
                "uri": alb.get("uri"),
                "spotify_url": alb.get("external_urls", {}).get("spotify"),
                "added_at": it.get("added_at", "")
            })

        return {
            "success": True,
            "total": total,
            "offset": offset,
            "count": len(albums),
            "albums": albums
        }
    except Exception as e:
        return {"success": False, "error": str(e), "albums": []}


@app.post("/api/library/albums")
def api_save_albums(payload: SaveAlbumsPayload):
    """Save one or more albums to the current user's library."""
    client = _get_valid_user_client()
    if not client:
        return {"success": False, "error": "Not authenticated with Spotify. Please connect your account."}
    try:
        cleaned = [_clean_spotify_id(a, "album") for a in (payload.album_ids or []) if a]
        if not cleaned:
            return {"success": False, "error": "No valid album IDs provided."}

        for i in range(0, len(cleaned), 50):
            batch = cleaned[i:i + 50]
            client.current_user_saved_albums_add(albums=batch)

        return {
            "success": True,
            "message": f"Successfully saved {len(cleaned)} album(s) to your library.",
            "saved_count": len(cleaned),
            "album_ids": cleaned
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.delete("/api/library/albums")
def api_remove_saved_albums(payload: RemoveAlbumsPayload):
    """Remove one or more albums from the current user's library."""
    client = _get_valid_user_client()
    if not client:
        return {"success": False, "error": "Not authenticated with Spotify. Please connect your account."}
    try:
        cleaned = [_clean_spotify_id(a, "album") for a in (payload.album_ids or []) if a]
        if not cleaned:
            return {"success": False, "error": "No valid album IDs provided."}

        for i in range(0, len(cleaned), 50):
            batch = cleaned[i:i + 50]
            client.current_user_saved_albums_delete(albums=batch)

        return {
            "success": True,
            "message": f"Successfully removed {len(cleaned)} album(s) from your library.",
            "removed_count": len(cleaned),
            "album_ids": cleaned
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/library/albums/check")
def api_check_saved_albums_get(
    album_ids: str = Query(..., description="Comma-separated album IDs or URIs")
):
    """Verify whether specific albums exist in the current user's library (GET)."""
    a_ids = [a.strip() for a in album_ids.split(",") if a.strip()]
    return api_check_saved_albums(CheckAlbumsPayload(album_ids=a_ids))


@app.post("/api/library/albums/check")
def api_check_saved_albums(payload: CheckAlbumsPayload):
    """Verify whether specific albums exist in the current user's library (POST)."""
    client = _get_valid_user_client()
    if not client:
        return {"success": False, "error": "Not authenticated with Spotify. Please connect your account."}
    try:
        cleaned = [_clean_spotify_id(a, "album") for a in (payload.album_ids or []) if a]
        if not cleaned:
            return {"success": False, "error": "No valid album IDs provided."}

        cleaned = cleaned[:50]
        results = client.current_user_saved_albums_contains(albums=cleaned)

        status_list = []
        for aid, is_saved in zip(cleaned, results):
            status_list.append({
                "album_id": aid,
                "is_saved": bool(is_saved),
                "status": "Saved in Library" if is_saved else "Not in Library"
            })

        return {
            "success": True,
            "count": len(status_list),
            "results": status_list
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==============================================================================
# CATALOG & ENTITY INSPECTION (BROWSE) ENDPOINTS
# ==============================================================================

@app.get("/api/browse/track")
def api_browse_track(
    track_id: str = Query(..., description="Spotify track ID, URI, or title"),
    market: Optional[str] = Query(None)
):
    """Inspect full track metadata including ISRC, popularity, preview URL, and album details."""
    client = _get_valid_user_client() or public_sp
    if not client:
        return {"success": False, "error": "Spotify credentials not configured."}
    try:
        clean_id = _clean_spotify_id(track_id, "track")
        if not clean_id or len(clean_id) != 22 and not track_id.startswith("spotify:track:"):
            search_res = client.search(q=track_id, type="track", limit=1)
            items = search_res.get("tracks", {}).get("items", [])
            if not items:
                return {"success": False, "error": f"Track '{track_id}' not found."}
            t = items[0]
        else:
            t = client.track(clean_id, market=market)

        if not t:
            return {"success": False, "error": f"Track '{track_id}' not found."}

        dur_ms = t.get("duration_ms", 0)
        sec = dur_ms // 1000
        ext_ids = t.get("external_ids", {})
        album = t.get("album", {})

        track_data = {
            "id": t.get("id"),
            "name": t.get("name"),
            "artists": ", ".join(a.get("name", "Unknown") for a in t.get("artists", [])),
            "artist_list": [{"id": a.get("id"), "name": a.get("name"), "uri": a.get("uri")} for a in t.get("artists", [])],
            "album_name": album.get("name", "Unknown Album"),
            "album_id": album.get("id"),
            "album_cover": album.get("images", [{}])[0].get("url") if album.get("images") else None,
            "release_date": album.get("release_date", ""),
            "duration_ms": dur_ms,
            "duration": f"{sec // 60}:{sec % 60:02d}",
            "popularity": t.get("popularity", 0),
            "explicit": bool(t.get("explicit")),
            "track_number": t.get("track_number", 1),
            "disc_number": t.get("disc_number", 1),
            "isrc": ext_ids.get("isrc", ""),
            "ean": ext_ids.get("ean", ""),
            "upc": ext_ids.get("upc", ""),
            "preview_url": t.get("preview_url"),
            "uri": t.get("uri"),
            "spotify_url": t.get("external_urls", {}).get("spotify", "")
        }

        return {
            "success": True,
            "track": track_data
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/browse/album")
def api_browse_album(
    album_id: str = Query(..., description="Spotify album ID, URI, or title"),
    market: Optional[str] = Query(None)
):
    """Inspect album details, label, copyright, and tracklist."""
    client = _get_valid_user_client() or public_sp
    if not client:
        return {"success": False, "error": "Spotify credentials not configured."}
    try:
        clean_id = _clean_spotify_id(album_id, "album")
        if not clean_id or len(clean_id) != 22 and not album_id.startswith("spotify:album:"):
            search_res = client.search(q=album_id, type="album", limit=1)
            items = search_res.get("albums", {}).get("items", [])
            if not items:
                return {"success": False, "error": f"Album '{album_id}' not found."}
            alb = client.album(items[0]["id"], market=market)
        else:
            alb = client.album(clean_id, market=market)

        if not alb:
            return {"success": False, "error": f"Album '{album_id}' not found."}

        artists = ", ".join(a.get("name", "Unknown") for a in alb.get("artists", []))
        tracks_raw = alb.get("tracks", {}).get("items", [])
        tracklist = []
        for t in tracks_raw:
            dur_ms = t.get("duration_ms", 0)
            sec = dur_ms // 1000
            tracklist.append({
                "track_number": t.get("track_number", 1),
                "id": t.get("id"),
                "name": t.get("name"),
                "artists": ", ".join(a.get("name", "") for a in t.get("artists", [])),
                "duration": f"{sec // 60}:{sec % 60:02d}",
                "duration_ms": dur_ms,
                "explicit": bool(t.get("explicit")),
                "preview_url": t.get("preview_url"),
                "uri": t.get("uri")
            })

        album_data = {
            "id": alb.get("id"),
            "name": alb.get("name"),
            "artists": artists,
            "artist_list": [{"id": a.get("id"), "name": a.get("name"), "uri": a.get("uri")} for a in alb.get("artists", [])],
            "release_date": alb.get("release_date", ""),
            "total_tracks": alb.get("total_tracks", len(tracklist)),
            "label": alb.get("label", ""),
            "copyrights": [c.get("text", "") for c in alb.get("copyrights", [])],
            "popularity": alb.get("popularity", 0),
            "genres": alb.get("genres", []),
            "image": alb.get("images", [{}])[0].get("url") if alb.get("images") else None,
            "uri": alb.get("uri"),
            "spotify_url": alb.get("external_urls", {}).get("spotify", ""),
            "tracks": tracklist
        }

        return {
            "success": True,
            "album": album_data
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/browse/artist")
def api_browse_artist(
    artist_id: str = Query(..., description="Spotify artist ID, URI, or artist name")
):
    """Inspect artist details including genres, followers, and popularity."""
    client = _get_valid_user_client() or public_sp
    if not client:
        return {"success": False, "error": "Spotify credentials not configured."}
    try:
        clean_id = _clean_spotify_id(artist_id, "artist")
        if not clean_id or len(clean_id) != 22 and not artist_id.startswith("spotify:artist:"):
            search_res = client.search(q=artist_id, type="artist", limit=1)
            items = search_res.get("artists", {}).get("items", [])
            if not items:
                return {"success": False, "error": f"Artist '{artist_id}' not found."}
            a = items[0]
        else:
            a = client.artist(clean_id)

        if not a:
            return {"success": False, "error": f"Artist '{artist_id}' not found."}

        artist_data = {
            "id": a.get("id"),
            "name": a.get("name"),
            "genres": a.get("genres", []),
            "followers": a.get("followers", {}).get("total", 0),
            "popularity": a.get("popularity", 0),
            "image": a.get("images", [{}])[0].get("url") if a.get("images") else None,
            "uri": a.get("uri"),
            "spotify_url": a.get("external_urls", {}).get("spotify", "")
        }

        return {
            "success": True,
            "artist": artist_data
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/browse/artist/albums")
def api_browse_artist_albums(
    artist_id: str = Query(..., description="Spotify artist ID, URI, or name"),
    include_groups: Optional[str] = Query("album,single", description="album,single,appears_on,compilation"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    country: Optional[str] = Query(None)
):
    """Get all albums, singles, and compilations by an artist."""
    client = _get_valid_user_client() or public_sp
    if not client:
        return {"success": False, "error": "Spotify credentials not configured."}
    try:
        clean_id = _clean_spotify_id(artist_id, "artist")
        artist_name = artist_id

        if not clean_id or len(clean_id) != 22 and not artist_id.startswith("spotify:artist:"):
            search_res = client.search(q=artist_id, type="artist", limit=1)
            items = search_res.get("artists", {}).get("items", [])
            if not items:
                return {"success": False, "error": f"Artist '{artist_id}' not found."}
            clean_id = items[0]["id"]
            artist_name = items[0].get("name", artist_id)
        else:
            try:
                artist_meta = client.artist(clean_id)
                artist_name = artist_meta.get("name", artist_id)
            except Exception:
                pass

        limit = max(1, min(limit, 50))
        offset = max(0, offset)
        groups = include_groups or "album,single"

        results = client.artist_albums(clean_id, include_groups=groups, limit=limit, offset=offset, country=country)
        items = results.get("items", [])
        total = results.get("total", len(items))

        albums = []
        for alb in items:
            albums.append({
                "id": alb.get("id"),
                "name": alb.get("name"),
                "group": alb.get("album_group", alb.get("album_type", "album")).upper(),
                "release_date": alb.get("release_date", ""),
                "total_tracks": alb.get("total_tracks", 0),
                "image": alb.get("images", [{}])[0].get("url") if alb.get("images") else None,
                "uri": alb.get("uri"),
                "spotify_url": alb.get("external_urls", {}).get("spotify", "")
            })

        return {
            "success": True,
            "artist_id": clean_id,
            "artist_name": artist_name,
            "total": total,
            "offset": offset,
            "count": len(albums),
            "albums": albums
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/browse/user")
def api_browse_user(
    user_id: str = Query(..., description="Spotify user ID or URI")
):
    """Fetch public profile information and public playlists for any user."""
    client = _get_valid_user_client() or public_sp
    if not client:
        return {"success": False, "error": "Spotify credentials not configured."}
    try:
        clean_id = _clean_spotify_id(user_id, "user")
        if not clean_id:
            return {"success": False, "error": "User ID required."}

        u = client.user(clean_id)
        if not u:
            return {"success": False, "error": f"User '{clean_id}' not found."}

        display_name = u.get("display_name") or clean_id
        followers = u.get("followers", {}).get("total", 0)
        spotify_url = u.get("external_urls", {}).get("spotify", "")
        images = u.get("images", [])
        image_url = images[0].get("url") if images else None

        playlists = []
        try:
            pl_res = client.user_playlists(clean_id, limit=20)
            for p in pl_res.get("items", []):
                playlists.append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "total_tracks": p.get("tracks", {}).get("total", 0),
                    "image": p.get("images", [{}])[0].get("url") if p.get("images") else None,
                    "uri": p.get("uri"),
                    "spotify_url": p.get("external_urls", {}).get("spotify", "")
                })
        except Exception:
            pass

        return {
            "success": True,
            "user": {
                "id": clean_id,
                "display_name": display_name,
                "followers": followers,
                "image": image_url,
                "spotify_url": spotify_url,
                "public_playlists": playlists
            },
            "public_playlists": playlists
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# -------------------------------------------------------------
# Additional Tool Endpoints (Bridging all tools to Python API)
# -------------------------------------------------------------

class CreateActorPlaylistRequest(BaseModel):
    actor_name: str
    playlist_name: Optional[str] = None
    max_movies: Optional[int] = 10
    max_songs_per_movie: Optional[int] = 3
    specific_movies: Optional[str] = None
    sort_by: Optional[str] = "popularity"
    public: Optional[bool] = True

class AddMovieSongsRequest(BaseModel):
    playlist_id: str
    movie_name: str
    max_songs: Optional[int] = 5

class ReorderFeaturesRequest(BaseModel):
    playlist_id: str
    feature: Optional[str] = "energy"
    ascending: Optional[bool] = False
    order: Optional[str] = None

class AudioFeaturesPayload(BaseModel):
    track_ids: List[str]

@app.post("/api/playlist/create_actor")
def create_actor_playlist_endpoint(payload: CreateActorPlaylistRequest):
    """End-to-End Pipeline: Discover an actor's filmography, find songs on Spotify, and create a playlist."""
    try:
        from tools import playlists as tool_playlists
        result = tool_playlists.create_actor_playlist(
            actor_name=payload.actor_name,
            playlist_name=payload.playlist_name,
            max_movies=payload.max_movies or 10,
            max_songs_per_movie=payload.max_songs_per_movie or 3,
            specific_movies=payload.specific_movies,
            sort_by=payload.sort_by or "popularity",
            public=True if payload.public is None else payload.public
        )
        is_success = not result.startswith("Error") and not result.startswith("Could not")
        return {"success": is_success, "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/playlist/add_movie_songs")
def add_movie_songs_endpoint(payload: AddMovieSongsRequest):
    """Search Spotify for soundtrack songs from a movie and append them to an existing playlist."""
    try:
        from tools import playlists as tool_playlists
        result = tool_playlists.add_movie_songs_to_playlist(
            playlist_id=payload.playlist_id,
            movie_name=payload.movie_name,
            max_songs=payload.max_songs or 5
        )
        is_success = not result.startswith("Error") and not result.startswith("No songs")
        return {"success": is_success, "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/playlist/reorder_by_features")
def reorder_by_features_endpoint(payload: ReorderFeaturesRequest):
    """Reorder a playlist based on audio features (energy, valence, danceability, tempo)."""
    try:
        from tools import playlists as tool_playlists
        sort_order = "asc" if payload.ascending or (payload.order and payload.order.lower() in ("asc", "ascending")) else (payload.order or "desc")
        result = tool_playlists.reorder_playlist_by_audio_features(
            playlist_id=payload.playlist_id,
            feature=payload.feature or "energy",
            order=sort_order
        )
        is_success = not result.startswith("Error") and not result.startswith("Cannot")
        return {"success": is_success, "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/actor/profile")
def get_actor_profile_endpoint(actor_name: str = Query(..., description="Name of the actor")):
    """Get rich biographical and career profile details for an actor from TMDB."""
    try:
        from tools import search as tool_search, tmdb_helpers
        result_text = tool_search.get_actor_tmdb_profile(actor_name)
        person = tmdb_helpers.tmdb_search_person(actor_name)
        profile_data = None
        if person:
            profile_data = tmdb_helpers.tmdb_get_person_profile(person["id"]) or person
        return {
            "success": "not found" not in result_text.lower() and "error" not in result_text.lower(),
            "summary": result_text,
            "profile": profile_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search/duckduckgo")
def search_duckduckgo_endpoint(query: str = Query(..., description="Query to search"), max_results: int = Query(5, ge=1, le=20)):
    """Perform a web search using DuckDuckGo."""
    try:
        from tools import tmdb_helpers, search as tool_search
        results = tmdb_helpers.ddg_web_search(query, max_results=max_results)
        text_summary = tool_search.search_duckduckgo(query, max_results=max_results)
        return {
            "success": True,
            "query": query,
            "results": results,
            "summary": text_summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tracks/audio_features")
def get_audio_features_endpoint(track_ids: str = Query(..., description="Comma-separated track IDs or URIs")):
    """Get Spotify audio features (danceability, energy, valence, tempo, etc.) for tracks."""
    client = _get_valid_user_client() or public_sp
    ids = [_clean_spotify_id(tid) for tid in track_ids.split(",") if tid.strip()]
    if not ids:
        return {"success": False, "features": []}
    try:
        if client:
            features = client.audio_features(ids)
            features = [f for f in features if f]
            return {"success": True, "features": features}
        else:
            from tools import taste as tool_taste
            res = tool_taste.get_audio_features(ids)
            return {"success": True, "features_summary": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tracks/audio_features")
def post_audio_features_endpoint(payload: AudioFeaturesPayload):
    """Get Spotify audio features for tracks via POST."""
    client = _get_valid_user_client() or public_sp
    ids = [_clean_spotify_id(tid) for tid in payload.track_ids if tid.strip()]
    if not ids:
        return {"success": False, "features": []}
    try:
        if client:
            features = client.audio_features(ids)
            features = [f for f in features if f]
            return {"success": True, "features": features}
        else:
            from tools import taste as tool_taste
            res = tool_taste.get_audio_features(ids)
            return {"success": True, "features_summary": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/artist/network")
def get_artist_network_endpoint(artist: str = Query(..., description="Target artist name or URI")):
    """Map the network of related artists and genre overlaps."""
    client = _get_valid_user_client() or public_sp
    try:
        from tools import taste as tool_taste
        summary = tool_taste.get_artist_network(artist)
        
        network_nodes = []
        if client:
            clean_id = _clean_spotify_id(artist)
            art_obj = None
            if len(clean_id) == 22 and not " " in clean_id:
                try:
                    art_obj = client.artist(clean_id)
                except Exception:
                    pass
            if not art_obj:
                sr = client.search(q=artist, type="artist", limit=1)
                items = sr.get("artists", {}).get("items", [])
                if items:
                    art_obj = items[0]
            if art_obj:
                rel = client.artist_related_artists(art_obj["id"]).get("artists", [])
                network_nodes = [{
                    "id": a["id"],
                    "name": a["name"],
                    "popularity": a.get("popularity", 0),
                    "genres": a.get("genres", []),
                    "followers": a.get("followers", {}).get("total", 0),
                    "images": a.get("images", [{}])
                } for a in rel]
                
        return {
            "success": True,
            "artist": artist,
            "summary": summary,
            "related_artists": network_nodes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/guide", response_class=HTMLResponse)
@app.get("/tools-guide", response_class=HTMLResponse)
def serve_guide():
    """Serves the tools guide & architecture documentation page."""
    template_path = BASE_DIR / "templates" / "guide.html"
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/tools", response_class=HTMLResponse)
def serve_tools():
    """Serves the new tools (shuffle, dedupe, combine) frontend page."""
    template_path = BASE_DIR / "templates" / "tools.html"
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    template_path = BASE_DIR / "templates" / "index.html"
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    import threading
    import time
    import webbrowser
    import uvicorn

    def open_browser():
        time.sleep(1.2)
        webbrowser.open("http://127.0.0.1:8000")

    threading.Thread(target=open_browser, daemon=True).start()
    print("\n" + "=" * 55)
    print(" Soundtrack Curator Studio is RUNNING!")
    print(" Open your browser at: http://127.0.0.1:8000")
    print(" Press CTRL+C to stop the server.")
    print("=" * 55 + "\n")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)

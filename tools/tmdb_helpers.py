from typing import Optional, List, Dict, Any
import requests
import os
import urllib.parse
from bs4 import BeautifulSoup
from tools.core import get_spotify_client, TMDB_BASE_URL
import spotipy
import re

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

def tmdb_get_credentials() -> tuple[Optional[str], Optional[str]]:
    """Resolve TMDB token or API key from environment variables.
    
    Accepts either TMDB_API_KEY or TMDB_READ_ACCESS_TOKEN (any single one is sufficient).
    Automatically detects whether a credential is a v4 Read Access Token (Bearer JWT)
    or a standard v3 API key (hex string).
    """
    token = (os.getenv("TMDB_READ_ACCESS_TOKEN") or "").strip()
    api_key = (os.getenv("TMDB_API_KEY") or "").strip()

    # Filter out empty or placeholder values
    if "your_" in token:
        token = ""
    if "your_" in api_key:
        api_key = ""

    bearer_token = None
    v3_key = None

    for val in (token, api_key):
        if not val:
            continue
        # Bearer tokens are long JWT tokens (typically >40 chars, often start with 'eyJ')
        if len(val) > 40 or val.startswith("eyJ"):
            if not bearer_token:
                bearer_token = val
        else:
            if not v3_key:
                v3_key = val

    return bearer_token, v3_key


def tmdb_get_auth_headers() -> Dict[str, str]:
    """Return authorization headers for TMDB API."""
    bearer_token, _ = tmdb_get_credentials()
    headers = {"accept": "application/json"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    return headers


def tmdb_get_auth_params() -> Dict[str, str]:
    """Return query params if API key is used for authentication."""
    bearer_token, v3_key = tmdb_get_credentials()
    params: Dict[str, str] = {}
    if not bearer_token and v3_key:
        params["api_key"] = v3_key
    return params


def tmdb_search_person(actor_name: str) -> Optional[Dict[str, Any]]:
    """Search TMDB for a person by name and return top matching person details."""
    headers = tmdb_get_auth_headers()
    params = tmdb_get_auth_params()
    
    import re
    clean_name = actor_name.lower()
    for word in ["kannada", "telugu", "tamil", "hindi", "malayalam", "english", "bollywood", "tollywood", "kollywood", "sandalwood", "actor", "actress", "singer", "director"]:
        clean_name = re.sub(rf"\b{word}\b", "", clean_name)
    clean_name = clean_name.strip() or actor_name

    params.update({"query": clean_name, "include_adult": "false", "language": "en-US", "page": "1"})

    try:
        resp = requests.get(f"{TMDB_BASE_URL}/search/person", headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                # Prioritize acting department if available
                acting_matches = [r for r in results if r.get("known_for_department") == "Acting"]
                return acting_matches[0] if acting_matches else results[0]
    except Exception:
        pass
    return None


def tmdb_get_actor_movie_credits(person_id: int, sort_by: str = "popularity") -> List[Dict[str, Any]]:
    """Fetch movie credits for an actor from TMDB.
    
    Args:
        person_id: TMDB person ID
        sort_by: 'popularity' or 'release_date'
    """
    headers = tmdb_get_auth_headers()
    params = tmdb_get_auth_params()
    params.update({"language": "en-US"})

    try:
        resp = requests.get(f"{TMDB_BASE_URL}/person/{person_id}/movie_credits", headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            cast_entries = data.get("cast", [])

            # Filter valid movie titles and deduplicate
            unique_movies: Dict[int, Dict[str, Any]] = {}
            for entry in cast_entries:
                movie_id = entry.get("id")
                title = entry.get("title") or entry.get("original_title")
                if movie_id and title and movie_id not in unique_movies:
                    unique_movies[movie_id] = {
                        "id": movie_id,
                        "title": title,
                        "character": entry.get("character", ""),
                        "release_date": entry.get("release_date", ""),
                        "popularity": entry.get("popularity", 0.0),
                        "vote_average": entry.get("vote_average", 0.0),
                        "vote_count": entry.get("vote_count", 0),
                        "overview": entry.get("overview", "")
                    }

            movie_list = list(unique_movies.values())
            if sort_by == "release_date":
                movie_list.sort(key=lambda m: m["release_date"] or "0000", reverse=True)
            else:
                movie_list.sort(key=lambda m: m["popularity"] or 0.0, reverse=True)

            return movie_list
    except Exception:
        pass
    return []


def tmdb_search_movie_details(movie_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search TMDB for movies matching a name."""
    headers = tmdb_get_auth_headers()
    params = tmdb_get_auth_params()
    params.update({"query": movie_name, "include_adult": "false", "language": "en-US", "page": "1"})

    try:
        resp = requests.get(f"{TMDB_BASE_URL}/search/movie", headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            return results[:limit]
    except Exception:
        pass
    return []


def tmdb_get_person_profile(person_id: int) -> Optional[Dict[str, Any]]:
    """Get full biographical details for a person from TMDB."""
    headers = tmdb_get_auth_headers()
    params = tmdb_get_auth_params()
    params.update({"language": "en-US"})

    try:
        resp = requests.get(f"{TMDB_BASE_URL}/person/{person_id}", headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def ddg_web_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Execute a web search using DuckDuckGo and return list of result items."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", ""),
                    "href": r.get("href", ""),
                    "body": r.get("body", "")
                }
                for r in results
            ]
    except Exception:
        return []


def ddg_find_soundtrack_songs(movie_name: str, max_songs: int = 5) -> List[str]:
    """Search DuckDuckGo to extract known soundtrack song titles for a movie.
    
    Helps discover regional or non-standard soundtrack track names to search on Spotify.
    """
    song_titles: List[str] = []
    queries = [
        f'"{movie_name}" soundtrack tracklist songs',
        f'"{movie_name}" movie songs list',
    ]

    for q in queries:
        results = ddg_web_search(q, max_results=3)
        for item in results:
            text = f"{item['title']} {item['body']}"
            # Match quotes or track listings e.g. "Song Name", 1. Song Name
            quoted = re.findall(r'["“]([^"”]{3,40})["”]', text)
            for s in quoted:
                clean = s.strip()
                if (
                    clean
                    and clean.lower() not in [movie_name.lower(), "soundtrack", "ost", "theme", "original soundtrack"]
                    and not clean.lower().startswith("http")
                ):
                    if clean not in song_titles:
                        song_titles.append(clean)

            # Match numbered lines e.g. "1. Song Name" or "1 - Song Name"
            numbered = re.findall(r'(?:^|\n|\. )\d+[\.\-]\s*([A-Za-z0-9\s\',-]{3,40})', text)
            for s in numbered:
                clean = s.strip()
                if clean and clean not in song_titles and len(clean) > 3:
                    song_titles.append(clean)

            if len(song_titles) >= max_songs:
                break
        if len(song_titles) >= max_songs:
            break

    return song_titles[:max_songs]


def scrape_actor_movies_from_web(actor_name: str) -> List[str]:
    """Search Wikipedia to extract the filmography for an actor as a tertiary fallback."""
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    urls = []
    queries = [
        f"{actor_name} filmography",
        actor_name
    ]

    for q in queries:
        try:
            encoded_query = urllib.parse.quote(q)
            api_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={encoded_query}&limit=5&format=json"
            resp = s.get(api_url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) > 3 and data[3]:
                    for u in data[3]:
                        if "filmography" in u.lower():
                            urls.insert(0, u)
                        else:
                            urls.append(u)
                    if urls:
                        break
        except Exception:
            continue

    if not urls:
        return []

    movies: List[str] = []
    excluded_keywords = {
        "title", "film", "role", "notes", "year", "director", "ref", "awards",
        "work", "character", "episodes", "episode", "season", "soundtrack", "album"
    }

    for target_url in urls[:2]:
        try:
            page_resp = s.get(target_url, timeout=10)
            if page_resp.status_code != 200:
                continue
            soup = BeautifulSoup(page_resp.text, "html.parser")

            for table in soup.find_all("table", class_="wikitable"):
                for row in table.find_all("tr"):
                    for i_tag in row.find_all("i"):
                        text = i_tag.get_text().strip()
                        if text and len(text) > 1 and not text.isdigit():
                            if text.lower() not in excluded_keywords:
                                movies.append(text)
            if movies:
                break
        except Exception:
            continue

    seen = set()
    unique_movies: List[str] = []
    for m in movies:
        norm = m.lower()
        if norm not in seen:
            seen.add(norm)
            unique_movies.append(m)

    return unique_movies


def get_actor_filmography(actor_name: str, limit: int = 30, sort_by: str = "popularity") -> Dict[str, Any]:
    """Retrieve an actor's filmography using a multi-tiered strategy:
    1. TMDB (Primary - high accuracy, characters, release dates)
    2. DuckDuckGo Search (Secondary - handles regional / unindexed names)
    3. Wikipedia Scraper (Tertiary)
    """
    # Tier 1: TMDB
    tmdb_person = tmdb_search_person(actor_name)
    if tmdb_person:
        person_id = tmdb_person["id"]
        credits = tmdb_get_actor_movie_credits(person_id, sort_by=sort_by)
        if credits:
            return {
                "source": "TMDB",
                "actor_name": tmdb_person.get("name", actor_name),
                "person_id": person_id,
                "profile_path": tmdb_person.get("profile_path", ""),
                "popularity": tmdb_person.get("popularity", 0.0),
                "movies": credits[:limit]
            }

    # Tier 2: Wikipedia Scraper
    wiki_movies = scrape_actor_movies_from_web(actor_name)
    if wiki_movies:
        return {
            "source": "Wikipedia",
            "actor_name": actor_name,
            "person_id": None,
            "profile_path": "",
            "popularity": 0.0,
            "movies": [{"title": m, "release_date": "", "character": ""} for m in wiki_movies[:limit]]
        }

    # Tier 3: DuckDuckGo Search
    ddg_results = ddg_web_search(f"{actor_name} filmography movies list", max_results=5)
    extracted: List[str] = []
    for r in ddg_results:
        snippets = f"{r['title']} {r['body']}"
        quoted = re.findall(r'["“]([^"”]{3,40})["”]', snippets)
        for q in quoted:
            if q.lower() not in extracted and q.lower() not in [actor_name.lower(), "filmography"]:
                extracted.append(q)

    if extracted:
        return {
            "source": "DuckDuckGo",
            "actor_name": actor_name,
            "person_id": None,
            "profile_path": "",
            "popularity": 0.0,
            "movies": [{"title": m, "release_date": "", "character": ""} for m in extracted[:limit]]
        }

    return {
        "source": "None",
        "actor_name": actor_name,
        "person_id": None,
        "profile_path": "",
        "popularity": 0.0,
        "movies": []
    }


_LANGUAGE_WORDS = {
    "kannada", "telugu", "tamil", "malayalam", "hindi", "english",
    "bengali", "marathi", "punjabi", "gujarati", "odia",
}
_SOUNDTRACK_NOISE = re.compile(
    r"\b(original motion picture soundtrack|original background score|motion picture soundtrack|"
    r"original soundtrack|music from the motion picture|background score|soundtrack|jukebox|ost|bgm)\b"
)
_FROM_MOVIE = re.compile(r'from\s+(?:the\s+)?(?:motion picture\s+|movie\s+|film\s+)?["“]([^"”]+)["”]', re.I)
_SPOTIFY_LINK = re.compile(r"open\.spotify\.com/(?:intl-[a-z-]+/)?(album|track)/([A-Za-z0-9]{22})")
_SCORE_ONLY = re.compile(r"background score|\bbgm\b|trailer|teaser|instrumental", re.I)


def _normalize_title(text: str) -> str:
    text = re.sub(r"[^\w\s]", " ", text.lower().replace("&", " and "))
    return " ".join(w for w in text.split() if w not in _LANGUAGE_WORDS)


def soundtrack_title_matches(movie_name: str, spotify_name: str, allow_plain: bool = True,
                             language: Optional[str] = None) -> bool:
    """Strictly check whether a Spotify album/track name belongs to `movie_name`.

    Understands names like 'Song (From "Movie")' and 'Movie (Original Motion Picture
    Soundtrack) [Telugu]'. With allow_plain=False only the 'From "Movie"' form counts,
    which is what track names need (a song merely titled 'Happy' is not from the movie).
    A name tagged with a different language than `language` is rejected (dubbed versions).
    """
    import difflib

    if language:
        words = set(re.sub(r"[^\w\s]", " ", spotify_name.lower()).split())
        lang = language.lower()
        if lang not in words and words & (_LANGUAGE_WORDS - {lang}):
            return False

    candidates = _FROM_MOVIE.findall(spotify_name)
    if allow_plain:
        candidates.append(re.sub(r"[\(\[][^\)\]]*[\)\]]", " ", spotify_name))

    movie = _normalize_title(movie_name)
    movie_solid = movie.replace(" ", "")
    if not movie_solid:
        return False
    for candidate in candidates:
        core = " ".join(_SOUNDTRACK_NOISE.sub(" ", _normalize_title(candidate)).split())
        core_solid = core.replace(" ", "")
        if core == movie or core_solid == movie_solid:
            return True
        # Tolerate transliteration differences (Desamuduru / Desamudhuru)
        if len(movie_solid) >= 6 and difflib.SequenceMatcher(None, movie_solid, core_solid).ratio() >= 0.88:
            return True
    return False


def _year_close(spotify_date: str, release_year: Optional[str], tolerance: int = 2) -> bool:
    try:
        return abs(int(spotify_date[:4]) - int(str(release_year)[:4])) <= tolerance
    except (TypeError, ValueError):
        return True


def soundtrack_album_rank(album: Dict[str, Any]) -> tuple:
    """Sort key: full song albums first, then singles ('Song (From "Movie")'), then score/trailer albums."""
    name = album.get("name", "")
    is_single = album.get("album_type") == "single" or bool(_FROM_MOVIE.search(name))
    return (bool(_SCORE_ONLY.search(name)), is_single, -(album.get("total_tracks") or 0))


def is_full_soundtrack_album(album: Dict[str, Any]) -> bool:
    return soundtrack_album_rank(album)[:2] == (False, False)


def web_find_spotify_soundtrack(sp: spotipy.Spotify, movie_name: str, release_year: Optional[str] = None,
                                language: Optional[str] = None, market: Optional[str] = None,
                                max_lookups: int = 6) -> Dict[str, Any]:
    """Find a movie's soundtrack on Spotify through web search.

    Spotify's own search misses many (especially regional) soundtracks, while web search
    engines index the open.spotify.com pages directly. Every link found is re-checked
    against the Spotify API with soundtrack_title_matches(), using at most `max_lookups` calls.

    Returns {"album": <full album object or None>, "tracks": [<track objects>]}.
    """
    extra = " ".join(x for x in (str(release_year or "")[:4], language or "") if x)
    queries = [
        f"{movie_name} {extra} film original motion picture soundtrack spotify",
        f"{movie_name} {extra} movie songs spotify album",
        f"site:open.spotify.com {movie_name} {extra} soundtrack",
    ]
    seen: set = set()
    albums: List[Dict[str, Any]] = []
    tracks: List[Dict[str, Any]] = []
    budget = [max_lookups]  # Spotify API calls left; keeps actor-wide runs clear of rate limits

    def consider_album(album_id: str) -> None:
        if album_id in seen or budget[0] <= 0:
            return
        seen.add(album_id)
        budget[0] -= 1
        try:
            album = sp.album(album_id, market=market)
        except Exception:
            return
        if not soundtrack_title_matches(movie_name, album.get("name", ""), language=language):
            return
        if release_year and not _year_close(album.get("release_date", ""), release_year):
            return
        albums.append(album)

    for q in queries:
        links: Dict[tuple, bool] = {}
        for result in ddg_web_search(" ".join(q.split()), max_results=8):
            # Page titles look like 'Movie (Original Motion Picture Soundtrack) - Album by X | Spotify'
            page_title = re.split(r"\s+[-–|]\s+(?:album|ep|single|compilation|song)\b|\s+[-–|]\s+spotify",
                                  result["title"], flags=re.I)[0]
            for link in _SPOTIFY_LINK.findall(f"{result['href']} {result['body']}"):
                links[link] = links.get(link, False) or soundtrack_title_matches(movie_name, page_title, language=language)
        # Links whose page title already matches first, album links before tracks
        for kind, sid in sorted(links, key=lambda link: (not links[link], link[0] != "album")):
            if kind == "album":
                consider_album(sid)
                continue
            if sid in seen or budget[0] <= 0:
                continue
            seen.add(sid)
            budget[0] -= 1
            try:
                t = sp.track(sid, market=market)
            except Exception:
                continue
            album = t.get("album") or {}
            if soundtrack_title_matches(movie_name, album.get("name", ""), language=language) and album.get("id"):
                consider_album(album["id"])
            elif soundtrack_title_matches(movie_name, t.get("name", ""), allow_plain=False, language=language):
                tracks.append(t)
        # Keep searching until a verified full soundtrack album turns up
        if budget[0] <= 0 or any(is_full_soundtrack_album(a) for a in albums):
            break

    albums.sort(key=soundtrack_album_rank)
    return {"album": albums[0] if albums else None, "tracks": tracks}


def fetch_tracks_for_movie(sp: spotipy.Spotify, movie_name: str, max_songs: int = 5,
                           release_year: Optional[str] = None) -> List[Dict[str, str]]:
    """Search Spotify for soundtrack albums and songs from a movie.

    Uses a 4-tier matching engine (strict title matching throughout):
    1. Spotify Soundtrack Album search
    2. Web search for open.spotify.com soundtrack links
    3. Spotify Track search ('Song (From "Movie")' or a matching album)
    4. DuckDuckGo tracklist discovery + Spotify direct search
    """
    tracks: List[Dict[str, str]] = []
    seen_uris = set()

    def add_track(item: Dict[str, Any], album_name: str) -> bool:
        """Append a track; returns True once max_songs is reached."""
        uri = item.get("uri")
        if uri and uri not in seen_uris:
            seen_uris.add(uri)
            tracks.append({
                "title": item.get("name", "Unknown"),
                "artists": ", ".join(a["name"] for a in item.get("artists", [])),
                "artist_ids": [a["id"] for a in item.get("artists", []) if "id" in a],
                "uri": uri,
                "movie": movie_name,
                "album": album_name
            })
        return len(tracks) >= max_songs

    def track_matches(item: Dict[str, Any]) -> bool:
        album = item.get("album", {})
        if release_year and not _year_close(album.get("release_date", ""), release_year):
            return False
        return (soundtrack_title_matches(movie_name, item.get("name", ""), allow_plain=False)
                or soundtrack_title_matches(movie_name, album.get("name", "")))

    # Strategy 1: Search for movie soundtrack/album
    album_queries = [
        f'album:"{movie_name}"',
        f"{movie_name} soundtrack",
        f"{movie_name} original motion picture soundtrack",
        movie_name
    ]

    candidates: Dict[str, Dict[str, Any]] = {}
    for query in album_queries:
        try:
            album_results = sp.search(q=query, type="album", limit=5)
            for a in album_results.get("albums", {}).get("items", []):
                if (soundtrack_title_matches(movie_name, a.get("name", ""))
                        and (not release_year or _year_close(a.get("release_date", ""), release_year))):
                    candidates.setdefault(a["id"], a)
        except Exception:
            pass
        if any(is_full_soundtrack_album(a) for a in candidates.values()):
            break
    albums = sorted(candidates.values(), key=soundtrack_album_rank)
    web_tracks: List[Dict[str, Any]] = []

    # Strategy 2: Spotify search found no full soundtrack album -> find its Spotify page via web search
    if not albums or not is_full_soundtrack_album(albums[0]):
        try:
            found = web_find_spotify_soundtrack(sp, movie_name, release_year=release_year)
            if found["album"]:
                albums.insert(0, found["album"])
            web_tracks = found["tracks"]
        except Exception:
            pass

    for album in albums:
        try:
            items = (album.get("tracks") or {}).get("items") or sp.album_tracks(album["id"], limit=max_songs).get("items", [])
        except Exception:
            continue
        for item in items:
            if add_track(item, album.get("name", "")):
                return tracks
    for item in web_tracks:
        if add_track(item, item.get("album", {}).get("name", "")):
            return tracks
    if tracks:
        return tracks

    # Strategy 3: Search tracks directly on Spotify
    track_queries = [
        f'track:"{movie_name}"',
        f'"From {movie_name}"',
        f"{movie_name} song",
        movie_name
    ]

    for tq in track_queries:
        try:
            results = sp.search(q=tq, type="track", limit=10)
            for item in results.get("tracks", {}).get("items", []):
                if track_matches(item) and add_track(item, item.get("album", {}).get("name", "")):
                    return tracks
        except Exception:
            pass

    # Strategy 4: DuckDuckGo-assisted song title resolution
    if len(tracks) < 2:
        try:
            for song_title in ddg_find_soundtrack_songs(movie_name, max_songs=max_songs):
                # Search Spotify for the specific song name discovered via DDG
                res = sp.search(q=f"{song_title} {movie_name}", type="track", limit=1)
                items = res.get("tracks", {}).get("items", [])
                if not items:
                    res = sp.search(q=song_title, type="track", limit=1)
                    items = res.get("tracks", {}).get("items", [])
                if items and track_matches(items[0]) and add_track(items[0], items[0].get("album", {}).get("name", "")):
                    break
        except Exception:
            pass

    return tracks


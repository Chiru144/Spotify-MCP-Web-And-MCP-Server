"""Discovery helpers built only on Spotify endpoints that still work for Development Mode apps.

In 2026 Spotify switched off related-artists, recommendations, genre seeds, artist top-tracks
and audio-features for Development Mode apps. These helpers approximate those features with
search and album data instead. Search pages hold 10 items, so every helper keeps its
number of Spotify calls small and bounded.
"""
import random
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional

# Genres that work with search's `genre:` filter (replaces /recommendations/available-genre-seeds)
GENRES = [
    "acoustic", "afrobeat", "alternative", "ambient", "blues", "bollywood", "chill", "classical",
    "country", "dance pop", "disco", "drum and bass", "dubstep", "edm", "electronic", "filmi", "folk",
    "funk", "gospel", "hip hop", "house", "indie", "indie pop", "j-pop", "jazz", "k-pop", "kannada",
    "latin", "lo-fi", "malayalam", "metal", "pop", "punk", "r&b", "reggae", "reggaeton", "rock",
    "romantic", "sad", "soul", "synthwave", "tamil", "techno", "telugu", "trance", "workout",
]

# Genres per mood (replaces audio-feature targets such as valence and energy)
MOOD_GENRES = {
    "happy": ["dance pop", "funk"],
    "sad": ["sad", "acoustic"],
    "chill": ["chill", "lo-fi"],
    "energetic": ["edm", "dance pop"],
    "focus": ["ambient", "classical"],
    "party": ["party", "dance pop"],
    "dark": ["metal", "industrial"],
    "romantic": ["romantic", "r&b"],
    "workout": ["workout", "edm"],
}

# Estimated (energy, valence) per genre, 0.0-1.0. Spotify no longer gives this app audio features,
# so energy/valence targets are matched against these genre estimates instead of per-track values.
GENRE_VIBES = {
    "acoustic": (0.30, 0.50), "afrobeat": (0.75, 0.80), "alternative": (0.65, 0.45),
    "ambient": (0.15, 0.40), "blues": (0.45, 0.40), "bollywood": (0.65, 0.70), "chill": (0.30, 0.55),
    "classical": (0.20, 0.40), "country": (0.55, 0.65), "dance pop": (0.80, 0.80), "disco": (0.80, 0.85),
    "drum and bass": (0.95, 0.50), "dubstep": (0.95, 0.35), "edm": (0.90, 0.65), "electronic": (0.75, 0.55),
    "filmi": (0.60, 0.65), "folk": (0.35, 0.50), "funk": (0.75, 0.85), "gospel": (0.55, 0.75),
    "hip hop": (0.70, 0.55), "house": (0.85, 0.70), "indie": (0.55, 0.50), "indie pop": (0.60, 0.60),
    "industrial": (0.90, 0.20), "j-pop": (0.75, 0.75), "jazz": (0.35, 0.55), "k-pop": (0.80, 0.75),
    "kannada": (0.60, 0.65), "latin": (0.80, 0.80), "lo-fi": (0.25, 0.50), "malayalam": (0.55, 0.60),
    "metal": (0.95, 0.25), "party": (0.85, 0.80), "pop": (0.70, 0.70), "punk": (0.90, 0.45),
    "r&b": (0.50, 0.55), "reggae": (0.55, 0.75), "reggaeton": (0.80, 0.75), "rock": (0.75, 0.50),
    "romantic": (0.40, 0.60), "sad": (0.25, 0.15), "soul": (0.50, 0.60), "synthwave": (0.70, 0.45),
    "tamil": (0.60, 0.65), "techno": (0.90, 0.45), "telugu": (0.65, 0.65), "trance": (0.85, 0.55),
    "workout": (0.95, 0.65),
}

# Target (energy, valence) per mood, used when ranking genres and cached tracks by vibe
MOOD_VIBES = {
    "happy": (0.75, 0.85), "sad": (0.25, 0.15), "chill": (0.30, 0.55), "energetic": (0.90, 0.70),
    "focus": (0.20, 0.45), "party": (0.85, 0.80), "dark": (0.85, 0.20), "romantic": (0.40, 0.65),
    "workout": (0.95, 0.65),
}

# Words in track, album or playlist names that hint at a genre (e.g. "Unplugged" -> acoustic, a "Gym" playlist -> workout)
NAME_HINTS = {
    "acoustic": "acoustic", "unplugged": "acoustic", "piano": "classical", "lofi": "lo-fi", "lo-fi": "lo-fi",
    "remix": "edm", "club mix": "house", "extended mix": "house", "instrumental": "ambient",
    "sad": "sad", "heartbreak": "sad", "love": "romantic", "romance": "romantic", "romantic": "romantic",
    "melody": "romantic", "party": "party", "dance": "dance pop", "workout": "workout", "gym": "workout",
    "chill": "chill", "relax": "chill", "sleep": "ambient", "study": "ambient", "focus": "ambient",
    "edm": "edm", "rock": "rock", "metal": "metal", "jazz": "jazz", "classical": "classical",
}


def _image(obj: Dict[str, Any]) -> Optional[str]:
    images = obj.get("images") or []
    return images[0].get("url") if images else None


def find_artist(sp, artist: str) -> Optional[Dict[str, Any]]:
    """Resolve an artist name, ID, URI or link to a Spotify artist object."""
    text = artist.strip()
    ref = text.split("?")[0].rstrip("/").split("/")[-1].split(":")[-1]
    if text.startswith("spotify:") or "spotify.com" in text or (len(ref) == 22 and " " not in ref):
        try:
            return sp.artist(ref)
        except Exception:
            pass
    items = sp.search(q=text, type="artist", limit=1).get("artists", {}).get("items", [])
    return items[0] if items else None


def artist_tracks(sp, artist: Dict[str, Any], limit: int = 20) -> List[Dict[str, Any]]:
    """Songs the artist performs on, via a name search (`artist:` filters return only 5 results)."""
    items = sp.search(q=artist["name"], type="track", limit=limit).get("tracks", {}).get("items", [])
    return [t for t in items if t and artist["id"] in [a.get("id") for a in t.get("artists", [])]]


def collaborators(sp, artist: Dict[str, Any], tracks: Optional[List[Dict[str, Any]]] = None,
                  limit: int = 10) -> List[Dict[str, Any]]:
    """Artists who share the most songs with `artist`, standing in for related-artists."""
    tracks = artist_tracks(sp, artist, limit=30) if tracks is None else tracks
    counts: Counter = Counter()
    info: Dict[str, Dict[str, Any]] = {}
    for t in tracks:
        for a in t.get("artists", []):
            if a.get("id") and a["id"] != artist["id"]:
                counts[a["id"]] += 1
                info[a["id"]] = a
    return [dict(info[aid], shared_tracks=n) for aid, n in counts.most_common(limit)]


def tracks_by_artists(sp, artists: Iterable[Dict[str, Any]], per_artist: int = 3,
                      exclude: Iterable[str] = ()) -> List[Dict[str, Any]]:
    """A few songs from each artist (one search call per artist)."""
    seen = set(exclude)
    out = []
    for a in artists:
        added = 0
        for t in artist_tracks(sp, a, limit=10):
            if added >= per_artist:
                break
            if t.get("uri") and t["uri"] not in seen:
                seen.add(t["uri"])
                out.append(t)
                added += 1
    return out


def genre_tracks(sp, genres: List[str], limit: int = 15) -> List[Dict[str, Any]]:
    """Songs for each genre via search's `genre:` filter, falling back to a plain search."""
    genres = [g for g in genres if g][:5]
    if not genres:
        return []
    per_genre = max(1, -(-limit // len(genres)))
    out, seen = [], set()
    for genre in genres:
        found = sp.search(q=f'genre:"{genre}"', type="track", limit=min(per_genre, 30)).get("tracks", {}).get("items", [])
        if not found:
            found = sp.search(q=genre, type="track", limit=min(per_genre, 30)).get("tracks", {}).get("items", [])
        for t in found:
            if t and t.get("uri") not in seen:
                seen.add(t["uri"])
                out.append(t)
    random.shuffle(out)
    return out[:limit]


def mood_tracks(sp, mood: Optional[str], genres: Optional[List[str]] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Songs for a mood. Other users' playlists are off-limits to this app (403), so moods
    are matched through genres instead."""
    mood_key = (mood or "").lower().strip()
    return genre_tracks(sp, genres or MOOD_GENRES.get(mood_key) or [mood_key or "pop"], limit)


def recommend(sp, seed_artists: List[str] = (), seed_tracks: List[str] = (), seed_genres: List[str] = (),
              limit: int = 20) -> List[Dict[str, Any]]:
    """Songs by the seeds' collaborators plus genre picks, standing in for /recommendations."""
    artist_ids = list(dict.fromkeys(a for a in seed_artists if a))
    exclude = set()
    for track_id in list(seed_tracks)[:3]:
        try:
            t = sp.track(track_id)
        except Exception:
            continue
        exclude.add(t.get("uri"))
        artist_ids += [a["id"] for a in t.get("artists", [])[:1] if a.get("id") not in artist_ids]

    picks: List[Dict[str, Any]] = []
    for artist_id in artist_ids[:2]:
        try:
            artist = sp.artist(artist_id)
        except Exception:
            continue
        own = artist_tracks(sp, artist)
        exclude.update(t["uri"] for t in own[:3])
        picks += tracks_by_artists(sp, collaborators(sp, artist, own, limit=5), per_artist=3,
                                   exclude=exclude | {p["uri"] for p in picks})
        picks += [t for t in own[3:6] if t["uri"] not in {p["uri"] for p in picks}]
    if seed_genres:
        taken = {p["uri"] for p in picks} | exclude
        picks += [t for t in genre_tracks(sp, list(seed_genres), limit) if t["uri"] not in taken]
    random.shuffle(picks)
    return picks[:limit]


def deep_cuts(sp, artist_or_album: str, limit: int = 15) -> Dict[str, Any]:
    """Album tracks that are not among the artist's (or album's) top search results.
    Track popularity is no longer provided, so 'deep cut' means 'not one of the hits'."""
    artist = find_artist(sp, artist_or_album)
    if artist:
        hits = {t["uri"] for t in artist_tracks(sp, artist)}
        albums = sp.artist_albums(artist["id"], include_groups="album", limit=5).get("items", [])
        cuts = []
        for album in albums[:4]:
            for t in sp.album_tracks(album["id"], limit=50).get("items", []):
                if t.get("uri") not in hits and artist["id"] in [a.get("id") for a in t.get("artists", [])]:
                    cuts.append(dict(t, album=album))
        random.shuffle(cuts)
        return {"name": artist.get("name"), "image": _image(artist), "tracks": cuts[:limit]}

    albums = sp.search(q=artist_or_album, type="album", limit=1).get("albums", {}).get("items", [])
    if not albums:
        return {"name": None, "image": None, "tracks": []}
    album = albums[0]
    hits = {t["uri"] for t in sp.search(q=album["name"], type="track", limit=10).get("tracks", {}).get("items", []) if t}
    cuts = [dict(t, album=album) for t in sp.album_tracks(album["id"], limit=50).get("items", []) if t.get("uri") not in hits]
    return {"name": album.get("name"), "image": _image(album), "tracks": cuts[:limit]}


def vibe_target(mood: Optional[str] = None, energy: Optional[float] = None,
                valence: Optional[float] = None) -> Optional[tuple]:
    """(energy, valence) to aim for: explicit values win, then the mood's preset. None if neither is given."""
    base = MOOD_VIBES.get((mood or "").lower().strip())
    if energy is None and valence is None and not base:
        return None
    e = energy if energy is not None else (base[0] if base else None)
    v = valence if valence is not None else (base[1] if base else None)
    return (None if e is None else max(0.0, min(1.0, float(e))),
            None if v is None else max(0.0, min(1.0, float(v))))


def _vibe_distance(vibe: tuple, target: tuple) -> float:
    return sum((a - b) ** 2 for a, b in zip(vibe, target) if b is not None) ** 0.5


def vibe_genres(target: tuple, count: int = 2, pool: Optional[Iterable[str]] = None) -> List[str]:
    """Genres whose estimated (energy, valence) is closest to `target`."""
    candidates = [g for g in (pool or GENRE_VIBES) if g in GENRE_VIBES]
    return sorted(candidates, key=lambda g: _vibe_distance(GENRE_VIBES[g], target))[:count]


def estimate_vibe(genres: Iterable[str]) -> Optional[tuple]:
    """Average estimated (energy, valence) of the known genres, or None."""
    vibes = [GENRE_VIBES[g] for g in genres if g in GENRE_VIBES]
    if not vibes:
        return None
    return (sum(e for e, _ in vibes) / len(vibes), sum(v for _, v in vibes) / len(vibes))


def name_genres(track: Dict[str, Any]) -> List[str]:
    """Genres hinted at by words in the track's or album's name, or in the names of the user's
    playlists that hold it (cached tracks list those as `sources`, e.g. "playlist:Gym Hits")."""
    album = track.get("album")
    playlists = " ".join(s[len("playlist:"):] for s in track.get("sources", []) if s.startswith("playlist:"))
    text = f"{track.get('name', '')} {album.get('name', '') if isinstance(album, dict) else album or ''} {playlists}".lower()
    return sorted({genre for word, genre in NAME_HINTS.items() if word in text})


def genre_artist_ids(sp, genre: str, limit: int = 30) -> set:
    """IDs of artists on the top `genre:` search results. Spotify returns null genres for
    artists and an empty `genre:` artist search, so a genre's artists are learned from its tracks."""
    items = sp.search(q=f'genre:"{genre}"', type="track", limit=limit).get("tracks", {}).get("items", [])
    return {a["id"] for t in items if t for a in t.get("artists", []) if a.get("id")}


def tag_tracks(sp, tracks: List[Dict[str, Any]], genres: List[str], per_genre: int = 30) -> Dict[str, List[str]]:
    """Estimated genres per track URI: genres whose search results include one of the track's
    artists, plus genres hinted at by its name. Makes one paged search per genre (max 4 genres)."""
    tags = {t["uri"]: name_genres(t) for t in tracks if t.get("uri")}
    for genre in genres[:4]:
        ids = genre_artist_ids(sp, genre, per_genre)
        for t in tracks:
            if t.get("uri") in tags and genre not in tags[t["uri"]] and any(
                    a.get("id") in ids for a in t.get("artists", [])):
                tags[t["uri"]].append(genre)
    return tags


def pick_by_vibe(sp, tracks: List[Dict[str, Any]], target: tuple, limit: int = 30,
                 max_distance: float = 0.35, genres: Optional[List[str]] = None,
                 report: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Tracks (e.g. from the user's library) whose estimated vibe is close to `target`, closest first.
    `genres` are the genres to check the tracks against (default: the 4 closest to `target`).
    Each track gets `vibe_genres` and `vibe` keys; tracks with no estimate are left out.
    If `report` is given, it is filled with the probed genres and how many tracks got an estimate."""
    probe = [g for g in (genres or []) if g][:4] or vibe_genres(target, count=4)
    tags = tag_tracks(sp, tracks, probe)
    if report is not None:
        report.update(genres=probe, placed=sum(1 for g in tags.values() if estimate_vibe(g) is not None))
    scored = []
    for t in tracks:
        vibe = estimate_vibe(tags.get(t.get("uri"), []))
        if vibe is not None and _vibe_distance(vibe, target) <= max_distance:
            scored.append((_vibe_distance(vibe, target), dict(t, vibe_genres=tags[t["uri"]], vibe=vibe)))
    scored.sort(key=lambda x: x[0])
    return [t for _, t in scored[:limit]]


def era_tracks(sp, start_year: int, end_year: int, genres: Optional[List[str]] = None,
               limit: int = 30) -> List[Dict[str, Any]]:
    """Songs released between two years via search's `year:` filter, optionally per genre."""
    years = f"{min(start_year, end_year)}-{max(start_year, end_year)}"
    queries = [f'year:{years} genre:"{g}"' for g in (genres or [])[:3]] or [f"year:{years}"]
    per_query = max(1, -(-limit // len(queries)))
    out, seen = [], set()
    for q in queries:
        for t in sp.search(q=q, type="track", limit=min(per_query, 50)).get("tracks", {}).get("items", []):
            if t and t.get("uri") not in seen:
                seen.add(t["uri"])
                out.append(t)
    random.shuffle(out)
    return out[:limit]

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

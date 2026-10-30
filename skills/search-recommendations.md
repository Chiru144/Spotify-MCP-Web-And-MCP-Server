# Search, Recommendations & Discovery Skill Guide

This skill equips AI agents to search Spotify's catalog, explore artist networks, discover music by mood and genre, unearth hidden album deep cuts, and generate seed-based recommendations through the 7 **Search, Recommendations & Discovery Tools**.

> [!NOTE]
> In 2026 Spotify switched off related artists, recommendations, genre seeds, artist top tracks and audio features for Development Mode apps, and now returns null popularity, followers and genres. These tools rebuild discovery from search and album data instead: "related" artists are the ones who share the most songs with an artist, moods map to genres, and `target_energy` / `target_valence` pick the genres whose estimated energy and valence are closest. Other `target_*` and popularity arguments are accepted but ignored (the tool output says so). Don't promise exact valence, energy, tempo or popularity filtering.

---

## Tool Roster & Capability Matrix

| Tool | Action | Primary Parameters | Key Output |
| :--- | :--- | :--- | :--- |
| **`spotify_search`** | Search catalog for tracks, artists, albums, playlists | `query` (str), `types` (List[str]), `limit` (int), `market` (Optional[str]) | Formatted list grouped by item type with URIs |
| **`spotify_related_artists`** | Find artists connected to a target artist | `artist` (name, ID, or URI) | Artists who share the most songs with the target, with shared-song counts |
| **`spotify_discover_by_artist`** | Derive tracks from the artist's collaborators | `artist` (str), `limit` (int), `include_artist_top_tracks` (bool) | Songs by collaborators + the artist's own top search results |
| **`spotify_discover_by_mood`** | Discover tracks by mood preset, genres or energy/valence | `mood` (preset name), `seed_genres`, `target_energy`, `target_valence`, `limit` | Genre-matched tracks for the mood |
| **`spotify_genre_explorer`** | List suggested genres or sample tracks for genres | `genres` (Optional[List[str]]), `limit` (int) | Built-in genre list, or sample tracks per genre |
| **`spotify_discover_deep_cuts`** | Unearth album tracks that aren't the artist's hits | `artist_or_album` (str), `limit` (int) | Album tracks outside the artist's or album's top search results |
| **`spotify_get_recommendations`** | Seed-based recommendations | `limit`, `seed_tracks`, `seed_artists`, `seed_genres` | Songs by the seeds' collaborators plus genre picks |

Mood presets: `happy`, `sad`, `chill`, `energetic`, `focus`, `party`, `dark`, `romantic`, `workout` (each maps to two genres).

---

## Common Agent Prompts & Patterns

### 1. Catalog Search
> *"Search Spotify for tracks, albums, and playlists related to 'Cyberpunk 2077'."*
```python
spotify_search(
    query="Cyberpunk 2077",
    types=["track", "album", "playlist"],
    limit=5
)
```

### 2. Discovering Related Artists
> *"Find artists similar to Ludovico Einaudi."*
```python
spotify_related_artists(artist="Ludovico Einaudi")
```
Tell the user these are collaborators (artists who appear on songs with them), not Spotify's old "Fans also like" list.

### 3. Artist Network Recommendations
> *"Find me 15 tracks from artists related to Radiohead, and include their top tracks."*
```python
spotify_discover_by_artist(
    artist="Radiohead",
    limit=15,
    include_artist_top_tracks=True
)
```

### 4. Mood Discovery
> *"Find me 20 energetic workout tracks."*
```python
spotify_discover_by_mood(mood="workout", limit=20)

# Or pick the genres yourself:
spotify_discover_by_mood(seed_genres=["edm", "hip hop"], limit=20)
```

### 5. Genre Sampling
> *"What genres can I explore? Also sample 10 synthwave and lo-fi tracks."*
```python
# To list the suggested genres:
spotify_genre_explorer()

# To sample specific genres (any genre keyword works, not only the listed ones):
spotify_genre_explorer(genres=["synthwave", "lo-fi"], limit=10)
```

### 6. Deep Cuts Finder (Hidden Gems)
> *"I love Pink Floyd but I want to discover their lesser-known album cuts, not 'Comfortably Numb' or 'Money'."*
```python
spotify_discover_deep_cuts(artist_or_album="Pink Floyd", limit=15)
```

### 7. Multi-Seed Recommendations
> *"Generate 20 recommendations using the track 'Billie Jean' and genre 'funk'."*
```python
spotify_get_recommendations(
    seed_tracks=["spotify:track:5ChkMS8Otdzsq2oj5BKx9Y"],
    seed_genres=["funk"],
    limit=20
)
```
"High energy" or "low valence" can be passed as `target_energy` / `target_valence`; they choose genres with similar estimated vibes. Danceability, acousticness and tempo can't be applied: explain that Spotify no longer provides audio features, and suggest a mood preset or genres that fit instead.

---

## Technical Constraints & Safety Rules
- **Seed Limit**: `get_recommendations` accepts at most 5 seeds in total; `spotify_get_recommendations` uses the first 2 artists and 3 tracks plus up to 5 genres.
- **Deep Cuts**: `spotify_discover_deep_cuts` takes the artist's top search results as their hits and returns other tracks from up to 4 of their albums.
- **Call Budget**: Spotify search pages hold 10 items, so each discovery call makes several searches. Avoid looping these tools over many artists in a row; this app has been rate-limited before.
- **URI Cleaning**: All IDs, full Spotify URLs (`https://open.spotify.com/track/...`), and URIs (`spotify:track:...`) are normalized automatically.

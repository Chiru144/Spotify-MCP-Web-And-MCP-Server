# Search, Recommendations & Discovery Skill Guide

This skill equips AI agents to search Spotify's catalog, explore artist networks, discover music by mood and audio attributes, sample genre seeds, unearth hidden album deep cuts, and generate fine-tuned recommendations through the 7 **Search, Recommendations & Discovery Tools**.

---

## Tool Roster & Capability Matrix

| Tool | Action | Primary Parameters | Key Output |
| :--- | :--- | :--- | :--- |
| **`spotify_search`** | Search catalog for tracks, artists, albums, playlists | `query` (str), `types` (List[str]), `limit` (int), `market` (Optional[str]) | Formatted list grouped by item type with URIs & metrics |
| **`spotify_related_artists`** | Find similar artists to a target artist | `artist` (name, ID, or URI) | List of related artists with popularity, genres, followers |
| **`spotify_discover_by_artist`** | Derive tracks from artist network | `artist` (str), `limit` (int), `include_artist_top_tracks` (bool) | Recommended tracks from peer network + top tracks |
| **`spotify_discover_by_mood`** | Discover tracks by mood or audio parameters | `mood` (preset name), `seed_genres`, `target_valence`, `target_energy`, `target_tempo`, `limit` | Curated tracks matching target emotional vibe |
| **`spotify_genre_explorer`** | Browse and sample Spotify genre seeds | `genres` (Optional[List[str]]), `limit` (int), `market` (Optional[str]) | Sample tracks across genre seeds or list all available seeds |
| **`spotify_discover_deep_cuts`** | Unearth non-single, album-only hidden tracks | `artist_or_album` (str), `max_popularity` (int, default 40), `limit` (int) | Low-popularity album gems excluding popular singles |
| **`spotify_get_recommendations`** | Direct wrapper for Spotify Recommendations API | `limit`, `seed_tracks`, `seed_artists`, `seed_genres`, `target_*`, `min_popularity`, `max_popularity` | Seed-based recommendations filtered by audio targets |

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

### 3. Artist Network Recommendations
> *"Find me 15 tracks from artists related to Radiohead, and include their top tracks."*
```python
spotify_discover_by_artist(
    artist="Radiohead",
    limit=15,
    include_artist_top_tracks=True
)
```

### 4. Mood Discovery with Emotional Presets & Audio Sliders
> *"Find me 20 energetic workout tracks with high tempo."*
```python
spotify_discover_by_mood(
    mood="workout",
    target_energy=0.95,
    target_tempo=135.0,
    limit=20
)
```

### 5. Genre Seed Sampling
> *"What genre seeds can I use on Spotify? Also sample 10 synthwave and lo-fi tracks."*
```python
# To inspect all available genre seeds:
spotify_genre_explorer()

# To sample specific genres:
spotify_genre_explorer(genres=["synthwave", "lo-fi"], limit=10)
```

### 6. Deep Cuts Finder (Hidden Gems)
> *"I love Pink Floyd but I want to discover their lesser-known album cuts, not 'Comfortably Numb' or 'Money'."*
```python
spotify_discover_deep_cuts(
    artist_or_album="Pink Floyd",
    max_popularity=35,
    limit=15
)
```

### 7. Precise Multi-Seed Recommendations
> *"Generate 20 recommendations using the track 'Billie Jean' and genre 'funk' with high danceability and low valence."*
```python
spotify_get_recommendations(
    seed_tracks=["spotify:track:5ChkMS8Otdzsq2oj5BKx9Y"],
    seed_genres=["funk"],
    target_danceability=0.85,
    target_valence=0.35,
    limit=20
)
```

---

## Technical Constraints & Safety Rules
- **Seed Limit**: Spotify Recommendations API strictly enforces $1 \le \text{total seeds} \le 5$ (sum of tracks, artists, and genres). All tools automatically enforce and truncate excess seeds.
- **Deep Cuts Singles Filtering**: `spotify_discover_deep_cuts` pulls artist top tracks and removes those URIs before scanning studio album tracklists.
- **URI Cleaning**: All IDs, full Spotify URLs (`https://open.spotify.com/track/...`), and URIs (`spotify:track:...`) are normalized automatically.

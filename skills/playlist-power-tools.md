# Playlist Power Tools Skill Guide

This skill equips AI agents to execute advanced, programmatic playlist curation, restructuring, and library analysis through the 8 **Playlist Power Tools**.

---

## Tool Roster & Capability Matrix

| Power Tool | Action | Primary Parameters | Key Output |
| :--- | :--- | :--- | :--- |
| **`spotify_merge_playlists`** | Combine multiple playlists | `playlist_ids` (List[str]), `target_playlist_id` (Optional), `new_name`, `public`, `deduplicate` | Unified target or new playlist ID & URL |
| **`spotify_split_playlist_by_artist`** | Separate tracks into sub-playlists | `playlist_id`, `min_tracks_per_artist` (int), `create_playlists` (bool), `public` (bool) | Preview breakdown or created sub-playlists |
| **`spotify_deduplicate_playlist`** | Deep duplicate scanner & stripper | `playlist_id`, `strategy` ('uri' or 'name_and_artist'), `dry_run` (bool) | Found duplicates report or in-place cleaned count |
| **`spotify_export_playlist`** | Full data backup to JSON | `playlist_id` | JSON structure with all track metadata (audio features are no longer available) |
| **`spotify_playlist_diff`** | Side-by-side playlist comparator | `playlist_id_a`, `playlist_id_b`, `strategy` ('uri' or 'name_and_artist') | Jaccard similarity %, shared songs, unique tracks |
| **`spotify_find_playlist_overlaps`** | Cross-library overlap scanner | `limit` (int), `min_overlap` (int) | Ranked pairs of playlists with highest track overlaps |
| **`spotify_find_playlist_subsets`** | Subset & redundancy detector | `limit` (int), `threshold` (float 0.5–1.0) | Discovered subset relations ($A \subseteq B$) & recommendations |
| **`spotify_absorb_playlist`** | Pull missing tracks into destination | `source_playlist_id`, `target_playlist_id`, `strategy` | Absorbed new songs count without any duplicates |

---

## Common Agent Prompts & Patterns

### 1. Merging Multiple Playlists
> *"Merge my Workout playlist and Running playlist into a single Marathon Mix, making sure to remove any duplicate tracks."*
```python
spotify_merge_playlists(
    playlist_ids=["37i9dQZF1DXdLEN7aqioXM", "37i9dQZF1DX70RN3TfWWJh"],
    new_name="Marathon Mix",
    deduplicate=True
)
```

### 2. Splitting a Mega-Playlist by Artist
> *"I have a 300-song playlist called 'Indie Favorites'. Split it up so artists with 3 or more songs get their own sub-playlist."*
```python
# Step 1: Preview the split
spotify_split_playlist_by_artist(playlist_id="...", min_tracks_per_artist=3, create_playlists=False)

# Step 2: Confirm and create
spotify_split_playlist_by_artist(playlist_id="...", min_tracks_per_artist=3, create_playlists=True)
```

### 3. Deep Deduplication
> *"Scan my 'Chill Vibes' playlist for duplicate songs using title and artist matching, but only preview what would be removed first."*
```python
# Dry run scan
spotify_deduplicate_playlist(playlist_id="...", strategy="name_and_artist", dry_run=True)

# Live removal
spotify_deduplicate_playlist(playlist_id="...", strategy="name_and_artist", dry_run=False)
```

### 4. Comparing Two Playlists (Diff)
> *"Compare my Roadtrip 2023 and Roadtrip 2024 playlists to show me what's shared and what's unique to each."*
```python
spotify_playlist_diff(playlist_id_a="...", playlist_id_b="...")
```

### 5. Identifying Redundant Playlists
> *"Check my playlists to see if any are complete duplicates or subsets of another so I can clean up my Spotify library."*
```python
spotify_find_playlist_subsets(limit=25, threshold=1.0)
```

### 6. Absorbing New Songs
> *"Pull all the songs from this Discover Weekly playlist into my Permanent Archive, but skip anything that's already in the archive."*
```python
spotify_absorb_playlist(source_playlist_id="...", target_playlist_id="...", strategy="name_and_artist")
```

### 7. Exporting Complete Backups
> *"Export my entire Favorites playlist to JSON."*
```python
spotify_export_playlist(playlist_id="...")
```

---

## Playlist Generators

| Tool | Builds | Key Parameters |
| :--- | :--- | :--- |
| **`spotify_vibe_playlist`** | Songs matching a mood or energy/valence target, from the cached library or all of Spotify | `mood`, `target_energy`, `target_valence`, `genres`, `from_library` |
| **`spotify_radio_playlist`** | An artist's songs mixed with songs by their collaborators | `seed` (artist or track) |
| **`spotify_era_playlist`** | Songs released in a year range | `start_year`, `end_year`, `genres`, `from_library` |
| **`spotify_time_capsule_playlist`** | Songs saved in a given year, or all-time top tracks | `year` |

All four take `limit`, `create`, `name` and `public`. They only preview their picks until called with `create=True`, so show the preview and ask before creating.

> *"Make a workout playlist from songs I already like."*
```python
spotify_sync_library()  # once
spotify_vibe_playlist(mood="workout", from_library=True)
spotify_vibe_playlist(mood="workout", from_library=True, create=True, name="Gym Mix")
```

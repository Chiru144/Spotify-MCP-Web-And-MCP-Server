# Stats, Analytics & Insights Skill

## Overview
Comprehensive listening telemetry, temporal volume distributions, taste profiles, multi-playlist comparisons, and library maintenance audits.

> [!NOTE]
> Spotify no longer returns audio features, popularity, followers or genres to Development Mode apps (2026 Web API changes). Outputs leave these out (or show N/A) instead of reporting energy, valence, obscurity or mainstream scores.

## Tools Included

### 1. `spotify_top_tracks(time_range="medium_term", limit=20)`
- **Purpose**: Fetch user's top tracks over short (`~4 weeks`), medium (`~6 months`), or long (`years`) term.
- **REST Endpoint**: `GET /api/stats/top_tracks?time_range=...&limit=...`
- **Output**: Ranked tracks with duration, artist, album and URI.

### 2. `spotify_top_artists(time_range="medium_term", limit=20)`
- **Purpose**: Fetch user's top artists over short, medium, or long term.
- **REST Endpoint**: `GET /api/stats/top_artists?time_range=...&limit=...`
- **Output**: Ranked artists with URI (genre tags only when Spotify provides them).

### 3. `spotify_recently_played(limit=50)`
- **Purpose**: Fetch recent listening history with UTC timestamps.
- **REST Endpoint**: `GET /api/stats/recently_played?limit=...`
- **Output**: Chronological list of recent tracks with playback timestamps and durations.

### 4. `spotify_listening_patterns(limit=50)`
- **Purpose**: Analyze listening volume distributions across hours and days of the week.
- **REST Endpoint**: `GET /api/stats/listening_patterns?limit=50`
- **Output**: Peak listening hour, peak day, 24-hour UTC histogram, and repeat tracks count.

### 5. `spotify_taste_profile(time_range="medium_term")`
- **Purpose**: Generate an overview of your top artists, artist variety, eras and listener type.
- **REST Endpoint**: `GET /api/stats/taste_profile?time_range=...`
- **Output**: Listener type based on artist variety (*Wide Explorer*, *Balanced Listener*, *Devoted Fan*), top artists, most-represented artists, decade spread and explicit share.

### 6. `spotify_playlist_compare(playlist_ids=["id1", "id2"])`
- **Purpose**: Compare playlists you own or follow side-by-side (Spotify returns 403 for other playlists).
- **REST Endpoint**: `POST /api/playlist/compare` & `GET /api/playlist/compare?playlist_ids=...`
- **Output**: Side-by-side table of track count, average song length, explicit share, artist count and median release year, plus songs and artists shared by every playlist.

### 7. `spotify_playlist_freshness(limit=25, stale_days_threshold=60)`
- **Purpose**: Sort playlists by last update timestamp to identify stale collections.
- **REST Endpoint**: `GET /api/playlist/freshness?limit=...&stale_days_threshold=...`
- **Output**: Sorted audit table with status (`🟢 Fresh`, `🟡 Aging`, `🔴 Stale / Empty`) and elapsed days since last track addition.

## UI Location
Open `http://127.0.0.1:8000/tools` and select the **📊 Stats, Analytics & Insights Studio** card.

# Stats, Analytics & Insights Skill

## Overview
Comprehensive listening telemetry, temporal volume distributions, taste archetype classification, multi-playlist audio feature comparisons, and library maintenance audits.

## Tools Included

### 1. `spotify_top_tracks(time_range="medium_term", limit=20)`
- **Purpose**: Fetch user's top tracks over short (`~4 weeks`), medium (`~6 months`), or long (`years`) term.
- **REST Endpoint**: `GET /api/stats/top_tracks?time_range=...&limit=...`
- **Output**: Ranked tracks with popularity, duration, artist, album, URI, and preview.

### 2. `spotify_top_artists(time_range="medium_term", limit=20)`
- **Purpose**: Fetch user's top artists over short, medium, or long term.
- **REST Endpoint**: `GET /api/stats/top_artists?time_range=...&limit=...`
- **Output**: Ranked artists with genre tags, popularity index, follower counts, and URI.

### 3. `spotify_recently_played(limit=50)`
- **Purpose**: Fetch recent listening history with UTC timestamps.
- **REST Endpoint**: `GET /api/stats/recently_played?limit=...`
- **Output**: Chronological list of recent tracks with playback timestamps and durations.

### 4. `spotify_listening_patterns(limit=50)`
- **Purpose**: Analyze listening volume distributions across hours and days of the week.
- **REST Endpoint**: `GET /api/stats/listening_patterns?limit=50`
- **Output**: Peak listening hour, peak day, 24-hour UTC histogram, and repeat tracks count.

### 5. `spotify_taste_profile(time_range="medium_term")`
- **Purpose**: Generate an overview of genre diversity, obscurity index, and listener archetype.
- **REST Endpoint**: `GET /api/stats/taste_profile?time_range=...`
- **Output**: Listener archetype (e.g. *Underground Explorer*, *Eclectic Connoisseur*), obscurity %, top genres, and niche/mainstream artists.

### 6. `spotify_playlist_compare(playlist_ids=["id1", "id2"])`
- **Purpose**: Compare multi-playlist audio feature distributions side-by-side.
- **REST Endpoint**: `POST /api/playlist/compare` & `GET /api/playlist/compare?playlist_ids=...`
- **Output**: Side-by-side table of energy, valence, danceability, acousticness, instrumentalness, tempo, and popularity averages.

### 7. `spotify_playlist_freshness(limit=25, stale_days_threshold=60)`
- **Purpose**: Sort playlists by last update timestamp to identify stale collections.
- **REST Endpoint**: `GET /api/playlist/freshness?limit=...&stale_days_threshold=...`
- **Output**: Sorted audit table with status (`🟢 Fresh`, `🟡 Aging`, `🔴 Stale / Empty`) and elapsed days since last track addition.

## UI Location
Open `http://127.0.0.1:8000/tools` and select the **📊 Stats, Analytics & Insights Studio** card.

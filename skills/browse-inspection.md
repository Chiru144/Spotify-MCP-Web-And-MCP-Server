# Catalog & Entity Inspection (Browse) Skill

## Overview
Deep-dive inspection and metadata analysis of Spotify catalog entities, including tracks, albums, artists, artist discographies, and your own user profile.

> [!NOTE]
> Spotify no longer returns popularity, followers or genres to Development Mode apps, or other users' profiles (2026 Web API changes). These fields show N/A.

## Tools Included

### 1. `spotify_get_track(track_id, market=None)`
- **Purpose**: Inspect full track metadata including ISRC, 30s preview URL, album info, and explicit status.
- **REST Endpoint**: `GET /api/browse/track?track_id=...&market=...`
- **Output**: Formatted overview with title, artists, album, duration, ISRC, and playable preview link (popularity shows N/A).

### 2. `spotify_get_album(album_id, market=None)`
- **Purpose**: Inspect album details, record label, legal copyrights, release date, and complete tracklist.
- **REST Endpoint**: `GET /api/browse/album?album_id=...&market=...`
- **Output**: Formatted overview with title, artists, release date, label, copyrights, and numbered tracklist.

### 3. `spotify_get_artist(artist_id)`
- **Purpose**: Inspect artist details and profile avatar.
- **REST Endpoint**: `GET /api/browse/artist?artist_id=...`
- **Output**: Formatted profile with name, image and Spotify URL (followers, popularity and genres show N/A).

### 4. `spotify_get_artist_albums(artist_id, include_groups="album,single", limit=20, offset=0, country=None)`
- **Purpose**: Fetch all albums, singles, and compilations released by a target artist.
- **REST Endpoint**: `GET /api/browse/artist/albums?artist_id=...&include_groups=...&limit=...`
- **Output**: Formatted discography grouped by type with release dates and total tracks.

### 5. `spotify_get_user(user_id)`
- **Purpose**: Fetch your own profile (pass your user ID or `me`). Other users' profiles return an "unavailable" message: Spotify blocks them for Development Mode apps.
- **REST Endpoint**: none (removed from the web app).
- **Output**: Formatted user card with display name, avatar, Spotify link, and your playlists.

## UI Location
Open `http://127.0.0.1:8000/tools` and navigate to the **🔎 Catalog & Entity Inspection (Browse) Studio** section.

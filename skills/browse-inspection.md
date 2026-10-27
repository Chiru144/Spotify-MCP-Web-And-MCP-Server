# Catalog & Entity Inspection (Browse) Skill

## Overview
Deep-dive inspection and metadata analysis of Spotify catalog entities, including tracks, albums, artists, artist discographies, and public user profiles.

## Tools Included

### 1. `spotify_get_track(track_id, market=None)`
- **Purpose**: Inspect full track metadata including ISRC, popularity rating, 30s preview URL, album info, and explicit status.
- **REST Endpoint**: `GET /api/browse/track?track_id=...&market=...`
- **Output**: Formatted overview with title, artists, album, duration, ISRC, popularity score, and playable preview link.

### 2. `spotify_get_album(album_id, market=None)`
- **Purpose**: Inspect album details, record label, legal copyrights, release date, and complete tracklist.
- **REST Endpoint**: `GET /api/browse/album?album_id=...&market=...`
- **Output**: Formatted overview with title, artists, release date, label, copyrights, and numbered tracklist.

### 3. `spotify_get_artist(artist_id)`
- **Purpose**: Inspect artist details including global followers, popularity index, genres, and profile avatar.
- **REST Endpoint**: `GET /api/browse/artist?artist_id=...`
- **Output**: Formatted profile with name, followers count, genres, popularity score, and Spotify URL.

### 4. `spotify_get_artist_albums(artist_id, include_groups="album,single", limit=20, offset=0, country=None)`
- **Purpose**: Fetch all albums, singles, and compilations released by a target artist.
- **REST Endpoint**: `GET /api/browse/artist/albums?artist_id=...&include_groups=...&limit=...`
- **Output**: Formatted discography grouped by type with release dates and total tracks.

### 5. `spotify_get_user(user_id)`
- **Purpose**: Fetch public profile information, followers count, avatar, and public playlists for any Spotify user.
- **REST Endpoint**: `GET /api/browse/user?user_id=...`
- **Output**: Formatted user card with display name, followers, Spotify link, and list of public playlists.

## UI Location
Open `http://127.0.0.1:8000/tools` and navigate to the **🔎 Catalog & Entity Inspection (Browse) Studio** section.

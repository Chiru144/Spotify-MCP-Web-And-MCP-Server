# Library & Liked Media Operations Skill

## Overview
Comprehensive management of the user's Spotify personal library, including Liked Songs (saved tracks) and saved album collections.

## Tools Included

### 1. `spotify_get_saved_tracks(limit=20, offset=0, market=None)`
- **Purpose**: List songs saved in the user's Liked Songs library.
- **REST Endpoint**: `GET /api/library/tracks?limit=...&offset=...`
- **Output**: Formatted list of liked tracks with rank, artist, album, duration, added date, and URI.

### 2. `spotify_save_tracks(track_ids=["spotify:track:..."])`
- **Purpose**: Save one or more tracks to user's Liked Songs.
- **REST Endpoint**: `POST /api/library/tracks`
- **Output**: Confirmation message with count of tracks saved.

### 3. `spotify_remove_saved_tracks(track_ids=["spotify:track:..."])`
- **Purpose**: Remove (unlike) one or more tracks from Liked Songs.
- **REST Endpoint**: `DELETE /api/library/tracks`
- **Output**: Confirmation message with count of tracks removed.

### 4. `spotify_check_saved_tracks(track_ids=["id1", "id2"])`
- **Purpose**: Verify whether specific tracks exist in Liked Songs.
- **REST Endpoint**: `POST /api/library/tracks/check` & `GET /api/library/tracks/check?track_ids=...`
- **Output**: Status per track (`🟢 Liked (In Library)` or `⚪ Not Liked`).

### 5. `spotify_get_saved_albums(limit=20, offset=0, market=None)`
- **Purpose**: Fetch albums saved in the user's library.
- **REST Endpoint**: `GET /api/library/albums?limit=...&offset=...`
- **Output**: Formatted list of saved albums with title, artists, release year, total tracks, and URI.

### 6. `spotify_save_albums(album_ids=["spotify:album:..."])`
- **Purpose**: Save one or more albums to user's library.
- **REST Endpoint**: `POST /api/library/albums`
- **Output**: Confirmation message with count of albums saved.

### 7. `spotify_remove_saved_albums(album_ids=["spotify:album:..."])`
- **Purpose**: Remove one or more albums from user's library.
- **REST Endpoint**: `DELETE /api/library/albums`
- **Output**: Confirmation message with count of albums removed.

### 8. `spotify_check_saved_albums(album_ids=["id1", "id2"])`
- **Purpose**: Verify whether specific albums exist in user library.
- **REST Endpoint**: `POST /api/library/albums/check` & `GET /api/library/albums/check?album_ids=...`
- **Output**: Status per album (`🟢 Saved (In Library)` or `⚪ Not Saved`).

## UI Location
Open `http://127.0.0.1:8000/tools` and navigate to the **📚 Library & Saved Media Studio** section.

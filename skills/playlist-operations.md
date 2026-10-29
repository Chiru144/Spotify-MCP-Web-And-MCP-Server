# Spotify Playlist Operations

## Description
A comprehensive skill for creating, updating, organizing, reordering, and inspecting Spotify playlists.

## When to use this skill
- When the user asks to "create a playlist", "list my playlists", "reorder songs in my playlist", "add or remove tracks from a playlist", "follow or unfollow a playlist", or "check who follows my playlist".

## Available Tools
1. `spotify_get_my_playlists(limit=50, offset=0)`: List user's created and saved playlists.
2. `spotify_get_playlist(playlist_id, fields=None)`: Fetch full details, metadata, follower count, and cover art.
3. `spotify_get_playlist_tracks(playlist_id, limit=50, offset=0)`: Paginate through tracks in a playlist.
4. `spotify_create_playlist(name, description="", public=True, collaborative=False)`: Create a new empty playlist.
5. `spotify_add_to_playlist(playlist_id, uris, position=None)`: Append or insert tracks into an existing playlist.
6. `spotify_remove_from_playlist(playlist_id, uris, snapshot_id=None)`: Remove specific tracks from a playlist.
7. `spotify_reorder_playlist(playlist_id, range_start, insert_before, range_length=1, snapshot_id=None)`: Move or reorder track positions in a playlist.
8. `spotify_update_playlist(playlist_id, name=None, description=None, public=None, collaborative=None)`: Modify playlist name, description, or privacy settings.
9. `spotify_follow_playlist(playlist_id, public=True)`: Add a playlist to user's library (Follow).
10. `spotify_unfollow_playlist(playlist_id)`: Remove a playlist from user's library (Unfollow/Delete).
11. `spotify_get_playlist_cover(playlist_id)`: Retrieve high-res cover image URL(s).
12. `spotify_check_playlist_followers(playlist_id, user_ids)`: Check whether you follow a playlist (only your own user ID; Spotify blocks checks for other users).

## Instructions
1. **Identify the playlist**: If the user provides a playlist name instead of an ID, call `spotify_get_my_playlists()` to locate the playlist ID.
2. **Execute operation**: Call the corresponding tool with appropriate parameters.
3. **Handle track identification**: When adding or removing tracks, ensure track URIs (`spotify:track:...`) are resolved via search if necessary.
4. **Confirm action**: Provide a concise confirmation with relevant details (e.g., new track position, updated name, or confirmed follower status).

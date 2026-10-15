# Spotify Playlist Deduplicator

## Description
A single-purpose skill that finds duplicate songs in a playlist and removes them.

## When to use this skill
- When the user says "My playlist has duplicates", "clean up my playlist", or "dedupe [Playlist Name]".

## Instructions
1. If the user doesn't provide a playlist ID, use `get_user_playlists` or `search_spotify(query=..., search_type='playlist')` to find the ID of the requested playlist.
2. Call the `dedupe_playlist(playlist_id)` tool using the identified `playlist_id`.
3. Report back to the user with the result of the deduplication process.

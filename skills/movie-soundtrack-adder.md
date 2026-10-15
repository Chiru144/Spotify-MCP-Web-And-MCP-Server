# Movie Soundtrack Adder

## Description
A single-purpose skill that searches for iconic songs from a specific movie and adds them to an existing Spotify playlist.

## When to use this skill
- When the user asks to "Add songs from [Movie Title] to my playlist".

## Instructions
1. Identify the movie name and the target playlist. If the playlist ID is unknown, search for it using `get_user_playlists`.
2. Call `add_movie_songs_to_playlist(playlist_id, movie_name, max_songs)`.
3. Inform the user how many songs from the movie were added to their playlist.

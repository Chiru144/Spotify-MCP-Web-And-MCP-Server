# Spotify Playlist Vibe Sorter

## Description
Handles requests to sort a playlist by audio features like energy, danceability, or valence. Spotify no longer provides audio features to Development Mode apps (2026 Web API changes), so these sorts are not possible; this skill explains that and offers the orderings that still work.

## When to use this skill
- When the user asks to "sort my playlist by energy", "make my playlist flow better", or "order [Playlist Name] by danceability".

## Instructions
1. Tell the user Spotify no longer gives this app audio features (energy, danceability, valence, tempo), so the playlist can't be sorted by them. Don't call `reorder_playlist_by_audio_features`; it only returns an "unavailable" message and leaves the playlist unchanged.
2. Offer what still works:
   - Move tracks or blocks of tracks by hand with `spotify_reorder_playlist(playlist_id, range_start, insert_before, range_length)`.
   - Shuffle the playlist with `shuffle_playlist(playlist_id)`.
   - Split it into per-artist playlists with `spotify_split_playlist_by_artist(playlist_id)`.
   - Build a new mood playlist with `spotify_discover_by_mood(mood=...)`, then add the tracks with `spotify_add_to_playlist`.
3. If the user picks one, find the playlist ID (using `get_user_playlists` if not provided) and run it.

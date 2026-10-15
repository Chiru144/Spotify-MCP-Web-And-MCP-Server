# Spotify Playlist Vibe Sorter

## Description
A single-purpose skill that reorders an existing playlist based on audio features like energy, danceability, or valence.

## When to use this skill
- When the user asks to "sort my playlist by energy", "make my playlist flow better", or "order [Playlist Name] by danceability".

## Instructions
1. Find the target playlist ID (using `get_user_playlists` if not provided).
2. Determine the requested audio feature (e.g., `energy`, `danceability`, `valence`, `tempo`).
3. Determine the order (e.g., `desc` for high-to-low, `asc` for low-to-high).
4. Call `reorder_playlist_by_audio_features(playlist_id, feature, order)`.
5. Inform the user that their playlist has been successfully sorted.

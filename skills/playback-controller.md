# Spotify Playback Controller

## Description
A single-purpose skill for controlling Spotify playback (play, pause, next, previous, volume).

## When to use this skill
- When the user asks to "play music", "pause", "skip this track", "go back", or "turn volume up/down".

## Instructions
1. Identify the user's intent: play, pause, next track, previous track, or volume adjustment.
2. Call the corresponding tool:
   - `play_track(device_id, uris, uri)` to start or resume playback.
   - `pause_playback(device_id)` to pause active playback.
   - `next_track(device_id)` to skip forward.
   - `previous_track(device_id)` to go back.
   - `set_volume(volume_percent, device_id)` to set volume (0 to 100).
3. If they ask to play a specific song, use `search_spotify(query=..., search_type='track')` to find the track URI first, then pass it to `play_track(uris=[uri])`.
4. Confirm the action simply and concisely (e.g., "Skipped to the next track!").

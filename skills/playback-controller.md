# Spotify Playback Controller

## Description
A single-purpose skill for controlling Spotify playback (play, pause, next, previous, volume).

## When to use this skill
- When the user asks to "play music", "pause", "skip this track", "go back", or "turn volume up/down".

## Instructions
1. Identify the user's intent: play, pause, next track, previous track, volume adjustment, repeat, shuffle, or queue.
2. Call the corresponding tool:
   - `spotify_status()`: Get connection and current playback state.
   - `spotify_now_playing()`: Get detailed currently playing song info.
   - `spotify_play(uri, uris, context_uri, device_id)`: Start or resume playback.
   - `spotify_pause(device_id)`: Pause active playback.
   - `spotify_resume(device_id)`: Resume active playback.
   - `spotify_skip_next(device_id)`: Skip forward.
   - `spotify_skip_previous(device_id)`: Skip backward.
   - `spotify_add_to_queue(uri, device_id)`: Add a track to playback queue.
   - `spotify_get_queue()`: View playback queue.
   - `spotify_get_devices()`: List active and available Spotify Connect devices.
   - `spotify_transfer_playback(device_id, play)`: Transfer playback to another device.
   - `spotify_set_volume(volume_percent, device_id)`: Set volume (0 to 100).
   - `spotify_seek(position_ms, device_id)`: Seek to timestamp.
   - `spotify_set_repeat(state, device_id)`: Set repeat ('track', 'context', or 'off').
   - `spotify_toggle_shuffle(state, device_id)`: Toggle shuffle mode on/off.
3. If they ask to play a specific song, use `search_spotify(query=..., search_type='track')` to find the track URI first, then pass it to `spotify_play(uri=...)`.
4. Confirm the action simply and concisely (e.g., "Skipped to the next track!").

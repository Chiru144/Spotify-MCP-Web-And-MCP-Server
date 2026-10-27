# Playback Queue & Flow Manager Skill

## Overview
Inspect, curate, and dynamically inject tracks into the user's upcoming Spotify playback queue.

## When to use this skill
- When the user asks "What's playing next?", "Add this to my queue", "Queue up some chill songs after this", or "Inspect queue".
- For managing upcoming song flow without altering permanent playlist order.

## Tools Included
- `get_queue()` / `spotify_get_queue()`: Retrieves the currently playing track and all queued upcoming songs.
- `add_to_queue(uri, device_id)` / `spotify_add_to_queue(uri, device_id)`: Enqueues a specific track URI at the top of the user's playback backlog.
- `get_current_playback()` / `spotify_now_playing()`: Checks current track metadata and millisecond progress.

## Workflow Instructions
1. Inspect the upcoming queue with `spotify_get_queue()`.
2. Format and display the upcoming tracks with artist names, track titles, and estimated remaining duration.
3. When queuing new tracks, call `spotify_add_to_queue(uri)` and confirm to the user that the song has been added to their active listening backlog.

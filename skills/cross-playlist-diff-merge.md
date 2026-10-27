# Cross-Playlist Diff & Merge Power Tools Skill

## Overview
Advanced multi-playlist operations enabling mathematical set operations (union, intersection, difference, and subset detection) across user playlists.

## When to use this skill
- When the user asks "What songs do these two playlists share?", "Merge these three playlists without duplicates", "Find unique tracks in playlist A vs B", or "Detect overlapping playlists".

## Tools Included
- `spotify_playlist_diff(playlist_id_a, playlist_id_b, strategy)`: Finds shared tracks, unique tracks in A, and unique tracks in B.
- `spotify_merge_playlists(playlist_ids, new_name, target_playlist_id)`: Combines multiple playlists into a unified destination list.
- `spotify_absorb_playlist(source_playlist_id, destination_playlist_id)`: Pulls only missing tracks from a source playlist into a destination playlist.
- `spotify_find_playlist_overlaps(threshold_percent)`: Scans all user playlists to identify significant cross-playlist duplicates.
- `spotify_find_playlist_subsets(threshold_percent)`: Detects if any user playlists are complete or near-complete subsets of another playlist.

## Workflow Instructions
1. For playlist comparisons: Call `spotify_playlist_diff()` and report shared songs and unique tracks in both lists.
2. For consolidation: Call `spotify_merge_playlists()` or `spotify_absorb_playlist()` to cleanly merge tracks without adding duplicates.
3. For library auditing: Run `spotify_find_playlist_subsets()` to suggest removing redundant playlists that are already contained in larger ones.

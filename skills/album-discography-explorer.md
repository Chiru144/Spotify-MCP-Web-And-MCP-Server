# Album Discography Explorer Skill

## Overview
Comprehensive discography exploration and album tracking for artists, covering full studio albums, EPs, singles, and compilations.

## When to use this skill
- When the user asks "Show all albums by [Artist]", "List [Artist]'s discography", "What year did [Album] come out?", or "Explore deep cuts on [Album]".

## Tools Included
- `spotify_get_artist_albums(artist_id, include_groups, limit, offset)`: Retrieves complete studio albums, singles, and appearances.
- `spotify_get_album(album_id)`: Fetches full tracklist, copyright details, record label, and release dates.
- `spotify_discover_deep_cuts(artist, album_name, limit)`: Identifies lesser-known, non-single album tracks.
- `spotify_get_artist(artist_id)`: Fetches the artist's profile and image (Spotify no longer returns genres, followers or popularity).

## Workflow Instructions
1. Retrieve artist albums using `spotify_get_artist_albums(artist_id)`.
2. Group albums by release year and type (Studio Album vs. Single vs. Compilation).
3. Inspect tracklists using `spotify_get_album(album_id)` to show total duration, track numbers, and audio preview availability.
4. If requested, uncover hidden gems using `spotify_discover_deep_cuts()`.

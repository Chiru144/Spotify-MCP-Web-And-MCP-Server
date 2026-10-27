# Cinema & Filmography Soundtrack Pipeline Skill

## Overview
Automated end-to-end pipeline bridging TMDB cinema filmographies and Spotify's audio catalog with automated 3-tier fallbacks (TMDB → DuckDuckGo → Wikipedia) and fuzzy tracklist discovery.

## When to use this skill
- When the user requests a complete playlist for an actor, film franchise, or director (e.g., "Make a playlist of all Cillian Murphy movies", "Create a Hans Zimmer score playlist").
- When movie soundtracks cannot be found via direct album titles and require track-level web discovery.

## Key Tools
- `create_actor_playlist(actor_name, playlist_name, max_movies, songs_per_movie, sort_by)`
- `search_actor_movies(actor_name, limit, sort_by)`
- `get_movie_songs(movie_name, limit)`
- `fetch_soundtrack_tracks(title, language, year, actor)`
- `search_duckduckgo(query, max_results)`

## Pipeline Protocol
1. **Filmography Extraction**: Query TMDB for top credited movies sorted by popularity or release date.
2. **Resilient Web Fallback**: If TMDB returns limited results, fall back to DuckDuckGo search or Wikipedia filmography parsing.
3. **Soundtrack Discovery**: Search Spotify for official OST albums (`OST`, `Soundtrack`, `Motion Picture`).
4. **Fuzzy Matching**: If no full album exists, search track titles with fuzzy film name matching.
5. **Playlist Synthesis**: Create or append to a Spotify playlist in batches of 100 with automatic deduplication.

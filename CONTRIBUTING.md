# Contributing

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Features & Technical Overview

### Features

- **Full Playback Control**: Play, pause, skip, seek to specific times, adjust volume, toggle repeat/shuffle, switch active devices (Premium), and manage your queue.
- **Smart Playlist Management**: Create playlists, combine, dedupe, and intelligently reorder tracks based on audio features (e.g., sorting by energy arcs or valence).
- **Search & Library Access**: Search for tracks, albums, artists, or playlists on Spotify, and access your saved playlists.
- **Deep Taste Analysis & Insights**: Retrieve top played songs and artists (short/medium/long term), analyze deep audio features (danceability, valence, energy), and map related artist networks.
- **TMDB Movie & Actor Search**: Look up rich biographical profiles for actors or get release details, overviews, and ratings for movies directly from The Movie Database.
- **Soundtrack Curator**: Integrated with TMDB and DuckDuckGo to automatically discover an actor's filmography, find the corresponding soundtracks, and build a dedicated Spotify playlist.
- **Soundtrack Staging Studio**: A local web interface to visualize and manage your curated soundtracks.

### Feature Comparison

Why use this server over standard Spotify MCP integrations? Most basic MCP servers only expose raw Spotify API endpoints without intelligence. This server bridges Spotify with TMDB cinema data, provides an interactive Web Soundtrack Curator Studio, and introduces advanced playlist curation algorithms:

| Feature / Capability | Spotify & TMDB MCP (This Project) | Standard Spotify MCPs |
|:---|:---:|:---:|
| **Actor Filmography Discovery** (TMDB + DuckDuckGo/Wikipedia fallbacks) | ✅ Yes | ❌ No |
| **End-to-End Actor Soundtrack Builder** (`create_actor_playlist` automated pipeline) | ✅ Yes | ❌ No |
| **Movie Soundtrack & Score Extraction** (Fuzzy matching + DuckDuckGo OST fallback) | ✅ Yes | ❌ No |
| **Soundtrack Staging Studio & Send Box** (Interactive Web UI with 30s track previews) | ✅ Yes | ❌ No |
| **Dual Paradigm Architecture** (Simultaneous Web Dashboard + FastMCP stdio/SSE server) | ✅ Yes | ❌ No |
| **Tkinter GUI OAuth Popup** (Desktop dialog preventing MCP stdio hangs/corruption) | ✅ Yes | ❌ No |
| **Smart Shuffle** (Random playlist mix & audio feature reordering by energy, valence, tempo) | ✅ Yes | ❌ No |
| **Smart Playlist Deduplication** (In-place duplicate song removal preserving first occurrence) | ✅ Yes | ❌ No |
| **Multi-Playlist Combiner** (Merges multiple playlists with auto-pagination & deduping) | ✅ Yes | ❌ No |
| **Multi-Seed Vibe & Mood Engine** (5 seeds + 6 tunable acoustic metric targets $0.0-1.0$) | ✅ Yes | ❌ No |
| **Web & Browser Song Tagger** (Autonomous agent research via DuckDuckGo to tag tracks) | ✅ Yes | ❌ No |
| **Artist Network & Taste Insights** (Related artist mapping + short/med/long listening analytics) | ✅ Yes | ❌ No |
| **Full Playback & Device Switching** (Spotify Connect controls + active hardware switching) | ✅ Yes | ⚠️ Partial (Raw playback only) |

#### Filmography & Cinema Soundtrack Pipeline

Unlike standard music-only integrations, this server deeply integrates TMDB (The Movie Database) with Spotify's library:
- **Actor Filmography Discovery**: Fetches full acting credits sorted by popularity or release date, with a resilient 3-tier fallback (TMDB $\rightarrow$ DuckDuckGo $\rightarrow$ Wikipedia).
- **Soundtrack Resolution**: Searches Spotify for official soundtracks and scores, falling back to track-level searches and DuckDuckGo tracklist discovery when albums are unlinked.
- **Automated Curation**: Creates dedicated actor or movie playlists in seconds (`create_actor_playlist`, `add_movie_songs_to_playlist`).

#### Vibe & Mood Sorting (audio_features)

Instead of arbitrary text labels, this server pulls standard audio feature scores ($0.0$ to $1.0$) for tracks:
- **Valence**: Positivity, musical cheerfulness, or sadness.
- **Energy**: Intensity, loudness, and fast-paced activity.
- **Danceability**: Rhythm stability, beat strength, and tempo consistency.
- **Acousticness & Instrumentalness**: Acoustic instrument usage vs. purely vocal/electronic elements.

Using these metrics, the AI calculates a track's "vibe profile". For example, a song with high valence and high energy is tagged by the LLM as "Upbeat Workout", while low valence and high acousticness is tagged as "Melancholic Chill".

#### Song & Type Suggestions (get_recommendations)

For song suggestions, it wraps Spotify's native Recommendations API, which accepts seed constraints (genres, audio targets, and seed tracks/artists).

### Tools & Agent Skills Catalog

This server registers **108 specialized FastMCP tools** across 7 domain modules, and packages **20 dedicated agent skills** for autonomous AI workflows:

#### 🎬 Cinema & Filmography Tools (`tools/search.py`, `tools/tmdb_helpers.py`)
- `create_actor_playlist(actor_name, ...)`: End-to-end automated pipeline to discover an actor's filmography, find the soundtracks on Spotify, and compile a dedicated playlist.
- `search_actor_movies(actor_name, limit, sort_by)`: Discovers an actor's full filmography via TMDB with DuckDuckGo and Wikipedia fallback engines.
- `get_actor_tmdb_profile(actor_name)`: Fetches rich actor biographical profiles, popularity metrics, and top known credits.
- `search_movie_tmdb(movie_name, limit)`: Searches TMDB for movie details, release year, ratings, and synopses.
- `get_movie_songs(movie_name, limit)`: Searches Spotify for soundtrack albums and songs from a movie with DuckDuckGo fallback assistance.
- `add_movie_songs_to_playlist(playlist_id, movie_name, max_songs)`: Finds songs from a movie on Spotify and appends them directly to an existing playlist.
- `search_duckduckgo(query, max_results)`: Autonomous web search engine for discovering movie tracklists, niche soundtracks, and music news.

#### 🎵 Smart Playlist Management & Power Tools (`tools/playlists.py`)
- Standard operations: `spotify_create_playlist`, `spotify_get_playlist`, `spotify_get_my_playlists`, `spotify_add_to_playlist`, `spotify_remove_from_playlist`, `spotify_reorder_playlist`, `spotify_update_playlist`, `spotify_follow_playlist`, `spotify_unfollow_playlist`, `spotify_get_playlist_cover`, `spotify_check_playlist_followers`.
- Algorithmic tools: `shuffle_playlist`, `reorder_playlist_by_audio_features`, `dedupe_playlist`, `combine_playlists`.
- Power tools: `spotify_merge_playlists`, `spotify_split_playlist_by_artist`, `spotify_deduplicate_playlist`, `spotify_export_playlist`, `spotify_playlist_diff`, `spotify_find_playlist_overlaps`, `spotify_find_playlist_subsets`, `spotify_absorb_playlist`.

#### 🔍 Catalog & Entity Inspection Tools (`tools/browse.py`)
- `spotify_get_track(track_id)`: Fetches complete track metadata, album info, and audio previews.
- `spotify_get_album(album_id)`: Inspects full album tracks, release dates, and copyright labels.
- `spotify_get_artist(artist_id)`: Retrieves artist profiles, genres, follower counts, and popularity.
- `spotify_get_artist_albums(artist_id)`: Lists full artist discography (albums, singles, appearances).
- `spotify_get_user(user_id)`: Inspects public Spotify user profiles.

#### 📚 Library & Saved Media Tools (`tools/library.py`)
- Saved tracks: `spotify_get_saved_tracks`, `spotify_save_tracks`, `spotify_remove_saved_tracks`, `spotify_check_saved_tracks`.
- Saved albums: `spotify_get_saved_albums`, `spotify_save_albums`, `spotify_remove_saved_albums`, `spotify_check_saved_albums`.

#### ✨ Taste Analysis & Recommendation Engine (`tools/taste.py`, `tools/search.py`)
- `spotify_get_recommendations` / `get_recommendations`: Multi-seed engine with 6 fine-grained acoustic targets.
- `spotify_top_tracks` / `get_user_top_tracks`: Top played songs across short, medium, and long-term timeframes.
- `spotify_top_artists` / `get_user_top_artists`: Top artists across short, medium, and long-term history.
- `spotify_recently_played`: Retrieves playback history with timestamps.
- `spotify_listening_patterns`: Analyzes peak listening hours and temporal habits.
- `spotify_taste_profile`: Comprehensive acoustic fingerprint across danceability, energy, and valence.
- `spotify_playlist_compare`: Comparative audio profile between two playlists.
- `spotify_playlist_freshness`: Evaluates track age and release distribution within a playlist.
- `spotify_related_artists` / `get_artist_network`: Maps related artist networks and sub-genres.

#### 🎛️ Playback & Hardware Controls (`tools/playback.py`)
- Playback states: `get_current_playback`, `spotify_get_playback_state`, `spotify_currently_playing`.
- Hardware & Connect: `get_available_devices`, `transfer_playback`.
- Track controls: `play_track`, `pause_playback`, `next_track`, `previous_track`, `seek_to_position`, `set_volume`, `set_repeat_mode`, `toggle_shuffle`.
- Queue management: `add_to_queue`, `get_user_queue`.
- Visual UI launcher: `open_soundtrack_studio`.

#### 🤖 Autonomous Agent Skills (`skills/`)
These skills are automatically injected into connecting MCP clients on startup:
- `actor-filmography-searcher.md`: Guides the AI to query TMDB and present an actor's filmography.
- `movie-soundtrack-adder.md`: Specialized agent workflow to identify movie tracks and append to playlists.
- `playlist-vibe-sorter.md`: Teaches the agent to re-sort playlists according to musical flow.
- `playlist-deduplicator.md`: Step-by-step cleanup protocol to identify duplicate tracks and sanitize playlists.
- `playlist-operations.md`: Standard playlist management best practices and batching rules.
- `playlist-power-tools.md`: Multi-playlist merging, subset extraction, and diff analysis.
- `taste-analyzer.md`: Guides AI to examine short/medium/long-term listening data and provide profiles.
- `playback-controller.md`: Natural language translation for playback control and multi-device routing.
- `browser-song-tagger.md`: Autonomous agent skill using DuckDuckGo to research obscure songs and tag playlists.
- `search-recommendations.md`: Discovery workflow using multi-seed targets, related artists, and genres.
- `stats-analytics.md`: Deep taste profiling, freshness scoring, and listening pattern analytics.
- `library-operations.md`: Library management for saved tracks and albums.
- `browse-inspection.md`: Deep inspection of Spotify catalog entities (tracks, albums, artists, users).

## We Develop with Github
We use github to host code, to track issues and feature requests, as well as accept pull requests.

## We Use Github Flow
All Code Changes Happen Through Pull Requests.

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Any contributions you make will be under the MIT Software License
In short, when you submit code changes, your submissions are understood to be under the same [MIT License](LICENSE.md) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issues](https://github.com/Chiru144/Spotify-MCP-Web-MCP-Server/issues)
We use GitHub issues to track public bugs. Report a bug by opening a new issue.

## Write bug reports with detail, background, and sample code
**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## License
By contributing, you agree that your contributions will be licensed under its MIT License.

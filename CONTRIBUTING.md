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

This server registers **43 specialized FastMCP tools** and packages **7 dedicated agent skills** for autonomous AI workflows:

#### 🎬 Cinema & Filmography Tools
- `create_actor_playlist(actor_name, ...)`: End-to-end automated pipeline to discover an actor's filmography, find the soundtracks on Spotify, and compile a dedicated playlist.
- `search_actor_movies(actor_name, limit, sort_by)`: Discovers an actor's full filmography via TMDB with DuckDuckGo and Wikipedia fallback engines.
- `get_actor_tmdb_profile(actor_name)`: Fetches rich actor biographical profiles, popularity metrics, and top known credits.
- `search_movie_tmdb(movie_name, limit)`: Searches TMDB for movie details, release year, ratings, and synopses.
- `get_movie_songs(movie_name, limit)`: Searches Spotify for soundtrack albums and songs from a movie with DuckDuckGo fallback assistance.
- `add_movie_songs_to_playlist(playlist_id, movie_name, max_songs)`: Finds songs from a movie on Spotify and appends them directly to an existing playlist.
- `search_duckduckgo(query, max_results)`: Autonomous web search engine for discovering movie tracklists, niche soundtracks, and music news.

#### 🎵 Smart Playlist Management Tools
- `create_playlist(name, description, public)`: Creates a new Spotify playlist for the user.
- `shuffle_playlist(playlist_id)`: Mixes and shuffles all songs in a playlist into a completely new random permutation.
- `reorder_playlist_by_audio_features(playlist_id, feature, order)`: Sorts tracks by acoustic properties (`energy`, `valence`, `danceability`, `tempo`, etc.) in ascending or descending order.
- `dedupe_playlist(playlist_id)`: In-place scan and removal of duplicate songs from a playlist, preserving the first instance.
- `combine_playlists(playlist_ids, new_name, description)`: Merges multiple playlists into a unified, deduplicated playlist with automated pagination.
- `add_tracks_to_playlist(playlist_id, track_uris)`: Adds track URIs in batches of 100 with deduplication checks.
- `get_user_playlists(limit)`: Retrieves user-owned playlists with track counts and URIs.
- `get_playlist_tracks(playlist_id, limit, offset)`: Inspects songs currently inside a playlist.
- `update_playlist(playlist_id, name, description, public)`: Updates playlist metadata.
- `remove_tracks_from_playlist(playlist_id, uris)`: Removes specific track URIs from a playlist.

#### ✨ Taste Analysis & Recommendation Engine
- `get_recommendations(seeds..., targets...)`: Multi-seed recommendation engine supporting up to 5 combined seeds (genres, tracks, artists) and 6 fine-grained acoustic targets (`valence`, `energy`, `danceability`, `acousticness`, `instrumentalness`, `tempo`).
- `get_audio_features(track_uris)`: Extracts deep acoustic scores ($0.0 - 1.0$), BPM, key, and musical mode for up to 100 tracks.
- `get_user_top_tracks(limit, time_range)`: Retrieves top songs across short (~4 weeks), medium (~6 months), and long-term (years) horizons.
- `get_user_top_artists(limit, time_range)`: Retrieves top artists across short, medium, and long-term listening history.
- `get_artist_network(artist_name_or_id)`: Maps related artist networks and sub-genres.
- `get_saved_tracks(limit, offset)`: Queries songs saved in the user's personal Spotify Library.
- `search_spotify(query, search_type, limit)`: Flexible search across Spotify tracks, albums, artists, or playlists.

#### 🎛️ Playback & Hardware Controls
- `get_current_playback()`: Returns currently playing track, artist, album, progress, and active device.
- `play_track(device_id, uris, uri)`: Starts or resumes music playback on Spotify.
- `pause_playback(device_id)`: Pauses active music playback.
- `next_track(device_id)` / `previous_track(device_id)`: Skips tracks forward or backward.
- `seek_to_position(position_ms, device_id)`: Seeks to a specific millisecond in the active track.
- `set_volume(volume_percent, device_id)`: Sets playback volume level (0 to 100%).
- `set_repeat_mode(state, device_id)`: Sets repeat mode (`off`, `track`, `context`).
- `toggle_shuffle(state, device_id)`: Toggles Spotify player shuffle mode.
- `get_available_devices()`: Lists active and discovered Spotify Connect hardware devices.
- `transfer_playback(device_id, play)`: Seamlessly switches audio playback to another device.
- `add_to_queue(uri, device_id)`: Enqueues a song to the user's upcoming playback queue.
- `get_user_queue()`: Inspects currently playing track and the queue.
- `open_soundtrack_studio()`: Launches or opens the visual Soundtrack Curator & Staging Studio web UI.

#### 🤖 Autonomous Agent Skills (`skills/`)
These skills are automatically injected into connecting MCP clients on startup:
- `actor-filmography-searcher.md`: Guides the AI to query TMDB and present an actor's filmography with character roles and release years.
- `movie-soundtrack-adder.md`: Specialized agent workflow to identify movie tracks and append them into user playlists.
- `playlist-vibe-sorter.md`: Teaches the agent to re-sort playlists according to musical flow (e.g. build up energy or cool down).
- `playlist-deduplicator.md`: Step-by-step cleanup protocol to identify duplicate tracks and sanitize playlists in-place.
- `taste-analyzer.md`: Guides AI to examine short/medium/long-term listening data and provide personalized listening profiles.
- `playback-controller.md`: Natural language translation for playback control and multi-device routing.
- `browser-song-tagger.md`: Autonomous agent skill using DuckDuckGo web search to research obscure song genres/cultural tags and auto-tag Spotify playlists.

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

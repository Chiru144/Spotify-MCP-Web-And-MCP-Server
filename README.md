# Spotify & TMDB Web MCP Server

[![M8ven Score](https://m8ven.ai/badge/mcp/chiru144/spotify-mcp-web-mcp-server)](https://m8ven.ai/mcp/chiru144/spotify-mcp-web-mcp-server)
[![MCP Tools](https://img.shields.io/badge/MCP%20Tools-43%20Registered-1DB954?style=flat&logo=spotify)](tools/)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-7%20Packaged-8A2BE2?style=flat)](skills/)

This repository contains a FastMCP application integrating Spotify and TMDB (The Movie Database), powered by **43 registered MCP tools** and **7 autonomous agent skills**. It allows you to build custom soundtracks, automate playlist curation, explore listening taste, and interact with a local web-based Soundtrack Curator & Staging Studio.

## Highlights

- **43 FastMCP Tools & 7 Agent Skills**: Comprehensive toolkit covering cinema filmography discovery, smart playlist management, acoustic feature reordering, deep taste analytics, and complete Spotify Connect hardware control.
- **Cross-Domain Media Blending**: Bridges cinema and music by letting your AI dynamically look up movies, cast, or crew on TMDB and map them into custom Spotify playlists.
- **Dual Web & Agent Design**: Built on FastAPI/Uvicorn, it functions as both a flexible web endpoint and an MCP server, supporting remote hosting and multiple networked AI connections.
- **Modular Architecture**: The codebase is cleanly separated into specialized tool modules (`playback.py`, `playlists.py`, `taste.py`, `search.py`), making it highly scalable and completely unit-testable.

## Features

- **Full Playback Control**: Play, pause, skip, seek to specific times, adjust volume, toggle repeat/shuffle, switch active devices (Premium), and manage your queue.
- **Smart Playlist Management**: Create playlists, combine, dedupe, and intelligently reorder tracks based on audio features (e.g., sorting by energy arcs or valence).
- **Search & Library Access**: Search for tracks, albums, artists, or playlists on Spotify, and access your saved playlists.
- **Deep Taste Analysis & Insights**: Retrieve top played songs and artists (short/medium/long term), analyze deep audio features (danceability, valence, energy), and map related artist networks.
- **TMDB Movie & Actor Search**: Look up rich biographical profiles for actors or get release details, overviews, and ratings for movies directly from The Movie Database.
- **Soundtrack Curator**: Integrated with TMDB and DuckDuckGo to automatically discover an actor's filmography, find the corresponding soundtracks, and build a dedicated Spotify playlist.
- **Soundtrack Staging Studio**: A local web interface to visualize and manage your curated soundtracks.

## Feature Comparison

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

### Filmography & Cinema Soundtrack Pipeline

Unlike standard music-only integrations, this server deeply integrates TMDB (The Movie Database) with Spotify's library:
- **Actor Filmography Discovery**: Fetches full acting credits sorted by popularity or release date, with a resilient 3-tier fallback (TMDB $\rightarrow$ DuckDuckGo $\rightarrow$ Wikipedia).
- **Soundtrack Resolution**: Searches Spotify for official soundtracks and scores, falling back to track-level searches and DuckDuckGo tracklist discovery when albums are unlinked.
- **Automated Curation**: Creates dedicated actor or movie playlists in seconds (`create_actor_playlist`, `add_movie_songs_to_playlist`).


### Vibe & Mood Sorting (audio_features)

Instead of arbitrary text labels, this server pulls standard audio feature scores ($0.0$ to $1.0$) for tracks:
- **Valence**: Positivity, musical cheerfulness, or sadness.
- **Energy**: Intensity, loudness, and fast-paced activity.
- **Danceability**: Rhythm stability, beat strength, and tempo consistency.
- **Acousticness & Instrumentalness**: Acoustic instrument usage vs. purely vocal/electronic elements.

Using these metrics, the AI calculates a track's "vibe profile". For example, a song with high valence and high energy is tagged by the LLM as "Upbeat Workout", while low valence and high acousticness is tagged as "Melancholic Chill".

### Song & Type Suggestions (get_recommendations)

For song suggestions, it wraps Spotify's native Recommendations API, which accepts seed constraints (genres, audio targets, and seed tracks/artists).

> 📖 **Deep Dive & Parameter Guide:**
> For the complete breakdown of core inputs, prompt scenarios (Scenario A: Vibe-Based Matching, Scenario B: Acoustic Type Matching), and capability status tables, see the interactive **[Web Tool Guide](http://127.0.0.1:8000/guide)** (`/guide`).

## Tools & Agent Skills Catalog

This server registers **43 specialized FastMCP tools** and packages **7 dedicated agent skills** for autonomous AI workflows:

### 🎬 Cinema & Filmography Tools
- `create_actor_playlist(actor_name, ...)`: End-to-end automated pipeline to discover an actor's filmography, find the soundtracks on Spotify, and compile a dedicated playlist.
- `search_actor_movies(actor_name, limit, sort_by)`: Discovers an actor's full filmography via TMDB with DuckDuckGo and Wikipedia fallback engines.
- `get_actor_tmdb_profile(actor_name)`: Fetches rich actor biographical profiles, popularity metrics, and top known credits.
- `search_movie_tmdb(movie_name, limit)`: Searches TMDB for movie details, release year, ratings, and synopses.
- `get_movie_songs(movie_name, limit)`: Searches Spotify for soundtrack albums and songs from a movie with DuckDuckGo fallback assistance.
- `add_movie_songs_to_playlist(playlist_id, movie_name, max_songs)`: Finds songs from a movie on Spotify and appends them directly to an existing playlist.
- `search_duckduckgo(query, max_results)`: Autonomous web search engine for discovering movie tracklists, niche soundtracks, and music news.

### 🎵 Smart Playlist Management Tools
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

### ✨ Taste Analysis & Recommendation Engine
- `get_recommendations(seeds..., targets...)`: Multi-seed recommendation engine supporting up to 5 combined seeds (genres, tracks, artists) and 6 fine-grained acoustic targets (`valence`, `energy`, `danceability`, `acousticness`, `instrumentalness`, `tempo`).
- `get_audio_features(track_uris)`: Extracts deep acoustic scores ($0.0 - 1.0$), BPM, key, and musical mode for up to 100 tracks.
- `get_user_top_tracks(limit, time_range)`: Retrieves top songs across short (~4 weeks), medium (~6 months), and long-term (years) horizons.
- `get_user_top_artists(limit, time_range)`: Retrieves top artists across short, medium, and long-term listening history.
- `get_artist_network(artist_name_or_id)`: Maps related artist networks and sub-genres.
- `get_saved_tracks(limit, offset)`: Queries songs saved in the user's personal Spotify Library.
- `search_spotify(query, search_type, limit)`: Flexible search across Spotify tracks, albums, artists, or playlists.

### 🎛️ Playback & Hardware Controls
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

### 🤖 Autonomous Agent Skills (`skills/`)
These skills are automatically injected into connecting MCP clients on startup:
- `actor-filmography-searcher.md`: Guides the AI to query TMDB and present an actor's filmography with character roles and release years.
- `movie-soundtrack-adder.md`: Specialized agent workflow to identify movie tracks and append them into user playlists.
- `playlist-vibe-sorter.md`: Teaches the agent to re-sort playlists according to musical flow (e.g. build up energy or cool down).
- `playlist-deduplicator.md`: Step-by-step cleanup protocol to identify duplicate tracks and sanitize playlists in-place.
- `taste-analyzer.md`: Guides AI to examine short/medium/long-term listening data and provide personalized listening profiles.
- `playback-controller.md`: Natural language translation for playback control and multi-device routing.
- `browser-song-tagger.md`: Autonomous agent skill using DuckDuckGo web search to research obscure song genres/cultural tags and auto-tag Spotify playlists.

## Prerequisites

Before running the application, make sure you have the following installed:
- [Python 3.10+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)

You will also need Developer API Keys for:
- [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- [TMDB API](https://developer.themoviedb.org/docs/getting-started)

## Installation & Setup

Follow these steps to get the project running locally:

### 1. Clone the repository

```bash
git clone https://github.com/Chiru144/Spotify-MCP-Web-MCP-Server.git
cd Spotify-MCP-Web-MCP-Server
```

### 2. Create and activate a Virtual Environment

It is recommended to use a virtual environment to manage dependencies.

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

Install the required Python packages from the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a file named `.env` in the root of the project directory. You need to add your API credentials from Spotify and TMDB.

Here is the `.env` template:

```ini
# Spotify Credentials
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
SPOTIPY_REDIRECT_URI=http://localhost:8080 # Or your configured redirect URI

# TMDB Credentials
TMDB_API_KEY=your_tmdb_api_key
TMDB_READ_ACCESS_TOKEN=your_tmdb_read_access_token
TMDB_ACCESS_TOKEN=your_tmdb_access_token

# Optional configuration
OPEN_BROWSER=true
```

Make sure to replace `your_*` placeholders with the actual keys from your developer dashboards.

## Running the Application

There are two entry points to run the server, depending on your use case:

### 1. `server.py` (Development & Web App Focus)

Start the MCP server and background web app simultaneously by running:

```bash
python server.py
```

The application will start, and the web interface should automatically open in your default browser at `http://127.0.0.1:8000`.

### 2. `mcp.py` (MCP Client Integration Focus)

If you are running this project as a tool inside an MCP host (like Cursor, VSCode, or Claude Desktop), you should use `mcp.py`:

```bash
python mcp.py
```

**Why `mcp.py`?** Standard MCP uses standard input/output (`stdio`) for communication. When Spotify requires you to log in for the first time, it normally pauses and asks you to paste a redirect URL in the terminal. This breaks the MCP protocol. `mcp.py` solves this by launching a **Tkinter GUI popup** for the Spotify authentication process, ensuring `stdio` remains clean and unblocked for the MCP client.

## API Limits

Please keep in mind the rate limits imposed by the external APIs used in this project:

- **Spotify Web API**: Spotify uses a dynamic rate limit based on a rolling window. If you make too many requests in a short period (such as aggressively searching or curating massive playlists), you will receive a `429 Too Many Requests` response. The app may need to back off and try again later.
- **TMDB API**: The Movie Database allows up to **50 requests per second**. This is generally quite generous for normal usage, but batch queries or rapid concurrent lookups could potentially hit this limit.

## MCP Integration

This project is built using `fastmcp`. Once running via `stdio` (or SSE if configured), it can be seamlessly consumed by other MCP clients.

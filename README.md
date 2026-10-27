# Spotify & TMDB Web MCP Server

[![M8ven Score](https://m8ven.ai/badge/mcp/chiru144/spotify-mcp-web-mcp-server)](https://m8ven.ai/mcp/chiru144/spotify-mcp-web-mcp-server)
[![MCP Tools](https://img.shields.io/badge/MCP%20Tools-108%20Registered-1DB954?style=flat&logo=spotify)](tools/)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-20%20Packaged-8A2BE2?style=flat)](skills/)

This repository contains a FastMCP application integrating Spotify and TMDB (The Movie Database), powered by **108 registered MCP tools** and **20 autonomous agent skills**. It allows you to build custom soundtracks, automate playlist curation, explore listening taste, and interact with a local web-based Soundtrack Curator & Staging Studio.

## Highlights

- **108 FastMCP Tools & 20 Agent Skills**: Comprehensive toolkit covering cinema filmography discovery, smart playlist management, acoustic feature reordering, deep taste analytics, catalog browsing, library management, and complete Spotify Connect hardware control.
- **PKCE OAuth & Flexible Auth**: Built-in Spotify PKCE authentication removes the need for a client secret via simple one-click browser login, alongside intelligent TMDB authentication accepting either an API Key or Read Access Token.
- **Cross-Domain Media Blending**: Bridges cinema and music by letting your AI dynamically look up movies, cast, or crew on TMDB and map them into custom Spotify playlists.
- **Dual Web & Agent Design**: Built on FastAPI/Uvicorn, it functions as both a flexible web endpoint and an MCP server, supporting remote hosting and multiple networked AI connections.
- **Modular Architecture**: The codebase is cleanly separated into specialized tool modules (`playback.py`, `playlists.py`, `taste.py`, `search.py`, `library.py`, `browse.py`, `web_app.py`), making it highly scalable and completely unit-testable.

## Features & Capabilities

For an in-depth breakdown of features, feature comparison tables, the cinema filmography pipeline, audio feature calculations, the complete 108-tool catalog, and 20 autonomous agent skills, please refer to **[CONTRIBUTING.md](CONTRIBUTING.md#features--technical-overview)**.

## Complete FastMCP Tools Catalog (108 Registered Tools)

The FastMCP server exposes **108 registered tools** organized across 7 specialized domain modules in `tools/`:

<details>
<summary><b>Cinema, Filmography & Search Tools</b> (<code>tools/search.py</code> &mdash; 16 tools)</summary>

| Tool Name | Description |
| :--- | :--- |
| fetch_soundtrack_tracks | Searches Spotify for movie soundtrack tracks using titles, language, release year, or actor name with fuzzy matching. |
| get_actor_tmdb_profile | Get rich biographical and career profile details for an actor from TMDB. |
| get_movie_songs | Search Spotify for soundtrack albums and songs from a movie with DuckDuckGo fallback assistance. |
| search_actor_movies | Discover the full filmography for an actor using TMDB (with DDG and Wikipedia fallbacks). |
| search_duckduckgo | Perform a web search using DuckDuckGo to look up movie news, filmographies, or sound tracks. |
| search_movie_tmdb | Search TMDB for movie information, release year, ratings, and overview. |
| search_singers | Search for singers, musical artists, or bands on Spotify. |
| search_songs | Search for songs or tracks on Spotify with detailed track metadata. |
| search_spotify | Search for songs, albums, artists, or playlists on Spotify. |
| spotify_discover_by_artist | Generate track recommendations derived from related artist networks. |
| spotify_discover_by_mood | Discover tracks using target audio parameters (valence, energy, tempo, etc.) or mood presets. |
| spotify_discover_deep_cuts | Discover non-single, album-only deep cut tracks from an artist or album. |
| spotify_genre_explorer | Browse and sample tracks across specific seed genres or list all available genre seeds. |
| spotify_get_recommendations | Direct wrapper for Spotify Recommendations API using seeds and target audio features. |
| spotify_related_artists | Find artists similar to a target artist. |
| spotify_search | Search Spotify catalog for tracks, artists, albums, or playlists. |

</details>

<details>
<summary><b>Smart Playlist Management & Power Tools</b> (<code>tools/playlists.py</code> &mdash; 33 tools)</summary>

| Tool Name | Description |
| :--- | :--- |
| add_movie_songs_to_playlist | Find songs for a specific movie on Spotify and add them directly to an existing playlist. |
| add_songs_to_playlist | Add a list of Spotify song URIs to an existing playlist. |
| add_tracks_to_playlist | Add a list of Spotify song URIs to an existing playlist. |
| combine_playlists | Combines multiple Spotify playlists into a single new playlist. |
| create_actor_playlist | End-to-End Pipeline: Discover an actor's filmography via TMDB/DDG, locate songs on Spotify, |
| create_playlist | Create a new Spotify playlist for the user. |
| dedupe_playlist | Removes all duplicate songs from a Spotify playlist, keeping only the first occurrence of each song. |
| get_playlist_tracks | Get the tracks currently inside a specific playlist. |
| get_user_playlists | Get the current user's playlists with song counts. |
| remove_tracks_from_playlist | Remove one or more tracks from a playlist by their URIs. |
| reorder_playlist_by_audio_features | Smart Reorder: Sorts a user's playlist by a given audio feature (energy, valence, danceability, etc). |
| shuffle_playlist | Mix and shuffle all songs in a Spotify playlist into a completely new random order. |
| spotify_absorb_playlist | Pull only missing/unique tracks from a source playlist into a destination playlist. |
| spotify_add_to_playlist | Append tracks to an existing playlist. |
| spotify_check_playlist_followers | Check if specific users follow a playlist. |
| spotify_create_playlist | Create a new empty playlist. |
| spotify_deduplicate_playlist | Scan and strip out duplicate tracks from a playlist. |
| spotify_export_playlist | Export full playlist data, track metadata, and audio features to structured JSON. |
| spotify_find_playlist_overlaps | Scan all user playlists to identify cross-playlist overlaps. |
| spotify_find_playlist_subsets | Detect if any user playlists are complete or near-complete subsets of another playlist. |
| spotify_follow_playlist | Add a playlist to the user's library (Follow). |
| spotify_get_my_playlists | List user's created and saved playlists. |
| spotify_get_playlist | Fetch details and tracks of a specific playlist. |
| spotify_get_playlist_cover | Get the image URL for a playlist cover. |
| spotify_get_playlist_tracks | Paginate through tracks in a playlist. |
| spotify_merge_playlists | Combine multiple playlists into a single new or existing playlist. |
| spotify_playlist_diff | Compare two playlists to find unique and shared tracks. |
| spotify_remove_from_playlist | Remove specific tracks from a playlist. |
| spotify_reorder_playlist | Move or reorder track positions in a playlist. |
| spotify_split_playlist_by_artist | Separate tracks in a playlist into sub-playlists by artist. |
| spotify_unfollow_playlist | Remove a playlist from the user's library (Unfollow/Delete). |
| spotify_update_playlist | Modify playlist name, description, or privacy settings. |
| update_playlist | Update a playlist's name, description, or public status. |

</details>

<details>
<summary><b>Playback & Spotify Connect Hardware Controls</b> (<code>tools/playback.py</code> &mdash; 31 tool)</summary>

| Tool Name | Description |
| :--- | :--- |
| add_to_queue | Add a song to the user's playback queue. |
| get_available_devices | Get information about a user's available devices. |
| get_current_playback | Get information about the user's current playback state, active song, and active device. |
| get_queue | Get the user's current playback queue. |
| next_song | Skip to the next song in the queue. |
| next_track | Skip to the next song in the queue. |
| pause_playback | Pause the current Spotify playback. |
| play_song | Resume playback or play a specific song/album/playlist by URI. |
| play_track | Start or resume playback. |
| previous_song | Skip to the previous song. |
| previous_track | Skip to the previous song. |
| seek_playback | Seeks to the given position in the user's currently playing track. |
| set_repeat_mode | Set the repeat mode for the user's playback. |
| set_shuffle | Toggle shuffle for the user's playback. |
| set_volume | Set the playback volume. |
| spotify_add_to_queue | Add a track URI to the user's current playback queue. |
| spotify_get_devices | List available Spotify Connect devices. |
| spotify_get_queue | View current playback queue and upcoming tracks. |
| spotify_now_playing | Fetch detailed information about the currently playing track. |
| spotify_pause | Pause playback. |
| spotify_play | Start or resume playback (accepts track, album, or playlist URIs). |
| spotify_resume | Resume active playback. |
| spotify_seek | Seek to a specific timestamp in the current track. |
| spotify_set_repeat | Set repeat mode (off, context, or track). |
| spotify_set_volume | Set playback volume (0–100). |
| spotify_skip_next | Skip to the next track in the queue. |
| spotify_skip_previous | Skip back to the previous track. |
| spotify_status | Get current connection status and basic playback state. |
| spotify_toggle_shuffle | Toggle shuffle mode on or off. |
| spotify_transfer_playback | Transfer active playback to another connected device. |
| transfer_playback | Transfer playback to a new device. |

</details>

<details>
<summary><b>Taste Analytics, Audio Features & Insights</b> (<code>tools/taste.py</code> &mdash; 14 tools)</summary>

| Tool Name | Description |
| :--- | :--- |
| get_artist_network | Map an artist's network by fetching related artists. |
| get_audio_features | Get audio features (danceability, energy, valence, etc) for multiple tracks. |
| get_recommendations | Get track recommendations based on seeds and audio features. |
| get_saved_tracks | Get tracks from the user's Library (Saved Tracks). |
| get_user_top_artists | Get the current user's top artists over a specified period. |
| get_user_top_songs | Get the current user's top songs over a specified period. |
| get_user_top_tracks | Get the current user's top songs over a specified period. |
| spotify_listening_patterns | Analyze listening volume distributions across hours and days. |
| spotify_playlist_compare | Compare multi-playlist audio feature distributions side-by-side. |
| spotify_playlist_freshness | Sort playlists by last update timestamp to identify stale lists. |
| spotify_recently_played | Fetch recent track listening history. |
| spotify_taste_profile | Generate an overview of genre diversity and niche artist affinity. |
| spotify_top_artists | Fetch user's top artists over short, medium, or long term. |
| spotify_top_tracks | Fetch user's top tracks over short, medium, or long term. |

</details>

<details>
<summary><b>Saved Library & Collection Management</b> (<code>tools/library.py</code> &mdash; 8 tools)</summary>

| Tool Name | Description |
| :--- | :--- |
| spotify_check_saved_albums | Verify whether specific albums exist in the current user's library. |
| spotify_check_saved_tracks | Verify whether specific tracks exist in the current user's Liked Songs library. |
| spotify_get_saved_albums | Fetch albums saved in the current user's library. |
| spotify_get_saved_tracks | List tracks saved in the current user's Liked Songs library. |
| spotify_remove_saved_albums | Remove one or more albums from the current user's library. |
| spotify_remove_saved_tracks | Remove one or more tracks from the current user's Liked Songs library. |
| spotify_save_albums | Save one or more albums to the current user's library. |
| spotify_save_tracks | Save one or more tracks to the current user's Liked Songs library. |

</details>

<details>
<summary><b>Catalog & Entity Inspection (Browse)</b> (<code>tools/browse.py</code> &mdash; 5 tools)</summary>

| Tool Name | Description |
| :--- | :--- |
| spotify_get_album | Inspect full album details including copyrights, label, release date, and complete tracklist. |
| spotify_get_artist | Inspect artist details including genres, follower count, popularity, and profile images. |
| spotify_get_artist_albums | Get all albums, singles, and compilations released by a specific artist. |
| spotify_get_track | Inspect full track metadata including ISRC, popularity, audio preview URL, and album details. |
| spotify_get_user | Fetch public profile information and public playlists for any Spotify user. |

</details>

<details>
<summary><b>Visual Soundtrack Studio Launcher</b> (<code>tools/web_app.py</code> &mdash; 1 tool)</summary>

| Tool Name | Description |
| :--- | :--- |
| open_soundtrack_studio | Launch or retrieve the URL for the Soundtrack Curator & Staging Studio web application. |

</details>


## Packaged Autonomous Agent Skills (20 Skills)

In addition to individual FastMCP tools, this repository packages **20 autonomous agent skills** in the [skills/](skills/) folder. These markdown guides teach connecting AI models how to orchestrate multi-step workflows, perform domain-specific music reasoning, execute fallbacks, and interact with users:

| Skill Document | Title | Purpose & Workflow |
| :--- | :--- | :--- |
| [actor-filmography-searcher.md](skills/actor-filmography-searcher.md) | **Actor Filmography Searcher** | A single-purpose skill that searches for an actor and returns a list of movies they have starred in using TMDB. |
| [album-discography-explorer.md](skills/album-discography-explorer.md) | **Album Discography Explorer Skill** | Comprehensive discography exploration and album tracking for artists, covering full studio albums, EPs, singles, and compilations. |
| [browse-inspection.md](skills/browse-inspection.md) | **Catalog & Entity Inspection (Browse) Skill** | Deep-dive inspection and metadata analysis of Spotify catalog entities, including tracks, albums, artists, artist discographies, and public user profiles. |
| [browser-song-tagger.md](skills/browser-song-tagger.md) | **Web & Browser Song Tagger** | An agent skill that researches a specific song via the web/browser to find its genres, cultural tags, or metadata, and then uses that information to effectively organize the song within Spotify (e.g., adding it to a genre-specific playlist or updating playlist metadata). |
| [cinema-soundtrack-pipeline.md](skills/cinema-soundtrack-pipeline.md) | **Cinema & Filmography Soundtrack Pipeline Skill** | Automated end-to-end pipeline bridging TMDB cinema filmographies and Spotify's audio catalog with automated 3-tier fallbacks (TMDB → DuckDuckGo → Wikipedia) and fuzzy tracklist discovery. |
| [cross-playlist-diff-merge.md](skills/cross-playlist-diff-merge.md) | **Cross-Playlist Diff & Merge Power Tools Skill** | Advanced multi-playlist operations enabling mathematical set operations (union, intersection, difference, and subset detection) across user playlists. |
| [hardware-connect-switcher.md](skills/hardware-connect-switcher.md) | **Spotify Connect & Hardware Switcher Skill** | Control, discover, and route active playback across Spotify Connect hardware devices (smartphones, computers, smart speakers, TVs, and receivers). |
| [library-operations.md](skills/library-operations.md) | **Library & Liked Media Operations Skill** | Comprehensive management of the user's Spotify personal library, including Liked Songs (saved tracks) and saved album collections. |
| [movie-soundtrack-adder.md](skills/movie-soundtrack-adder.md) | **Movie Soundtrack Adder** | A single-purpose skill that searches for iconic songs from a specific movie and adds them to an existing Spotify playlist. |
| [playback-controller.md](skills/playback-controller.md) | **Spotify Playback Controller** | A single-purpose skill for controlling Spotify playback (play, pause, next, previous, volume). |
| [playlist-deduplicator.md](skills/playlist-deduplicator.md) | **Spotify Playlist Deduplicator** | A single-purpose skill that finds duplicate songs in a playlist and removes them. |
| [playlist-operations.md](skills/playlist-operations.md) | **Spotify Playlist Operations** | A comprehensive skill for creating, updating, organizing, reordering, and inspecting Spotify playlists. |
| [playlist-power-tools.md](skills/playlist-power-tools.md) | **Playlist Power Tools Skill Guide** | This skill equips AI agents to execute advanced, programmatic playlist curation, restructuring, and library analysis through the 8 **Playlist Power Tools**. |
| [playlist-vibe-sorter.md](skills/playlist-vibe-sorter.md) | **Spotify Playlist Vibe Sorter** | A single-purpose skill that reorders an existing playlist based on audio features like energy, danceability, or valence. |
| [prompt-clarification-protocol.md](skills/prompt-clarification-protocol.md) | **Prompt Clarification Protocol Skill** | Guidelines for evaluating prompt specificity and resolving ambiguity before triggering large playlist creation or batch operations. |
| [queue-flow-manager.md](skills/queue-flow-manager.md) | **Playback Queue & Flow Manager Skill** | Inspect, curate, and dynamically inject tracks into the user's upcoming Spotify playback queue. |
| [search-recommendations.md](skills/search-recommendations.md) | **Search, Recommendations & Discovery Skill Guide** | This skill equips AI agents to search Spotify's catalog, explore artist networks, discover music by mood and audio attributes, sample genre seeds, unearth hidden album deep cuts, and generate fine-tuned recommendations through the 7 **Search, Recommendations & Discovery Tools**. |
| [soundtrack-staging-studio.md](skills/soundtrack-staging-studio.md) | **Soundtrack Curator & Staging Studio Skill** | Interactive visual curation workflow for launching, previewing, and staging soundtracks via the local Soundtrack Curator & Staging Studio web application. |
| [stats-analytics.md](skills/stats-analytics.md) | **Stats, Analytics & Insights Skill** | Comprehensive listening telemetry, temporal volume distributions, taste archetype classification, multi-playlist audio feature comparisons, and library maintenance audits. |
| [taste-analyzer.md](skills/taste-analyzer.md) | **Spotify Taste Analyzer** | A single-purpose skill that analyzes the user's Spotify listening habits, saved music library, and reports on their top tracks or artists. |

## Prerequisites

Before running the application, make sure you have the following installed:
- [Python 3.10+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)

You will also need Developer API Credentials for:
- [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) (Only **Client ID** is needed; uses PKCE browser authorization)
- [TMDB API](https://developer.themoviedb.org/docs/getting-started) (Provide **either** an API Key or a Read Access Token)

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

Create a file named `.env` in the root of the project directory (or copy from `.env.sample`). Add your API credentials:

```ini
# Spotify Developer API Credentials (PKCE Auth - No Secret Needed)
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback

# TMDB Credentials - Provide ANY ONE (either TMDB_API_KEY or TMDB_READ_ACCESS_TOKEN):
TMDB_API_KEY=your_tmdb_api_key
TMDB_READ_ACCESS_TOKEN=your_tmdb_read_access_token
TMDB_BASE_URL=https://api.themoviedb.org/3

# Modular Toolsets: Select active toolset profile to prevent LLM context window overload
# Options: core (default, 16 essential curation tools), playback, playlists, search, taste, library, browse, or all
SPOTIFY_TOOLSETS=core

# Optional configuration
OPEN_BROWSER=true
```

> [!TIP]
> - **Spotify PKCE Flow**: The app uses **PKCE (Proof Key for Code Exchange)** authorization. No client secret is needed or used—only your `SPOTIPY_CLIENT_ID` and a simple one-click browser authorization popup.
> - **Flexible TMDB Authentication**: You only need **any single one** of `TMDB_API_KEY` (v3 API key) or `TMDB_READ_ACCESS_TOKEN` (v4 Read Access Token). The server automatically detects the credential type.

### 5. (Optional) Quick Auth Verification

Run the one-click Spotify authorization script to test your connection:

```bash
python auth_spotify.py
```

## Modular Toolsets & On-Demand Lazy Loading

To prevent flooding the LLM context window in AI clients (Cursor, Claude Desktop, Antigravity), this server implements **Modular Toolsets** and **On-Demand Lazy Loading**:

- **Context Window Protection**: The full catalog of 108 tools consumes **~21,376 tokens**. Running with `--toolsets=core` exposes only the **16 essential curation tools (~2,757 tokens)** &mdash; an **87% context reduction**!
- **On-Demand Lazy Loading**: Modules (`spotipy`, `requests`, `bs4`, `ddgs`, etc.) are **never loaded at startup**. When an LLM calls a tool, the module is imported on-demand and cached in memory for instantaneous (0 ms) subsequent executions.

### Available Toolsets

| Toolset Profile | Exposed Tools | Token Footprint | Best For |
| :--- | :--- | :--- | :--- |
| **`core`** *(Default)* | **16 tools** | **~2,757 tokens** | Filmography curation, movie soundtracks, search, dedupe, audio features, staging studio |
| **`playback`** | 31 tools | ~5,800 tokens | DJ controls, Spotify Connect device switching, queue management |
| **`playlists`** | 33 tools | ~7,400 tokens | Advanced playlist diff, subset detection, merging, sorting, splitting |
| **`search`** | 16 tools | ~3,600 tokens | Music exploration, mood/genre search, TMDB movie & actor filmography lookup |
| **`taste`** | 14 tools | ~3,100 tokens | Top tracks, listening patterns, taste profile, audio feature comparisons |
| **`library`** | 8 tools | ~1,800 tokens | Saved tracks, saved albums, follower management |
| **`browse`** | 5 tools | ~1,100 tokens | Spotify catalog lookup (artist, album, track, user) |
| **`all`** | 108 tools | ~21,376 tokens | Full access to every tool across all domains |

### Running with Toolset Flags

You can specify toolsets via CLI flag `--toolsets=...` or environment variable `SPOTIFY_TOOLSETS`:

```bash
# Run with the lightweight core toolset (16 tools, optimal for Cursor/Claude):
python server.py --toolsets=core
python mcp.py --toolsets=core

# Combine multiple toolsets:
python server.py --toolsets=core,playback

# Run with the complete catalog (108 tools):
python server.py --toolsets=all
```

## Running the Application

There are two entry points to run the server, depending on your use case:

### 1. `server.py` (Development & Web App Focus)

Start the MCP server and background web app simultaneously by running:

```bash
python server.py --toolsets=core
```

The application will start, and the web interface should automatically open in your default browser at `http://127.0.0.1:8000`.

### 2. `mcp.py` (MCP Client Integration Focus)

If you are running this project as a tool inside an MCP host (like Cursor, VSCode, or Claude Desktop), you should use `mcp.py`:

```bash
python mcp.py --toolsets=core
```

## Repository Structure

```text
Spotify-MCP-Web-MCP-Server/
├── server.py                  # FastMCP server entrypoint & SSE ASGI app
├── mcp.py                     # Stdio FastMCP runner with PKCE GUI OAuth popup
├── auth_spotify.py            # CLI helper to verify Spotify OAuth connection
├── requirements.txt           # Python dependencies
├── Procfile                   # Cloud Run / web deployment entrypoint
├── SPOTIFY_RULES.md           # Master MCP tools & agent clarification protocol
├── tools/                     # Modular MCP tool implementations (108 tools)
│   ├── registry.py            # Modular toolset catalog, CLI toolset router & lazy loader
│   ├── core.py                # FastMCP server instance, Spotify/TMDB client helpers
│   ├── playlists.py           # Core playlist curation & power tools
│   ├── playback.py            # Spotify Connect playback & hardware controls
│   ├── taste.py               # Deep audio features, taste analytics & listening trends
│   ├── search.py              # Music discovery, search & TMDB filmography tools
│   ├── library.py             # Saved tracks, albums & library management
│   ├── browse.py              # Catalog entity inspection & artist discography
│   ├── tmdb_helpers.py        # TMDB API client & DuckDuckGo/Wikipedia fallback engines
│   ├── web_app.py             # MCP tool to open Soundtrack Studio UI
│   └── web_app_internal.py    # Background thread launcher for Soundtrack Studio
├── mcp-soundtrack-app/        # Soundtrack Curator & Staging Studio web app
│   ├── server.py              # FastAPI server serving REST API & web pages
│   └── templates/             # Jinja2 / HTML templates
│       ├── index.html         # Main Soundtrack Curator & Staging Studio UI
│       ├── tools.html         # Interactive MCP Tools Catalog dashboard
│       └── guide.html         # Comprehensive documentation & workflow guide
├── skills/                    # 20 autonomous agent skills for AI assistants
├── tests/                     # Pytest unit & integration test suites
│   ├── test_browse.py
│   ├── test_library.py
│   ├── test_playback.py
│   ├── test_playlists.py
│   ├── test_search.py
│   ├── test_server.py
│   ├── test_taste.py
│   └── test_web_app.py
├── scripts/                   # Deployment & cleanup scripts (PowerShell & Bash)
│   ├── deploy.ps1 / deploy.sh
│   └── destroy.ps1 / destroy.sh
├── terraform/                 # Terraform infrastructure (GCS Bucket + Cloud Run)
├── .cursor/rules/             # Modern Cursor IDE rules
├── .agents/rules/             # Agent / Antigravity IDE rules
└── .github/workflows/         # CI/CD deployment workflows
```

## API Limits

Please keep in mind the rate limits imposed by the external APIs used in this project:

- **Spotify Web API**: Spotify uses a dynamic rate limit based on a rolling window. If you make too many requests in a short period (such as aggressively searching or curating massive playlists), you will receive a `429 Too Many Requests` response. The app may need to back off and try again later.
- **TMDB API**: The Movie Database allows up to **50 requests per second**. This is generally quite generous for normal usage, but batch queries or rapid concurrent lookups could potentially hit this limit.

## MCP Integration

This project is built using `fastmcp`. Once running via `stdio` (or SSE if configured), it can be seamlessly consumed by other MCP clients.

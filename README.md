# Spotify & TMDB Web MCP Server

[![M8ven Score](https://m8ven.ai/badge/mcp/chiru144/spotify-mcp-web-mcp-server)](https://m8ven.ai/mcp/chiru144/spotify-mcp-web-mcp-server)
[![MCP Tools](https://img.shields.io/badge/MCP%20Tools-115%20Registered-1DB954?style=flat&logo=spotify)](tools/)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-20%20Packaged-8A2BE2?style=flat)](skills/)

This repository contains a FastMCP application that connects Spotify with TMDB (The Movie Database). It has **115 registered MCP tools** and **20 autonomous agent skills**, and lets you build movie soundtrack playlists, automate playlist curation, explore your listening taste, and use a local web app, the Soundtrack Curator & Staging Studio.

> [!NOTE]
> **Built mostly for Indian users.** The project is designed around Indian film music: it builds playlists from an actor's filmography and matches soundtracks for Telugu, Tamil, Kannada, Malayalam and Hindi movies, including songs credited as 'From "Movie Name"' and releases tagged with a language, such as "[Telugu]". It works for any music on Spotify, but Indian cinema is where it is strongest.

## Highlights

- **115 FastMCP Tools & 20 Agent Skills**: Covers cinema filmography discovery, smart playlist management, artist-network and mood discovery, a local library cache, vibe/radio/era/time-capsule playlist generators, taste analytics, catalog browsing, library management, and full Spotify Connect device control.
- **PKCE OAuth & Flexible Auth**: Spotify sign-in uses PKCE, so you only need a Client ID and a one-click browser login, with no client secret. TMDB accepts either an API key or a Read Access Token.
- **Cinema Meets Music**: Your AI assistant can look up movies, cast and crew on TMDB and turn them into Spotify playlists.
- **Dual Web & Agent Design**: Built on FastAPI and Uvicorn, it runs both as a web app and as an MCP server, and supports remote hosting and several AI clients at once.
- **Modular Architecture**: The tools are split into focused modules (`playback.py`, `playlists.py`, `taste.py`, `search.py`, `library.py`, `library_cache.py`, `generators.py`, `browse.py`, `web_app.py`), each covered by unit tests.

## Spotify 2026 Development Mode Limits

In 2026, Spotify switched off several Web API features for apps in Development Mode, which is what every personal Client ID is. The tools work around them where they can:

| Spotify feature | Status | What the tools do instead |
| :--- | :--- | :--- |
| Related artists | Removed (403) | `spotify_related_artists` and `get_artist_network` list the artists who share the most songs with the artist. |
| Recommendations and genre seeds | Removed (404) | `spotify_get_recommendations`, `get_recommendations` and `spotify_discover_by_artist` recommend songs by the seeds' collaborators plus genre-search picks. `spotify_genre_explorer` lists a built-in set of genres. |
| Artist top tracks | Removed (403) | The artist's top search results are used instead. |
| Audio features (energy, valence, tempo...) | Removed (403) | `get_audio_features` and `reorder_playlist_by_audio_features` return an "unavailable" message. `target_energy` and `target_valence` pick the genres whose estimated energy and valence are closest; other `target_*` arguments are ignored. Moods map to genres. |
| Popularity, followers, genres | Returned as null | Shown as N/A or left out. `spotify_discover_deep_cuts` treats a "deep cut" as an album track outside the artist's top search results, and `spotify_taste_profile` reports artist variety and eras instead of a mainstream score. |
| Other users' profiles, follower checks and playlists you don't follow | Removed (403) | `spotify_get_user` and `spotify_check_playlist_followers` work for your own account only. |
| Search `limit` above 10 | Rejected | The client fetches larger searches 10 results at a time. |

## Local Library Cache & Playlist Generators

`spotify_sync_library` downloads your Liked Songs and the playlists you own into a JSON file: `~/.cache/spotify-mcp/library.json`, or `%LOCALAPPDATA%\spotify-mcp\library.json` on Windows (set `SPOTIFY_MCP_LIBRARY_PATH` to change it). After that:

- `spotify_query_library` and `spotify_library_stats` answer questions about your music without calling Spotify.
- `spotify_vibe_playlist` builds a playlist for a mood, or an energy/valence target, from songs you already like.
- `spotify_era_playlist` (with `from_library=True`) and `spotify_time_capsule_playlist` (songs you saved in a given year) also use the cache.
- `spotify_radio_playlist` mixes an artist's songs with songs by the artists they collaborate with.

Every generator shows a preview first and only creates a playlist when called with `create=True`.

**How vibes are estimated:** Spotify no longer gives this app audio features or artist genres, so each genre has an estimated energy and valence (`GENRE_VIBES` in `tools/discovery.py`). A song gets its vibe from the genre searches its artist appears in, plus words in its track, album and playlist names ("Unplugged" means acoustic; a playlist called "Gym" means workout). Spotify's genre search mostly covers mainstream Western genres, so songs from other scenes, such as Telugu or Tamil film music, are often left unplaced. Naming your playlists by mood helps.

Run `spotify_sync_library` again whenever your library changes. A sync makes about one Spotify call per 50 Liked Songs, plus one or more per playlist.

## Features & Capabilities

For an in-depth breakdown of the features, a feature comparison table, and the cinema filmography pipeline, see **[CONTRIBUTING.md](CONTRIBUTING.md#features--technical-overview)**. The complete 115-tool catalog and the 20 agent skills are listed in **[CONTRIBUTING.md](CONTRIBUTING.md#complete-fastmcp-tools-catalog-115-registered-tools)**.

## Install from PyPI

The server and the web studio are published as two Python packages:

| Package | What it gives you | Commands |
| :--- | :--- | :--- |
| `spotify-soundtrack-mcp` | The MCP server with all 115 tools and 20 skills | `spotify-mcp`, `spotify-soundtrack-mcp`, `spotify-mcp-auth` |
| `spotify-mcp-web` | The Soundtrack Curator & Staging Studio web app | `soundtrack-studio` |

### 1. Install

```bash
pip install spotify-soundtrack-mcp spotify-mcp-web
```

You need Python 3.10 or later. Installing `spotify-mcp-web` also installs `spotify-soundtrack-mcp`. If you don't want the web studio, install only `spotify-soundtrack-mcp`.

### 2. Configure

Create `~/.spotify-mcp/.env` (or a `.env` file in the folder you run the commands from):

```env
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
TMDB_API_KEY=your_tmdb_api_key            # or TMDB_READ_ACCESS_TOKEN=...
SPOTIFY_TOOLSETS=core                     # optional: core (default), playback, playlists, search, taste, library, browse, all
```

In the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), add `http://127.0.0.1:8888/callback` as a Redirect URI for your app. Only the Client ID is needed; there is no client secret.

### 3. Connect your Spotify account

```bash
spotify-mcp-auth
```

This opens Spotify in your browser. Once you approve, the token is saved to `~/.spotify-mcp/.spotipyoauthcache` (set `SPOTIFY_MCP_CACHE_PATH` to store it elsewhere), and both the MCP server and the web studio use it.

### 4. Connect the MCP server to your AI client

`spotify-mcp` runs the server over stdio. Add it to Claude Desktop (`claude_desktop_config.json`), Cursor (`.cursor/mcp.json`) or any other MCP client:

```json
{
  "mcpServers": {
    "spotify": {
      "command": "spotify-mcp",
      "env": {
        "SPOTIFY_TOOLSETS": "core"
      }
    }
  }
}
```

If the client can't find `spotify-mcp` on your PATH, use the full path printed by `where spotify-mcp` (Windows) or `which spotify-mcp` (macOS/Linux). With [uv](https://docs.astral.sh/uv/), you can skip the install and let the client run it:

```json
{
  "mcpServers": {
    "spotify": {
      "command": "uvx",
      "args": ["--from", "spotify-soundtrack-mcp", "spotify-mcp"]
    }
  }
}
```

While `spotify-mcp` is running, it also starts the web studio at `http://127.0.0.1:8000` if `spotify-mcp-web` is installed.

To serve MCP over HTTP (SSE) for remote clients instead, run:

```bash
spotify-soundtrack-mcp
```

It listens on `0.0.0.0:8080`; set `HOST` and `PORT` to change this.

### 5. Open the web studio on its own

```bash
soundtrack-studio
```

This starts the studio at `http://127.0.0.1:8000` and opens your browser. Set `PORT` to use a different port, or `OPEN_BROWSER=false` to stop it from opening the browser. The tool guide is at `/guide` and the advanced tools are at `/tools`.

## Prerequisites

To run from source instead of PyPI, make sure you have the following installed:
- [Python 3.10+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)

You will also need developer API credentials for:
- [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) (only the **Client ID** is needed; sign-in uses PKCE browser authorization)
- [TMDB API](https://developer.themoviedb.org/docs/getting-started) (provide **either** an API key or a Read Access Token)

## Installation & Setup

Follow these steps to run the project locally:

### 1. Clone the repository

```bash
git clone https://github.com/Chiru144/Spotify-MCP-Web-MCP-Server.git
cd Spotify-MCP-Web-MCP-Server
```

### 2. Create and activate a virtual environment

Using a virtual environment is recommended for managing dependencies.

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

### 3. Install dependencies

Install the required Python packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a file named `.env` in the project root (or copy `.env.sample`) and add your API credentials:

```ini
# Spotify Developer API credentials (PKCE auth - no secret needed)
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback

# TMDB credentials - provide ANY ONE (either TMDB_API_KEY or TMDB_READ_ACCESS_TOKEN):
TMDB_API_KEY=your_tmdb_api_key
TMDB_READ_ACCESS_TOKEN=your_tmdb_read_access_token
TMDB_BASE_URL=https://api.themoviedb.org/3

# Modular toolsets: choose which tools to load, to avoid overloading the LLM's context window
# Options: core (default, 16 essential curation tools), playback, playlists, search, taste, library, browse, or all
SPOTIFY_TOOLSETS=core

# Optional configuration
OPEN_BROWSER=true
```

> [!TIP]
> - **Spotify PKCE flow**: The app uses **PKCE (Proof Key for Code Exchange)** authorization. No client secret is needed or used; you only need your `SPOTIPY_CLIENT_ID` and a one-click browser login.
> - **Flexible TMDB authentication**: You only need **one** of `TMDB_API_KEY` (v3 API key) or `TMDB_READ_ACCESS_TOKEN` (v4 Read Access Token). The server detects which one you provided.

### 5. (Optional) Verify Spotify sign-in

Run the one-click Spotify authorization script to test your connection:

```bash
python auth_spotify.py
```

## Modular Toolsets & On-Demand Lazy Loading

To avoid flooding the LLM context window in AI clients (Cursor, Claude Desktop, Antigravity), this server uses **modular toolsets** and **on-demand lazy loading**:

- **Context window protection**: The full catalog of 115 tools takes **~25,600 tokens**. Running with `--toolsets=core` exposes only the **16 essential curation tools (~4,100 tokens)**, an **84% reduction**.
- **On-demand lazy loading**: Heavy modules (`spotipy`, `requests`, `bs4`, `ddgs`, etc.) are **not loaded at startup**. When an LLM calls a tool, its module is imported and kept in memory, so later calls start instantly.

### Available Toolsets

| Toolset Profile | Exposed Tools | Token Footprint | Best For |
| :--- | :--- | :--- | :--- |
| **`core`** *(Default)* | **16 tools** | **~4,100 tokens** | Filmography curation, movie soundtracks, search, dedupe, staging studio |
| **`playback`** | 31 tools | ~4,700 tokens | DJ controls, Spotify Connect device switching, queue management |
| **`playlists`** | 37 tools | ~9,500 tokens | Playlist diff, subset detection, merging, splitting, and vibe/radio/era/time-capsule generators |
| **`search`** | 16 tools | ~4,500 tokens | Music exploration, mood/genre search, TMDB movie & actor filmography lookup |
| **`taste`** | 14 tools | ~3,100 tokens | Top tracks, listening patterns, taste profile, playlist comparisons |
| **`library`** | 11 tools | ~2,400 tokens | Saved tracks, saved albums, local library cache (sync, stats, query) |
| **`browse`** | 5 tools | ~1,200 tokens | Spotify catalog lookup (artist, album, track, your profile) |
| **`all`** | 115 tools | ~25,600 tokens | Full access to every tool |

### Running with Toolset Flags

You can choose toolsets with the `--toolsets=...` command-line flag or the `SPOTIFY_TOOLSETS` environment variable:

```bash
# Run with the lightweight core toolset (16 tools, best for Cursor/Claude):
python server.py --toolsets=core
python mcp.py --toolsets=core

# Combine multiple toolsets:
python server.py --toolsets=core,playback

# Run with the complete catalog (115 tools):
python server.py --toolsets=all
```

## Running the Application

There are two entry points, depending on how you want to use the server:

### 1. `server.py` (development and web app)

Start the MCP server and the web app together:

```bash
python server.py --toolsets=core
```

The web interface should open automatically in your default browser at `http://127.0.0.1:8000`.

### 2. `mcp.py` (MCP client integration)

If you are running this project as a tool inside an MCP host (such as Cursor, VS Code, or Claude Desktop), use `mcp.py`:

```bash
python mcp.py --toolsets=core
```

## Repository Structure

```text
Spotify-MCP-Web-MCP-Server/
├── server.py                  # FastMCP server entry point & SSE ASGI app
├── mcp.py                     # Stdio FastMCP runner with PKCE GUI OAuth popup
├── auth_spotify.py            # CLI helper to verify the Spotify OAuth connection
├── requirements.txt           # Python dependencies
├── SPOTIFY_RULES.md           # MCP tool usage rules & agent clarification protocol
├── tools/                     # Modular MCP tool implementations (115 tools)
│   ├── registry.py            # Toolset catalog, CLI toolset router & lazy loader
│   ├── core.py                # FastMCP server instance, Spotify/TMDB client helpers
│   ├── spotify_client.py      # Spotify client with rate-limit handling & 2026 API fixes
│   ├── playlists.py           # Core playlist curation & power tools
│   ├── playback.py            # Spotify Connect playback & device controls
│   ├── taste.py               # Taste analytics & listening trends
│   ├── search.py              # Music discovery, search & TMDB filmography tools
│   ├── library.py             # Saved tracks, albums & library management
│   ├── library_cache.py       # Local JSON cache of Liked Songs & your playlists
│   ├── generators.py          # Vibe, radio, era & time-capsule playlist generators
│   ├── discovery.py           # Search-based discovery & genre vibe estimates (2026 API workarounds)
│   ├── browse.py              # Catalog entity inspection & artist discography
│   ├── tmdb_helpers.py        # TMDB API client & DuckDuckGo/Wikipedia fallbacks
│   ├── web_app.py             # MCP tool that opens the Soundtrack Studio UI
│   └── web_app_internal.py    # Background thread launcher for Soundtrack Studio
├── mcp-soundtrack-app/        # Soundtrack Curator & Staging Studio web app
│   ├── server.py              # FastAPI server for the REST API & web pages
│   └── templates/             # HTML templates
│       ├── index.html         # Main Soundtrack Curator & Staging Studio UI
│       ├── tools.html         # Advanced tools dashboard
│       └── guide.html         # Tool guide & documentation
├── skills/                    # 20 autonomous agent skills for AI assistants
├── tests/                     # Pytest unit & integration tests
│   ├── test_browse.py
│   ├── test_discovery.py
│   ├── test_library.py
│   ├── test_library_cache.py
│   ├── test_playback.py
│   ├── test_playlists.py
│   ├── test_search.py
│   ├── test_server.py
│   ├── test_spotify_client.py
│   ├── test_studio_playlists.py
│   ├── test_taste.py
│   ├── test_toolsets.py
│   └── test_web_app.py
├── .cursor/rules/             # Cursor IDE rules
├── .agents/rules/             # Agent / Antigravity IDE rules
└── .github/                   # GitHub Copilot instructions
```

## API Limits

Keep in mind the rate limits of the external APIs this project uses:

- **Spotify Web API**: Spotify uses a dynamic rate limit over a rolling window. If you make too many requests in a short time (for example, searching aggressively or building very large playlists), Spotify returns `429 Too Many Requests` and may ask the app to wait, sometimes for hours. When the wait is long, the tools stop and tell you when you can try again instead of hanging.
- **TMDB API**: The Movie Database allows up to **50 requests per second**. That is generous for normal use, but large batches or many rapid lookups at once can still hit it.

## MCP Integration

This project is built with `fastmcp`. Once it is running over `stdio` (or SSE, if configured), any MCP client can use its tools.

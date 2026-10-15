# Spotify & TMDB Web MCP Server

[![M8ven Score](https://m8ven.ai/badge/mcp/chiru144/spotify-mcp-web-mcp-server)](https://m8ven.ai/mcp/chiru144/spotify-mcp-web-mcp-server)

This repository contains a FastMCP application that integrates Spotify and TMDB (The Movie Database). It allows you to build custom soundtracks and interact with a web-based Soundtrack Curator & Staging Studio.

## Highlights

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

### Vibe & Mood Sorting (audio_features)

Instead of arbitrary text labels, Gupta's tool pulls standard audio feature scores ($0.0$ to $1.0$) for tracks:
- **Valence**: Positivity, musical cheerfulness, or sadness.
- **Energy**: Intensity, loudness, and fast-paced activity.
- **Danceability**: Rhythm stability, beat strength, and tempo consistency.
- **Acousticness & Instrumentalness**: Acoustic instrument usage vs. purely vocal/electronic elements.

Using these metrics, the AI calculates a track's "vibe profile". For example, a song with high valence and high energy is tagged by the LLM as "Upbeat Workout", while low valence and high acousticness is tagged as "Melancholic Chill".

### Song & Type Suggestions (get_recommendations)

For song suggestions, it wraps Spotify's native Recommendations API, which accepts seed constraints:
- **Seed Genres**: Suggest songs by style (e.g., synthwave, indie-pop, lo-fi).
- **Target Audio Features**: Request songs matching specific parameters (e.g., `target_energy=0.8`, `target_valence=0.4`).
- **Seed Tracks/Artists**: Give 1-5 tracks or artists as reference points.

Exposes Spotify's audio analysis metrics so the attached LLM (Claude/Cursor) can tag and categorize tracks.

#### 1. The Core Inputs It Accepts

To generate recommendations, the tool passes up to 5 Seed Anchors and a set of Target Metric Sliders:

**Seed Anchors (1 to 5 total):**
- `seed_tracks` (Track IDs)
- `seed_artists` (Artist IDs)
- `seed_genres` (e.g., synthwave, indie-pop, lo-fi, deep-house)

**Target Audio Feature Constraints ($0.0$ to $1.0$ scale):**
- `target_energy`: Intensity and activity level
- `target_valence`: Positivity, happiness vs. sadness
- `target_danceability`: Rhythm stability and tempo suitability
- `target_acousticness`: Acoustic vs. electronic instrumentation
- `target_tempo`: Specific target BPM

#### 2. How Vibe & Type Recommendations Work in Practice

When you prompt your AI client (like Claude Desktop or Cursor), the LLM translates your natural language into the `get_recommendations` call:

**Scenario A: Vibe-Based Matching**
- **Prompt**: "Give me 10 songs with a dark, energetic synthwave vibe like Blinding Lights by The Weeknd."
- **Tool Call Executed**:
  - `seed_tracks`: ["Blinding_Lights_ID"]
  - `seed_genres`: ["synthwave"]
  - `target_energy`: 0.85 (High energy)
  - `target_valence`: 0.30 (Darker tone)

**Scenario B: Mood/Acoustic Type Matching**
- **Prompt**: "Find late-night study songs similar to Phoebe Bridgers, but purely instrumental."
- **Tool Call Executed**:
  - `seed_artists`: ["Phoebe_Bridgers_ID"]
  - `target_instrumentalness`: 0.90 (Instrumental focus)
  - `target_energy`: 0.20 (Quiet/Calm)
  - `target_valence`: 0.25 (Melancholic vibe)

#### 3. What It Does vs. What It Doesn't Do

| Capability | Status | Explanation |
|---|---|---|
| **Numeric Vibe Targets** | Built-in | Accepts raw target values (valence, energy, danceability) directly from Spotify's audio analysis. |
| **Genre Seeding** | Built-in | Accepts valid Spotify genres to narrow down recommendations. |
| **Automatic Clustering** | Built-in | Pairs with tools like smart_shuffle or distance algorithms to organize the recommended tracks into a smooth flow. |
| **Text Tag Matching** | LLM-Driven | Doesn't search plain-text tags like "#workout" directly; instead, the attached LLM maps text tags (e.g., "upbeat workout") to numeric parameters (energy=0.9, valence=0.8). |

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

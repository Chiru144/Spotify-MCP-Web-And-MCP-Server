# spotify-soundtrack-mcp

<!-- mcp-name: io.github.Chiru144/spotify-soundtrack-mcp -->

[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-io.github.Chiru144%2Fspotify--soundtrack--mcp-1DB954)](https://registry.modelcontextprotocol.io/v0/servers?search=io.github.Chiru144/spotify-soundtrack-mcp)
[![PyPI](https://img.shields.io/pypi/v/spotify-soundtrack-mcp)](https://pypi.org/project/spotify-soundtrack-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/spotify-soundtrack-mcp)](https://pypi.org/project/spotify-soundtrack-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE.md)

> **115 FastMCP Tools** for Spotify & TMDB — filmography playlists, smart playlist curation, a local library cache, vibe/radio/era/time-capsule playlist generators, taste analytics, Spotify Connect hardware control, and a built-in **Soundtrack Curator & Staging Studio** web UI.

---

## Installation

```bash
pip install spotify-soundtrack-mcp
# with the Soundtrack Studio web UI:
pip install "spotify-soundtrack-mcp[web]"
```

Or run it without installing, using [uv](https://docs.astral.sh/uv/):

```bash
uvx spotify-soundtrack-mcp --transport stdio
```

This server is listed in the [official MCP Registry](https://registry.modelcontextprotocol.io) as
`io.github.Chiru144/spotify-soundtrack-mcp`, so MCP clients that browse the registry can install it directly.

---

## Quick Start

### 1. Configure credentials

Create a `.env` file in your working directory:

```env
# Spotify Developer App credentials (PKCE — no secret needed!)
# Get yours at https://developer.spotify.com/dashboard
SPOTIPY_CLIENT_ID=your_spotify_client_id_here
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback

# TMDB (optional, enables cinema/filmography features)
# Get from https://www.themoviedb.org/settings/api
TMDB_API_KEY=your_tmdb_api_key_here
# OR: TMDB_READ_ACCESS_TOKEN=your_tmdb_read_access_token_here
```

> **Important:** In your Spotify Developer Dashboard, add `http://127.0.0.1:8888/callback` as a Redirect URI.

### 2. Authenticate

```bash
spotify-mcp-auth
```

This opens your browser for Spotify login and saves the token locally.

### 3. Run

**For Claude Desktop / Cursor (stdio transport):**
```bash
spotify-mcp
# With a specific toolset (recommended for token efficiency):
spotify-mcp --toolsets=core
```

**Also stdio, through the package-named command (what MCP Registry clients run):**
```bash
spotify-soundtrack-mcp --transport stdio
```

**For web/remote SSE transport:**
```bash
spotify-soundtrack-mcp            # same as --transport sse
# Custom host/port via env:
HOST=0.0.0.0 PORT=8080 spotify-soundtrack-mcp
```

---

## Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "spotify": {
      "command": "spotify-mcp",
      "args": ["--toolsets=core"],
      "env": {
        "SPOTIPY_CLIENT_ID": "your_client_id",
        "TMDB_API_KEY": "your_tmdb_key"
      }
    }
  }
}
```

Or let uv fetch and run it:

```json
{
  "mcpServers": {
    "spotify": {
      "command": "uvx",
      "args": ["spotify-soundtrack-mcp", "--transport", "stdio", "--toolsets=core"],
      "env": {
        "SPOTIPY_CLIENT_ID": "your_client_id",
        "TMDB_API_KEY": "your_tmdb_key"
      }
    }
  }
}
```

---

## Toolsets

| Toolset | Tools | Best For |
|---|---|---|
| `core` *(default)* | 16 | Filmography curation, movie soundtracks, search, dedup |
| `playback` | 31 | DJ controls, device switching, queue management |
| `playlists` | 37 | Advanced playlist diff, merging, splitting, vibe/radio/era/time-capsule generators |
| `search` | 16 | Music discovery, mood/genre search, TMDB lookup |
| `taste` | 14 | Top tracks, listening patterns, taste profile |
| `library` | 11 | Saved tracks, albums, local library cache (sync, stats, query) |
| `browse` | 5 | Artist, album, track, your profile lookup |
| `all` | 115 | Full access to every tool |

```bash
spotify-mcp --toolsets=core,playback
spotify-mcp --toolsets=all
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SPOTIPY_CLIENT_ID` | ✅ | Spotify app Client ID |
| `SPOTIPY_REDIRECT_URI` | ✅ | Must match Spotify dashboard (default: `http://127.0.0.1:8888/callback`) |
| `TMDB_API_KEY` | Optional | TMDB v3 API key |
| `TMDB_READ_ACCESS_TOKEN` | Optional | TMDB v4 Bearer token (alternative to API key) |
| `SPOTIFY_TOOLSETS` | Optional | Comma-separated toolset list (e.g. `core,playback`, or `all` for every tool; default `core`) |
| `SPOTIFY_MCP_CACHE_PATH` | Optional | Spotify token cache file, shared with `spotify-mcp-web` (default `~/.spotify-mcp/.spotipyoauthcache`) |
| `OPEN_BROWSER` | Optional | Set to `true` to auto-open the Soundtrack Studio UI |
| `MCP_TRANSPORT` | Optional | `stdio` or `sse`: default transport for `spotify-soundtrack-mcp` when `--transport` is not given (default `sse`) |
| `HOST` | Optional | Server bind host (default `0.0.0.0`, for `spotify-soundtrack-mcp`) |
| `PORT` | Optional | Server bind port (default `8080`, for `spotify-soundtrack-mcp`) |

---

## Links

- [GitHub Repository](https://github.com/Chiru144/Spotify-MCP-Web-And-MCP-Server)
- [Web App Package (spotify-mcp-web)](https://pypi.org/project/spotify-mcp-web/)
- [Report Issues](https://github.com/Chiru144/Spotify-MCP-Web-And-MCP-Server/issues)

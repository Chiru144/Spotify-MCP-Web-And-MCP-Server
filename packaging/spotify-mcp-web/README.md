# spotify-mcp-web

[![PyPI](https://img.shields.io/pypi/v/spotify-mcp-web)](https://pypi.org/project/spotify-mcp-web/)
[![Python](https://img.shields.io/pypi/pyversions/spotify-mcp-web)](https://pypi.org/project/spotify-mcp-web/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE.md)

> **Soundtrack Curator & Staging Studio** — a self-hosted FastAPI web application for Spotify playlist curation, TMDB filmography browsing, and MCP tools management. Pairs with [spotify-soundtrack-mcp](https://pypi.org/project/spotify-soundtrack-mcp/).

---

## Installation

```bash
pip install spotify-mcp-web
```

---

## Quick Start

### 1. Configure credentials

Create a `.env` file in your working directory:

```env
# Spotify Developer App credentials (PKCE — no secret needed!)
SPOTIPY_CLIENT_ID=your_spotify_client_id_here
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback

# TMDB (optional, enables cinema/filmography features)
TMDB_API_KEY=your_tmdb_api_key_here
```

> **Important:** In your [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), add `http://127.0.0.1:8888/callback` as a Redirect URI.

### 2. Start the Studio

```bash
soundtrack-studio
```

This starts the web app at **http://127.0.0.1:8000** and opens it in your browser automatically.

---

## Features

- 🎬 **Cinema Filmography** — Search actors/movies via TMDB and build soundtracks automatically
- 🎵 **Playlist Curation** — Create, merge, deduplicate, sort, split, and export Spotify playlists
- 🎚️ **Playback Controls** — Control Spotify Connect devices, queue management, volume/shuffle/repeat
- 📊 **Taste Analytics** — Top tracks, artists, listening patterns, playlist comparisons
- 📚 **Library Management** — Saved tracks & albums, library browsing
- 🔍 **Catalog Browsing** — Artist, album, and track lookup

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SPOTIPY_CLIENT_ID` | ✅ | Spotify app Client ID |
| `SPOTIPY_REDIRECT_URI` | ✅ | Must match Spotify dashboard (default: `http://127.0.0.1:8888/callback`) |
| `TMDB_API_KEY` | Optional | TMDB v3 API key |
| `TMDB_READ_ACCESS_TOKEN` | Optional | TMDB v4 Bearer token (alternative to API key) |
| `HOST` | Optional | Bind host (default `127.0.0.1`) |
| `PORT` | Optional | Bind port (default `8000`) |
| `OPEN_BROWSER` | Optional | Set to `false` to suppress auto-open |
| `SOUNDTRACK_TEMPLATES_DIR` | Optional | Custom path to HTML templates directory |

---

## Running as a Remote Server

```bash
HOST=0.0.0.0 PORT=8080 OPEN_BROWSER=false soundtrack-studio
```

---

## Pairing with the MCP Agent

Install both packages to get the full experience:

```bash
pip install spotify-soundtrack-mcp spotify-mcp-web
```

- `spotify-mcp` — starts the agent (for Claude Desktop / Cursor)
- `soundtrack-studio` — starts the web UI

---

## Links

- [GitHub Repository](https://github.com/Chiru144/Spotify-MCP-Web-And-MCP-Server)
- [MCP Agent Package (spotify-soundtrack-mcp)](https://pypi.org/project/spotify-soundtrack-mcp/)
- [Report Issues](https://github.com/Chiru144/Spotify-MCP-Web-And-MCP-Server/issues)

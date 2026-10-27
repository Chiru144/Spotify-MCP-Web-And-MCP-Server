# Soundtrack Curator & Staging Studio Skill

## Overview
Interactive visual curation workflow for launching, previewing, and staging soundtracks via the local Soundtrack Curator & Staging Studio web application.

## When to use this skill
- When the user asks to "open the studio", "launch soundtrack studio", "preview songs", "open web UI", or "stage tracks visually".
- When an interactive visual interface is better suited for a user wanting to preview 30-second audio clips before adding tracks to their library.

## Tools Included
- `open_soundtrack_studio()`: Launches or retrieves the URL for the Soundtrack Curator & Staging Studio web application.

## Workflow Instructions
1. Call `open_soundtrack_studio()` to launch or verify that the local server is running on `http://127.0.0.1:8000`.
2. Present the user with the active dashboard link `http://127.0.0.1:8000`.
3. Inform the user of key visual studio features:
   - **Send Box**: Stage tracks from any search or filmography query into an in-memory staging area.
   - **30-Second Previews**: Listen to playable track snippets before committing them to playlists.
   - **One-Click Playlist Sync**: Commit all staged tracks directly to a new or existing Spotify playlist.
   - **Interactive Tool Guide**: Browse and trigger all 108 MCP endpoints visually at `http://127.0.0.1:8000/tools`.

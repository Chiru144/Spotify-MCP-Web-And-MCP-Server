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
- **Smart Playlist Management**: Create playlists, combine, dedupe, split, diff and merge, and generate vibe, radio, era and time-capsule playlists.
- **Search & Library Access**: Search for tracks, albums, artists, or playlists on Spotify, and keep a local cache of your Liked Songs and playlists for fast "songs I already like" queries.
- **Deep Taste Analysis & Insights**: Retrieve top played songs and artists (short/medium/long term), profile your taste by artist variety and era, and map artist networks through collaborations.
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
| **Smart Shuffle** (Random playlist mix into a new playlist) | ✅ Yes | ❌ No |
| **Smart Playlist Deduplication** (In-place duplicate song removal preserving first occurrence) | ✅ Yes | ❌ No |
| **Multi-Playlist Combiner** (Merges multiple playlists with auto-pagination & deduping) | ✅ Yes | ❌ No |
| **Multi-Seed Vibe & Mood Engine** (5 seeds + energy/valence targets matched to genre vibe estimates) | ✅ Yes | ❌ No |
| **Local Library Cache** (Liked Songs & your playlists cached as JSON for offline queries) | ✅ Yes | ❌ No |
| **Playlist Generators** (vibe, artist radio, era, time capsule; preview before creating) | ✅ Yes | ❌ No |
| **Web & Browser Song Tagger** (Autonomous agent research via DuckDuckGo to tag tracks) | ✅ Yes | ❌ No |
| **Artist Network & Taste Insights** (Collaborator mapping + short/med/long listening analytics) | ✅ Yes | ❌ No |
| **Full Playback & Device Switching** (Spotify Connect controls + active hardware switching) | ✅ Yes | ⚠️ Partial (Raw playback only) |

#### Filmography & Cinema Soundtrack Pipeline

Unlike standard music-only integrations, this server deeply integrates TMDB (The Movie Database) with Spotify's library:
- **Actor Filmography Discovery**: Fetches full acting credits sorted by popularity or release date, with a resilient 3-tier fallback (TMDB $\rightarrow$ DuckDuckGo $\rightarrow$ Wikipedia).
- **Soundtrack Resolution**: Searches Spotify for official soundtracks and scores, falling back to track-level searches and DuckDuckGo tracklist discovery when albums are unlinked.
- **Automated Curation**: Creates dedicated actor or movie playlists in seconds (`create_actor_playlist`, `add_movie_songs_to_playlist`).

#### Vibe & Mood Matching (genre estimates)

Spotify stopped giving Development Mode apps per-track audio features (valence, energy, danceability) and artist genres in 2026. Instead, this server keeps an estimated energy and valence for each genre (`GENRE_VIBES` in `tools/discovery.py`) and a target for each mood preset (`MOOD_VIBES`):
- **Energy/valence targets** pick the genres whose estimates are closest, then sample songs from those genres.
- **Songs in your library** get a vibe from the genre searches their artist appears in, plus words in the track, album and playlist names (e.g. "Unplugged" means acoustic, a "Gym" playlist means workout). Songs nothing can be inferred about are skipped rather than guessed.
- **Coverage:** Spotify's genre search mostly covers mainstream Western genres, so songs from other scenes are often left unplaced.

#### Song & Type Suggestions (get_recommendations)

Spotify's Recommendations API is gone for Development Mode apps, so suggestions are rebuilt from search: songs by the artists the seeds collaborate with, plus genre-search picks (including genres chosen from energy/valence targets).

### Complete FastMCP Tools Catalog (115 Registered Tools)

The FastMCP server exposes **115 registered tools** organized across 9 specialized domain modules in `tools/`:

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
| spotify_discover_by_artist | Recommend songs by the artists a seed artist collaborates with. |
| spotify_discover_by_mood | Discover tracks for a mood preset, a set of genres, or energy/valence targets. |
| spotify_discover_deep_cuts | Discover album tracks from an artist or album that are not among their best-known songs. |
| spotify_genre_explorer | Sample tracks across specific genres, or list suggested genres. |
| spotify_get_recommendations | Recommend tracks from seed tracks, artists and genres (songs by the seeds' collaborators plus genre picks). |
| spotify_related_artists | Find artists connected to a target artist (the artists who share the most songs with them). |
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
| reorder_playlist_by_audio_features | Unavailable: Spotify no longer provides audio features (energy, valence, danceability, tempo) for Development Mode apps, so playlists cannot be sorted by them. The playlist is left unchanged. |
| shuffle_playlist | Mix and shuffle all songs in a Spotify playlist into a completely new random order. |
| spotify_absorb_playlist | Pull only missing/unique tracks from a source playlist into a destination playlist. |
| spotify_add_to_playlist | Append tracks to an existing playlist. |
| spotify_check_playlist_followers | Check whether you follow (have saved) a playlist. Spotify no longer answers this for other users for Development Mode apps, so only your own user ID can be checked. |
| spotify_create_playlist | Create a new empty playlist. |
| spotify_deduplicate_playlist | Scan and strip out duplicate tracks from a playlist. |
| spotify_export_playlist | Export full playlist data and track metadata to structured JSON. |
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
<summary><b>Taste Analytics & Insights</b> (<code>tools/taste.py</code> &mdash; 14 tools)</summary>

| Tool Name | Description |
| :--- | :--- |
| get_artist_network | Map an artist's network: the artists who share the most songs with them. |
| get_audio_features | Unavailable: Spotify no longer provides audio features (danceability, energy, valence, tempo) for Development Mode apps. |
| get_recommendations | Get track recommendations from seed tracks, artists and genres (songs by the seeds' collaborators plus genre picks). |
| get_saved_tracks | Get tracks from the user's Library (Saved Tracks). |
| get_user_top_artists | Get the current user's top artists over a specified period. |
| get_user_top_songs | Get the current user's top songs over a specified period. |
| get_user_top_tracks | Get the current user's top songs over a specified period. |
| spotify_listening_patterns | Analyze listening volume distributions across hours and days. |
| spotify_playlist_compare | Compare playlists side-by-side: size, song length, explicit share, artist variety, era and overlap. (Spotify no longer provides audio features such as energy or valence for Development Mode apps.) |
| spotify_playlist_freshness | Sort playlists by last update timestamp to identify stale lists. |
| spotify_recently_played | Fetch recent track listening history. |
| spotify_taste_profile | Generate an overview of your top artists, artist variety, eras and (when Spotify provides them) genres. |
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
<summary><b>Local Library Cache</b> (<code>tools/library_cache.py</code> &mdash; 3 tools)</summary>

| Tool Name | Description |
| :--- | :--- |
| spotify_library_stats | Summarize the locally cached library: size, top artists, decades and playlists. Makes no Spotify calls. |
| spotify_query_library | Search your locally cached library (Liked Songs and your playlists) without calling Spotify. |
| spotify_sync_library | Download your Liked Songs and your own playlists into a local cache file, so other tools can answer "songs I already like" requests without searching Spotify. Run it once, then again when your library changes. |

</details>

<details>
<summary><b>Playlist Generators</b> (<code>tools/generators.py</code> &mdash; 4 tools)</summary>

| Tool Name | Description |
| :--- | :--- |
| spotify_era_playlist | Build a playlist of songs released in a year range (e.g. 1990-1999), optionally limited to genres or to your cached library. |
| spotify_radio_playlist | Build an artist radio playlist: the seed artist's songs mixed with songs by the artists they collaborate with. |
| spotify_time_capsule_playlist | Build a time capsule playlist: the songs you saved in a given year (from your cached library), or, without a year, your all-time top tracks. |
| spotify_vibe_playlist | Build a playlist for a mood or an energy/valence target, from songs you already like (cached library) or from all of Spotify. Spotify no longer provides audio features, so each song's vibe is estimated from the genres its artist appears under. |

</details>

<details>
<summary><b>Catalog & Entity Inspection (Browse)</b> (<code>tools/browse.py</code> &mdash; 5 tools)</summary>

| Tool Name | Description |
| :--- | :--- |
| spotify_get_album | Inspect full album details including copyrights, label, release date, and complete tracklist. |
| spotify_get_artist | Inspect artist details and profile images (Spotify no longer returns genres, followers or popularity for Development Mode apps; these show N/A). |
| spotify_get_artist_albums | Get all albums, singles, and compilations released by a specific artist. |
| spotify_get_track | Inspect full track metadata including ISRC, popularity, audio preview URL, and album details. |
| spotify_get_user | Fetch your own Spotify profile and playlists. Other users' profiles are unavailable: Spotify no longer provides them to Development Mode apps. |

</details>

<details>
<summary><b>Visual Soundtrack Studio Launcher</b> (<code>tools/web_app.py</code> &mdash; 1 tool)</summary>

| Tool Name | Description |
| :--- | :--- |
| open_soundtrack_studio | Launch or retrieve the URL for the Soundtrack Curator & Staging Studio web application. |

</details>


### Packaged Autonomous Agent Skills (20 Skills)

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
| [playlist-vibe-sorter.md](skills/playlist-vibe-sorter.md) | **Spotify Playlist Vibe Sorter** | Explains that sorting by audio features is no longer possible (Spotify removed them for Development Mode apps) and offers the reorder, shuffle and split tools instead. |
| [prompt-clarification-protocol.md](skills/prompt-clarification-protocol.md) | **Prompt Clarification Protocol Skill** | Guidelines for evaluating prompt specificity and resolving ambiguity before triggering large playlist creation or batch operations. |
| [queue-flow-manager.md](skills/queue-flow-manager.md) | **Playback Queue & Flow Manager Skill** | Inspect, curate, and dynamically inject tracks into the user's upcoming Spotify playback queue. |
| [search-recommendations.md](skills/search-recommendations.md) | **Search, Recommendations & Discovery Skill Guide** | This skill equips AI agents to search Spotify's catalog, explore artist networks, discover music by mood and genre, unearth hidden album deep cuts, and generate seed-based recommendations through the 7 **Search, Recommendations & Discovery Tools**. |
| [soundtrack-staging-studio.md](skills/soundtrack-staging-studio.md) | **Soundtrack Curator & Staging Studio Skill** | Interactive visual curation workflow for launching, previewing, and staging soundtracks via the local Soundtrack Curator & Staging Studio web application. |
| [stats-analytics.md](skills/stats-analytics.md) | **Stats, Analytics & Insights Skill** | Comprehensive listening telemetry, temporal volume distributions, taste profiles, multi-playlist comparisons, and library maintenance audits. |
| [taste-analyzer.md](skills/taste-analyzer.md) | **Spotify Taste Analyzer** | A single-purpose skill that analyzes the user's Spotify listening habits, saved music library, and reports on their top tracks or artists. |

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

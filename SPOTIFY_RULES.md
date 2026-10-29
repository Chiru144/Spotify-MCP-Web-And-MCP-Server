# Spotify MCP Rules

Always use the registered MCP tools directly for Spotify actions. Never write standalone Python scripts or files to interact with the API when an MCP tool is available.

If the user asks to create a playlist, inspect tracks, reorder, shuffle, search, discover music, or do any other Spotify action, check the available MCP tools (including the standard `spotify_*` tools like `spotify_get_my_playlists`, `spotify_get_playlist`, `spotify_create_playlist`, `spotify_add_to_playlist`, `spotify_remove_from_playlist`, `spotify_reorder_playlist`, `spotify_update_playlist`, `spotify_follow_playlist`, `spotify_unfollow_playlist`, `spotify_get_playlist_cover`, `spotify_check_playlist_followers`, the **Playlist Power Tools**: `spotify_merge_playlists`, `spotify_split_playlist_by_artist`, `spotify_deduplicate_playlist`, `spotify_export_playlist`, `spotify_playlist_diff`, `spotify_find_playlist_overlaps`, `spotify_find_playlist_subsets`, `spotify_absorb_playlist`, the **Search, Recommendations & Discovery Tools**: `spotify_search`, `spotify_related_artists`, `spotify_discover_by_artist`, `spotify_discover_by_mood`, `spotify_genre_explorer`, `spotify_discover_deep_cuts`, `spotify_get_recommendations`, the **Stats, Analytics & Insights Tools**: `spotify_top_tracks`, `spotify_top_artists`, `spotify_recently_played`, `spotify_listening_patterns`, `spotify_taste_profile`, `spotify_playlist_compare`, `spotify_playlist_freshness`, the **Library & Saved Media Tools**: `spotify_get_saved_tracks`, `spotify_save_tracks`, `spotify_remove_saved_tracks`, `spotify_check_saved_tracks`, `spotify_get_saved_albums`, `spotify_save_albums`, `spotify_remove_saved_albums`, `spotify_check_saved_albums`, the **Catalog & Entity Inspection (Browse) Tools**: `spotify_get_track`, `spotify_get_album`, `spotify_get_artist`, `spotify_get_artist_albums`, `spotify_get_user`, as well as `create_actor_playlist`, `shuffle_playlist`, etc.) and call them directly.

Do NOT attempt to write temporary python scripts like `make_playlist.py` and run them.

### Spotify 2026 Development Mode Limits
Spotify no longer gives this app audio features (energy, valence, danceability, tempo), related artists, recommendations, genre seeds, artist top tracks, other users' profiles or follower checks, or playlists the user does not own or follow. Popularity, followers and genres come back empty.
- Don't promise valence/energy/tempo targets, audio-feature sorting, popularity filters or other users' profiles. `get_audio_features` and `reorder_playlist_by_audio_features` only return an "unavailable" message.
- Related-artist, recommendation, mood, genre and deep-cut tools still work: they are rebuilt from search and album data (collaborators, genre search, album tracks). Tell the user when results are approximations, e.g. "related" means "shares songs with".
- Every discovery call makes several Spotify searches, so don't loop them over many artists; the app has been rate-limited before.

> [!NOTE]
> The server supports modular toolsets (`--toolsets=core`) with on-demand lazy loading to prevent overloading LLM context windows (~2,757 tokens for `core` vs ~21,376 tokens for `all`). Tools are imported only when invoked. Specify `--toolsets=core,playback` or `--toolsets=all` when additional toolsets are needed.

### Prompt Clarification Protocol
Before making a playlist for a person (e.g., an actor, director, lyricist, or composer), evaluate if the user's prompt is specific enough.
- If the prompt is highly specific (e.g., "Make a playlist on Yogaraj Bhat, his movies from early 2000s and till now all the movies songs that he wrote"), proceed directly to create it using the MCP tools.
- If the prompt is vague (e.g., "Make a playlist on Yogaraj Bhat"), DO NOT execute immediately. Instead, ask the user clarifying questions tailored to the entity type to get more context. 
  - For an actor: Ask if they want songs from a specific era, specific co-stars, or their most popular hits.
  - For a director/lyricist: Ask if they want songs written/directed in a specific decade, particular blockbusters, or specific music director collaborations.
  - For a composer/singer: Ask if they want romantic songs, upbeat tracks, specific eras, or all-time hits.
Only after receiving clarified instructions should you invoke the MCP tools to generate the playlist.

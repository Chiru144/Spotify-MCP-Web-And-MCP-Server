# Spotify MCP Rules

Always use the registered MCP tools directly for Spotify actions. Never write standalone Python scripts or files to interact with the API when an MCP tool is available.

If the user asks to create a playlist, inspect tracks, reorder, shuffle, search, discover music, or do any other Spotify action, check the available MCP tools (including the standard `spotify_*` tools like `spotify_get_my_playlists`, `spotify_get_playlist`, `spotify_create_playlist`, `spotify_add_to_playlist`, `spotify_remove_from_playlist`, `spotify_reorder_playlist`, `spotify_update_playlist`, `spotify_follow_playlist`, `spotify_unfollow_playlist`, `spotify_get_playlist_cover`, `spotify_check_playlist_followers`, the **Playlist Power Tools**: `spotify_merge_playlists`, `spotify_split_playlist_by_artist`, `spotify_deduplicate_playlist`, `spotify_export_playlist`, `spotify_playlist_diff`, `spotify_find_playlist_overlaps`, `spotify_find_playlist_subsets`, `spotify_absorb_playlist`, the **Search, Recommendations & Discovery Tools**: `spotify_search`, `spotify_related_artists`, `spotify_discover_by_artist`, `spotify_discover_by_mood`, `spotify_genre_explorer`, `spotify_discover_deep_cuts`, `spotify_get_recommendations`, the **Stats, Analytics & Insights Tools**: `spotify_top_tracks`, `spotify_top_artists`, `spotify_recently_played`, `spotify_listening_patterns`, `spotify_taste_profile`, `spotify_playlist_compare`, `spotify_playlist_freshness`, the **Library & Saved Media Tools**: `spotify_get_saved_tracks`, `spotify_save_tracks`, `spotify_remove_saved_tracks`, `spotify_check_saved_tracks`, `spotify_get_saved_albums`, `spotify_save_albums`, `spotify_remove_saved_albums`, `spotify_check_saved_albums`, the **Catalog & Entity Inspection (Browse) Tools**: `spotify_get_track`, `spotify_get_album`, `spotify_get_artist`, `spotify_get_artist_albums`, `spotify_get_user`, as well as `create_actor_playlist`, `shuffle_playlist`, etc.) and call them directly.

Do NOT attempt to write temporary python scripts like `make_playlist.py` and run them.

### Prompt Clarification Protocol
Before making a playlist for a person (e.g., an actor, director, lyricist, or composer), evaluate if the user's prompt is specific enough.
- If the prompt is highly specific (e.g., "Make a playlist on Yogaraj Bhat, his movies from early 2000s and till now all the movies songs that he wrote"), proceed directly to create it using the MCP tools.
- If the prompt is vague (e.g., "Make a playlist on Yogaraj Bhat"), DO NOT execute immediately. Instead, ask the user clarifying questions tailored to the entity type to get more context. 
  - For an actor: Ask if they want songs from a specific era, specific co-stars, or their most popular hits.
  - For a director/lyricist: Ask if they want songs written/directed in a specific decade, particular blockbusters, or specific music director collaborations.
  - For a composer/singer: Ask if they want romantic songs, upbeat tracks, specific eras, or all-time hits.
Only after receiving clarified instructions should you invoke the MCP tools to generate the playlist.

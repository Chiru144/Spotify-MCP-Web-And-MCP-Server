# Spotify MCP Rules

Always use the registered MCP tools directly for Spotify actions. Never write standalone Python scripts or files to interact with the API when an MCP tool is available.

If the user asks to create a playlist, shuffle a playlist, add songs, or do any other Spotify action, check the available MCP tools (such as `create_actor_playlist`, `create_playlist`, `add_tracks_to_playlist`, `shuffle_playlist`, `get_user_playlists`, `reorder_playlist_by_audio_features`, etc.) and call them directly. 

Do NOT attempt to write temporary python scripts like `make_playlist.py` and run them.

### Prompt Clarification Protocol
Before making a playlist for a person (e.g., an actor, director, lyricist, or composer), evaluate if the user's prompt is specific enough.
- If the prompt is highly specific (e.g., "Make a playlist on Yogaraj Bhat, his movies from early 2000s and till now all the movies songs that he wrote"), proceed directly to create it using the MCP tools.
- If the prompt is vague (e.g., "Make a playlist on Yogaraj Bhat"), DO NOT execute immediately. Instead, ask the user clarifying questions tailored to the entity type to get more context. 
  - For an actor: Ask if they want songs from a specific era, specific co-stars, or their most popular hits.
  - For a director/lyricist: Ask if they want songs written/directed in a specific decade, particular blockbusters, or specific music director collaborations.
  - For a composer/singer: Ask if they want romantic songs, upbeat tracks, specific eras, or all-time hits.
Only after receiving clarified instructions should you invoke the MCP tools to generate the playlist.

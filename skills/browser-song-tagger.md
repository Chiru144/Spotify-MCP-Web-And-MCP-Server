# Web & Browser Song Tagger

## Description
An agent skill that researches a specific song via the web/browser to find its genres, cultural tags, or metadata, and then uses that information to effectively organize the song within Spotify (e.g., adding it to a genre-specific playlist or updating playlist metadata).

## When to use this skill
- When the user asks you to "tag this song" or "find tags from the browser for this track."
- When organizing a library into highly specific genre or mood categories based on external web data.
- When the user asks to enrich a playlist's description with accurate song metadata found online.

## Instructions
1. **Identify the Song**: First, figure out what song the user is referring to (e.g., by checking the currently playing track via `get_current_playback` or by asking the user).
2. **Web/Browser Research**: Use `search_duckduckgo` (or a browser tool if available in the agent's environment) to search for the song title, artist, and terms like "genre", "tags", or "music metadata".
3. **Extract Tags**: Analyze the search results to extract relevant tags, genres, or moods associated with the song (e.g., "Synthwave", "Cyberpunk", "80s Nostalgia").
4. **Apply the Tags**: Since Spotify doesn't have a direct "song tag" API, apply these tags by doing one of the following:
   - Creating a new playlist named after the tag and adding the song to it (e.g., `create_playlist(name="Tag: Synthwave")` -> `add_songs_to_playlist`).
   - Updating an existing playlist's description to include these tags using `update_playlist(description="Tags: Synthwave, 80s Nostalgia...")`.
5. **Report**: Tell the user what tags were found from the web and how the song was categorized.

## Example Workflow
User: "Check the song tags from the browser for 'Blinding Lights' and tag it."
Agent:
- Searches the web for "Blinding Lights The Weeknd genre tags".
- Discovers tags: Synth-pop, Synthwave, Electropop.
- Creates or finds a playlist called "Tag: Synthwave" or updates the master playlist's description.
- Responds: "I searched the web and found these tags for 'Blinding Lights': Synthwave, Electropop, Synth-pop. I've categorized the song into your Synthwave playlist accordingly!"

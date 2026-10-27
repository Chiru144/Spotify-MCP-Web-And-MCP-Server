# Prompt Clarification Protocol Skill

## Overview
Guidelines for evaluating prompt specificity and resolving ambiguity before triggering large playlist creation or batch operations.

## When to use this skill
- Whenever a user gives a vague or open-ended music creation command involving an entity (actor, director, lyricist, composer, or singer).
- Before invoking large-scale MCP tools that create or heavily modify playlists.

## Evaluation Rules
1. **Specific Prompt**: If the prompt specifies clear eras, movie names, specific moods, or albums:
   - *Example*: "Make a playlist of Quentin Tarantino soundtracks from the 90s."
   - *Action*: Proceed directly with MCP tool execution.
2. **Vague Prompt**: If the prompt only names a person without temporal, mood, or thematic constraints:
   - *Example*: "Make a playlist for Hans Zimmer."
   - *Action*: **STOP AND CLARIFY**. Formulate 2-3 tailored options to narrow intent:
     - **For an Actor**: Ask whether they prefer iconic all-time hits, a specific decade/era, or specific co-stars.
     - **For a Director**: Ask if they want instrumental scores, licensed popular songs, or specific franchise collaborations.
     - **For a Composer/Singer**: Ask if they want romantic ballads, energetic high-tempo tracks, acoustic sets, or all-time top hits.
3. Once the user replies with their preference, invoke the appropriate MCP tool (`create_actor_playlist`, `spotify_create_playlist`, `add_tracks_to_playlist`).

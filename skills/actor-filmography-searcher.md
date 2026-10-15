# Actor Filmography Searcher

## Description
A single-purpose skill that searches for an actor and returns a list of movies they have starred in using TMDB.

## When to use this skill
- When the user asks "What movies is [Actor] in?", "Find [Actor]'s filmography", or "List movies starring [Actor]".

## Instructions
1. Identify the actor's name from the prompt.
2. Call `search_actor_movies(actor_name)` or `get_actor_tmdb_profile(actor_name)`.
3. Present the list of movies clearly to the user with release years and character roles if available.
4. Do not perform any Spotify-related actions (like making playlists) unless explicitly requested. Just return the filmography.

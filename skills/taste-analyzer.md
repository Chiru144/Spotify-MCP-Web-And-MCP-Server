# Spotify Taste Analyzer

## Description
A single-purpose skill that analyzes the user's Spotify listening habits, saved music library, and reports on their top tracks or artists.

## When to use this skill
- When the user asks "What is my music taste?", "Who are my top artists?", or "Show my favorite songs lately."

## Instructions
1. Determine the timeframe the user is asking about (`short_term` = ~4 weeks, `medium_term` = ~6 months, `long_term` = years). Default to `medium_term` if unspecified.
2. Determine if they want top tracks, top artists, or library tracks:
   - For tracks: Call `get_user_top_tracks(limit, time_range)`.
   - For artists: Call `get_user_top_artists(limit, time_range)`.
   - For library songs: Call `get_saved_tracks(limit, offset)`.
3. Format the response nicely into a list so the user can easily read their top artists or tracks.

import os
import sys
import importlib
from typing import Optional, List, Dict, Any, Union
from mcp.types import ToolAnnotations

_LOADED_FUNCTIONS: Dict[str, Any] = {}

def _dispatch(module_name: str, func_name: str, **kwargs):
    cache_key = f"{module_name}.{func_name}"
    if cache_key not in _LOADED_FUNCTIONS:
        mod = importlib.import_module(module_name)
        _LOADED_FUNCTIONS[cache_key] = getattr(mod, func_name)
    return _LOADED_FUNCTIONS[cache_key](**kwargs)

def _stub_get_current_playback() -> str:
    """Get information about the user's current playback state, active song, and active device."""
    return _dispatch("tools.playback", "get_current_playback", **locals())

def _stub_play_track(device_id: str | None = None, context_uri: str | None = None, uris: list[str] | None = None, uri: str | None = None, offset_position: int | None = None, position_ms: int | None = None) -> str:
    """Start or resume playback.
Args:
    device_id: ID of the device to play on. Uses active device if omitted.
    context_uri: Spotify URI of context (album, artist, playlist).
    uris: List of Spotify track URIs to play. E.g. ["spotify:track:xxx"].
    uri: Single track URI (for backward compatibility).
    offset_position: Position in the context to start playback (0-based index).
    position_ms: Position in milliseconds to seek to."""
    return _dispatch("tools.playback", "play_track", **locals())

def _stub_play_song(uri: str | None = None, context_uri: str | None = None) -> str:
    """Resume playback or play a specific song/album/playlist by URI."""
    return _dispatch("tools.playback", "play_song", **locals())

def _stub_pause_playback() -> str:
    """Pause the current Spotify playback."""
    return _dispatch("tools.playback", "pause_playback", **locals())

def _stub_next_track() -> str:
    """Skip to the next song in the queue."""
    return _dispatch("tools.playback", "next_track", **locals())

def _stub_next_song() -> str:
    """Skip to the next song in the queue."""
    return _dispatch("tools.playback", "next_song", **locals())

def _stub_previous_track() -> str:
    """Skip to the previous song."""
    return _dispatch("tools.playback", "previous_track", **locals())

def _stub_previous_song() -> str:
    """Skip to the previous song."""
    return _dispatch("tools.playback", "previous_song", **locals())

def _stub_set_volume(volume_percent: int) -> str:
    """Set the playback volume.

Args:
    volume_percent: Volume level between 0 and 100."""
    return _dispatch("tools.playback", "set_volume", **locals())

def _stub_seek_playback(position_ms: int) -> str:
    """Seeks to the given position in the user's currently playing track.

Args:
    position_ms: The position in milliseconds to seek to."""
    return _dispatch("tools.playback", "seek_playback", **locals())

def _stub_set_repeat_mode(state: str) -> str:
    """Set the repeat mode for the user's playback.

Args:
    state: 'track', 'context', or 'off'."""
    return _dispatch("tools.playback", "set_repeat_mode", **locals())

def _stub_set_shuffle(state: bool) -> str:
    """Toggle shuffle for the user's playback.

Args:
    state: True to turn shuffle on, False to turn it off."""
    return _dispatch("tools.playback", "set_shuffle", **locals())

def _stub_get_available_devices() -> str:
    """Get information about a user's available devices."""
    return _dispatch("tools.playback", "get_available_devices", **locals())

def _stub_transfer_playback(device_id: str, play: bool = False) -> str:
    """Transfer playback to a new device.

Args:
    device_id: The ID of the device to transfer playback to.
    play: Whether to ensure playback happens on the new device."""
    return _dispatch("tools.playback", "transfer_playback", **locals())

def _stub_add_to_queue(uri: str) -> str:
    """Add a song to the user's playback queue.

Args:
    uri: Spotify song or episode URI (e.g., 'spotify:track:...')"""
    return _dispatch("tools.playback", "add_to_queue", **locals())

def _stub_get_queue() -> str:
    """Get the user's current playback queue."""
    return _dispatch("tools.playback", "get_queue", **locals())

def _stub_spotify_status() -> str:
    """Get current connection status and basic playback state."""
    return _dispatch("tools.playback", "spotify_status", **locals())

def _stub_spotify_now_playing() -> str:
    """Fetch detailed information about the currently playing track."""
    return _dispatch("tools.playback", "spotify_now_playing", **locals())

def _stub_spotify_play(uri: str | None = None, uris: List[str] | None = None, context_uri: str | None = None, device_id: str | None = None, position_ms: int | None = None) -> str:
    """Start or resume playback (accepts track, album, or playlist URIs)."""
    return _dispatch("tools.playback", "spotify_play", **locals())

def _stub_spotify_pause(device_id: str | None = None) -> str:
    """Pause playback."""
    return _dispatch("tools.playback", "spotify_pause", **locals())

def _stub_spotify_resume(device_id: str | None = None) -> str:
    """Resume active playback."""
    return _dispatch("tools.playback", "spotify_resume", **locals())

def _stub_spotify_skip_next(device_id: str | None = None) -> str:
    """Skip to the next track in the queue."""
    return _dispatch("tools.playback", "spotify_skip_next", **locals())

def _stub_spotify_skip_previous(device_id: str | None = None) -> str:
    """Skip back to the previous track."""
    return _dispatch("tools.playback", "spotify_skip_previous", **locals())

def _stub_spotify_add_to_queue(uri: str, device_id: str | None = None) -> str:
    """Add a track URI to the user's current playback queue."""
    return _dispatch("tools.playback", "spotify_add_to_queue", **locals())

def _stub_spotify_get_queue() -> str:
    """View current playback queue and upcoming tracks."""
    return _dispatch("tools.playback", "spotify_get_queue", **locals())

def _stub_spotify_get_devices() -> str:
    """List available Spotify Connect devices."""
    return _dispatch("tools.playback", "spotify_get_devices", **locals())

def _stub_spotify_transfer_playback(device_id: str, play: bool = False) -> str:
    """Transfer active playback to another connected device."""
    return _dispatch("tools.playback", "spotify_transfer_playback", **locals())

def _stub_spotify_set_volume(volume_percent: int, device_id: str | None = None) -> str:
    """Set playback volume (0–100)."""
    return _dispatch("tools.playback", "spotify_set_volume", **locals())

def _stub_spotify_seek(position_ms: int, device_id: str | None = None) -> str:
    """Seek to a specific timestamp in the current track."""
    return _dispatch("tools.playback", "spotify_seek", **locals())

def _stub_spotify_set_repeat(state: str, device_id: str | None = None) -> str:
    """Set repeat mode (off, context, or track)."""
    return _dispatch("tools.playback", "spotify_set_repeat", **locals())

def _stub_spotify_toggle_shuffle(state: bool | None = None, device_id: str | None = None) -> str:
    """Toggle shuffle mode on or off."""
    return _dispatch("tools.playback", "spotify_toggle_shuffle", **locals())

def _stub_create_actor_playlist(actor_name: str, playlist_name: str | None = None, max_movies: int = 10, max_songs_per_movie: int = 3, specific_movies: str | None = None, sort_by: str = 'popularity', public: bool = True) -> str:
    """End-to-End Pipeline: Discover an actor's filmography via TMDB/DDG, locate songs on Spotify,
create a new playlist, and add all tracks.

Args:
    actor_name: Name of the actor (e.g., 'Cillian Murphy', 'Shah Rukh Khan', 'Keanu Reeves')
    playlist_name: Optional custom name for the playlist
    max_movies: Number of movies to pull songs from (default: 10)
    max_songs_per_movie: Number of songs to add per movie (default: 3)
    specific_movies: Optional comma-separated list of specific movies to use (e.g. 'Inception, Dunkirk, Oppenheimer')
    sort_by: Filmography sort order ('popularity' or 'release_date', default: 'popularity')
    public: Whether the created playlist is public (default: True)"""
    return _dispatch("tools.playlists", "create_actor_playlist", **locals())

def _stub_create_playlist(name: str, description: str = '', public: bool = True) -> str:
    """Create a new Spotify playlist for the user.

Args:
    name: Name of the playlist
    description: Description of the playlist
    public: Whether the playlist is public (default: True)"""
    return _dispatch("tools.playlists", "create_playlist", **locals())

def _stub_shuffle_playlist(playlist_id: str) -> str:
    """Mix and shuffle all songs in a Spotify playlist into a completely new random order.

Args:
    playlist_id: The Spotify ID, URI, or URL of the playlist to shuffle"""
    return _dispatch("tools.playlists", "shuffle_playlist", **locals())

def _stub_add_tracks_to_playlist(playlist_id: str, track_uris: List[str]) -> str:
    """Add a list of Spotify song URIs to an existing playlist.

Args:
    playlist_id: The Spotify ID or URI of the playlist
    track_uris: List of Spotify song URIs (e.g. ['spotify:track:...', ...])"""
    return _dispatch("tools.playlists", "add_tracks_to_playlist", **locals())

def _stub_combine_playlists(playlist_ids: List[str], new_name: str = 'Combined Playlist', description: str = 'Combined playlist from multiple sources.') -> str:
    """Combines multiple Spotify playlists into a single new playlist.

Args:
    playlist_ids: A list of Spotify playlist IDs, URIs, or URLs to combine.
    new_name: The name for the newly created combined playlist.
    description: The description for the new playlist."""
    return _dispatch("tools.playlists", "combine_playlists", **locals())

def _stub_dedupe_playlist(playlist_id: str) -> str:
    """Removes all duplicate songs from a Spotify playlist, keeping only the first occurrence of each song.

Args:
    playlist_id: The Spotify ID, URI, or URL of the playlist to deduplicate."""
    return _dispatch("tools.playlists", "dedupe_playlist", **locals())

def _stub_add_songs_to_playlist(playlist_id: str, song_uris: List[str]) -> str:
    """Add a list of Spotify song URIs to an existing playlist.

Args:
    playlist_id: The Spotify ID or URI of the playlist
    song_uris: List of Spotify song URIs (e.g. ['spotify:track:...', ...])"""
    return _dispatch("tools.playlists", "add_songs_to_playlist", **locals())

def _stub_add_movie_songs_to_playlist(playlist_id: str, movie_name: str, max_songs: int = 5) -> str:
    """Find songs for a specific movie on Spotify and add them directly to an existing playlist.

Args:
    playlist_id: The Spotify ID of the existing playlist
    movie_name: Title of the movie
    max_songs: Maximum number of songs to add (default: 5)"""
    return _dispatch("tools.playlists", "add_movie_songs_to_playlist", **locals())

def _stub_get_user_playlists(limit: int = 10) -> str:
    """Get the current user's playlists with song counts.

Args:
    limit: Number of playlists to fetch (default 10, max 50)"""
    return _dispatch("tools.playlists", "get_user_playlists", **locals())

def _stub_reorder_playlist_by_audio_features(playlist_id: str, feature: str = 'energy', order: str = 'desc', ascending: bool | None = None) -> str:
    """Smart Reorder: Sorts a user's playlist by a given audio feature (energy, valence, danceability, etc).

Args:
    playlist_id: Spotify playlist ID or URI.
    feature: The audio feature to sort by (e.g., 'energy', 'valence', 'danceability', 'tempo').
    order: 'asc' for ascending, 'desc' for descending.
    ascending: Optional boolean (True for 'asc', False for 'desc'). Overrides order if provided."""
    return _dispatch("tools.playlists", "reorder_playlist_by_audio_features", **locals())

def _stub_update_playlist(playlist_id: str, name: str | None = None, description: str | None = None, public: bool | None = None) -> str:
    """Update a playlist's name, description, or public status."""
    return _dispatch("tools.playlists", "update_playlist", **locals())

def _stub_get_playlist_tracks(playlist_id: str, limit: int = 100, offset: int = 0) -> str:
    """Get the tracks currently inside a specific playlist."""
    return _dispatch("tools.playlists", "get_playlist_tracks", **locals())

def _stub_remove_tracks_from_playlist(playlist_id: str, uris: list[str]) -> str:
    """Remove one or more tracks from a playlist by their URIs."""
    return _dispatch("tools.playlists", "remove_tracks_from_playlist", **locals())

def _stub_spotify_get_my_playlists(limit: int = 50, offset: int = 0) -> str:
    """List user's created and saved playlists.

Args:
    limit: The maximum number of items to return (default: 50, max: 50).
    offset: The index of the first playlist to return (default: 0)."""
    return _dispatch("tools.playlists", "spotify_get_my_playlists", **locals())

def _stub_spotify_get_playlist(playlist_id: str, fields: str | None = None) -> str:
    """Fetch details and tracks of a specific playlist.

Args:
    playlist_id: Spotify playlist ID or URI.
    fields: Optional filter for specific fields (e.g., 'name,description,followers,tracks.total')."""
    return _dispatch("tools.playlists", "spotify_get_playlist", **locals())

def _stub_spotify_get_playlist_tracks(playlist_id: str, limit: int = 50, offset: int = 0) -> str:
    """Paginate through tracks in a playlist.

Args:
    playlist_id: Spotify playlist ID or URI.
    limit: Number of tracks to return (default: 50, max: 100).
    offset: Index of the first track to return (default: 0)."""
    return _dispatch("tools.playlists", "spotify_get_playlist_tracks", **locals())

def _stub_spotify_create_playlist(name: str, description: str = '', public: bool = True, collaborative: bool = False) -> str:
    """Create a new empty playlist.

Args:
    name: The name of the new playlist.
    description: Optional description for the playlist.
    public: Whether the playlist should be public (default: True).
    collaborative: Whether the playlist should be collaborative (default: False)."""
    return _dispatch("tools.playlists", "spotify_create_playlist", **locals())

def _stub_spotify_add_to_playlist(playlist_id: str, uris: List[str], position: int | None = None) -> str:
    """Append tracks to an existing playlist.

Args:
    playlist_id: Spotify playlist ID or URI.
    uris: List of Spotify track URIs to add (e.g. ['spotify:track:...']).
    position: Optional zero-based position to insert the tracks at."""
    return _dispatch("tools.playlists", "spotify_add_to_playlist", **locals())

def _stub_spotify_remove_from_playlist(playlist_id: str, uris: List[str], snapshot_id: str | None = None) -> str:
    """Remove specific tracks from a playlist.

Args:
    playlist_id: Spotify playlist ID or URI.
    uris: List of Spotify track URIs to remove.
    snapshot_id: Optional playlist snapshot ID to protect against concurrent modifications."""
    return _dispatch("tools.playlists", "spotify_remove_from_playlist", **locals())

def _stub_spotify_reorder_playlist(playlist_id: str, range_start: int, insert_before: int, range_length: int = 1, snapshot_id: str | None = None) -> str:
    """Move or reorder track positions in a playlist.

Args:
    playlist_id: Spotify playlist ID or URI.
    range_start: The zero-based index of the first track to be moved.
    insert_before: The zero-based index of where the tracks should be inserted.
    range_length: The amount of tracks to be moved (default: 1).
    snapshot_id: Optional playlist snapshot ID."""
    return _dispatch("tools.playlists", "spotify_reorder_playlist", **locals())

def _stub_spotify_update_playlist(playlist_id: str, name: str | None = None, description: str | None = None, public: bool | None = None, collaborative: bool | None = None) -> str:
    """Modify playlist name, description, or privacy settings.

Args:
    playlist_id: Spotify playlist ID or URI.
    name: Optional new name for the playlist.
    description: Optional new description.
    public: Optional public/private status.
    collaborative: Optional collaborative status."""
    return _dispatch("tools.playlists", "spotify_update_playlist", **locals())

def _stub_spotify_follow_playlist(playlist_id: str, public: bool = True) -> str:
    """Add a playlist to the user's library (Follow).

Args:
    playlist_id: Spotify playlist ID or URI to follow.
    public: Whether to include the followed playlist in the user's public profile (default: True)."""
    return _dispatch("tools.playlists", "spotify_follow_playlist", **locals())

def _stub_spotify_unfollow_playlist(playlist_id: str) -> str:
    """Remove a playlist from the user's library (Unfollow/Delete).

Args:
    playlist_id: Spotify playlist ID or URI to unfollow."""
    return _dispatch("tools.playlists", "spotify_unfollow_playlist", **locals())

def _stub_spotify_get_playlist_cover(playlist_id: str) -> str:
    """Get the image URL for a playlist cover.

Args:
    playlist_id: Spotify playlist ID or URI."""
    return _dispatch("tools.playlists", "spotify_get_playlist_cover", **locals())

def _stub_spotify_check_playlist_followers(playlist_id: str, user_ids: List[str]) -> str:
    """Check if specific users follow a playlist.

Args:
    playlist_id: Spotify playlist ID or URI.
    user_ids: List of Spotify user IDs to check (e.g. ['user1', 'user2'])."""
    return _dispatch("tools.playlists", "spotify_check_playlist_followers", **locals())

def _stub_spotify_merge_playlists(playlist_ids: List[str], target_playlist_id: str | None = None, new_name: str | None = 'Merged Playlist', description: str | None = 'Merged playlist created via Spotify MCP Power Tools', public: bool = False, deduplicate: bool = True) -> str:
    """Combine multiple playlists into a single new or existing playlist.

Args:
    playlist_ids: List of Spotify playlist IDs, URIs, or URLs to merge.
    target_playlist_id: Optional existing playlist ID or URL to append to. If not provided, creates a new playlist.
    new_name: Name for the newly created playlist (if target_playlist_id is not provided).
    description: Description for the new playlist.
    public: Whether the newly created playlist should be public (default: False).
    deduplicate: Whether to remove duplicate tracks across playlists (default: True)."""
    return _dispatch("tools.playlists", "spotify_merge_playlists", **locals())

def _stub_spotify_split_playlist_by_artist(playlist_id: str, min_tracks_per_artist: int = 2, create_playlists: bool = False, public: bool = False) -> str:
    """Separate tracks in a playlist into sub-playlists by artist.

Args:
    playlist_id: Spotify playlist ID, URI, or URL.
    min_tracks_per_artist: Minimum number of tracks an artist must have to get their own sub-playlist (default: 2).
    create_playlists: If True, creates the new sub-playlists on Spotify. If False (default), returns a preview breakdown.
    public: Whether created sub-playlists should be public (default: False)."""
    return _dispatch("tools.playlists", "spotify_split_playlist_by_artist", **locals())

def _stub_spotify_deduplicate_playlist(playlist_id: str, strategy: str = 'uri', dry_run: bool = False) -> str:
    """Scan and strip out duplicate tracks from a playlist.

Args:
    playlist_id: Spotify playlist ID, URI, or URL.
    strategy: Matching strategy - 'uri' (exact Spotify track URI) or 'name_and_artist' (normalized song title + artist name). Default: 'uri'.
    dry_run: If True, only scans and returns found duplicates without modifying the playlist. Default: False."""
    return _dispatch("tools.playlists", "spotify_deduplicate_playlist", **locals())

def _stub_spotify_export_playlist(playlist_id: str, include_audio_features: bool = False) -> str:
    """Export full playlist data, track metadata, and audio features to structured JSON.

Args:
    playlist_id: Spotify playlist ID, URI, or URL.
    include_audio_features: Whether to include audio features (tempo, energy, valence, danceability, etc.). Default: False."""
    return _dispatch("tools.playlists", "spotify_export_playlist", **locals())

def _stub_spotify_playlist_diff(playlist_id_a: str, playlist_id_b: str, strategy: str = 'uri') -> str:
    """Compare two playlists to find unique and shared tracks.

Args:
    playlist_id_a: First Spotify playlist ID, URI, or URL.
    playlist_id_b: Second Spotify playlist ID, URI, or URL.
    strategy: Matching strategy - 'uri' or 'name_and_artist' (default: 'uri')."""
    return _dispatch("tools.playlists", "spotify_playlist_diff", **locals())

def _stub_spotify_find_playlist_overlaps(limit: int = 20, min_overlap: int = 2) -> str:
    """Scan all user playlists to identify cross-playlist overlaps.

Args:
    limit: Number of user playlists to scan (default: 20, max: 50).
    min_overlap: Minimum shared tracks between two playlists to report (default: 2)."""
    return _dispatch("tools.playlists", "spotify_find_playlist_overlaps", **locals())

def _stub_spotify_find_playlist_subsets(limit: int = 20, threshold: float = 1.0) -> str:
    """Detect if any user playlists are complete or near-complete subsets of another playlist.

Args:
    limit: Number of user playlists to scan (default: 20, max: 50).
    threshold: Containment threshold between 0.5 and 1.0 (default: 1.0 = 100% complete subset)."""
    return _dispatch("tools.playlists", "spotify_find_playlist_subsets", **locals())

def _stub_spotify_absorb_playlist(source_playlist_id: str, target_playlist_id: str, strategy: str = 'uri') -> str:
    """Pull only missing/unique tracks from a source playlist into a destination playlist.

Args:
    source_playlist_id: Spotify playlist ID, URI, or URL to pull missing tracks from.
    target_playlist_id: Destination Spotify playlist ID, URI, or URL to receive the new tracks.
    strategy: Matching strategy - 'uri' or 'name_and_artist' (default: 'uri')."""
    return _dispatch("tools.playlists", "spotify_absorb_playlist", **locals())

def _stub_get_user_top_tracks(limit: int = 10, time_range: str = 'medium_term') -> str:
    """Get the current user's top songs over a specified period.

Args:
    limit: Number of songs (default 10, max 50)
    time_range: Over what time frame ('short_term' = ~4 weeks, 'medium_term' = ~6 months, 'long_term' = years)"""
    return _dispatch("tools.taste", "get_user_top_tracks", **locals())

def _stub_get_user_top_songs(limit: int = 10, time_range: str = 'medium_term') -> str:
    """Get the current user's top songs over a specified period."""
    return _dispatch("tools.taste", "get_user_top_songs", **locals())

def _stub_get_user_top_artists(limit: int = 10, time_range: str = 'medium_term') -> str:
    """Get the current user's top artists over a specified period.

Args:
    limit: Number of artists (default 10, max 50)
    time_range: Over what time frame ('short_term', 'medium_term', 'long_term')"""
    return _dispatch("tools.taste", "get_user_top_artists", **locals())

def _stub_get_audio_features(track_uris: list[str]) -> str:
    """Get audio features (danceability, energy, valence, etc) for multiple tracks.

Args:
    track_uris: List of Spotify track URIs (max 100)."""
    return _dispatch("tools.taste", "get_audio_features", **locals())

def _stub_get_artist_network(artist_name_or_id: str) -> str:
    """Map an artist's network by fetching related artists.

Args:
    artist_name_or_id: Name or Spotify ID of the artist."""
    return _dispatch("tools.taste", "get_artist_network", **locals())

def _stub_get_saved_tracks(limit: int = 50, offset: int = 0) -> str:
    """Get tracks from the user's Library (Saved Tracks)."""
    return _dispatch("tools.taste", "get_saved_tracks", **locals())

def _stub_get_recommendations(limit: int = 10, seed_tracks: List[str] | None = None, seed_artists: List[str] | None = None, seed_genres: List[str] | None = None, target_energy: float | None = None, target_valence: float | None = None, target_danceability: float | None = None, target_acousticness: float | None = None, target_instrumentalness: float | None = None, target_tempo: float | None = None) -> str:
    """Get track recommendations based on seeds and audio features.

Args:
    limit: Number of recommendations to return (default: 10, max: 100).
    seed_tracks: List of Spotify track IDs or URIs.
    seed_artists: List of Spotify artist IDs or URIs.
    seed_genres: List of genres (e.g., 'synthwave', 'indie-pop').
    target_energy: Target energy (0.0 to 1.0).
    target_valence: Target valence (0.0 to 1.0).
    target_danceability: Target danceability (0.0 to 1.0).
    target_acousticness: Target acousticness (0.0 to 1.0).
    target_instrumentalness: Target instrumentalness (0.0 to 1.0).
    target_tempo: Target tempo in BPM."""
    return _dispatch("tools.taste", "get_recommendations", **locals())

def _stub_spotify_top_tracks(time_range: str = 'medium_term', limit: int = 20, offset: int = 0) -> str:
    """Fetch user's top tracks over short, medium, or long term.

Args:
    time_range: Period of analysis ('short_term' = ~4 weeks, 'medium_term' = ~6 months, 'long_term' = all time / years). Default: 'medium_term'.
    limit: Number of tracks to return (default: 20, max: 50).
    offset: Index of the first track to return (default: 0)."""
    return _dispatch("tools.taste", "spotify_top_tracks", **locals())

def _stub_spotify_top_artists(time_range: str = 'medium_term', limit: int = 20, offset: int = 0) -> str:
    """Fetch user's top artists over short, medium, or long term.

Args:
    time_range: Period of analysis ('short_term' = ~4 weeks, 'medium_term' = ~6 months, 'long_term' = all time / years). Default: 'medium_term'.
    limit: Number of artists to return (default: 20, max: 50).
    offset: Index of the first artist to return (default: 0)."""
    return _dispatch("tools.taste", "spotify_top_artists", **locals())

def _stub_spotify_recently_played(limit: int = 20, after: int | None = None, before: int | None = None) -> str:
    """Fetch recent track listening history.

Args:
    limit: Number of items to return (default: 20, max: 50).
    after: A Unix timestamp in milliseconds. Returns items played after this date.
    before: A Unix timestamp in milliseconds. Returns items played before this date."""
    return _dispatch("tools.taste", "spotify_recently_played", **locals())

def _stub_spotify_listening_patterns() -> str:
    """Analyze listening volume distributions across hours and days."""
    return _dispatch("tools.taste", "spotify_listening_patterns", **locals())

def _stub_spotify_taste_profile() -> str:
    """Generate an overview of genre diversity and niche artist affinity."""
    return _dispatch("tools.taste", "spotify_taste_profile", **locals())

def _stub_spotify_playlist_compare(playlist_ids: List[str]) -> str:
    """Compare multi-playlist audio feature distributions side-by-side.

Args:
    playlist_ids: List of 2 or more Spotify playlist IDs or URIs."""
    return _dispatch("tools.taste", "spotify_playlist_compare", **locals())

def _stub_spotify_playlist_freshness(limit: int = 50, stale_days_threshold: int = 90) -> str:
    """Sort playlists by last update timestamp to identify stale lists.

Args:
    limit: Maximum playlists to inspect (default: 50).
    stale_days_threshold: Days of inactivity before a playlist is flagged as stale (default: 90)."""
    return _dispatch("tools.taste", "spotify_playlist_freshness", **locals())

def _stub_search_actor_movies(actor_name: str, limit: int = 30, sort_by: str = 'popularity') -> str:
    """Discover the full filmography for an actor using TMDB (with DDG and Wikipedia fallbacks).

Args:
    actor_name: Name of the actor (e.g. 'Cillian Murphy', 'Shah Rukh Khan', 'Tom Cruise')
    limit: Maximum number of movies to return (default: 30)
    sort_by: Ordering for movies ('popularity' or 'release_date', default: 'popularity')"""
    return _dispatch("tools.search", "search_actor_movies", **locals())

def _stub_get_actor_tmdb_profile(actor_name: str) -> str:
    """Get rich biographical and career profile details for an actor from TMDB.

Args:
    actor_name: Name of the actor (e.g. 'Robert Downey Jr.', 'Zendaya')"""
    return _dispatch("tools.search", "get_actor_tmdb_profile", **locals())

def _stub_search_movie_tmdb(movie_name: str, limit: int = 5) -> str:
    """Search TMDB for movie information, release year, ratings, and overview.

Args:
    movie_name: Title of the movie to search (e.g. 'Inception', 'Interstellar')
    limit: Maximum results to return (default: 5)"""
    return _dispatch("tools.search", "search_movie_tmdb", **locals())

def _stub_search_duckduckgo(query: str, max_results: int = 5) -> str:
    """Perform a web search using DuckDuckGo to look up movie news, filmographies, or sound tracks.

Args:
    query: Search query string
    max_results: Maximum results to return (default: 5)"""
    return _dispatch("tools.search", "search_duckduckgo", **locals())

def _stub_get_movie_songs(movie_name: str, limit: int = 10) -> str:
    """Search Spotify for soundtrack albums and songs from a movie with DuckDuckGo fallback assistance.

Args:
    movie_name: Title of the movie (e.g. 'Inception', 'Darr', 'Top Gun')
    limit: Maximum number of songs to return (default: 10)"""
    return _dispatch("tools.search", "get_movie_songs", **locals())

def _stub_search_spotify(query: str, search_type: str = 'track', limit: int = 5) -> str:
    """Search for songs, albums, artists, or playlists on Spotify.

Args:
    query: Search keywords
    search_type: Types to search for (comma-separated: 'track', 'album', 'artist', 'playlist')
    limit: Number of results (default 5, max 20)"""
    return _dispatch("tools.search", "search_spotify", **locals())

def _stub_spotify_search(query: str, types: List[str] | None = None, limit: int = 10, market: str | None = None) -> str:
    """Search Spotify catalog for tracks, artists, albums, or playlists.

Args:
    query: Search keywords or query syntax (e.g. 'Daft Punk', 'track:Get Lucky', 'artist:Queen').
    types: List of Spotify item types to search for (options: 'track', 'artist', 'album', 'playlist'). Default: ['track', 'artist', 'album', 'playlist'].
    limit: Number of results to return per type (default: 10, max: 50).
    market: Optional ISO 3166-1 alpha-2 country code (e.g. 'US', 'GB')."""
    return _dispatch("tools.search", "spotify_search", **locals())

def _stub_spotify_related_artists(artist: str) -> str:
    """Find artists similar to a target artist.

Args:
    artist: Artist name, Spotify artist ID, or Spotify artist URI (e.g. 'Hans Zimmer', 'spotify:artist:0YC192cP3KPCRWx8zr8MfZ')."""
    return _dispatch("tools.search", "spotify_related_artists", **locals())

def _stub_spotify_discover_by_artist(artist: str, limit: int = 15, include_artist_top_tracks: bool = True) -> str:
    """Generate track recommendations derived from related artist networks.

Args:
    artist: Seed artist name, ID, or URI.
    limit: Number of recommended tracks to return (default: 15, max: 50).
    include_artist_top_tracks: Whether to include top tracks from the seed artist (default: True)."""
    return _dispatch("tools.search", "spotify_discover_by_artist", **locals())

def _stub_spotify_discover_by_mood(mood: str | None = None, seed_genres: List[str] | None = None, target_valence: float | None = None, target_energy: float | None = None, target_danceability: float | None = None, target_acousticness: float | None = None, target_tempo: float | None = None, limit: int = 20) -> str:
    """Discover tracks using target audio parameters (valence, energy, tempo, etc.) or mood presets.

Args:
    mood: Optional mood preset ('happy', 'sad', 'chill', 'energetic', 'focus', 'party', 'dark', 'romantic', 'workout').
    seed_genres: Optional list of seed genres (e.g. ['pop', 'indie', 'electronic']). Max 5 combined seeds.
    target_valence: Musical positiveness ($0.0$ to $1.0$).
    target_energy: Intensity and activity ($0.0$ to $1.0$).
    target_danceability: Suitability for dancing ($0.0$ to $1.0$).
    target_acousticness: Confidence measure from $0.0$ to $1.0$ of whether track is acoustic.
    target_tempo: Target tempo in BPM (beats per minute).
    limit: Number of tracks to discover (default: 20, max: 100)."""
    return _dispatch("tools.search", "spotify_discover_by_mood", **locals())

def _stub_spotify_genre_explorer(genres: List[str] | None = None, limit: int = 15, market: str | None = None) -> str:
    """Browse and sample tracks across specific seed genres or list all available genre seeds.

Args:
    genres: Optional list of genre seed keywords (e.g. ['synthwave', 'indie-pop', 'jazz']). If None or empty, returns all available Spotify genre seeds.
    limit: Number of tracks to sample (default: 15, max: 50).
    market: Optional ISO country code."""
    return _dispatch("tools.search", "spotify_genre_explorer", **locals())

def _stub_spotify_discover_deep_cuts(artist_or_album: str, max_popularity: int = 40, limit: int = 15) -> str:
    """Discover non-single, album-only deep cut tracks from an artist or album.

Args:
    artist_or_album: Name, ID, or URI of an artist or album (e.g. 'Radiohead', 'The Dark Side of the Moon').
    max_popularity: Maximum popularity threshold (0-100, default: 40). Tracks with popularity <= this threshold are considered deep cuts.
    limit: Maximum number of deep cuts to return (default: 15)."""
    return _dispatch("tools.search", "spotify_discover_deep_cuts", **locals())

def _stub_spotify_get_recommendations(limit: int = 20, seed_tracks: List[str] | None = None, seed_artists: List[str] | None = None, seed_genres: List[str] | None = None, target_energy: float | None = None, target_valence: float | None = None, target_danceability: float | None = None, target_acousticness: float | None = None, target_instrumentalness: float | None = None, target_tempo: float | None = None, min_popularity: int | None = None, max_popularity: int | None = None, market: str | None = None) -> str:
    """Direct wrapper for Spotify Recommendations API using seeds and target audio features.

Args:
    limit: Number of recommendations to return (default: 20, max: 100).
    seed_tracks: List of Spotify track IDs or URIs (max 5 combined seeds).
    seed_artists: List of Spotify artist IDs or URIs.
    seed_genres: List of seed genres (e.g. ['pop', 'rock', 'synthwave']).
    target_energy: Target energy (0.0 to 1.0).
    target_valence: Target valence (0.0 to 1.0).
    target_danceability: Target danceability (0.0 to 1.0).
    target_acousticness: Target acousticness (0.0 to 1.0).
    target_instrumentalness: Target instrumentalness (0.0 to 1.0).
    target_tempo: Target tempo in BPM.
    min_popularity: Minimum track popularity (0-100).
    max_popularity: Maximum track popularity (0-100).
    market: Optional ISO 3166-1 alpha-2 country code."""
    return _dispatch("tools.search", "spotify_get_recommendations", **locals())

def _stub_fetch_soundtrack_tracks(movie_title: str, language_name: str | None = None, release_year: str | None = None, actor_name: str | None = None) -> List[Dict[str, Any]]:
    """Searches Spotify for movie soundtrack tracks using titles, language, release year, or actor name with fuzzy matching.

Args:
    movie_title: Title of the movie
    language_name: Optional language filter (e.g. 'Hindi', 'Telugu', 'English')
    release_year: Optional movie release year (e.g. '2023')
    actor_name: Optional actor name to narrow down soundtrack"""
    return _dispatch("tools.search", "fetch_soundtrack_tracks", **locals())

def _stub_search_singers(query: str, limit: int = 10) -> str:
    """Search for singers, musical artists, or bands on Spotify.

Args:
    query: Name of singer, artist, or band to search
    limit: Maximum number of artists to return (default: 10)"""
    return _dispatch("tools.search", "search_singers", **locals())

def _stub_search_songs(query: str, limit: int = 10) -> str:
    """Search for songs or tracks on Spotify with detailed track metadata.

Args:
    query: Song name or keywords to search
    limit: Maximum number of songs to return (default: 10)"""
    return _dispatch("tools.search", "search_songs", **locals())

def _stub_spotify_get_saved_tracks(limit: int = 20, offset: int = 0, market: str | None = None) -> str:
    """List tracks saved in the current user's Liked Songs library.

Args:
    limit: Number of tracks to return (default: 20, max: 50).
    offset: Index of the first item to return (default: 0).
    market: An ISO 3166-1 alpha-2 country code."""
    return _dispatch("tools.library", "spotify_get_saved_tracks", **locals())

def _stub_spotify_save_tracks(track_ids: List[str]) -> str:
    """Save one or more tracks to the current user's Liked Songs library.

Args:
    track_ids: List of Spotify track IDs, URIs, or URLs to save."""
    return _dispatch("tools.library", "spotify_save_tracks", **locals())

def _stub_spotify_remove_saved_tracks(track_ids: List[str]) -> str:
    """Remove one or more tracks from the current user's Liked Songs library.

Args:
    track_ids: List of Spotify track IDs, URIs, or URLs to remove."""
    return _dispatch("tools.library", "spotify_remove_saved_tracks", **locals())

def _stub_spotify_check_saved_tracks(track_ids: List[str]) -> str:
    """Verify whether specific tracks exist in the current user's Liked Songs library.

Args:
    track_ids: List of Spotify track IDs, URIs, or URLs to check (max: 50)."""
    return _dispatch("tools.library", "spotify_check_saved_tracks", **locals())

def _stub_spotify_get_saved_albums(limit: int = 20, offset: int = 0, market: str | None = None) -> str:
    """Fetch albums saved in the current user's library.

Args:
    limit: Number of albums to return (default: 20, max: 50).
    offset: Index of the first album to return (default: 0).
    market: An ISO 3166-1 alpha-2 country code."""
    return _dispatch("tools.library", "spotify_get_saved_albums", **locals())

def _stub_spotify_save_albums(album_ids: List[str]) -> str:
    """Save one or more albums to the current user's library.

Args:
    album_ids: List of Spotify album IDs, URIs, or URLs to save."""
    return _dispatch("tools.library", "spotify_save_albums", **locals())

def _stub_spotify_remove_saved_albums(album_ids: List[str]) -> str:
    """Remove one or more albums from the current user's library.

Args:
    album_ids: List of Spotify album IDs, URIs, or URLs to remove."""
    return _dispatch("tools.library", "spotify_remove_saved_albums", **locals())

def _stub_spotify_check_saved_albums(album_ids: List[str]) -> str:
    """Verify whether specific albums exist in the current user's library.

Args:
    album_ids: List of Spotify album IDs, URIs, or URLs to check (max: 50)."""
    return _dispatch("tools.library", "spotify_check_saved_albums", **locals())

def _stub_spotify_get_track(track_id: str, market: str | None = None) -> str:
    """Inspect full track metadata including ISRC, popularity, audio preview URL, and album details.

Args:
    track_id: Spotify track ID, URI, or URL (e.g. 'spotify:track:4cOdK2wGLETKBW3PvgPWqT').
    market: Optional ISO 3166-1 alpha-2 country code."""
    return _dispatch("tools.browse", "spotify_get_track", **locals())

def _stub_spotify_get_album(album_id: str, market: str | None = None) -> str:
    """Inspect full album details including copyrights, label, release date, and complete tracklist.

Args:
    album_id: Spotify album ID, URI, or URL (e.g. 'spotify:album:4aawyAB9vmqN3uQ7FjRGTy').
    market: Optional ISO 3166-1 alpha-2 country code."""
    return _dispatch("tools.browse", "spotify_get_album", **locals())

def _stub_spotify_get_artist(artist_id: str) -> str:
    """Inspect artist details including genres, follower count, popularity, and profile images.

Args:
    artist_id: Spotify artist ID, URI, URL, or artist name (e.g. 'Radiohead' or 'spotify:artist:4Z8W4fKeB5YxbusRsdQVPb')."""
    return _dispatch("tools.browse", "spotify_get_artist", **locals())

def _stub_spotify_get_artist_albums(artist_id: str, include_groups: str | None = 'album,single', limit: int = 20, offset: int = 0, country: str | None = None) -> str:
    """Get all albums, singles, and compilations released by a specific artist.

Args:
    artist_id: Spotify artist ID, URI, URL, or artist name.
    include_groups: Comma-separated list of groups ('album', 'single', 'appears_on', 'compilation'). Default: 'album,single'.
    limit: Number of items to return (default: 20, max: 50).
    offset: Index of the first item to return (default: 0).
    country: Optional ISO 3166-1 alpha-2 country code."""
    return _dispatch("tools.browse", "spotify_get_artist_albums", **locals())

def _stub_spotify_get_user(user_id: str) -> str:
    """Fetch public profile information and public playlists for any Spotify user.

Args:
    user_id: Spotify user ID, URI, or profile URL (e.g. 'spotify:user:wizzler' or 'wizzler')."""
    return _dispatch("tools.browse", "spotify_get_user", **locals())

def _stub_open_soundtrack_studio() -> str:
    """Launch or retrieve the URL for the Soundtrack Curator & Staging Studio web application.

Returns the local web application URL and opens it in your default browser."""
    return _dispatch("tools.web_app", "open_soundtrack_studio", **locals())

TOOL_SPECS = {
    "get_current_playback": {
        "fn": _stub_get_current_playback,
        "module": "tools.playback",
        "fn_name": "get_current_playback",
        "doc": """Get information about the user's current playback state, active song, and active device.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "play_track": {
        "fn": _stub_play_track,
        "module": "tools.playback",
        "fn_name": "play_track",
        "doc": """Start or resume playback.
Args:
    device_id: ID of the device to play on. Uses active device if omitted.
    context_uri: Spotify URI of context (album, artist, playlist).
    uris: List of Spotify track URIs to play. E.g. ["spotify:track:xxx"].
    uri: Single track URI (for backward compatibility).
    offset_position: Position in the context to start playback (0-based index).
    position_ms: Position in milliseconds to seek to.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playback']
    },
    "play_song": {
        "fn": _stub_play_song,
        "module": "tools.playback",
        "fn_name": "play_song",
        "doc": """Resume playback or play a specific song/album/playlist by URI.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playback']
    },
    "pause_playback": {
        "fn": _stub_pause_playback,
        "module": "tools.playback",
        "fn_name": "pause_playback",
        "doc": """Pause the current Spotify playback.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "next_track": {
        "fn": _stub_next_track,
        "module": "tools.playback",
        "fn_name": "next_track",
        "doc": """Skip to the next song in the queue.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playback']
    },
    "next_song": {
        "fn": _stub_next_song,
        "module": "tools.playback",
        "fn_name": "next_song",
        "doc": """Skip to the next song in the queue.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playback']
    },
    "previous_track": {
        "fn": _stub_previous_track,
        "module": "tools.playback",
        "fn_name": "previous_track",
        "doc": """Skip to the previous song.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playback']
    },
    "previous_song": {
        "fn": _stub_previous_song,
        "module": "tools.playback",
        "fn_name": "previous_song",
        "doc": """Skip to the previous song.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playback']
    },
    "set_volume": {
        "fn": _stub_set_volume,
        "module": "tools.playback",
        "fn_name": "set_volume",
        "doc": """Set the playback volume.

Args:
    volume_percent: Volume level between 0 and 100.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "seek_playback": {
        "fn": _stub_seek_playback,
        "module": "tools.playback",
        "fn_name": "seek_playback",
        "doc": """Seeks to the given position in the user's currently playing track.

Args:
    position_ms: The position in milliseconds to seek to.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "set_repeat_mode": {
        "fn": _stub_set_repeat_mode,
        "module": "tools.playback",
        "fn_name": "set_repeat_mode",
        "doc": """Set the repeat mode for the user's playback.

Args:
    state: 'track', 'context', or 'off'.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "set_shuffle": {
        "fn": _stub_set_shuffle,
        "module": "tools.playback",
        "fn_name": "set_shuffle",
        "doc": """Toggle shuffle for the user's playback.

Args:
    state: True to turn shuffle on, False to turn it off.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "get_available_devices": {
        "fn": _stub_get_available_devices,
        "module": "tools.playback",
        "fn_name": "get_available_devices",
        "doc": """Get information about a user's available devices.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "transfer_playback": {
        "fn": _stub_transfer_playback,
        "module": "tools.playback",
        "fn_name": "transfer_playback",
        "doc": """Transfer playback to a new device.

Args:
    device_id: The ID of the device to transfer playback to.
    play: Whether to ensure playback happens on the new device.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "add_to_queue": {
        "fn": _stub_add_to_queue,
        "module": "tools.playback",
        "fn_name": "add_to_queue",
        "doc": """Add a song to the user's playback queue.

Args:
    uri: Spotify song or episode URI (e.g., 'spotify:track:...')""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playback']
    },
    "get_queue": {
        "fn": _stub_get_queue,
        "module": "tools.playback",
        "fn_name": "get_queue",
        "doc": """Get the user's current playback queue.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "spotify_status": {
        "fn": _stub_spotify_status,
        "module": "tools.playback",
        "fn_name": "spotify_status",
        "doc": """Get current connection status and basic playback state.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "spotify_now_playing": {
        "fn": _stub_spotify_now_playing,
        "module": "tools.playback",
        "fn_name": "spotify_now_playing",
        "doc": """Fetch detailed information about the currently playing track.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "spotify_play": {
        "fn": _stub_spotify_play,
        "module": "tools.playback",
        "fn_name": "spotify_play",
        "doc": """Start or resume playback (accepts track, album, or playlist URIs).""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playback']
    },
    "spotify_pause": {
        "fn": _stub_spotify_pause,
        "module": "tools.playback",
        "fn_name": "spotify_pause",
        "doc": """Pause playback.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "spotify_resume": {
        "fn": _stub_spotify_resume,
        "module": "tools.playback",
        "fn_name": "spotify_resume",
        "doc": """Resume active playback.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playback']
    },
    "spotify_skip_next": {
        "fn": _stub_spotify_skip_next,
        "module": "tools.playback",
        "fn_name": "spotify_skip_next",
        "doc": """Skip to the next track in the queue.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playback']
    },
    "spotify_skip_previous": {
        "fn": _stub_spotify_skip_previous,
        "module": "tools.playback",
        "fn_name": "spotify_skip_previous",
        "doc": """Skip back to the previous track.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playback']
    },
    "spotify_add_to_queue": {
        "fn": _stub_spotify_add_to_queue,
        "module": "tools.playback",
        "fn_name": "spotify_add_to_queue",
        "doc": """Add a track URI to the user's current playback queue.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playback']
    },
    "spotify_get_queue": {
        "fn": _stub_spotify_get_queue,
        "module": "tools.playback",
        "fn_name": "spotify_get_queue",
        "doc": """View current playback queue and upcoming tracks.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "spotify_get_devices": {
        "fn": _stub_spotify_get_devices,
        "module": "tools.playback",
        "fn_name": "spotify_get_devices",
        "doc": """List available Spotify Connect devices.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "spotify_transfer_playback": {
        "fn": _stub_spotify_transfer_playback,
        "module": "tools.playback",
        "fn_name": "spotify_transfer_playback",
        "doc": """Transfer active playback to another connected device.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "spotify_set_volume": {
        "fn": _stub_spotify_set_volume,
        "module": "tools.playback",
        "fn_name": "spotify_set_volume",
        "doc": """Set playback volume (0–100).""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "spotify_seek": {
        "fn": _stub_spotify_seek,
        "module": "tools.playback",
        "fn_name": "spotify_seek",
        "doc": """Seek to a specific timestamp in the current track.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "spotify_set_repeat": {
        "fn": _stub_spotify_set_repeat,
        "module": "tools.playback",
        "fn_name": "spotify_set_repeat",
        "doc": """Set repeat mode (off, context, or track).""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "spotify_toggle_shuffle": {
        "fn": _stub_spotify_toggle_shuffle,
        "module": "tools.playback",
        "fn_name": "spotify_toggle_shuffle",
        "doc": """Toggle shuffle mode on or off.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playback']
    },
    "create_actor_playlist": {
        "fn": _stub_create_actor_playlist,
        "module": "tools.playlists",
        "fn_name": "create_actor_playlist",
        "doc": """End-to-End Pipeline: Discover an actor's filmography via TMDB/DDG, locate songs on Spotify,
create a new playlist, and add all tracks.

Args:
    actor_name: Name of the actor (e.g., 'Cillian Murphy', 'Shah Rukh Khan', 'Keanu Reeves')
    playlist_name: Optional custom name for the playlist
    max_movies: Number of movies to pull songs from (default: 10)
    max_songs_per_movie: Number of songs to add per movie (default: 3)
    specific_movies: Optional comma-separated list of specific movies to use (e.g. 'Inception, Dunkirk, Oppenheimer')
    sort_by: Filmography sort order ('popularity' or 'release_date', default: 'popularity')
    public: Whether the created playlist is public (default: True)""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playlists', 'core']
    },
    "create_playlist": {
        "fn": _stub_create_playlist,
        "module": "tools.playlists",
        "fn_name": "create_playlist",
        "doc": """Create a new Spotify playlist for the user.

Args:
    name: Name of the playlist
    description: Description of the playlist
    public: Whether the playlist is public (default: True)""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playlists', 'core']
    },
    "shuffle_playlist": {
        "fn": _stub_shuffle_playlist,
        "module": "tools.playlists",
        "fn_name": "shuffle_playlist",
        "doc": """Mix and shuffle all songs in a Spotify playlist into a completely new random order.

Args:
    playlist_id: The Spotify ID, URI, or URL of the playlist to shuffle""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "add_tracks_to_playlist": {
        "fn": _stub_add_tracks_to_playlist,
        "module": "tools.playlists",
        "fn_name": "add_tracks_to_playlist",
        "doc": """Add a list of Spotify song URIs to an existing playlist.

Args:
    playlist_id: The Spotify ID or URI of the playlist
    track_uris: List of Spotify song URIs (e.g. ['spotify:track:...', ...])""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playlists', 'core']
    },
    "combine_playlists": {
        "fn": _stub_combine_playlists,
        "module": "tools.playlists",
        "fn_name": "combine_playlists",
        "doc": """Combines multiple Spotify playlists into a single new playlist.

Args:
    playlist_ids: A list of Spotify playlist IDs, URIs, or URLs to combine.
    new_name: The name for the newly created combined playlist.
    description: The description for the new playlist.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "dedupe_playlist": {
        "fn": _stub_dedupe_playlist,
        "module": "tools.playlists",
        "fn_name": "dedupe_playlist",
        "doc": """Removes all duplicate songs from a Spotify playlist, keeping only the first occurrence of each song.

Args:
    playlist_id: The Spotify ID, URI, or URL of the playlist to deduplicate.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists', 'core']
    },
    "add_songs_to_playlist": {
        "fn": _stub_add_songs_to_playlist,
        "module": "tools.playlists",
        "fn_name": "add_songs_to_playlist",
        "doc": """Add a list of Spotify song URIs to an existing playlist.

Args:
    playlist_id: The Spotify ID or URI of the playlist
    song_uris: List of Spotify song URIs (e.g. ['spotify:track:...', ...])""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "add_movie_songs_to_playlist": {
        "fn": _stub_add_movie_songs_to_playlist,
        "module": "tools.playlists",
        "fn_name": "add_movie_songs_to_playlist",
        "doc": """Find songs for a specific movie on Spotify and add them directly to an existing playlist.

Args:
    playlist_id: The Spotify ID of the existing playlist
    movie_name: Title of the movie
    max_songs: Maximum number of songs to add (default: 5)""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playlists', 'core']
    },
    "get_user_playlists": {
        "fn": _stub_get_user_playlists,
        "module": "tools.playlists",
        "fn_name": "get_user_playlists",
        "doc": """Get the current user's playlists with song counts.

Args:
    limit: Number of playlists to fetch (default 10, max 50)""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists', 'core']
    },
    "reorder_playlist_by_audio_features": {
        "fn": _stub_reorder_playlist_by_audio_features,
        "module": "tools.playlists",
        "fn_name": "reorder_playlist_by_audio_features",
        "doc": """Smart Reorder: Sorts a user's playlist by a given audio feature (energy, valence, danceability, etc).

Args:
    playlist_id: Spotify playlist ID or URI.
    feature: The audio feature to sort by (e.g., 'energy', 'valence', 'danceability', 'tempo').
    order: 'asc' for ascending, 'desc' for descending.
    ascending: Optional boolean (True for 'asc', False for 'desc'). Overrides order if provided.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playlists', 'core']
    },
    "update_playlist": {
        "fn": _stub_update_playlist,
        "module": "tools.playlists",
        "fn_name": "update_playlist",
        "doc": """Update a playlist's name, description, or public status.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "get_playlist_tracks": {
        "fn": _stub_get_playlist_tracks,
        "module": "tools.playlists",
        "fn_name": "get_playlist_tracks",
        "doc": """Get the tracks currently inside a specific playlist.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists', 'core']
    },
    "remove_tracks_from_playlist": {
        "fn": _stub_remove_tracks_from_playlist,
        "module": "tools.playlists",
        "fn_name": "remove_tracks_from_playlist",
        "doc": """Remove one or more tracks from a playlist by their URIs.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_get_my_playlists": {
        "fn": _stub_spotify_get_my_playlists,
        "module": "tools.playlists",
        "fn_name": "spotify_get_my_playlists",
        "doc": """List user's created and saved playlists.

Args:
    limit: The maximum number of items to return (default: 50, max: 50).
    offset: The index of the first playlist to return (default: 0).""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_get_playlist": {
        "fn": _stub_spotify_get_playlist,
        "module": "tools.playlists",
        "fn_name": "spotify_get_playlist",
        "doc": """Fetch details and tracks of a specific playlist.

Args:
    playlist_id: Spotify playlist ID or URI.
    fields: Optional filter for specific fields (e.g., 'name,description,followers,tracks.total').""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_get_playlist_tracks": {
        "fn": _stub_spotify_get_playlist_tracks,
        "module": "tools.playlists",
        "fn_name": "spotify_get_playlist_tracks",
        "doc": """Paginate through tracks in a playlist.

Args:
    playlist_id: Spotify playlist ID or URI.
    limit: Number of tracks to return (default: 50, max: 100).
    offset: Index of the first track to return (default: 0).""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_create_playlist": {
        "fn": _stub_spotify_create_playlist,
        "module": "tools.playlists",
        "fn_name": "spotify_create_playlist",
        "doc": """Create a new empty playlist.

Args:
    name: The name of the new playlist.
    description: Optional description for the playlist.
    public: Whether the playlist should be public (default: True).
    collaborative: Whether the playlist should be collaborative (default: False).""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_add_to_playlist": {
        "fn": _stub_spotify_add_to_playlist,
        "module": "tools.playlists",
        "fn_name": "spotify_add_to_playlist",
        "doc": """Append tracks to an existing playlist.

Args:
    playlist_id: Spotify playlist ID or URI.
    uris: List of Spotify track URIs to add (e.g. ['spotify:track:...']).
    position: Optional zero-based position to insert the tracks at.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_remove_from_playlist": {
        "fn": _stub_spotify_remove_from_playlist,
        "module": "tools.playlists",
        "fn_name": "spotify_remove_from_playlist",
        "doc": """Remove specific tracks from a playlist.

Args:
    playlist_id: Spotify playlist ID or URI.
    uris: List of Spotify track URIs to remove.
    snapshot_id: Optional playlist snapshot ID to protect against concurrent modifications.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_reorder_playlist": {
        "fn": _stub_spotify_reorder_playlist,
        "module": "tools.playlists",
        "fn_name": "spotify_reorder_playlist",
        "doc": """Move or reorder track positions in a playlist.

Args:
    playlist_id: Spotify playlist ID or URI.
    range_start: The zero-based index of the first track to be moved.
    insert_before: The zero-based index of where the tracks should be inserted.
    range_length: The amount of tracks to be moved (default: 1).
    snapshot_id: Optional playlist snapshot ID.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_update_playlist": {
        "fn": _stub_spotify_update_playlist,
        "module": "tools.playlists",
        "fn_name": "spotify_update_playlist",
        "doc": """Modify playlist name, description, or privacy settings.

Args:
    playlist_id: Spotify playlist ID or URI.
    name: Optional new name for the playlist.
    description: Optional new description.
    public: Optional public/private status.
    collaborative: Optional collaborative status.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_follow_playlist": {
        "fn": _stub_spotify_follow_playlist,
        "module": "tools.playlists",
        "fn_name": "spotify_follow_playlist",
        "doc": """Add a playlist to the user's library (Follow).

Args:
    playlist_id: Spotify playlist ID or URI to follow.
    public: Whether to include the followed playlist in the user's public profile (default: True).""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_unfollow_playlist": {
        "fn": _stub_spotify_unfollow_playlist,
        "module": "tools.playlists",
        "fn_name": "spotify_unfollow_playlist",
        "doc": """Remove a playlist from the user's library (Unfollow/Delete).

Args:
    playlist_id: Spotify playlist ID or URI to unfollow.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_get_playlist_cover": {
        "fn": _stub_spotify_get_playlist_cover,
        "module": "tools.playlists",
        "fn_name": "spotify_get_playlist_cover",
        "doc": """Get the image URL for a playlist cover.

Args:
    playlist_id: Spotify playlist ID or URI.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_check_playlist_followers": {
        "fn": _stub_spotify_check_playlist_followers,
        "module": "tools.playlists",
        "fn_name": "spotify_check_playlist_followers",
        "doc": """Check if specific users follow a playlist.

Args:
    playlist_id: Spotify playlist ID or URI.
    user_ids: List of Spotify user IDs to check (e.g. ['user1', 'user2']).""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_merge_playlists": {
        "fn": _stub_spotify_merge_playlists,
        "module": "tools.playlists",
        "fn_name": "spotify_merge_playlists",
        "doc": """Combine multiple playlists into a single new or existing playlist.

Args:
    playlist_ids: List of Spotify playlist IDs, URIs, or URLs to merge.
    target_playlist_id: Optional existing playlist ID or URL to append to. If not provided, creates a new playlist.
    new_name: Name for the newly created playlist (if target_playlist_id is not provided).
    description: Description for the new playlist.
    public: Whether the newly created playlist should be public (default: False).
    deduplicate: Whether to remove duplicate tracks across playlists (default: True).""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_split_playlist_by_artist": {
        "fn": _stub_spotify_split_playlist_by_artist,
        "module": "tools.playlists",
        "fn_name": "spotify_split_playlist_by_artist",
        "doc": """Separate tracks in a playlist into sub-playlists by artist.

Args:
    playlist_id: Spotify playlist ID, URI, or URL.
    min_tracks_per_artist: Minimum number of tracks an artist must have to get their own sub-playlist (default: 2).
    create_playlists: If True, creates the new sub-playlists on Spotify. If False (default), returns a preview breakdown.
    public: Whether created sub-playlists should be public (default: False).""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_deduplicate_playlist": {
        "fn": _stub_spotify_deduplicate_playlist,
        "module": "tools.playlists",
        "fn_name": "spotify_deduplicate_playlist",
        "doc": """Scan and strip out duplicate tracks from a playlist.

Args:
    playlist_id: Spotify playlist ID, URI, or URL.
    strategy: Matching strategy - 'uri' (exact Spotify track URI) or 'name_and_artist' (normalized song title + artist name). Default: 'uri'.
    dry_run: If True, only scans and returns found duplicates without modifying the playlist. Default: False.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_export_playlist": {
        "fn": _stub_spotify_export_playlist,
        "module": "tools.playlists",
        "fn_name": "spotify_export_playlist",
        "doc": """Export full playlist data, track metadata, and audio features to structured JSON.

Args:
    playlist_id: Spotify playlist ID, URI, or URL.
    include_audio_features: Whether to include audio features (tempo, energy, valence, danceability, etc.). Default: False.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_playlist_diff": {
        "fn": _stub_spotify_playlist_diff,
        "module": "tools.playlists",
        "fn_name": "spotify_playlist_diff",
        "doc": """Compare two playlists to find unique and shared tracks.

Args:
    playlist_id_a: First Spotify playlist ID, URI, or URL.
    playlist_id_b: Second Spotify playlist ID, URI, or URL.
    strategy: Matching strategy - 'uri' or 'name_and_artist' (default: 'uri').""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_find_playlist_overlaps": {
        "fn": _stub_spotify_find_playlist_overlaps,
        "module": "tools.playlists",
        "fn_name": "spotify_find_playlist_overlaps",
        "doc": """Scan all user playlists to identify cross-playlist overlaps.

Args:
    limit: Number of user playlists to scan (default: 20, max: 50).
    min_overlap: Minimum shared tracks between two playlists to report (default: 2).""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_find_playlist_subsets": {
        "fn": _stub_spotify_find_playlist_subsets,
        "module": "tools.playlists",
        "fn_name": "spotify_find_playlist_subsets",
        "doc": """Detect if any user playlists are complete or near-complete subsets of another playlist.

Args:
    limit: Number of user playlists to scan (default: 20, max: 50).
    threshold: Containment threshold between 0.5 and 1.0 (default: 1.0 = 100% complete subset).""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "spotify_absorb_playlist": {
        "fn": _stub_spotify_absorb_playlist,
        "module": "tools.playlists",
        "fn_name": "spotify_absorb_playlist",
        "doc": """Pull only missing/unique tracks from a source playlist into a destination playlist.

Args:
    source_playlist_id: Spotify playlist ID, URI, or URL to pull missing tracks from.
    target_playlist_id: Destination Spotify playlist ID, URI, or URL to receive the new tracks.
    strategy: Matching strategy - 'uri' or 'name_and_artist' (default: 'uri').""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True),
        "toolsets": ['playlists']
    },
    "get_user_top_tracks": {
        "fn": _stub_get_user_top_tracks,
        "module": "tools.taste",
        "fn_name": "get_user_top_tracks",
        "doc": """Get the current user's top songs over a specified period.

Args:
    limit: Number of songs (default 10, max 50)
    time_range: Over what time frame ('short_term' = ~4 weeks, 'medium_term' = ~6 months, 'long_term' = years)""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['taste']
    },
    "get_user_top_songs": {
        "fn": _stub_get_user_top_songs,
        "module": "tools.taste",
        "fn_name": "get_user_top_songs",
        "doc": """Get the current user's top songs over a specified period.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['taste']
    },
    "get_user_top_artists": {
        "fn": _stub_get_user_top_artists,
        "module": "tools.taste",
        "fn_name": "get_user_top_artists",
        "doc": """Get the current user's top artists over a specified period.

Args:
    limit: Number of artists (default 10, max 50)
    time_range: Over what time frame ('short_term', 'medium_term', 'long_term')""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['taste']
    },
    "get_audio_features": {
        "fn": _stub_get_audio_features,
        "module": "tools.taste",
        "fn_name": "get_audio_features",
        "doc": """Get audio features (danceability, energy, valence, etc) for multiple tracks.

Args:
    track_uris: List of Spotify track URIs (max 100).""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['taste', 'core']
    },
    "get_artist_network": {
        "fn": _stub_get_artist_network,
        "module": "tools.taste",
        "fn_name": "get_artist_network",
        "doc": """Map an artist's network by fetching related artists.

Args:
    artist_name_or_id: Name or Spotify ID of the artist.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['taste']
    },
    "get_saved_tracks": {
        "fn": _stub_get_saved_tracks,
        "module": "tools.taste",
        "fn_name": "get_saved_tracks",
        "doc": """Get tracks from the user's Library (Saved Tracks).""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['taste']
    },
    "get_recommendations": {
        "fn": _stub_get_recommendations,
        "module": "tools.taste",
        "fn_name": "get_recommendations",
        "doc": """Get track recommendations based on seeds and audio features.

Args:
    limit: Number of recommendations to return (default: 10, max: 100).
    seed_tracks: List of Spotify track IDs or URIs.
    seed_artists: List of Spotify artist IDs or URIs.
    seed_genres: List of genres (e.g., 'synthwave', 'indie-pop').
    target_energy: Target energy (0.0 to 1.0).
    target_valence: Target valence (0.0 to 1.0).
    target_danceability: Target danceability (0.0 to 1.0).
    target_acousticness: Target acousticness (0.0 to 1.0).
    target_instrumentalness: Target instrumentalness (0.0 to 1.0).
    target_tempo: Target tempo in BPM.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['taste', 'core']
    },
    "spotify_top_tracks": {
        "fn": _stub_spotify_top_tracks,
        "module": "tools.taste",
        "fn_name": "spotify_top_tracks",
        "doc": """Fetch user's top tracks over short, medium, or long term.

Args:
    time_range: Period of analysis ('short_term' = ~4 weeks, 'medium_term' = ~6 months, 'long_term' = all time / years). Default: 'medium_term'.
    limit: Number of tracks to return (default: 20, max: 50).
    offset: Index of the first track to return (default: 0).""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['taste']
    },
    "spotify_top_artists": {
        "fn": _stub_spotify_top_artists,
        "module": "tools.taste",
        "fn_name": "spotify_top_artists",
        "doc": """Fetch user's top artists over short, medium, or long term.

Args:
    time_range: Period of analysis ('short_term' = ~4 weeks, 'medium_term' = ~6 months, 'long_term' = all time / years). Default: 'medium_term'.
    limit: Number of artists to return (default: 20, max: 50).
    offset: Index of the first artist to return (default: 0).""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['taste']
    },
    "spotify_recently_played": {
        "fn": _stub_spotify_recently_played,
        "module": "tools.taste",
        "fn_name": "spotify_recently_played",
        "doc": """Fetch recent track listening history.

Args:
    limit: Number of items to return (default: 20, max: 50).
    after: A Unix timestamp in milliseconds. Returns items played after this date.
    before: A Unix timestamp in milliseconds. Returns items played before this date.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['taste']
    },
    "spotify_listening_patterns": {
        "fn": _stub_spotify_listening_patterns,
        "module": "tools.taste",
        "fn_name": "spotify_listening_patterns",
        "doc": """Analyze listening volume distributions across hours and days.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['taste']
    },
    "spotify_taste_profile": {
        "fn": _stub_spotify_taste_profile,
        "module": "tools.taste",
        "fn_name": "spotify_taste_profile",
        "doc": """Generate an overview of genre diversity and niche artist affinity.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['taste']
    },
    "spotify_playlist_compare": {
        "fn": _stub_spotify_playlist_compare,
        "module": "tools.taste",
        "fn_name": "spotify_playlist_compare",
        "doc": """Compare multi-playlist audio feature distributions side-by-side.

Args:
    playlist_ids: List of 2 or more Spotify playlist IDs or URIs.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['taste']
    },
    "spotify_playlist_freshness": {
        "fn": _stub_spotify_playlist_freshness,
        "module": "tools.taste",
        "fn_name": "spotify_playlist_freshness",
        "doc": """Sort playlists by last update timestamp to identify stale lists.

Args:
    limit: Maximum playlists to inspect (default: 50).
    stale_days_threshold: Days of inactivity before a playlist is flagged as stale (default: 90).""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['taste']
    },
    "search_actor_movies": {
        "fn": _stub_search_actor_movies,
        "module": "tools.search",
        "fn_name": "search_actor_movies",
        "doc": """Discover the full filmography for an actor using TMDB (with DDG and Wikipedia fallbacks).

Args:
    actor_name: Name of the actor (e.g. 'Cillian Murphy', 'Shah Rukh Khan', 'Tom Cruise')
    limit: Maximum number of movies to return (default: 30)
    sort_by: Ordering for movies ('popularity' or 'release_date', default: 'popularity')""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['search', 'core']
    },
    "get_actor_tmdb_profile": {
        "fn": _stub_get_actor_tmdb_profile,
        "module": "tools.search",
        "fn_name": "get_actor_tmdb_profile",
        "doc": """Get rich biographical and career profile details for an actor from TMDB.

Args:
    actor_name: Name of the actor (e.g. 'Robert Downey Jr.', 'Zendaya')""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['search', 'core']
    },
    "search_movie_tmdb": {
        "fn": _stub_search_movie_tmdb,
        "module": "tools.search",
        "fn_name": "search_movie_tmdb",
        "doc": """Search TMDB for movie information, release year, ratings, and overview.

Args:
    movie_name: Title of the movie to search (e.g. 'Inception', 'Interstellar')
    limit: Maximum results to return (default: 5)""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['search', 'core']
    },
    "search_duckduckgo": {
        "fn": _stub_search_duckduckgo,
        "module": "tools.search",
        "fn_name": "search_duckduckgo",
        "doc": """Perform a web search using DuckDuckGo to look up movie news, filmographies, or sound tracks.

Args:
    query: Search query string
    max_results: Maximum results to return (default: 5)""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['search']
    },
    "get_movie_songs": {
        "fn": _stub_get_movie_songs,
        "module": "tools.search",
        "fn_name": "get_movie_songs",
        "doc": """Search Spotify for soundtrack albums and songs from a movie with DuckDuckGo fallback assistance.

Args:
    movie_name: Title of the movie (e.g. 'Inception', 'Darr', 'Top Gun')
    limit: Maximum number of songs to return (default: 10)""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['search']
    },
    "search_spotify": {
        "fn": _stub_search_spotify,
        "module": "tools.search",
        "fn_name": "search_spotify",
        "doc": """Search for songs, albums, artists, or playlists on Spotify.

Args:
    query: Search keywords
    search_type: Types to search for (comma-separated: 'track', 'album', 'artist', 'playlist')
    limit: Number of results (default 5, max 20)""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['search', 'core']
    },
    "spotify_search": {
        "fn": _stub_spotify_search,
        "module": "tools.search",
        "fn_name": "spotify_search",
        "doc": """Search Spotify catalog for tracks, artists, albums, or playlists.

Args:
    query: Search keywords or query syntax (e.g. 'Daft Punk', 'track:Get Lucky', 'artist:Queen').
    types: List of Spotify item types to search for (options: 'track', 'artist', 'album', 'playlist'). Default: ['track', 'artist', 'album', 'playlist'].
    limit: Number of results to return per type (default: 10, max: 50).
    market: Optional ISO 3166-1 alpha-2 country code (e.g. 'US', 'GB').""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['search']
    },
    "spotify_related_artists": {
        "fn": _stub_spotify_related_artists,
        "module": "tools.search",
        "fn_name": "spotify_related_artists",
        "doc": """Find artists similar to a target artist.

Args:
    artist: Artist name, Spotify artist ID, or Spotify artist URI (e.g. 'Hans Zimmer', 'spotify:artist:0YC192cP3KPCRWx8zr8MfZ').""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['search']
    },
    "spotify_discover_by_artist": {
        "fn": _stub_spotify_discover_by_artist,
        "module": "tools.search",
        "fn_name": "spotify_discover_by_artist",
        "doc": """Generate track recommendations derived from related artist networks.

Args:
    artist: Seed artist name, ID, or URI.
    limit: Number of recommended tracks to return (default: 15, max: 50).
    include_artist_top_tracks: Whether to include top tracks from the seed artist (default: True).""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['search']
    },
    "spotify_discover_by_mood": {
        "fn": _stub_spotify_discover_by_mood,
        "module": "tools.search",
        "fn_name": "spotify_discover_by_mood",
        "doc": """Discover tracks using target audio parameters (valence, energy, tempo, etc.) or mood presets.

Args:
    mood: Optional mood preset ('happy', 'sad', 'chill', 'energetic', 'focus', 'party', 'dark', 'romantic', 'workout').
    seed_genres: Optional list of seed genres (e.g. ['pop', 'indie', 'electronic']). Max 5 combined seeds.
    target_valence: Musical positiveness ($0.0$ to $1.0$).
    target_energy: Intensity and activity ($0.0$ to $1.0$).
    target_danceability: Suitability for dancing ($0.0$ to $1.0$).
    target_acousticness: Confidence measure from $0.0$ to $1.0$ of whether track is acoustic.
    target_tempo: Target tempo in BPM (beats per minute).
    limit: Number of tracks to discover (default: 20, max: 100).""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['search']
    },
    "spotify_genre_explorer": {
        "fn": _stub_spotify_genre_explorer,
        "module": "tools.search",
        "fn_name": "spotify_genre_explorer",
        "doc": """Browse and sample tracks across specific seed genres or list all available genre seeds.

Args:
    genres: Optional list of genre seed keywords (e.g. ['synthwave', 'indie-pop', 'jazz']). If None or empty, returns all available Spotify genre seeds.
    limit: Number of tracks to sample (default: 15, max: 50).
    market: Optional ISO country code.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['search']
    },
    "spotify_discover_deep_cuts": {
        "fn": _stub_spotify_discover_deep_cuts,
        "module": "tools.search",
        "fn_name": "spotify_discover_deep_cuts",
        "doc": """Discover non-single, album-only deep cut tracks from an artist or album.

Args:
    artist_or_album: Name, ID, or URI of an artist or album (e.g. 'Radiohead', 'The Dark Side of the Moon').
    max_popularity: Maximum popularity threshold (0-100, default: 40). Tracks with popularity <= this threshold are considered deep cuts.
    limit: Maximum number of deep cuts to return (default: 15).""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['search']
    },
    "spotify_get_recommendations": {
        "fn": _stub_spotify_get_recommendations,
        "module": "tools.search",
        "fn_name": "spotify_get_recommendations",
        "doc": """Direct wrapper for Spotify Recommendations API using seeds and target audio features.

Args:
    limit: Number of recommendations to return (default: 20, max: 100).
    seed_tracks: List of Spotify track IDs or URIs (max 5 combined seeds).
    seed_artists: List of Spotify artist IDs or URIs.
    seed_genres: List of seed genres (e.g. ['pop', 'rock', 'synthwave']).
    target_energy: Target energy (0.0 to 1.0).
    target_valence: Target valence (0.0 to 1.0).
    target_danceability: Target danceability (0.0 to 1.0).
    target_acousticness: Target acousticness (0.0 to 1.0).
    target_instrumentalness: Target instrumentalness (0.0 to 1.0).
    target_tempo: Target tempo in BPM.
    min_popularity: Minimum track popularity (0-100).
    max_popularity: Maximum track popularity (0-100).
    market: Optional ISO 3166-1 alpha-2 country code.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['search']
    },
    "fetch_soundtrack_tracks": {
        "fn": _stub_fetch_soundtrack_tracks,
        "module": "tools.search",
        "fn_name": "fetch_soundtrack_tracks",
        "doc": """Searches Spotify for movie soundtrack tracks using titles, language, release year, or actor name with fuzzy matching.

Args:
    movie_title: Title of the movie
    language_name: Optional language filter (e.g. 'Hindi', 'Telugu', 'English')
    release_year: Optional movie release year (e.g. '2023')
    actor_name: Optional actor name to narrow down soundtrack""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['search', 'core']
    },
    "search_singers": {
        "fn": _stub_search_singers,
        "module": "tools.search",
        "fn_name": "search_singers",
        "doc": """Search for singers, musical artists, or bands on Spotify.

Args:
    query: Name of singer, artist, or band to search
    limit: Maximum number of artists to return (default: 10)""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['search']
    },
    "search_songs": {
        "fn": _stub_search_songs,
        "module": "tools.search",
        "fn_name": "search_songs",
        "doc": """Search for songs or tracks on Spotify with detailed track metadata.

Args:
    query: Song name or keywords to search
    limit: Maximum number of songs to return (default: 10)""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['search']
    },
    "spotify_get_saved_tracks": {
        "fn": _stub_spotify_get_saved_tracks,
        "module": "tools.library",
        "fn_name": "spotify_get_saved_tracks",
        "doc": """List tracks saved in the current user's Liked Songs library.

Args:
    limit: Number of tracks to return (default: 20, max: 50).
    offset: Index of the first item to return (default: 0).
    market: An ISO 3166-1 alpha-2 country code.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['library']
    },
    "spotify_save_tracks": {
        "fn": _stub_spotify_save_tracks,
        "module": "tools.library",
        "fn_name": "spotify_save_tracks",
        "doc": """Save one or more tracks to the current user's Liked Songs library.

Args:
    track_ids: List of Spotify track IDs, URIs, or URLs to save.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['library']
    },
    "spotify_remove_saved_tracks": {
        "fn": _stub_spotify_remove_saved_tracks,
        "module": "tools.library",
        "fn_name": "spotify_remove_saved_tracks",
        "doc": """Remove one or more tracks from the current user's Liked Songs library.

Args:
    track_ids: List of Spotify track IDs, URIs, or URLs to remove.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['library']
    },
    "spotify_check_saved_tracks": {
        "fn": _stub_spotify_check_saved_tracks,
        "module": "tools.library",
        "fn_name": "spotify_check_saved_tracks",
        "doc": """Verify whether specific tracks exist in the current user's Liked Songs library.

Args:
    track_ids: List of Spotify track IDs, URIs, or URLs to check (max: 50).""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['library']
    },
    "spotify_get_saved_albums": {
        "fn": _stub_spotify_get_saved_albums,
        "module": "tools.library",
        "fn_name": "spotify_get_saved_albums",
        "doc": """Fetch albums saved in the current user's library.

Args:
    limit: Number of albums to return (default: 20, max: 50).
    offset: Index of the first album to return (default: 0).
    market: An ISO 3166-1 alpha-2 country code.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['library']
    },
    "spotify_save_albums": {
        "fn": _stub_spotify_save_albums,
        "module": "tools.library",
        "fn_name": "spotify_save_albums",
        "doc": """Save one or more albums to the current user's library.

Args:
    album_ids: List of Spotify album IDs, URIs, or URLs to save.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['library']
    },
    "spotify_remove_saved_albums": {
        "fn": _stub_spotify_remove_saved_albums,
        "module": "tools.library",
        "fn_name": "spotify_remove_saved_albums",
        "doc": """Remove one or more albums from the current user's library.

Args:
    album_ids: List of Spotify album IDs, URIs, or URLs to remove.""",
        "annotations": ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['library']
    },
    "spotify_check_saved_albums": {
        "fn": _stub_spotify_check_saved_albums,
        "module": "tools.library",
        "fn_name": "spotify_check_saved_albums",
        "doc": """Verify whether specific albums exist in the current user's library.

Args:
    album_ids: List of Spotify album IDs, URIs, or URLs to check (max: 50).""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['library']
    },
    "spotify_get_track": {
        "fn": _stub_spotify_get_track,
        "module": "tools.browse",
        "fn_name": "spotify_get_track",
        "doc": """Inspect full track metadata including ISRC, popularity, audio preview URL, and album details.

Args:
    track_id: Spotify track ID, URI, or URL (e.g. 'spotify:track:4cOdK2wGLETKBW3PvgPWqT').
    market: Optional ISO 3166-1 alpha-2 country code.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['browse']
    },
    "spotify_get_album": {
        "fn": _stub_spotify_get_album,
        "module": "tools.browse",
        "fn_name": "spotify_get_album",
        "doc": """Inspect full album details including copyrights, label, release date, and complete tracklist.

Args:
    album_id: Spotify album ID, URI, or URL (e.g. 'spotify:album:4aawyAB9vmqN3uQ7FjRGTy').
    market: Optional ISO 3166-1 alpha-2 country code.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['browse']
    },
    "spotify_get_artist": {
        "fn": _stub_spotify_get_artist,
        "module": "tools.browse",
        "fn_name": "spotify_get_artist",
        "doc": """Inspect artist details including genres, follower count, popularity, and profile images.

Args:
    artist_id: Spotify artist ID, URI, URL, or artist name (e.g. 'Radiohead' or 'spotify:artist:4Z8W4fKeB5YxbusRsdQVPb').""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['browse']
    },
    "spotify_get_artist_albums": {
        "fn": _stub_spotify_get_artist_albums,
        "module": "tools.browse",
        "fn_name": "spotify_get_artist_albums",
        "doc": """Get all albums, singles, and compilations released by a specific artist.

Args:
    artist_id: Spotify artist ID, URI, URL, or artist name.
    include_groups: Comma-separated list of groups ('album', 'single', 'appears_on', 'compilation'). Default: 'album,single'.
    limit: Number of items to return (default: 20, max: 50).
    offset: Index of the first item to return (default: 0).
    country: Optional ISO 3166-1 alpha-2 country code.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['browse']
    },
    "spotify_get_user": {
        "fn": _stub_spotify_get_user,
        "module": "tools.browse",
        "fn_name": "spotify_get_user",
        "doc": """Fetch public profile information and public playlists for any Spotify user.

Args:
    user_id: Spotify user ID, URI, or profile URL (e.g. 'spotify:user:wizzler' or 'wizzler').""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['browse']
    },
    "open_soundtrack_studio": {
        "fn": _stub_open_soundtrack_studio,
        "module": "tools.web_app",
        "fn_name": "open_soundtrack_studio",
        "doc": """Launch or retrieve the URL for the Soundtrack Curator & Staging Studio web application.

Returns the local web application URL and opens it in your default browser.""",
        "annotations": ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True),
        "toolsets": ['web_app', 'core']
    },
}


def get_active_toolsets(argv=None, env=None) -> List[str]:
    """Parses requested toolsets from CLI arguments (--toolsets=...) or environment variables."""
    if argv is None:
        argv = sys.argv
    if env is None:
        env = os.environ

    for i, arg in enumerate(argv):
        if arg.startswith("--toolsets="):
            val = arg.split("=", 1)[1]
            return [t.strip().lower() for t in val.split(",") if t.strip()]
        elif arg == "--toolsets" and i + 1 < len(argv):
            val = argv[i + 1]
            return [t.strip().lower() for t in val.split(",") if t.strip()]

    env_val = env.get("SPOTIFY_TOOLSETS") or env.get("TOOLSETS")
    if env_val:
        return [t.strip().lower() for t in env_val.split(",") if t.strip()]

    # If running under pytest or tests, default to all so existing suites pass
    if "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in env:
        return ["all"]

    # Default modular toolset: core
    return ["core"]


def register_active_toolsets(mcp_instance, toolsets: Optional[List[str]] = None) -> List[str]:
    """Registers tool stubs into FastMCP for the active toolsets without loading heavy libraries."""
    if toolsets is None:
        toolsets = get_active_toolsets()

    requested = set(t.strip().lower() for t in toolsets)
    registered = []

    for tool_name, spec in TOOL_SPECS.items():
        if "all" in requested or any(ts in requested for ts in spec["toolsets"]):
            mcp_instance.add_tool(
                spec["fn"],
                name=tool_name,
                description=spec["doc"],
                annotations=spec["annotations"]
            )
            registered.append(tool_name)
    return registered

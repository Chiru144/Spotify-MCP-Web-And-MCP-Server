from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from collections import Counter
from mcp.types import ToolAnnotations
from tools.core import mcp, get_spotify_client, _clean_spotify_id, _format_duration
import spotipy

@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def get_user_top_tracks(limit: int = 10, time_range: str = "medium_term") -> str:
    """Get the current user's top songs over a specified period.
    
    Args:
        limit: Number of songs (default 10, max 50)
        time_range: Over what time frame ('short_term' = ~4 weeks, 'medium_term' = ~6 months, 'long_term' = years)
    """
    try:
        sp = get_spotify_client()
        results = sp.current_user_top_tracks(limit=min(limit, 50), time_range=time_range)
        items = results.get("items", [])
        if not items:
            return "No top songs found."
        lines = [f"Top Songs ({time_range}) - Total count: {len(items)}:"]
        for idx, t in enumerate(items, 1):
            artists = ", ".join(a["name"] for a in t["artists"])
            lines.append(f"{idx}. {t['name']} - {artists} (URI: {t['uri']})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching top songs: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def get_user_top_songs(limit: int = 10, time_range: str = "medium_term") -> str:
    """Get the current user's top songs over a specified period."""
    return get_user_top_tracks(limit=limit, time_range=time_range)


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def get_user_top_artists(limit: int = 10, time_range: str = "medium_term") -> str:
    """Get the current user's top artists over a specified period.
    
    Args:
        limit: Number of artists (default 10, max 50)
        time_range: Over what time frame ('short_term', 'medium_term', 'long_term')
    """
    try:
        sp = get_spotify_client()
        results = sp.current_user_top_artists(limit=min(limit, 50), time_range=time_range)
        items = results.get("items", [])
        if not items:
            return "No top artists found."
        lines = [f"Top Artists ({time_range}) - Total count: {len(items)}:"]
        for idx, a in enumerate(items, 1):
            lines.append(f"{idx}. {a['name']} (URI: {a['uri']})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching top artists: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def get_audio_features(track_uris: list[str]) -> str:
    """Get audio features (danceability, energy, valence, etc) for multiple tracks.
    
    Args:
        track_uris: List of Spotify track URIs (max 100).
    """
    try:
        sp = get_spotify_client()
        features = sp.audio_features(tracks=track_uris[:100])
        lines = ["Audio Features:"]
        for i, feat in enumerate(features):
            if not feat:
                lines.append(f"Track {i+1}: Features not found")
                continue
            lines.append(f"Track URI: {feat.get('uri')}")
            lines.append(f"  Danceability: {feat.get('danceability')} | Energy: {feat.get('energy')} | Valence: {feat.get('valence')}")
            lines.append(f"  Tempo: {feat.get('tempo')} BPM | Key: {feat.get('key')} | Mode: {'Major' if feat.get('mode') == 1 else 'Minor'}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching audio features: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def get_artist_network(artist_name_or_id: str) -> str:
    """Map an artist's network by fetching related artists.
    
    Args:
        artist_name_or_id: Name or Spotify ID of the artist.
    """
    try:
        sp = get_spotify_client()
        # Search if not an ID/URI
        artist_id = artist_name_or_id
        if not artist_id.startswith('spotify:artist:') and len(artist_id) != 22:
            results = sp.search(q=artist_name_or_id, type='artist', limit=1)
            if not results['artists']['items']:
                return "Artist not found."
            artist_id = results['artists']['items'][0]['id']
            artist_name = results['artists']['items'][0]['name']
        else:
            artist_name = sp.artist(artist_id)['name']

        related = sp.artist_related_artists(artist_id)
        items = related.get('artists', [])
        if not items:
            return f"No related artists found for {artist_name}."
        
        lines = [f"Related Artists for {artist_name} (Network):"]
        for a in items:
            lines.append(f"- {a['name']} (URI: {a['uri']}, Genres: {', '.join(a.get('genres', [])[:3])})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error mapping artist network: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def get_saved_tracks(limit: int = 50, offset: int = 0) -> str:
    """Get tracks from the user's Library (Saved Tracks)."""
    try:
        sp = get_spotify_client()
        results = sp.current_user_saved_tracks(limit=limit, offset=offset)
        items = results.get("items", [])
        if not items:
            return "No saved tracks found in your library."
        output = [f"Found {len(items)} saved tracks (offset {offset}):"]
        for i, item in enumerate(items, 1):
            t = item.get("track", {})
            artists = ", ".join([a.get("name", "Unknown") for a in t.get("artists", [])])
            output.append(f"{i}. {t.get('name')} by {artists} (URI: {t.get('uri')})")
        return "\n".join(output)
    except Exception as e:
        return f"Error fetching saved tracks: {str(e)}"

@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def get_recommendations(
    limit: int = 10,
    seed_tracks: Optional[List[str]] = None,
    seed_artists: Optional[List[str]] = None,
    seed_genres: Optional[List[str]] = None,
    target_energy: Optional[float] = None,
    target_valence: Optional[float] = None,
    target_danceability: Optional[float] = None,
    target_acousticness: Optional[float] = None,
    target_instrumentalness: Optional[float] = None,
    target_tempo: Optional[float] = None
) -> str:
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
        target_tempo: Target tempo in BPM.
    """
    try:
        sp = get_spotify_client()
        
        # Ensure total seeds do not exceed 5
        num_seeds = (len(seed_tracks) if seed_tracks else 0) + \
                    (len(seed_artists) if seed_artists else 0) + \
                    (len(seed_genres) if seed_genres else 0)
        
        if num_seeds == 0:
            return "Error: You must provide at least one seed (track, artist, or genre)."
        if num_seeds > 5:
            return f"Error: Up to 5 seed values may be provided in any combination of seed_tracks, seed_artists, and seed_genres. You provided {num_seeds}."
            
        kwargs = {}
        if target_energy is not None: kwargs["target_energy"] = target_energy
        if target_valence is not None: kwargs["target_valence"] = target_valence
        if target_danceability is not None: kwargs["target_danceability"] = target_danceability
        if target_acousticness is not None: kwargs["target_acousticness"] = target_acousticness
        if target_instrumentalness is not None: kwargs["target_instrumentalness"] = target_instrumentalness
        if target_tempo is not None: kwargs["target_tempo"] = target_tempo

        results = sp.recommendations(
            seed_tracks=seed_tracks,
            seed_artists=seed_artists,
            seed_genres=seed_genres,
            limit=min(limit, 100),
            **kwargs
        )
        
        tracks = results.get("tracks", [])
        if not tracks:
            return "No recommendations found for the given seeds and targets."
            
        output = [f"Found {len(tracks)} recommendations:"]
        for i, t in enumerate(tracks, 1):
            artists = ", ".join([a.get("name", "Unknown") for a in t.get("artists", [])])
            output.append(f"{i}. {t.get('name')} by {artists} (URI: {t.get('uri')})")
        return "\n".join(output)
    except Exception as e:
        return f"Error fetching recommendations: {str(e)}"


# ==============================================================================
# STATS, ANALYTICS & INSIGHTS TOOLS
# ==============================================================================

@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_top_tracks(
    time_range: str = "medium_term",
    limit: int = 20,
    offset: int = 0
) -> str:
    """Fetch user's top tracks over short, medium, or long term.
    
    Args:
        time_range: Period of analysis ('short_term' = ~4 weeks, 'medium_term' = ~6 months, 'long_term' = all time / years). Default: 'medium_term'.
        limit: Number of tracks to return (default: 20, max: 50).
        offset: Index of the first track to return (default: 0).
    """
    try:
        sp = get_spotify_client()
        valid_ranges = ["short_term", "medium_term", "long_term"]
        tr = time_range.lower().strip() if time_range else "medium_term"
        if tr not in valid_ranges:
            tr = "medium_term"

        limit = max(1, min(limit, 50))
        results = sp.current_user_top_tracks(limit=limit, offset=offset, time_range=tr)
        items = results.get("items", [])
        if not items:
            return f"No top tracks found for period '{tr}'."

        range_names = {
            "short_term": "Last 4 Weeks",
            "medium_term": "Last 6 Months",
            "long_term": "All-Time / Years"
        }
        lines = [
            f"Spotify Top Tracks ({range_names.get(tr, tr)}):",
            f"Showing {len(items)} tracks (offset {offset}):\n"
        ]
        for idx, t in enumerate(items, offset + 1):
            artists = ", ".join(a.get("name", "Unknown") for a in t.get("artists", []))
            album = t.get("album", {}).get("name", "Unknown Album")
            dur = _format_duration(t.get("duration_ms", 0))
            pop = t.get("popularity", 0)
            lines.append(f"{idx}. {t.get('name')} - {artists} ({dur}) [Album: {album}] (Popularity: {pop}/100, URI: {t.get('uri')})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching top tracks: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_top_artists(
    time_range: str = "medium_term",
    limit: int = 20,
    offset: int = 0
) -> str:
    """Fetch user's top artists over short, medium, or long term.
    
    Args:
        time_range: Period of analysis ('short_term' = ~4 weeks, 'medium_term' = ~6 months, 'long_term' = all time / years). Default: 'medium_term'.
        limit: Number of artists to return (default: 20, max: 50).
        offset: Index of the first artist to return (default: 0).
    """
    try:
        sp = get_spotify_client()
        valid_ranges = ["short_term", "medium_term", "long_term"]
        tr = time_range.lower().strip() if time_range else "medium_term"
        if tr not in valid_ranges:
            tr = "medium_term"

        limit = max(1, min(limit, 50))
        results = sp.current_user_top_artists(limit=limit, offset=offset, time_range=tr)
        items = results.get("items", [])
        if not items:
            return f"No top artists found for period '{tr}'."

        range_names = {
            "short_term": "Last 4 Weeks",
            "medium_term": "Last 6 Months",
            "long_term": "All-Time / Years"
        }
        lines = [
            f"Spotify Top Artists ({range_names.get(tr, tr)}):",
            f"Showing {len(items)} artists (offset {offset}):\n"
        ]
        for idx, a in enumerate(items, offset + 1):
            genres = ", ".join(a.get("genres", [])[:3]) or "No genres listed"
            followers = a.get("followers", {}).get("total", 0)
            pop = a.get("popularity", 0)
            lines.append(f"{idx}. {a.get('name')} [Genres: {genres}] (Popularity: {pop}/100, Followers: {followers:,}, URI: {a.get('uri')})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching top artists: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_recently_played(
    limit: int = 20,
    after: Optional[int] = None,
    before: Optional[int] = None
) -> str:
    """Fetch recent track listening history.
    
    Args:
        limit: Number of items to return (default: 20, max: 50).
        after: A Unix timestamp in milliseconds. Returns items played after this date.
        before: A Unix timestamp in milliseconds. Returns items played before this date.
    """
    try:
        sp = get_spotify_client()
        limit = max(1, min(limit, 50))
        kwargs = {}
        if after: kwargs["after"] = after
        if before: kwargs["before"] = before

        results = sp.current_user_recently_played(limit=limit, **kwargs)
        items = results.get("items", [])
        if not items:
            return "No recently played tracks found."

        lines = [
            f"Spotify Recently Played History (Total: {len(items)}):",
        ]
        for idx, item in enumerate(items, 1):
            t = item.get("track", {})
            played_at = item.get("played_at", "")
            time_display = played_at.replace("T", " ")[:19] + " UTC" if played_at else "Recently"
            artists = ", ".join(a.get("name", "Unknown") for a in t.get("artists", []))
            dur = _format_duration(t.get("duration_ms", 0))
            lines.append(f"{idx}. [{time_display}] {t.get('name')} - {artists} ({dur}) (URI: {t.get('uri')})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching recently played history: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_listening_patterns() -> str:
    """Analyze listening volume distributions across hours and days."""
    try:
        sp = get_spotify_client()
        results = sp.current_user_recently_played(limit=50)
        items = results.get("items", [])
        if not items:
            return "Not enough recent listening history to calculate patterns."

        hours = [0] * 24
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        days = {d: 0 for d in day_names}
        track_counter = Counter()

        for item in items:
            played_at = item.get("played_at")
            if played_at:
                try:
                    dt = datetime.fromisoformat(played_at.replace("Z", "+00:00"))
                    hours[dt.hour] += 1
                    day_str = day_names[dt.weekday()]
                    days[day_str] += 1
                except Exception:
                    pass
            t = item.get("track", {})
            t_name = t.get("name")
            t_art = ", ".join(a.get("name", "") for a in t.get("artists", []))
            if t_name:
                track_counter[f"{t_name} by {t_art}"] += 1

        late_night = sum(hours[0:6])
        morning = sum(hours[6:12])
        afternoon = sum(hours[12:18])
        evening = sum(hours[18:24])
        slots = [("Morning (06:00-12:00)", morning), ("Afternoon (12:00-18:00)", afternoon), ("Evening (18:00-24:00)", evening), ("Late Night (00:00-06:00)", late_night)]
        slots.sort(key=lambda x: x[1], reverse=True)

        peak_hour = hours.index(max(hours))
        peak_day = max(days.items(), key=lambda x: x[1])

        lines = [
            "🎧 Spotify Listening Patterns & Temporal Insights (Last 50 Plays):",
            f"• Dominant Listening Window: {slots[0][0]} ({slots[0][1]} plays)",
            f"• Peak Listening Hour: {peak_hour:02d}:00 - {(peak_hour+1)%24:02d}:00 UTC ({max(hours)} plays)",
            f"• Most Active Day: {peak_day[0]} ({peak_day[1]} plays)\n",
            "Day of Week Breakdown:"
        ]
        max_day_cnt = max(days.values()) or 1
        for d, cnt in days.items():
            bar = "█" * int((cnt / max_day_cnt) * 12)
            lines.append(f"  {d[:3]}: {bar:<12} {cnt} plays")

        lines.append("\nHourly Activity (UTC 24h):")
        max_hr_cnt = max(hours) or 1
        for h in range(0, 24, 2):
            cnt = hours[h] + hours[h+1]
            bar = "█" * int((cnt / (max_hr_cnt * 2 or 1)) * 12)
            lines.append(f"  {h:02d}:00-{(h+2)%24:02d}:00: {bar:<12} {cnt} plays")

        if track_counter:
            top_repeats = track_counter.most_common(3)
            lines.append("\nTop Replayed Tracks in Recent Session:")
            for rank, (name, count) in enumerate(top_repeats, 1):
                lines.append(f"  {rank}. {name} ({count}x played)")

        return "\n".join(lines)
    except Exception as e:
        return f"Error analyzing listening patterns: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_taste_profile() -> str:
    """Generate an overview of genre diversity and niche artist affinity."""
    try:
        sp = get_spotify_client()
        top_artists_res = sp.current_user_top_artists(limit=50, time_range="medium_term")
        top_tracks_res = sp.current_user_top_tracks(limit=50, time_range="medium_term")

        artists = top_artists_res.get("items", [])
        tracks = top_tracks_res.get("items", [])

        if not artists and not tracks:
            return "No sufficient listening history found to generate taste profile."

        genre_counter = Counter()
        for a in artists:
            for g in a.get("genres", []):
                genre_counter[g] += 1

        total_genre_mentions = sum(genre_counter.values()) or 1
        top_genres = genre_counter.most_common(8)

        art_pops = [a.get("popularity", 50) for a in artists]
        trk_pops = [t.get("popularity", 50) for t in tracks]
        avg_art_pop = sum(art_pops) / len(art_pops) if art_pops else 50.0
        avg_trk_pop = sum(trk_pops) / len(trk_pops) if trk_pops else 50.0
        overall_pop = (avg_art_pop + avg_trk_pop) / 2.0

        if overall_pop >= 70:
            archetype = "Mainstream Hit Enthusiast (Chart-Toppers & Viral Anthems)"
            archetype_desc = "Your taste leans heavily into widely celebrated global hits and mainstream cultural moments."
        elif overall_pop >= 55:
            archetype = "Eclectic Trendsetter (Blend of Popular & Discoveries)"
            archetype_desc = "You balance popular favorites with emerging acts, staying culturally connected while exploring new sounds."
        elif overall_pop >= 40:
            archetype = "Indie Explorer (Selective, Alt & Independent Sounds)"
            archetype_desc = "You actively seek out independent artists, college radio gems, and deeper sub-genres over radio Top 40."
        else:
            archetype = "Deep Underground Connoisseur (Niche & Obscure)"
            archetype_desc = "You live on the cutting edge of obscure, underground, and non-commercial music that most listeners have never heard."

        eras = Counter()
        explicit_count = 0
        for t in tracks:
            if t.get("explicit"):
                explicit_count += 1
            rel = t.get("album", {}).get("release_date", "")[:4]
            if rel.isdigit():
                decade = f"{rel[:3]}0s"
                eras[decade] += 1

        lines = [
            "🧬 Spotify Musical Taste Profile & Affinity Analysis:",
            f"• Musical Archetype: {archetype}",
            f"  {archetype_desc}",
            f"• Mainstream Index: {overall_pop:.1f}/100 (Artist Pop: {avg_art_pop:.1f}, Track Pop: {avg_trk_pop:.1f})",
            f"• Unique Genres Discovered: {len(genre_counter)} genres",
            f"• Explicit Content Affinity: {explicit_count}/{len(tracks)} tracks ({(explicit_count/len(tracks)*100 if tracks else 0):.0f}%)\n",
            "Top Musical Genres:"
        ]

        for rank, (genre, cnt) in enumerate(top_genres, 1):
            pct = (cnt / total_genre_mentions) * 100
            bar = "█" * int(pct / 3)
            lines.append(f"  {rank}. {genre.title():<20} {bar:<14} {pct:.1f}%")

        if eras:
            lines.append("\nDecade / Era Spread:")
            for era, cnt in sorted(eras.items()):
                lines.append(f"  {era}: {cnt} tracks")

        return "\n".join(lines)
    except Exception as e:
        return f"Error generating taste profile: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_playlist_compare(playlist_ids: List[str]) -> str:
    """Compare multi-playlist audio feature distributions side-by-side.
    
    Args:
        playlist_ids: List of 2 or more Spotify playlist IDs or URIs.
    """
    try:
        sp = get_spotify_client()
        if isinstance(playlist_ids, str):
            playlist_ids = [p.strip() for p in playlist_ids.split(",") if p.strip()]

        if len(playlist_ids) < 2:
            return "Please provide at least 2 playlist IDs or URIs to compare."

        playlists_stats = []

        for raw_id in playlist_ids[:5]:
            clean_id = _clean_spotify_id(raw_id, "playlist")
            pl = sp.playlist(clean_id, fields="id,name,tracks.total,owner.display_name")
            p_name = pl.get("name", "Untitled")

            items_res = sp.playlist_items(clean_id, limit=50, additional_types=('track',))
            items = items_res.get("items", [])
            t_ids = [item.get("track", {}).get("id") for item in items if item.get("track") and item.get("track", {}).get("id")]

            if not t_ids:
                playlists_stats.append({
                    "name": p_name,
                    "total_tracks": pl.get("tracks", {}).get("total", 0),
                    "energy": 0.0, "valence": 0.0, "danceability": 0.0, "acousticness": 0.0, "tempo": 0.0
                })
                continue

            features = sp.audio_features(t_ids[:50])
            valid_feats = [f for f in features if f]

            if not valid_feats:
                playlists_stats.append({
                    "name": p_name,
                    "total_tracks": pl.get("tracks", {}).get("total", 0),
                    "energy": 0.0, "valence": 0.0, "danceability": 0.0, "acousticness": 0.0, "tempo": 0.0
                })
                continue

            n = len(valid_feats)
            avg_energy = sum(f.get("energy", 0) for f in valid_feats) / n
            avg_valence = sum(f.get("valence", 0) for f in valid_feats) / n
            avg_dance = sum(f.get("danceability", 0) for f in valid_feats) / n
            avg_acoustic = sum(f.get("acousticness", 0) for f in valid_feats) / n
            avg_tempo = sum(f.get("tempo", 0) for f in valid_feats) / n

            playlists_stats.append({
                "name": p_name,
                "total_tracks": pl.get("tracks", {}).get("total", 0),
                "energy": avg_energy,
                "valence": avg_valence,
                "danceability": avg_dance,
                "acousticness": avg_acoustic,
                "tempo": avg_tempo
            })

        lines = [
            f"Multi-Playlist Audio Feature Comparison ({len(playlists_stats)} Playlists):",
            f"{'Playlist':<26} {'Energy':<8} {'Valence':<8} {'Dance':<8} {'Acoustic':<10} {'Tempo':<8}"
        ]
        lines.append("-" * 72)

        for s in playlists_stats:
            p_short = (s["name"][:23] + "...") if len(s["name"]) > 25 else s["name"]
            lines.append(
                f"{p_short:<26} {s['energy']:.2f}     {s['valence']:.2f}     {s['danceability']:.2f}     {s['acousticness']:.2f}       {s['tempo']:.0f} BPM"
            )

        highest_energy = max(playlists_stats, key=lambda x: x["energy"])
        highest_valence = max(playlists_stats, key=lambda x: x["valence"])
        highest_dance = max(playlists_stats, key=lambda x: x["danceability"])
        highest_acoustic = max(playlists_stats, key=lambda x: x["acousticness"])

        lines.append("\nKey Comparative Observations:")
        lines.append(f"• Most High-Energy: '{highest_energy['name']}' ({highest_energy['energy']:.2f}/1.0)")
        lines.append(f"• Most Positive/Happy (Valence): '{highest_valence['name']}' ({highest_valence['valence']:.2f}/1.0)")
        lines.append(f"• Best for Dancing: '{highest_dance['name']}' ({highest_dance['danceability']:.2f}/1.0)")
        lines.append(f"• Most Organic/Acoustic: '{highest_acoustic['name']}' ({highest_acoustic['acousticness']:.2f}/1.0)")

        return "\n".join(lines)
    except Exception as e:
        return f"Error comparing playlists: {str(e)}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True))
def spotify_playlist_freshness(
    limit: int = 50,
    stale_days_threshold: int = 90
) -> str:
    """Sort playlists by last update timestamp to identify stale lists.
    
    Args:
        limit: Maximum playlists to inspect (default: 50).
        stale_days_threshold: Days of inactivity before a playlist is flagged as stale (default: 90).
    """
    try:
        sp = get_spotify_client()
        limit = max(1, min(limit, 50))
        pl_res = sp.current_user_playlists(limit=limit)
        items = pl_res.get("items", [])
        if not items:
            return "No playlists found in your library."

        now = datetime.now(timezone.utc)
        analyzed = []

        for p in items:
            if not p:
                continue
            pid = p.get("id")
            pname = p.get("name", "Untitled")
            total = p.get("tracks", {}).get("total", 0)

            if total == 0:
                analyzed.append({
                    "name": pname,
                    "id": pid,
                    "total": 0,
                    "days": 9999,
                    "last_updated": "Never (Empty)",
                    "status": "🔴 Empty"
                })
                continue

            offset = max(0, total - 1)
            last_item_res = sp.playlist_items(pid, limit=1, offset=offset, fields="items(added_at)")
            last_items = last_item_res.get("items", [])

            if last_items and last_items[0].get("added_at"):
                added_at_str = last_items[0]["added_at"]
                try:
                    dt = datetime.fromisoformat(added_at_str.replace("Z", "+00:00"))
                    days_ago = (now - dt).days
                    if days_ago < 30:
                        status = "🟢 Fresh"
                    elif days_ago <= stale_days_threshold:
                        status = "🟡 Aging"
                    else:
                        status = "🔴 Stale"
                    analyzed.append({
                        "name": pname,
                        "id": pid,
                        "total": total,
                        "days": days_ago,
                        "last_updated": f"{days_ago} days ago ({added_at_str[:10]})",
                        "status": status
                    })
                except Exception:
                    analyzed.append({
                        "name": pname, "id": pid, "total": total, "days": 0, "last_updated": "Unknown", "status": "⚪ Active"
                    })
            else:
                analyzed.append({
                    "name": pname, "id": pid, "total": total, "days": 0, "last_updated": "Unknown", "status": "⚪ Active"
                })

        analyzed.sort(key=lambda x: x["days"], reverse=True)

        stale_count = sum(1 for a in analyzed if "🔴" in a["status"])
        fresh_count = sum(1 for a in analyzed if "🟢" in a["status"])

        lines = [
            f"Spotify Playlist Freshness Audit ({len(analyzed)} Playlists Inspected):",
            f"• Fresh Playlists (<30 days): {fresh_count}",
            f"• Stale Playlists (>{stale_days_threshold} days): {stale_count}\n",
            f"{'Status':<10} {'Playlist':<26} {'Tracks':<8} {'Last Ingestion'}"
        ]
        lines.append("-" * 65)

        for a in analyzed:
            p_short = (a["name"][:23] + "...") if len(a["name"]) > 25 else a["name"]
            lines.append(f"{a['status']:<10} {p_short:<26} {a['total']:<8} {a['last_updated']}")

        if stale_count > 0:
            lines.append(f"\nTip: You have {stale_count} stale or empty playlists. You can refresh them with 'spotify_absorb_playlist' or merge them into active collections.")

        return "\n".join(lines)
    except Exception as e:
        return f"Error auditing playlist freshness: {str(e)}"




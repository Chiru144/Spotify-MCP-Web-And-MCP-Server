import pytest
from unittest.mock import patch, MagicMock

from tools import playback

@pytest.fixture(autouse=True)
def mock_clients():
    with patch("tools.core.get_spotify_client") as sp:
        yield sp

def test_playback_tools(mock_clients):
    sp_mock = mock_clients.return_value
    sp_mock.current_playback.return_value = {}
    sp_mock.devices.return_value = {"devices": []}
    sp_mock.queue.return_value = {}
    
    playback.get_current_playback()
    playback.play_track(uri="spotify:track:123")
    playback.play_song(uri="spotify:track:123")
    playback.pause_playback()
    playback.next_track()
    playback.next_song()
    playback.previous_track()
    playback.previous_song()
    playback.set_volume(50)
    playback.seek_playback(0)
    playback.set_repeat_mode("off")
    playback.set_shuffle(False)
    playback.get_available_devices()
    playback.transfer_playback("device_id")
    playback.get_queue()
    playback.add_to_queue("spotify:track:123")

    # Test the 15 standard spotify_* tools
    playback.spotify_status()
    playback.spotify_now_playing()
    playback.spotify_play(uri="spotify:track:123")
    playback.spotify_pause()
    playback.spotify_resume()
    playback.spotify_skip_next()
    playback.spotify_skip_previous()
    playback.spotify_add_to_queue("spotify:track:123")
    playback.spotify_get_queue()
    playback.spotify_get_devices()
    playback.spotify_transfer_playback("device_id")
    playback.spotify_set_volume(50)
    playback.spotify_seek(0)
    playback.spotify_set_repeat("off")
    playback.spotify_toggle_shuffle()

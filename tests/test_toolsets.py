import tools
import pytest
import asyncio
from mcp.server.mcpserver import MCPServer
from tools.registry import register_active_toolsets, get_active_toolsets, TOOL_SPECS, _dispatch

def test_toolset_core_registration():
    server = MCPServer("test_core")
    registered = register_active_toolsets(server, ["core"])
    assert len(registered) == 16
    assert "create_actor_playlist" in registered
    assert "add_movie_songs_to_playlist" in registered
    assert "search_spotify" in registered
    assert "get_audio_features" in registered
    assert "open_soundtrack_studio" in registered

def test_toolset_playback_registration():
    server = MCPServer("test_playback")
    registered = register_active_toolsets(server, ["playback"])
    assert len(registered) == 31
    assert "play_track" in registered
    assert "pause_playback" in registered
    assert "get_queue" in registered

def test_toolset_combined_registration():
    server = MCPServer("test_combined")
    registered = register_active_toolsets(server, ["core", "playback"])
    assert len(registered) == 47

def test_toolset_all_registration():
    server = MCPServer("test_all")
    registered = register_active_toolsets(server, ["all"])
    assert len(registered) == 115

def test_get_active_toolsets_cli_parsing():
    argv_core = ["server.py", "--toolsets=core"]
    assert get_active_toolsets(argv=argv_core) == ["core"]

    argv_combo = ["server.py", "--toolsets=core,playback"]
    assert get_active_toolsets(argv=argv_combo) == ["core", "playback"]

    argv_flag = ["server.py", "--toolsets", "playlists"]
    assert get_active_toolsets(argv=argv_flag) == ["playlists"]

def test_lazy_tool_execution():
    server = MCPServer("test_lazy")
    register_active_toolsets(server, ["core"])
    
    # Execute open_soundtrack_studio on-demand
    res = asyncio.run(server.call_tool("open_soundtrack_studio", {}))
    assert res is not None
    assert "Soundtrack Curator & Staging Studio" in res.content[0].text

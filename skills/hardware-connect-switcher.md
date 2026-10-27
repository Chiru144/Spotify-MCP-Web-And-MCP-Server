# Spotify Connect & Hardware Switcher Skill

## Overview
Control, discover, and route active playback across Spotify Connect hardware devices (smartphones, computers, smart speakers, TVs, and receivers).

## When to use this skill
- When the user asks "What devices are available?", "Play on my speaker", "Switch music to TV", or "Move audio to phone".
- For hardware-aware playback routing and volume management.

## Tools Included
- `get_available_devices()` / `spotify_get_devices()`: Inspects all active, idle, and restricted Spotify Connect devices on the local network.
- `transfer_playback(device_id, play)` / `spotify_transfer_playback(device_id, play)`: Seamlessly transfers the user's active session to a target device.
- `set_volume(volume_percent, device_id)` / `spotify_set_volume(volume)`: Controls output volume on target hardware.

## Workflow Instructions
1. Retrieve active devices using `spotify_get_devices()`.
2. Match the user's spoken target (e.g. "Echo", "Living Room Speaker", "MacBook", "iPhone") against the discovered device names.
3. Call `spotify_transfer_playback(device_id, play=True)` to shift playback instantly without interruption.
4. Report the active device name, volume level, and device type back to the user.

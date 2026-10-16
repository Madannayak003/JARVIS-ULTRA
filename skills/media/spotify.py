import os

from pynput.keyboard import Controller, Key

from services.spotify_api import (
    play_track,
    ensure_spotify,
)

from core.registry import register
from voice.manager import speak

keyboard = Controller()


def spotify_open(data):

    speak("Opening Spotify")

    ensure_spotify()

    return True


def spotify_close(data):

    speak("Closing Spotify")

    os.system("taskkill /IM Spotify.exe /F >nul 2>&1")

    return True


def spotify_play(data):
    try:
        ensure_spotify()
        keyboard.press(Key.media_play_pause)
        keyboard.release(Key.media_play_pause)
        message = "Play command sent to Spotify. Playback state was not verified."
        ok = True
    except Exception as exc:
        ok = False
        message = f"Spotify local playback failed: {exc}"

    speak(message)
    return {
        "ok": bool(ok),
        "status": "completed" if ok else "failed",
        "action": "spotify_play",
        "message": message,
        "playback_state_verified": False,
    }


def spotify_pause(data):
    try:
        keyboard.press(Key.media_play_pause)
        keyboard.release(Key.media_play_pause)
        message = "Pause command sent to Spotify. Playback state was not verified."
        ok = True
    except Exception as exc:
        ok = False
        message = f"Spotify local pause failed: {exc}"

    speak(message)
    return {
        "ok": ok,
        "status": "completed" if ok else "failed",
        "action": "spotify_pause",
        "message": message,
        "playback_state_verified": False,
    }

def spotify_next(data):
    try:
        keyboard.press(Key.media_next)
        keyboard.release(Key.media_next)
        ok = True
        message = "Next-track command sent to Spotify. Playback state was not verified."
    except Exception as exc:
        ok = False
        message = f"Spotify next-track control failed: {exc}"

    speak(message)
    return {
        "ok": ok,
        "status": "completed" if ok else "failed",
        "action": "spotify_next",
        "message": message,
        "playback_state_verified": False,
    }


def spotify_previous(data):
    try:
        keyboard.press(Key.media_previous)
        keyboard.release(Key.media_previous)
        ok = True
        message = "Previous-track command sent to Spotify. Playback state was not verified."
    except Exception as exc:
        ok = False
        message = f"Spotify previous-track control failed: {exc}"

    speak(message)
    return {
        "ok": ok,
        "status": "completed" if ok else "failed",
        "action": "spotify_previous",
        "message": message,
        "playback_state_verified": False,
    }


def spotify_volume_up(data):

    keyboard.press(Key.media_volume_up)
    keyboard.release(Key.media_volume_up)

    return True


def spotify_volume_down(data):

    keyboard.press(Key.media_volume_down)
    keyboard.release(Key.media_volume_down)

    return True

def spotify_play_song(data):

    song = data.get("song", "").strip()

    if not song:

        speak("Which song would you like me to play?")

        return True

    try:
        ok, message = play_track(song)
    except Exception as exc:
        ok = False
        message = f"Spotify playback is unavailable: {exc}"

    speak(message)
    if ok:
        print("[SPOTIFY]", message)

    return {
        "ok": bool(ok),
        "status": "completed" if ok else "failed",
        "action": "spotify_play_song",
        "message": message,
        "playback_state_verified": bool(ok),
        "song": song,
    }


register("spotify_open", spotify_open)
register("spotify_close", spotify_close)
register("spotify_play", spotify_play)
register("spotify_pause", spotify_pause)
register("spotify_next", spotify_next)
register("spotify_previous", spotify_previous)
register("spotify_volume_up", spotify_volume_up)
register("spotify_volume_down", spotify_volume_down)
register("spotify_play_song", spotify_play_song)

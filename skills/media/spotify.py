import os
import subprocess
import time

from pynput.keyboard import Controller, Key

from services.spotify_api import (
    play_track,
    ensure_spotify,
    resume_playback,
    pause_playback
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

    speak("Playing music")

    ensure_spotify()

    time.sleep(3)

    keyboard.press(Key.media_play_pause)
    keyboard.release(Key.media_play_pause)

    return True


def spotify_pause(data):

    speak("Pausing music")

    try:

        pause_playback()

    except:

        keyboard.press(Key.media_play_pause)
        keyboard.release(Key.media_play_pause)

    return True


def spotify_next(data):

    from services.spotify_api import spotify_client

    speak("Next song")

    try:
        spotify_client().next_track()
    except:
        keyboard.press(Key.media_next)
        keyboard.release(Key.media_next)

    return True


def spotify_previous(data):

    from services.spotify_api import spotify_client

    speak("Previous song")

    try:
        spotify_client().previous_track()
    except:
        keyboard.press(Key.media_previous)
        keyboard.release(Key.media_previous)

    return True


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

    speak(f"Playing {song}")

    ok, message = play_track(song)

    if not ok:

        speak(message)

    else:

        print("[SPOTIFY]", message)

    return True


register("spotify_open", spotify_open)
register("spotify_close", spotify_close)
register("spotify_play", spotify_play)
register("spotify_pause", spotify_pause)
register("spotify_next", spotify_next)
register("spotify_previous", spotify_previous)
register("spotify_volume_up", spotify_volume_up)
register("spotify_volume_down", spotify_volume_down)
register("spotify_play_song", spotify_play_song)
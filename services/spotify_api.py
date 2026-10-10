import spotipy

import time

import os

import psutil

import subprocess

from spotipy.oauth2 import SpotifyOAuth

from config.spotify import (
    CLIENT_ID,
    CLIENT_SECRET,
    REDIRECT_URI
)

SCOPE = (
    "user-read-playback-state "
    "user-modify-playback-state "
    "user-read-currently-playing "
    "user-library-read "
)

def spotify_client():
    if not CLIENT_ID or not CLIENT_SECRET:
        raise RuntimeError(
            "Spotify credentials are not configured."
        )

    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            cache_path=".spotify_cache"
        )
    )
    
def is_spotify_running():

    for process in psutil.process_iter(["name"]):
        try:
            if process.info["name"] and process.info["name"].lower() == "spotify.exe":
                return True
        except:
            pass

    return False

def ensure_spotify():

    if is_spotify_running():
        return

    try:
        os.startfile("spotify:")
    except:
        subprocess.Popen("start spotify:", shell=True)

    # * Wait for process
    for _ in range(30):

        if is_spotify_running():
            break

        time.sleep(1)

    # * Extra time for Spotify to connect
    time.sleep(5)

def get_device():

    ensure_spotify()

    spotify = spotify_client()

    for _ in range(15):

        try:

            devices = spotify.devices()["devices"]

            if devices:

                for device in devices:

                    if device["is_active"]:
                        return device["id"]

                return devices[0]["id"]

        except Exception as e:

            print("[SPOTIFY]", e)

        time.sleep(1)

    return None


def resume_playback():

    spotify = spotify_client()

    device = get_device()

    if device is None:
        return False, "No Spotify device found."

    spotify.transfer_playback(
        device_id=device,
        force_play=False
    )

    spotify.start_playback(device_id=device)

    return True, "Playback resumed."

def pause_playback():

    spotify = spotify_client()

    spotify.pause_playback()

    return True, "Playback paused."

def search_track(song):

    spotify = spotify_client()

    results = spotify.search(
        q=song,
        type="track",
        limit=1
    )

    items = results["tracks"]["items"]

    if not items:
        return None

    return items[0]

def play_track(song):

    spotify = spotify_client()

    device = get_device()

    if device is None:
        return False, "No Spotify device found."

    track = search_track(song)

    if track is None:
        return False, f"I couldn't find {song}."

    try:
        spotify.transfer_playback(
            device_id=device,
            force_play=True
        )
    except Exception as e:
        print(e)

    spotify.start_playback(
        device_id=device,
        uris=[track["uri"]]
    )

    artist = track["artists"][0]["name"]

    return True, f"Sure. Playing {track['name']} by {artist}."


def current_song():

    spotify = spotify_client()

    song = spotify.current_playback()

    if not song or not song["is_playing"]:
        return None

    item = song["item"]

    return (
        item["name"],
        item["artists"][0]["name"]
    )
    
    
# * _PREMIUM = None


# * def is_premium():

# * global _PREMIUM

# * if _PREMIUM is not None:
# * return _PREMIUM

# * try:

# * spotify = spotify_client()

# * user = spotify.me()

# * _PREMIUM = (
# * user.get("product", "").lower() == "premium"
# * )

# * except Exception as e:

# * print("[SPOTIFY] Premium check failed:", e)

# * _PREMIUM = False

# * return _PREMIUM

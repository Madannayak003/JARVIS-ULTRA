import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import threading
import time


pygame.mixer.init()

_lock = threading.Lock()


# * =========================================================
# * Play
# * =========================================================

def play(
    file,
    cancel_event=None,
):

    with _lock:

        # * -------------------------------------------------
        # * Cancel before playback
        # * -------------------------------------------------

        if (
            cancel_event
            and cancel_event.is_set()
        ):

            return False

        # * -------------------------------------------------
        # * Stop previous playback
        # * -------------------------------------------------

        pygame.mixer.music.stop()

        try:

            pygame.mixer.music.unload()

        except Exception:

            pass

        # * -------------------------------------------------
        # * Load
        # * -------------------------------------------------

        try:

            pygame.mixer.music.load(file)

            if (
                cancel_event
                and cancel_event.is_set()
            ):

                return False

            pygame.mixer.music.play()

        except Exception as e:

            print(
                "[PLAYER ERROR] "
                f"Could not play audio: {e}"
            )

            return False

        # * -------------------------------------------------
        # * Monitor playback
        # * -------------------------------------------------

        while pygame.mixer.music.get_busy():

            if (
                cancel_event
                and cancel_event.is_set()
            ):

                pygame.mixer.music.stop()

                try:

                    pygame.mixer.music.unload()

                except Exception:

                    pass

                print(
                    "[PLAYER] Playback interrupted"
                )

                return False

            time.sleep(0.02)

        # * -------------------------------------------------
        # * Release resource
        # * -------------------------------------------------

        pygame.mixer.music.stop()

        try:

            pygame.mixer.music.unload()

        except Exception as e:

            print(
                "[PLAYER] Could not unload audio:",
                e
            )

        return True


# * =========================================================
# * Stop
# * =========================================================

def stop():

    with _lock:

        pygame.mixer.music.stop()

        try:

            pygame.mixer.music.unload()

        except Exception:

            pass


# * =========================================================
# * Speaking Status
# * =========================================================

def speaking():

    return pygame.mixer.music.get_busy()

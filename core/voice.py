import threading
import pyttsx3

from core.context import add_message

engine = pyttsx3.init()

engine.setProperty("rate", 175)
engine.setProperty("volume", 1.0)

voices = engine.getProperty("voices")
engine.setProperty("voice", voices[0].id)

_lock = threading.Lock()


def speak(text):

    if not text:
        return

    add_message("assistant", text)

    with _lock:

        engine.stop()

        engine.say(text)

        engine.runAndWait()


def stop_speaking():

    with _lock:

        engine.stop()
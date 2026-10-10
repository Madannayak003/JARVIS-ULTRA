from core.registry import register
from voice.manager import speak

from skills.browser.browser_controller import browser


def ai_play(data):

    target = data.get("target", "")

    # * -----------------------------------------
    # * YouTube first result
    # * -----------------------------------------

    if target == "first_result":

        speak("Playing first result")

        return browser.play_first_video()

    # * -----------------------------------------
    # * Normal media resume
    # * -----------------------------------------

    browser.resume_video()

    return True


register("play", ai_play)
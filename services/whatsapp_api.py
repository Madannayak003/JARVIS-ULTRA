import os
import subprocess
import psutil
import time
import pyautogui
import pyperclip

from PIL import Image
from io import BytesIO
import win32clipboard

from config.whatsapp import WHATSAPP_EXE

def open_whatsapp():

    try:

        os.startfile("whatsapp:")

        return True

    except:

        try:

            subprocess.Popen("start whatsapp:", shell=True)

            return True

        except:

            return False


def close_whatsapp():

    for process in psutil.process_iter(["name"]):

        try:

            if process.info["name"] == WHATSAPP_EXE:

                process.kill()

        except:

            pass

    return True

def open_chat(contact):

    if not open_whatsapp():
        return False

    time.sleep(3)

    # * Focus search
    pyautogui.hotkey("ctrl", "f")
    time.sleep(0.5)

    pyperclip.copy(contact)
    pyautogui.hotkey("ctrl", "v")

    time.sleep(2)

    pyautogui.press("enter")

    time.sleep(1)

    return True

def send_message(contact, message):

    if not open_chat(contact):

        return False

    pyperclip.copy(message)

    pyautogui.hotkey("ctrl", "v")

    time.sleep(0.2)

    pyautogui.press("enter")

    return True

def send_photo(contact, image_path):

    if not os.path.exists(image_path):

        return False

    if not open_chat(contact):

        return False

    try:

        copy_image_to_clipboard(image_path)

    except Exception as e:

        print("[WHATSAPP]", e)

        return False

    time.sleep(0.5)

    # * Paste image
    pyautogui.hotkey("ctrl", "v")

    # * Wait for WhatsApp preview
    time.sleep(2)

    # * Send image
    pyautogui.press("enter")

    return True

def copy_image_to_clipboard(image_path):

    image = Image.open(image_path)

    output = BytesIO()

    image.convert("RGB").save(
        output,
        "BMP"
    )

    data = output.getvalue()[14:]

    output.close()

    win32clipboard.OpenClipboard()

    try:

        win32clipboard.EmptyClipboard()

        win32clipboard.SetClipboardData(
            win32clipboard.CF_DIB,
            data
        )

    finally:

        win32clipboard.CloseClipboard()
        
def send_file(contact, file_path):

    if not os.path.exists(file_path):
        return False

    if not open_chat(contact):
        return False

    try:

        # * Open WhatsApp file picker
        pyautogui.hotkey("ctrl", "shift", "u")

        time.sleep(2)

        # * Paste full path
        pyperclip.copy(file_path)

        pyautogui.hotkey("ctrl", "v")

        time.sleep(0.5)

        pyautogui.press("enter")

        # * Wait for preview/upload
        time.sleep(3)

        # * Send
        pyautogui.press("enter")

        return True

    except Exception as e:

        print("[WHATSAPP]", e)

        return False

# * =========================================================
# * WhatsApp Voice Call
# * =========================================================

def call_contact(contact):

    if not open_chat(contact):
        return False

    try:

        time.sleep(1)

        pyautogui.hotkey(
            "ctrl",
            "shift",
            "c"
        )

        print(
            f"[WHATSAPP] Voice call started: {contact}"
        )

        return True

    except Exception as e:

        print(
            f"[WHATSAPP] Voice call failed: {e}"
        )

        return False

# * =========================================================
# * WhatsApp Video Call
# * =========================================================

def video_call_contact(contact):

    if not open_chat(contact):
        return False

    try:

        time.sleep(1)

        pyautogui.hotkey(
            "ctrl",
            "shift",
            "v"
        )

        print(
            f"[WHATSAPP] Video call started: {contact}"
        )

        return True

    except Exception as e:

        print(
            f"[WHATSAPP] Video call failed: {e}"
        )

        return False    
    
def focus_whatsapp():

    try:

        subprocess.Popen("start whatsapp:", shell=True)

    except:

        pass

    time.sleep(1)

    pyautogui.hotkey("alt", "tab")

    time.sleep(0.5)

    return True
from pywinauto import Application
from pywinauto.findwindows import find_windows
from pywinauto.keyboard import send_keys


def connect_window(title):

    handles = find_windows(title_re=f".*{title}.*")

    if not handles:
        return None

    app = Application(backend="uia").connect(
        handle=handles[0]
    )

    return app.window(handle=handles[0])

def activate_window(title):

    window = connect_window(title)

    if window is None:
        return None

    window.set_focus()

    return window

def activate_whatsapp():

    return activate_window("WhatsApp")
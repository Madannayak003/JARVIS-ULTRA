"""
Native clipboard support for the standalone AI Chatbot.

This module provides a Windows system clipboard fallback for
native WebView environments where browser clipboard APIs may
not work reliably.
"""

from __future__ import annotations

import ctypes
import os
import time


CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

if os.name == "nt":
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.OpenClipboard.argtypes = [
        ctypes.c_void_p,
    ]
    user32.OpenClipboard.restype = ctypes.c_bool

    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = ctypes.c_bool

    user32.SetClipboardData.argtypes = [
        ctypes.c_uint,
        ctypes.c_void_p,
    ]
    user32.SetClipboardData.restype = ctypes.c_void_p

    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = ctypes.c_bool

    user32.GetOpenClipboardWindow.argtypes = []
    user32.GetOpenClipboardWindow.restype = ctypes.c_void_p

    kernel32.GlobalAlloc.argtypes = [
        ctypes.c_uint,
        ctypes.c_size_t,
    ]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p

    kernel32.GlobalLock.argtypes = [
        ctypes.c_void_p,
    ]
    kernel32.GlobalLock.restype = ctypes.c_void_p

    kernel32.GlobalUnlock.argtypes = [
        ctypes.c_void_p,
    ]
    kernel32.GlobalUnlock.restype = ctypes.c_bool

    kernel32.GlobalFree.argtypes = [
        ctypes.c_void_p,
    ]
    kernel32.GlobalFree.restype = ctypes.c_void_p


def copy_text_to_system_clipboard(
    text: str,
    retries: int = 5,
) -> bool:
    """
    Copy text directly to the Windows system clipboard.

    This is intended as a native fallback for pywebview/WebView2,
    where navigator.clipboard or execCommand("copy") may not work
    reliably.
    """

    if os.name != "nt":
        return False

    text = str(text)

    data = (
        text.encode("utf-16-le")
        + b"\x00\x00"
    )

    for attempt in range(max(1, retries)):
        handle = None
        locked_memory = None
        clipboard_open = False

        try:
            if not user32.OpenClipboard(None):
                time.sleep(0.05 * (attempt + 1))
                continue

            clipboard_open = True

            if not user32.EmptyClipboard():
                continue

            handle = kernel32.GlobalAlloc(
                GMEM_MOVEABLE,
                len(data),
            )

            if not handle:
                continue

            locked_memory = kernel32.GlobalLock(
                handle
            )

            if not locked_memory:
                continue

            ctypes.memmove(
                locked_memory,
                data,
                len(data),
            )

            kernel32.GlobalUnlock(handle)
            locked_memory = None

            result = user32.SetClipboardData(
                CF_UNICODETEXT,
                handle,
            )

            if result:
                # * Windows now owns this memory handle.
                handle = None
                return True

        except Exception as exc:
            print(
                "[AI CHAT CLIPBOARD] "
                f"Attempt {attempt + 1} failed: {exc}"
            )

        finally:
            if locked_memory is not None:
                kernel32.GlobalUnlock(
                    handle
                )

            if handle is not None:
                kernel32.GlobalFree(
                    handle
                )

            if clipboard_open:
                user32.CloseClipboard()

        time.sleep(
            0.05 * (attempt + 1)
        )

    return False
"""
=============================================================
JARVIS PRO — DASHBOARD SERVER
=============================================================

Mark Remote Dashboard adapted for JARVIS PRO.

Architecture:

    Phone
       ↓
    Dashboard
       ↓
    core.dispatcher.dispatch()
       ↓
    NCI / Fast Router / Skills

This server does NOT create another JARVIS brain.

Features:

    - 6-character pairing PIN
    - Multiple authenticated sessions
    - Device auto-reconnect
    - AES-256-CBC command encryption
    - WebSocket dashboard
    - Command/event history
    - File upload
    - File download
    - Phone microphone WebSocket queue
    - Direct Agent stop
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import mimetypes
import os
import shutil
import secrets
import socket
import threading
import time
from uuid import uuid4

from pathlib import Path
from typing import Callable, Optional

import json

from core.runtime import handle_priority
from core.interrupt import interrupt
from core.paths import CAPTURES, GENERATED_IMAGES, RECORDINGS, SCREENSHOTS
from core.diagnostics import debug_print
from ai.core.service import ai_service
from config.settings import (
    get_assistant_display_name,
    get_assistant_name_lower,
    get_gemini_live_gender_setting,
    GEMINI_LIVE_DEFAULT_VOICE,
    GEMINI_LIVE_FEMALE_VOICE,
    set_assistant_name,
)

from hud.integration import HUDIntegration
from hud.bus import hud_bus
from hud.events import (
    HUD_COMMAND,
    HUD_ERROR,
    HUD_NOTIFICATION,
    HUD_RESPONSE,
    HUD_SYSTEM_ACTIVITY,
)

from chatbot.ai_chat_api import (
    create_chat,
    list_chats,
    get_chat,
    delete_chat,
    rename_chat,
    send_message,
    get_model,
    set_model,
)

from chatbot.ai_chat_clipboard import (
    copy_text_to_system_clipboard,
)

from tools.windows_integration import (
    create_desktop_shortcut,
    get_autostart_status,
    set_autostart,
)

from hud.workspace_center import workspace_center
from skills.files.file_intelligence import (
    edit_file as intelligence_edit_file,
    file_intelligence_action,
    get_file as intelligence_get_file,
    list_files as intelligence_list_files,
    read_file as intelligence_read_file,
    remove_file as intelligence_remove_file,
    save_uploaded_file as intelligence_save_uploaded_file,
    search_files as intelligence_search_files,
    speak_file as intelligence_speak_file,
    file_speech_status as intelligence_file_speech_status,
    stop_file_speech as intelligence_stop_file_speech,
    summarize_file as intelligence_summarize_file,
)

from core.listener import (
    start_listener,
    pause_listener,
    resume_listener,
    listener_running,
    listener_paused,
)

# * =============================================================
# * FASTAPI
# * =============================================================

try:

    from fastapi import (
        FastAPI,
        File,
        Request,
        UploadFile,
        WebSocket,
        WebSocketDisconnect,
    )

    from fastapi.middleware.cors import CORSMiddleware

    from fastapi.responses import (
        FileResponse,
        HTMLResponse,
        JSONResponse,
    )

    from fastapi.staticfiles import StaticFiles

    import uvicorn

    FASTAPI_AVAILABLE = True

except ImportError:

    FastAPI = None
    File = None
    Request = None
    UploadFile = None
    WebSocket = None
    WebSocketDisconnect = None

    FileResponse = None
    HTMLResponse = None
    JSONResponse = None

    StaticFiles = None
    uvicorn = None

    FASTAPI_AVAILABLE = False


# * =============================================================
# * MULTIPART
# * =============================================================

try:

    import multipart

    MULTIPART_AVAILABLE = True

except ImportError:

    MULTIPART_AVAILABLE = False


# * =============================================================
# * PATHS / CONFIGURATION
# * =============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

STATIC_DIR = (
    Path(__file__)
    .resolve()
    .parent
    / "static"
)

STATIC_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


PORT = 8765

PIN_EXPIRY_SECONDS = 600

MAX_UPLOAD_MB = 500

PIN_CHARS = (
    "ABCDEFGHJKMNPQRSTUVWXYZ"
    "23456789"
)

AES_SALT = (
    b"JARVIS-DASHBOARD-v1"
)


# * =============================================================
# * UPLOAD DIRECTORY
# * =============================================================

def _make_uploads_dir() -> Path:

    candidates = (

        Path.home()
        / "Downloads"
        / "JARVIS Uploads",

        Path.home()
        / "Documents"
        / "JARVIS Uploads",

        BASE_DIR
        / "uploads",
    )

    for candidate in candidates:

        try:

            candidate.mkdir(
                parents=True,
                exist_ok=True,
            )

            return candidate

        except Exception:

            pass

    fallback = (
        BASE_DIR
        / "uploads"
    )

    fallback.mkdir(
        parents=True,
        exist_ok=True,
    )

    return fallback


UPLOADS_DIR = (
    _make_uploads_dir()
)


# * =============================================================
# * LOCAL IP
# * =============================================================

def _local_ip() -> str:
    """
    Find the LAN IP used by JARVIS.

    This does not send application data.
    It only asks Windows which local interface
    would be used for the UDP route.
    """

    for probe in (
        "8.8.8.8",
        "1.1.1.1",
        "192.168.1.1",
    ):

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        try:

            sock.settimeout(0.5)

            sock.connect(
                (
                    probe,
                    80,
                )
            )

            ip = (
                sock
                .getsockname()[0]
            )

            if not ip.startswith(
                "127."
            ):

                return ip

        except Exception:

            pass

        finally:

            sock.close()

    # * ---------------------------------------------------------
    # * Fallback
    # * ---------------------------------------------------------

    try:

        ip = socket.gethostbyname(
            socket.gethostname()
        )

        if not ip.startswith(
            "127."
        ):

            return ip

    except Exception:

        pass

    return "127.0.0.1"


# * =============================================================
# * STATIC FILES
# * =============================================================

def _read_static(
    filename: str,
) -> str:

    path = (
        STATIC_DIR
        / filename
    )

    content = path.read_text(
        encoding="utf-8"
    )

    # * Static dashboard pages use explicit identity placeholders so protocol
    # * and storage identifiers remain literal and unchanged.
    return (
        content
        .replace("__ASSISTANT_NAME__", get_assistant_display_name())
        .replace("__ASSISTANT_NAME_LOWER__", get_assistant_name_lower())
    )


# * =============================================================
# * AES-256
# * =============================================================

def _derive_key(
    session_key: str,
) -> bytes:

    return hashlib.sha256(
        session_key.encode(
            "utf-8"
        )
        + AES_SALT
    ).digest()


def _decrypt_cbc(
    aes_key: bytes,
    encrypted: str,
) -> str:

    from cryptography.hazmat.primitives.ciphers import (
        Cipher,
        algorithms,
        modes,
    )

    from cryptography.hazmat.primitives import (
        padding,
    )

    raw = base64.b64decode(
        encrypted
    )

    if len(raw) < 32:

        raise ValueError(
            "Invalid encrypted payload."
        )

    iv = raw[:16]

    ciphertext = raw[16:]

    decryptor = Cipher(
        algorithms.AES(
            aes_key
        ),
        modes.CBC(
            iv
        ),
    ).decryptor()

    padded = (
        decryptor.update(
            ciphertext
        )
        + decryptor.finalize()
    )

    unpadder = (
        padding.PKCS7(
            128
        ).unpadder()
    )

    plaintext = (
        unpadder.update(
            padded
        )
        + unpadder.finalize()
    )

    return plaintext.decode(
        "utf-8"
    )

# * =============================================================
# * ENGLISH VOICE SETTINGS
# * =============================================================

VOICE_SETTINGS_FILE = (
    BASE_DIR
    / "data"
    / "settings"
    / "jarvis_settings.json"
)


def _load_english_voice() -> str:
    try:
        if not VOICE_SETTINGS_FILE.exists():
            return "Ryan"

        with VOICE_SETTINGS_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            settings = json.load(file)

        voice = str(
            settings.get(
                "assistantVoice",
                "Ryan",
            )
        ).strip()

        from voice.online_edge import ENGLISH_VOICES

        if voice in ENGLISH_VOICES:
            return voice

    except Exception as exc:
        print(
            "[VOICE SETTINGS] Load failed:",
            exc,
        )

    return "Ryan"


def _save_english_voice(
    voice_name: str,
) -> None:

    VOICE_SETTINGS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    settings = {}

    if VOICE_SETTINGS_FILE.exists():
        try:
            with VOICE_SETTINGS_FILE.open(
                "r",
                encoding="utf-8",
            ) as file:
                settings = json.load(file)
        except Exception:
            settings = {}

    settings["assistantVoice"] = voice_name

    with VOICE_SETTINGS_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            settings,
            file,
            indent=2,
        )
        file.write("\n")

# * =============================================================
# * DASHBOARD SERVER
# * =============================================================

class DashboardServer:

    def __init__(
        self,
        command_handler: Optional[
            Callable[[str], object]
        ] = None,

        agent_stop_handler: Optional[
            Callable[..., object]
        ] = None,

        port: int = PORT,
    ):

        # * -----------------------------------------------------
        # * Existing JARVIS dispatcher
        # * -----------------------------------------------------

        self.command_handler = (
            command_handler
        )

        # * -----------------------------------------------------
        # * Direct Agent stop
        # * -----------------------------------------------------

        self.agent_stop_handler = (
            agent_stop_handler
        )

        # * -----------------------------------------------------
        # * Network
        # * -----------------------------------------------------

        self.port = int(
            port
        )

        self.ip = _local_ip()

        # * -----------------------------------------------------
        # * Pairing
        # * -----------------------------------------------------

        self._pin = None

        self._pin_expiry = 0.0

        # * -----------------------------------------------------
        # * Authentication
        #
        # * token -> session key
        # * -----------------------------------------------------

        self._tokens = set()

        self._token_keys = {}

        # * -----------------------------------------------------
        # * Persistent device sessions
        #
        # * device token -> session information
        # * -----------------------------------------------------

        self._device_sessions = {}

        # * -----------------------------------------------------
        # * WebSocket clients
        # * -----------------------------------------------------

        self._clients = set()

        # * -----------------------------------------------------
        # * Dashboard history
        # * -----------------------------------------------------

        self._history = []

        self._history_event_ids = set()

        self._history_lock = threading.Lock()

        self._hud_events_subscribed = False

        # * -----------------------------------------------------
        # * Phone audio
        #
        # * This queue will later be connected to the
        # * existing JARVIS Agent engine.
        # * -----------------------------------------------------

        self._phone_audio_queue = (
            asyncio.Queue(
                maxsize=200
            )
        )

        # * -----------------------------------------------------
        # * Async event loop
        # * -----------------------------------------------------

        self._loop = None

        # * -----------------------------------------------------
        # * Server thread
        # * -----------------------------------------------------

        self._thread = None

        # * -----------------------------------------------------
        # * HTML
        # * -----------------------------------------------------

        self._login_html = (
            _read_static(
                "login.html"
            )
        )

        self._app_html = (
            _read_static(
                "app.html"
            )
        )

        # * -----------------------------------------------------
        # * FastAPI
        # * -----------------------------------------------------

        self.app = (

            self._build_app()

            if FASTAPI_AVAILABLE

            else None
        )
        
        # * -----------------------------------------------------
        # * Connect JARVIS voice output to Remote Dashboard
        # * -----------------------------------------------------

        try:

            from voice.manager import (
                add_speech_listener
            )

            add_speech_listener(
                self._on_voice_output
            )

            debug_print(
                "[REMOTE] Voice output bridge connected."
            )

        except Exception as e:

            print(
                "[REMOTE] Voice output bridge failed:",
                e
            )

        self._subscribe_hud_events()
            
        # * -----------------------------------------------------
        # * Restore saved English voice
        # * -----------------------------------------------------

        try:

            from voice.online_edge import (
                set_english_voice,
            )

            saved_voice = (
                _load_english_voice()
            )

            set_english_voice(
                saved_voice
            )

            debug_print(
                "[VOICE SETTINGS] "
                f"Restored: {saved_voice}"
            )

        except Exception as exc:

            print(
                "[VOICE SETTINGS] "
                "Restore failed:",
                exc,
            )
            
    # * =========================================================
    # * JARVIS VOICE OUTPUT → HUD + REMOTE DASHBOARD
    # * =========================================================

    def _on_voice_output(
        self,
        text: str,
    ):

        if not text:
            return

        text = str(text).strip()

        if not text:
            return

        debug_print(
            "[REMOTE VOICE] Sending:",
            text,
        )

        # * -----------------------------------------------------
        # * HUD Activity Log
        #
        # * This records the actual JARVIS response.
        # * It does NOT control voice playback.
        # * -----------------------------------------------------

        try:

            from hud.integration import (
                HUDIntegration
            )

            from core.live_execution import (
                is_live_execution
            )

            speaker = (
                "live"
                if is_live_execution()
                else "jarvis"
            )

            HUDIntegration.response(
                text,
                speaker=speaker
            )

        except Exception as exc:

            print(
                "[HUD RESPONSE LOG] Failed:",
                exc
            )

    # * =========================================================
    # * PAIRING PIN
    # * =========================================================

    def new_pairing_pin(
        self,
        expiry_seconds: int = (
            PIN_EXPIRY_SECONDS
        ),
    ) -> str:

        self._pin = "".join(

            secrets.choice(
                PIN_CHARS
            )

            for _ in range(6)
        )

        self._pin_expiry = (
            time.time()
            + int(
                expiry_seconds
            )
        )

        # * -----------------------------------------------------
        # * New pairing invalidates current sessions.
        # * -----------------------------------------------------

        self._tokens.clear()

        self._token_keys.clear()

        debug_print(
            "[REMOTE] New pairing PIN generated."
        )

        return self._pin

    # * =========================================================
    # * URL
    # * =========================================================

    def url(self) -> str:

        return (
            f"http://"
            f"{self.ip}:"
            f"{self.port}"
        )

    def pairing_host(self) -> str:
        """Return an optional explicitly configured private-network host.

        The listener remains bound by the existing server startup path. This
        value only controls the address embedded in a QR pairing URL, allowing
        a Tailscale/private-VPN address to be advertised without guessing or
        scanning network interfaces.
        """
        return os.getenv("JARVIS_REMOTE_HOST", "").strip() or self.ip

    # * =========================================================
    # * PAIRING URL
    # * =========================================================

    def pairing_url(self) -> str:

        return (
            f"http://{self.pairing_host()}:{self.port}"
            f"/login"
            f"?pin={self._pin or ''}"
        )

    # * =========================================================
    # * AUTH
    # * =========================================================

    def _get_token(
        self,
        request: Request,
    ) -> Optional[str]:

        auth = request.headers.get(
            "authorization",
            "",
        )

        token = (
            auth
            .removeprefix(
                "Bearer "
            )
            .strip()
        )

        if token in self._tokens:

            return token

        return None

    def _authorize(
        self,
        request: Request,
    ) -> bool:

        return (
            self._get_token(
                request
            )
            is not None
        )
        
    # * =========================================================
    # * LOCAL CONTROL AUTHORIZATION
    # * =========================================================

    def _authorize_local(
        self,
        request: Request,
    ) -> bool:
        """
        Allow local JARVIS HUD controls only from this PC.

        Remote phones/devices must not be able to create
        Windows shortcuts or modify Windows startup.
        """

        client = request.client

        if client is None:
            return False

        host = client.host

        return host in {
            "127.0.0.1",
            "::1",
            self.ip,
        }

    def _android_status_payload(self):
        """Serialize the shared Android bridge status for the local HUD."""
        from services.android import get_android_manager

        status = get_android_manager().connection_status()
        device = status.selected_device
        return {
            "ok": True,
            "adb_available": status.adb_available,
            "adb_path": status.adb_path or "",
            "connected": status.connected,
            "device": device.display_name if device else "",
            "serial": device.serial if device else "",
            "model": status.model,
            "connection_type": status.connection_type,
            "endpoint": status.endpoint or "",
            "host": status.host,
            "port": status.port,
            "wireless_endpoints": list(status.wireless_endpoints),
            "android_version": status.android_version,
            "error": status.error,
        }

    # * =========================================================
    # * BROADCAST
    # * =========================================================

    def _subscribe_hud_events(self):

        if self._hud_events_subscribed:

            return

        hud_bus.subscribe(
            self._on_hud_event
        )

        self._hud_events_subscribed = True

    def _unsubscribe_hud_events(self):

        if not self._hud_events_subscribed:

            return

        hud_bus.unsubscribe(
            self._on_hud_event
        )

        self._hud_events_subscribed = False

    @staticmethod
    def _event_id(message):

        return (
            message.get("event_id")
            or message.get("message_id")
            or message.get("id")
        )

    def _record_message(self, message):
        """Record one remote event, suppressing repeated identities."""

        payload = dict(message)

        event_id = self._event_id(payload)

        if not event_id:

            event_id = uuid4().hex

            payload["event_id"] = event_id

        with self._history_lock:

            if event_id in self._history_event_ids:

                debug_print(
                    "[REMOTE EVENT] Duplicate suppressed:",
                    event_id,
                )

                return None

            self._history_event_ids.add(event_id)

            self._history.append(payload)

            if len(self._history) > 300:

                removed = self._history[:-300]

                self._history = self._history[-300:]

                for old in removed:

                    old_id = self._event_id(old)

                    if old_id:

                        self._history_event_ids.discard(old_id)

        return payload

    def _on_hud_event(self, event):
        """Mirror shared HUD activity events into the remote stream."""

        name = getattr(event, "name", "")

        data = getattr(event, "data", {}) or {}

        if name == HUD_COMMAND:

            payload = {
                "type": "log",
                "speaker": "user",
                "text": str(data.get("text", "")),
            }

        elif name == HUD_RESPONSE:

            payload = {
                "type": "log",
                "speaker": str(data.get("speaker", "jarvis")),
                "text": str(data.get("text", "")),
            }

        elif name in {
            HUD_SYSTEM_ACTIVITY,
            HUD_NOTIFICATION,
            HUD_ERROR,
        }:

            message = (
                data.get("message")
                or data.get("error")
                or ""
            )

            payload = {
                "type": "sys",
                "text": str(message),
            }

        else:

            return

        payload.update({
            "event_id": getattr(event, "event_id", "") or uuid4().hex,
            "timestamp": getattr(event, "timestamp", ""),
            "source": getattr(event, "source", None),
        })

        if not payload["text"]:

            return

        debug_print(
            "[REMOTE EVENT] "
            f"{payload.get('speaker', 'system').upper()} event emitted:",
            payload["event_id"],
        )

        self._broadcast_threadsafe(payload)

    async def broadcast(
        self,
        message: dict,
    ):

        message = self._record_message(message)

        if message is None:

            return

        dead = set()

        for client in list(
            self._clients
        ):

            try:

                await client.send_json(
                    message
                )

            except Exception:

                dead.add(
                    client
                )

        self._clients.difference_update(
            dead
        )

    # * =========================================================
    # * THREADSAFE BROADCAST
    # * =========================================================

    def _broadcast_threadsafe(
        self,
        message: dict,
    ):

        if self._loop is None:

            # * Keep events emitted before a remote client connects so the
            # * normal websocket replay path can deliver them later.
            self._record_message(message)

            return

        try:

            asyncio.run_coroutine_threadsafe(

                self.broadcast(
                    message
                ),

                self._loop,
            )

        except Exception:

            pass

    # * =========================================================
    # * REMOTE COMMAND
    # * =========================================================

    def _run_command(
        self,
        text: str,
    ):

        debug_print(
            "[REMOTE COMMAND] Received:",
            text,
        )

        # * The HUD bus is the single authoritative activity stream. The
        # * same event is consumed by the desktop Activity Log and by the
        # * remote dashboard subscriber.
        HUDIntegration.command(
            text,
            source="remote_control",
        )

        # * =====================================================
        # * PRIORITY INTERRUPT
        #
        # * "stop conversation" means:
        # * stop the current response/task.
        #
        # * It does NOT stop Agent.
        # * =====================================================

        try:

            if handle_priority(text):

                HUDIntegration.response(
                    "Stopped."
                )

                return

        except Exception as exc:

            print(
                "[REMOTE INTERRUPT ERROR]",
                exc,
            )

            HUDIntegration.system_activity(
                f"Interrupt error: {exc}"
            )

            return

        # * =====================================================
        # * NORMAL COMMAND
        # * =====================================================

        if not self.command_handler:

            print(
                "[REMOTE COMMAND] "
                "ERROR: dispatcher not connected."
            )

            HUDIntegration.system_activity(
                f"{get_assistant_display_name()} dispatcher is not connected."
            )

            return

        # * =====================================================
        # * LIVE TEXT BRIDGE
        #
        # * All conversational text is sent to the one Gemini Live session.
        # * There is deliberately no dispatcher fallback: that would create a
        # * second conversational controller and could execute a request twice.
        # * =====================================================

        try:

            from voice.agent import (
                agent_state,
                send_agent_text,
            )

            if agent_state()["connected"]:

                if send_agent_text(text):

                    return

        except Exception as exc:

            print(
                "[LIVE TEXT BRIDGE] Failed:",
                exc,
            )

        # Live unavailable: report the real state and do not execute through
        # the legacy dispatcher or another model.
        print("[LIVE TEXT BRIDGE] Gemini Live is unavailable; request not executed.")
        HUDIntegration.system_activity(
            "Gemini Live is unavailable. Request not executed."
        )

    # * =========================================================
    # * BUILD FASTAPI
    # * =========================================================

    def _build_app(
        self,
    ):

        app = FastAPI(
            docs_url=None,
            redoc_url=None,
        )

        # * -----------------------------------------------------
        # * CORS
        #
        # * The JARVIS PRO HUD runs on Next.js
        # * while the remote dashboard runs on Python.
        # * -----------------------------------------------------

        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:3000",
                "http://127.0.0.1:3000",

                # * JARVIS PRO HUD opened through the LAN address.
                f"http://{self.ip}:3000",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # * -----------------------------------------------------
        # * Static files
        # * -----------------------------------------------------

        if StaticFiles:

            app.mount(
                "/static",
                StaticFiles(
                    directory=str(
                        STATIC_DIR
                    )
                ),
                name="static",
            )

        # * -----------------------------------------------------
        # * CryptoJS compatibility
        #
        # * app.html expects:
        #
        # * /static/crypto.js
        #
        # * Mark's folder contains:
        #
        # * crypto-js.min.js
        #
        # * So expose the same file under crypto.js.
        # * -----------------------------------------------------

        @app.get(
            "/static/crypto.js"
        )
        async def crypto_js():

            crypto_file = (
                STATIC_DIR
                / "crypto-js.min.js"
            )

            if not crypto_file.exists():

                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            "crypto-js.min.js "
                            "is missing."
                        ),
                    },
                    status_code=404,
                )

            return FileResponse(
                str(
                    crypto_file
                ),
                media_type=(
                    "application/javascript"
                ),
            )

        # * =====================================================
        # * LOGIN PAGE
        # * =====================================================

        @app.get(
            "/login",
            response_class=HTMLResponse,
        )
        async def login_page():

            return HTMLResponse(
                _read_static("login.html")
            )

        # * =====================================================
        # * DASHBOARD
        # * =====================================================

        @app.get(
            "/",
            response_class=HTMLResponse,
        )
        async def index():

            html = (
                _read_static("app.html")
                .replace(
                    "__IP__",
                    self.ip,
                )
                .replace(
                    "__PORT__",
                    str(
                        self.port
                    ),
                )
            )

            return HTMLResponse(
                html
            )

        # * =====================================================
        # * LOGIN
        # * =====================================================

        @app.post(
            "/login"
        )
        async def login(
            request: Request,
        ):

            self._loop = (
                asyncio.get_running_loop()
            )

            try:

                body = (
                    await request.json()
                )

            except Exception:

                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            "Invalid request."
                        ),
                    },
                    status_code=400,
                )

            entered = str(
                body.get(
                    "pin",
                    "",
                )
            ).strip().upper()

            # * -------------------------------------------------
            # * Validate PIN
            # * -------------------------------------------------

            if (
                not self._pin
                or time.time()
                > self._pin_expiry
                or entered
                != self._pin
            ):

                print(
                    "[REMOTE LOGIN] "
                    "Invalid or expired PIN."
                )

                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            "Invalid or expired key."
                        ),
                    },
                    status_code=401,
                )

            # * -------------------------------------------------
            # * Create session
            # * -------------------------------------------------

            session_key = (
                secrets.token_urlsafe(
                    32
                )
            )

            token = (
                secrets.token_urlsafe(
                    32
                )
            )

            device_token = (
                secrets.token_urlsafe(
                    32
                )
            )

            self._tokens.add(
                token
            )

            self._token_keys[
                token
            ] = session_key

            self._device_sessions[
                device_token
            ] = {
                "session_key":
                    session_key,

                "created_at":
                    time.time(),
            }

            remaining = max(
                0,
                int(
                    self._pin_expiry
                    - time.time()
                ),
            )

            print(
                "[REMOTE LOGIN] SUCCESS."
            )

            print(
                "[REMOTE LOGIN] "
                "Remote device authenticated."
            )

            print(
                "[REMOTE LOGIN] "
                f"PIN remaining: {remaining}s"
            )

            await self.broadcast({
                "type": "sys",
                "text": (
                    "Remote device connected."
                ),
            })

            return {
                "ok": True,
                "token": token,
                "key": session_key,
                "device_token":
                    device_token,
            }

        # * =====================================================
        # * DEVICE AUTO LOGIN
        # * =====================================================

        @app.post(
            "/api/device-login"
        )
        async def device_login(
            request: Request,
        ):

            self._loop = (
                asyncio.get_running_loop()
            )

            try:

                body = (
                    await request.json()
                )

            except Exception:

                return JSONResponse(
                    {
                        "ok": False
                    },
                    status_code=400,
                )

            device_token = str(
                body.get(
                    "device_token",
                    "",
                )
            ).strip()

            device = (
                self._device_sessions.get(
                    device_token
                )
            )

            if not device:

                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            "Device session "
                            "not found."
                        ),
                    },
                    status_code=401,
                )

            session_key = (
                device[
                    "session_key"
                ]
            )

            token = (
                secrets.token_urlsafe(
                    32
                )
            )

            self._tokens.add(
                token
            )

            self._token_keys[
                token
            ] = session_key

            print(
                "[REMOTE] "
                "Known device reconnected."
            )

            await self.broadcast({
                "type": "sys",
                "text": (
                    "Known device "
                    "reconnected automatically."
                ),
            })

            return {
                "ok": True,
                "token": token,
                "key": session_key,
            }

        # * =====================================================
        # * INFO
        # * =====================================================

        @app.get(
            "/api/info"
        )
        async def info():

            pairing_active = (
                bool(self._pin)
                and
                time.time()
                < self._pin_expiry
            )

            return {
                "ok": True,

                "assistant_name": get_assistant_display_name(),

                "url": self.url(),

                "pairing_url": (
                    self.pairing_url()
                    if pairing_active
                    else ""
                ),

                "pairing_pin": (
                    self._pin
                    if pairing_active
                    else ""
                ),

                "pairing_active": pairing_active,

                "pairing_remaining_seconds": max(
                    0,
                    int(self._pin_expiry - time.time())
                ) if pairing_active else 0,

                "clients": len(
                    self._clients
                ),
            }

        @app.post("/api/local/remote/new-pin")
        async def local_remote_new_pin(request: Request):
            if not self._authorize_local(request):
                return JSONResponse(
                    {"ok": False, "error": "Local access required."},
                    status_code=403,
                )
            try:
                self.new_pairing_pin()
                active = bool(self._pin) and time.time() < self._pin_expiry
                return {
                    "ok": True,
                    "pairing_pin": self._pin if active else "",
                    "pairing_url": self.pairing_url() if active else "",
                    "pairing_active": active,
                    "pairing_remaining_seconds": max(
                        0,
                        int(self._pin_expiry - time.time())
                    ) if active else 0,
                }
            except Exception:
                return JSONResponse(
                    {"ok": False, "error": "Unable to generate a new pairing PIN."},
                    status_code=500,
                )
            
        # * =====================================================
        # * LOCAL — ANDROID CONNECTION
        # * =====================================================

        @app.get("/api/local/android")
        async def local_android_status(request: Request):
            if not self._authorize_local(request):
                return JSONResponse(
                    {"ok": False, "error": "Local access required."},
                    status_code=403,
                )
            try:
                return self._android_status_payload()
            except Exception as exc:
                print("[LOCAL ANDROID STATUS ERROR]", exc)
                return JSONResponse(
                    {"ok": False, "error": "Android status unavailable."},
                    status_code=500,
                )

        # * =====================================================
        # * LOCAL — HUD WORKSPACE / PROJECT CENTER
        # * =====================================================

        @app.get("/api/local/workspace/projects")
        async def local_workspace_projects(request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)
            try:
                return workspace_center.list_projects()
            except Exception:
                return JSONResponse({"ok": False, "error": "Workspace is unavailable."}, status_code=500)

        @app.post("/api/local/workspace/{action}")
        async def local_workspace_action(action: str, request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)
            try:
                body = await request.json()
            except Exception:
                body = {}
            project_id = str(body.get("project_id", ""))
            if action == "start-preview":
                return workspace_center.start_preview(project_id, open_external=False)
            if action == "open-external":
                return workspace_center.open_externally(project_id)
            if action == "stop-preview":
                return workspace_center.stop_preview(project_id)
            if action == "open-folder":
                return workspace_center.open_folder(project_id)
            if action == "open-vscode":
                return workspace_center.open_in_vscode(project_id)
            if action == "delete":
                return workspace_center.delete_project(project_id)
            return JSONResponse({"ok": False, "error": "Unknown workspace action."}, status_code=404)

        # * =====================================================
        # * LOCAL — HUD GALLERY
        # * =====================================================

        gallery_directories = {
            "screenshots": (SCREENSHOTS, {".png", ".jpg", ".jpeg", ".webp", ".gif"}),
            "captures": (CAPTURES, {".png", ".jpg", ".jpeg", ".webp", ".gif"}),
            "generated_images": (GENERATED_IMAGES, {".png", ".jpg", ".jpeg", ".webp", ".gif"}),
            "recordings": (RECORDINGS, {".mp4", ".webm", ".mkv", ".avi", ".mov", ".wav", ".mp3", ".m4a", ".ogg"}),
        }

        @app.get("/api/local/gallery")
        async def local_gallery(request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)
            payload = {}
            for category, (directory, extensions) in gallery_directories.items():
                directory.mkdir(parents=True, exist_ok=True)
                items = []
                for item in sorted(directory.iterdir(), key=lambda path: path.stat().st_mtime, reverse=True):
                    if not item.is_file() or item.suffix.lower() not in extensions:
                        continue
                    stat = item.stat()
                    items.append({
                        "name": item.name,
                        "size": stat.st_size,
                        "modified_at": stat.st_mtime,
                        "url": f"/api/local/gallery/{category}/{item.name}",
                        "media_type": mimetypes.guess_type(item.name)[0] or "application/octet-stream",
                    })
                payload[category] = items
            return {"ok": True, **payload}

        @app.delete("/api/local/gallery/{category}/{filename:path}")
        async def local_gallery_delete(category: str, filename: str, request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)
            entry = gallery_directories.get(category)
            if not entry or "/" in filename or "\\" in filename:
                return JSONResponse({"ok": False, "error": "Gallery file not found."}, status_code=404)
            directory, extensions = entry
            source = (directory / filename).resolve()
            try:
                source.relative_to(directory.resolve())
            except ValueError:
                return JSONResponse({"ok": False, "error": "Gallery file not found."}, status_code=404)
            if not source.is_file() or source.suffix.lower() not in extensions:
                return JSONResponse({"ok": False, "error": "Gallery file not found."}, status_code=404)
            try:
                source.unlink()
                return {"ok": True, "filename": source.name}
            except Exception:
                return JSONResponse({"ok": False, "error": "Gallery delete failed."}, status_code=500)

        @app.get("/api/local/gallery/{category}/{filename:path}")
        async def local_gallery_file(category: str, filename: str, request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)
            entry = gallery_directories.get(category)
            if not entry or "/" in filename or "\\" in filename:
                return JSONResponse({"ok": False, "error": "Gallery file not found."}, status_code=404)
            directory, extensions = entry
            candidate = (directory / filename).resolve()
            try:
                candidate.relative_to(directory.resolve())
            except ValueError:
                return JSONResponse({"ok": False, "error": "Gallery file not found."}, status_code=404)
            if not candidate.is_file() or candidate.suffix.lower() not in extensions:
                return JSONResponse({"ok": False, "error": "Gallery file not found."}, status_code=404)
            return FileResponse(str(candidate), media_type=mimetypes.guess_type(candidate.name)[0] or "application/octet-stream")

        # * =====================================================
        # * LOCAL — FILE INTELLIGENCE
        # * =====================================================

        @app.get("/api/local/file-intelligence/files")
        async def local_file_intelligence_files(request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)
            return {"ok": True, "files": intelligence_list_files()}

        if MULTIPART_AVAILABLE and UploadFile is not None:
            @app.post("/api/local/file-intelligence/upload")
            async def local_file_intelligence_upload(request: Request, file: UploadFile = File(...)):
                if not self._authorize_local(request):
                    return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)
                try:
                    chunks = []
                    total = 0
                    while True:
                        chunk = await file.read(1024 * 1024)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > 500 * 1024 * 1024:
                            return JSONResponse({"ok": False, "error": "File exceeds 500 MB."}, status_code=413)
                        chunks.append(chunk)
                    record = intelligence_save_uploaded_file(file.filename or "upload", b"".join(chunks), mime_type=file.content_type or "")
                    return {"ok": True, "file": record}
                except Exception as exc:
                    return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)
                finally:
                    await file.close()

        @app.get("/api/local/file-intelligence/{file_id}")
        async def local_file_intelligence_read(file_id: str, request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)
            try:
                return {"ok": True, **intelligence_read_file(file_id)}
            except FileNotFoundError as exc:
                return JSONResponse({"ok": False, "error": str(exc)}, status_code=404)
            except Exception as exc:
                return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)

        @app.get("/api/local/file-intelligence/{file_id}/download")
        async def local_file_intelligence_download(file_id: str, request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)
            try:
                record = intelligence_get_file(file_id)
                return FileResponse(record["storage_path"], filename=record["filename"], media_type=record.get("mime_type"))
            except FileNotFoundError as exc:
                return JSONResponse({"ok": False, "error": str(exc)}, status_code=404)

        @app.post("/api/local/file-intelligence/search")
        async def local_file_intelligence_search(request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)
            body = await request.json()
            return {"ok": True, "results": intelligence_search_files(body.get("query", ""), body.get("file_ids"))}

        @app.post("/api/local/file-intelligence/{file_id}/summarize")
        async def local_file_intelligence_summarize(file_id: str, request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)
            try:
                body = await request.json()
                text = await asyncio.to_thread(intelligence_summarize_file, file_id, body.get("question", ""))
                return {"ok": True, "text": text}
            except Exception as exc:
                return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)

        @app.post("/api/local/file-intelligence/{file_id}/speak")
        async def local_file_intelligence_speak(file_id: str, request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)
            try:
                try:
                    body = await request.json()
                except Exception:
                    body = {}
                result = await asyncio.to_thread(intelligence_speak_file, file_id, str(body.get("text", "")))
                return {"ok": True, **result}
            except Exception as exc:
                return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)

        @app.get("/api/local/file-intelligence/speech/status")
        async def local_file_intelligence_speech_status(request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)
            return {"ok": True, **intelligence_file_speech_status()}

        @app.post("/api/local/file-intelligence/speech/stop")
        async def local_file_intelligence_speech_stop(request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)
            return {"ok": True, **intelligence_stop_file_speech()}

        @app.post("/api/local/file-intelligence/{file_id}/edit")
        async def local_file_intelligence_edit(file_id: str, request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)
            try:
                body = await request.json()
                return {"ok": True, "file": intelligence_edit_file(file_id, body.get("find", ""), body.get("replace", ""), expected_text=body.get("expected_text"))}
            except Exception as exc:
                return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)

        @app.post("/api/local/file-intelligence/{file_id}/open-folder")
        async def local_file_intelligence_open_folder(file_id: str, request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)
            try:
                return {"ok": True, "folder": file_intelligence_action({"action": "file_open_folder", "file_id": file_id})}
            except Exception as exc:
                return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)

        @app.delete("/api/local/file-intelligence/{file_id}")
        async def local_file_intelligence_remove(file_id: str, request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)
            return {"ok": intelligence_remove_file(file_id)}

        @app.post("/api/local/android/connect")
        async def local_android_connect(request: Request):
            if not self._authorize_local(request):
                return JSONResponse(
                    {"ok": False, "error": "Local access required."},
                    status_code=403,
                )
            try:
                body = await request.json()
                address = str(
                    body.get("ip", body.get("address", ""))
                ).strip()
                port = body.get("port", 5555)
                if not address:
                    return JSONResponse(
                        {"ok": False, "error": "Android IP address is required."},
                        status_code=400,
                    )

                from services.android import get_android_manager, normalize_endpoint

                manager = get_android_manager()
                manager.connect_wireless(address, port)
                payload = self._android_status_payload()
                endpoint = normalize_endpoint(address, port)
                connected = endpoint in payload["wireless_endpoints"]
                if not connected:
                    return JSONResponse(
                        {
                            "ok": False,
                            "status": payload,
                            "error": "Unable to connect to Android device.",
                        },
                        status_code=502,
                    )
                return {"ok": True, "status": payload}
            except (TypeError, ValueError) as exc:
                return JSONResponse(
                    {"ok": False, "error": str(exc)},
                    status_code=400,
                )
            except Exception as exc:
                print("[LOCAL ANDROID CONNECT ERROR]", exc)
                return JSONResponse(
                    {"ok": False, "error": "Unable to connect to Android device."},
                    status_code=502,
                )

        @app.post("/api/local/android/disconnect")
        async def local_android_disconnect(request: Request):
            if not self._authorize_local(request):
                return JSONResponse(
                    {"ok": False, "error": "Local access required."},
                    status_code=403,
                )
            try:
                body = await request.json()
            except Exception:
                body = {}

            try:
                from services.android import get_android_manager

                manager = get_android_manager()
                payload = self._android_status_payload()
                endpoint = str(body.get("endpoint", "")).strip()
                if not endpoint:
                    endpoint = str(payload.get("endpoint", "")).strip()
                if not endpoint or endpoint not in payload["wireless_endpoints"]:
                    return JSONResponse(
                        {
                            "ok": False,
                            "status": payload,
                            "error": "No connected wireless Android endpoint is selected.",
                        },
                        status_code=400,
                    )

                manager.disconnect_wireless(endpoint)
                return {"ok": True, "status": self._android_status_payload()}
            except (TypeError, ValueError) as exc:
                return JSONResponse(
                    {"ok": False, "error": str(exc)},
                    status_code=400,
                )
            except Exception as exc:
                print("[LOCAL ANDROID DISCONNECT ERROR]", exc)
                return JSONResponse(
                    {"ok": False, "error": "Unable to disconnect Android device."},
                    status_code=502,
                )

        # * =====================================================
        # * LOCAL — DESKTOP SHORTCUT
        # * =====================================================

        @app.post(
            "/api/local/shortcut"
        )
        async def local_shortcut(
            request: Request,
        ):

            if not self._authorize_local(
                request
            ):

                return JSONResponse(
                    {
                        "ok": False,
                        "error": "Local access required.",
                    },
                    status_code=403,
                )

            try:

                result = create_desktop_shortcut()

                return {
                    "ok": True,
                    "message": result,
                }

            except Exception as exc:

                print(
                    "[LOCAL SHORTCUT ERROR]",
                    exc,
                )

                return JSONResponse(
                    {
                        "ok": False,
                        "error": str(exc),
                    },
                    status_code=500,
                )


        # * =====================================================
        # * LOCAL — AUTO START STATUS
        # * =====================================================

        @app.get(
            "/api/local/autostart"
        )
        async def local_autostart_status(
            request: Request,
        ):

            if not self._authorize_local(
                request
            ):

                return JSONResponse(
                    {
                        "ok": False,
                        "error": "Local access required.",
                    },
                    status_code=403,
                )

            try:

                enabled = get_autostart_status()

                return {
                    "ok": True,
                    "enabled": enabled,
                }

            except Exception as exc:

                print(
                    "[LOCAL AUTOSTART STATUS ERROR]",
                    exc,
                )

                return JSONResponse(
                    {
                        "ok": False,
                        "error": str(exc),
                    },
                    status_code=500,
                )


        # * =====================================================
        # * LOCAL — AUTO START SET
        # * =====================================================

        @app.post(
            "/api/local/autostart"
        )
        async def local_autostart(
            request: Request,
        ):

            if not self._authorize_local(
                request
            ):

                return JSONResponse(
                    {
                        "ok": False,
                        "error": "Local access required.",
                    },
                    status_code=403,
                )

            try:

                body = await request.json()

            except Exception:

                return JSONResponse(
                    {
                        "ok": False,
                        "error": "Invalid request.",
                    },
                    status_code=400,
                )

            enabled = bool(
                body.get(
                    "enabled",
                    False,
                )
            )

            try:

                result = set_autostart(
                    enabled
                )

                return {
                    "ok": True,
                    "enabled": enabled,
                    "message": result,
                }

            except Exception as exc:

                print(
                    "[LOCAL AUTOSTART ERROR]",
                    exc,
                )

                return JSONResponse(
                    {
                        "ok": False,
                        "error": str(exc),
                    },
                    status_code=500,
                )
                
        # * =====================================================
        # * LOCAL — MICROPHONE STATUS
        # * =====================================================

        @app.get(
            "/api/local/microphone"
        )
        async def local_microphone_status(
            request: Request,
        ):

            if not self._authorize_local(
                request
            ):

                return JSONResponse(
                    {
                        "ok": False,
                        "error": "Local access required.",
                    },
                    status_code=403,
                )

            try:

                from voice.agent import _agent

                running = bool(_agent.running)
                connected = bool(_agent.connected)
                enabled = bool(_agent.microphone_enabled()) if running else False

                return {
                    "ok": True,
                    "enabled": enabled,
                    "running": running,
                    "connected": connected,
                    "state": "connected" if connected else ("reconnecting" if running else "unavailable"),
                    "paused": running and not enabled,
                    "controller": "gemini-live",
                }

            except Exception as exc:

                print(
                    "[LOCAL MICROPHONE STATUS ERROR]",
                    exc,
                )

                return JSONResponse(
                    {
                        "ok": False,
                        "error": str(exc),
                    },
                    status_code=500,
                )


        # * =====================================================
        # * LOCAL — MICROPHONE SET
        # * =====================================================

        @app.post(
            "/api/local/microphone"
        )
        async def local_microphone(
            request: Request,
        ):

            if not self._authorize_local(
                request
            ):

                return JSONResponse(
                    {
                        "ok": False,
                        "error": "Local access required.",
                    },
                    status_code=403,
                )

            try:

                body = await request.json()

            except Exception:

                return JSONResponse(
                    {
                        "ok": False,
                        "error": "Invalid request.",
                    },
                    status_code=400,
                )

            enabled = bool(
                body.get(
                    "enabled",
                    False,
                )
            )

            try:
                from voice.agent import _agent
            except Exception:
                return JSONResponse(
                    {"ok": False, "error": "Gemini Live microphone is unavailable."},
                    status_code=503,
                )

            if not _agent.running or not _agent.connected:
                return JSONResponse(
                    {"ok": False, "error": "Gemini Live is reconnecting or unavailable. Microphone not changed."},
                    status_code=503,
                )

            _agent.set_microphone_enabled(enabled, source="dashboard_toggle")
            actual_enabled = _agent.microphone_enabled()
            running = True
            paused = not actual_enabled

            print(
                "[LOCAL MICROPHONE]",
                "ON" if actual_enabled else "OFF",
            )

            try:

                HUDIntegration.system_activity(
                    "MICROPHONE "
                    + (
                        "ON"
                        if actual_enabled
                        else "OFF"
                    )
                )

            except Exception as exc:

                print(
                    "[HUD MICROPHONE LOG ERROR]",
                    exc,
                )

            return {
                "ok": True,
                "enabled": actual_enabled,
                "connected": True,
                "state": "connected",
                "running": running,
                "paused": paused,
                "controller": "gemini-live",
            }

        @app.post("/api/local/interrupt")
        async def local_interrupt(request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)
            try:
                interrupt(source="hud_button")
                return {"ok": True}
            except Exception:
                return JSONResponse({"ok": False, "error": "Interrupt unavailable."}, status_code=500)
                
        # * =====================================================
        # * LOCAL — MORNING BRIEF STATUS
        # * =====================================================

        @app.get(
            "/api/local/morning-brief"
        )
        async def local_morning_brief_status(
            request: Request,
        ):

            if not self._authorize_local(
                request
            ):

                return JSONResponse(
                    {
                        "ok": False,
                        "error": "Local access required.",
                    },
                    status_code=403,
                )

            settings_file = (
                Path(__file__).resolve().parent.parent
                / "data"
                / "settings"
                / "jarvis_settings.json"
            )

            try:

                if not settings_file.exists():

                    return {
                        "ok": True,
                        "enabled": True,
                    }

                with settings_file.open(
                    "r",
                    encoding="utf-8",
                ) as file:

                    settings = json.load(file)

                return {
                    "ok": True,
                    "enabled": bool(
                        settings.get(
                            "morningBrief",
                            True,
                        )
                    ),
                }

            except Exception as exc:

                print(
                    "[LOCAL MORNING BRIEF STATUS ERROR]",
                    exc,
                )

                return JSONResponse(
                    {
                        "ok": False,
                        "error": str(exc),
                    },
                    status_code=500,
                )


        # * =====================================================
        # * LOCAL — MORNING BRIEF SET
        # * =====================================================

        @app.post(
            "/api/local/morning-brief"
        )
        async def local_morning_brief(
            request: Request,
        ):

            if not self._authorize_local(
                request
            ):

                return JSONResponse(
                    {
                        "ok": False,
                        "error": "Local access required.",
                    },
                    status_code=403,
                )

            try:

                body = await request.json()

            except Exception:

                return JSONResponse(
                    {
                        "ok": False,
                        "error": "Invalid request.",
                    },
                    status_code=400,
                )

            enabled = bool(
                body.get(
                    "enabled",
                    False,
                )
            )
            
            try:

                HUDIntegration.system_activity(
                    "MORNING BRIEF "
                    + (
                        "ON"
                        if enabled
                        else "OFF"
                    )
                )

            except Exception as exc:

                print(
                    "[HUD MORNING BRIEF LOG ERROR]",
                    exc,
                )

            settings_file = (
                Path(__file__).resolve().parent.parent
                / "data"
                / "settings"
                / "jarvis_settings.json"
            )

            try:

                settings_file.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                settings = {}

                if settings_file.exists():

                    try:

                        with settings_file.open(
                            "r",
                            encoding="utf-8",
                        ) as file:

                            settings = json.load(file)

                    except Exception:

                        settings = {}

                settings["morningBrief"] = enabled

                with settings_file.open(
                    "w",
                    encoding="utf-8",
                ) as file:

                    json.dump(
                        settings,
                        file,
                        indent=2,
                    )

                    file.write("\n")

                print(
                    "[LOCAL MORNING BRIEF] "
                    f"Set to {'ON' if enabled else 'OFF'}"
                )

                return {
                    "ok": True,
                    "enabled": enabled,
                }

            except Exception as exc:

                print(
                    "[LOCAL MORNING BRIEF ERROR]",
                    exc,
                )

                return JSONResponse(
                    {
                        "ok": False,
                        "error": str(exc),
                    },
                    status_code=500,
                )
                
        # * =====================================================
        # * LOCAL — CUSTOMISE SETTINGS (NAME & COLOUR)
        # * =====================================================

        # * =====================================================
        # * LOCAL — CUSTOMISE SETTINGS (NAME & COLOUR)
        # * =====================================================

        @app.get("/api/local/customise")
        async def local_get_customise(request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)

            settings_file = Path(__file__).resolve().parent.parent / "data" / "settings" / "jarvis_settings.json"
            try:
                if not settings_file.exists():
                    return {
                        "ok": True,
                        "assistantName": get_assistant_display_name(),
                        "userName": "",
                        "assistantColour": "",
                    }

                with settings_file.open("r", encoding="utf-8") as f:
                    settings = json.load(f)

                return {
                    "ok": True,
                    "assistantName": get_assistant_display_name(),
                    "userName": settings.get("userName", ""),
                    "assistantColour": settings.get("assistantColour", ""),
                }
            except Exception as exc:
                return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
            

        @app.post("/api/local/customise")
        async def local_save_customise(request: Request,):
            if not self._authorize_local(request):
                return JSONResponse(
                    {"ok": False, "error": "Local access required."},
                    status_code=403,
                )

            try:
                body = await request.json()
            except Exception:
                return JSONResponse(
                    {"ok": False, "error": "Invalid JSON body."},
                    status_code=400,
                )

            settings_file = (
                Path(__file__).resolve().parent.parent
                / "data"
                / "settings"
                / "jarvis_settings.json"
            )

            try:
                settings_file.parent.mkdir(parents=True, exist_ok=True)
                settings = {}

                if settings_file.exists():
                    try:
                        with settings_file.open("r", encoding="utf-8") as f:
                            settings = json.load(f)
                    except Exception:
                        settings = {}

                if "assistantName" in body and body["assistantName"]:
                    settings["assistantName"] = set_assistant_name(
                        body["assistantName"]
                    )
                if "userName" in body:
                    settings["userName"] = str(body["userName"]).strip()
                if "assistantColour" in body and body["assistantColour"]:
                    settings["assistantColour"] = str(body["assistantColour"]).strip()

                with settings_file.open("w", encoding="utf-8") as f:
                    json.dump(settings, f, indent=2)
                    f.write("\n")

                print(
                    f"[LOCAL CUSTOMISE] Updated name: {settings.get('assistantName')} | colour: {settings.get('assistantColour')}"
                )

                return {"ok": True, "settings": settings}
            except Exception as exc:
                return JSONResponse(
                    {"ok": False, "error": str(exc)},
                    status_code=500,
                )

        # * =====================================================
        # * LOCAL — AI PROVIDER
        # * =====================================================

        @app.get("/api/local/ai-provider")
        async def local_ai_provider_status(request: Request):
            if not self._authorize_local(request):
                return JSONResponse(
                    {"ok": False, "error": "Local access required."},
                    status_code=403,
                )

            return {
                "ok": True,
                "provider": "GEMINI_LIVE",
                "model": "gemini-3.8-live",
            }

        @app.post("/api/local/ai-provider")
        async def local_ai_provider(request: Request):
            if not self._authorize_local(request):
                return JSONResponse(
                    {"ok": False, "error": "Local access required."},
                    status_code=403,
                )

            return JSONResponse(
                {
                    "ok": False,
                    "error": "Gemini Live is the only runtime provider and cannot be changed.",
                },
                status_code=409,
            )
                
        # * =====================================================
        # * LOCAL — ASSISTANT VOICE STATUS
        # * =====================================================

        @app.get(
            "/api/local/voice"
        )
        async def local_voice_status(
            request: Request,
        ):

            if not self._authorize_local(
                request
            ):
                return JSONResponse(
                    {
                        "ok": False,
                        "error": "Local access required.",
                    },
                    status_code=403,
                )

            try:
                from voice.online_edge import (
                    get_english_voice,
                )

                voice = get_english_voice()

                return {
                    "ok": True,
                    "voice": voice,
                }

            except Exception as exc:
                print(
                    "[LOCAL VOICE STATUS ERROR]",
                    exc,
                )

                return JSONResponse(
                    {
                        "ok": False,
                        "error": str(exc),
                    },
                    status_code=500,
                )


        # * =====================================================
        # * LOCAL — ASSISTANT VOICE SET
        # * =====================================================

        @app.post(
            "/api/local/voice"
        )
        async def local_voice(
            request: Request,
        ):

            if not self._authorize_local(
                request
            ):
                return JSONResponse(
                    {
                        "ok": False,
                        "error": "Local access required.",
                    },
                    status_code=403,
                )

            try:
                body = await request.json()
            except Exception:
                return JSONResponse(
                    {
                        "ok": False,
                        "error": "Invalid JSON body.",
                    },
                    status_code=400,
                )

            voice_name = str(
                body.get(
                    "voice",
                    "",
                )
            ).strip()

            try:
                from voice.online_edge import (
                    set_english_voice,
                    get_english_voice,
                    ENGLISH_VOICES,
                )

                if voice_name not in ENGLISH_VOICES:
                    return JSONResponse(
                        {
                            "ok": False,
                            "error": "Invalid English voice.",
                        },
                        status_code=400,
                    )

                if not set_english_voice(
                    voice_name
                ):
                    return JSONResponse(
                        {
                            "ok": False,
                            "error": "Unable to set English voice.",
                        },
                        status_code=500,
                    )

                _save_english_voice(
                    voice_name
                )

                current_voice = (
                    get_english_voice()
                )

                print(
                    "[LOCAL VOICE] Set to:",
                    current_voice,
                )

                return {
                    "ok": True,
                    "voice": current_voice,
                }

            except Exception as exc:
                print(
                    "[LOCAL VOICE ERROR]",
                    exc,
                )

                return JSONResponse(
                    {
                        "ok": False,
                        "error": str(exc),
                    },
                    status_code=500,
                )
                
        # * =====================================================
        # * LOCAL — GEMINI LIVE VOICE SETTINGS
        # * =====================================================

        @app.get("/api/local/live-voice")
        async def local_live_voice_status(request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)

            runtime = {}
            try:
                from voice.agent import live_voice_state

                runtime = live_voice_state()
            except Exception:
                pass

            return {
                "ok": True,
                "enabled": get_gemini_live_gender_setting(),
                "default_voice": GEMINI_LIVE_DEFAULT_VOICE,
                "female_voice": GEMINI_LIVE_FEMALE_VOICE,
                "runtime": runtime,
            }

        @app.post("/api/local/live-voice")
        async def local_live_voice_set(request: Request):
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)

            try:
                body = await request.json()
                enabled = bool(body.get("enabled", False))

                from voice.agent import set_live_voice_state

                result = set_live_voice_state(enabled)
                return {"ok": True, **result}
            except Exception as exc:
                print("[LIVE VOICE SETTINGS ERROR]", exc)
                return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)

        # * =====================================================
        # AI CHATBOT
        # * =====================================================

        @app.post(
            "/api/ai-chat/new"
        )
        async def ai_chat_new(
            request: Request,
        ):
            if not (
                self._authorize(request)
                or self._authorize_local(request)
            ):
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Unauthorized.",
                    },
                    status_code=401,
                )

            return create_chat()


        @app.get(
            "/api/ai-chat/chats"
        )
        async def ai_chat_list(
            request: Request,
        ):
            if not (
                self._authorize(request)
                or self._authorize_local(request)
            ):
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Unauthorized.",
                    },
                    status_code=401,
                )

            return list_chats()
        
        
        @app.get("/api/ai-chat/model")
        async def ai_chat_model(request: Request):
            if not (
                self._authorize(request)
                or self._authorize_local(request)
            ):
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Unauthorized.",
                    },
                    status_code=401,
                )

            return get_model()


        @app.post("/api/ai-chat/{session_id}/model")
        async def ai_chat_set_model(
            session_id: str,
            request: Request,
        ):
            if not (
                self._authorize(request)
                or self._authorize_local(request)
            ):
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Unauthorized.",
                    },
                    status_code=401,
                )

            try:
                body = await request.json()
            except Exception:
                body = {}

            model = str(
                body.get("model", "")
            ).strip()

            if not model:
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Model is required.",
                    },
                    status_code=400,
                )

            result = set_model(
                session_id=session_id,
                model=model,
            )

            if not result.get("success"):
                return JSONResponse(
                    result,
                    status_code=400,
                )

            return result


        @app.get(
            "/api/ai-chat/{session_id}"
        )
        async def ai_chat_get(
            session_id: str,
            request: Request,
        ):
            if not (
                self._authorize(request)
                or self._authorize_local(request)
            ):
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Unauthorized.",
                    },
                    status_code=401,
                )

            result = get_chat(
                session_id
            )

            if not result.get("success"):
                return JSONResponse(
                    result,
                    status_code=404,
                )

            return result
        
        
        @app.post(
            "/api/ai-chat/{session_id}/rename"
        )
        async def ai_chat_rename(
            session_id: str,
            request: Request,
        ):
            if not (
                self._authorize(request)
                or self._authorize_local(request)
            ):
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Unauthorized.",
                    },
                    status_code=401,
                )

            try:
                body = await request.json()

            except Exception:
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Invalid request.",
                    },
                    status_code=400,
                )

            title = str(
                body.get(
                    "title",
                    "",
                )
            ).strip()

            if not title:
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Chat name cannot be empty.",
                    },
                    status_code=400,
                )

            result = rename_chat(
                session_id=session_id,
                title=title,
            )

            if not result.get("success"):
                return JSONResponse(
                    result,
                    status_code=404,
                )

            return result


        @app.delete(
            "/api/ai-chat/{session_id}"
        )
        async def ai_chat_delete(
            session_id: str,
            request: Request,
        ):
            if not (
                self._authorize(request)
                or self._authorize_local(request)
            ):
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Unauthorized.",
                    },
                    status_code=401,
                )

            result = delete_chat(
                session_id
            )

            if not result.get("success"):
                return JSONResponse(
                    result,
                    status_code=404,
                )

            return result


        @app.post(
            "/api/ai-chat/message"
        )
        async def ai_chat_message(
            request: Request,
        ):
            if not (
                self._authorize(request)
                or self._authorize_local(request)
            ):
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Unauthorized.",
                    },
                    status_code=401,
                )

            try:
                body = await request.json()

            except Exception:
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Invalid request.",
                    },
                    status_code=400,
                )

            session_id = str(
                body.get(
                    "session_id",
                    "",
                )
            ).strip()

            message = str(
                body.get(
                    "message",
                    "",
                )
            ).strip()

            if not session_id:
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Session ID is required.",
                    },
                    status_code=400,
                )

            if not message:
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Message cannot be empty.",
                    },
                    status_code=400,
                )

            result = await asyncio.to_thread(
                send_message,
                session_id,
                message,
            )

            if not result.get("success"):
                return JSONResponse(
                    result,
                    status_code=400,
                )

            return result
        
        @app.post(
            "/api/ai-chat/clipboard"
        )
        async def ai_chat_clipboard(
            request: Request,
        ):
            if not (
                self._authorize(request)
                or self._authorize_local(request)
            ):
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Unauthorized.",
                    },
                    status_code=401,
                )

            try:
                body = await request.json()

            except Exception:
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Invalid request.",
                    },
                    status_code=400,
                )

            text = str(
                body.get(
                    "text",
                    "",
                )
            )

            if not text:
                return JSONResponse(
                    {
                        "success": False,
                        "error": "Clipboard text cannot be empty.",
                    },
                    status_code=400,
                )

            success = copy_text_to_system_clipboard(
                text
            )

            if not success:
                return JSONResponse(
                    {
                        "success": False,
                        "error": (
                            "Unable to copy text "
                            "to the Windows clipboard."
                        ),
                    },
                    status_code=500,
                )

            return {
                "success": True,
                "message": "Copied to system clipboard.",
            }

        # * =====================================================
        # * COMMAND
        # * =====================================================

        @app.post(
            "/api/command"
        )
        async def command(
            request: Request,
        ):

            self._loop = (
                asyncio.get_running_loop()
            )

            if not (
                self._authorize(request)
                or self._authorize_local(request)
            ):
                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            "Unauthorized."
                        ),
                    },
                    status_code=401,
                )

            try:

                body = (
                    await request.json()
                )

            except Exception:

                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            "Invalid request."
                        ),
                    },
                    status_code=400,
                )

            token = (
                self._get_token(
                    request
                )
            )

            encrypted = str(
                body.get(
                    "enc",
                    "",
                )
            ).strip()

            if encrypted:

                if not token:

                    return JSONResponse(
                        {
                            "ok": False,
                            "error": (
                                "Unauthorized."
                            ),
                        },
                        status_code=401,
                    )

                session_key = (
                    self._token_keys.get(
                        token
                    )
                )

                if not session_key:

                    return JSONResponse(
                        {
                            "ok": False,
                            "error": (
                                "Session expired."
                            ),
                        },
                        status_code=401,
                    )

                try:

                    text = (
                        _decrypt_cbc(
                            _derive_key(
                                session_key
                            ),
                            encrypted,
                        )
                        .strip()
                    )

                except Exception:

                    return JSONResponse(
                        {
                            "ok": False,
                            "error": (
                                "Decryption failed."
                            ),
                        },
                        status_code=400,
                    )

            else:

                text = str(
                    body.get(
                        "text",
                        body.get("command", ""),
                    )
                ).strip()

            if not text:

                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            "Command is empty."
                        ),
                    },
                    status_code=400,
                )

            threading.Thread(
                target=self._run_command,
                args=(text,),
                daemon=True,
                name=(
                    "JARVIS-RemoteCommand"
                ),
            ).start()

            return {
                "ok": True,
                "message": (
                    f"Command sent to {get_assistant_display_name()}."
                ),
            }

        # * =====================================================
        # * WAKE
        # * =====================================================

        @app.post(
            "/api/wake"
        )
        async def wake(
            request: Request,
        ):

            if not self._authorize(
                request
            ):

                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            "Unauthorized."
                        ),
                    },
                    status_code=401,
                )

            threading.Thread(
                target=self._run_command,
                args=(
                    f"hey {get_assistant_name_lower()}",
                ),
                daemon=True,
                name=(
                    "JARVIS-RemoteWake"
                ),
            ).start()

            return {
                "ok": True
            }
            
        @app.post("/api/live/text")
        async def live_text_endpoint(request: Request):
            """Send typed text to the already-running Gemini Live session."""
            if not self._authorize_local(request):
                return JSONResponse({"ok": False, "error": "Local access required."}, status_code=403)

            try:
                body = await request.json()
            except Exception:
                return JSONResponse({"ok": False, "error": "Invalid request."}, status_code=400)

            text = str(body.get("text", "")).strip()
            if not text:
                return JSONResponse({"ok": False, "error": "Text is required."}, status_code=400)

            try:
                from voice.agent import agent_state, send_agent_text

                if not agent_state()["connected"]:
                    return JSONResponse(
                        {"ok": False, "error": "Gemini Live is unavailable. Request not executed."},
                        status_code=503,
                    )
                if not send_agent_text(text):
                    return JSONResponse(
                        {"ok": False, "error": "Gemini Live is unavailable. Request not executed."},
                        status_code=503,
                    )
                return {"ok": True, "status": "accepted", "controller": "gemini-live"}
            except Exception:
                return JSONResponse(
                    {"ok": False, "error": "Gemini Live is unavailable. Request not executed."},
                    status_code=503,
                )

        # * =====================================================
        # * DIRECT AGENT STATUS
        # * =====================================================

        @app.get(
            "/api/agent/status"
        )
        async def agent_status_endpoint(
            request: Request,
        ):

            if not self._authorize_local(
                request
            ):

                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            "Unauthorized."
                        ),
                    },
                    status_code=401,
                )

            try:

                from voice.agent import agent_state

                state = agent_state()

                return {
                    "ok": True,
                    "running": state["running"],
                    "connected": state["connected"],
                    "state": state["state"],
                    "controller": state["controller"],
                }

            except Exception as exc:

                return JSONResponse(
                    {
                        "ok": False,
                        "error": str(exc),
                    },
                    status_code=500,
                )

        # * =====================================================
        # * DIRECT AGENT START
        # * =====================================================

        @app.post(
            "/api/agent/start"
        )
        async def agent_start_endpoint(
            request: Request,
        ):

            if not self._authorize_local(
                request
            ):

                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            "Unauthorized."
                        ),
                    },
                    status_code=401,
                )

            return JSONResponse(
                {
                    "ok": False,
                    "error": "Gemini Live starts automatically with JARVIS; it is not user-toggleable.",
                },
                status_code=409,
            )

            try:

                from voice.agent import (
                    start_agent,
                )

                result = (
                    start_agent()
                )

                await self.broadcast({
                    "type": "sys",
                    "text": (
                        "Agent "
                        "start requested."
                    ),
                })

                return {
                    "ok": True,
                    "result": str(
                        result
                    ),
                }

            except Exception as exc:

                return JSONResponse(
                    {
                        "ok": False,
                        "error": str(
                            exc
                        ),
                    },
                    status_code=500,
                )

        # * =====================================================
        # * DIRECT AGENT STOP
        # * =====================================================

        @app.post(
            "/api/agent/stop"
        )
        async def agent_stop_endpoint(
            request: Request,
        ):

            if not self._authorize_local(
                request
            ):

                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            "Unauthorized."
                        ),
                    },
                    status_code=401,
                )

            if not self.agent_stop_handler:

                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            "Live stop handler "
                            "is not connected."
                        ),
                    },
                    status_code=503,
                )

            try:

                result = (
                    self.agent_stop_handler()
                )

                await self.broadcast({
                    "type": "sys",
                    "text": (
                        "Agent "
                        "stop requested."
                    ),
                })

                return {
                    "ok": True,
                    "result": str(
                        result
                    ),
                }

            except Exception as exc:

                return JSONResponse(
                    {
                        "ok": False,
                        "error": str(
                            exc
                        ),
                    },
                    status_code=500,
                )

        # * =====================================================
        # * FILE UPLOAD
        # * =====================================================

        if (
            MULTIPART_AVAILABLE
            and UploadFile is not None
        ):

            @app.post(
                "/api/upload"
            )
            async def upload(
                request: Request,
                file: UploadFile = File(...),
            ):

                if not self._authorize(
                    request
                ):

                    return JSONResponse(
                        {
                            "ok": False,
                            "error": (
                                "Unauthorized."
                            ),
                        },
                        status_code=401,
                    )

                original_name = (
                    file.filename
                    or "upload"
                )

                safe_name = (
                    Path(
                        original_name
                    ).name
                )

                if not safe_name:

                    safe_name = "upload"

                target = (
                    self._unique_upload_path(
                        safe_name
                    )
                )

                total = 0

                limit = (
                    MAX_UPLOAD_MB
                    * 1024
                    * 1024
                )

                try:

                    with target.open(
                        "wb"
                    ) as output:

                        while True:

                            chunk = (
                                await file.read(
                                    1024 * 1024
                                )
                            )

                            if not chunk:

                                break

                            total += len(
                                chunk
                            )

                            if total > limit:

                                output.close()

                                target.unlink(
                                    missing_ok=True
                                )

                                return JSONResponse(
                                    {
                                        "ok": False,
                                        "error": (
                                            "File exceeds "
                                            f"{MAX_UPLOAD_MB} MB."
                                        ),
                                    },
                                    status_code=413,
                                )

                            output.write(
                                chunk
                            )

                finally:

                    await file.close()

                print(
                    "[REMOTE] File received:",
                    target,
                )

                intelligence_record = None
                intelligence_error = ""
                try:
                    intelligence_record = intelligence_save_uploaded_file(
                        original_name,
                        target.read_bytes(),
                        mime_type=file.content_type or "",
                    )
                except Exception as exc:
                    intelligence_error = str(exc)

                event = {
                    "type": "file_received",
                    "name": target.name,
                    "size": total,
                }
                if intelligence_record:
                    event["file"] = intelligence_record
                    event["file_id"] = intelligence_record.get("id", "")
                    event["processing_status"] = intelligence_record.get(
                        "processing_status", ""
                    )
                if intelligence_error:
                    event["file_intelligence_error"] = intelligence_error
                await self.broadcast(event)

                if intelligence_error:
                    return JSONResponse(
                        {
                            "ok": False,
                            "name": target.name,
                            "size": total,
                            "file_intelligence": {
                                "ok": False,
                                "error": intelligence_error,
                            },
                            "error": (
                                "Raw upload succeeded, but File Intelligence "
                                f"ingestion failed: {intelligence_error}"
                            ),
                        },
                        status_code=500,
                    )

                response = {
                    "ok": True,
                    "name": target.name,
                    "size": total,
                    "file": intelligence_record,
                    "file_id": intelligence_record.get("id", ""),
                }

                if intelligence_record.get("processing_status") != "READY":
                    response["ok"] = False
                    response["error"] = (
                        intelligence_record.get("error")
                        or "File Intelligence processing failed."
                    )
                    response["file_intelligence"] = {
                        "ok": False,
                        "processing_status": intelligence_record.get(
                            "processing_status", ""
                        ),
                    }
                    return JSONResponse(response, status_code=422)

                return response

        # * =====================================================
        # * FILE DOWNLOAD
        # * =====================================================

        @app.get(
            "/uploads/{filename}"
        )
        async def download(
            filename: str,
            token: str = "",
        ):

            if token not in self._tokens:

                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            "Unauthorized."
                        ),
                    },
                    status_code=401,
                )

            safe_name = (
                Path(
                    filename
                ).name
            )

            path = (
                UPLOADS_DIR
                / safe_name
            )

            if not path.is_file():

                return JSONResponse(
                    {
                        "ok": False,
                        "error": (
                            "File not found."
                        ),
                    },
                    status_code=404,
                )

            return FileResponse(
                str(path),
                filename=safe_name,
            )

        # * =====================================================
        # * DASHBOARD WEBSOCKET
        # * =====================================================

        @app.websocket(
            "/ws"
        )
        async def websocket(
            websocket: WebSocket,
            token: str = "",
        ):

            self._loop = (
                asyncio.get_running_loop()
            )

            if token not in self._tokens:

                await websocket.close(
                    code=4001
                )

                return

            await websocket.accept()

            self._clients.add(
                websocket
            )

            try:

                for message in (
                    self._history[-100:]
                ):

                    await websocket.send_json(
                        message
                    )

                await websocket.send_json({
                    "type": "status",
                    "state": "active",
                })

                await websocket.send_json({
                    "type": "sys",
                    "text": (
                        "Remote session active."
                    ),
                    "event_id": uuid4().hex,
                    "timestamp": time.time(),
                    "source": "remote_control",
                })

                while True:

                    await websocket.receive_text()

            except WebSocketDisconnect:

                pass

            except Exception as exc:

                print(
                    "[REMOTE WS ERROR]",
                    exc,
                )

            finally:

                self._clients.discard(
                    websocket
                )

        # * =====================================================
        # * PHONE AUDIO
        # * =====================================================

        @app.websocket(
            "/ws/phone-audio"
        )
        async def phone_audio(
            websocket: WebSocket,
            token: str = "",
        ):

            self._loop = (
                asyncio.get_running_loop()
            )

            if token not in self._tokens:

                await websocket.close(
                    code=4001
                )

                return

            await websocket.accept()

            await self.broadcast({
                "type": "sys",
                "text": (
                    "Phone microphone live."
                ),
            })

            try:

                while True:

                    data = (
                        await websocket.receive_bytes()
                    )

                    try:

                        self._phone_audio_queue.put_nowait(
                            data
                        )

                    except asyncio.QueueFull:

                        try:

                            self._phone_audio_queue.get_nowait()

                        except asyncio.QueueEmpty:

                            pass

                        try:

                            self._phone_audio_queue.put_nowait(
                                data
                            )

                        except asyncio.QueueFull:

                            pass

            except WebSocketDisconnect:

                pass

            finally:

                await self.broadcast({
                    "type": "sys",
                    "text": (
                        "Phone microphone stopped."
                    ),
                })

        return app

    # * =========================================================
    # * UNIQUE UPLOAD PATH
    # * =========================================================

    @staticmethod
    def _unique_upload_path(
        filename: str,
    ) -> Path:

        base = Path(
            filename
        )

        stem = base.stem

        suffix = base.suffix

        candidate = (
            UPLOADS_DIR
            / filename
        )

        counter = 1

        while candidate.exists():

            candidate = (
                UPLOADS_DIR
                / (
                    f"{stem}_"
                    f"{counter}"
                    f"{suffix}"
                )
            )

            counter += 1

        return candidate

    # * =========================================================
    # * PHONE AUDIO QUEUE
    # * =========================================================

    def phone_audio_queue(self):

        return (
            self._phone_audio_queue
        )

    # * =========================================================
    # * START
    # * =========================================================

    def start(self) -> bool:

        if not FASTAPI_AVAILABLE:

            print(
                "[REMOTE] Disabled."
            )

            print(
                "[REMOTE] Install:"
            )

            print(
                "pip install fastapi "
                '"uvicorn[standard]" '
                "cryptography"
            )

            return False

        if (
            self._thread
            and self._thread.is_alive()
        ):

            return True

        def run_server():

            try:

                uvicorn.run(
                    self.app,
                    host="0.0.0.0",
                    port=self.port,
                    log_level="warning",
                )

            except Exception as exc:

                print(
                    "[REMOTE] Server stopped:",
                    exc,
                )

        self._thread = (
            threading.Thread(
                target=run_server,
                daemon=True,
                name=(
                    "JARVIS-DashboardServer"
                ),
            )
        )

        self._thread.start()

        print(
            "[REMOTE] Dashboard Server:"
        )

        print(
            f"[REMOTE] {self.url()}"
        )

        return True

    # * =========================================================
    # * STOP
    # * =========================================================

    def stop(self):

        self._unsubscribe_hud_events()

        self._tokens.clear()

        self._token_keys.clear()

        self._device_sessions.clear()

        self._pin = None

        self._pin_expiry = 0.0

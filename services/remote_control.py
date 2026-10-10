"""
=============================================================
JARVIS PRO - Remote Control Service
=============================================================

Mark-L-main remote/dashboard idea adapted as an optional
JARVIS PRO service.

The service:

- creates a short-lived pairing PIN
- serves a phone-friendly command page
- accepts text commands
- sends commands into the existing JARVIS dispatcher
- provides useful diagnostics when authentication fails
- can stop Agent directly
- does NOT replace the existing JARVIS brain/dispatcher

Remote Control is intentionally a thin interface over the
existing JARVIS system.
"""

from __future__ import annotations

import secrets
import socket
import threading
import time

from typing import Callable, Optional

from config.settings import (
    get_assistant_display_name,
    get_assistant_name_lower,
)


# * ==========================================================
# * Optional FastAPI / Uvicorn
# * ==========================================================

try:

    from fastapi import (
        FastAPI,
        Request,
    )

    from fastapi.responses import (
        HTMLResponse,
        JSONResponse,
    )

    import uvicorn

    FASTAPI_AVAILABLE = True

except ImportError:

    FastAPI = None
    Request = None
    HTMLResponse = None
    JSONResponse = None
    uvicorn = None

    FASTAPI_AVAILABLE = False


# * ==========================================================
# * Configuration
# * ==========================================================

PORT = 8765

_PIN_CHARS = (
    "ABCDEFGHJKMNPQRSTUVWXYZ"
    "23456789"
)

PIN_EXPIRY_SECONDS = 600


# * ==========================================================
# * Local IP
# * ==========================================================

def _local_ip() -> str:
    """
    Best-effort LAN IP detection.

    The UDP socket is only used by Windows to select the
    appropriate local network interface.

    No application data is sent to the internet.
    """

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM,
    )

    try:

        sock.connect(
            ("8.8.8.8", 80)
        )

        return sock.getsockname()[0]

    except Exception:

        return "127.0.0.1"

    finally:

        sock.close()


# * ==========================================================
# * Remote Control Server
# * ==========================================================

class RemoteControlServer:

    def __init__(
        self,
        command_handler: Optional[
            Callable[[str], object]
        ] = None,
        agent_stop_handler: Optional[
            Callable[[], object]
        ] = None,
        port: int = PORT,
    ):

        # * Existing JARVIS dispatcher.
        self.command_handler = (
            command_handler
        )

        # * Direct Agent stop action.
        #
        # ! This is important because the normal JARVIS
        # * microphone is paused while Agent
        # * owns the microphone.
        self.agent_stop_handler = (
            agent_stop_handler
        )

        self.port = int(port)

        self.ip = _local_ip()

        self._pin: Optional[str] = None

        self._pin_expiry = 0.0

        self._token: Optional[str] = None

        self._thread = None

        self.app = (
            self._build_app()
            if FASTAPI_AVAILABLE
            else None
        )

    # * ======================================================
    # * Pairing
    # * ======================================================

    def new_pairing_pin(
        self,
        expiry_seconds: int = PIN_EXPIRY_SECONDS,
    ) -> str:
        """
        Generate a new temporary pairing PIN.
        """

        self._pin = "".join(
            secrets.choice(
                _PIN_CHARS
            )
            for _ in range(6)
        )

        self._pin_expiry = (
            time.time()
            + int(expiry_seconds)
        )

        # * Invalidate old phone sessions.

        self._token = None

        print(
            "[REMOTE] New pairing PIN generated."
        )

        return self._pin

    # * ======================================================
    # * PIN status
    # * ======================================================

    def _pin_is_valid(
        self,
        pin: str,
    ) -> bool:

        if not self._pin:

            return False

        if time.time() > self._pin_expiry:

            return False

        return secrets.compare_digest(
            pin,
            self._pin,
        )

    # * ======================================================
    # * URL
    # * ======================================================

    def url(self) -> str:

        return (
            f"http://"
            f"{self.ip}:"
            f"{self.port}"
        )

    def pairing_url(self) -> str:

        pin = self._pin or ""

        return (
            f"{self.url()}"
            f"/?pin={pin}"
        )

    # * ======================================================
    # * Authorization
    # * ======================================================

    def _authorize(
        self,
        request: "Request",
    ) -> bool:

        authorization = request.headers.get(
            "authorization",
            "",
        )

        if not authorization:

            return False

        if not authorization.lower().startswith(
            "bearer "
        ):

            return False

        token = authorization[
            7:
        ].strip()

        if not token:

            return False

        if not self._token:

            return False

        return secrets.compare_digest(
            token,
            self._token,
        )

    # * ======================================================
    # * FastAPI
    # * ======================================================

    def _build_app(self):

        app = FastAPI(
            docs_url=None,
            redoc_url=None,
        )

        # * ==================================================
        # * Main page
        # * ==================================================

        @app.get(
            "/",
            response_class=HTMLResponse,
        )
        async def index():

            return HTMLResponse(
                _PAGE
                .replace("__ASSISTANT_NAME__", get_assistant_display_name())
                .replace("__ASSISTANT_NAME_LOWER__", get_assistant_name_lower())
            )

        # * ==================================================
        # * Login
        # * ==================================================

        @app.post(
            "/api/login"
        )
        async def login(
            request: "Request",
        ):

            client_ip = (
                request.client.host
                if request.client
                else "unknown"
            )

            try:

                body = await request.json()

            except Exception as exc:

                print(
                    "[REMOTE LOGIN] "
                    f"Invalid JSON from "
                    f"{client_ip}: "
                    f"{exc}"
                )

                return JSONResponse(
                    {
                        "ok": False,
                        "error":
                            "Invalid login request.",
                    },
                    status_code=400,
                )

            pin = str(
                body.get(
                    "pin",
                    "",
                )
            ).strip().upper()

            print(
                "[REMOTE LOGIN] "
                f"Request from "
                f"{client_ip}"
            )

            print(
                "[REMOTE LOGIN] "
                f"PIN received: "
                f"{pin if pin else '(empty)'}"
            )

            # * ----------------------------------------------
            # * No active PIN
            # * ----------------------------------------------

            if not self._pin:

                print(
                    "[REMOTE LOGIN] "
                    "REJECTED: no active PIN."
                )

                return JSONResponse(
                    {
                        "ok": False,
                        "error":
                            "No active pairing PIN. "
                            f"Restart {get_assistant_display_name()}.",
                    },
                    status_code=401,
                )

            # * ----------------------------------------------
            # * Expired PIN
            # * ----------------------------------------------

            if (
                time.time()
                > self._pin_expiry
            ):

                print(
                    "[REMOTE LOGIN] "
                    "REJECTED: PIN expired."
                )

                return JSONResponse(
                    {
                        "ok": False,
                        "error":
                            "PIN expired. "
                            "Restart or generate "
                            "a new pairing PIN.",
                    },
                    status_code=401,
                )

            # * ----------------------------------------------
            # * PIN mismatch
            # * ----------------------------------------------

            if not secrets.compare_digest(
                pin,
                self._pin,
            ):

                print(
                    "[REMOTE LOGIN] "
                    "REJECTED: PIN mismatch."
                )

                return JSONResponse(
                    {
                        "ok": False,
                        "error":
                            "Incorrect pairing PIN.",
                    },
                    status_code=401,
                )

            # * ----------------------------------------------
            # * Successful authentication
            # * ----------------------------------------------

            self._token = (
                secrets.token_urlsafe(
                    32
                )
            )

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
                f"PIN remaining: "
                f"{remaining}s"
            )

            return {
                "ok": True,
                "token": self._token,
                "message":
                    f"Connected to {get_assistant_display_name()}.",
            }

        # * ==================================================
        # * Normal JARVIS Command
        # * ==================================================

        @app.post(
            "/api/command"
        )
        async def command(
            request: "Request",
        ):

            client_ip = (
                request.client.host
                if request.client
                else "unknown"
            )

            if not self._authorize(
                request
            ):

                print(
                    "[REMOTE COMMAND] "
                    f"Unauthorized request "
                    f"from {client_ip}"
                )

                return JSONResponse(
                    {
                        "ok": False,
                        "error":
                            "Unauthorized. "
                            "Connect with the "
                            "pairing PIN first.",
                    },
                    status_code=401,
                )

            try:

                body = await request.json()

            except Exception as exc:

                print(
                    "[REMOTE COMMAND] "
                    f"Invalid JSON: {exc}"
                )

                return JSONResponse(
                    {
                        "ok": False,
                        "error":
                            "Invalid command request.",
                    },
                    status_code=400,
                )

            text = str(
                body.get(
                    "text",
                    "",
                )
            ).strip()

            if not text:

                return JSONResponse(
                    {
                        "ok": False,
                        "error":
                            "Command is empty.",
                    },
                    status_code=400,
                )

            print(
                "[REMOTE COMMAND] "
                f"Received: {text}"
            )

            # * ----------------------------------------------
            # * Existing JARVIS dispatcher
            # * ----------------------------------------------

            if self.command_handler:

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
                    "message":
                        f"Command sent to {get_assistant_display_name()}.",
                }

            print(
                "[REMOTE COMMAND] "
                "ERROR: command handler "
                "is not configured."
            )

            return JSONResponse(
                {
                    "ok": False,
                    "error":
                        f"{get_assistant_display_name()} command handler "
                        "is not connected.",
                },
                status_code=503,
            )

        # * ==================================================
        # * DIRECT AGENT STOP
        # * ==================================================

        @app.post(
            "/api/agent/stop"
        )
        async def agent_stop_endpoint(
            request: "Request",
        ):

            client_ip = (
                request.client.host
                if request.client
                else "unknown"
            )

            # * ----------------------------------------------
            # * Authentication
            # * ----------------------------------------------

            if not self._authorize(
                request
            ):

                print(
                    "[REMOTE LIVE] "
                    "Unauthorized stop request "
                    f"from {client_ip}"
                )

                return JSONResponse(
                    {
                        "ok": False,
                        "error":
                            "Unauthorized. "
                            "Connect with the "
                            "pairing PIN first.",
                    },
                    status_code=401,
                )

            # * ----------------------------------------------
            # * Handler availability
            # * ----------------------------------------------

            if not self.agent_stop_handler:

                print(
                    "[REMOTE LIVE] "
                    "ERROR: Live stop handler "
                    "is not connected."
                )

                return JSONResponse(
                    {
                        "ok": False,
                        "error":
                            "Agent stop "
                            "handler is not connected.",
                    },
                    status_code=503,
                )

            # * ----------------------------------------------
            # * Stop Agent
            # * ----------------------------------------------

            try:

                print(
                    "[REMOTE LIVE] "
                    "Stop requested from "
                    f"{client_ip}"
                )

                result = (
                    self.agent_stop_handler()
                )

                print(
                    "[REMOTE LIVE] "
                    "Agent stop "
                    "requested successfully."
                )

                return {
                    "ok": True,
                    "message":
                        "Agent stopped.",
                    "result":
                        str(result),
                }

            except Exception as exc:

                print(
                    "[REMOTE LIVE] "
                    f"Stop error: {exc}"
                )

                return JSONResponse(
                    {
                        "ok": False,
                        "error":
                            "Unable to stop "
                            "Agent: "
                            f"{exc}",
                    },
                    status_code=500,
                )

        # * ==================================================
        # * Server Information
        # * ==================================================

        @app.get(
            "/api/info"
        )
        async def info():

            return {
                "ok": True,

                "url":
                    self.url(),

                "pairing_active":
                    (
                        self._pin is not None
                        and
                        time.time()
                        < self._pin_expiry
                    ),

                "authenticated":
                    (
                        self._token is not None
                    ),

                "agent_stop_available":
                    (
                        self.agent_stop_handler
                        is not None
                    ),

                "server":
                    f"{get_assistant_display_name()} Remote Control",
            }

        return app

    # * ======================================================
    # * Command Worker
    # * ======================================================

    def _run_command(
        self,
        text: str,
    ):

        try:

            result = (
                self.command_handler(
                    text
                )
            )

            print(
                "[REMOTE COMMAND] "
                "Dispatcher completed."
            )

            if result is not None:

                print(
                    "[REMOTE COMMAND RESULT]",
                    result,
                )

        except Exception as exc:

            print(
                "[REMOTE COMMAND] "
                f"Dispatcher error: {exc}"
            )

    # * ======================================================
    # * Start
    # * ======================================================

    def start(self):

        if not FASTAPI_AVAILABLE:

            print(
                "[REMOTE] Disabled."
            )

            print(
                "[REMOTE] Install:"
            )

            print(
                "pip install fastapi uvicorn"
            )

            return False

        if (
            self._thread
            and self._thread.is_alive()
        ):

            print(
                "[REMOTE] Server already running."
            )

            return True

        def _run():

            try:

                uvicorn.run(
                    self.app,
                    host="0.0.0.0",
                    port=self.port,
                    log_level="info",
                )

            except Exception as exc:

                print(
                    "[REMOTE] "
                    f"Server stopped: {exc}"
                )

        self._thread = (
            threading.Thread(
                target=_run,
                daemon=True,
                name=(
                    "JARVIS-RemoteServer"
                ),
            )
        )

        self._thread.start()

        print(
            "[REMOTE] Server:"
        )

        print(
            f"[REMOTE] {self.url()}"
        )

        return True

    # * ======================================================
    # * Stop
    # * ======================================================

    def stop(self):

        self._token = None

        self._pin = None

        self._pin_expiry = 0.0

        print(
            "[REMOTE] Authentication "
            "session cleared."
        )


# * ==========================================================
# * Mobile Web Interface
# * ==========================================================

_PAGE = r"""
<!doctype html>

<html>

<head>

<meta
    name="viewport"
    content=
        "width=device-width,
         initial-scale=1"
>

<meta
    name="theme-color"
    content="#07090f"
>

<title>
    __ASSISTANT_NAME__ Remote
</title>

<style>

* {
    box-sizing: border-box;
}

body {

    font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    background:
        # * 07090f;

    color:
        # * e6edf7;

    max-width:
        620px;

    margin:
        0 auto;

    padding:
        30px 20px;
}

h1 {

    margin-bottom:
        8px;
}

p {

    opacity:
        0.75;
}

input,
button {

    width:
        100%;

    font-size:
        18px;

    padding:
        13px;

    border-radius:
        10px;

    border:
        1px solid  # * 394255;

    margin-top:
        10px;
}

input {

    background:
        # * 111827;

    color:
        white;

    outline:
        none;
}

button {

    background:
        # * 1d4ed8;

    color:
        white;

    cursor:
        pointer;
}

button:active {

    transform:
        scale(0.98);
}

.agent-button {

    background:
        # * b91c1c;
}

.agent-button:hover {

    background:
        # * dc2626;
}

# * status {

    margin:
        15px 0;

    padding:
        12px;

    border-radius:
        10px;

    background:
        # * 111827;

    word-break:
        break-word;
}

# * controls {

    display:
        none;
}

.command-row {

    margin-top:
        15px;
}

.small {

    font-size:
        14px;

    opacity:
        0.6;
}

.section {

    margin-top:
        22px;

    padding-top:
        10px;

    border-top:
        1px solid  # * 252b38;
}

</style>

</head>


<body>

<h1>
    __ASSISTANT_NAME__ Remote
</h1>

<p>
    Connect your phone to your local __ASSISTANT_NAME__.
</p>


<div id="status">

    Enter the pairing PIN shown
    in the __ASSISTANT_NAME__ terminal.

</div>


<input
    id="pin"
    maxlength="6"
    autocomplete="one-time-code"
    autocapitalize="characters"
    placeholder="6-character PIN"
>


<button
    onclick="login()"
>
    Connect
</button>


<div
    id="controls"
>

    <!-- ================================================
         NORMAL COMMANDS
         ================================================ -->

    <div class="command-row">

        <input
            id="cmd"
            autocomplete="off"
            placeholder=
                "Tell __ASSISTANT_NAME__ what to do"
        >

        <button
            onclick="sendCommand()"
        >
            Send Command
        </button>

    </div>


    <button
        onclick="wake()"
    >
        Wake __ASSISTANT_NAME__
    </button>


    <!-- ================================================
         AGENT
         ================================================ -->

    <div class="section">

        <p>
            Agent
        </p>

        <button
            class="agent-button"
            onclick="stopAgent()"
        >
            Stop Agent
        </button>

    </div>


    <p class="small">

        Normal commands are sent directly into
        your existing __ASSISTANT_NAME__ dispatcher.

        The Agent stop button directly
        controls the Gemini Live session because
        the normal __ASSISTANT_NAME__ microphone is paused
        while Agent is active.

    </p>

</div>


<script>

let token = "";


/* ========================================================
   Helpers
   ======================================================== */

function setStatus(message) {

    document
        .getElementById("status")
        .textContent = message;
}


async function readResponse(response) {

    const raw =
        await response.text();

    console.log(
        "[__ASSISTANT_NAME__ REMOTE RESPONSE]",
        response.status,
        raw
    );

    let data;

    try {

        data =
            JSON.parse(raw);

    }

    catch {

        data = {

            ok: false,

            error:
                raw ||
                (
                    "HTTP " +
                    response.status
                )
        };
    }

    return data;
}


/* ========================================================
   Login
   ======================================================== */

async function login() {

    const pin =
        document
            .getElementById("pin")
            .value
            .trim()
            .toUpperCase();


    if (!pin) {

        setStatus(
            "Please enter the pairing PIN."
        );

        return;
    }


    setStatus(
        "Connecting to __ASSISTANT_NAME__..."
    );


    try {

        const response =
            await fetch(
                "/api/login",
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            pin: pin
                        })
                }
            );


        const data =
            await readResponse(
                response
            );


        if (
            !response.ok
            ||
            !data.ok
        ) {

            setStatus(
                "Login failed: " +
                (
                    data.error
                    ||
                    (
                        "HTTP " +
                        response.status
                    )
                )
            );

            return;
        }


        token =
            data.token;


        document
            .getElementById(
                "controls"
            )
            .style.display =
                "block";


        setStatus(
            "Connected to __ASSISTANT_NAME__."
        );


        console.log(
            "[__ASSISTANT_NAME__ REMOTE] "
            + "Authentication successful."
        );

    }

    catch (error) {

        console.error(
            "[__ASSISTANT_NAME__ REMOTE LOGIN ERROR]",
            error
        );

        setStatus(
            "Connection error: " +
            error.message
        );
    }
}


/* ========================================================
   Send Command
   ======================================================== */

async function sendCommand() {

    const input =
        document.getElementById(
            "cmd"
        );


    const text =
        input.value.trim();


    if (!text) {

        return;
    }


    if (!token) {

        setStatus(
            "Please connect to __ASSISTANT_NAME__ first."
        );

        return;
    }


    try {

        const response =
            await fetch(
                "/api/command",
                {
                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Authorization":
                            "Bearer " +
                            token
                    },

                    body:
                        JSON.stringify({
                            text: text
                        })
                }
            );


        const data =
            await readResponse(
                response
            );


        if (
            !response.ok
            ||
            !data.ok
        ) {

            setStatus(
                "Command failed: " +
                (
                    data.error
                    ||
                    (
                        "HTTP " +
                        response.status
                    )
                )
            );

            return;
        }


        input.value = "";


        setStatus(
        "Command sent to __ASSISTANT_NAME__."
        );

    }

    catch (error) {

        console.error(
            "[__ASSISTANT_NAME__ REMOTE COMMAND ERROR]",
            error
        );

        setStatus(
            "Command error: " +
            error.message
        );
    }
}


/* ========================================================
   Wake
   ======================================================== */

async function wake() {

    await sendCommandText(
        "hey __ASSISTANT_NAME_LOWER__"
    );
}


/* ========================================================
   Send arbitrary command
   ======================================================== */

async function sendCommandText(
    text
) {

    if (!token) {

        setStatus(
            "Please connect to __ASSISTANT_NAME__ first."
        );

        return;
    }


    try {

        const response =
            await fetch(
                "/api/command",
                {
                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Authorization":
                            "Bearer " +
                            token
                    },

                    body:
                        JSON.stringify({
                            text: text
                        })
                }
            );


        const data =
            await readResponse(
                response
            );


        if (
            !response.ok
            ||
            !data.ok
        ) {

            setStatus(
                "Command failed: " +
                (
                    data.error
                    ||
                    (
                        "HTTP " +
                        response.status
                    )
                )
            );

            return;
        }


        setStatus(
            "Wake command sent."
        );

    }

    catch (error) {

        console.error(
            "[__ASSISTANT_NAME__ REMOTE WAKE ERROR]",
            error
        );

        setStatus(
            "Wake error: " +
            error.message
        );
    }
}


/* ========================================================
   STOP AGENT
   ======================================================== */

async function stopAgent() {

    if (!token) {

        setStatus(
            "Please connect to __ASSISTANT_NAME__ first."
        );

        return;
    }


    setStatus(
        "Stopping Agent..."
    );


    try {

        const response =
            await fetch(
                "/api/agent/stop",
                {
                    method:
                        "POST",

                    headers: {

                        "Authorization":
                            "Bearer " +
                            token
                    }
                }
            );


        const data =
            await readResponse(
                response
            );


        if (
            !response.ok
            ||
            !data.ok
        ) {

            setStatus(
                "Live stop failed: " +
                (
                    data.error
                    ||
                    (
                        "HTTP " +
                        response.status
                    )
                )
            );

            return;
        }


        setStatus(
            "Agent stopped. "
            +
            "Normal __ASSISTANT_NAME__ voice resumed."
        );


        console.log(
            "[__ASSISTANT_NAME__ REMOTE] "
            + "Agent stopped."
        );

    }

    catch (error) {

        console.error(
            "[__ASSISTANT_NAME__ REMOTE LIVE STOP ERROR]",
            error
        );

        setStatus(
            "Live stop error: " +
            error.message
        );
    }
}


/* ========================================================
   Enter key support
   ======================================================== */

document
    .getElementById("pin")
    .addEventListener(
        "keydown",
        function(event) {

            if (
                event.key === "Enter"
            ) {

                login();
            }
        }
    );


document
    .getElementById("cmd")
    .addEventListener(
        "keydown",
        function(event) {

            if (
                event.key === "Enter"
            ) {

                sendCommand();
            }
        }
    );

</script>

</body>

</html>
"""

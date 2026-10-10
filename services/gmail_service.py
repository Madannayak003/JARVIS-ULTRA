"""
JARVIS PRO
Gmail Service

Responsibilities:
- Authenticate with Gmail using Google OAuth
- Store and refresh the OAuth token
- Send emails through the Gmail API
"""

import os
import base64
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# * =========================================================
# * Configuration
# * =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

CREDENTIALS_FILE = os.path.join(
    BASE_DIR,
    "credentials.json"
)

TOKEN_FILE = os.path.join(
    BASE_DIR,
    "token.json"
)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]


# * =========================================================
# * Authentication
# * =========================================================

def _get_credentials():
    """
    Load existing Gmail credentials or start OAuth flow.
    """

    credentials = None

    if os.path.exists(TOKEN_FILE):

        credentials = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    if credentials and credentials.valid:
        return credentials

    if (
        credentials
        and credentials.expired
        and credentials.refresh_token
    ):

        credentials.refresh(Request())

    else:

        if not os.path.exists(CREDENTIALS_FILE):

            raise FileNotFoundError(
                "credentials.json was not found."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            SCOPES
        )

        credentials = flow.run_local_server(
            port=0
        )

    with open(TOKEN_FILE, "w") as token:

        token.write(
            credentials.to_json()
        )

    return credentials


# * =========================================================
# * Gmail Service
# * =========================================================

def _get_gmail_service():
    """
    Create and return the Gmail API service.
    """

    credentials = _get_credentials()

    return build(
        "gmail",
        "v1",
        credentials=credentials
    )


# * =========================================================
# * Send Email
# * =========================================================

def send_email(
    recipient,
    subject,
    body
):
    """
    Send an email through Gmail.

    Returns:
        True  -> email sent successfully
        False -> failed
    """

    recipient = str(
        recipient or ""
    ).strip()

    subject = str(
        subject or ""
    ).strip()

    body = str(
        body or ""
    ).strip()

    if not recipient:
        raise ValueError(
            "Recipient email address is required."
        )

    if not subject:
        raise ValueError(
            "Email subject is required."
        )

    if not body:
        raise ValueError(
            "Email body is required."
        )

    service = _get_gmail_service()

    message = MIMEText(body)

    message["to"] = recipient
    message["subject"] = subject

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    request_body = {
        "raw": encoded_message
    }

    service.users().messages().send(
        userId="me",
        body=request_body
    ).execute()

    print(
        f"[GMAIL] Email sent to: {recipient}"
    )

    return True
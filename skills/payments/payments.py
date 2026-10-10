"""User-driven payment-app launch flow.

This skill only launches the selected/default payment application (or the
Android UPI app chooser). QR capture, recipient details, PIN/OTP/CVV input,
and final authorization remain entirely inside the official phone app.
"""

from __future__ import annotations

import os

from core.registry import register
from services.android import get_android_manager
from services.android.android_intents import ACTION_VIEW
from services.android.models import IntentSpec


def _say(message: str) -> None:
    print(f"[PAYMENT] {message}")
    try:
        from voice.manager import speak
        speak(message)
    except Exception:
        pass


def _configured_payment_app() -> str:
    return os.getenv("ANDROID_DEFAULT_PAYMENT_APP", "").strip()


def make_payment(data=None):
    """Open a payment app and hand every financial step to the user."""
    data = data or {}
    app_name = str(data.get("payment_app", "")).strip() or _configured_payment_app()
    manager = get_android_manager()

    if app_name:
        result = manager.open_app(app_name)
        if not result.success:
            if result.error_code == "not_installed":
                _say(f"{app_name} is not available on the connected Android device.")
            elif result.detail:
                _say(f"I could not open {app_name}: {result.detail}")
            else:
                _say(f"I could not open {app_name}.")
            return False
        # * The audited PhonePe and Google Pay packages expose normal launcher
        # * activities and UPI handlers, but no documented scanner-specific
        # ! launcher. Do not infer a scanner action from internal activity names.
        _say("Payment app opened. Please open its QR scanner.")
        return True

    # * Generic UPI VIEW delegates app selection to Android's normal resolver.
    # * It carries no recipient, amount, or payment credentials.
    chooser_opened = manager.launch_intent(IntentSpec(action=ACTION_VIEW, data="upi://pay"))
    if not chooser_opened:
        _say("I could not open the Android payment-app chooser.")
        return False
    _say("Choose your payment app, then open its QR scanner.")
    return True


register("make_payment", make_payment, category="payments")

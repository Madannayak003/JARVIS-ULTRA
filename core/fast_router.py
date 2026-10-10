from core.routers.news_router import news_route
from core.routers.browser_router import browser_route
from core.routers.system_router import system_route
from core.routers.automation_router import automation_route
from core.routers.network_router import network_route
from core.routers.media_router import media_route
from core.routers.file_router import file_route
from core.routers.vision_router import vision_route
from core.routers.spotify_router import spotify_route
from core.routers.greeting_router import greeting_route
from core.routers.whatsapp_router import whatsapp_route
from core.routers.contact_router import contact_route
from core.routers.email_router import email_route
from core.routers.file_selection_router import file_selection_route
from core.routers.memory_router import memory_route
from core.routers.web_router import web_route
from core.routers.weather_router import weather_route
from core.routers.android_router import android_route
from core.routers.payment_router import payment_route
from core.routers.phone_call_router import phone_call_route
from core.routers.schedule_router import schedule_route
from core.diagnostics import debug_print

ROUTERS = [

    phone_call_route,
    payment_route,
    schedule_route,
    memory_route,
    news_route,
    weather_route,
    web_route,
    automation_route,
    spotify_route,
    browser_route,
    greeting_route,
    system_route,
    network_route,
    media_route,
    vision_route,
    android_route,
    file_route,
    email_route,
    contact_route,
    whatsapp_route,
    file_selection_route

]

def fast_route(command):
    original_command = command.strip().rstrip("?!.,")
    command = original_command.lower()
    debug_print("[FAST ROUTER]", command)

    android_targeted = (
        command.startswith((
            "open phone ",
            "open mobile ",
            "open my phone ",
            "open my mobile ",
        ))
        or (
            command.startswith("open ")
            and command.endswith((
                " on phone",
                " on mobile",
                " on my phone",
                " on my mobile",
            ))
        )
    )

    if android_targeted:
        android_plan = android_route(command)
        if android_plan:
            debug_print(
                "[FAST ROUTER MATCH]",
                {"actions": [item.get("action") for item in android_plan if isinstance(item, dict)]},
            )
            return android_plan

    for router in ROUTERS:
        # * Preserve the spoken casing for registration names while keeping the
        # * existing normalized input contract for every other router.
        route_command = (
            original_command
            if router in (vision_route, schedule_route)
            else command
        )
        plan = router(route_command)

        if plan:
            debug_print(
                "[FAST ROUTER MATCH]",
                {"actions": [item.get("action") for item in plan if isinstance(item, dict)]},
            )
            return plan

    return None

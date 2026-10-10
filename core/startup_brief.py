"""Local, non-AI daily startup brief coordinator."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, wait
from datetime import datetime
from typing import Any, Callable, Mapping

from skills.assistant.greetings import startup_brief_greeting, speak_startup_text
from core.diagnostics import debug_print


_DATA_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="JARVIS-Startup")
DEFAULT_TIMEOUT = 2.0
STARTUP_DATA_TIMEOUT = 8.0
WEATHER_GRACE_TIMEOUT = 3.0


def _ordinal(day: int) -> str:
    if 10 < day % 100 < 14:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix}"


def _date_sentence(now: datetime) -> str:
    return f"Today is {now.strftime('%A, %B')} {_ordinal(now.day)}."


def _time_sentence(now: datetime) -> str:
    return f"It's currently {now.strftime('%I:%M %p').lstrip('0')}."


def _count_sentence(count: int, singular: str, plural: str) -> str:
    return f"You have {count} {singular if count == 1 else plural} today."


def _safe_call(label: str, provider: Callable[[], Any], default: Any = None) -> Any:
    try:
        return provider()
    except Exception as error:
        print(f"[STARTUP BRIEF] {label} unavailable: {error}")
        return default


def _today_reminders(now: datetime):
    from skills.memory.reminders import get_active_reminders
    return get_active_reminders(now=now)


def _today_tasks(now: datetime):
    from skills.automation.scheduling import list_schedules
    tasks = []
    for item in list_schedules() or []:
        if not item.get("enabled", True):
            continue
        try:
            target = datetime.fromisoformat(str(item.get("next_run_at", "")))
        except ValueError:
            continue
        if target.date() == now.date():
            tasks.append(item)
    return tasks


def _latest_note():
    from skills.memory.notes import get_latest_note
    return get_latest_note()


def _weather_sentence(weather: Mapping[str, Any]) -> str | None:
    condition = weather.get("condition")
    temperature = weather.get("temperature")
    location = weather.get("location")
    fields = []
    if condition:
        fields.append(str(condition))
    if temperature is not None:
        fields.append(f"{round(float(temperature))} degrees")
    if not fields:
        return None
    location_part = f" in {location}" if location else ""
    return f"The current weather{location_part} is " + " with ".join(fields) + "."


def _note_sentence(note: Any) -> str | None:
    if isinstance(note, Mapping):
        text = str(note.get("text", "")).strip()
    else:
        text = str(note or "").strip()
    if not text:
        return None
    if len(text) > 180:
        text = text[:177].rstrip() + "..."
    return f"Your latest note says: {text}."


def _get_current_weather():
    from skills.network.weather import get_current_weather
    return get_current_weather()


def start_weather_fetch():
    """Start the existing weather retrieval without creating a second provider."""
    return _DATA_EXECUTOR.submit(_get_current_weather)


def build_startup_brief(
    now: datetime | None = None,
    profile=None,
    *,
    weather_provider: Callable[[], Any] | None = None,
    reminders_provider: Callable[[], Any] | None = None,
    tasks_provider: Callable[[], Any] | None = None,
    latest_note_provider: Callable[[], Any] | None = None,
    latest_note: Any = None,
    news_headlines: list[dict[str, Any]] | None = None,
    news_enabled: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    """Collect available data and render one natural spoken utterance."""
    now = now or datetime.now()
    debug_print("[STARTUP BRIEF] Building daily startup brief...")
    parts = [
        startup_brief_greeting(now=now, profile=profile),
        _date_sentence(now),
        _time_sentence(now),
    ]

    reminders = list(_safe_call("Reminders", reminders_provider or (lambda: _today_reminders(now)), []) or [])
    debug_print(f"[STARTUP BRIEF] Reminders: {len(reminders)}")
    if reminders:
        parts.append(_count_sentence(len(reminders), "reminder", "reminders"))

    tasks = list(_safe_call("Schedule", tasks_provider or (lambda: _today_tasks(now)), []) or [])
    debug_print(f"[STARTUP BRIEF] Schedule: {len(tasks)} scheduled tasks")
    if tasks:
        parts.append(_count_sentence(len(tasks), "scheduled task", "scheduled tasks"))
    if not reminders and not tasks:
        parts.append("You have no reminders or scheduled tasks for today.")

    note = latest_note
    if note is None and latest_note_provider is not None:
        note = _safe_call("Latest note", latest_note_provider)
    note_text = _note_sentence(note)
    if note_text:
        parts.append(note_text)

    if weather_provider is None:
        def weather_provider():
            from skills.network.weather import get_current_weather
            return get_current_weather()
    weather_future = None
    try:
        weather_future: Future[Any] = _DATA_EXECUTOR.submit(weather_provider)
        weather = weather_future.result(timeout=max(0.0, timeout))
        sentence = _weather_sentence(weather or {})
        if sentence:
            parts.append(sentence)
            debug_print("[STARTUP BRIEF] Weather: READY")
        else:
            print("[STARTUP BRIEF] Weather unavailable: no current fields")
    except Exception as error:
        if weather_future is not None:
            weather_future.cancel()
        print(f"[STARTUP BRIEF] Weather unavailable: {error}")

    if news_enabled and news_headlines:
        try:
            from core.morning_brief import build_spoken_brief
            parts.append(build_spoken_brief(news_headlines))
            debug_print(f"[STARTUP BRIEF] News: {len(news_headlines[:3])} headlines")
        except Exception as error:
            print(f"[STARTUP BRIEF] News unavailable: {error}")
    elif news_enabled:
        print("[STARTUP BRIEF] News unavailable: no headlines")
    else:
        print("[STARTUP BRIEF] News: DISABLED")

    debug_print("[STARTUP BRIEF] Greeting: READY")
    debug_print("[STARTUP BRIEF] Date: READY")
    debug_print("[STARTUP BRIEF] Brief generated successfully")
    return " ".join(part.strip() for part in parts if part and part.strip())


def speak_startup_brief(
    speaker,
    profile=None,
    now=None,
    news_enabled=False,
    news_future=None,
    weather_future=None,
    return_text=False,
    weather_provider: Callable[[], Any] | None = None,
    reminders_provider: Callable[[], Any] | None = None,
    tasks_provider: Callable[[], Any] | None = None,
    latest_note_provider: Callable[[], Any] | None = None,
) -> bool:
    """Collect existing startup providers within one bounded readiness window."""
    try:
        debug_print("[STARTUP BRIEF] Collecting startup data...")
        if weather_future is None:
            weather_future = _DATA_EXECUTOR.submit(
                weather_provider or _get_current_weather
            )
        futures = {
            weather_future: "weather",
            _DATA_EXECUTOR.submit(
                reminders_provider or (lambda: _today_reminders(now))
            ): "reminders",
            _DATA_EXECUTOR.submit(
                tasks_provider or (lambda: _today_tasks(now))
            ): "schedule",
            _DATA_EXECUTOR.submit(
                latest_note_provider or _latest_note
            ): "notes",
        }
        if news_enabled and news_future is not None:
            futures[news_future] = "news"

        debug_print("[STARTUP BRIEF] Waiting for startup data...")
        done, pending = wait(futures, timeout=STARTUP_DATA_TIMEOUT)
        pending = set(pending)

        # Weather is already in flight and normally completes just after the
        # general deadline. Give that same Future a small bounded grace period
        # without delaying or changing the deadline for other data sources.
        if weather_future in pending:
            weather_done, _ = wait(
                [weather_future],
                timeout=WEATHER_GRACE_TIMEOUT,
            )
            if weather_done:
                done.add(weather_future)
                pending.remove(weather_future)

        results = {}
        for future in done:
            label = futures[future]
            try:
                results[label] = future.result()
                if label == "weather":
                    debug_print("[STARTUP BRIEF] Weather: READY")
                elif label == "reminders":
                    debug_print(f"[STARTUP BRIEF] Reminders: {len(results[label] or [])}")
                elif label == "schedule":
                    debug_print(f"[STARTUP BRIEF] Schedule: {len(results[label] or [])} scheduled tasks")
                elif label == "notes":
                    debug_print("[STARTUP BRIEF] Notes: READY" if results[label] else "[STARTUP BRIEF] Notes: EMPTY")
                elif results[label]:
                    debug_print(f"[STARTUP BRIEF] News: {len(results[label][:3])} headlines")
            except Exception as error:
                print(f"[STARTUP BRIEF] {label.title()} unavailable: {error}")

        for future in pending:
            label = futures[future]
            if label != "weather":
                future.cancel()
            print(f"[STARTUP BRIEF] {label.title()}: TIMEOUT")
            print(f"[STARTUP BRIEF] Continuing without {label}.")

        headlines = results.get("news")
        weather = results.get("weather")
        reminders = results.get("reminders", [])
        tasks = results.get("schedule", [])
        latest_note = results.get("notes")
        debug_print("[STARTUP BRIEF] Startup data collection complete.")
        text = build_startup_brief(
            now=now,
            profile=profile,
            reminders_provider=lambda: reminders,
            tasks_provider=lambda: tasks,
            latest_note=latest_note,
            weather_provider=lambda: weather,
            news_headlines=headlines,
            news_enabled=news_enabled,
        )
        if return_text:
            return text
        return speak_startup_text(speaker, text)
    except Exception as error:
        print(f"[STARTUP BRIEF] Coordinator failed safely: {error}")
        from skills.assistant.greetings import speak_startup_greeting
        return speak_startup_greeting(speaker, profile=profile, now=now)

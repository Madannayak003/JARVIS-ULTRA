"""Safe synchronous checks for the Gemini Live status/API contract."""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from pathlib import Path
from unittest.mock import patch

import pytest

# Avoid importing optional Edge-TTS/Google networking during these unit checks.
# The production modules are not replaced; only their unused test-time imports
# are isolated from the host SSL-filter failure.
_voice_manager_stub = ModuleType("voice.manager")
for _name in (
    "add_speech_listener",
    "speak",
    "stop_speaking",
    "start_speech_session",
    "prepare_speech",
    "play_prepared_speech",
):
    setattr(_voice_manager_stub, _name, lambda *_args, **_kwargs: None)
sys.modules.setdefault("voice.manager", _voice_manager_stub)

_genai_stub = ModuleType("google.genai")
_genai_stub.Client = object
_genai_types_stub = ModuleType("google.genai.types")
_genai_stub.types = _genai_types_stub
sys.modules.setdefault("google.genai", _genai_stub)
sys.modules.setdefault("google.genai.types", _genai_types_stub)

from voice import agent as live_agent
from hud.manager import HUDManager
import core.interrupt as interrupt_engine


ROOT = Path(__file__).resolve().parent
DASHBOARD_SOURCE = (ROOT / "dashboard" / "server.py").read_text(encoding="utf-8")


class _FakeAgent:
    def __init__(self, *, running: bool, connected: bool, microphone_enabled: bool = True):
        self.running = running
        self.connected = connected
        self._microphone_enabled = microphone_enabled

    def microphone_enabled(self):
        return self._microphone_enabled


@pytest.mark.parametrize(
    ("running", "connected", "expected_state", "expected_message"),
    [
        (True, True, "connected", "Agent is connected."),
        (True, False, "reconnecting", "Agent is reconnecting."),
        (False, False, "stopped", "Agent is stopped."),
    ],
)
def test_agent_state_and_legacy_status_are_consistent(
    running, connected, expected_state, expected_message
):
    fake = _FakeAgent(running=running, connected=connected)
    with patch.object(live_agent, "_agent", fake):
        assert live_agent.agent_status() == expected_message
        assert live_agent.agent_state() == {
            "running": running,
            "connected": connected,
            "state": expected_state,
            "microphone_enabled": running,
            "controller": "gemini-live",
        }


def test_typed_text_endpoint_uses_authoritative_connected_state():
    section = DASHBOARD_SOURCE[DASHBOARD_SOURCE.index('"/api/live/text"'):]
    section = section[:section.index('"/api/agent/status"')]

    assert "from voice.agent import agent_state, send_agent_text" in section
    assert 'if not agent_state()["connected"]:' in section
    assert '"status": "accepted"' in section
    assert '"error": "Gemini Live is unavailable. Request not executed."' in section
    assert "Agent is running." not in section


def test_remote_command_bridge_uses_authoritative_connected_state():
    section = DASHBOARD_SOURCE[DASHBOARD_SOURCE.index('# * LIVE TEXT BRIDGE'):]
    section = section[:section.index('# * BUILD FASTAPI')]

    assert "from voice.agent import (\n                agent_state," in section
    assert 'if agent_state()["connected"]:' in section
    assert "agent_status" not in section


def test_agent_status_endpoint_preserves_running_and_adds_connection_state():
    section = DASHBOARD_SOURCE[DASHBOARD_SOURCE.index('"/api/agent/status"'):]
    section = section[:section.index('"/api/agent/start"')]

    assert "from voice.agent import agent_state" in section
    assert '"running": state["running"]' in section
    assert '"connected": state["connected"]' in section
    assert '"state": state["state"]' in section
    assert '"controller": state["controller"]' in section
    assert "Agent is running." not in section


def test_microphone_endpoint_keeps_truthful_unavailable_gate():
    section = DASHBOARD_SOURCE[DASHBOARD_SOURCE.index('"/api/local/microphone"'):]
    section = section[:section.index('"/api/live/text"')]

    assert "if not _agent.running or not _agent.connected:" in section
    assert "Microphone not changed." in section
    assert '"connected": True' in section


def test_forced_listening_releases_speaking_after_live_playback():
    manager = HUDManager()
    manager.speaking()

    # Ordinary microphone notifications are intentionally suppressed while
    # audio is active; the playback-completion edge is allowed to transition.
    manager.listening()
    assert manager.state.status == "speaking"

    manager.listening(force=True)
    assert manager.state.status == "listening"
    assert manager.state.speaking is False
    assert manager.state.listening is True


def test_live_voice_activity_detector_has_start_and_hysteresis_end_edges():
    detector = live_agent.LiveVoiceActivityDetector()

    assert detector.update(100.0) is None
    assert detector.update(800.0) is True
    assert detector.update(400.0) is None
    assert detector.update(400.0) is None
    assert detector.update(400.0) is False


def test_voice_activity_does_not_clear_higher_priority_hud_states():
    manager = HUDManager()
    manager.thinking()
    manager.voice_activity(False)
    assert manager.state.status == "thinking"

    manager.speaking()
    manager.voice_activity(False)
    assert manager.state.status == "speaking"


def test_interrupt_engine_delegates_to_live_without_legacy_task_stop():
    with patch("voice.agent.interrupt_live_response", return_value=True), \
         patch.object(interrupt_engine, "stop") as stop_audio, \
         patch.object(interrupt_engine.task_manager, "stop_all") as stop_tasks, \
         patch.object(interrupt_engine, "clear") as clear_queue:
        assert interrupt_engine.interrupt() is True

    stop_audio.assert_not_called()
    stop_tasks.assert_not_called()
    clear_queue.assert_called_once()


def test_interrupt_engine_records_source_and_live_state():
    with patch("voice.agent.interrupt_live_response", return_value=False), \
         patch.object(interrupt_engine, "stop"), \
         patch.object(interrupt_engine, "stop_speaking"), \
         patch.object(interrupt_engine.task_manager, "stop_all"), \
         patch.object(interrupt_engine, "clear"), \
         patch("builtins.print") as output:
        assert interrupt_engine.interrupt(source="hud_button") is True

    assert any(
        call.args and call.args[0] == "[INTERRUPT]"
        and "hud_button" in call.args
        for call in output.call_args_list
    )


def test_legacy_assistant_stays_out_of_the_live_handoff_while_listener_is_paused():
    source = (ROOT / "core" / "assistant.py").read_text(encoding="utf-8")
    assert "if listener_paused():" in source
    listener_source = (ROOT / "core" / "listener.py").read_text(encoding="utf-8")
    assert "COMMAND_QUEUE.get_nowait()" in listener_source
    assert "discarded_commands=" in listener_source


def test_live_speaker_interrupt_does_not_restart_portaudio_stream_inline():
    agent = live_agent.Agent()
    calls = []

    class FakeSpeaker:
        def abort(self):
            calls.append("abort")

        def start(self):
            calls.append("start")

    agent._speaker_started = True

    assert agent._interrupt_speaker(FakeSpeaker()) is True
    assert calls == ["abort"]
    assert agent._speaker_started is False


def test_live_speaker_reopens_only_before_the_next_output_chunk():
    agent = live_agent.Agent()
    calls = []

    class FakeSpeaker:
        def start(self):
            calls.append("start")

        def write(self, audio):
            calls.append(("write", audio))

    agent._speaker_started = False
    agent._write_speaker(FakeSpeaker(), b"chunk")

    assert calls == ["start", ("write", b"chunk")]
    assert agent._speaker_started is True


def test_live_interrupt_barrier_rejects_late_audio_until_server_turn_boundary():
    agent = live_agent.Agent()
    generation = agent._live_generation_value()

    agent._begin_live_audio_discard()

    assert agent._live_output_allowed(generation) is False
    assert agent._is_discarding_live_audio() is True

    agent._finish_live_audio_discard()

    assert agent._live_output_allowed(generation) is True


def test_microphone_callback_defers_rms_processing_off_portaudio_thread():
    source = (ROOT / "voice" / "agent.py").read_text(encoding="utf-8")
    assert "def process_microphone_audio(audio_bytes):" in source
    assert "loop.call_soon_threadsafe(\n                process_microphone_audio," in source

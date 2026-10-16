import ast
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from brain.brain_router import BrainRouter
from ai.core.schemas import AIResponse, AIStreamChunk
from ai.core.service import ai_service
from brain.developer.generator.providers.gemini_provider import GeminiProvider
from brain.developer.editor.provider.gemini_provider import GeminiProvider as EditorGeminiProvider
from brain.developer.repair.repair_provider import RepairProvider
from brain.developer.prompt_builder.models.prompt_result import PromptResult
from core.live_execution import (
    LiveInvocationDeduplicator,
    is_live_developer_generation_allowed,
    live_developer_generation,
    live_execution,
)
from voice.agent import _is_expired_session_resumption_error, _live_reconnect_delay


VOICE_SOURCE = Path("voice/agent.py").read_text(encoding="utf-8")


def test_live_developer_tool_is_explicit_and_delegates_to_existing_dispatcher():
    tree = ast.parse(VOICE_SOURCE)
    function_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }
    assert "_build_jarvis_developer_tool" in function_names
    assert '"jarvis_developer"' in VOICE_SOURCE
    assert 'function_name in {"jarvis_command", "jarvis_developer"}' in VOICE_SOURCE
    assert "dispatch(" in VOICE_SOURCE
    assert "BrainRouter" not in VOICE_SOURCE


def test_existing_developer_router_receives_live_developer_wording():
    with TemporaryDirectory() as temp_dir:
        router = BrainRouter()
        router.configure_project(temp_dir)
        calls = []

        def fake_execute(user_request, project_path):
            calls.append((user_request, project_path))
            return SimpleNamespace(
                success=True,
                message="controlled developer result",
                patches=[],
                warnings=[],
                errors=[],
            )

        router.developer.execute = fake_execute
        result = router.route("create html login page")

        assert result.handled is True
        assert result.module == "developer"
        assert calls == [("create html login page", "")]


def test_secondary_ai_remains_blocked_for_ordinary_live_generation():
    with live_execution():
        result = ai_service.generate("normal live request", capability="conversation")

    assert result.success is False
    assert result.metadata["status"] == "live_only_blocked"


def test_only_scoped_developer_generation_is_allowed_during_live(monkeypatch):
    calls = []

    def fake_generate(**kwargs):
        calls.append(kwargs)
        return AIResponse(success=True, text="generated code", provider="test", model="test")

    monkeypatch.setattr(ai_service.router, "generate", lambda request: fake_generate(
        prompt=request.prompt,
        capability=request.capability,
        metadata=request.metadata,
    ))

    with live_execution():
        with live_developer_generation():
            result = ai_service.generate(
                "write code",
                capability="coding",
                metadata={"developer_generation": True},
            )

    assert result.success is True
    assert calls == [{
        "prompt": "write code",
        "capability": "coding",
        "metadata": {"developer_generation": True},
    }]


def test_developer_provider_enters_scoped_generation_and_preserves_failure(monkeypatch):
    calls = []

    def fake_generate(**kwargs):
        calls.append(kwargs)
        return AIResponse(
            success=False,
            error="configured generator failed",
            metadata={"status": "provider_error"},
        )

    monkeypatch.setattr(
        "brain.developer.generator.providers.gemini_provider.ai_service.generate",
        fake_generate,
    )
    prompt = PromptResult(user_prompt="generate a login page", system_prompt="code only")

    with live_execution():
        result = GeminiProvider().generate(prompt)

    assert result == ""
    assert calls[0]["capability"] == "coding"
    assert calls[0]["metadata"] == {"developer_generation": True}
    assert is_live_developer_generation_allowed() is False


def test_editor_provider_enters_scoped_generation_during_live(monkeypatch):
    calls = []

    def fake_generate(**kwargs):
        calls.append(kwargs)
        assert is_live_developer_generation_allowed() is True
        return AIResponse(success=True, text="edited response", provider="test", model="test")

    monkeypatch.setattr(
        "brain.developer.editor.provider.gemini_provider.ai_service.generate",
        fake_generate,
    )

    with live_execution():
        result = EditorGeminiProvider().generate(
            SimpleNamespace(system_prompt="edit safely", user_prompt="change the title")
        )

    assert result == "edited response"
    assert calls[0]["capability"] == "editing"
    assert calls[0]["metadata"] == {"developer_generation": True}
    assert is_live_developer_generation_allowed() is False


def test_repair_provider_enters_scoped_generation_during_live(monkeypatch):
    calls = []

    def fake_generate(**kwargs):
        calls.append(kwargs)
        assert is_live_developer_generation_allowed() is True
        return AIResponse(success=True, text="repaired response", provider="test", model="test")

    monkeypatch.setattr(
        "brain.developer.repair.repair_provider.ai_service.generate",
        fake_generate,
    )

    with live_execution():
        result = RepairProvider().generate(
            PromptResult(user_prompt="repair missing file", system_prompt="repair safely")
        )

    assert result == "repaired response"
    assert calls[0]["capability"] == "coding"
    assert calls[0]["metadata"] == {"developer_generation": True}
    assert is_live_developer_generation_allowed() is False


def test_developer_scope_is_cleared_after_editor_failure(monkeypatch):
    original_generate = ai_service.generate

    def fake_generate(**_kwargs):
        assert is_live_developer_generation_allowed() is True
        raise RuntimeError("provider failure")

    monkeypatch.setattr(
        "brain.developer.editor.provider.gemini_provider.ai_service.generate",
        fake_generate,
    )

    with live_execution():
        try:
            EditorGeminiProvider().generate(
                SimpleNamespace(system_prompt="edit safely", user_prompt="fail")
            )
        except RuntimeError:
            pass

        assert is_live_developer_generation_allowed() is False
        blocked = original_generate("unrelated", capability="conversation")

    assert blocked.success is False
    assert blocked.metadata["status"] == "live_only_blocked"


def test_editor_provider_preserves_non_live_ai_service_behavior(monkeypatch):
    calls = []

    def fake_generate(**kwargs):
        calls.append(kwargs)
        return AIResponse(success=True, text="non-live edit", provider="test", model="test")

    monkeypatch.setattr(
        "brain.developer.editor.provider.gemini_provider.ai_service.generate",
        fake_generate,
    )

    result = EditorGeminiProvider().generate(
        SimpleNamespace(system_prompt="edit", user_prompt="change code")
    )

    assert result == "non-live edit"
    assert calls[0]["capability"] == "editing"
    assert calls[0]["metadata"] == {"developer_generation": True}
    assert is_live_developer_generation_allowed() is False


def test_live_generation_scope_is_restored_after_timeout_or_cancellation():
    try:
        with live_execution():
            with live_developer_generation():
                raise TimeoutError("generator timed out")
    except TimeoutError:
        pass

    with live_execution():
        result = ai_service.generate("after timeout", capability="coding")
    assert result.success is False
    assert result.metadata["status"] == "live_only_blocked"


def test_only_expired_resumption_errors_clear_the_handle():
    assert _is_expired_session_resumption_error(
        "1008 session not found or expired"
    ) is True
    assert _is_expired_session_resumption_error(
        "1008 policy violation"
    ) is False
    assert _is_expired_session_resumption_error(
        "temporary network timeout"
    ) is False


def test_live_reconnect_backoff_is_bounded():
    assert _live_reconnect_delay(1) == 1.0
    assert _live_reconnect_delay(2) == 2.0
    assert _live_reconnect_delay(99) == 30.0


def test_duplicate_invocation_reuses_completed_response():
    cache = LiveInvocationDeduplicator(max_entries=2)
    assert cache.begin("call-1") == ("new", None)
    response = {"success": True, "message": "closed"}
    cache.complete("call-1", response)
    status, cached = cache.begin("call-1")
    assert status == "cached"
    assert cached is response


def test_concurrent_duplicate_invocation_waits_for_one_owner():
    cache = LiveInvocationDeduplicator()
    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(lambda _: cache.begin("call-2")[0], (1, 2)))
    assert sorted(statuses) == ["new", "wait"]
    waiting_status, future = cache.begin("call-2")
    assert waiting_status == "wait"
    response = {"success": False, "message": "process not found"}
    cache.complete("call-2", response)
    assert future.result() is response


def test_identical_text_with_distinct_invocation_ids_is_not_deduplicated():
    cache = LiveInvocationDeduplicator()
    assert cache.begin("call-a") == ("new", None)
    assert cache.begin("call-b") == ("new", None)


def test_invocation_cache_is_bounded():
    cache = LiveInvocationDeduplicator(max_entries=2)
    for invocation_id in ("one", "two", "three"):
        cache.begin(invocation_id)
        cache.complete(invocation_id, invocation_id)
    assert len(cache._completed) == 2
    status, value = cache.begin("one")
    assert (status, value) == ("new", None)


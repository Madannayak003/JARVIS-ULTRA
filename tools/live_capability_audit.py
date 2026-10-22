"""Safe static inventory of the configured JARVIS skill system.

This parses source with AST only. It never imports skill modules, starts
hardware/Torch/MediaPipe, launches schedulers, or performs external actions.
"""
from __future__ import annotations

import ast
import argparse
import csv
import json
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"
TEST_ROOTS = [ROOT / "tests", ROOT / "brain" / "tests"]

# Evidence supplied by the project owner in the continuation audit request.
# It is intentionally labeled as owner-reported because the raw Windows log
# is not present in this workspace for independent replay.
OWNER_REPORTED_LIVE_RUNTIME = {
    "capture": "Owner-reported normal Windows CMD run: photo saved as JPG.",
    "screenshot": "Owner-reported normal Windows CMD run: screenshot saved as PNG.",
    "create_reminder": "Owner-reported normal Windows CMD run: reminder persisted, triggered, spoke, and showed a Windows toast.",
}

CONFIRMED_FINDINGS = {
    "running_apps": {
        "root_cause": "Generic Windows running-apps intent was not a structured Live capability, while the Android foreground-app tool had a semantically broad description that could attract the model.",
        "repair": "Added a Windows running_apps Live schema, explicit platform boundaries in both tool descriptions, and exact Windows router aliases using the existing process handler.",
    },
    "brightness": {
        "root_cause": "The Windows display backend could raise access-denied during module import, preventing the brightness skill from registering and making its Live tool unavailable.",
        "repair": "Brightness backend import is now guarded; the registered capability returns an explicit unavailable result when the display backend cannot be used.",
    },
    "lock": {
        "root_cause": "The Windows lock action was registered only for the legacy dispatcher and had no reviewed structured Live declaration.",
        "repair": "Added a dedicated lock Live schema and regression coverage that keeps it separate from Windows shutdown.",
    },
    "shutdown": {
        "root_cause": "Windows shutdown was absent from structured Live declarations and the legacy exact 'shutdown' route meant application shutdown, creating an ambiguous model path.",
        "repair": "Added a dedicated Windows shutdown schema, spoken variants, and explicit confirmation enforcement before the existing handler runs.",
    },
    "terminate_jarvis": {
        "root_cause": "Application termination was only available through natural-language dispatch and the system skill could stop the listener without the complete application lifecycle callback.",
        "repair": "Added a distinct Live schema and injected the existing main application shutdown callback alongside the HUD callback, retaining a safe legacy fallback.",
    },
    "weather": {
        "root_cause": "Live weather work was scheduled asynchronously and task outcomes were previously discarded.",
        "repair": "drain_live_tasks now returns outcomes and voice.agent reports delayed failures honestly.",
    },
    "screen_vision_analyze": {
        "root_cause": "Live screen analysis uses scheduled asynchronous work whose failure outcome was not propagated.",
        "repair": "Live tool execution now inspects delayed task outcomes before claiming success.",
    },
}

UNIT_EVIDENCE = {
    "chatgpt_search": "test_action_edges.ActionEdgeTests.test_chatgpt_search_delegates_to_navigation",
    "clarify": "test_action_edges.ActionEdgeTests.test_clarify_starts_coordinator_and_speaks_question",
    "phone_call_confirmed": "test_action_edges.ActionEdgeTests.test_phone_confirmation_rejects_invalid_number_without_calling",
    "play": "test_action_edges.ActionEdgeTests.test_play_delegates_first_result_without_external_side_effect",
    "running_apps": "test_action_edges.ActionEdgeTests.test_running_apps_reports_processes_without_termination",
    "whatsapp_wait_contact": "test_action_edges.ActionEdgeTests.test_whatsapp_wait_contact_only_enters_prompt_state",
    "youtube_play_result": "test_action_edges.ActionEdgeTests.test_youtube_result_rejects_missing_video_id",
    "lock": "tests/test_system_live_controls.py::test_lock_calls_lock_handler_without_shutdown",
    "shutdown": "tests/test_system_live_controls.py::test_windows_shutdown_requires_confirmation_before_handler",
    "terminate_jarvis": "tests/test_system_live_controls.py::test_jarvis_shutdown_uses_application_callback_not_windows_shutdown",
    "brightness": "tests/test_brightness_live.py::test_brightness_reports_unavailable_without_backend",
}

# These tests exercise the Live declaration/validation/dispatch boundary with
# a fake registry. They are useful regression evidence, but deliberately do
# not upgrade the underlying skill to runtime-verified status.
MOCKED_LIVE_BOUNDARY_EVIDENCE = {
    action: "tests/test_live_capability_matrix.py::test_high_impact_capabilities_dispatch_real_payload_shape_without_side_effects"
    for action in (
        "file_info",
        "open_file",
        "volume",
        "brightness",
        "wifi_status",
        "android_check_device",
        "whatsapp_send_message",
    )
}


def _parse(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _literal_assignment(tree: ast.AST, name: str, default):
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    try:
                        return ast.literal_eval(node.value)
                    except Exception:
                        return default
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            try:
                return ast.literal_eval(node.value)
            except Exception:
                return default
    return default


def _function_index(tree: ast.AST) -> dict[str, ast.AST]:
    return {node.name: node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _registered_actions(path: Path) -> list[dict]:
    tree = _parse(path)
    functions = _function_index(tree)
    actions = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "register":
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
            continue
        action = node.args[0].value
        handler = node.args[1] if len(node.args) > 1 else None
        handler_name = handler.id if isinstance(handler, ast.Name) else ast.unparse(handler) if handler else None
        function = functions.get(handler_name)
        callable_defined = function is not None or isinstance(handler, ast.Lambda)
        parameters = []
        if function:
            parameters = [arg.arg for arg in function.args.args if arg.arg not in {"self", "_data"}]
            parameters.extend(arg.arg for arg in function.args.kwonlyargs)
        category = next((keyword.value.value for keyword in node.keywords if keyword.arg == "category" and isinstance(keyword.value, ast.Constant)), None)
        actions.append({
            "action": action,
            "module": path.relative_to(ROOT).with_suffix("").as_posix().replace("/", "."),
            "source": str(path.relative_to(ROOT)),
            "implementation": handler_name,
            "implementation_defined": callable_defined,
            "parameters": parameters,
            "category": category,
            "registration_line": node.lineno,
        })
    return actions


def _test_references(action: str) -> list[str]:
    references = []
    for root in TEST_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("test_*.py"):
            try:
                if action in path.read_text(encoding="utf-8"):
                    references.append(str(path.relative_to(ROOT)))
            except OSError:
                continue
    return references


def _dependency_class(module: str) -> str:
    lowered = module.lower()
    if any(token in lowered for token in ("camera", "vision", "screen", "phone_call")):
        return "hardware_or_visual_runtime"
    if any(token in lowered for token in ("browser", "youtube", "github", "news", "weather", "maps", "translate", "whatsapp", "email")):
        return "external_service_or_network"
    if any(token in lowered for token in ("payment", "android", "home_automation", "spotify")):
        return "external_or_consequential_integration"
    return "local_or_deterministic"


def _router_references(actions: set[str]) -> dict[str, list[str]]:
    references = {action: [] for action in actions}
    for path in (ROOT / "core" / "routers").glob("*.py"):
        try:
            tree = _parse(path)
        except (OSError, SyntaxError):
            continue
        found = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value in actions
        }
        for action in found:
            references[action].append(str(path.relative_to(ROOT)))
    return references


def build_inventory() -> dict:
    configured = _literal_assignment(_parse(SKILLS_ROOT / "loader.py"), "SKILLS", [])
    configured = [item for item in configured if isinstance(item, str)]
    modules, actions = [], []
    for module in configured:
        path = SKILLS_ROOT / (module.replace(".", "/") + ".py")
        record = {"module": module, "source": str(path.relative_to(ROOT)), "exists": path.exists(), "registered_action_count": 0}
        if path.exists():
            found = _registered_actions(path)
            record["registered_action_count"] = len(found)
            actions.extend(found)
        modules.append(record)

    schemas = _literal_assignment(_parse(ROOT / "core" / "live_agent.py"), "LIVE_CAPABILITY_SCHEMAS", {})
    schemas = schemas if isinstance(schemas, dict) else {}
    router_refs = _router_references({item["action"] for item in actions})
    for item in actions:
        action = item["action"]
        has_schema = action in schemas
        item["live_exposure"] = {"generic_dispatcher_tool": True, "structured_tool": has_schema, "structured_tool_name": f"jarvis_capability__{action}" if has_schema else None}
        item["schema"] = schemas.get(action)
        item["dependency_class"] = _dependency_class(item["module"])
        item["test_references"] = _test_references(action)
        item["router_references"] = router_refs.get(action, [])
        item["router_status"] = "PASS_STATIC" if item["router_references"] else "NOT_TESTED"
        item["static_status"] = "PASS_STATIC" if item["implementation_defined"] else "FAIL"
        item["execution_status"] = "NOT_TESTED"
        item["integration_status"] = "NOT_TESTED"
        item["verification_status"] = "PASS_STATIC" if item["implementation_defined"] else "FAIL"
        item["runtime_evidence"] = None
        item["unit_evidence"] = UNIT_EVIDENCE.get(action)
        item["mocked_live_boundary_evidence"] = MOCKED_LIVE_BOUNDARY_EVIDENCE.get(action)
        if item["unit_evidence"] and action not in OWNER_REPORTED_LIVE_RUNTIME:
            item["verification_status"] = "PASS_UNIT"
        item["confirmed_finding"] = CONFIRMED_FINDINGS.get(action)
        if not item["router_references"] and not has_schema and action not in OWNER_REPORTED_LIVE_RUNTIME and not item["unit_evidence"]:
            item["verification_status"] = "NOT_TESTED"
        if action in OWNER_REPORTED_LIVE_RUNTIME:
            item["verification_status"] = "PASS_LIVE_RUNTIME"
            item["runtime_evidence"] = OWNER_REPORTED_LIVE_RUNTIME[action]
        item["result_contract"] = "core.live_agent compatibility adapter; execution required for verification"

    action_names = [item["action"] for item in actions]
    duplicate_actions = sorted({name for name in action_names if action_names.count(name) > 1})
    return {
        "audit_mode": "static_ast_only",
        "side_effects_during_audit": False,
        "configured_module_count": len(configured),
        "existing_module_count": sum(1 for item in modules if item["exists"]),
        "callable_action_count": len(actions),
        "structured_live_action_count": sum(1 for item in actions if item["live_exposure"]["structured_tool"]),
        "duplicate_action_names": duplicate_actions,
        "duplicate_action_count": len(duplicate_actions),
        "modules": modules,
        "actions": sorted(actions, key=lambda item: item["action"]),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a side-effect-free JARVIS action inventory.")
    parser.add_argument("--output", type=Path, help="Write the JSON inventory to this path as well as stdout.")
    parser.add_argument("--csv-output", type=Path, help="Write the action-level CSV manifest to this path.")
    args = parser.parse_args()
    inventory = build_inventory()
    payload = json.dumps(inventory, indent=2, default=str) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    if args.csv_output:
        args.csv_output.parent.mkdir(parents=True, exist_ok=True)
        csv_buffer = io.StringIO()
        fields = [
            "action", "source", "registration_line", "live_path", "structured_tool",
            "schema_status", "static_status", "execution_status", "integration_status",
            "verification_status", "evidence", "mocked_live_boundary_evidence",
        ]
        writer = csv.DictWriter(csv_buffer, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for item in inventory["actions"]:
            exposure = item["live_exposure"]
            writer.writerow({
                "action": item["action"],
                "source": item["source"],
                "registration_line": item["registration_line"],
                "live_path": "jarvis_capability__" + item["action"] if exposure["structured_tool"] else "jarvis_command",
                "structured_tool": exposure["structured_tool"],
                "schema_status": "PRESENT" if item["schema"] is not None else "GENERIC_DISPATCH",
                "static_status": item["static_status"],
                "execution_status": item["execution_status"],
                "integration_status": item["integration_status"],
                "verification_status": item["verification_status"],
                "evidence": item["unit_evidence"] or item["runtime_evidence"] or "static AST route only",
                "mocked_live_boundary_evidence": item.get("mocked_live_boundary_evidence") or "",
            })
        args.csv_output.write_text(csv_buffer.getvalue(), encoding="utf-8")
    print(payload, end="")

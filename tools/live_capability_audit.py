"""Safe static inventory of the configured JARVIS skill system.

This parses source with AST only. It never imports skill modules, starts
hardware/Torch/MediaPipe, launches schedulers, or performs external actions.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"
TEST_ROOTS = [ROOT / "tests", ROOT / "brain" / "tests"]


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
    for item in actions:
        action = item["action"]
        has_schema = action in schemas
        item["live_exposure"] = {"generic_dispatcher_tool": True, "structured_tool": has_schema, "structured_tool_name": f"jarvis_capability__{action}" if has_schema else None}
        item["schema"] = schemas.get(action)
        item["dependency_class"] = _dependency_class(item["module"])
        item["test_references"] = _test_references(action)
        item["static_status"] = "PASS" if item["implementation_defined"] else "FAIL"
        item["execution_status"] = "NOT TESTED"
        item["integration_status"] = "NOT TESTED"
        item["result_contract"] = "core.live_agent compatibility adapter; execution required for verification"

    return {
        "audit_mode": "static_ast_only",
        "side_effects_during_audit": False,
        "configured_module_count": len(configured),
        "existing_module_count": sum(1 for item in modules if item["exists"]),
        "callable_action_count": len(actions),
        "structured_live_action_count": sum(1 for item in actions if item["live_exposure"]["structured_tool"]),
        "modules": modules,
        "actions": sorted(actions, key=lambda item: item["action"]),
    }


if __name__ == "__main__":
    print(json.dumps(build_inventory(), indent=2, default=str))

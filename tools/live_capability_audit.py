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
    "whatsapp_wait_message": "tests/test_live_batch20_contracts.py::test_batch20_whatsapp_followup_reports_needs_input_and_validates_contact",
    "whatsapp_send_latest_photo": "tests/test_live_batch19_media_contracts.py::test_batch19_whatsapp_media_reports_missing_assets_and_send_failures",
    "whatsapp_send_latest_screenshot": "tests/test_live_batch19_media_contracts.py::test_batch19_whatsapp_media_reports_missing_assets_and_send_failures",
    "whatsapp_send_file": "tests/test_live_batch19_media_contracts.py::test_batch19_whatsapp_media_reports_missing_assets_and_send_failures",
    "whatsapp_send_selected_file": "tests/test_live_batch19_media_contracts.py::test_batch19_whatsapp_file_selection_reports_state_and_success",
    "screenshot_ai": "tests/test_live_batch18_contracts.py::test_batch18_schemas_validate_screenshot_and_home_automation",
    "home_automation": "tests/test_live_batch18_contracts.py::test_batch18_schemas_validate_screenshot_and_home_automation",
    "whatsapp_send_message": "tests/test_live_batch18_contracts.py::test_batch18_whatsapp_send_reports_needs_input_and_send_failure",
    "whatsapp_open": "tests/test_live_batch18_contracts.py::test_batch18_whatsapp_open_close_preserve_truthful_boundary",
    "whatsapp_close": "tests/test_live_batch18_contracts.py::test_batch18_whatsapp_open_close_preserve_truthful_boundary",
    "close": "tests/test_live_batch17_contracts.py::test_batch17_new_schemas_validate_and_dispatch",
    "create_image": "tests/test_live_batch17_contracts.py::test_batch17_image_generation_preserves_success_and_failure",
    "create_reminder": "tests/test_live_batch17_contracts.py::test_batch17_reminder_live_result_keeps_persisted_item_and_legacy_bool",
    "screen_vision_analyze": "tests/test_live_batch17_contracts.py::test_batch17_screen_vision_live_boundary_reports_image_or_capture_failure",
    "send_email": "tests/test_live_batch17_contracts.py::test_batch17_new_schemas_validate_and_dispatch",
    "remember_email_contact": "tests/test_live_batch16_persistence_contracts.py::test_email_contact_results_are_structured_and_failures_are_truthful",
    "forget_email_contact": "tests/test_live_batch16_persistence_contracts.py::test_email_contact_results_are_structured_and_failures_are_truthful",
    "schedule_whatsapp_message": "tests/test_live_batch16_persistence_contracts.py::test_whatsapp_schedule_returns_persisted_item_without_sending",
    "reschedule_scheduled_whatsapp": "tests/test_live_batch16_persistence_contracts.py::test_whatsapp_schedule_and_reschedule_fail_before_persistence_on_bad_input",
    "youtube_search": "tests/test_live_batch16_persistence_contracts.py::test_youtube_search_live_boundary_preserves_actual_results",
    "google_search": "tests/test_live_batch15_browser_contracts.py::test_google_search_returns_browser_context_results_to_live",
    "open": "tests/test_live_batch15_browser_contracts.py::test_open_returns_target_details_and_failure_is_truthful",
    "youtube_play_first": "tests/test_live_batch15_browser_contracts.py::test_batch15_youtube_schemas_are_registered_and_validate",
    "youtube_pause": "tests/test_live_batch15_browser_contracts.py::test_youtube_pause_and_resume_preserve_verified_failure_states",
    "youtube_resume": "tests/test_live_batch15_browser_contracts.py::test_youtube_pause_and_resume_preserve_verified_failure_states",
    "youtube_next": "tests/test_live_batch15_browser_contracts.py::test_youtube_queue_navigation_reports_success_and_empty_queue",
    "youtube_previous": "tests/test_live_batch15_browser_contracts.py::test_batch15_youtube_schemas_are_registered_and_validate",
    "clear_notes": "tests/test_live_batch14_safe_contracts.py::test_clear_notes_returns_confirmed_structured_result",
    "close_process": "tests/test_live_batch14_safe_contracts.py::test_process_close_reports_termination_and_no_match_without_real_processes",
    "zip": "tests/test_live_batch14_safe_contracts.py::test_zip_and_extract_return_operation_details_with_mocked_archive_calls",
    "extract": "tests/test_live_batch14_safe_contracts.py::test_zip_and_extract_return_operation_details_with_mocked_archive_calls",
    "recycle": "tests/test_live_batch14_safe_contracts.py::test_recycle_uses_mocked_trash_boundary_and_rejects_empty_path",
    "remember_contact": "tests/test_live_batch14_safe_contracts.py::test_contacts_return_truthful_save_and_remove_results",
    "forget_contact": "tests/test_live_batch14_safe_contracts.py::test_contacts_return_truthful_save_and_remove_results",
    "weather": "tests/test_live_batch13_provider_results.py::test_weather_sync_returns_measured_fields_to_live",
    "get_news": "tests/test_live_batch13_provider_results.py::test_news_unavailable_and_exception_paths_do_not_report_truthy_text",
    "maps_open": "tests/test_live_batch12_browser_local_contracts.py::test_maps_actions_return_browser_open_results_through_live",
    "maps_directions": "tests/test_live_batch12_browser_local_contracts.py::test_maps_actions_return_browser_open_results_through_live",
    "translate_open": "tests/test_live_batch12_browser_local_contracts.py::test_translate_open_and_personal_link_use_safe_mocked_browser_boundaries",
    "open_personal_link": "tests/test_live_batch12_browser_local_contracts.py::test_translate_open_and_personal_link_use_safe_mocked_browser_boundaries",
    "welcome": "tests/test_live_batch12_browser_local_contracts.py::test_welcome_uses_local_speaker_and_reports_completion",
    "time": "tests/test_live_batch11_result_contracts.py::test_time_returns_the_value_to_live_without_breaking_truthiness",
    "taskmanager": "tests/test_live_batch11_result_contracts.py::test_taskmanager_returns_measured_usage_to_live",
    "wifi_on": "tests/test_live_batch11_result_contracts.py::test_wifi_enable_and_disable_return_verified_mocked_state",
    "wifi_off": "tests/test_live_batch11_result_contracts.py::test_wifi_enable_and_disable_return_verified_mocked_state",
    "wifi_status": "tests/test_live_batch11_result_contracts.py::test_wifi_status_and_list_return_structured_read_only_results",
    "wifi_list": "tests/test_live_batch11_result_contracts.py::test_wifi_status_and_list_return_structured_read_only_results",
    "translate_text": "tests/test_live_batch11_result_contracts.py::test_translate_text_returns_translation_and_rejects_missing_arguments",
    "assistant_name": "tests/test_live_non_android_repairs.py::test_first_batch_actions_have_live_boundary_contracts",
    "greet": "tests/test_live_batch4_greetings.py::test_greeting_actions_have_live_contracts_and_local_handlers",
    "how_are_you": "tests/test_live_batch4_greetings.py::test_greeting_actions_have_live_contracts_and_local_handlers",
    "goodbye": "tests/test_live_batch4_greetings.py::test_greeting_actions_have_live_contracts_and_local_handlers",
    "back": "tests/test_live_non_android_repairs.py::test_first_batch_actions_have_live_boundary_contracts",
    "forward": "tests/test_live_non_android_repairs.py::test_first_batch_actions_have_live_boundary_contracts",
    "close_tab": "tests/test_live_non_android_repairs.py::test_first_batch_actions_have_live_boundary_contracts",
    "refresh": "tests/test_live_non_android_repairs.py::test_first_batch_actions_have_live_boundary_contracts",
    "bluetooth_devices": "tests/test_live_non_android_repairs.py::test_bluetooth_structured_dispatch_injects_registered_action",
    "bluetooth_status": "tests/test_live_non_android_repairs.py::test_bluetooth_structured_dispatch_injects_registered_action",
    "camera_close": "tests/test_live_non_android_repairs.py::test_first_batch_actions_have_live_boundary_contracts",
    "camera_preview": "tests/test_live_non_android_repairs.py::test_first_batch_actions_have_live_boundary_contracts",
    "camera_status": "tests/test_live_non_android_repairs.py::test_first_batch_actions_have_live_boundary_contracts",
    "list_notes": "tests/test_live_non_android_repairs.py::test_second_batch_read_only_actions_have_live_contracts",
    "clipboard": "tests/test_live_non_android_repairs.py::test_second_batch_read_only_actions_have_live_contracts",
    "new_tab": "tests/test_live_non_android_repairs.py::test_second_batch_read_only_actions_have_live_contracts",
    "scroll_down": "tests/test_live_non_android_repairs.py::test_second_batch_read_only_actions_have_live_contracts",
    "scroll_up": "tests/test_live_non_android_repairs.py::test_second_batch_read_only_actions_have_live_contracts",
    "recent_files": "tests/test_live_batch5_results.py::test_batch5_handlers_return_truthful_structured_results",
    "list_reminders": "tests/test_live_batch5_results.py::test_batch5_handlers_return_truthful_structured_results",
    "list_scheduled_whatsapp": "tests/test_live_batch5_results.py::test_batch5_handlers_return_truthful_structured_results",
    "open_file": "tests/test_live_batch6_files.py::test_file_actions_reach_safe_path_validation",
    "open_folder": "tests/test_live_batch6_files.py::test_file_actions_reach_safe_path_validation",
    "file_info": "tests/test_live_batch7_file_results.py::test_file_info_and_search_return_structured_results",
    "search_file": "tests/test_live_batch7_file_results.py::test_file_info_and_search_return_structured_results",
    "file_intelligence_request": "tests/test_live_batch7_file_results.py::test_file_intelligence_request_schemas_inject_action",
    "file_question_request": "tests/test_live_batch7_file_results.py::test_file_intelligence_request_schemas_inject_action",
    "file_search_request": "tests/test_live_batch7_file_results.py::test_file_intelligence_request_schemas_inject_action",
    "show_contacts": "tests/test_live_batch8_readonly_lists.py::test_readonly_list_handlers_return_structured_results",
    "show_email_contacts": "tests/test_live_batch8_readonly_lists.py::test_readonly_list_handlers_return_structured_results",
    "show_personal_links": "tests/test_live_batch8_readonly_lists.py::test_readonly_list_handlers_return_structured_results",
    "create_note": "tests/test_live_batch9_persistence_results.py::test_note_and_schedule_results_are_structured",
    "list_schedules": "tests/test_live_batch9_persistence_results.py::test_note_and_schedule_results_are_structured",
    "spotify_open": "tests/test_live_batch10_spotify_contracts.py::test_spotify_actions_validate_and_reach_executor",
    "spotify_close": "tests/test_live_batch10_spotify_contracts.py::test_spotify_actions_validate_and_reach_executor",
    "spotify_next": "tests/test_live_batch10_spotify_contracts.py::test_spotify_actions_validate_and_reach_executor",
    "spotify_previous": "tests/test_live_batch10_spotify_contracts.py::test_spotify_actions_validate_and_reach_executor",
    "spotify_pause": "tests/test_live_batch10_spotify_contracts.py::test_spotify_actions_validate_and_reach_executor",
    "spotify_play": "tests/test_live_batch10_spotify_contracts.py::test_spotify_actions_validate_and_reach_executor",
    "spotify_volume_up": "tests/test_live_batch10_spotify_contracts.py::test_spotify_actions_validate_and_reach_executor",
    "spotify_volume_down": "tests/test_live_batch10_spotify_contracts.py::test_spotify_actions_validate_and_reach_executor",
    "spotify_play_song": "tests/test_live_batch10_spotify_contracts.py::test_spotify_actions_validate_and_reach_executor",
    "create_folder": "tests/test_live_batch6_files.py::test_file_actions_reach_safe_path_validation",
    "create_file": "tests/test_live_batch6_files.py::test_file_actions_reach_safe_path_validation",
    "copy": "tests/test_live_batch6_files.py::test_file_actions_reach_safe_path_validation",
    "move": "tests/test_live_batch6_files.py::test_file_actions_reach_safe_path_validation",
    "delete": "tests/test_live_batch6_files.py::test_file_actions_reach_safe_path_validation",
    "rename": "tests/test_live_batch6_files.py::test_file_actions_reach_safe_path_validation",
    "battery": "tests/test_live_batch3_contracts.py::test_batch3_structured_actions_validate_and_propagate",
    "browser_open_result": "tests/test_live_batch3_contracts.py::test_batch3_structured_actions_validate_and_propagate",
    "browser_read_page": "tests/test_live_batch3_contracts.py::test_batch3_structured_actions_validate_and_propagate",
    "cancel_reminder": "tests/test_live_batch3_contracts.py::test_batch3_structured_actions_validate_and_propagate",
    "cancel_schedule": "tests/test_live_batch3_contracts.py::test_batch3_structured_actions_validate_and_propagate",
    "cancel_scheduled_whatsapp": "tests/test_live_batch3_contracts.py::test_batch3_structured_actions_validate_and_propagate",
    "capture": "tests/test_live_batch3_contracts.py::test_batch3_structured_actions_validate_and_propagate",
    "create_reminder": "tests/test_live_batch3_contracts.py::test_batch3_structured_actions_validate_and_propagate",
    "create_schedule": "tests/test_live_batch3_contracts.py::test_batch3_structured_actions_validate_and_propagate",
    "github_search": "tests/test_live_batch3_contracts.py::test_batch3_structured_actions_validate_and_propagate",
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
    "file_list": "tests/test_live_agent.py::test_file_list_registry_boundary_uses_file_intelligence_action",
    "file_search": "tests/test_live_agent.py::test_file_search_payload_matches_file_intelligence_dispatch",
}

# These tests exercise the Live declaration/validation/dispatch boundary with
# a fake registry. They are useful regression evidence, but deliberately do
# not upgrade the underlying skill to runtime-verified status.
MOCKED_LIVE_BOUNDARY_EVIDENCE = {
    "whatsapp_wait_message": "Mocked WhatsApp follow-up state; no application was opened and no message was sent.",
    "whatsapp_send_latest_photo": "Mocked photo lookup and sender failure; no media was sent.",
    "whatsapp_send_latest_screenshot": "Mocked screenshot lookup; no screenshot was read or sent.",
    "whatsapp_send_file": "Mocked file lookup and sender failure; no file was sent.",
    "whatsapp_send_selected_file": "Mocked pending-file state and successful sender; no file was sent.",
    "screenshot_ai": "Mocked screenshot-file boundary; no screenshot was read and Live correctly reports this path unsupported.",
    "home_automation": "Mocked ESP32 control boundary; no hardware command was sent.",
    "whatsapp_send_message": "Mocked sender with success, failure, and invalid-input paths; no message was sent.",
    "whatsapp_open": "Mocked WhatsApp launcher success/failure; no application was opened.",
    "whatsapp_close": "Mocked WhatsApp close boundary; no application was closed.",
    "close": "Mocked browser close and structured-schema dispatch; no real browser was closed.",
    "create_image": "Mocked image-service response and temporary output directory; no external request was made.",
    "create_reminder": "Mocked reminder clock, persistence, and speech; no user reminder data was changed.",
    "screen_vision_analyze": "Mocked screen capture image encoding and capture failure; no desktop screen was captured.",
    "send_email": "Mocked local draft flow and schema validation; no email was sent.",
    "file_info": "tests/test_live_capability_matrix.py::test_high_impact_capabilities_dispatch_real_payload_shape_without_side_effects",
    "open_file": "tests/test_live_capability_matrix.py::test_high_impact_capabilities_dispatch_real_payload_shape_without_side_effects",
    "volume": "tests/test_live_capability_matrix.py::test_high_impact_capabilities_dispatch_real_payload_shape_without_side_effects",
    "brightness": "tests/test_live_capability_matrix.py::test_high_impact_capabilities_dispatch_real_payload_shape_without_side_effects",
    "wifi_status": "tests/test_live_capability_matrix.py::test_high_impact_capabilities_dispatch_real_payload_shape_without_side_effects",
    "android_check_device": "tests/test_live_capability_matrix.py::test_high_impact_capabilities_dispatch_real_payload_shape_without_side_effects",
    "whatsapp_send_message": "tests/test_live_capability_matrix.py::test_high_impact_capabilities_dispatch_real_payload_shape_without_side_effects",
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
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id not in {"register", "ai_register"}:
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

    # A small number of existing non-Android skills register an intentional
    # family of actions through a literal loop. Expand those registrations so
    # the inventory reflects the runtime registry rather than only literal
    # call sites. This remains AST-only and never imports a skill module.
    for node in ast.walk(tree):
        if not isinstance(node, ast.For) or not isinstance(node.target, ast.Name):
            continue
        if not isinstance(node.iter, (ast.List, ast.Tuple)):
            continue
        values = [item.value for item in node.iter.elts if isinstance(item, ast.Constant) and isinstance(item.value, str)]
        if not values:
            continue
        for call in ast.walk(node):
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name) or call.func.id != "register":
                continue
            if not call.args or not isinstance(call.args[0], ast.Name) or call.args[0].id != node.target.id:
                continue
            handler = call.args[1] if len(call.args) > 1 else None
            handler_name = handler.id if isinstance(handler, ast.Name) else ast.unparse(handler) if handler else None
            function = functions.get(handler_name)
            parameters = []
            if function:
                parameters = [arg.arg for arg in function.args.args if arg.arg not in {"self", "_data"}]
                parameters.extend(arg.arg for arg in function.args.kwonlyargs)
            category = next((keyword.value.value for keyword in call.keywords if keyword.arg == "category" and isinstance(keyword.value, ast.Constant)), None)
            for action in values:
                if any(item["action"] == action for item in actions):
                    continue
                actions.append({
                    "action": action,
                    "module": path.relative_to(ROOT).with_suffix("").as_posix().replace("/", "."),
                    "source": str(path.relative_to(ROOT)),
                    "implementation": handler_name,
                    "implementation_defined": function is not None or isinstance(handler, ast.Lambda),
                    "parameters": parameters,
                    "category": category,
                    "registration_line": call.lineno,
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
        item["scope"] = (
            "EXCLUDED_BY_USER"
            if item["module"].startswith(("skills.android_control.", "skills.payments.", "skills.phone_call."))
            else "IN_SCOPE_NON_ANDROID"
        )
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
        if item["scope"] == "EXCLUDED_BY_USER":
            item["audit_classification"] = "EXCLUDED_BY_USER"
        elif item["verification_status"] == "NOT_TESTED":
            item["audit_classification"] = "UNTESTED"
        elif item["verification_status"] == "PASS_UNIT":
            item["audit_classification"] = "PASS"
        elif item["verification_status"] == "PASS_LIVE_RUNTIME":
            # These entries are owner-reported, not independently reproduced
            # in a credentialed Live session.
            item["audit_classification"] = "PARTIAL"
        elif item["verification_status"] == "FAIL":
            item["audit_classification"] = "FAIL"
        else:
            item["audit_classification"] = "PARTIAL"
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
            "verification_status", "scope", "audit_classification", "evidence", "mocked_live_boundary_evidence",
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
                "scope": item["scope"],
                "audit_classification": item["audit_classification"],
                "evidence": item["unit_evidence"] or item["runtime_evidence"] or "static AST route only",
                "mocked_live_boundary_evidence": item.get("mocked_live_boundary_evidence") or "",
            })
        args.csv_output.write_text(csv_buffer.getvalue(), encoding="utf-8")
    print(payload, end="")

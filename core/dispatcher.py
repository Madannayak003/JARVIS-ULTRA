from ai.intent import detect
from core.task_manager import task_manager
from core.workers import chat_worker
from core.planner_worker import planner_worker

from core.action_memory import (
    get_memory,
    set_memory,
)

from core.executor import execute_ai_plan
from ai.memory_manager import learn as learn_explicit_memory
from ai.memory_view import show_all
from ai.memory_intent import handle as memory_forget
from ai.memory_profile import profile_summary

from core.context import (
    get_value,
    set_value,
)

from ai.memory_stats import (
    total,
    by_category,
)

from brain.brain_router import BrainRouter
brain_router = BrainRouter()
from core.fast_router import fast_route
from core.assistant_name import normalize_assistant_invocation
from config.settings import get_assistant_display_name
from core.registry import execute
from brain.screen_followup import is_screen_followup
from brain.conversation_coordinator import conversation_coordinator
from brain.execution_context import execution_context_resolver

from brain.followup_execution_bridge import (
    followup_execution_bridge,
)

from brain.followup_resolver import (
    FollowUpResolver,
)

from brain.conversation_context import (
    conversation_context,
)
from brain.natural.response_strategy import action_result_message

from core.live_execution import is_live_execution, capture_live_response, get_live_responses
from core.core_state import wait_for_core
from core.diagnostics import debug_print

# * =========================================================
# * DISPATCHER
# * =========================================================

def dispatch(
    command,
    skip_fast=False,
    fast_plan=None,
    conversation_request=None,
    skip_nci=False,
):

    if command is None or not str(command).strip():

        if conversation_coordinator.clarification.is_waiting():

            conversation_coordinator.consume_clarification_reply(
                command
            )

        return

    wait_for_core()

    command = str(command).strip()

    if not command:
        return

    # * The preferred ConversationRequest path is intentionally read-only. The
    # * dispatcher owns the turn boundary, so record the current input here for
    # * both microphone and dashboard/remote callers before NCI reads context.
    try:
        conversation_context.set_user_input(command)
    except Exception as error:
        print(
            "[CONVERSATION] Current input context update failed safely: "
            f"{error}"
        )

    # * Normalize assistant invocations before clarification, NCI, or planner
    # * handling. Microphone, HUD, and remote commands therefore share one path.
    invocation = normalize_assistant_invocation(command)
    if invocation:
        # ! A fresh known assistant invocation is a new request, never an answer
        # * to an older clarification. Keep normal clarification replies such as
        # * "github" and "google" unchanged.
        if conversation_coordinator.clarification.is_waiting():
            print(
                "[CLARIFICATION] Current assistant invocation "
                "preempts pending clarification."
            )
            conversation_coordinator.cancel_clarification()

        command = invocation.command or "hey"
        if fast_plan is None:
            fast_plan = fast_route(command)
        if fast_plan:
            skip_nci = True

    # * Resolve deterministic commands before NCI can classify a fresh
    # * command as a contextual conversation follow-up. This preserves the
    # * existing follow-up path when no deterministic route matches, while
    # * allowing registered Vision and other skill commands to execute first.
    if not skip_fast and fast_plan is None:
        fast_plan = fast_route(command)
        if fast_plan:
            skip_nci = True

    # * A face registration flow owns its next reply until it completes or is
    # * cancelled. This keeps a name such as "Madan" from becoming a new task.
    from skills.camera.face_registration import face_registration
    if face_registration.handle_pending_input(command):
        return

    # * =====================================================
    # * PENDING CLARIFICATION
    # * =====================================================
    #
    # ! A clarification reply must be consumed before email, fast routing, or
    # * the normal planner can reinterpret it as a brand-new request.
    # * =====================================================

    clarification_reply = (
        conversation_coordinator.consume_clarification_reply(
            command
        )
    )

    if clarification_reply:

        status = clarification_reply.get("status")

        if status == "new_request":

            # * The user explicitly abandoned the question in favour of a new
            # ! command. Do not let stale clarification state capture a later
            # * turn after that command finishes.
            conversation_coordinator.clarification.clear()
            conversation_coordinator.context.clear_pending()

        if status == "cancelled":

            print("[CLARIFICATION] Cancelled.")

            return

        if status == "resolved":

            merged_request = clarification_reply.get("merged_request")

            if not merged_request:

                print(
                    "[CLARIFICATION] Missing original request; "
                    "continuing with the answer."
                )

                merged_request = command

            print(
                "[CLARIFICATION] Resolved request:",
                merged_request,
            )

            print(
                "[CLARIFICATION] Context after resolution:",
                conversation_coordinator.context.snapshot(),
            )

            task_manager.start(
                "planner",
                planner_worker,
                merged_request,
            )

            return

    # * =====================================================
    # * PENDING EMAIL COMPOSITION
    # * =====================================================

    from skills.communication.email import (
        has_pending_email,
        handle_email_reply,
    )

    if has_pending_email():

        print(
            "[EMAIL] Handling pending email reply."
        )

        handle_email_reply(
            command
        )

        return
    
    # * =====================================================
    # * AGENT CONTROL
    # * =====================================================

    agent_command = command.lower().strip()

    if agent_command in {
        "start agent",
        "enter agent",
        "start natural agent",
    }:

        return execute(
            "start_agent"
        )

    if agent_command in {
        "stop agent",
        "exit agent",
        "end agent",
    }:

        return execute(
            "stop_agent"
        )

    if agent_command in {
        "agent status",
    }:

        return execute(
            "agent_status"
        )

    # * =====================================================
    # * CLARIFICATION CONTEXT
    # * =====================================================

    clarify = get_memory(
        "clarify_context"
    )

    if clarify:

        subject = clarify.get(
            "subject"
        )

        ctype = clarify.get(
            "type"
        )

        if ctype == "generic_action":

            cmd = command.lower()

            # * -------------------------------------------------
            # * Google
            # * -------------------------------------------------

            if cmd in [
                "google",
                "search google",
                "search on google",
                "on google",
            ]:

                set_memory(
                    "clarify_context",
                    None,
                )

                execute_ai_plan(
                    [
                        {
                            "action": "google_search",
                            "query": subject,
                        }
                    ],
                    task_manager.event(
                        "planner"
                    ),
                )

                return

            # * -------------------------------------------------
            # * YouTube
            # * -------------------------------------------------

            elif cmd in [
                "youtube",
                "search youtube",
                "search on youtube",
                "on youtube",
            ]:

                set_memory(
                    "clarify_context",
                    None,
                )

                execute_ai_plan(
                    [
                        {
                            "action": "youtube_search",
                            "query": subject,
                        }
                    ],
                    task_manager.event(
                        "planner"
                    ),
                )

                return

            # * -------------------------------------------------
            # * GitHub
            # * -------------------------------------------------

            elif cmd in [
                "github",
                "search github",
            ]:

                set_memory(
                    "clarify_context",
                    None,
                )

                execute_ai_plan(
                    [
                        {
                            "action": "github_search",
                            "query": subject,
                        }
                    ],
                    task_manager.event(
                        "planner"
                    ),
                )

                return

            # * -------------------------------------------------
            # * ChatGPT
            # * -------------------------------------------------

            elif cmd in [
                "chatgpt",
                "search chatgpt",
            ]:

                set_memory(
                    "clarify_context",
                    None,
                )

                execute_ai_plan(
                    [
                        {
                            "action": "chatgpt_search",
                            "query": subject,
                        }
                    ],
                    task_manager.event(
                        "planner"
                    ),
                )

                return
            
    # * =====================================================
    # * NATURAL CONVERSATION ANALYSIS
    # * =====================================================
    #
    # * ConversationRequest is now the preferred common
    # * conversational interface.
    #
    # * During migration, the existing ConversationCoordinator
    # * remains as a compatibility fallback.
    #
    # ! IMPORTANT:
    # * This section only prepares conversational information.
    # * It does not execute anything.
    # * =====================================================

    conversation_analysis = None

    try:

        # * Dashboard/remote/Live callers may enter through dispatch() without
        # * the assistant loop's pre-built ConversationRequest. Build the same
        # * read-only NCI request here so short conversational follow-ups use
        # * the same context-aware route across input surfaces.
        if not skip_nci and conversation_request is None:
            try:
                from brain import (
                    conversation as brain_conversation,
                    profile as brain_profile,
                    state as brain_state,
                )
                from brain.natural.natural_bridge import (
                    natural_conversation_bridge,
                )

                conversation_request = (
                    natural_conversation_bridge.process(
                        user_input=command,
                        conversation_context=conversation_context,
                        conversation_manager=brain_conversation,
                        profile_manager=brain_profile,
                        state_manager=brain_state,
                        ai_context=None,
                    )
                )
            except Exception as error:
                print(
                    "[CONVERSATION] Direct NCI request failed safely: "
                    f"{error}"
                )

        if skip_nci:

            conversation_analysis = None

        elif conversation_request is not None:

            from brain.followup_resolver import (
                FollowUpResolution,
            )

            # * -------------------------------------------------
            # * Adapt the new common ConversationRequest into
            # * the existing FollowUpResolution interface.
            #
            # * This allows the existing FollowUpExecutionBridge
            # * to remain unchanged during the migration.
            # * -------------------------------------------------

            conversation_analysis = type(
                "ConversationAnalysisAdapter",
                (),
                {}
            )()

            conversation_analysis.follow_up = (
                FollowUpResolution(

                    is_follow_up=(
                        conversation_request.relation
                        in {
                            "follow_up",
                            "continuation",
                            "correction",
                            "reference",
                            "contextual_reference",
                        }
                        or conversation_request.intent
                        == "contextual_reference"
                    ),

                    raw_input=(
                        conversation_request.user_input
                        or command
                    ),

                    relation=(
                        conversation_request.relation
                        or "new_request"
                    ),

                    application=(
                        conversation_request.application
                    ),

                    skill=(
                        conversation_request.skill
                    ),

                    topic=(
                        conversation_request.topic
                    ),

                    task=(
                        conversation_request.task
                    ),

                    intent=(
                        conversation_request.intent
                    ),

                    action=(
                        conversation_request.action
                    ),

                    object=(
                        conversation_request.object
                    ),

                    references=list(
                        conversation_request.references
                        or (
                            [conversation_request.reference]
                            if conversation_request.reference
                            else []
                        )
                    ),

                    resolved_references=dict(
                        conversation_request
                        .resolved_references
                        or {}
                    ),

                    unresolved_references=list(
                        conversation_request
                        .unresolved_references
                        or []
                    ),

                    confidence=(
                        conversation_request.confidence
                    ),

                    reason=(
                        "Adapted from ConversationRequest."
                    ),
                )
            )

            print(
                "[CONVERSATION] "
                "Using ConversationRequest."
            )

        else:

            # * -------------------------------------------------
            # * Compatibility fallback
            # * -------------------------------------------------

            conversation_analysis = (
                conversation_coordinator.analyze(
                    command
                )
            )

            print(
                "[CONVERSATION] "
                "Using ConversationCoordinator fallback."
            )

    except Exception as e:

        print(
            "[CONVERSATION] "
            f"Analysis failed safely: {e}"
        )

    # * ---------------------------------------------------------
    # * File Intelligence question preemption
    # * ---------------------------------------------------------
    # ! A natural-language question about the active uploaded file can be
    # ! classified by ConversationRequest as generic conversation first. Give
    # ! the existing File Intelligence router a chance before contextual chat
    # ! follow-up handling so it reaches its dedicated model path.
    # * ---------------------------------------------------------
    if not skip_fast:
        try:
            from core.routers.file_router import file_route

            file_plan = file_route(command)
            file_question_plan = [
                action
                for action in (file_plan or [])
                if action.get("action") == "file_question_request"
            ]

            if file_question_plan:
                print("[DISPATCHER] File Intelligence question preempted generic conversation routing.")
                for action in file_question_plan:
                    result = execute(action["action"], action)
                    if isinstance(result, str) and result.strip():
                        from voice.manager import speak
                        speak(result)
                return
        except Exception as error:
            print(f"[FILE INTELLIGENCE ROUTING] Preemption failed safely: {error}")
        
    # * =====================================================
    # * NATURAL CONVERSATION FOLLOW-UP PRIORITY
    # * =====================================================
    #
    # * If NCI has a valid contextual follow-up, let the
    # * Follow-Up Execution Bridge handle it before FAST ROUTE.
    #
    # * This prevents generic fast commands from stealing
    # * context-sensitive commands such as:
    #
    # * YouTube → "play the next one"
    # * YouTube → "play the first one"
    #
    # * Normal commands still continue to FAST ROUTE.
    # * =====================================================

    if (
        not skip_fast
        and conversation_analysis is not None
        and conversation_analysis.follow_up is not None
        and conversation_analysis.follow_up.is_follow_up
    ):

        # * -------------------------------------------------
        # * Re-resolve the follow-up against the LIVE
        # * conversation context.
        #
        # ! This is important for references such as:
        #
        # * "the second one"
        #
        # * ConversationRequest understands the reference,
        # * but FollowUpResolver resolves it to the actual
        # * contextual object.
        # * -------------------------------------------------

        follow_up = FollowUpResolver().resolve(
            conversation_analysis.follow_up,
            conversation_context.context,
        )

        debug_print(
            "[FOLLOW-UP DEBUG] resolved_references:",
            follow_up.resolved_references,
        )

        debug_print(
            "[FOLLOW-UP DEBUG] object:",
            follow_up.object,
        )

        if follow_up.object is not None:
            debug_print(
                "[FOLLOW-UP DEBUG] object video_id:",
                getattr(
                    follow_up.object,
                    "data",
                    {}
                ).get("video_id")
                if hasattr(
                    getattr(
                        follow_up.object,
                        "data",
                        None
                    ),
                    "get"
                )
                else None,
            )

        follow_up_plan = (
            followup_execution_bridge.resolve(
                raw_input=command,
                follow_up=follow_up,
            )
        )

        if follow_up_plan:

            print(
                "[CONVERSATION PRIORITY] "
                "Contextual follow-up takes priority:",
                follow_up_plan,
            )

            for action in follow_up_plan:

                action_name = action.get(
                    "action"
                )

                if not action_name:
                    continue

                print(
                    "[CONVERSATION PRIORITY] "
                    f"Executing {action_name}"
                )

                live_response_count = len(get_live_responses()) if is_live_execution() else 0
                result = execute(
                    action_name,
                    action,
                )

                # Live skills may return their real result without calling
                # voice.manager.speak (news, weather, and screen analysis do
                # this). Preserve that result for the Live tool response.
                if is_live_execution() and result is not False and len(get_live_responses()) == live_response_count:
                    if isinstance(result, str) and result.strip():
                        capture_live_response(result)
                    elif isinstance(result, dict) and result.get("status") != "pending_analysis":
                        message = action_result_message(action_name, action, result)
                        if message:
                            capture_live_response(message)

                print(
                    "[CONVERSATION PRIORITY RESULT]",
                    repr(result),
                )

                # * -----------------------------------------
                # * Synchronize conversational context after
                # * follow-up execution.
                #
                # * The follow-up may have changed the active
                # * browser object, for example:
                #
                # * "play the second one"
                #
                # * The existing normal execution path already
                # * performs this synchronization. The
                # ! contextual follow-up path must do the same.
                # * -----------------------------------------

                try:

                    execution_context = (
                        execution_context_resolver.resolve(

                            action_name=action_name,

                            action_data=action,

                            result=result,

                        )
                    )

                    conversation_coordinator.record_execution(

                        topic=execution_context.topic,

                        task=execution_context.task,

                        application=(
                            execution_context.application
                        ),

                        skill=execution_context.skill,

                        intent=execution_context.intent,

                        action=execution_context.action,

                        object=execution_context.object,

                        objects=execution_context.objects,

                        result=result,

                    )

                    debug_print(
                        "[CONVERSATION EXECUTION]",
                        conversation_coordinator.context.snapshot(),
                    )

                except Exception as e:

                    # * -------------------------------------
                    # ! Natural Conversation must NEVER
                    # * break existing JARVIS execution.
                    # * -------------------------------------

                    print(
                        "[CONVERSATION] "
                        f"Follow-up context update failed: {e}"
                    )

            return            

    # * =====================================================
    # * FAST ROUTE
    # * =====================================================
    #
    # * There are now TWO possible ways to reach here:
    #
    # * 1. Normal dispatch:
    #
    # * dispatch(command)
    #
    # * → dispatcher calculates fast_plan
    #
    # * 2. FAST PREEMPTION:
    #
    # * assistant.py calculates fast_plan
    #
    # * → interrupt()
    #
    # * → dispatch(
    # * command,
    # * fast_plan=fast_plan
    # * )
    #
    # * In case #2 we reuse the existing plan.
    #
    # * This prevents:
    #
    # * fast_route()
    # * fast_route()
    #
    # * for the same command.
    # * =====================================================

    # ! A generic fast-router match must not steal an already-classified
    # * conversational continuation. Action follow-ups that the existing bridge
    # * can execute have already returned above; only unresolved AI follow-ups
    # * are protected here.
    contextual_chat_follow_up = (
        conversation_request is not None
        and conversation_request.relation in {
            "follow_up",
            "continuation",
            "correction",
            "reference",
            "contextual_reference",
        }
        and conversation_request.mode == "conversation"
        and conversation_request.needs_ai
        and not fast_plan
    )

    if not skip_fast and not contextual_chat_follow_up:

        # * -------------------------------------------------
        # * Reuse existing plan if assistant already
        # * calculated it.
        # * -------------------------------------------------

        if fast_plan is None:

            fast_plan = fast_route(
                command
            )

        # * -------------------------------------------------
        # * Execute FAST plan
        # * -------------------------------------------------

        if fast_plan:

            debug_print(
                "[DISPATCHER] "
                "Fast route handled command:",
                {"actions": [
                    item.get("action")
                    for item in fast_plan
                    if isinstance(item, dict)
                ]},
            )

            for action in fast_plan:

                action_name = action.get(
                    "action"
                )

                if not action_name:
                    continue

                live_response_count = len(get_live_responses()) if is_live_execution() else 0
                result = execute(
                    action_name,
                    action,
                )

                if is_live_execution() and result is not False and len(get_live_responses()) == live_response_count:
                    if isinstance(result, str) and result.strip():
                        capture_live_response(result)
                    elif isinstance(result, dict) and result.get("status") != "pending_analysis":
                        message = action_result_message(action_name, action, result)
                        if message:
                            capture_live_response(message)

                debug_print(
                    "[DISPATCHER RESULT]",
                    repr(result),
                )

                if result is not False:
                    app = str(
                        action.get("app")
                        or action.get("process", "")
                    ).strip()
                    if action_name == "open" and app:
                        action_label = f"Opening {app}"
                    elif action_name == "close_process" and app:
                        action_label = f"Closing {app}"
                    else:
                        action_label = action_name.replace("_", " ").title()
                    print(f"[ACTION] {action_label}")
                    print("[STATUS] Done")

                # * =========================================
                # * NATURAL CONVERSATION
                #
                # * Convert the already-executed action into
                # * semantic conversational context.
                #
                # * This does NOT execute anything.
                # * =========================================

                try:

                    execution_context = (
                        execution_context_resolver.resolve(

                            action_name=action_name,

                            action_data=action,

                            result=result,

                        )
                    )

                    conversation_coordinator.record_execution(

                        topic=execution_context.topic,

                        task=execution_context.task,

                        application=(
                            execution_context.application
                        ),

                        skill=execution_context.skill,

                        intent=execution_context.intent,

                        action=execution_context.action,

                        object=execution_context.object,

                        objects=execution_context.objects,

                        result=result,

                    )

                    debug_print(
                        "[CONVERSATION EXECUTION]",
                        conversation_coordinator.context.snapshot(),
                    )

                except Exception as e:

                    # * -------------------------------------
                    # ! Natural Conversation must NEVER
                    # * break existing JARVIS execution.
                    # * -------------------------------------

                    print(
                        "[CONVERSATION] "
                        f"Execution context update failed: {e}"
                    )

                # * -----------------------------------------
                # * Speak skill result
                # * -----------------------------------------
                #
                # * Normal JARVIS:
                # * Skill result -> Edge TTS
                #
                # * Live JARVIS:
                # * Skill result -> Gemini Live
                #
                # ! Gemini Live must remain the only speaker
                # * while a command is being executed through
                # * the Live tool bridge.
                # * -----------------------------------------

                if result is not None:

                    # * =====================================
                    # * LIVE EXECUTION
                    # * =====================================

                    if is_live_execution():

                        print(
                            "[DISPATCHER] "
                            "Live execution detected - "
                            "suppressing normal TTS."
                        )

                    # * =====================================
                    # * NORMAL JARVIS EXECUTION
                    # * =====================================

                    else:

                        from voice.manager import speak

                        # * ---------------------------------
                        # * Boolean result
                        # * ---------------------------------

                        if isinstance(
                            result,
                            bool,
                        ):

                            if action_name == "vision_check":

                                message = (
                                    "Yes, I can see it."
                                    if result
                                    else "No, I don't see it."
                                )

                                speak(
                                    message
                                )

                        # * ---------------------------------
                        # * Dictionary result
                        # * ---------------------------------

                        elif isinstance(
                            result,
                            (dict, str),
                        ):

                            message = action_result_message(
                                action_name,
                                action,
                                result,
                            )

                            if message:
                                speak(message)

                        # * ---------------------------------
                        # * Normal result
                        # * ---------------------------------

                        else:

                            message = action_result_message(
                                action_name,
                                action,
                                result,
                            )

                            if message:
                                speak(message)

            return

    if contextual_chat_follow_up:
        print(
            "[CONVERSATION] Contextual follow-up detected."
        )
        if conversation_request.topic:
            print(
                "[CONVERSATION] Previous topic:",
                conversation_request.topic,
            )

        task_manager.start(
            "chat",
            chat_worker,
            command,
        )

        return

    # * =====================================================
    # * CONTEXT-AWARE GENERIC SEARCH
    # * =====================================================
    #
    # * If the user previously selected a search platform,
    # * a natural "search ..." continuation should inherit
    # * that platform.
    #
    # * Example:
    #
    # * Open YouTube
    # * Search ESP32 weather station
    #
    # * becomes:
    #
    # * youtube_search("ESP32 weather station")
    #
    # * This is shared by voice and Remote Control because
    # * both use the same dispatcher and action memory.
    # * =====================================================

    if (
        not skip_fast
        and command.lower().startswith("search ")
        and "youtube" not in command.lower()
        and "google" not in command.lower()
        and "github" not in command.lower()
        and "chatgpt" not in command.lower()
    ):

        current_site = get_memory(
            "site"
        )

        query = command[
            len("search "):
        ].strip()

        if query:

            # * -------------------------------------------------
            # * YouTube context
            # * -------------------------------------------------

            if current_site == "youtube":

                debug_print(
                    "[ACTION MEMORY] "
                    "Context resolved: YouTube"
                )

                debug_print(
                    "[ACTION MEMORY] "
                    f"YouTube Search: {query}"
                )

                result = execute(
                    "youtube_search",
                    {
                        "action":
                            "youtube_search",
                        "query":
                            query,
                    },
                )

                debug_print(
                    "[ACTION MEMORY RESULT]",
                    repr(result),
                )

                return

            # * -------------------------------------------------
            # * Google context
            # * -------------------------------------------------

            if current_site == "google":

                debug_print(
                    "[ACTION MEMORY] "
                    "Context resolved: Google"
                )

                debug_print(
                    "[ACTION MEMORY] "
                    f"Google Search: {query}"
                )

                result = execute(
                    "google_search",
                    {
                        "action":
                            "google_search",
                        "query":
                            query,
                    },
                )

                debug_print(
                    "[ACTION MEMORY RESULT]",
                    repr(result),
                )

                return

            # * -------------------------------------------------
            # * GitHub context
            # * -------------------------------------------------

            if current_site == "github":

                debug_print(
                    "[ACTION MEMORY] "
                    "Context resolved: GitHub"
                )

                debug_print(
                    "[ACTION MEMORY] "
                    f"GitHub Search: {query}"
                )

                result = execute(
                    "github_search",
                    {
                        "action":
                            "github_search",
                        "query":
                            query,
                    },
                )

                debug_print(
                    "[ACTION MEMORY RESULT]",
                    repr(result),
                )

                return

    # * =====================================================
    # * NATURAL CONVERSATION FOLLOW-UP EXECUTION
    # * =====================================================
    #
    # * Fast routing has already been given priority.
    #
    # * The conversation analysis was already performed
    # * BEFORE FAST ROUTE.
    #
    # * We reuse that analysis here.
    #
    # * Natural Conversation does NOT execute directly.
    # * The normal registry executor remains authoritative.
    # * =====================================================

    try:

        # * -------------------------------------------------
        # * Reuse existing conversation analysis
        # * -------------------------------------------------

        if conversation_analysis is not None:

            follow_up = (
                conversation_analysis.follow_up
            )

            follow_up_plan = (
                followup_execution_bridge.resolve(

                    raw_input=command,

                    follow_up=follow_up,

                )
            )

        else:

            follow_up_plan = None

        # * -------------------------------------------------
        # * Execute resolved follow-up
        # * -------------------------------------------------

        if follow_up_plan:

            print(
                "[CONVERSATION FOLLOW-UP] "
                "Execution plan:",
                follow_up_plan,
            )

            for action in follow_up_plan:

                action_name = action.get(
                    "action"
                )

                if not action_name:
                    continue

                print(
                    "[CONVERSATION FOLLOW-UP] "
                    f"Executing {action_name}"
                )

                result = execute(
                    action_name,
                    action,
                )

                print(
                    "[CONVERSATION FOLLOW-UP RESULT]",
                    repr(result),
                )

                # * -----------------------------------------
                # * Update conversational context
                # * -----------------------------------------

                try:

                    execution_context = (
                        execution_context_resolver.resolve(

                            action_name=action_name,

                            action_data=action,

                            result=result,

                        )
                    )

                    conversation_coordinator.record_execution(

                        topic=execution_context.topic,

                        task=execution_context.task,

                        application=(
                            execution_context.application
                        ),

                        skill=execution_context.skill,

                        intent=execution_context.intent,

                        action=execution_context.action,

                        object=execution_context.object,

                        objects=execution_context.objects,

                        result=result,

                    )

                    debug_print(
                        "[CONVERSATION EXECUTION]",
                        conversation_coordinator.context.snapshot(),
                    )

                except Exception as e:

                    print(
                        "[CONVERSATION] "
                        f"Follow-up context update failed: {e}"
                    )

            return

    except Exception as e:

        # * -------------------------------------------------
        # ! Natural Conversation must NEVER break JARVIS.
        # * -------------------------------------------------

        print(
            "[CONVERSATION] "
            f"Follow-up execution failed safely: {e}"
        )

    # * =====================================================
    # * SCREEN CONTEXT FOLLOW-UP
    # * =====================================================

    if is_screen_followup(
        command
    ):

        print(
            "[SCREEN FOLLOWUP] "
            "Routing request through conversational context."
        )

        task_manager.start(
            "chat",
            chat_worker,
            command,
        )

        return

    # * =====================================================
    # * DEVELOPER INTENT
    # * =====================================================

    mode = detect(
        command
    )

    if mode == "developer":

        from voice.manager import speak

        print(
            "[DEVELOPER] Request detected."
        )

        speak(
            "Developer request received."
        )

        # * -------------------------------------------------
        # * Send directly to Brain Router
        # * -------------------------------------------------

        brain_result = brain_router.route(
            command
        )

        if brain_result.handled:

            print(
                "[BRAIN ROUTER] "
                f"{brain_result.module} "
                "module handled request."
            )

            # * ---------------------------------------------
            # * Developer Result
            # * ---------------------------------------------

            if (
                brain_result.module
                == "developer"
            ):

                result = (
                    brain_result.result
                )

                if result is None:

                    speak(
                        "Developer request completed."
                    )

                    return

                if result.success:

                    # * -------------------------------------
                    # * Developer CREATE result
                    # * -------------------------------------

                    if hasattr(
                        result,
                        "files",
                    ):

                        files = []

                        for file in result.files:

                            path = getattr(
                                file,
                                "path",
                                "",
                            )

                            if (
                                path
                                and path not in files
                            ):

                                files.append(
                                    path
                                )

                        if files:

                            message = (
                                "Developer project "
                                "created successfully. "
                                f"Created {len(files)} files."
                            )

                        else:

                            message = (
                                "Developer project "
                                "created successfully."
                            )

                    # * -------------------------------------
                    # * Developer EDIT result
                    # * -------------------------------------

                    elif hasattr(
                        result,
                        "patches",
                    ):

                        files = []

                        for patch in result.patches:

                            path = getattr(
                                patch,
                                "path",
                                "",
                            )

                            if (
                                path
                                and path not in files
                            ):

                                files.append(
                                    path
                                )

                        if files:

                            if len(files) == 1:

                                message = (
                                    "Developer edit "
                                    "completed. "
                                    f"Modified {files[0]}."
                                )

                            else:

                                message = (
                                    "Developer edit "
                                    "completed. "
                                    f"Modified {len(files)} files."
                                )

                        else:

                            message = (
                                "Developer edit "
                                "completed successfully."
                            )

                    # * -------------------------------------
                    # * Unknown Developer result
                    # * -------------------------------------

                    else:

                        message = (
                            "Developer request "
                            "completed successfully."
                        )

                    print(
                        "[DEVELOPER RESULT]"
                    )

                    print(
                        message
                    )

                    speak(
                        message
                    )

                else:

                    errors = getattr(
                        result,
                        "errors",
                        [],
                    )

                    print(
                        "[DEVELOPER ERROR]"
                    )

                    for error in errors:

                        print(
                            error
                        )

                    speak(
                        "The Developer request failed."
                    )

                return

        # * ---------------------------------------------
        # * Developer request detected but not handled
        # * ---------------------------------------------

        print(
            "[DEVELOPER] "
            "Request was not handled."
        )

        speak(
            "I received the Developer request, "
            "but I could not execute it."
        )

        return
    
    # * =====================================================
    # * ACTION MEMORY
    # * =====================================================

    # * Only the existing rule-based explicit-memory recognizer belongs in the
    # ! dispatcher. Broad AI memory extraction must not consume normal commands
    # * before the planner gets a chance to route or clarify them.
    memory_result = learn_explicit_memory(
        command
    )

    # * =====================================================
    # * MEMORY SAVED
    # * =====================================================

    if memory_result.get(
        "saved"
    ):

        debug_print(
            f"[MEMORY] Saved -> "
            f"{memory_result['key']} = "
            f"{memory_result['value']}"
        )

        from voice.manager import speak

        if memory_result.get(
            "updated"
        ):

            speak(
                f"I've updated your "
                f"{memory_result['key']}."
            )

        else:

            speak(
                "I'll remember that."
            )

        return

    # * =====================================================
    # * ALREADY KNOWN
    # * =====================================================

    if memory_result.get(
        "already_known"
    ):

        from voice.manager import speak

        debug_print(
            "[MEMORY] Already known."
        )

        speak(
            "I already knew that."
        )

        return

    # * =====================================================
    # * SHOW STORED MEMORIES
    # * =====================================================

    MEMORY_VIEW_COMMANDS = (

        "show my memories",
        "list my memories",
        "show all memories",
        "what do you know about me",
        "show everything you know",

    )

    if command in MEMORY_VIEW_COMMANDS:

        from voice.manager import speak

        result = show_all()

        print(
            "\n[MEMORY VIEW]\n"
        )

        print(
            result
        )

        speak(
            result
        )

        return

    # * =====================================================
    # * USER PROFILE
    # * =====================================================

    PROFILE_COMMANDS = (

        "show my profile",
        "my profile",
        "user profile",
        "profile",
        "summarize me",
        "summarize my profile",

    )

    if command in PROFILE_COMMANDS:

        from voice.manager import speak

        profile = profile_summary()

        print(
            "\n[USER PROFILE]\n"
        )

        print(
            profile
        )

        speak(
            profile
        )

        return

    # * =====================================================
    # * MEMORY STATISTICS
    # * =====================================================

    MEMORY_STATS_COMMANDS = (

        "memory statistics",
        "memory stats",
        "show memory statistics",
        "how many memories do you have",
        "how many things do you remember",

    )

    if command in MEMORY_STATS_COMMANDS:

        from voice.manager import speak

        count = total()

        categories = by_category()

        text = (
            f"I currently remember "
            f"{count} thing"
        )

        if count != 1:

            text += "s"

        text += ".\n"

        for category, value in categories.items():

            text += (
                f"\n{category.title()} : {value}"
            )

        print(
            "\n[MEMORY STATS]\n"
        )

        print(
            text
        )

        speak(
            text
        )

        return

    # * =====================================================
    # * FORGET MEMORY
    # * =====================================================

    forget_result = memory_forget(
        command
    )

    if forget_result:

        from voice.manager import speak

        print(
            "\n[MEMORY FORGET]\n"
        )

        print(
            forget_result
        )

        if (
            forget_result["type"]
            == "key"
        ):

            message = (
                f"I forgot your "
                f"{forget_result['key']}."
            )

        elif (
            forget_result["type"]
            == "category"
        ):

            deleted = len(
                forget_result["deleted"]
            )

            message = (
                f"I forgot "
                f"{deleted} "
                f"memories from "
                f"{forget_result['category']}."
            )

        else:

            deleted = len(
                forget_result["deleted"]
            )

            message = (
                f"I forgot "
                f"{deleted} memories."
            )

        speak(
            message
        )

        return

    # * =====================================================
    # * PENDING SEARCH SUBJECT
    # * =====================================================

    pending = get_memory(
        "pending_subject"
    )

    if (
        pending
        and command.startswith("search on")
    ):

        platform = (
            command
            .replace(
                "search on",
                "",
                1,
            )
            .strip()
        )

        print(
            "[PENDING SUBJECT]",
            pending,
        )

        if platform == "youtube":

            execute_ai_plan(
                [
                    {
                        "action": "youtube_search",
                        "query": pending,
                    }
                ],
                task_manager.event(
                    "planner"
                ),
            )

            set_memory(
                "pending_subject",
                None,
            )

            return

        elif platform == "google":

            execute_ai_plan(
                [
                    {
                        "action": "google_search",
                        "query": pending,
                    }
                ],
                task_manager.event(
                    "planner"
                ),
            )

            set_memory(
                "pending_subject",
                None,
            )

            return

        elif platform == "github":

            execute_ai_plan(
                [
                    {
                        "action": "github_search",
                        "query": pending,
                    }
                ],
                task_manager.event(
                    "planner"
                ),
            )

            set_memory(
                "pending_subject",
                None,
            )

            return
        
    # * =====================================================
    # * AGENT FALLBACK BARRIER
    # * =====================================================
    #
    # * When Gemini Live invokes jarvis_command, JARVIS
    # ! skills must still execute through this dispatcher.
    #
    # * However, if no JARVIS skill/action handled the
    # ! command, NEVER fall through into the normal AI
    # * worker while Agent is active.
    #
    # * Gemini Live remains the conversational speaker.
    # * =====================================================

    if is_live_execution():

        print(
            "[DISPATCHER] Live execution active - "
            f"no {get_assistant_display_name()} skill handled command; "
            "suppressing normal AI fallback."
        )

        return False

    
    # * =====================================================
    # * EXISTING CHAT / PLANNER
    # * =====================================================

    mode = detect(
        command
    )

    # ! A context-aware conversational request must reach the existing chat
    # * worker even when the generic intent engine does not recognize a short
    # * phrase such as "Give me an example" as a chat prefix.
    if (
        conversation_request is not None
        and conversation_request.mode == "conversation"
        and conversation_request.needs_ai
    ):
        mode = "chat"

    # * -----------------------------------------------------
    # * Continue conversation
    # * -----------------------------------------------------

    if get_value(
        "chat_mode"
    ):

        mode = "chat"

    # * -----------------------------------------------------
    # * Chat
    # * -----------------------------------------------------

    if mode == "chat":

        task_manager.start(
            "chat",
            chat_worker,
            command,
        )

    # * -----------------------------------------------------
    # * Planner
    # * -----------------------------------------------------

    else:

        task_manager.start(
            "planner",
            planner_worker,
            command,
        )

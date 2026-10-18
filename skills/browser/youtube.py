from core.registry import register
from voice.manager import speak

from core.live_execution import is_live_execution

from skills.browser.browser_controller import browser
from config.youtube import get_first_video
from config.youtube import get_video_list

from core.browser_context import browser_context

import threading

youtube_queue = []
youtube_index = -1
current_youtube_query = ""

# * =====================================================
# * YouTube Search
# * =====================================================

def ai_youtube(data):

    global current_youtube_query
    global youtube_queue
    global youtube_index

    query = data.get("query", "").strip()

    if not query:
        return False

    current_youtube_query = query

    if not is_live_execution():
        speak(
            f"Searching YouTube for {query}"
        )

    # * -------------------------------------------------
    # * Open YouTube search page
    # * -------------------------------------------------

    opened = browser.search_youtube(query)
    if not opened:
        print(f"[YouTube] Search navigation failed for: {query}")
        return {
            "ok": False,
            "status": "failed",
            "action": "youtube_search",
            "query": query,
            "platform": "youtube",
            "results": [],
            "result_count": 0,
            "message": "YouTube search navigation failed.",
        }

    # * -------------------------------------------------
    # * Capture search results for NCI
    #
    # ! This is important:
    #
    # * "play the second one"
    #
    # ! must have actual YouTube result objects
    # * available to ReferenceResolver.
    # * -------------------------------------------------

    videos = get_video_list(
        query,
        10
    )

    if not videos:
        browser_context.set_search(query=query, platform="youtube", results=[])
        browser_context.set_youtube_queue(query=query, videos=[])
        youtube_queue = []
        youtube_index = -1
        return {
            "ok": True,
            "status": "empty_results",
            "action": "youtube_search",
            "query": query,
            "platform": "youtube",
            "results": [],
            "result_count": 0,
            "message": f"YouTube returned no results for {query}.",
        }

    # * -------------------------------------------------
    # * Store generic browser search context
    # * -------------------------------------------------

    browser_context.set_search(
        query=query,
        platform="youtube",
        results=videos,
    )

    # * -------------------------------------------------
    # * Store YouTube-specific queue
    # * -------------------------------------------------

    browser_context.set_youtube_queue(
        query=query,
        videos=videos,
    )

    # * -------------------------------------------------
    # * Keep existing YouTube runtime queue synchronized
    # * -------------------------------------------------

    youtube_queue = videos

    youtube_index = (
        0
        if videos
        else -1
    )

    # * -------------------------------------------------
    # * Record successful YouTube search for NCI
    #
    # * This connects the existing BrowserContext result
    # * list to ConversationContext.
    #
    # * It allows:
    #
    # * "play the second one"
    # * "play the third one"
    # * "open the first one"
    #
    # * to resolve against the actual YouTube results.
    # * -------------------------------------------------

    try:

        from brain.conversation_coordinator import (
            conversation_coordinator,
        )

        from brain.execution_context import (
            execution_context_resolver,
        )

        execution_context = (
            execution_context_resolver.resolve(
                action_name="youtube_search",
                action_data={
                    "query": query,
                },
                result=True,
            )
        )

        conversation_coordinator.record_execution(

            topic=execution_context.topic,

            task=execution_context.task,

            application=execution_context.application,

            skill=execution_context.skill,

            intent=execution_context.intent,

            action=execution_context.action,

            object=execution_context.object,

            objects=execution_context.objects,

            result=True,

        )

        print(
            "[YOUTUBE CONVERSATION] "
            "Search context recorded."
        )

    except Exception as e:

        print(
            "[YOUTUBE CONVERSATION] "
            f"Context update failed safely: {e}"
        )

    snapshot = browser_context.search_snapshot()
    return {
        "ok": True,
        "status": "success",
        "action": "youtube_search",
        "query": query,
        "platform": "youtube",
        "results": snapshot["results"],
        "result_count": len(snapshot["results"]),
        "message": f"YouTube search returned {len(snapshot['results'])} result(s) for {query}.",
    }


# * =====================================================
# * YouTube Controls
# * =====================================================

def _playback_result(action, result, message, **extra):
    return {
        "ok": bool(result),
        "status": "completed" if result else "failed",
        "action": action,
        "message": message if result else "YouTube navigation failed.",
        "playback_state_verified": False,
        **extra,
    }

def youtube_play_first(data):
    
    print(
        f"[YouTube THREAD] "
        f"{threading.current_thread().name} | "
        f"ID: {threading.get_ident()}"
    )

    global youtube_queue, youtube_index, current_youtube_query

    query = data.get("query", "").strip()

    # * Use the previous YouTube search if no new query was supplied
    if not query:
        query = current_youtube_query

    if not query:
        speak("What should I play on YouTube?")
        return False

    if not is_live_execution():
        speak(f"Finding YouTube videos for {query}")

    videos = get_video_list(query, 10)

    if not videos:
        speak("I could not find YouTube videos.")
        return False
    
    # * Save YouTube search results to browser context
    browser_context.set_search(
        query=query,
        platform="youtube",
        results=videos,
    )

    browser_context.set_youtube_queue(
        query=query,
        videos=videos,
    )

    # * Save search results as JARVIS queue
    youtube_queue = videos
    youtube_index = 0

    video = youtube_queue[youtube_index]
    
    browser_context.set_current_youtube(
        youtube_index
    )

    print(f"[YouTube Queue] Loaded {len(youtube_queue)} videos")
    print(f"[YouTube Queue] Position: {youtube_index + 1}")
    print(f"[YouTube API] Playing: {video['title']}")
    print(f"[YouTube API] Video ID: {video['video_id']}")

    if not is_live_execution():
        speak(f"Playing {video['title']}")

    result = browser.play_video(video["video_id"])
    return _playback_result(
        "youtube_play_first",
        result,
        f"YouTube navigation sent for {video['title']}; playback state was not verified.",
        video_id=video["video_id"],
    )


def youtube_pause(data):
    result = browser.pause_video()
    if not is_live_execution():
        speak("YouTube is paused." if result else "I couldn't pause YouTube.")
    return {
        "ok": bool(result),
        "status": "completed" if result else "failed",
        "action": "youtube_pause",
        "message": "YouTube is paused." if result else "I couldn't pause YouTube.",
        "playback_state_verified": bool(result),
    }


def youtube_resume(data):
    result = browser.resume_video()
    if not is_live_execution():
        speak("YouTube is playing." if result else "I couldn't resume YouTube.")
    return {
        "ok": bool(result),
        "status": "completed" if result else "failed",
        "action": "youtube_resume",
        "message": "YouTube is playing." if result else "I couldn't resume YouTube.",
        "playback_state_verified": bool(result),
    }


def youtube_next(data):

    global youtube_queue, youtube_index

    if not youtube_queue:
        speak("There is no YouTube queue.")
        return False

    # * Move to next video
    if youtube_index + 1 >= len(youtube_queue):
        speak("There are no more videos in the queue.")
        return False

    youtube_index += 1
    
    browser_context.set_current_youtube(
        youtube_index
    )

    video = youtube_queue[youtube_index]

    print(f"[YouTube Queue] Position: {youtube_index + 1}/{len(youtube_queue)}")
    print(f"[YouTube Queue] Playing: {video['title']}")
    print(f"[YouTube API] Video ID: {video['video_id']}")

    if not is_live_execution():
        speak(f"Playing {video['title']}")

    result = browser.play_video(video["video_id"])
    return _playback_result(
        "youtube_next",
        result,
        f"YouTube navigation sent for {video['title']}; playback state was not verified.",
        video_id=video["video_id"],
    )


def youtube_previous(data):

    global youtube_queue, youtube_index

    if not youtube_queue:
        speak("There is no YouTube queue.")
        return False

    # * Move to previous video
    if youtube_index <= 0:
        speak("This is the first video in the queue.")
        return False

    youtube_index -= 1

    browser_context.set_current_youtube(
        youtube_index
    )

    video = youtube_queue[youtube_index]

    print(
        f"[YouTube Queue] Position: "
        f"{youtube_index + 1}/{len(youtube_queue)}"
    )

    print(
        f"[YouTube Queue] Playing: "
        f"{video['title']}"
    )

    print(
        f"[YouTube API] Video ID: "
        f"{video['video_id']}"
    )

    if not is_live_execution():
        speak(f"Playing {video['title']}")

    result = browser.play_video(video["video_id"])
    return _playback_result(
        "youtube_previous",
        result,
        f"YouTube navigation sent for {video['title']}; playback state was not verified.",
        video_id=video["video_id"],
    )

def youtube_play_result(data):

    video_id = (
        data.get("video_id", "")
        or ""
    ).strip()

    if not video_id:
        return False

    # * =====================================================
    # * Synchronize BrowserContext with the requested video
    # * =====================================================

    video = None

    for index, queued_video in enumerate(
        browser_context.youtube_queue
    ):

        queued_video_id = (
            queued_video.data.get(
                "video_id",
                ""
            )
            if queued_video.data
            else ""
        )

        if queued_video_id == video_id:

            video = (
                browser_context.set_current_youtube(
                    index
                )
            )

            break

    # * =====================================================
    # * Speak the actual video being played
    # * =====================================================

    if video is not None:

        title = getattr(
            video,
            "title",
            ""
        )

        if title and not is_live_execution():

            speak(
                f"Playing {title}"
            )

    # * =====================================================
    # * Play
    # * =====================================================

    result = browser.play_video(video_id)
    return _playback_result(
        "youtube_play_result",
        result,
        "YouTube navigation sent; playback state was not verified.",
        video_id=video_id,
    )


# * =====================================================
# * Registry
# * =====================================================

register("youtube_search", ai_youtube)

register("youtube_play_first", youtube_play_first)

register("youtube_pause", youtube_pause)

register("youtube_resume", youtube_resume)

register("youtube_next", youtube_next)

register("youtube_previous", youtube_previous)

register("youtube_play_result",youtube_play_result)

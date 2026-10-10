import json

from ai.core.service import ai_service


def fallback(step):

    prompt = f"""
This action is unsupported.

{json.dumps(step)}

Convert it into supported actions.

Supported:

open
youtube_search
google_search
play
volume
remember
recall
clarify

Return ONLY JSON.
"""

    response = ai_service.generate(
        prompt=prompt,
        capability="conversation",
    )

    if not response.success:

        print(
            "[FALLBACK AI] Generation failed:",
            response.error,
        )

        return ""

    print(
        "[FALLBACK AI] Provider:",
        response.provider,
    )

    print(
        "[FALLBACK AI] Model:",
        response.model,
    )

    return response.text
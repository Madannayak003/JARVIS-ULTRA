"""
JARVIS PRO Image Generation Skill

Generates images from natural-language prompts using
Pollinations AI.

This skill is independent from the standalone AI Chatbot.
"""

import time
from pathlib import Path
from urllib.parse import quote

import requests

from core.registry import register
from voice.manager import speak


# * =============================================================
# * IMAGE CONFIGURATION
# * =============================================================

IMAGE_BASE_URL = (
    "https://image.pollinations.ai/prompt/"
)

# * Pollinations image model.
# * Keep this simple for now and use the same endpoint
# * style as the working test supplied for this skill.
DEFAULT_IMAGE_MODEL = "flux"


IMAGE_OUTPUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "generated_images"
)


# * =============================================================
# * IMAGE GENERATION
# * =============================================================

def create_image(data=None):
    """
    Create an image from a text prompt.

    Expected data:

        {
            "prompt": "a futuristic city at night"
        }
    """

    data = data or {}

    prompt = str(
        data.get("prompt", "")
    ).strip()

    # * ---------------------------------------------------------
    # * Validate prompt
    # * ---------------------------------------------------------

    if not prompt:

        speak(
            "Please tell me what image you want me to create."
        )

        return False

    print(
        f"[IMAGE] Image generation requested: {prompt}"
    )

    # * ---------------------------------------------------------
    # * Output directory
    # * ---------------------------------------------------------

    try:

        IMAGE_OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

    except Exception as exc:

        print(
            f"[IMAGE] Failed to create output directory: {exc}"
        )

        speak(
            "I could not prepare the image output folder."
        )

        return False

    # * ---------------------------------------------------------
    # * Build Pollinations URL
    # * ---------------------------------------------------------

    try:

        encoded_prompt = quote(
            prompt,
            safe=""
        )

        url = (
            f"{IMAGE_BASE_URL}"
            f"{encoded_prompt}"
        )

        print(
            f"[IMAGE] Pollinations URL: {url}"
        )

        # * -----------------------------------------------------
        # * Generate image
        # * -----------------------------------------------------

        response = requests.get(
            url,
            timeout=60,
        )

        print(
            f"[IMAGE] Status code: {response.status_code}"
        )

        print(
            f"[IMAGE] Content type: "
            f"{response.headers.get('content-type')}"
        )

        print(
            f"[IMAGE] Content length: "
            f"{len(response.content)}"
        )

        response.raise_for_status()

        # * -----------------------------------------------------
        # * Validate returned data
        # * -----------------------------------------------------

        content_type = (
            response.headers
            .get("content-type", "")
            .lower()
        )

        if not content_type.startswith("image/"):

            print(
                "[IMAGE] Pollinations did not return "
                "an image."
            )

            speak(
                "The image service did not return a valid image."
            )

            return False

        if not response.content:

            print(
                "[IMAGE] Pollinations returned empty data."
            )

            speak(
                "The image service returned an empty image."
            )

            return False

        # * -----------------------------------------------------
        # * Save image
        # * -----------------------------------------------------

        timestamp = int(
            time.time()
        )

        extension = "jpg"

        if "png" in content_type:
            extension = "png"

        elif "webp" in content_type:
            extension = "webp"

        elif "jpeg" in content_type:
            extension = "jpg"

        filename = (
            f"jarvis_image_{timestamp}"
            f".{extension}"
        )

        output_path = (
            IMAGE_OUTPUT_DIR
            / filename
        )

        output_path.write_bytes(
            response.content
        )

        print(
            f"[IMAGE] Image saved: {output_path}"
        )

        # * -----------------------------------------------------
        # * JARVIS response
        # * -----------------------------------------------------

        speak(
            "The image has been created successfully."
        )

        return (
            f"Image created successfully. "
            f"Saved to: {output_path}"
        )

    # * ---------------------------------------------------------
    # ! HTTP errors
    # * ---------------------------------------------------------

    except requests.exceptions.Timeout:

        print(
            "[IMAGE] Pollinations request timed out."
        )

        speak(
            "The image generation request timed out."
        )

        return False

    except requests.exceptions.HTTPError as exc:

        print(
            f"[IMAGE] Pollinations HTTP error: {exc}"
        )

        status_code = (
            exc.response.status_code
            if exc.response is not None
            else None
        )

        if status_code == 429:

            speak(
                "The image service is currently rate limited."
            )

        elif status_code in (401, 403):

            speak(
                "The image service requires valid access."
            )

        elif status_code == 503:

            speak(
                "The image service is temporarily unavailable."
            )

        else:

            speak(
                "The image service returned an error."
            )

        return False

    # * ---------------------------------------------------------
    # ! Network / runtime errors
    # * ---------------------------------------------------------

    except requests.exceptions.RequestException as exc:

        print(
            f"[IMAGE] Pollinations request failed: {exc}"
        )

        speak(
            "I could not connect to the image generation service."
        )

        return False

    except Exception as exc:

        print(
            f"[IMAGE] Generation failed: {exc}"
        )

        speak(
            "I could not create that image."
        )

        return False


# * =============================================================
# * REGISTRATION
# * =============================================================

register(
    "create_image",
    create_image,
)
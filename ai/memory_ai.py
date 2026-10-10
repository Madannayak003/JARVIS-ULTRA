"""
JARVIS PRO
AI Memory Extraction

Stage 2B

Responsibilities
----------------
✓ Learn from natural language
✓ Extract permanent personal facts
✓ Return structured JSON
✓ Never save directly
"""

import json

# * from ai.ollama import ask_ollama

from ai.core.service import ai_service


SYSTEM_PROMPT = """
You are a memory extraction engine.

Your task is to detect permanent personal information.

Examples of permanent facts:

- Name
- Birthday
- College
- University
- School
- Email
- Phone
- Occupation
- Address
- City
- Country
- Favorite programming language
- Favorite editor
- Operating system
- Laptop
- Project
- Company

Ignore:

- Temporary events
- Weather
- Current mood
- Questions
- Commands
- General conversation

Return ONLY valid JSON.

If nothing should be remembered return:

{
    "remember": false
}

Otherwise return:

{
    "remember": true,
    "key": "...",
    "value": "...",
    "category": "...",
    "keywords": "...",
    "importance": 3
}
"""


def extract_memory(text):
    """
    Ask the configured AI provider whether this sentence
    contains a permanent personal fact.
    """

    prompt = f"""
User sentence:

{text}

Extract one memory if appropriate.

Return ONLY JSON.
"""

    try:
        
        ai_response = ai_service.generate(

            prompt=prompt,

            system_prompt=SYSTEM_PROMPT,

            capability="memory",

        )

        if not ai_response.success:

            print(
                "[MEMORY AI ERROR]",
                ai_response.error
            )

            return None

        response = ai_response.text.strip()

        # * Remove markdown if model adds it
        if response.startswith("```"):
            response = (
                response
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

        data = json.loads(response)

        if not isinstance(data, dict):
            return None

        return normalize(data)

    except Exception as e:

        print("[MEMORY AI]", e)

        return None
    
# * ---------------------------------------
# * Normalize AI Output
# * ---------------------------------------

KEY_MAP = {

    "name": "name",

    "full name": "name",
    
    "birthday": "birthday",

    "date_of_birth": "birthday",

    "date of birth": "birthday",

    "birth date": "birthday",

    "dob": "birthday",

    "college": "college",

    "university": "college",

    "school": "college",

    "email": "email",

    "email address": "email",

    "phone": "phone",

    "mobile": "phone",

    "mobile number": "phone",

    "operating system": "os",

    "os": "os",

    "windows": "os",

    "laptop": "laptop",

    "computer": "laptop",

    "pc": "laptop",

    "project": "project",

    "favorite language": "favorite_language",

    "programming language": "favorite_language",

    "language": "favorite_language"

}


CATEGORY_MAP = {

    "identity": "identity",

    "education": "education",

    "technology": "device",

    "device": "device",

    "laptop": "device",  # * <-- add

    "computer": "device",  # * <-- add

    "hardware": "device",  # * <-- add

    "email": "contact",

    "contact": "contact",

    "personal": "personal",

    "project": "project"
}


def normalize(data):

    if not data:

        return None

    if not data.get("remember"):

        return data

    key = data.get("key", "").lower().strip()

    category = data.get("category", "").lower().strip()

    data["key"] = KEY_MAP.get(key, key)

    data["category"] = CATEGORY_MAP.get(category, "other")

    data["keywords"] = ",".join(

        word.strip().lower()

        for word in

        data.get("keywords", "").split(",")

        if word.strip()

    )
    
    
    # * ---------------------------------------
    # * Reject Empty Values
    # * ---------------------------------------

    value = str(

        data.get("value", "")

    ).strip()

    BAD_VALUES = {

        "",

        "unknown",

        "none",

        "null",

        "n/a",

        "not provided"

    }

    if value.lower() in BAD_VALUES:

        return {

            "remember": False

        }

    data["value"] = value
    

    return data
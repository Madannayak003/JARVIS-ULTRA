"""
JARVIS PRO
Developer Workspace

Project Name Resolver
"""

import re
from pathlib import Path

from brain.developer.generator.models.generated_project import (
    GeneratedProject,
)


class ProjectNameResolver:
    """
    Generates a clean, concise, unique project name.

    The resolver intentionally uses deterministic local rules so
    project folder names do not depend on AI-generated verbose names.
    """

    DEFAULT_NAME = "GeneratedProject"

    SPECIAL_WORDS = {
        "ai": "AI",
        "ecommerce": "ECommerce",
        "rfid": "RFID",
        "iot": "IoT",
        "api": "API",
        "gps": "GPS",
        "gsm": "GSM",
        "wifi": "WiFi",
        "bluetooth": "Bluetooth",
        "esp32": "ESP32",
        "esp8266": "ESP8266",
        "arduino": "Arduino",
        "mqtt": "MQTT",
        "http": "HTTP",
        "https": "HTTPS",
        "oled": "OLED",
        "lcd": "LCD",
        "i2c": "I2C",
        "spi": "SPI",
        "uart": "UART",
        "usb": "USB",
        "json": "JSON",
        "html": "HTML",
        "css": "CSS",
        "javascript": "JavaScript",
        "python": "Python",
        "cpp": "CPP",
        "c++": "CPP",
    }

    TECHNOLOGY_WORDS = set(SPECIAL_WORDS)
    LANGUAGE_WORDS = {
        "python",
        "javascript",
        "typescript",
        "cpp",
        "c++",
        "c",
    }

    # Words that describe the command rather than the project itself.
    COMMAND_WORDS = {
        "create",
        "build",
        "generate",
        "make",
        "develop",
        "design",
        "write",
        "developing",
        "creating",
        "building",
    }

    # Generic words that should not normally appear in a folder name.
    GENERIC_WORDS = {
        "a",
        "an",
        "the",
        "project",
        "application",
        "app",
        "program",
        "software",
        "system",
        "solution",
        "tool",
        "website",
        "web",
        "site",
        "script",
        "solution",
    }

    # Implementation/detail words that commonly make names unnecessarily long.
    DETAIL_WORDS = {
        "using",
        "use",
        "with",
        "without",
        "including",
        "include",
        "based",
        "built",
        "support",
        "supports",
        "feature",
        "features",
        "for",
        "and",
        "or",
        "to",
        "of",
        "in",
        "on",
        "from",
        "that",
        "which",
        "this",
        "these",
        "those",
        "modern",
        "responsive",
        "simple",
        "basic",
        "advanced",
        "powered",
        "power",
        "ui",
        "ux",
        "mode",
        "modes",
        "animation",
        "animations",
        "chart",
        "charts",
        "notification",
        "notifications",
        "animated",
        "dark",
        "light",
        "location",
        "search",
        "filter",
        "filters",
    }

    # Detailed implementation phrases that should not become folder names.
    DETAIL_PHRASES = (
        r"\busing\s+html\b",
        r"\busing\s+css\b",
        r"\busing\s+javascript\b",
        r"\bhtml\s+css\s+javascript\b",
        r"\bhtml\s+css\s+js\b",
        r"\bwith\s+dark\s+mode\b",
        r"\bwith\s+light\s+mode\b",
        r"\bwith\s+responsive\s+design\b",
        r"\bwith\s+modern\s+ui\b",
        r"\bwith\s+modern\s+responsive\s+ui\b",
        r"\bai[\s-]+powered\b",
        r"\baddition\s*,?\s*subtraction\s*,?\s*multiplication\s*(?:and\s*)?division\b",
        r"\baddition\s+subtraction\s+multiplication\s+division\b",
    )

    # Common operation/detail words that are useful in the request but
    # unnecessary in a concise project folder name.
    OPERATION_WORDS = {
        "addition",
        "subtraction",
        "multiplication",
        "division",
        "calculation",
    }

    # Keep important project nouns while limiting excessive description.
    PROJECT_NOUNS = {
        "calculator",
        "portfolio",
        "dashboard",
        "parking",
        "attendance",
        "chatbot",
        "assistant",
        "automation",
        "robot",
        "robotics",
        "weather",
        "music",
        "player",
        "inventory",
        "billing",
        "login",
        "authentication",
        "booking",
        "ecommerce",
        "shop",
        "store",
        "blog",
        "camera",
        "vision",
        "monitor",
        "tracker",
        "manager",
        "management",
        "system",
        "website",
        "app",
    }

    def resolve(
        self,
        project: GeneratedProject,
        output_directory: Path,
    ) -> str:
        """
        Resolve a clean and unique project folder name.
        """

        # -------------------------------------------------
        # Arduino / ESP sketches
        # -------------------------------------------------
        #
        # Arduino requires the folder name and .ino filename
        # to match. Preserve the actual .ino filename exactly.
        #
        ino_name = self._get_ino_name(project)

        if ino_name:
            base_name = ino_name

        else:
            # -------------------------------------------------
            # Always derive normal project names from the
            # original user request instead of trusting a
            # potentially verbose AI-generated project.name.
            # -------------------------------------------------

            text = (project.user_request or "").strip()

            if not text:
                text = (project.name or "").strip()

            base_name = self._build_clean_name(
                text,
                project,
            )

        if not base_name:
            base_name = self.DEFAULT_NAME

        # -------------------------------------------------
        # Unique Folder Name
        # -------------------------------------------------

        candidate = base_name
        counter = 1

        while (output_directory / candidate).exists():
            candidate = f"{base_name}_{counter}"
            counter += 1

        return candidate

    # -----------------------------------------------------
    # Arduino Helper
    # -----------------------------------------------------

    @staticmethod
    def _get_ino_name(project: GeneratedProject) -> str:
        """
        Return the first .ino filename stem.

        This preserves Arduino's required sketch/folder
        naming relationship.
        """

        for generated_file in project.files:
            path = str(generated_file.path).replace("\\", "/")

            if path.lower().endswith(".ino"):
                return Path(path).stem

        return ""

    # -----------------------------------------------------
    # Clean Project Name
    # -----------------------------------------------------

    def _build_clean_name(
        self,
        text: str,
        project: GeneratedProject,
    ) -> str:
        """
        Convert a natural-language request into a concise
        PascalCase project name.
        """

        explicit_name = self._explicit_name(text)

        if explicit_name:
            return self._format_name(explicit_name.split())

        # Remove implementation/detail phrases first.
        for pattern in self.DETAIL_PHRASES:
            text = re.sub(
                pattern,
                " ",
                text,
                flags=re.IGNORECASE,
            )

        # Normalize punctuation.
        text = re.sub(r"\be[\s-]+commerce\b", "ecommerce", text, flags=re.IGNORECASE)
        text = re.sub(
            r"[^A-Za-z0-9+# ]",
            " ",
            text,
        )

        words = re.findall(r"[A-Za-z0-9]+(?:\+\+)?", text)
        lowered = [word.lower() for word in words]
        using_index = next(
            (index for index, key in enumerate(lowered) if key in {"using", "with"}),
            len(words),
        )

        candidates = []
        seen = set()
        technology = []

        for index, word in enumerate(words):
            key = word.lower()

            if (
                key in self.COMMAND_WORDS
                or key in self.GENERIC_WORDS
                or key in self.DETAIL_WORDS
                or key in self.OPERATION_WORDS
                or len(key) <= 2
            ):
                continue

            if key in seen:
                continue

            if key in self.TECHNOLOGY_WORDS:
                technology.append((index, word))
                # Markup/language details after "using" are implementation,
                # while leading or hardware technologies can identify a project.
                if index > using_index:
                    continue
                if key in {"html", "css", "javascript", "json", "http", "https"}:
                    continue

            seen.add(key)
            candidates.append((index, word))

        # A request can contain a long feature list. Keep the first coherent
        # concept and at most four meaningful words in its original order.
        if len(candidates) > 4:
            candidates = candidates[:4]

        result_words = [word for _, word in candidates]

        # Metadata can supply a language when the request explicitly used it
        # as the project identity, e.g. "Python calculator". Do not prefix
        # every project with its implementation language.
        language = str(getattr(project, "language", "") or "").lower()
        language_name = next(
            (
                canonical
                for key, canonical in self.SPECIAL_WORDS.items()
                if key in self.LANGUAGE_WORDS and key in language
            ),
            "",
        )
        if language_name and result_words:
            first_key = result_words[0].lower()
            if first_key in self.LANGUAGE_WORDS and first_key not in seen:
                result_words.insert(0, language_name)

        # If all descriptive content was filtered, retain a technology name
        # rather than inventing one.
        if not result_words and technology:
            result_words = [technology[0][1]]

        return self._format_name(result_words)

    @staticmethod
    def _explicit_name(text: str) -> str:
        """Return a user-supplied project name when one is clearly labelled."""

        quoted = re.search(
            r"\b(?:called|named|name(?:d)?)\s+(?:[\"']([^\"']+)[\"']|([A-Za-z0-9_]+))",
            text,
            flags=re.IGNORECASE,
        )
        if quoted:
            return (quoted.group(1) or quoted.group(2)).strip()

        quoted_project = re.search(
            r"\bproject\s+[\"']([^\"']+)[\"']",
            text,
            flags=re.IGNORECASE,
        )
        if quoted_project:
            return quoted_project.group(1).strip()

        return ""

    def _format_name(self, words: list[str]) -> str:
        """Format ordered, already-selected words as a safe PascalCase name."""

        parts = []
        seen = set()

        for word in words:
            key = re.sub(r"[^a-z0-9]+", "", word.lower())
            if not key or key in seen:
                continue
            seen.add(key)

            special = self.SPECIAL_WORDS.get(key)
            if special:
                parts.append(special)
            elif word.isupper() and len(word) <= 5:
                parts.append(word)
            else:
                parts.append(word[:1].upper() + word[1:])

        name = re.sub(r"[^A-Za-z0-9_]+", "", "".join(parts))
        name = name.strip(" .")
        return name or self.DEFAULT_NAME

from pathlib import Path
import shutil
import re
import sys


# ============================================================
# JARVIS PRO — PROJECT-WIDE BETTER COMMENTS FORMATTER
# ============================================================

# The folder containing this script is treated as the project root.
PROJECT_ROOT = Path(__file__).resolve().parent

# Create backups before modifying files.
CREATE_BACKUPS = False

# Files that should NEVER be touched.
EXCLUDED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".next",
    "dist",
    "build",
    "out",
    "target",
    ".gradle",
    ".idea",
    ".vscode",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
}

# Source/documentation files where comment formatting makes sense.
SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cc",
    ".cs",
    ".go",
    ".rs",
    ".php",
    ".swift",
    ".kt",
    ".kts",
    ".dart",
    ".ino",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".html",
    ".htm",
    ".vue",
    ".sql",
    ".sh",
    ".bat",
    ".cmd",
    ".ps1",
}

# Files that should never be modified.
EXCLUDED_FILES = {
    "format_project_comments.py",
}


# ============================================================
# COMMENT CLASSIFICATION
# ============================================================

IMPORTANT_WORDS = {
    "IMPORTANT",
    "CRITICAL",
    "WARNING",
    "SECURITY",
    "ERROR",
    "DANGER",
    "MUST",
    "DO NOT",
    "DON'T",
    "NEVER",
    "REQUIRED",
    "CAUTION",
    "FIXME",
    "BUG",
    "BROKEN",
}

INFORMATION_WORDS = {
    "INFO",
    "INFORMATION",
    "NOTE",
    "DETAIL",
    "EXPLANATION",
    "JARVIS",
    "CONFIG",
    "CONFIGURATION",
    "SETUP",
    "CORE",
    "API",
    "DATABASE",
    "MODULE",
    "FUNCTION",
    "CLASS",
}


# ============================================================
# DETERMINE BETTER COMMENTS TAG
# ============================================================

def get_tag(comment: str) -> str:
    """
    Decide whether a comment should use ! or *.
    """

    text = comment.strip()

    if not text:
        return "*"

    upper = text.upper()

    # Already contains a Better Comments tag.
    if re.match(
        r"^(?:!|\*|\?|TODO|AI|FIXME)\b",
        text,
        re.IGNORECASE,
    ):
        return ""

    # Important / critical comments.
    for word in IMPORTANT_WORDS:
        if word in upper:
            return "!"

    # Section headings and informational comments.
    for word in INFORMATION_WORDS:
        if upper.startswith(word):
            return "*"

    # Separator-style comments.
    if re.fullmatch(r"[\s=\-_*#\/]{3,}", text):
        return "*"

    # Default.
    return "*"


# ============================================================
# FORMAT A COMMENT
# ============================================================

def format_comment(comment: str) -> str:
    """
    Add ! or * to an existing comment.
    """

    original = comment.rstrip()

    if not original.strip():
        return original

    stripped = original.strip()

    # Already formatted.
    if re.match(
        r"^(?:!|\*|\?|TODO|AI|FIXME)\b",
        stripped,
        re.IGNORECASE,
    ):
        return stripped

    tag = get_tag(stripped)

    if not tag:
        return stripped

    return f"{tag} {stripped}"


# ============================================================
# FORMAT SINGLE-LINE COMMENTS
# ============================================================

def format_single_line_comment(
    line: str,
    comment_start: str,
) -> str:

    newline = "\n" if line.endswith("\n") else ""

    content = line.rstrip("\r\n")

    index = content.find(comment_start)

    if index == -1:
        return line

    before = content[:index]
    comment = content[index + len(comment_start):]

    # Don't modify shebang.
    if comment_start == "#" and before == "" and comment.startswith("!"):
        return line

    # Don't modify empty comments.
    if not comment.strip():
        return line

    formatted = format_comment(comment)

    return (
        before
        + comment_start
        + " "
        + formatted
        + newline
    )


# ============================================================
# PYTHON
# ============================================================

def format_python_line(line: str) -> str:
    """
    Format Python # comments.

    Triple quoted strings/docstrings are deliberately untouched.
    """

    stripped = line.lstrip()

    # Full-line comment.
    if stripped.startswith("#"):

        indentation = line[:len(line) - len(stripped)]

        if stripped.startswith("#!"):
            return line

        comment = stripped[1:].rstrip("\r\n")

        if not comment.strip():
            return line

        formatted = format_comment(comment)

        newline = "\n" if line.endswith("\n") else ""

        return (
            indentation
            + "# "
            + formatted
            + newline
        )

    # Inline Python comment.
    #
    # We intentionally avoid attempting complicated parsing here.
    # Only obvious inline comments are modified.
    if "#" in line:

        quote_count = 0
        in_single = False
        in_double = False
        escaped = False

        for i, char in enumerate(line):

            if escaped:
                escaped = False
                continue

            if char == "\\":
                escaped = True
                continue

            if char == "'" and not in_double:
                in_single = not in_single

            elif char == '"' and not in_single:
                in_double = not in_double

            elif (
                char == "#"
                and not in_single
                and not in_double
            ):
                before = line[:i]
                comment = line[i + 1:].rstrip("\r\n")

                if comment.strip():

                    formatted = format_comment(comment)

                    newline = "\n" if line.endswith("\n") else ""

                    return (
                        before.rstrip()
                        + "  # "
                        + formatted
                        + newline
                    )

                break

    return line


# ============================================================
# C-STYLE COMMENTS
# ============================================================

def format_c_style_line(
    line: str,
    comment_prefix: str = "//",
) -> str:

    stripped = line.lstrip()

    # Full-line comment.
    if stripped.startswith(comment_prefix):

        indentation = line[:len(line) - len(stripped)]

        comment = stripped[len(comment_prefix):].rstrip(
            "\r\n"
        )

        if not comment.strip():
            return line

        formatted = format_comment(comment)

        newline = "\n" if line.endswith("\n") else ""

        return (
            indentation
            + comment_prefix
            + " "
            + formatted
            + newline
        )

    # Inline comment.
    if comment_prefix in line:

        index = line.find(comment_prefix)

        before = line[:index]
        comment = line[
            index + len(comment_prefix):
        ].rstrip("\r\n")

        if comment.strip():

            formatted = format_comment(comment)

            newline = "\n" if line.endswith("\n") else ""

            return (
                before.rstrip()
                + "  "
                + comment_prefix
                + " "
                + formatted
                + newline
            )

    return line


# ============================================================
# HTML COMMENTS
# ============================================================

def format_html_line(line: str) -> str:

    if "<!--" not in line:
        return line

    start = line.find("<!--")
    end = line.find("-->", start + 4)

    if end == -1:
        return line

    before = line[:start]
    comment = line[start + 4:end]

    if not comment.strip():
        return line

    formatted = format_comment(comment)

    return (
        before
        + "<!-- "
        + formatted
        + " -->"
        + ("\n" if line.endswith("\n") else "")
    )


# ============================================================
# SQL COMMENTS
# ============================================================

def format_sql_line(line: str) -> str:
    return format_c_style_line(line, "--")


# ============================================================
# PROCESS FILE
# ============================================================

def process_file(path: Path) -> tuple[bool, int]:

    try:
        original = path.read_text(
            encoding="utf-8"
        )
    except UnicodeDecodeError:
        return False, 0
    except Exception as exc:
        print(
            f"[ERROR] Could not read {path}: {exc}"
        )
        return False, 0

    lines = original.splitlines(
        keepends=True
    )

    extension = path.suffix.lower()

    new_lines = []

    changed_count = 0

    for line in lines:

        if extension == ".py":

            new_line = format_python_line(line)

        elif extension in {
            ".html",
            ".htm",
            ".vue",
        }:

            new_line = format_html_line(line)

        elif extension == ".sql":

            new_line = format_sql_line(line)

        elif extension in {
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".java",
            ".c",
            ".h",
            ".cpp",
            ".hpp",
            ".cc",
            ".cs",
            ".go",
            ".rs",
            ".php",
            ".swift",
            ".kt",
            ".kts",
            ".dart",
            ".ino",
        }:

            new_line = format_c_style_line(line)

        elif extension in {
            ".css",
            ".scss",
            ".sass",
            ".less",
        }:

            new_line = format_c_style_line(line)

        elif extension in {
            ".sh",
            ".bat",
            ".cmd",
            ".ps1",
        }:

            new_line = format_python_line(line)

        else:
            new_line = line

        if new_line != line:
            changed_count += 1

        new_lines.append(new_line)

    updated = "".join(new_lines)

    if updated == original:
        return False, 0

    # --------------------------------------------------------
    # Backup
    # --------------------------------------------------------

    if CREATE_BACKUPS:

        backup_path = path.with_suffix(
            path.suffix + ".bak"
        )

        # Don't overwrite an existing backup.
        if not backup_path.exists():

            shutil.copy2(
                path,
                backup_path
            )

    # --------------------------------------------------------
    # Write
    # --------------------------------------------------------

    path.write_text(
        updated,
        encoding="utf-8"
    )

    return True, changed_count


# ============================================================
# FIND PROJECT FILES
# ============================================================

def find_project_files() -> list[Path]:

    files = []

    for path in PROJECT_ROOT.rglob("*"):

        if not path.is_file():
            continue

        # Skip excluded directories.
        if any(
            part in EXCLUDED_DIRECTORIES
            for part in path.parts
        ):
            continue

        # Skip this formatter.
        if path.name in EXCLUDED_FILES:
            continue

        # Only supported source files.
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        files.append(path)

    return files


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print(" JARVIS PRO — PROJECT-WIDE BETTER COMMENTS FORMATTER")
    print("=" * 70)
    print()

    print(f"Project root:")
    print(f"  {PROJECT_ROOT}")
    print()

    print("Scanning entire project...")
    print()

    files = find_project_files()

    print(
        f"Found {len(files)} supported source files."
    )
    print()

    modified_files = 0
    total_comments = 0

    for path in files:

        try:

            changed, count = process_file(path)

            if changed:

                modified_files += 1
                total_comments += count

                relative = path.relative_to(
                    PROJECT_ROOT
                )

                print(
                    f"[UPDATED] {relative} "
                    f"({count} comment lines)"
                )

        except Exception as exc:

            print(
                f"[ERROR] {path}: {exc}"
            )

    print()
    print("=" * 70)
    print(" COMPLETE")
    print("=" * 70)
    print()

    print(
        f"Files scanned   : {len(files)}"
    )

    print(
        f"Files modified  : {modified_files}"
    )

    print(
        f"Comment lines   : {total_comments}"
    )

    if CREATE_BACKUPS:
        print()
        print(
            "Backup files were created as *.bak"
        )

    print()
    print("Better Comments:")
    print("  !  Important / Critical")
    print("  *  Information")
    print()
    print("IMPORTANT:")
    print("Python triple-quoted docstrings were NOT modified.")
    print()
    print("Done.")
    print()


if __name__ == "__main__":
    main()
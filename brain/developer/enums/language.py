"""
Programming Languages
"""

from enum import Enum


class Language(str, Enum):
    PYTHON = "python"
    CPP = "cpp"
    C = "c"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    HTML = "html"
    CSS = "css"
    PHP = "php"
    CSHARP = "csharp"
    DART = "dart"
    KOTLIN = "kotlin"
    SWIFT = "swift"
    GO = "go"
    RUST = "rust"
    UNKNOWN = "unknown"
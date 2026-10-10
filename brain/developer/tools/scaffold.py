"""
JARVIS PRO
Developer

Scaffold Tool
"""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


STRUCTURES = {

    "memory": {

        "folders": [

            "memory",

            "memory/models",

            "memory/rules",

            "memory/tests",

        ],

        "files": [

            # * Root
            "memory/__init__.py",
            "memory/developer_memory.py",
            "memory/memory_manager.py",
            "memory/memory_store.py",
            "memory/memory_loader.py",
            "memory/memory_saver.py",
            "memory/memory_indexer.py",
            "memory/memory_search.py",
            "memory/memory_builder.py",
            "memory/memory_context.py",

            # * Specialized Memory
            "memory/project_memory.py",
            "memory/file_memory.py",
            "memory/symbol_memory.py",
            "memory/dependency_memory.py",
            "memory/style_memory.py",
            "memory/session_memory.py",
            "memory/edit_history.py",

            # * Models
            "memory/models/__init__.py",
            "memory/models/memory_record.py",
            "memory/models/project_profile.py",
            "memory/models/file_profile.py",
            "memory/models/symbol_record.py",
            "memory/models/dependency_record.py",
            "memory/models/style_profile.py",
            "memory/models/edit_record.py",
            "memory/models/session_state.py",

            # * Rules
            "memory/rules/__init__.py",
            "memory/rules/memory_rules.py",

            # * Tests
            "memory/tests/__init__.py",
            "memory/tests/test_memory.py",
            "memory/tests/test_manager.py",
            "memory/tests/test_store.py",
            "memory/tests/test_search.py",
            "memory/tests/test_indexer.py",
            "memory/tests/test_context.py",

        ],

    },
}


def create_structure(name: str):

    if name not in STRUCTURES:

        print(f"Unknown structure: {name}")

        return

    structure = STRUCTURES[name]

    print(f"\nCreating '{name}'...\n")

    for folder in structure["folders"]:

        path = ROOT / folder

        path.mkdir(parents=True, exist_ok=True)

        print(f"[Folder] {folder}")

    for file in structure["files"]:

        path = ROOT / file

        path.parent.mkdir(parents=True, exist_ok=True)

        path.touch(exist_ok=True)

        print(f"[File]   {file}")

    print("\nDone.")


def main():

    if len(sys.argv) != 2:

        print("\nUsage:")

        print("python -m brain.developer.tools.scaffold memory")

        return

    create_structure(sys.argv[1])


if __name__ == "__main__":

    main()
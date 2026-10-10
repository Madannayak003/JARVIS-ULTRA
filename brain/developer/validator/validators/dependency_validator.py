"""
JARVIS PRO
Developer Validator

Dependency Validator
"""

import re

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brain.developer.context import DeveloperContext

from brain.developer.validator.models.validation_issue import (
    ValidationIssue,
)

from brain.developer.validator.models.validation_level import (
    ValidationLevel,
)

from brain.developer.validator.models.validation_result import (
    ValidationResult,
)

from brain.developer.validator.validators.base_validator import (
    BaseValidator,
)

from pathlib import PurePosixPath


class DependencyValidator(BaseValidator):
    """
    Validates project dependencies.

    Detects dependencies that are declared
    but never used in the generated source code.
    """

    IMPORT_PATTERN = re.compile(

        r"^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)",

        re.MULTILINE,

    )
    
    STANDARD_LIBRARY = {

        "abc",
        "argparse",
        "asyncio",
        "collections",
        "csv",
        "dataclasses",
        "datetime",
        "functools",
        "hashlib",
        "itertools",
        "json",
        "logging",
        "math",
        "multiprocessing",
        "os",
        "pathlib",
        "queue",
        "random",
        "re",
        "shutil",
        "socket",
        "sqlite3",
        "statistics",
        "subprocess",
        "sys",
        "threading",
        "time",
        "typing",
        "unittest",

    }
    
    PACKAGE_ALIASES = {

        "opencv_python": {"cv2"},
        "pillow": {"pil"},
        "pyyaml": {"yaml"},
        "beautifulsoup4": {"bs4"},
        "python_dateutil": {"dateutil"},

    }

    def validate(

        self,

        context: "DeveloperContext",

        result: ValidationResult,

    ) -> None:
        
        plan = context.execution_plan

        project = context.generated_project

        requirements = None

        # * -------------------------------------
        # * Find requirements.txt
        # * -------------------------------------

        for file in project.files:

            if PurePosixPath(file.path).name.lower() == "requirements.txt":

                requirements = file

                break

        if requirements is None:

            return

        if not requirements.content.strip():

            return

        # * -------------------------------------
        # * Declared packages
        # * -------------------------------------

        declared = set()

        for line in requirements.content.splitlines():

            # * Remove inline comments
            line = line.split("#", 1)[0].strip()

            if (

                not line
                or line.startswith("-e")
                or line.startswith(".")
                or line.startswith("git+")
                or line.startswith("http")

            ):

                continue

            package = re.split(

                r"[<>=\[\]]",

                line,

            )[0].strip()

            package = package.replace("-", "_").lower()

            declared.add(package)
            
        
        planned = set()

        if plan and plan.dependencies:

            planned = {

                dep.replace("-", "_").lower()

                for dep in plan.dependencies

            }

        missing = planned - declared

        for package in sorted(missing):

            result.total_checks += 1

            result.failed_checks += 1

            result.warning_count += 1

            result.issues.append(

                ValidationIssue(

                    level=ValidationLevel.WARNING,

                    validator="DependencyValidator",

                    file="requirements.txt",

                    message=f"Missing dependency: {package}",

                    expected="Declared in planner",

                    actual="Missing from requirements.txt",

                    suggestion="Add the dependency to requirements.txt.",

                )

            )

        # * -------------------------------------
        # * Imported packages
        # * -------------------------------------

        imported = set()

        for file in project.files:

            if not file.generated:

                continue

            if file.is_empty:

                continue

            if file.extension != ".py":

                continue

            path = file.path.replace("\\", "/")

            if path.startswith("tests/"):

                continue

            matches = self.IMPORT_PATTERN.findall(

                file.content

            )

            for module in matches:

                root = module.split(".")[0].lower()

                imported.add(root)

                imported.add(module.lower())

        # * -------------------------------------
        # * Compare
        # * -------------------------------------

        for package in sorted(declared):
            
            if package in self.STANDARD_LIBRARY:

                result.total_checks += 1

                result.passed_checks += 1

                continue

            result.total_checks += 1

            aliases = {

                alias.lower()

                for alias in self.PACKAGE_ALIASES.get(

                    package,

                    {package},

                )

            }

            if aliases & imported:

                result.passed_checks += 1

                continue

            result.failed_checks += 1

            result.warning_count += 1

            result.issues.append(

                ValidationIssue(

                    level=ValidationLevel.WARNING,

                    validator="DependencyValidator",

                    file="requirements.txt",

                    message=f"Unused dependency: {package}",

                    expected="Used by project",

                    actual="Not imported",

                    suggestion="Remove the unused dependency.",

                )

            )
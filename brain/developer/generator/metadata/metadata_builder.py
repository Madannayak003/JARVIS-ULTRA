"""
JARVIS PRO
Developer Generator

Metadata Builder
"""

from brain.developer.generator.models.generated_project import GeneratedProject


class MetadataBuilder:
    """
    Populates project metadata after generation.
    """

    def build(
        self,
        project: GeneratedProject,
    ) -> GeneratedProject:

        file_paths = {

            file.path.replace("\\", "/")

            for file in project.files

        }

        # * -------------------------------------
        # * Normalize Enum Values
        # * -------------------------------------

        language = str(project.language).upper()

        framework = str(project.framework).upper()

        workspace = str(project.workspace).upper()

        # * -------------------------------------
        # * Entry File
        # * -------------------------------------

        # * Arduino / ESP32 (.ino)
        for path in sorted(file_paths):

            if path.lower().endswith(".ino"):

                project.entry_file = path

                break

        # * Python
        if not project.entry_file:

            for candidate in (

                "src/main.py",
                "main.py",
                "app.py",

            ):

                if candidate in file_paths:

                    project.entry_file = candidate

                    break

        # * C / C++
        if not project.entry_file:

            for candidate in (

                "src/main.cpp",
                "main.cpp",
                "src/main.c",
                "main.c",

            ):

                if candidate in file_paths:

                    project.entry_file = candidate

                    break

        # * React
        if not project.entry_file:

            for candidate in (

                "src/App.tsx",
                "src/App.jsx",

            ):

                if candidate in file_paths:

                    project.entry_file = candidate

                    break

        # * -------------------------------------
        # * Run / Build Commands
        # * -------------------------------------

        if "ARDUINO" in workspace:

            project.run_command = "Open in Arduino IDE and Upload"

            project.build_command = "Verify Sketch"

        elif "ESP32" in workspace:

            project.run_command = "platformio run --target upload"

            project.build_command = "platformio run"

        elif "PYTHON" in language:

            project.run_command = f"python {project.entry_file}"

            project.build_command = ""
            
        elif "NODE" in workspace:

            project.run_command = "npm start"

            project.build_command = "npm install"
            
        elif "CPP" in language:

            project.run_command = project.entry_file

            project.build_command = "g++"

        elif "FLASK" in framework:

            project.run_command = "python app.py"

        elif "REACT" in framework:

            project.run_command = "npm run dev"

            project.build_command = "npm run build"

        return project
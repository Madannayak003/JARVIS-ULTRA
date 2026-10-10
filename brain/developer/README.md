# Developer

Developer is the software engineering subsystem of JARVIS PRO.

Its responsibility is to understand software development requests,
plan projects, generate code, validate the generated output,
and save projects into the correct workspace.

---

## Responsibilities

Developer is responsible for:

- Understanding development requests
- Detecting technologies
- Planning project structure
- Generating source code
- Validating generated code
- Managing project workspace
- Editing existing projects
- Managing developer memory

Developer is NOT responsible for:

- Voice recognition
- Text-to-speech
- Conversation memory
- General AI chat
- Skill execution

---

## Architecture

Developer consists of independent modules.

Developer
│
├── API
├── Models
├── Analyzer
├── Planner
├── Generator
├── Validator
├── Workspace
├── Editor
├── Memory
├── Integration
└── Utils

Every module has one responsibility.

Modules communicate only through models.

---

## Request Flow

User

↓

Developer API

↓

Analyzer

↓

Planner

↓

Generator

↓

Validator

↓

Workspace

↓

Developer Result

---

## Design Principles

- One responsibility per module.
- No circular imports.
- No hidden dependencies.
- Stable public interfaces.
- Every phase is independently testable.
- Workspace is the only module that writes files.
- Generator is the only module that communicates with AI.
- Analyzer never generates code.
- Planner never writes files.
- Validator never modifies generated code.

---

## Coding Standards

- Python 3.11+
- Type hints required
- Dataclasses where appropriate
- One primary class per file
- Clear docstrings
- Meaningful names
- No wildcard imports

---

## Public API

Only this class is public.

Developer

All internal modules remain private.

---

## Workspace

Projects are automatically stored inside:

workspace/

Examples

workspace/Python/

workspace/Web/

workspace/ESP32/

workspace/Arduino/

workspace/Javascript/

workspace/Html/

workspace/General/

workspace/jarvis/

---

## Development Order

Phase 0 Foundation

Phase 1 Core Models

Phase 2 Analyzer

Phase 3 Planner

Phase 4 Generator

Phase 5 Validator

Phase 6 Workspace

Phase 7 Editor

Phase 8 Memory

Phase 9 Integration

Future features are implemented only after the architecture is complete.
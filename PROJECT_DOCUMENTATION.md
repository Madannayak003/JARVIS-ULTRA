============================================================ JARVIS PRO
COMPLETE PROJECT TECHNICAL DOCUMENTATION
============================================================

## AUDIT BASIS

Repository audited from the working tree at audit time: 2026-09-20. This
document is an inventory of the code and data currently present on disk.
Static inspection was used. No services were started, no dependencies
were installed, no source functionality was changed, and no Git commit
or push was performed.

Secret-handling rule: - Secret values, API keys, OAuth contents,
cookies, PINs, tokens, and credentials are intentionally not
reproduced. - Sensitive files are identified by name and role only. -
Environment-variable names are documented; values are omitted.

# 1. PROJECT OVERVIEW

Project identity: JARVIS PRO is a Windows-oriented Python desktop
assistant with a native pywebview HUD, a Next.js/React HUD frontend, a
voice command runtime, a local/remote dashboard, deterministic skill
routing, AI providers, local memory, browser automation, camera/vision
functions, Android/ADB integration, communication/media integrations,
and a developer-oriented code-generation/editing subsystem.

Current runtime shape: main.py is the application entry point.
run_jarvis.py is a windowless/shortcut launcher that captures startup
errors. The Python runtime owns command processing and skills. The
Next.js frontend is started as a child process in hud/web. The native
pywebview window displays the frontend. dashboard/server.py provides the
active local/LAN HTTP/WebSocket API.

Architecture philosophy confirmed in source: - deterministic fast routes
are tried before the normal AI/planner path; - skills register actions
into core.registry; - the dispatcher is the shared command path for
microphone, HUD, and remote dashboard text; - optional systems fail
independently where their modules handle errors; - online and offline
voice modes reuse the same core/action registry; - HUD events are
emitted through a Python event bus and consumed by the web client
through an SSE bridge; - compatibility and legacy code remains in the
tree.

Major subsystems: configuration, runtime startup/shutdown, core
routing/dispatch, action registry, skills, AI provider routing,
brain/conversation, clarification, memory/profile, voice/STT/TTS,
browser/CDP, camera/vision, Android/ADB and payment handoff,
communications/media, remote dashboard, HUD telemetry/events, frontend
chat/cockpit, and developer automation.

Current development state: The repository is an active, feature-rich but
mixed-generation codebase. Some modules are directly wired into startup;
others are imported only by specific routes, tests, or compatibility
paths. Source alone cannot prove that every external service is
configured or available on a given machine.

# 2. CURRENT IDENTITY

The requested product terminology says: CURRENT USER-FACING NAME: JARVIS
PRO INTERNAL / LEGACY IDENTIFIERS: JARVIS / JARVIS PRO

The current repository does not consistently confirm JARVIS PRO as the
active runtime name. The authoritative settings module starts with
APP*NAME = \"JARVIS PRO\", then loads data/settings/jarvis*settings.json
when present. That persisted file currently contains a customized
assistantName of \"JARVIS\". Therefore the runtime display name resolves
to the persisted setting on this checkout, not to JARVIS PRO.

JARVIS PRO evidence: - offline AI instructions use the name JARVIS
PRO; - browser runtime messages include JARVIS PRO in some
descriptions; - tests and newer UI terminology refer to JARVIS PRO in
places.

JARVIS evidence: - package/module/file names, action protocol names,
dashboard constants, storage filenames, prompt text, and compatibility
aliases use JARVIS; - settings.py defines JARVIS PRO as the built-in
fallback; - \"jarvis\" is an explicit legacy assistant alias; - the
persisted runtime setting currently resolves to JARVIS.

Safe conclusion: JARVIS PRO is a requested/new identity and appears in
parts of the code, but this checkout\'s effective persisted display name
is JARVIS. JARVIS and JARVIS PRO remain active technical identifiers.
The name system is configurable and intentionally preserves explicit
compatibility aliases.

# 3. PROJECT ROOT STRUCTURE

Root-owned source/configuration: main.py, run_jarvis.py ai/, brain/,
chatbot/, config/, core/, dashboard/, hud/, services/, skills/, tests/,
tools/, voice/ requirements.txt, .env.example, .gitignore

Sensitive or machine-local root artifacts: .env, credentials.json,
token.json, .spotify_cache, yolo11n.pt These are not documented by
value. They are ignored or intended to be local.

Frontend: hud/web/ contains Next.js source, package metadata, public 3D
models, and installed node_modules. The dependency directory is not
source-audited.

Runtime/generated data: data/ contains faces, settings,
logs/uploads/runtime data where created. voice/cache/ contains generated
audio cache. workspace/ contains generated example/user projects and
JARVIS memory/backup state, not the assistant\'s core source.
hud/web/node_modules/ contains installed JavaScript dependencies.

# 4. COMPLETE DIRECTORY TREE

The source tree below is represented by the complete file inventory in
Section 5. Large generated/dependency areas are intentionally summarized
separately.

JARVIS-PRO/ \|\-- .env (local environment values; secret) \|\--
.env.example (safe variable-name template) \|\-- .gitignore \|\--
credentials.json (OAuth credential artifact; secret) \|\-- main.py \|\--
README.md (existing; not modified) \|\-- requirements.txt \|\--
run*jarvis.py \|\-- token.json (OAuth token artifact; secret) \|\--
yolo11n.pt (local YOLO model) \|\-- ai/ \|\-- brain/ \|\-- chatbot/
\|\-- config/ \|\-- core/ \|\-- dashboard/ \|\-- data/ \|\-- hud/ \|\--
services/ \|\-- skills/ \|\-- tests/ \|\-- tools/ \|\-- voice/ \|\--
workspace/ \|\-- .vscode/ \|\-- .pytest*cache/ \|\-- **pycache**/

Source package summaries: ai/ AI contracts, providers, prompts, planner,
and memory. brain/ conversation/context/clarification plus developer
subsystem. chatbot/ independent dashboard AI-chat API/session/clipboard
support. config/ environment, settings, feature-specific configuration.
core/ runtime, routers, dispatcher, action registry, workers, state.
dashboard/ active FastAPI local/LAN dashboard server and static client.
hud/ event bus, state, telemetry, bridge, native window, web app.
services/ Android, contacts, email, files, location, remote, media, web.
skills/ import-time action modules grouped by capability. tests/ focused
routing, provider, vision, remote, and feature tests. tools/ Windows
integration and database utility scripts. voice/ online/offline STT/TTS,
Agent, queues and state.

Large/derived areas: hud/web/node*modules/ installed Node dependencies;
not manually audited. hud/web/.next/ Next build/development output if
present; generated. workspace/ generated projects and .jarvis
memories/backups. data/ runtime/user/model data; not core source.
voice/cache/ generated MP3/Piper cache. **pycache**/, .pytest*cache/
compiled/interpreter/test caches. .git/ repository metadata.

# 5. FILE-BY-FILE INVENTORY

Inventory convention: The Python manifest below lists every
non-generated Python file outside workspace/, node_modules/, .git/,
.next/, and **pycache**. It reports the top-level classes and functions
discovered by AST inspection. Descriptions and runtime roles are grouped
immediately after the manifest so small helpers remain readable.

Python manifest: ai/**init**.py \| classes=- \| functions=-
ai/ai*worker.py \| classes=- \| functions=clean*for*speech,run*chat
ai/chat.py \| classes=ChatSession \| functions=ai*chat*stream,ask*chat
ai/chat*prompt.py \| classes=- \| functions=- ai/conversation.py \|
classes=- \| functions=set*context,get*context,clear*context,all*context
ai/core/commands.py \| classes=AICommandHandler \| functions=-
ai/core/model*manager.py \| classes=ModelManager \| functions=-
ai/core/policy.py \| classes=AIModelPolicy \| functions=-
ai/core/preference.py \| classes=AIPreference \| functions=-
ai/core/registry.py \| classes=ModelDefinition,ModelRegistry \|
functions=- ai/core/router.py \| classes=AIRouter \| functions=-
ai/core/schemas.py \| classes=AIRequest,AIResponse,AIStreamChunk,AIError
\| functions=- ai/core/service.py \| classes=AIService \| functions=-
ai/intent.py \| classes=- \| functions=detect ai/llm.py \| classes=- \|
functions=ask ai/memory.py \| classes=- \|
functions=connect,init*memory,migrate ai/memory*ai.py \| classes=- \|
functions=extract*memory,normalize ai/memory*answer.py \| classes=- \|
functions=is*personal*question,*normalize*text,normalize*question,*get*memory,*format*memory,direct*answer,answer
ai/memory*confidence.py \| classes=- \|
functions=confidence,is*high,is*medium,is*low ai/memory*forget.py \|
classes=- \| functions=forget*key,forget*category,forget*all
ai/memory*intent.py \| classes=- \| functions=handle
ai/memory*manager.py \| classes=- \| functions=clean*value,learn
ai/memory*pipeline.py \| classes=- \| functions=learn
ai/memory*preference.py \| classes=- \| functions=clean,extract
ai/memory*profile.py \| classes=- \|
functions=profile,profile*summary,ai*profile ai/memory*rank.py \|
classes=- \| functions=parse*time,score,rank ai/memory*schema.py \|
classes=Memory \| functions=now ai/memory*search.py \| classes=- \|
functions=score*memory,search,search*category,format*memories,row*to*memory
ai/memory*semantic.py \| classes=- \| functions=tokenize,search
ai/memory*stats.py \| classes=- \|
functions=total,by*category,most*used,least*used,recent,unused,stats
ai/memory*store.py \| classes=- \|
functions=remember,get,exists,forget,list*all,total,touch,all*memories
ai/memory*view.py \| classes=- \|
functions=show*all,show,show*category,pretty ai/planner.py \| classes=-
\| functions=*looks*like*bare*topic,create*plan ai/planner*prompt.py \|
classes=- \| functions=- ai/prompt*builder.py \| classes=- \|
functions=build*conversation,build*memory,build*prompt
ai/providers/base.py \| classes=AIProvider \| functions=-
ai/providers/gemini.py \| classes=GeminiProvider \|
functions=*is*quota*error ai/providers/ollama.py \|
classes=OllamaProvider \| functions=- ai/providers/openai.py \|
classes=OpenAIProvider \| functions=- ai/query*parser.py \| classes=- \|
functions=normalize,extract*keywords ai/sentence*buffer.py \| classes=-
\| functions=sentence*buffer brain/**init**.py \| classes=- \|
functions=- brain/ai*pipeline.py \| classes=AIPipeline \| functions=-
brain/brain.py \| classes=Brain \| functions=- brain/brain*controller.py
\| classes=- \| functions=- brain/brain*router.py \|
classes=BrainResult,BrainRouter \| functions=-
brain/clarification*manager.py \|
classes=ClarificationState,ClarificationManager \|
functions=start,is*waiting,resolve,clear,info brain/context*builder.py
\| classes=ContextBuilder \| functions=- brain/context*types.py \|
classes=AIContext \| functions=- brain/conversation*context.py \|
classes=ConversationContext,ConversationContextManager \|
functions=get*context,get,update,clear brain/conversation*coordinator.py
\| classes=ConversationAnalysis,ConversationCoordinator \| functions=-
brain/conversation*manager.py \| classes=Message,ConversationManager \|
functions=- brain/conversation*state.py \|
classes=ConversationState,ConversationStateManager \| functions=-
brain/conversation*understanding.py \|
classes=ConversationRelation,ConversationUnderstanding,ConversationUnderstandingEngine
\| functions=understand brain/developer/**init**.py \| classes=- \|
functions=- brain/developer/analyzer/**init**.py \| classes=- \|
functions=- brain/developer/analyzer/analyzer.py \| classes=Analyzer \|
functions=- brain/developer/analyzer/detectors/**init**.py \| classes=-
\| functions=- brain/developer/analyzer/detectors/base*detector.py \|
classes=BaseDetector \| functions=-
brain/developer/analyzer/detectors/board*detector.py \|
classes=BoardDetector \| functions=-
brain/developer/analyzer/detectors/framework*detector.py \|
classes=FrameworkDetector \| functions=-
brain/developer/analyzer/detectors/intent*detector.py \|
classes=IntentDetector \| functions=-
brain/developer/analyzer/detectors/language*detector.py \|
classes=LanguageDetector \| functions=-
brain/developer/analyzer/detectors/project*detector.py \|
classes=ProjectDetector \| functions=-
brain/developer/analyzer/detectors/runtime*detector.py \|
classes=RuntimeDetector \| functions=-
brain/developer/analyzer/detectors/workspace*detector.py \|
classes=WorkspaceDetector \| functions=-
brain/developer/analyzer/resolvers/**init**.py \| classes=- \|
functions=- brain/developer/analyzer/resolvers/base*resolver.py \|
classes=BaseResolver \| functions=-
brain/developer/analyzer/resolvers/board*resolver.py \|
classes=BoardResolver \| functions=-
brain/developer/analyzer/resolvers/language*resolver.py \|
classes=LanguageResolver \| functions=-
brain/developer/analyzer/resolvers/workspace*resolver.py \|
classes=WorkspaceResolver \| functions=-
brain/developer/analyzer/rules/**init**.py \| classes=- \| functions=-
brain/developer/analyzer/rules/board*language*rules.py \| classes=- \|
functions=- brain/developer/analyzer/rules/board*rules.py \| classes=-
\| functions=-
brain/developer/analyzer/rules/framework*language*rules.py \| classes=-
\| functions=- brain/developer/analyzer/rules/framework*rules.py \|
classes=- \| functions=- brain/developer/analyzer/rules/intent*rules.py
\| classes=- \| functions=-
brain/developer/analyzer/rules/language*rules.py \| classes=- \|
functions=- brain/developer/analyzer/rules/project*rules.py \| classes=-
\| functions=- brain/developer/analyzer/rules/runtime*rules.py \|
classes=- \| functions=-
brain/developer/analyzer/rules/workspace*rules.py \| classes=- \|
functions=- brain/developer/api/**init**.py \| classes=- \| functions=-
brain/developer/config/config.py \| classes=- \| functions=-
brain/developer/config.py \| classes=- \| functions=-
brain/developer/constants.py \| classes=- \| functions=-
brain/developer/context/**init**.py \| classes=- \| functions=-
brain/developer/context/developer*context.py \| classes=DeveloperContext
\| functions=- brain/developer/developer.py \| classes=Developer \|
functions=*launch*project*assets brain/developer/editor/**init**.py \|
classes=- \| functions=- brain/developer/editor/analyzer/**init**.py \|
classes=- \| functions=-
brain/developer/editor/analyzer/edit*analyzer.py \| classes=EditAnalyzer
\| functions=- brain/developer/editor/analyzer/project*scanner.py \|
classes=ProjectScanner \| functions=-
brain/developer/editor/analyzer/target*locator.py \|
classes=TargetLocator \| functions=- brain/developer/editor/editor.py \|
classes=Editor \| functions=- brain/developer/editor/models/**init**.py
\| classes=- \| functions=-
brain/developer/editor/models/edit*context.py \| classes=EditContext \|
functions=- brain/developer/editor/models/edit*plan.py \|
classes=EditPlan \| functions=-
brain/developer/editor/models/edit*request.py \| classes=EditRequest \|
functions=- brain/developer/editor/models/edit*result.py \|
classes=EditResult \| functions=- brain/developer/editor/models/patch.py
\| classes=Patch \| functions=-
brain/developer/editor/models/project*index.py \| classes=ProjectIndex
\| functions=- brain/developer/editor/models/prompt*context.py \|
classes=PromptContext \| functions=-
brain/developer/editor/models/prompt*result.py \| classes=PromptResult
\| functions=- brain/developer/editor/parser/**init**.py \| classes=- \|
functions=- brain/developer/editor/parser/block*parser.py \| classes=-
\| functions=- brain/developer/editor/parser/file*parser.py \|
classes=FileParser \| functions=-
brain/developer/editor/parser/response*parser.py \|
classes=ResponseParser \| functions=-
brain/developer/editor/planner/**init**.py \| classes=- \| functions=-
brain/developer/editor/planner/dependency*analyzer.py \|
classes=DependencyAnalyzer \| functions=-
brain/developer/editor/planner/edit*planner.py \| classes=EditPlanner \|
functions=- brain/developer/editor/planner/file*selector.py \|
classes=FileSelector \| functions=-
brain/developer/editor/planner/instruction*planner.py \|
classes=InstructionPlanner \| functions=-
brain/developer/editor/prompt*builder/**init**.py \| classes=- \|
functions=- brain/developer/editor/prompt*builder/context*builder.py \|
classes=ContextBuilder \| functions=-
brain/developer/editor/prompt*builder/instruction*builder.py \|
classes=InstructionBuilder \| functions=-
brain/developer/editor/prompt*builder/prompt*builder.py \|
classes=PromptBuilder \| functions=-
brain/developer/editor/prompt*builder/system*builder.py \|
classes=SystemBuilder \| functions=-
brain/developer/editor/provider/**init**.py \| classes=- \| functions=-
brain/developer/editor/provider/base*provider.py \| classes=BaseProvider
\| functions=- brain/developer/editor/provider/ollama*provider.py \|
classes=OllamaProvider \| functions=-
brain/developer/editor/rules/**init**.py \| classes=- \| functions=-
brain/developer/editor/rules/edit*rules.py \| classes=- \| functions=-
brain/developer/editor/tests/**init**.py \| classes=- \| functions=-
brain/developer/editor/tests/test*backup*builder.py \| classes=- \|
functions=main brain/developer/editor/tests/test*editor.py \| classes=-
\| functions=main brain/developer/editor/tests/test*editor*engine.py \|
classes=- \| functions=run*test,main
brain/developer/editor/tests/test*main.py \| classes=TestCalculator \|
functions=- brain/developer/editor/tests/test*parser.py \| classes=- \|
functions=main brain/developer/editor/tests/test*patch*writer.py \|
classes=- \| functions=main
brain/developer/editor/tests/test*rollback*manager.py \| classes=- \|
functions=main brain/developer/editor/tests/test*validator.py \|
classes=- \| functions=main
brain/developer/editor/tests/test*web*project*editing.py \| classes=- \|
functions=*file*response,*single*file*html,*edit*embedded*css,test*single*file*html*edit*receives*and*preserves*complete*file,test*multi*file*css*edit*changes*only*the*existing*stylesheet,test*incomplete*large*single*file*response*is*rejected,test*complete*large*single*file*response*is*accepted
brain/developer/editor/validator/**init**.py \| classes=- \| functions=-
brain/developer/editor/validator/edit*validator.py \|
classes=EditValidator \| functions=-
brain/developer/editor/validator/syntax*validator.py \|
classes=SyntaxValidator \| functions=- brain/developer/enums/**init**.py
\| classes=- \| functions=- brain/developer/enums/board.py \|
classes=Board \| functions=- brain/developer/enums/framework.py \|
classes=Framework \| functions=- brain/developer/enums/intent.py \|
classes=Intent \| functions=- brain/developer/enums/language.py \|
classes=Language \| functions=- brain/developer/enums/project*type.py \|
classes=ProjectType \| functions=- brain/developer/enums/runtime.py \|
classes=Runtime \| functions=- brain/developer/enums/workspace.py \|
classes=Workspace \| functions=- brain/developer/exceptions.py \|
classes=DeveloperError,ConfigurationError,AnalysisError,PlanningError,GenerationError,ValidationError,WorkspaceError
\| functions=- brain/developer/generator/**init**.py \| classes=- \|
functions=- brain/developer/generator/generator.py \| classes=Generator
\| functions=- brain/developer/generator/metadata/**init**.py \|
classes=- \| functions=-
brain/developer/generator/metadata/metadata*builder.py \|
classes=MetadataBuilder \| functions=-
brain/developer/generator/models/**init**.py \| classes=- \| functions=-
brain/developer/generator/models/generated*file.py \|
classes=GeneratedFile \| functions=-
brain/developer/generator/models/generated*project.py \|
classes=GeneratedProject \| functions=-
brain/developer/generator/parsers/**init**.py \| classes=- \|
functions=- brain/developer/generator/parsers/markdown*parser.py \|
classes=MarkdownParser \| functions=-
brain/developer/generator/parsers/response*parser.py \|
classes=ResponseParser \| functions=-
brain/developer/generator/providers/**init**.py \| classes=- \|
functions=- brain/developer/generator/providers/base*provider.py \|
classes=BaseProvider \| functions=-
brain/developer/generator/providers/ollama*provider.py \|
classes=OllamaProvider \| functions=-
brain/developer/generator/rules/**init**.py \| classes=- \| functions=-
brain/developer/generator/rules/generator*rules.py \| classes=- \|
functions=- brain/developer/integration/**init**.py \| classes=- \|
functions=- brain/developer/integration/active*project.py \|
classes=ActiveProjectResolver \| functions=-
brain/developer/integration/tests/test*active*project.py \| classes=- \|
functions=main brain/developer/integration/tests/test*brain*router.py \|
classes=- \| functions=main
brain/developer/integration/tests/test*create*integration.py \|
classes=ControlledProvider \| functions=main
brain/developer/integration/tests/test*developer*connection.py \|
classes=- \| functions=main
brain/developer/integration/tests/test*dispatcher*developer.py \|
classes=- \| functions=main
brain/developer/integration/tests/test*full*integration.py \| classes=-
\| functions=main
brain/developer/integration/tests/test*memory*integration.py \|
classes=- \| functions=main
brain/developer/integration/tests/test*rollback*integration.py \|
classes=- \| functions=main brain/developer/logging/**init**.py \|
classes=- \| functions=- brain/developer/logging/logger.py \| classes=-
\| functions=- brain/developer/memory/**init**.py \| classes=- \|
functions=- brain/developer/memory/developer*memory.py \|
classes=DeveloperMemory \| functions=-
brain/developer/memory/memory*builder.py \| classes=MemoryBuilder \|
functions=- brain/developer/memory/memory*context.py \|
classes=MemoryContext \| functions=-
brain/developer/memory/memory*indexer.py \| classes=MemoryIndexer \|
functions=- brain/developer/memory/memory*loader.py \|
classes=MemoryLoader \| functions=-
brain/developer/memory/memory*manager.py \| classes=MemoryManager \|
functions=- brain/developer/memory/memory*saver.py \|
classes=MemorySaver \| functions=-
brain/developer/memory/memory*search.py \| classes=MemorySearch \|
functions=- brain/developer/memory/memory*store.py \|
classes=MemoryStore \| functions=-
brain/developer/memory/models/**init**.py \| classes=- \| functions=-
brain/developer/memory/models/dependency*record.py \|
classes=DependencyRecord \| functions=-
brain/developer/memory/models/edit*record.py \| classes=EditRecord \|
functions=- brain/developer/memory/models/file*profile.py \|
classes=FileProfile \| functions=-
brain/developer/memory/models/memory*record.py \| classes=MemoryRecord
\| functions=- brain/developer/memory/models/project*profile.py \|
classes=ProjectProfile \| functions=-
brain/developer/memory/models/session*state.py \| classes=SessionState
\| functions=- brain/developer/memory/models/style*profile.py \|
classes=StyleProfile \| functions=-
brain/developer/memory/models/symbol*record.py \| classes=SymbolRecord
\| functions=- brain/developer/memory/rules/**init**.py \| classes=- \|
functions=- brain/developer/memory/rules/memory*rules.py \| classes=- \|
functions=- brain/developer/memory/tests/**init**.py \| classes=- \|
functions=- brain/developer/memory/tests/test*builder.py \| classes=- \|
functions=main brain/developer/memory/tests/test*context.py \| classes=-
\| functions=main brain/developer/memory/tests/test*indexer.py \|
classes=- \| functions=main brain/developer/memory/tests/test*manager.py
\| classes=- \| functions=main
brain/developer/memory/tests/test*memory.py \| classes=- \|
functions=main brain/developer/memory/tests/test*saver.py \| classes=-
\| functions=main brain/developer/memory/tests/test*search.py \|
classes=- \| functions=main brain/developer/memory/tests/test*store.py
\| classes=- \| functions=main brain/developer/models/**init**.py \|
classes=- \| functions=- brain/developer/models/analysis*context.py \|
classes=AnalysisContext \| functions=-
brain/developer/models/analysis*result.py \| classes=AnalysisResult \|
functions=- brain/developer/models/developer*request.py \|
classes=DeveloperRequest \| functions=-
brain/developer/models/developer*result.py \| classes=DeveloperResult \|
functions=- brain/developer/models/generation*result.py \|
classes=GenerationResult \| functions=-
brain/developer/models/project*plan.py \| classes=ProjectPlan \|
functions=- brain/developer/models/validation*result.py \|
classes=ValidationResult \| functions=-
brain/developer/models/workspace*result.py \| classes=WorkspaceResult \|
functions=- brain/developer/pipeline/**init**.py \| classes=- \|
functions=- brain/developer/pipeline/developer*pipeline.py \|
classes=DeveloperPipeline \| functions=-
brain/developer/planner/**init**.py \| classes=- \| functions=-
brain/developer/planner/models/**init**.py \| classes=- \| functions=-
brain/developer/planner/models/execution*plan.py \|
classes=ExecutionPlan \| functions=- brain/developer/planner/planner.py
\| classes=Planner \| functions=-
brain/developer/planner/planners/**init**.py \| classes=- \| functions=-
brain/developer/planner/planners/arduino*planner.py \|
classes=ArduinoPlanner \| functions=-
brain/developer/planner/planners/base*planner.py \| classes=BasePlanner
\| functions=- brain/developer/planner/planners/cpp*planner.py \|
classes=CppPlanner \| functions=-
brain/developer/planner/planners/esp32*planner.py \|
classes=ESP32Planner \| functions=-
brain/developer/planner/planners/general*planner.py \|
classes=GeneralPlanner \| functions=-
brain/developer/planner/planners/javascript*planner.py \|
classes=JavaScriptPlanner \| functions=-
brain/developer/planner/planners/python*planner.py \|
classes=PythonPlanner \| functions=-
brain/developer/planner/rules/**init**.py \| classes=- \| functions=-
brain/developer/planner/rules/board*rules.py \| classes=- \| functions=-
brain/developer/planner/rules/framework*rules.py \| classes=- \|
functions=- brain/developer/planner/rules/language*rules.py \| classes=-
\| functions=- brain/developer/planner/rules/planner*rules.py \|
classes=- \| functions=- brain/developer/planner/templates/**init**.py
\| classes=- \| functions=- brain/developer/planner/utils/**init**.py \|
classes=- \| functions=- brain/developer/planner/utils/path*utils.py \|
classes=- \| functions=- brain/developer/prompt*builder/**init**.py \|
classes=- \| functions=-
brain/developer/prompt*builder/builders/**init**.py \| classes=- \|
functions=- brain/developer/prompt*builder/builders/base*builder.py \|
classes=BaseBuilder \| functions=-
brain/developer/prompt*builder/builders/context*builder.py \|
classes=ContextBuilder \| functions=-
brain/developer/prompt*builder/builders/instruction*builder.py \|
classes=InstructionBuilder \| functions=-
brain/developer/prompt*builder/builders/system*builder.py \|
classes=SystemBuilder \| functions=-
brain/developer/prompt*builder/models/**init**.py \| classes=- \|
functions=- brain/developer/prompt*builder/models/prompt*context.py \|
classes=PromptContext \| functions=-
brain/developer/prompt*builder/models/prompt*result.py \|
classes=PromptResult \| functions=-
brain/developer/prompt*builder/prompt*builder.py \|
classes=PromptBuilder \| functions=-
brain/developer/prompt*builder/rules/**init**.py \| classes=- \|
functions=- brain/developer/prompt*builder/rules/instruction*rules.py \|
classes=- \| functions=-
brain/developer/prompt*builder/rules/system*rules.py \| classes=- \|
functions=- brain/developer/repair/**init**.py \| classes=- \|
functions=- brain/developer/repair/builders/**init**.py \| classes=- \|
functions=- brain/developer/repair/builders/base*builder.py \|
classes=BaseBuilder \| functions=-
brain/developer/repair/builders/repair*context*builder.py \|
classes=RepairContextBuilder \| functions=-
brain/developer/repair/builders/repair*instruction*builder.py \|
classes=RepairInstructionBuilder \| functions=-
brain/developer/repair/local*file*builder.py \| classes=LocalFileBuilder
\| functions=- brain/developer/repair/merge*builder.py \|
classes=MergeBuilder \| functions=-
brain/developer/repair/models/repair*prompt.py \| classes=RepairPrompt
\| functions=- brain/developer/repair/models/repair*request.py \|
classes=RepairRequest \| functions=-
brain/developer/repair/models/repair*result.py \| classes=RepairResult
\| functions=- brain/developer/repair/prompt*builder.py \|
classes=RepairPromptBuilder \| functions=-
brain/developer/repair/repair.py \| classes=Repair \| functions=-
brain/developer/repair/repair*builder.py \| classes=RepairBuilder \|
functions=- brain/developer/repair/repair*parser.py \|
classes=RepairParser \| functions=-
brain/developer/repair/repair*provider.py \| classes=RepairProvider \|
functions=- brain/developer/tests/**init**.py \| classes=- \|
functions=- brain/developer/tests/test*analyzer.py \| classes=- \|
functions=main brain/developer/tests/test*board*detector.py \| classes=-
\| functions=main brain/developer/tests/test*enums.py \| classes=- \|
functions=main brain/developer/tests/test*foundation.py \| classes=- \|
functions=main brain/developer/tests/test*framework*detector.py \|
classes=- \| functions=main brain/developer/tests/test*generator.py \|
classes=- \| functions=main
brain/developer/tests/test*intent*detector.py \| classes=- \|
functions=main brain/developer/tests/test*language*detector.py \|
classes=- \| functions=main brain/developer/tests/test*planner.py \|
classes=- \| functions=main
brain/developer/tests/test*project*detector.py \| classes=- \|
functions=main brain/developer/tests/test*prompt*builder.py \| classes=-
\| functions=main brain/developer/tests/test*repair.py \| classes=- \|
functions=main brain/developer/tests/test*runtime*detector.py \|
classes=- \| functions=main brain/developer/tests/test*validator.py \|
classes=- \| functions=main brain/developer/tests/test*workspace.py \|
classes=- \| functions=main
brain/developer/tests/test*workspace*detector.py \| classes=- \|
functions=main brain/developer/tools/**init**.py \| classes=- \|
functions=- brain/developer/tools/scaffold.py \| classes=- \|
functions=create*structure,main brain/developer/tools/templates.py \|
classes=- \| functions=- brain/developer/utils/**init**.py \| classes=-
\| functions=- brain/developer/validator/**init**.py \| classes=- \|
functions=- brain/developer/validator/models/**init**.py \| classes=- \|
functions=- brain/developer/validator/models/validation*issue.py \|
classes=ValidationIssue \| functions=-
brain/developer/validator/models/validation*level.py \|
classes=ValidationLevel \| functions=-
brain/developer/validator/models/validation*result.py \|
classes=ValidationResult \| functions=-
brain/developer/validator/models/validation*summary.py \|
classes=ValidationSummary \| functions=-
brain/developer/validator/rules/**init**.py \| classes=- \| functions=-
brain/developer/validator/rules/validator*rules.py \| classes=- \|
functions=- brain/developer/validator/utils/**init**.py \| classes=- \|
functions=- brain/developer/validator/utils/validation*utils.py \|
classes=- \| functions=- brain/developer/validator/validator.py \|
classes=Validator \| functions=-
brain/developer/validator/validators/**init**.py \| classes=- \|
functions=- brain/developer/validator/validators/base*validator.py \|
classes=BaseValidator \| functions=-
brain/developer/validator/validators/content*validator.py \|
classes=ContentValidator \| functions=-
brain/developer/validator/validators/dependency*validator.py \|
classes=DependencyValidator \| functions=-
brain/developer/validator/validators/file*validator.py \|
classes=FileValidator \| functions=-
brain/developer/validator/validators/framework*validator.py \|
classes=FrameworkValidator \| functions=-
brain/developer/validator/validators/language*validator.py \|
classes=LanguageValidator \| functions=-
brain/developer/validator/validators/project*validator.py \|
classes=ProjectValidator \| functions=-
brain/developer/validator/validators/structure*validator.py \|
classes=StructureValidator \| functions=- brain/developer/version.py \|
classes=- \| functions=- brain/execution*context.py \|
classes=ExecutionContext,ExecutionContextResolver \| functions=-
brain/execution*engine.py \| classes=- \| functions=-
brain/followup*execution*bridge.py \| classes=FollowUpExecutionBridge \|
functions=- brain/followup*resolver.py \|
classes=FollowUpResolution,FollowUpResolver \|
functions=resolve*follow*up brain/goal*analyzer.py \|
classes=Goal,GoalAnalyzer \| functions=- brain/intent*engine.py \|
classes=IntentResult,IntentEngine \| functions=-
brain/natural/**init**.py \| classes=- \| functions=-
brain/natural/conversation*request.py \|
classes=ConversationRequest,ConversationRequestBuilder \| functions=-
brain/natural/interaction*classifier.py \| classes=InteractionClassifier
\| functions=- brain/natural/interaction*decision.py \|
classes=InteractionDecision \| functions=-
brain/natural/interaction*mode.py \| classes=InteractionMode \|
functions=- brain/natural/meaning*understanding.py \|
classes=MeaningUnderstanding,MeaningUnderstandingEngine \| functions=-
brain/natural/natural*bridge.py \| classes=NaturalConversationBridge \|
functions=- brain/natural/natural*context.py \|
classes=NaturalContext,NaturalContextAggregator \| functions=-
brain/natural/natural*pipeline.py \| classes=NaturalConversationPipeline
\| functions=- brain/natural/response*strategy.py \|
classes=ResponseMode,ResponseStrategy,ResponseStrategyEngine \|
functions=- brain/profile*manager.py \| classes=ProfileManager \|
functions=- brain/prompt*builder.py \| classes=PromptBuilder \|
functions=- brain/reasoning*loop.py \| classes=- \| functions=-
brain/reference*resolver.py \|
classes=ReferenceResolution,ReferenceResolver \|
functions=resolve*reference brain/routing/base*router.py \|
classes=BaseRouter \| functions=- brain/screen*context.py \|
classes=ScreenContextManager \| functions=- brain/screen*followup.py \|
classes=- \| functions=has*screen*context,is*screen*followup,info
brain/task*planner.py \| classes=- \| functions=-
brain/tests/test*clarification*flow.py \| classes=ClarificationFlowTests
\| functions=- brain/tests/test*intent*engine.py \| classes=- \|
functions=- brain/tool*selector.py \| classes=- \| functions=-
chatbot/**init**.py \| classes=- \| functions=- chatbot/ai*chat*api.py
\| classes=- \|
functions=*session*to*dict,create*chat,list*chats,get*chat,delete*chat,rename*chat,send*message,stream*message,get*model,set*model
chatbot/ai*chat*bot.py \| classes=ChatStreamChunk,AIChatBot \|
functions=ask*chat chatbot/ai*chat*clipboard.py \| classes=- \|
functions=copy*text*to*system*clipboard chatbot/ai*chat*session.py \|
classes=ChatMessage,ChatSessionRecord,AIChatSessionManager \|
functions=*utc*now,*ensure*storage,*load*data,*save*data
config/**init**.py \| classes=- \| functions=- config/environment.py \|
classes=- \| functions=load*environment,get*env config/hud*settings.py
\| classes=- \| functions=- config/personal*links.py \| classes=- \|
functions=is*safe*personal*url,configured*links,get*link,has*link
config/settings.py \| classes=- \|
functions=*persisted*assistant*name,get*assistant*name,get*assistant*name*lower,get*assistant*display*name,get*assistant*aliases,get*wake*words,set*assistant*name,*float*setting,*int*setting
config/spotify.py \| classes=- \| functions=- config/whatsapp.py \|
classes=- \| functions=- config/youtube.py \| classes=- \|
functions=get*youtube,search*videos,get*first*video,get*video*list
core/**init**.py \| classes=- \| functions=- core/action*memory.py \|
classes=- \| functions=set*memory,get*memory,clear*memory,dump
core/ai.py \| classes=AI \| functions=- core/app*resolver.py \|
classes=- \| functions=resolve*app core/assistant.py \| classes=- \|
functions=is*morning*brief*enabled,run core/assistant*name.py \|
classes=AssistantInvocation \|
functions=get*assistant*name,get*assistant*name*lower,get*assistant*aliases,is*current*assistant*name,is*legacy*assistant*alias,is*assistant*invocation,strip*assistant*invocation,*invocation*pattern,normalize*assistant*invocation
core/browser*context.py \| classes=BrowserResult,BrowserContext \|
functions=- core/browser*reference.py \|
classes=BrowserReferenceResolver \| functions=- core/browser*worker.py
\| classes=- \| functions=browser*busy,browser*start,browser*stop
core/busy*manager.py \| classes=- \|
functions=is*busy,start*task,finish*task,ask*switch
core/camera*manager.py \| classes=CameraManager \| functions=-
core/command*queue.py \| classes=- \| functions=put,get,empty,clear,size
core/confirmation.py \| classes=- \| functions=ask,get,clear,waiting
core/context.py \| classes=Context \|
functions=set*value,get*value,add*message,get*history,clear,reset*session,update*result,show
core/core*state.py \| classes=- \|
functions=mark*core*ready,wait*for*core,is*core*ready core/dispatcher.py
\| classes=- \| functions=dispatch core/executor.py \| classes=- \|
functions=execute*ai*plan core/executor*worker.py \| classes=- \|
functions=execute*plan core/fallback.py \| classes=- \|
functions=fallback core/fast*router.py \| classes=- \|
functions=fast*route core/file*selection*memory.py \| classes=- \|
functions=set*files,get*files,clear*files core/hud*bridge.py \|
classes=HUDBridge \| functions=- core/intent.py \| classes=Intent \|
functions=extract*intents core/interrupt.py \| classes=- \|
functions=interrupt core/listener.py \| classes=- \|
functions=*dispatch,*callback,start*listener,pause*listener,resume*listener,stop*listener,request*shutdown,shutdown*requested,listener*running,listener*paused,get*command
core/live*execution.py \| classes=- \|
functions=is*live*execution,capture*live*response,get*live*responses,clear*live*responses,live*execution
core/memory.py \| classes=- \| functions=- core/morning*brief.py \|
classes=- \|
functions=*clean*text,*fetch*feed,*deduplicate,fetch*news,build*brief,build*spoken*brief,publish*to*hud,get*morning*brief,*fetch*news*for*startup,start*news*fetch,shutdown
core/path*resolver.py \| classes=- \| functions=resolve core/paths.py \|
classes=- \| functions=- core/pipeline.py \| classes=- \| functions=-
core/planner.py \| classes=- \| functions=execute*plan
core/planner*worker.py \| classes=- \| functions=planner*worker
core/plugins.py \| classes=PluginManager \| functions=register,execute
core/power.py \| classes=- \| functions=sleep,wake,shutdown
core/registry.py \| classes=- \|
functions=register,unregister,get*handler,has*skill,get*skill*category,execute,list*skills,skill*count,list*skill*categories,list*skills*by*category,categorized*skills,registry*info
core/router.py \| classes=- \| functions=route core/routers/**init**.py
\| classes=- \| functions=- core/routers/android*router.py \| classes=-
\| functions=android*route core/routers/automation*router.py \|
classes=- \| functions=automation*route core/routers/browser*router.py
\| classes=- \| functions=browser*route core/routers/contact*router.py
\| classes=- \| functions=contact*route core/routers/email*router.py \|
classes=- \| functions=email*route core/routers/file*router.py \|
classes=- \| functions=file*route core/routers/file*selection*router.py
\| classes=- \| functions=file*selection*route
core/routers/greeting*router.py \| classes=- \|
functions=*with*assistant*aliases,greeting*route
core/routers/media*router.py \| classes=- \| functions=media*route
core/routers/memory*router.py \| classes=- \|
functions=memory*route,*parse*clock*time core/routers/network*router.py
\| classes=- \| functions=network*route core/routers/news*router.py \|
classes=- \| functions=news*route core/routers/payment*router.py \|
classes=- \| functions=payment*route core/routers/phone*call*router.py
\| classes=- \| functions=*target*data,phone*call*route
core/routers/spotify*router.py \| classes=- \| functions=spotify*route
core/routers/system*router.py \| classes=- \| functions=system*route
core/routers/vision*router.py \| classes=- \|
functions=*match*face*delete,*match*face*registration,*normalize*object,*match*object*count,*match*object*existence,*match*object*location,*match*object*target,*match*position,*match*static,vision*route
core/routers/weather*router.py \| classes=- \| functions=weather*route
core/routers/web*router.py \| classes=- \| functions=web*route
core/routers/whatsapp*router.py \| classes=- \| functions=whatsapp*route
core/runtime.py \| classes=- \| functions=handle*priority
core/services.py \| classes=- \|
functions=start*all,stop*all,start*remote*control
core/skill*categories.py \| classes=- \|
functions=action*requires*network,get*category,list*categories,list*actions*by*category
core/speech*queue.py \| classes=- \| functions=worker,say
core/spotify*controller.py \| classes=- \| functions=-
core/task*manager.py \| classes=TaskManager \| functions=-
core/task*queue.py \| classes=- \|
functions=add*task,get*task,has*tasks,clear,size core/task*worker.py \|
classes=- \| functions=worker,start*worker core/tasks.py \| classes=- \|
functions=split*commands core/voice.py \| classes=- \|
functions=speak,stop*speaking core/voice*queue.py \| classes=- \|
functions=add,get,empty core/voice*worker.py \| classes=- \| functions=-
core/wakeword.py \| classes=- \| functions=listen
core/whatsapp*memory.py \| classes=- \|
functions=set*contact,get*contact,clear*contact,set*pending*message,get*pending*message,clear*pending*message
core/workers.py \| classes=- \| functions=chat*worker
dashboard/**init**.py \| classes=- \| functions=- dashboard/server.py \|
classes=DashboardServer \|
functions=create*desktop*shortcut,*make*uploads*dir,*local*ip,*read*static,*derive*key,*decrypt*cbc,*load*english*voice,*save*english*voice
hud/**init**.py \| classes=- \| functions=- hud/adapter.py \|
classes=HUDAdapter \| functions=- hud/bus.py \| classes=HUDEventBus \|
functions=- hud/desktop*window.py \| classes=*WindowApi \|
functions=wait*for*hud,*load*nextjs*when*ready,request*jarvis*shutdown,close*native*window,run
hud/emitter.py \| classes=HUDEmitter \| functions=-
hud/event*contract.py \| classes=HUDEvent \| functions=- hud/events.py
\| classes=HUDEvent \| functions=- hud/integration.py \|
classes=HUDIntegration \| functions=- hud/manager.py \|
classes=HUDManager \| functions=- hud/panels/**init**.py \| classes=- \|
functions=- hud/runtime.py \| classes=HUDRuntime \| functions=-
hud/state.py \| classes=HUDState \| functions=- hud/telemetry.py \|
classes=HUDTelemetry \| functions=- hud/web*bridge.py \|
classes=*Client,*BridgeHandler,HUDWebBridge \| functions=- main.py \|
classes=- \|
functions=start*web*hud,wait*for*web*hud,run*voice*engine,start*voice*engine,run*offline*voice*engine,start*offline*voice*engine,request*jarvis*shutdown,configure*hud*shutdown,start*native*hud,stop*web*hud,initialize*core*background,main
run*jarvis.py \| classes=- \| functions=main
services/android/**init**.py \| classes=- \|
functions=get*android*manager services/android/adb*client.py \|
classes=AdbError,AdbNotFoundError,AdbDeviceError,AdbCommandError,AdbClient
\| functions=normalize*endpoint services/android/android*intents.py \|
classes=- \|
functions=normalize*app*name,standard*intent*for,package*hints*for
services/android/device*manager.py \| classes=AndroidDeviceManager \|
functions=- services/android/models.py \|
classes=AdbCommandResult,AndroidDevice,DeviceStatus,AndroidConnectionStatus,IntentSpec,AppLaunchResult
\| functions=- services/contact*manager.py \| classes=- \|
functions=load*contacts,save*contacts,add*contact,get*contact,resolve*contact,remove*contact,list*contacts,contact*exists,total*contacts
services/email*contact*manager.py \| classes=- \|
functions=load*email*contacts,save*email*contacts,add*email*contact,get*email*contact,resolve*email*contact,remove*email*contact,list*email*contacts,email*contact*exists,total*email*contacts
services/file*manager.py \| classes=- \|
functions=*latest*file,latest*photo,latest*screenshot,latest*video,find*file,latest*file,search*files
services/gmail*service.py \| classes=- \|
functions=*get*credentials,*get*gmail*service,send*email
services/location.py \| classes=LocationService \| functions=-
services/personal*link*service.py \| classes=- \|
functions=show*personal*links,open*personal*link
services/remote*control.py \| classes=RemoteControlServer \|
functions=*local*ip services/spotify*api.py \| classes=- \|
functions=spotify*client,is*spotify*running,ensure*spotify,get*device,resume*playback,pause*playback,search*track,play*track,current*song
services/web*launcher.py \| classes=- \| functions=open*url
services/whatsapp*api.py \| classes=- \|
functions=open*whatsapp,close*whatsapp,open*chat,send*message,send*photo,copy*image*to*clipboard,send*file,call*contact,video*call*contact,focus*whatsapp
services/whatsapp*parser.py \| classes=- \|
functions=parse*scheduled*whatsapp,parse*list*scheduled*whatsapp,parse*cancel*scheduled*whatsapp,parse*reschedule*scheduled*whatsapp,*parse*whatsapp*clock*time,*parse*schedule*time,parse*whatsapp,parse*whatsapp*call,parse*whatsapp*video*call
services/windows*automation.py \| classes=- \|
functions=connect*window,activate*window,activate*whatsapp
skills/**init**.py \| classes=- \| functions=- skills/ai/**init**.py \|
classes=- \| functions=- skills/ai/clarify.py \| classes=- \|
functions=ai*clarify skills/android*control/**init**.py \| classes=- \|
functions=- skills/android*control/android*control.py \| classes=- \|
functions=*say,android*check*adb,android*check*device,android*device*info,android*open*app,android*launch*app
skills/assistant/**init**.py \| classes=- \| functions=-
skills/assistant/greetings.py \| classes=*StartupVariant,GreetingEngine
\|
functions=*time*context,*preferred*name,*fallback*startup,startup*greeting,*get*speaker,speak*startup*greeting,*command*text,*speak,greet,how*are*you,assistant*name,welcome,goodbye
skills/assistant/test*greetings.py \| classes=GreetingEngineTests \|
functions=- skills/automation/home*automation.py \| classes=- \|
functions=*endpoint,control*device,get*hardware*status,home*automation
skills/automation/init.py \| classes=- \| functions=-
skills/browser/**init**.py \| classes=- \| functions=-
skills/browser/browser*ai.py \| classes=- \|
functions=ai*open,ai*google,ai*youtube,browser*open*result
skills/browser/browser*config.py \|
classes=BrowserConfigurationError,BrowserSettings \|
functions=*local*app*data,*configured*path
skills/browser/browser*controller.py \|
classes=BrowserWorker,BrowserController \| functions=-
skills/browser/browser*open.py \| classes=BrowserOpen \| functions=-
skills/browser/browser*resolver.py \|
classes=BrowserExecutableNotFoundError \|
functions=*windows*roots,*candidates,*first*existing,resolve*browser*executable
skills/browser/browser*runtime.py \|
classes=BrowserRuntimeError,BrowserRuntime \| functions=-
skills/browser/navigation.py \| classes=NavigationEngine \| functions=-
skills/browser/youtube.py \| classes=- \|
functions=ai*youtube,youtube*play*first,youtube*pause,youtube*resume,youtube*next,youtube*previous,youtube*play*result
skills/browser/youtube*api.py \| classes=- \| functions=search*videos
skills/browser*control/**init**.py \| classes=- \| functions=-
skills/browser*control/browser*controls.py \| classes=- \| functions=-
skills/camera/**init**.py \| classes=- \| functions=-
skills/camera/camera.py \| classes=- \|
functions=capture,preview,close*camera,start*recording,stop*recording,camera*status
skills/camera/detector.py \| classes=ObjectDetector \| functions=-
skills/camera/face*recognizer.py \| classes=FaceRecognizer \|
functions=*center*inside skills/camera/face*registration.py \|
classes=FaceRegistrationFlow \| functions=*speak
skills/camera/face*registry.py \| classes=FaceRegistry \|
functions=sanitize*name skills/camera/face*speech.py \|
classes=VisionSpeechState \| functions=people*message
skills/camera/scene*analyzer.py \| classes=SceneAnalyzer \| functions=-
skills/camera/spatial*analyzer.py \| classes=SpatialAnalyzer \|
functions=- skills/camera/vision.py \| classes=VisionEngine \|
functions=- skills/camera/vision*analyzer.py \| classes=VisionAnalyzer
\| functions=- skills/camera/vision*loop.py \| classes=VisionLoop \|
functions=- skills/camera/vision*query.py \| classes=VisionQuery \|
functions=- skills/camera/vision*skill.py \| classes=- \|
functions=*start*vision,*stop*vision,vision*start,vision*stop,vision*describe,vision*count,vision*check,vision*position,vision*locate,vision*target,register*face,cancel*face*registration,delete*face
skills/communication/**init**.py \| classes=- \| functions=-
skills/communication/chatgpt.py \| classes=- \| functions=ai*chatgpt
skills/communication/contact.py \| classes=- \|
functions=remember*contact,forget*contact,show*contacts
skills/communication/email.py \| classes=- \|
functions=has*pending*email,clear*email*draft,start*email*draft,handle*email*reply,send*email,remember*email*contact,forget*email*contact,show*email*contacts
skills/communication/github.py \| classes=- \| functions=ai*github
skills/communication/whatsapp.py \| classes=- \|
functions=whatsapp*open,whatsapp*close,whatsapp*send*message,*load*scheduled*whatsapp,*save*scheduled*whatsapp,schedule*whatsapp*message,list*scheduled*whatsapp,cancel*scheduled*whatsapp,reschedule*scheduled*whatsapp,*whatsapp*scheduler*worker,*start*whatsapp*scheduler,whatsapp*send*latest*photo,whatsapp*send*latest*screenshot,whatsapp*send*file,whatsapp*send*selected*file,whatsapp*wait*contact,whatsapp*wait*message,whatsapp*call,whatsapp*video*call
skills/files/**init**.py \| classes=- \| functions=-
skills/files/file*info.py \| classes=- \| functions=info
skills/files/files.py \| classes=- \|
functions=*resolve*path,*path*exists,file*action skills/files/recent.py
\| classes=- \| functions=recent skills/files/recycle.py \| classes=- \|
functions=recycle skills/files/zip*manager.py \| classes=- \|
functions=zip*action skills/loader.py \| classes=- \|
functions=load*skill,load*all,loaded*skills,failed*skills,loader*info
skills/media/**init**.py \| classes=- \| functions=-
skills/media/image*generation.py \| classes=- \| functions=create*image
skills/media/media.py \| classes=- \| functions=ai*play
skills/media/spotify.py \| classes=- \|
functions=spotify*open,spotify*close,spotify*play,spotify*pause,spotify*next,spotify*previous,spotify*volume*up,spotify*volume*down,spotify*play*song
skills/memory/**init**.py \| classes=- \| functions=-
skills/memory/memory.py \| classes=- \|
functions=*recall,*list*memory,memory*command,ai*remember,ai*recall,ai*forget
skills/memory/notes.py \| classes=- \|
functions=*load*notes,*save*notes,create*note,list*notes,clear*notes
skills/memory/reminders.py \| classes=- \|
functions=*load*reminders,*save*reminders,create*reminder,list*reminders,cancel*reminder,*reminder*worker,*start*scheduler
skills/navigation/maps.py \| classes=- \|
functions=maps*open,maps*directions skills/navigation/translate.py \|
classes=- \| functions=translate*open,translate*text
skills/network/**init**.py \| classes=- \| functions=-
skills/network/bluetooth.py \| classes=- \| functions=bluetooth*action
skills/network/weather.py \| classes=- \|
functions=*normalize*location*name,*select*nominatim*result,*query*nominatim,*has*geographic*result,*resolve*location,*detect*current*location,*get*weather,*build*message,weather
skills/network/wifi.py \| classes=- \| functions=*run,wifi*action
skills/news/news.py \| classes=- \| functions=get*news
skills/payments/**init**.py \| classes=- \| functions=-
skills/payments/payments.py \| classes=- \|
functions=*say,*configured*payment*app,make*payment
skills/phone*call/**init**.py \| classes=- \| functions=-
skills/phone*call/monitor.py \| classes=CallSnapshot,PhoneCallMonitor \|
functions=parse*telephony*registry,get*call*monitor,start*phone*call*monitor,stop*phone*call*monitor
skills/phone*call/phone*call.py \| classes=- \|
functions=*say,normalize*phone*number,*normalize*contact*name,*phone*digits,*numbers*match,*spoken*contact*name,*parse*phone*contacts,*provider*field,query*phone*contacts,*find*contact,*start*call,phone*call*number,phone*call*contact,phone*call*confirmed,call*status,*recent*missed*calls,missed*calls,*manual*call*control,answer*call,reject*call,end*call
skills/screen/**init**.py \| classes=- \| functions=-
skills/screen/clipboard.py \| classes=- \| functions=clipboard
skills/screen/screen*vision.py \| classes=ScreenVision \| functions=-
skills/screen/screen*vision*skill.py \| classes=- \|
functions=screen*vision*analyze skills/screen/screenshot.py \| classes=-
\| functions=screenshot skills/screen/screenshot*ai.py \| classes=- \|
functions=screenshot*ai skills/system/**init**.py \| classes=- \|
functions=- skills/system/battery.py \| classes=- \|
functions=battery,*battery*monitor,start*battery*monitor
skills/system/brightness.py \| classes=- \|
functions=current*brightness,set*brightness,brightness
skills/system/process.py \| classes=- \|
functions=*list*processes,process*action skills/system/system.py \|
classes=- \|
functions=*is*windows,*request*confirmation,*shutdown,*restart,*sleep,*lock,*terminate*jarvis,system*action
skills/system/taskmanager.py \| classes=- \| functions=taskmanager
skills/system/volume.py \| classes=- \|
functions=*get*volume*interface,current,set*volume,is*muted,volume*action
skills/utilities/**init**.py \| classes=- \| functions=-
skills/utilities/calculator.py \| classes=- \| functions=-
skills/utilities/search.py \| classes=- \| functions=search*action
skills/utilities/time*skill.py \| classes=- \| functions=current*time
skills/web/personal*links.py \| classes=- \|
functions=personal*link*action tests/test*android*hud*connection.py \|
classes=FakeCompleted,WirelessRunner,UsbRunner,AndroidHudConnectionTests
\| functions=- tests/test*android*payment*routing.py \|
classes=FakeCompleted,FakeRunner,AndroidBridgeTests \| functions=-
tests/test*browser*followup*references.py \|
classes=BrowserFollowUpReferenceTests \| functions=-
tests/test*configuration.py \| classes=ConfigurationTests \| functions=-
tests/test*face*vision.py \|
classes=FaceRegistryTests,FaceSpeechTests,VisionIntegrationTests \|
functions=- tests/test*offline*mode.py \|
classes=OfflineActionBridgeTests,OfflineCommandTests,OfflineAIProviderTests
\| functions=- tests/test*openai*provider.py \|
classes=OpenAIProviderTests \| functions=*error*category
tests/test*personal*website*list.py \| classes=PersonalWebsiteListTests
\| functions=- tests/test*phone*call.py \|
classes=FakeManager,PhoneCallTests \|
functions=*load*phone*skill*without*optional*ai*dependencies
tests/test*remote*event*sync.py \| classes=RemoteEventSyncTests \|
functions=*install*optional*dependency*stubs tools/database*delete.py \|
classes=- \| functions=- tools/windows*integration.py \| classes=- \|
functions=*require*windows,*python*executable,*desktop*directory,create*desktop*shortcut,*startup*directory,*autostart*shortcut*path,get*autostart*status,set*autostart
voice/**init**.py \| classes=- \| functions=- voice/interrupt.py \|
classes=- \| functions=stop,clear,stopped voice/live*conversation.py \|
classes=Agent \|
functions=*api*key,*system*prompt,send*live*text,start*live*conversation,stop*live*conversation,live*conversation*status
voice/manager.py \| classes=- \|
functions=*clean*tts*text,add*speech*listener,remove*speech*listener,*notify*speech*listeners,notify*speech*output,check*internet,start*speech*session,*worker,prepare*speech,play*prepared*speech,speak,wait*for*speech,stop*speaking
voice/mode.py \| classes=- \| functions=internet*available,get*mode
voice/offline/**init**.py \| classes=- \| functions=-
voice/offline/offline*action*bridge.py \|
classes=OfflineRoute,OfflineDispatchResult,OfflineActionBridge \|
functions=- voice/offline/offline*ai.py \| classes=OfflineAI \|
functions=get*ai,ask voice/offline/offline*player.py \| classes=- \|
functions=play,stop voice/offline/offline*runner.py \| classes=- \|
functions=process*command,handle*text*command,run
voice/offline/offline*stt.py \| classes=- \|
functions=initialize,*audio*to*array,*audio*quality,transcribe*audio,calibrate,listen*once
voice/offline/offline*tts.py \| classes=- \|
functions=piper*available,model*available,generate,split*sentences,prepare,play*prepared,speak
voice/offline/offline*voice.py \| classes=- \|
functions=print*banner,run voice/offline*piper.py \| classes=- \|
functions=*piper*available,*model*available,*delete*file,generate*audio,play*audio,speak*offline
voice/online*edge.py \| classes=- \|
functions=*get*voice,set*english*voice,get*english*voice,*cleanup*cache,*delete*file,*generate,generate*audio,play*audio,*worker,speak*online
voice/online*runner.py \| classes=- \| functions=run voice/player.py \|
classes=- \| functions=play,stop,speaking voice/queue.py \| classes=- \|
functions=- voice/runner.py \| classes=- \| functions=run
voice/speech*state.py \| classes=- \| functions=set*speaking,is*speaking
voice/state.py \| classes=SpeechSession \|
functions=create*session,current*session,cancel*current,is*current,is*cancelled
voice/tts*pipeline.py \| classes=TTSPipeline \| functions=-

brain/developer/editor/workspace/**init**.py \| classes=- \| functions=-
brain/developer/editor/workspace/appliers/**init**.py \| classes=- \|
functions=- brain/developer/editor/workspace/appliers/base*applier.py \|
classes=BaseApplier \| functions=-
brain/developer/editor/workspace/appliers/python*applier.py \|
classes=PythonApplier \| functions=-
brain/developer/editor/workspace/appliers/text*applier.py \|
classes=TextApplier \| functions=-
brain/developer/editor/workspace/backup*builder.py \|
classes=BackupBuilder \| functions=-
brain/developer/editor/workspace/code*extractor.py \|
classes=CodeExtractor \| functions=-
brain/developer/editor/workspace/extractors/arduino*extractor.py \|
classes=- \| functions=-
brain/developer/editor/workspace/extractors/base*extractor.py \|
classes=BaseExtractor \| functions=-
brain/developer/editor/workspace/extractors/python*extractor.py \|
classes=PythonExtractor \| functions=-
brain/developer/editor/workspace/extractors/regex*extractor.py \|
classes=RegexExtractor \| functions=-
brain/developer/editor/workspace/file*reader.py \| classes=FileReader \|
functions=- brain/developer/editor/workspace/patch*applier.py \|
classes=PatchApplier \| functions=-
brain/developer/editor/workspace/patch*writer.py \| classes=PatchWriter
\| functions=- brain/developer/editor/workspace/rollback*manager.py \|
classes=RollbackManager \| functions=-
brain/developer/workspace/**init**.py \| classes=- \| functions=-
brain/developer/workspace/builders/**init**.py \| classes=- \|
functions=- brain/developer/workspace/builders/file*builder.py \|
classes=FileBuilder \| functions=-
brain/developer/workspace/builders/folder*builder.py \|
classes=FolderBuilder \| functions=-
brain/developer/workspace/builders/project*builder.py \|
classes=ProjectBuilder \| functions=-
brain/developer/workspace/builders/project*name*resolver.py \|
classes=ProjectNameResolver \| functions=-
brain/developer/workspace/builders/workspace*resolver.py \|
classes=WorkspaceResolver \| functions=-
brain/developer/workspace/models/**init**.py \| classes=- \| functions=-
brain/developer/workspace/models/created*file.py \| classes=CreatedFile
\| functions=- brain/developer/workspace/models/created*folder.py \|
classes=CreatedFolder \| functions=-
brain/developer/workspace/models/workspace*result.py \|
classes=WorkspaceResult \| functions=-
brain/developer/workspace/rules/**init**.py \| classes=- \| functions=-
brain/developer/workspace/rules/workspace*rules.py \| classes=- \|
functions=- brain/developer/workspace/workspace.py \| classes=Workspace
\| functions=- brain/developer/workspace/writers/**init**.py \|
classes=- \| functions=-
brain/developer/workspace/writers/file*writer.py \| classes=FileWriter
\| functions=- brain/developer/workspace/writers/folder*writer.py \|
classes=FolderWriter \| functions=- Non-Python source/configuration
manifest: .env.example brain\\developer\\CHANGELOG.md
brain\\developer\\README.md brain\\developer\\tests\\test.txt
dashboard\\static\\app.html dashboard\\static\\crypto-js.min.js
dashboard\\static\\login.html hud\\web\\app\\ai-chat.css
hud\\web\\app\\globals.css hud\\web\\app\\globals.css.append
hud\\web\\app\\layout.tsx hud\\web\\app\\page.tsx
hud\\web\\components\\AIChatBot.tsx hud\\web\\components\\HudCockpit.tsx
hud\\web\\components\\JarvisOrb.tsx
hud\\web\\components\\PhoneCallIsland.tsx
hud\\web\\lib\\expressiveRobot.ts hud\\web\\lib\\flyingRobot.ts
hud\\web\\lib\\handTracker.ts hud\\web\\lib\\hudBridge.ts
hud\\web\\lib\\jarvisAvatar.tsx hud\\web\\lib\\jarvisFullBody.tsx
hud\\web\\lib\\orbScene.ts hud\\web\\next-env.d.ts
hud\\web\\next.config.ts hud\\web\\package-lock.json
hud\\web\\package.json hud\\web\\public\\models\\flying*robot.glb
hud\\web\\public\\models\\jarvis.glb
hud\\web\\public\\models\\jarvis1.glb
hud\\web\\public\\models\\RobotExpressive.glb hud\\web\\README.md
hud\\web\\tsconfig.json hud\\web\\tsconfig.tsbuildinfo README.md
requirements.txt skills\\automation\\ESP CODE MARK.txt
voice\\models\\en_US-lessac-medium.onnx.json

Non-Python role map: .env / credentials.json / token.json: local secrets
or OAuth artifacts; values intentionally omitted. .env.example:
documented environment-variable template. .gitignore: ignore policy for
Python caches, generated workspaces, secrets, models, Node
dependencies/build output, and local runtime state. requirements.txt:
Python runtime dependency set. hud/web/package.json and
package-lock.json: Next.js frontend dependency and script manifests.
hud/web/tsconfig.json, next.config.ts, next-env.d.ts: TypeScript/Next
configuration. hud/web/app/*, components/*, lib/*: React/TypeScript HUD
pages, cockpit, chat, avatar/robot scenes, bridge, and browser-side
helpers. hud/web/app/*.css and globals.css: HUD visual styling.
hud/web/public/models/\*.glb: frontend 3D model assets.
dashboard/static/app.html and login.html: legacy/alternate
phone-friendly remote dashboard HTML clients served by Python dashboard
code; they are not the Next.js app. README files and text files: human
documentation, test notes, or automation notes; not runtime entry points
unless explicitly imported. binary model/audio/image files: runtime
assets or generated/local data; not source modules.

Important source-file descriptions: main.py: Active startup coordinator.
Loads configuration, selects online/offline voice mode, initializes
skills/memory/services in a background thread, starts HUD
runtime/bridge, starts Next.js, starts DashboardServer, starts the voice
engine, opens native pywebview, and performs shutdown. run*jarvis.py:
Shortcut-safe wrapper around main.py; redirects output to
data/logs/shortcut*startup.log and preserves startup failures.
config/settings.py: Authoritative assistant name, aliases,
version/author/voice settings, Ollama defaults, vision thresholds, and
persisted customization. config/environment.py: Loads .env once and
exposes environment lookup helpers. core/assistant.py: Legacy/online
microphone-driven command loop. Handles greetings, follow-ups,
confirmations, interruptions, planning and dispatch. core/dispatcher.py:
Shared command dispatcher. Normalizes invocation, gives pending
clarification/email/face-registration state priority, invokes fast
routes, BrainRouter, planner workers, registry actions, and follow-up
bridges. core/fast_router.py and core/routers/\*: Deterministic route
layer. Ordered routers cover phone calls, payments, memory, news,
weather, personal links, automation, Spotify, browser, greetings,
system, network, media, vision, Android, files, email, contacts,
WhatsApp, and file selection. core/registry.py: Global action registry:
register, unregister, lookup, execute, category queries, and fallback
handling. skills/loader.py: Import-time skill loader with an explicit
list of 46 configured module paths, loaded/failed diagnostics, and
continue-on-error behavior. core/services.py: Starts/stops the
phone-call monitor. Its optional start*remote*control helper constructs
services.remote_control.RemoteControlServer, but main.py directly uses
dashboard.server.DashboardServer. ai/core/\*:
ModelDefinition/ModelRegistry, policy/preferences, selection manager,
request/response schemas, AIRouter, and AIService public interface.
ai/providers/ollama.py: Local HTTP generation/streaming against
Ollama\'s /api/generate. ai/providers/gemini.py: Google GenAI
generation/streaming, image/context support, quota/error detection, and
optional API-key-backed operation. ai/providers/openai.py: OpenAI
generation/streaming with Windows TLS/truststore handling and
OPENAI*API*KEY lookup. brain/brain_router.py: Detects developer-like
requests and routes CREATE to Developer pipeline or EDIT requests
through active-project resolution/editor logic. brain/developer/\*:
Large developer subsystem: analyzer/detectors/resolvers/rules, planner
variants, prompt builders, Ollama generators, validators, repair,
workspace builders/writers, editor/parser/patch/rollback tooling, memory
models, integration tests, and compatibility APIs.
brain/conversation\_\* / natural/*: conversation state, context,
intent/meaning understanding, response strategy, and natural-language
bridges. brain/clarification*manager.py: Temporary
field/question/task/owner/metadata state with a 120-second timeout; it
records and resolves conversational clarification but does not execute
commands itself. brain/profile*manager.py: JSON-backed user profile
manager used by context/prompt construction. ai/memory*.py: Explicit
memory learning, storage, search/ranking/semantic helpers,
profile/preference/forget/stats/view APIs. Runtime persistence is
generally under ai/memory.db and related local data. voice/\*: Online
Edge TTS and SpeechRecognition path, offline Faster-Whisper, Piper TTS,
shared voice state/queues, and Gemini Agent.
services/remote_control.py: Optional thin FastAPI remote service with
PIN pairing and bearer token; compatible with the dispatcher but not the
primary object started by current main.py. dashboard/server.py: Active
FastAPI server. Serves local/remote dashboard HTML, APIs for
commands/settings/history/AI chat/Android/upload/customisation,
WebSocket event/audio channels, and pairing/authentication. hud/\*:
Python HUD state/event contracts, manager, bus, telemetry, native
window, and passive SSE web bridge. hud/web_bridge.py includes an older
commented implementation plus the active bridge. services/*:
OS/browser-adjacent adapters: Android/ADB, email/Gmail, contacts, files,
location, personal links, Spotify, WhatsApp, Windows automation, and web
launch. tests/*: Top-level regression/feature tests; individual test
descriptions are listed in Section 30. tools/\*: Windows
integration/database maintenance helpers; development/supporting rather
than automatic startup components.

Runtime status vocabulary: Active: imported by main or on the live
command path. Supporting: used by active modules or selected
conditionally. Test: test-only or manual validation.
Compatibility/legacy: retained API, alternate implementation, or older
architecture. Generated/local: runtime state, assets, caches, dependency
installation, or workspace output. Unknown: source presence alone does
not prove runtime use.

# 6. HIGH-LEVEL ARCHITECTURE

Confirmed online path: USER MICROPHONE / HUD TEXT / REMOTE TEXT \| v
voice listener or DashboardServer command endpoint \| v
core.dispatcher.dispatch() \| +\--\> assistant invocation normalization
+\--\> pending face-registration / clarification / email state +\--\>
deterministic core.fast*router.fast*route() \| \| \| +\--\>
core.registry.execute(action) \| +\--\> skill/service result \| +\--\>
BrainRouter developer request detection +\--\>
conversation/NCI/context/follow-up handling +\--\> planner worker / AI
plan +\--\> core.executor / registry action execution \| v response,
voice manager, HUD event bus, remote event stream

Confirmed offline path: microphone or typed HUD text -\> Faster-Whisper
STT (voice only) -\> OfflineActionBridge -\> local deterministic action
or OfflineAI -\> Ollama local model for non-action conversation -\>
Piper TTS -\> shared HUD/action/event systems

Boundaries: - Fast routes are deterministic and ordered. - AI provider
routing is separate from action registration. - Brain developer routing
is separate from normal skills. - HUD receives state/events and provides
text/settings interfaces; it does not replace the Python dispatcher. -
Remote Control is a transport/UI layer over existing command handling. -
Vision has separate camera, YOLO scene, face-recognition, and
screen-vision domains.

# 7. APPLICATION STARTUP FLOW

    START
      |
      v
    import config -> load .env and settings
      |
      v
    get_mode() -> network probe -> "online" or "offline"
      |
      v
    initialize_core_background thread:
        load_all skills
        init_memory
        start_all services / phone-call monitor
        mark_core_ready
      |
      +--> start HUD runtime and passive web bridge
      +--> start Next.js HUD at http://127.0.0.1:3000
      +--> register HUD shutdown callback
      |
      +--> online:
      |       create DashboardServer on port 8765
      |       create pairing PIN
      |       start online voice thread
      |
      +--> offline:
              set JARVIS_OFFLINE_MODE
              create local DashboardServer on port 8765
              start offline STT/AI/TTS voice thread

      |
      v
    wait for Next.js readiness
      |
      v
    start native pywebview HUD on the main thread
      |
      v
    READY / command loop
      |
      v
    native-window close, Ctrl+C, listener exit, or voice failure
      |
      v
    request shutdown -> stop listener -> close native HUD
      -> stop services/HUD bridge/Next.js -> terminate process

Startup notes: pywebview is deliberately run on the main thread. Core
initialization is backgrounded so HUD startup can proceed. Offline mode
changes providers, not the shared action registry/core. The final
main.py cleanup calls os.\_exit(0), so shutdown is intentionally
forceful after cleanup attempts.

# 8. COMMAND PROCESSING PIPELINE

Priority established by dispatcher: 1. empty input / pending
clarification reply 2. known assistant invocation normalization 3.
pending face registration input 4. pending clarification
resolution/cancel/new request 5. pending email composition reply 6.
Agent control commands 7. legacy clarification contexts such
as Google/YouTube/GitHub choice 8. screen/browser/file follow-up
resolution and action memory 9. deterministic fast route 10. BrainRouter
developer path 11. AI intent/conversation/planner path 12. action
execution, result output, and memory/HUD updates

Invocation handling: normalize*assistant*invocation accepts only
configured explicit aliases, with optional leading \"hey\" or \"hello\".
It strips the alias before routing. Current configured name and the
explicit legacy alias \"jarvis\" are supported; pronunciation aliases
include \"JARVIS PRO\" and \"ashtra\" in settings.

Examples confirmed by routers/actions: \"hey jarvis \...\" -\> alias
normalization if alias list matches current settings. \"take a photo\",
\"open camera\", \"start vision\", \"what do you see\" \"open youtube\",
\"search google \...\", \"play \... on youtube\" \"make payment\" /
\"make payment using `<app>`{=html}\" \"open file\", \"create folder\",
\"recent files\", \"zip \...\", \"recycle bin\" \"wifi status\",
\"bluetooth status\", \"weather\", \"get news\" \"open whatsapp\",
\"send whatsapp message\", \"send email\" \"start Agent\",
\"stop Agent\" \"create note\", \"list reminders\",
\"remember \...\" \"volume\", \"brightness\", \"battery\", \"running
apps\", \"lock\", \"sleep\" These are representative source-confirmed
patterns, not a promise that external dependencies or devices are
available.

# 9. ASSISTANT IDENTITY / NAME SYSTEM

Sources: config/settings.py is authoritative. core/assistant_name.py
provides normalization and compatibility exports. core/listener.py and
core/dispatcher.py consume the normalized invocation. dashboard and HUD
replace name placeholders or load the settings API.

Behavior: - APP*NAME begins as JARVIS PRO. -
data/settings/jarvis*settings.json may override it through
assistantName. - PRONUNCIATION*ALIASES = (). - LEGACY*ASSISTANT*ALIASES
= (\"jarvis\",). - aliases are explicit; matching is not fuzzy. -
runtime set*assistant*name updates APP*NAME in-process and persists
settings. - the dashboard customisation endpoint can change the
configured identity. - technical JARVIS names remain in
storage/protocols/modules for compatibility.

# 10. AI ARCHITECTURE

AI control points: ai/core/schemas.py request/response/stream/error
contracts ai/core/registry.py model definitions and enabled model
registry ai/core/policy.py capability/provider preference policy
ai/core/preference.py temporary user provider/model preference
ai/core/model*manager.py capability-aware model selection
ai/core/router.py availability, generation, streaming, cooldown,
fallback ai/core/service.py public AIService facade ai/chat.py,
ai/ai*worker.py, ai/llm.py compatibility/chat/background consumers

Registered model families confirmed in source: Ollama: jarvis,
qwen2.5:3b, qwen3:4b Gemini: gemini-3.6-flash, gemini-3.5-flash,
gemini-3.5-flash-lite OpenAI: model definitions/provider support are
present; exact runtime default selection depends on registry/policy
configuration.

Provider summary: PROVIDER: Ollama MODELS: jarvis, qwen2.5:3b, qwen3:4b
and configured explicit model names IMPLEMENTATION:
ai/providers/ollama.py; voice/offline/offline_ai.py GENERATION: local
HTTP POST to configured Ollama API STREAMING: implemented in provider
contract and provider FALLBACK ROLE: local/offline provider and policy
candidate ERROR HANDLING: unavailable response/error, stream errors,
router fallback STATUS: implemented; requires a reachable local Ollama
service/model.

    PROVIDER: Google Gemini
    MODELS: Gemini model names registered above; Agent also uses
            a Gemini Live path in voice/agent.py
    IMPLEMENTATION: ai/providers/gemini.py; voice/agent.py
    GENERATION: Google GenAI client, including text and supported multimodal
                context paths
    STREAMING: implemented
    FALLBACK ROLE: preferred model family for many capabilities in ModelManager
    STATUS: implemented in source; requires GEMINI_API_KEY and service access.
            Quota/rate-limit errors trigger temporary model cooldown.

    PROVIDER: OpenAI
    MODELS: provider-compatible configured models
    IMPLEMENTATION: ai/providers/openai.py
    GENERATION: OpenAI client
    STREAMING: implemented
    FALLBACK ROLE: registered/provider-compatible fallback or explicit selection
    STATUS: implemented in source; requires OPENAI_API_KEY and a usable model.
            Runtime availability depends on registry/policy and configuration.

Fallback/cooldown: AIRouter tries policy/model candidates, checks
availability, catches generation errors, recognizes quota/rate-limit
markers such as 429 and RESOURCE_EXHAUSTED, and applies a 15-minute
per-router model cooldown (or a longer provider retry delay when
parsed). This is fallback logic, not proof that all configured providers
are usable.

# 11. AGENT / BRAIN / PLANNER SYSTEM

Normal AI/planner: core.dispatcher -\> ai.intent / brain conversation
components -\> planner_worker/core.planner -\> core.executor -\>
core.registry actions.

BrainRouter: brain/brain_router.py detects developer vocabulary and
phrases. CREATE requests go to brain.developer.Developer. EDIT requests
resolve an active project and use developer editor behavior. Results may
return as BrainResult(handled,module,result).

Developer subsystem: brain/developer/pipeline/developer_pipeline.py
composes analyzer, planner, prompt builder, generator, validator,
workspace, and repair stages. The analyzer detects
language/framework/board/project/runtime/workspace. Planners include
Python, JavaScript, C++, Arduino, ESP32, and general paths. Editor
modules support project scan, target location, edit planning, parsing,
patch writing, validation, backups, rollback, and workspace appliers.
Developer memory stores project/file/edit/style/session records. Many
tests cover this subsystem. The source contains both newer centralized
BrainRouter integration and a substantial older Developer architecture;
both are documented as present, but presence alone does not prove every
branch is used for every command.

# 12. CONVERSATION SYSTEM

brain/conversation_manager.py: maintains structured Message entries and
bounded conversation history, with persistence helpers.

brain/conversation*context.py and conversation*state.py: hold current
request/context/state used by follow-up resolution.

brain/context*builder.py and brain/prompt*builder.py: assemble profile,
conversation, memory, project/screen context and instruction/prompt
material for AI-facing paths.

brain/natural/\*: natural request/meaning classification, interaction
mode and response strategy bridge.

core/context.py and core/action_memory.py: lightweight runtime
values/action context used by deterministic and follow-up paths.

chatbot/\*: independent dashboard AI chat sessions/history; the HUD
explicitly labels this as independent Gemini chat and not the main
assistant conversation.

# 13. CLARIFICATION SYSTEM

Unified conversational state: brain/clarification_manager.py stores
waiting, field, question, task, owner, metadata, creation time, and a
120-second timeout. resolve() returns structured data; the manager does
not execute commands.

Dispatcher interaction: - pending clarification is checked before normal
fast routing/AI handling; - an answer may merge into the original
request and re-enter planner_worker; - cancellation clears the state; -
a new known assistant invocation preempts stale clarification; -
explicit new requests can clear stale state; - older
core.context/confirmation/memory clarification mechanisms remain
authoritative in their own features.

Confirmed source examples: generic action context can ask whether to use
Google, YouTube, GitHub, or ChatGPT; follow-up answers such as
\"google\", \"youtube\", \"github\", or \"chatgpt\" are recognized by
dispatcher logic. Exact natural examples like \"Which file should I
edit?\" are not asserted globally unless a relevant active module
handles that field.

# 14. MEMORY SYSTEM

Persistent/structured memory: ai/memory*schema.py, memory*store.py,
memory*manager.py, memory*search.py, memory*rank.py, memory*semantic.py,
memory_pipeline.py and related modules implement explicit
facts/preferences/profile-style memory, search/ranking,
confidence/forget/stats/view operations. ai/memory.db is a local
application database if present.

Conversation context: in-memory conversation messages and current
request context; not the same as durable explicit memory.

Profile: brain/profile_manager.py stores/loads user profile JSON and
contributes profile data to context/prompt generation.

Developer memory: brain/developer/memory/\* stores
project/file/dependency/edit/style/session records and is separate from
general user memory.

Workspace memory: generated workspace projects contain .jarvis*memory
and .jarvis*backups artifacts. These belong to generated projects, not
necessarily the main assistant database.

What is actually learned: explicit pattern-based memory modules
recognize supported forms such as \"my name is\", preference/favorite,
contact/email/memory actions. The code does not establish unrestricted
autonomous learning.

# 15. PERSONALIZATION / USER PROFILE

Settings/profile surfaces include: assistant name, user name, assistant
colour, selected voice, morning brief, microphone/Agent
toggles, HUD visibility toggles, personal links, contacts, email
contacts, WhatsApp contacts, and remembered facts.

Persistence is split: data/settings/jarvis*settings.json for UI
customization; profile manager storage for profile/context; memory
database/files for explicit memory; workspace .jarvis*\* directories for
developer project state; runtime globals/queues for temporary session
state.

The current settings file was inspected only for non-secret identity
behavior; personal values are not reproduced here.

# 16. SKILL ARCHITECTURE

Skill packages present: ai, android*control, assistant, automation,
browser, browser*control, camera, communication, files, media, memory,
navigation, network, news, payments, phone_call, screen, system,
utilities, web.

Important skill capabilities: AI: clarification action. Android: ADB
availability/device/app launch/info. Assistant: greetings, name,
welcome/goodbye. Automation: home automation and ESP32-oriented notes.
Browser: browser open/search/result and YouTube operations. Browser
control: tabs, navigation, scrolling, refresh/close. Camera: camera
capture/preview/recording/status. Vision: YOLO scene actions,
count/position/locate/target, face register/delete. Communication:
ChatGPT search, GitHub search, contacts, email, WhatsApp. Files:
open/create/copy/move/rename/delete, recent/recycle/zip/extract. Media:
generic media, image generation, Spotify. Memory: notes/reminders and
explicit memory actions. Navigation: Maps and translation. Network:
Wi-Fi, Bluetooth, weather. News: news retrieval. Payments: Android
payment-app/UPI chooser handoff only. Phone call: number/contact call,
monitor/status and call control boundaries. Screen: clipboard,
screenshot, screenshot AI, screen vision. System: battery, brightness,
processes, task manager, volume, shutdown/lock. Utilities: file search,
time. Web: personal links.

A skill file can exist without being loaded. The authoritative
configured import list is skills/loader.py; modules outside that list
may be supporting, legacy, or route-only code.

# 17. SKILL LOADING / REGISTRATION

    main.initialize_core_background()
        -> skills.loader.load_all()
        -> import_module("skills." + configured_name)
        -> module-level register(...) calls
        -> core.registry.SKILLS / SKILL_CATEGORIES

The loader records configured, loaded, and failed lists and continues
after a module import error. Registration is explicit and occurs as a
side effect of module import. main.py adds the three Agent
actions after core startup.

Action registry behavior: register(name, handler, category) get*handler
/ has*skill / get*skill*category execute(name, data) list*skills /
list*skill*categories / categorized*skills fallback handler for
missing/unavailable actions.

# 18. BROWSER SYSTEM

Current browser design: skills/browser/browser*config.py resolves
host/port/executable/profile. Default CDP host is 127.0.0.1 and default
port is 9223. browser*resolver.py discovers Chrome/Edge/Chromium
executables or validates JARVIS*BROWSER*EXECUTABLE. browser*runtime.py
owns a Chromium process/profile and a verified CDP endpoint with
ownership/session markers; it does not adopt arbitrary existing
endpoints. browser*controller.py uses Playwright sync API through CDP
and manages tabs, navigation, search, page/result context, and YouTube
context. browser*ai.py, browser*open.py, navigation.py and youtube.py
adapt actions and conversational follow-ups. core/browser*context.py and
browser*reference.py retain sequential result, current/previous/next
video, tab and search context.

Browser configuration: JARVIS*BROWSER*CDP*HOST, JARVIS*BROWSER*CDP*PORT,
JARVIS*BROWSER*EXECUTABLE, JARVIS*BROWSER*PROFILE_DIR. Values are not
copied from .env.

# 19. VISION SYSTEM

Camera: core.camera_manager and skills/camera/camera.py own
capture/preview/record lifecycle.

YOLO: skills/camera/detector.py uses the local Ultralytics YOLO model
asset yolo11n.pt for object/person detection. vision.py/vision*skill.py,
vision*analyzer.py, scene*analyzer.py and vision*loop.py form the
continuous scene path. VisionLoop stabilizes scene signatures across
frames.

Face recognition: face*recognizer.py uses YOLO person boxes to derive
head/upper-body crops, OpenCV LBPH recognition, a local FaceRegistry,
and samples under data/faces. face*registration.py handles sample
capture/registration and deletion/cancellation. Threshold, minimum
size/quality, sample count, attempts, interval, and speech cooldown are
environment-backed settings. This is distinct from generic object
detection.

Screen vision: screen/screen*vision.py, screen*vision*skill.py and
screenshot*ai.py provide screen capture/analysis paths. Exact provider
availability depends on AI configuration.

Hardware behavior: source supports lazy optional OpenCV/vision imports;
exact CPU/GPU choice is not globally guaranteed from source. The bundled
detector/model and installed Ultralytics/OpenCV dependencies determine
actual operation.

# 20. VOICE SYSTEM

Online: voice.mode.py probes network and selects online/offline.
voice.online*runner.py calls core.assistant.run. core.listener.py uses
SpeechRecognition/PyAudio input and dispatch callback. voice.manager.py
coordinates speech state, queues/listeners, interruption,
preparation/playback and TTS choice. voice.online*edge.py uses Edge TTS
with cached MP3 output and selectable English/Indian/other language
voice mappings.

Offline: voice.offline.offline*stt.py uses Faster-Whisper
(small/cpu/int8 defaults) for local transcription, calibration and
audio-quality filtering. voice.offline.offline*ai.py uses Ollama plus
shared profile/conversation/ context/prompt components.
voice.offline.offline*tts.py uses Piper process/model output and
playback. offline*runner.py runs typed and microphone commands through
the shared OfflineActionBridge and avoids duplicate local-action speech.

Agent: voice/agent.py contains a separate Gemini
Live session, microphone/audio streaming, typed-to-live integration,
interruption and session lifecycle. main.py registers start/stop/status
actions after startup.

Voice status: startup greeting, HUD speaking/listening/thinking/idle
state, stop-speaking and interruption are implemented. Actual
online/offline success depends on network, audio devices, model files,
and service configuration.

# 21. REMOTE CONTROL

Active path: main.py constructs dashboard.server.DashboardServer with
core.dispatcher as command_handler, a live stop handler, a generated
six-character PIN, and port 8765. The server is optional at runtime if
dependencies fail; main logs the failure and continues toward HUD/voice.

DashboardServer responsibilities: local/LAN URL and pairing URL, PIN
lifecycle, bearer-token authorization, static remote UI, command
endpoints, event transport, phone microphone/audio handling,
upload/settings/customisation, Android status/connect/disconnect, AI
chat APIs, system/voice settings, and WebSocket routes.

Compatibility path: services/remote*control.py defines another
RemoteControlServer on port 8765 with a similar PIN/bearer-token model
and dispatcher adapter. core.services exposes start*remote_control(),
but current main.py uses DashboardServer directly. Treat the former as
alternate/compatibility infrastructure, not the active object in the
normal main startup path.

Security/transport: pairing uses short-lived PINs (600-second expiry in
source), then bearer authorization. The service uses FastAPI/Uvicorn and
browser/WebSocket clients. This is a command transport/UI, not a second
brain. It is optional, and payment is not implemented as dependent on
remote control.

# 22. HUD / FRONTEND

Python HUD: hud/events.py defines event/state names and HUDEvent.
hud/bus.py provides thread-safe publish/subscribe. hud/manager.py
mutates HUDState and emits voice/task/AI/system/activity/
response/error/personal-link events. hud/integration.py exposes the
application-facing facade. hud/telemetry.py reads CPU/RAM/battery
through psutil. hud/runtime.py manages periodic runtime updates.
hud/desktop*window.py opens a 900x600 native pywebview window and
requests shutdown when closed. hud/web*bridge.py is a passive SSE bridge
at port 8766 with health/state/ events/shutdown behavior; an older
implementation remains commented above the active implementation.

Next.js/React: hud/web/app/page.tsx is the main client page and
integrates bridge events, command entry, activity log, settings,
remote/Android modals, morning brief, phone-call island, microphone
waveform, AI chat, QR pairing and cockpit. HudCockpit.tsx renders
assistant state, system gauges, activity and quick tools. AIChatBot.tsx
provides independent chat history/model/message APIs. JarvisOrb.tsx,
PhoneCallIsland.tsx and lib/\* provide visual/3D/hand-tracker/
avatar/bridge helpers. package.json scripts are dev, build, start. The
repo currently starts npm run dev from main.py rather than an
independently managed production build.

# 23. SYSTEM MONITOR

Confirmed telemetry: CPU percent, RAM percent, battery percent (when
psutil and a battery are available), timestamp, system status, and
uptime/state are emitted to HUD. hud/web components format CPU/RAM/BAT
gauges and uptime. Missing psutil/sensors produce unavailable/null
values rather than invented values. Exact update cadence is controlled
by hud/runtime.py and telemetry calls; source confirms periodic runtime
management but this document does not claim a fixed interval unless the
active runtime configuration changes.

# 24. PERSONAL WEBSITES / LINKS

config/personal*links.py defines named link slots backed by environment
values. services/personal*link*service.py validates/opens or displays
configured links through the browser controller and HUD integration.
skills/web/personal*links.py registers open*personal*link and
show*personal*links. dashboard/HUD expose link data and UI. URL values
are not reproduced. Blank/missing links are treated as unavailable;
source validation accepts HTTP/HTTPS URL forms.

# 25. PAYMENT SYSTEM

skills/payments/payments.py and core/routers/payment*router.py implement
the make*payment action for \"make payment\" and \"make payment
using/with `<app>`{=html}\".

Implemented: - optional ANDROID*DEFAULT*PAYMENT_APP selection; - Android
app launch through the shared safe ADB bridge; - generic upi://pay
intent to let Android choose an installed app; - spoken/user-facing
instructions to continue in the official app.

Not implemented by this repository: - automatic recipient/amount parsing
into a completed transfer; - QR capture/scanning flow inside JARVIS; -
PIN, OTP, CVV, biometric, or final authorization entry; - automatic
money transfer confirmation.

Payment request preparation: opening a selected payment app or UPI
chooser is the preparation/hand-off.

Actual payment authorization: remains entirely inside the official
Android payment application and under user control. Remote Control is
not required for the payment action; Android connectivity/ADB is the
relevant dependency for app launch.

# 26. CONFIGURATION

Primary configuration sources: config/environment.py loads .env.
config/settings.py stores defaults and typed setting helpers.
config/hud*settings.py stores HUD settings. config/personal*links.py,
config/spotify.py, config/youtube.py, config/whatsapp.py provide
integration-specific settings. data/settings/jarvis_settings.json stores
runtime customization.

Selected settings: APP*NAME / assistantName: identity and display;
built-in default JARVIS PRO; persisted override. AI*PROVIDER: source
default ollama; actual routing also uses model policy/registry.
OLLAMA*MODEL: source default qwen2.5:3b in config; offline*ai retains
jarvis default unless OLLAMA*MODEL is explicitly set there. OLLAMA*URL:
local Ollama API endpoint, default localhost:11434/api/generate.
browser: CDP host/port/executable/profile overrides. vision: face
threshold/min size/quality/registration controls. dashboard: source port
8765; HUD bridge source port 8766; Next HUD source port 3000.

Configuration table: SETTING / VARIABLE REQUIRED SECRET DEFAULT / NOTE
GEMINI*API*KEY no\* yes blank; Gemini OPENAI*API*KEY no\* yes blank;
OpenAI YOUTUBE*API*KEY no\* yes blank; YouTube API SPOTIFY*CLIENT*ID
no\* yes blank; Spotify SPOTIFY*CLIENT*SECRET no\* yes blank; Spotify
SPOTIFY*REDIRECT*URI no no localhost:8888 OLLAMA*API*URL no no local
Ollama URL JARVIS*ESP32*IP no no blank JARVIS*LIVE*MODEL no no
blank/provider use ANDROID*ADB*PATH no no PATH or
C:\\platform-tools\\adb.exe ANDROID*DEVICE*ID no no blank/selected
device ANDROID*DEFAULT*PAYMENT*APP no no blank/chooser
JARVIS*VISION*FACE*RECOGNITION*THRESHOLD no no 75
JARVIS*VISION*FACE*MIN*SIZE no no 80 JARVIS*VISION*FACE*MIN*QUALITY no
no 0.20 JARVIS*VISION*REGISTRATION*SAMPLE*COUNT no no 5
JARVIS*VISION*REGISTRATION*MAX*ATTEMPTS no no 30
JARVIS*VISION*REGISTRATION*SAMPLE*INTERVAL no no 0.25
JARVIS*VISION*SPEECH*COOLDOWN no no 5 PERSONAL*\* / JARVIS*\**URL no no
blank; link slots JARVIS*BROWSER*CDP*HOST no no 127.0.0.1
JARVIS*BROWSER*CDP*PORT no no 9223 JARVIS*BROWSER*EXECUTABLE no no auto
discovery JARVIS*BROWSER*PROFILE*DIR no no runtime profile

\*Required only for the corresponding configured feature/provider. No
secret values are included.

# 27. ENVIRONMENT VARIABLES

Names present in .env.example: GEMINI*API*KEY, OPENAI*API*KEY,
YOUTUBE*API*KEY SPOTIFY*CLIENT*ID, SPOTIFY*CLIENT*SECRET,
SPOTIFY*REDIRECT*URI OLLAMA*API*URL, JARVIS*ESP32*IP, JARVIS*LIVE*MODEL
ANDROID*ADB*PATH, ANDROID*DEVICE*ID, ANDROID*DEFAULT*PAYMENT*APP
JARVIS*VISION*FACE*RECOGNITION*THRESHOLD JARVIS*VISION*FACE*MIN*SIZE,
JARVIS*VISION*FACE*MIN*QUALITY JARVIS*VISION*REGISTRATION*SAMPLE*COUNT
JARVIS*VISION*REGISTRATION*MAX*ATTEMPTS
JARVIS*VISION*REGISTRATION*SAMPLE*INTERVAL JARVIS*VISION*SPEECH*COOLDOWN
PERSONAL*GITHUB*URL, PERSONAL*GITHUB*PROFILE*URL,
PERSONAL*GITHUB*REPOSITORIES*URL, PERSONAL*FACEBOOK*URL,
PERSONAL*FACEBOOK*PROFILE*URL, PERSONAL*LINKEDIN*URL,
PERSONAL*LINKEDIN*PROFILE*URL, PERSONAL*WEBSITE*URL,
PERSONAL*PORTFOLIO*URL, PERSONAL*IOT*URL, PERSONAL*IOT*WEBSITE*URL,
IOTRIX*LAB*URL, JARVIS*GITHUB*URL, JARVIS*REPOSITORY*URL,
SMART*PARKING*URL, ATMERS*URL JARVIS*BROWSER*CDP*HOST,
JARVIS*BROWSER*CDP*PORT, JARVIS*BROWSER*EXECUTABLE,
JARVIS*BROWSER*PROFILE_DIR

Additional runtime setting names appear in code (for example
OLLAMA*MODEL, NEXT*PUBLIC*JARVIS*OFFLINE,
NEXT*PUBLIC*JARVIS*DASHBOARD*URL, and
NEXT*PUBLIC*JARVIS*HUD*BRIDGE_URL). Exact effective value depends on
startup environment and dashboard settings.

# 28. EXTERNAL SERVICES / INTEGRATIONS

SERVICE PURPOSE STATUS FROM SOURCE Ollama local AI/offline AI
implemented; local service required Google Gemini/GenAI cloud
text/vision/live implemented; key/service required OpenAI cloud provider
implemented; key/model required Google/YouTube APIs YouTube
search/results implemented; key required Chrome/Edge/Chromium CDP
browser automation implemented conditionally FastAPI/Uvicorn
dashboard/remote HTTP implemented Next.js/React HUD frontend
implemented; npm required SpeechRecognition/PyAudio microphone input
implemented conditionally Faster-Whisper offline STT implemented
conditionally Piper TTS offline speech implemented conditionally Edge
TTS online speech implemented conditionally OpenCV/Ultralytics YOLO
camera/object/face support implemented conditionally Android ADB
device/apps/UPI/phone bridge implemented conditionally Spotify/Spotipy
desktop playback implemented conditionally WhatsApp desktop UI
automation/messaging implemented conditionally Gmail API/OAuth email
sending implemented conditionally Google Maps/translation
navigation/browser links implemented conditionally Windows APIs/tools
system, clipboard, windowing implemented conditionally MediaPipe/Three
frontend interaction/3D frontend dependency/assets

No Firebase or Google Apps Script integration was confirmed in the
audited source paths. A service listed in code is not proof that
credentials/device/ network access is present.

# 29. DEPENDENCIES

Python requirements grouped by source manifest: Core/UI/voice: requests,
pywebview, SpeechRecognition, PyAudio, edge-tts, pygame, pyttsx3.
Offline voice: numpy, sounddevice, faster-whisper, piper-tts. AI/Google:
openai, google-genai, python-dotenv, google-api-python-client,
google-auth-oauthlib, google-auth-httplib2, truststore. Dashboard:
fastapi, uvicorn\[standard\], python-multipart, cryptography.
Browser/media: playwright, spotipy, pynput. Windows: psutil, pyautogui,
pyperclip, pywin32, pywinauto, comtypes, pycaw,
screen-brightness-control, Send2Trash, WinRT geolocation. Vision:
opencv-contrib-python, Pillow, ultralytics.

Node dependencies: Next 16, React 19, TypeScript, Three, MediaPipe tasks
vision, QR code, React Markdown/syntax highlighting, TanStack virtual,
remark-gfm and corresponding type packages. hud/web/package-lock.json is
present. hud/web/node_modules is installed locally and is generated
dependency data.

External applications commonly required: Python 3, npm/Node, Ollama for
local AI, Chrome/Edge/Chromium for CDP, microphone/audio device,
optional Android platform-tools/ADB, optional WhatsApp/Spotify/desktop
apps, optional camera, and Windows GUI/audio APIs.

# 30. TESTING

Observed test inventory: tests/ (11 top-level files): Android/HUD
connection, Android payment routing, JARVIS PRO routing, browser
follow-up references, configuration, face vision, offline mode, OpenAI
provider, personal website list, phone call, remote event sync.
brain/tests/: clarification flow, intent engine. brain/developer/tests/:
analyzer, board/framework/intent/language/project/runtime/workspace
detectors, enums/foundation, generator, planner, prompt builder, repair,
validator, workspace. brain/developer/editor/tests/: backup builder,
editor engine/editor, parser, patch writer, rollback, validator, web
project editing. brain/developer/integration/tests/: active project,
brain router, create integration, developer connection,
dispatcher/developer, full integration, memory integration, rollback
integration. skills/assistant/test_greetings.py: greeting skill checks.

Important validation themes: TEST: test*JARVIS PRO*routing.py PURPOSE:
name/invocation routing behavior. TEST: test*offline*mode.py PURPOSE:
shared offline action/runtime behavior. TEST: test*face*vision.py
PURPOSE: face/vision detection and registration boundaries. TEST:
test*remote*event*sync.py PURPOSE: remote event/HUD synchronization.
TEST: test*android*payment*routing.py PURPOSE: payment route and Android
handoff behavior. TEST: developer test suites PURPOSE:
analyzer/planner/editor/repair/validation/workspace subsystem.

This is an inventory, not a test report. No tests were run for this
audit, so no pass/fail claim is made.

# 31. CURRENTLY IMPLEMENTED CAPABILITIES

VOICE: online SpeechRecognition/Edge TTS path; offline
Faster-Whisper/Piper path; voice queues/state/interruption; live Gemini
conversation actions.

AI: Ollama/Gemini/OpenAI provider classes; model registry/policy/router;
generation and streaming contracts; quota cooldown/fallback.

CONVERSATION: dispatch, context, follow-up, natural bridge,
confirmations, clarification state, independent dashboard AI chat.

MEMORY: explicit fact/preference memory, notes, reminders,
search/rank/forget/stats, profile and developer memory.

BROWSER: owned CDP runtime, browser executable resolution, Playwright
control, search/navigation, tab actions, YouTube integration/result
references.

VISION: camera capture/preview/record, YOLO object/person scenes, stable
scene loop, local face registration/recognition, screen
vision/screenshot analysis.

COMMUNICATION/MEDIA: WhatsApp UI automation/scheduling/calls, Gmail
sending, contact stores, Spotify controls,
news/weather/maps/translation, GitHub/ChatGPT search.

SYSTEM/FILES: volume, brightness, battery, process/task manager, power
actions, clipboard/screenshot, file/folder/zip/recycle/recent/search
actions.

ANDROID/PAYMENTS: ADB discovery/connect/device/app intents; payment
app/UPI chooser handoff; phone-call-related Android integration and
monitoring boundaries.

HUD/REMOTE: native webview HUD, Next.js cockpit/activity/system monitor,
SSE events, local/LAN dashboard, pairing/PIN/bearer authorization,
WebSocket/event paths.

DEVELOPER/AGENT: project analysis, language/framework/board/runtime
detection, generation, edit/patch/validation/backup/rollback/workspace
pipeline.

# 32. PARTIALLY IMPLEMENTED FEATURES

    - Online/cloud providers require external keys/services; source cannot prove
      availability in the current environment.
    - Face recognition, camera, offline STT/TTS, CDP, ADB, WhatsApp, Spotify,
      Gmail, and Windows automation are dependency/hardware conditional.
    - Some settings and frontend toggles exist but their complete behavioral
      connection is controlled by dashboard/server implementation and external
      runtime state.
    - Multiple remote-control implementations exist; only DashboardServer is
      directly constructed by main.py.
    - AI model registry/policy lists model families broader than any single
      configured/default provider can guarantee.
    - Generated workspace/developer editing features are substantial but not
      automatically active for every normal command.

# 33. EXPERIMENTAL FEATURES

    - Gemini Agent/audio session in voice/agent.py.
    - Offline shared-core mode with local Ollama and Piper.
    - YOLO temporal stabilization and local LBPH identity recognition.
    - Android wireless/ADB connection and phone-call monitor.
    - Frontend 3D/robot/avatar/hand-tracking assets and components.
    - AI chat history/model switching in the independent HUD chatbot.
    - Developer editor/generator/repair migration layers.

The source labels or structure indicate experimental/optional behavior,
but this section does not claim production readiness.

# 34. LEGACY / COMPATIBILITY FEATURES

    - JARVIS/JARVIS PRO names in protocols, filenames, prompts, and aliases.
    - brain/developer is a large older/compatibility architecture alongside the
      newer BrainRouter/natural conversation layers.
    - ai/intent.py is a compatibility wrapper over the newer intent engine.
    - services/remote_control.py is an alternate remote implementation.
    - hud/web_bridge.py retains a commented earlier SSE implementation.
    - core.services.start_remote_control remains available although main.py uses
      DashboardServer directly.
    - legacy core.context/action memory/confirmation paths coexist with the
      newer conversation clarification system.
    - dashboard/static HTML clients coexist with the Next.js HUD.

# 35. UNUSED / UNCONNECTED COMPONENTS

A source file is not automatically active. The following are not
confirmed as part of every startup: - modules absent from
skills.loader.SKILLS; - services.remote*control.RemoteControlServer in
the normal main path; - compatibility wrappers and alternate client
HTML; - tools scripts and manual test/demo entry points; - generated
workspace projects and their local memories/backups; - installed
node*modules and compiled caches; - any provider/skill that failed
optional import or lacks configuration.

Exact dead-code status is NOT DETERMINED FROM SOURCE for individual
modules unless import/registration evidence exists. See the Python
manifest and loader.

# 36. NOT IMPLEMENTED / UNKNOWN AREAS

    - JARVIS PRO is not confirmed as the effective persisted display name on this
      checkout; current persisted name is JARVIS.
    - No automatic payment authorization or credential entry is implemented.
    - No Firebase/Apps Script integration was confirmed.
    - No source-only audit can confirm external service quotas, valid credentials,
      device presence, browser installation, camera/microphone access, or model
      downloads.
    - Exact runtime activation of every module, frontend control, and legacy
      path is NOT DETERMINED FROM SOURCE.
    - No claim is made that all listed tests pass; they were not executed here.

# 37. END-TO-END DATA FLOWS

A. Voice command: microphone -\> SpeechRecognition or Faster-Whisper -\>
text -\> dispatcher/OfflineActionBridge -\> fast route or planner -\>
registry action/service -\> HUD response + voice TTS.

B. Text command: HUD/dashboard input -\> DashboardServer command handler
-\> core.dispatcher.dispatch -\> same fast route/planner/action path.

C. AI generation: request -\> AIService/AIRouter -\>
ModelManager/Policy/Registry -\> provider availability -\> selected
model generation/stream -\> quota cooldown/fallback -\> AIResponse -\>
caller/HUD/voice.

D. Clarification: request lacking field -\> clarification state/question
-\> next input -\> invocation/priority checks -\> resolve/merge/cancel
-\> planner or action execution.

E. Browser: browser action -\> BrowserController -\>
BrowserRuntime/executable/profile -\> CDP -\> Playwright page/tab -\>
result context/reference -\> response.

F. Vision: camera -\> VisionEngine/CameraManager -\> YOLO detection -\>
scene analyzer/stability loop -\> describe/count/locate or face crop -\>
optional LBPH recognition -\> spoken/HUD result.

G. Remote: phone/web client -\> pairing PIN -\> bearer token -\>
FastAPI/WebSocket command/event endpoint -\> dispatcher -\> result/event
-\> client.

H. HUD: core/voice/service -\> HUDIntegration/HUDManager -\> HUDState +
HUDEvent -\> hud_bus -\> SSE bridge -\> HUDBridge EventSource -\> React
state/cockpit/activity UI.

I. Skill: startup loader -\> import skill -\> register action -\>
router/planner emits action name -\> core.registry.execute -\>
handler/service -\> response/HUD/voice.

J. Payment: \"make payment \...\" -\> payment*router -\> make*payment
-\> AndroidManager ADB app launch or upi://pay chooser -\> user
completes scan/details/auth in official app.

# 38. ROUTERS / REGISTRIES / LOADERS / DISPATCHERS

    core.fast_router.fast_route:
        ordered deterministic router fan-out.
    core.routers.*:
        domain-specific command recognizers/planners.
    core.dispatcher.dispatch:
        central input priority and execution coordinator.
    core.registry:
        action handler/category registry.
    skills.loader:
        import and diagnostics for configured skill packages.
    ai.core.ModelRegistry:
        model metadata registry.
    ai.core.ModelManager:
        capability/provider-aware selection.
    ai.core.AIRouter:
        provider availability, streaming, fallback, cooldown.
    brain.BrainRouter:
        developer request boundary and active-project/editor routing.
    dashboard.DashboardServer:
        HTTP/WebSocket protocol/API dispatcher adapter.
    hud.bus:
        event bus between Python runtime and presentation.
    voice.offline.OfflineActionBridge:
        offline deterministic/local/network-required classification.
    browser runtime/controller:
        executable/CDP ownership and browser action boundary.

# 39. ACTION INVENTORY

The following are the important registered action names discovered from
module-level register(\...) calls. Handler source is shown by
package/module.

    AI:
        clarify                         skills/ai/clarify.py
    Android:
        android_check_adb, android_check_device, android_device_info,
        android_open_app, android_launch_app
        skills/android_control/android_control.py
    Assistant:
        greet, how_are_you, assistant_name, welcome, goodbye
        skills/assistant/greetings.py
    Automation:
        home_automation                  skills/automation/home_automation.py
    Browser:
        browser_open_result, open, google_search
        skills/browser/browser_ai.py
        youtube_search, youtube_play_first, youtube_pause, youtube_resume,
        youtube_next, youtube_previous, youtube_play_result
        skills/browser/youtube.py
        new_tab, close_tab, forward, back, scroll_down, scroll_up, refresh, close
        skills/browser_control/browser_controls.py
    Camera/Vision:
        camera_status, capture, camera_preview, camera_close,
        start_recording, stop_recording
        skills/camera/camera.py
        vision_start, vision_stop, vision_describe, vision_count, vision_check,
        vision_position, vision_locate, vision_target, register_face,
        cancel_face_registration, delete_face
        skills/camera/vision_skill.py
    Communication:
        chatgpt_search                     skills/communication/chatgpt.py
        github_search                      skills/communication/github.py
        remember_contact, forget_contact, show_contacts
        skills/communication/contact.py
        send_email, remember_email_contact, forget_email_contact,
        show_email_contacts
        skills/communication/email.py
        whatsapp_open, whatsapp_close, whatsapp_send_message,
        whatsapp_wait_message, whatsapp_send_latest_photo,
        whatsapp_send_latest_screenshot, whatsapp_send_file,
        whatsapp_send_selected_file, whatsapp_wait_contact,
        schedule_whatsapp_message, list_scheduled_whatsapp,
        cancel_scheduled_whatsapp, reschedule_scheduled_whatsapp,
        whatsapp_call, whatsapp_video_call
        skills/communication/whatsapp.py
    Files:
        file_info                           skills/files/file_info.py
        open_file, open_folder, create_file, create_folder, copy, move,
        rename, delete                         skills/files/files.py
        recent_files                         skills/files/recent.py
        recycle                             skills/files/recycle.py
        zip, extract                        skills/files/zip_manager.py
    Media:
        create_image                        skills/media/image_generation.py
        play                                skills/media/media.py
        spotify_open, spotify_close, spotify_play, spotify_pause,
        spotify_next, spotify_previous, spotify_volume_up,
        spotify_volume_down, spotify_play_song
        skills/media/spotify.py
    Memory/Navigation:
        create_note, list_notes, clear_notes
        skills/memory/notes.py
        create_reminder, list_reminders, cancel_reminder
        skills/memory/reminders.py
        maps_open, maps_directions       skills/navigation/maps.py
        translate_open, translate_text  skills/navigation/translate.py
    Network/News:
        bluetooth_status, bluetooth_devices
        skills/network/bluetooth.py
        weather                             skills/network/weather.py
        wifi_on, wifi_off, wifi_status, wifi_list
        skills/network/wifi.py
        get_news                            skills/news/news.py
    Payments/Phone:
        make_payment                        skills/payments/payments.py
        phone_call_number, phone_call_contact, phone_call_confirmed,
        answer_call, reject_call, end_call, call_status, missed_calls
        skills/phone_call/phone_call.py
    Screen/System/Utilities/Web:
        clipboard                           skills/screen/clipboard.py
        screen_vision_analyze               skills/screen/screen_vision_skill.py
        screenshot                          skills/screen/screenshot.py
        screenshot_ai                       skills/screen/screenshot_ai.py
        battery                             skills/system/battery.py
        brightness                          skills/system/brightness.py
        running_apps, close_process         skills/system/process.py
        terminate_jarvis, shutdown, restart, sleep, lock
        skills/system/system.py
        taskmanager                         skills/system/taskmanager.py
        volume                              skills/system/volume.py
        search_file                         skills/utilities/search.py
        time                                skills/utilities/time_skill.py
        open_personal_link, show_personal_links
        skills/web/personal_links.py
    Runtime-registered after core init:
        start_agent, stop_agent,
        agent_status            main.py

# 40. SECURITY ARCHITECTURE

Secrets: .env, credentials.json, token.json, OAuth files and API keys
are local sensitive material. They are ignored or treated as local and
are not copied.

Remote authentication: pairing PIN is generated with secrets, expires
after 600 seconds, invalidates older sessions, and is exchanged for a
bearer token. Dashboard endpoints distinguish public pairing/static
operations from authorized operations; exact endpoint policy is in
dashboard/server.py.

Payment security: payment skill does not receive or enter payment
credentials and deliberately delegates authorization to the official
Android app.

Browser security: browser config enforces local CDP host behavior and
runtime ownership/ session markers; browser profiles can contain cookies
and user data.

OS/security-sensitive actions: file deletion, process termination, power
actions, clipboard, ADB, WhatsApp UI automation, email sending, and
payment-app launch are capability-bearing handlers. Source-level
presence is not a security audit.

# 41. NETWORK PORTS / SERVICES

PORT: 3000 PURPOSE: Next.js HUD dev server SERVICE: hud/web via npm run
dev BIND: Next.js default/local URL used by main.py CLIENT: native
pywebview and browser-side HUD CONFIG: WEB*HUD*URL in main.py STATUS:
active startup target

PORT: 8765 PURPOSE: Dashboard/remote control HTTP/WebSocket SERVICE:
dashboard.server.DashboardServer; alternate services.remote_control
BIND: local/LAN IP selected by server CLIENT: HUD, phone/browser remote,
command/audio clients CONFIG: PORT constant / constructor STATUS: active
normal main path; optional if dependencies fail

PORT: 8766 PURPOSE: passive Python-to-web HUD SSE bridge SERVICE:
hud.web*bridge.hud*web BIND: 127.0.0.1 by source CLIENT: Next.js
HUDBridge EventSource CONFIG: bridge constructor/default STATUS: active
HUD event path when bridge starts

PORT: 9223 PURPOSE: browser Chrome/Edge/Chromium CDP SERVICE:
skills.browser.browser*runtime BIND: 127.0.0.1 CLIENT: Playwright
BrowserController CONFIG: JARVIS*BROWSER*CDP*\* values STATUS:
selected/owned on browser use; not always running

PORT: 8888 PURPOSE: Spotify OAuth callback SERVICE: config/Spotify
integration BIND: localhost callback URI CLIENT: Spotipy OAuth STATUS:
configured integration endpoint; actual use conditional

# 42. GENERATED / CACHE / MACHINE-SPECIFIC DATA

    .env, credentials.json, token.json:
        secrets/OAuth artifacts; values excluded.
    .spotify_cache:
        Spotify OAuth/cache state.
    ai/memory.db and related local data:
        persistent assistant memory if created.
    data/faces/:
        local face samples; .gitkeep is source-control placeholder.
    data/settings/:
        persisted UI/identity customization.
    data/logs/ and dashboard upload directories:
        runtime logs/uploads created by startup/dashboard.
    voice/cache/:
        Edge/Piper generated audio cache.
    yolo11n.pt:
        local ML model asset; ignored by repository policy.
    workspace/:
        generated sample/user projects, .jarvis_memory, .jarvis_backups,
        source examples and per-project runtime state.
    hud/web/node_modules/:
        installed third-party packages; generated/dependency data.
    __pycache__/.pytest_cache:
        compiled and test caches.
    hud/web/.next/:
        generated Next.js output if present.
    browser profiles/CDP state:
        machine-specific browser data; not source.

Observed scale at audit: hud/web/node_modules: approximately 181,397
files. workspace: approximately 1,278 files. data: approximately 1,190
files. These areas are identified but not expanded into the manual
source tree.

# 43. GIT / REPOSITORY INFORMATION

Repository root: D:\\MY FILES\\MY-VSCODE\\MY-ASSISTANT\\JARVIS-PRO

Branch: main

Remote: origin is configured; credential details are intentionally
omitted.

Latest observed commit: 046536e feat(phone_call): Implement dedicated
phone call skill with monitoring and routing

Working tree at audit start: clean; no pre-existing modified/untracked
changes were reported. The documentation file itself is the only
intended new change after creation.

Ignore policy: source caches, virtual environments, generated
workspaces, local tools, secrets/OAuth files, AI memory data, models,
Node dependencies/build output, and local runtime state are ignored. The
exact policy is in .gitignore.

# 44. ARCHITECTURAL RELATIONSHIPS

    FAST ROUTER -> domain routers -> action plan
    ACTION PLAN -> core.registry -> skill/service handler
    SKILL LOADER -> module imports -> register() side effects
    DISPATCHER -> clarification/email/follow-up/BrainRouter/planner ordering
    AI SERVICE -> AIRouter -> ModelManager -> provider implementation
    MODEL REGISTRY -> capability metadata -> policy-aware selection
    BRAIN ROUTER -> Developer -> analyzer/planner/editor/generator/validator
    BROWSER CONTROLLER -> BrowserRuntime -> owned CDP -> Playwright
    VISION SKILL -> CameraManager/VisionEngine -> YOLO -> scene/face analysis
    VOICE LISTENER -> dispatcher; voice manager -> Edge/Piper player
    DASHBOARD -> dispatcher -> same core action system
    HUD MANAGER -> event bus -> SSE bridge -> React HUDBridge -> UI
    DASHBOARD -> WebSocket/events -> remote/mobile client
    PAYMENT -> AndroidManager -> ADB intent -> official payment app
    PROFILE/MEMORY -> ContextBuilder/PromptBuilder -> AI/offline AI
    PHONE MONITOR -> service startup -> phone-call actions/HUD events

# 45. CURRENT PROJECT STATUS

    STATUS: ACTIVE SOURCE PRESENT
        Core startup, routers, registry, skills, AI contracts/providers, voice,
        HUD, dashboard, browser, vision, Android, payment handoff, and tests
        exist in the current checkout.

    STATUS: CONFIGURATION/HARDWARE CONDITIONAL
        Cloud AI, audio, camera, browser, ADB, desktop apps, OAuth APIs and
        model assets require external conditions not proven by static inspection.

    STATUS: MIXED-GENERATION ARCHITECTURE
        Newer dispatcher/brain/AI/HUD paths coexist with legacy/compatibility
        wrappers, alternate remote control, static clients, and large developer
        subsystems.

    STATUS: NOT A TEST REPORT
        This audit did not execute tests or start services.

    STATUS: IDENTITY DISCREPANCY
        Requested JARVIS PRO identity is present in parts of code, but persisted
        effective runtime name on this checkout is JARVIS.

# 46. FINAL COMPLETE INVENTORY

TOTAL SOURCE DIRECTORIES: 12 top-level source/package directories
counted in this documentation: ai, brain, chatbot, config, core,
dashboard, hud, services, skills, tests, tools, voice, plus
generated/data/runtime directories listed separately. Exact nested
directory count is represented by the manifest/tree.

TOTAL SOURCE FILES: approximately 604 Python source files outside root
generated workspace/dependency areas, plus frontend/config/static source
files listed in the manifests.

TOTAL TEST FILES: approximately 58 Python test files across tests/,
brain/tests/, brain/developer/tests/, brain/developer/editor/tests/,
brain/developer/integration/tests/, and skills/assistant/.

TOTAL CONFIG FILES: exact set includes .env.example, .gitignore,
requirements.txt, config/\*.py, hud/web/package.json, package-lock.json,
tsconfig.json, next.config.ts, and runtime JSON/settings files.

TOTAL FRONTEND FILES: 15 TypeScript/TSX source files under hud/web plus
CSS/JSON/config/static frontend assets; dependency files are excluded
from this count.

TOTAL SKILL MODULES: 87 Python files under skills/ (including package
initializers); 46 explicit modules are configured in
skills.loader.SKILLS.

TOTAL AI PROVIDERS: 3 provider implementations: Ollama, Gemini, OpenAI.

TOTAL MAJOR SERVICES: dashboard/remote, HUD bridge/runtime, voice,
browser/CDP, vision/camera, Android/ADB, phone-call monitor, email,
WhatsApp, Spotify, location, personal links, files and Windows
automation; exact count is architectural.

TOTAL MAJOR ROUTERS: 1 fast-router coordinator plus 20 domain router
modules listed in core/routers and additional AI/brain/browser routing
boundaries.

TOTAL MAJOR REGISTRIES: core action registry, skill loader
registry/diagnostics, AI model registry, developer memory/project
registries, face registry, and browser/result context registries.

TOTAL EXTERNAL INTEGRATIONS: approximately 18 integration families
listed in Section 28; availability is conditional and no credentials are
included.

TOTAL ENTRY POINTS: main.py and run_jarvis.py are confirmed application
launchers; additional module-level/manual test/demo entry points exist
but are not all startup paths.

## FINAL AUDIT CONFIRMATIONS

    - Documentation-only scope honored.
    - Existing application functionality was not changed.
    - README.md and all existing source/config/test files were not modified.
    - No secret values were included.
    - No services were started and no dependencies were installed.
    - No Git commit or push was performed.
    - The final Git status was checked after creating this file.

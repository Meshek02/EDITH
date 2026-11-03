# E.D.I.T.H.

Even Dead, I'm The Hero. EDITH is a modular hybrid personal AI assistant project inspired by JARVIS, FRIDAY and EDITH. Its long-term vision includes configurable text/voice assistance, academic scheduling, Windows diagnostics, Plex and website workflows, editable memory and iPhone access.

## Current status
Phase 1 Tasks A, B and C are complete and verified. Task C passed 86 tests, Ruff lint/format checks, dependency consistency, a fresh constrained installation and live loopback startup/shutdown verification. A local backend foundation now works; EDITH is not yet an AI assistant. No AI, model router, voice, memory persistence, Windows control, remote access, external integrations or frontend is implemented.

## Install and run locally
Use Python 3.12 and PowerShell from the repository root. On a fresh checkout:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c requirements-dev.lock.txt -e '.[backend,dev]'
.\.venv\Scripts\python.exe -m backend.main
```

The verified .venv already exists on the development machine. These commands use it directly without activation or execution-policy changes. The constraints snapshot records tested dependency versions; pyproject.toml retains compatible ranges. See [development guidance](docs/DEVELOPMENT.md) for limits and updates.

No .env or credentials are required. Optional local .env settings use [.env.example](.env.example); environment variables override the file. The file is resolved relative to the working directory. Run from the repository root. The supported launcher honors EDITH_HOST and EDITH_PORT, defaulting to 127.0.0.1:8000. Stop with Ctrl+C and wait for shutdown completion.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected JSON:

```json
{"assistant":"EDITH","version":"0.1.0","status":"healthy","ai_connected":false,"windows_control_enabled":false}
```

The name is configurable. Version comes from installed edith-assistant package metadata. /health is the only application endpoint; FastAPI also exposes /docs, /redoc, /openapi.json and its documentation OAuth redirect. Documentation UI assets may require internet access in the browser; the backend health check makes no external calls.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/verify_backend.py
```

The Windows live verifier checks health, the actual listener address and clean shutdown in an isolated child process. It uses 8000 if available, otherwise a temporary local port, and never terminates unrelated processes. See scripts/README.md for its test-only stdin control hook.

## Security and limitations
Settings reject enabled AI, Windows control or remote access and any host other than 127.0.0.1. Port, environment and log level are validated. Every executable action is denied by the policy foundation; there is no executor. No authentication is implemented, so localhost is not a user identity boundary. Do not expose this service through a proxy or tunnel.

Use the documented Python launcher: directly invoking Uvicorn with arbitrary --host/--port overrides can bypass application-selected binding. Disabling ASGI lifespan also bypasses startup validation and is unsupported. Configuration checks cannot control externally supplied server options. There is no wildcard CORS or execution route. JSON console logs redact representative known secrets; redaction is not universal. See [security details](docs/SECURITY.md).

## Structure and planned stack
backend/main.py creates the app and launcher; backend/core contains configuration, logging and the policy; backend/api/health.py provides status. backend/agents, skills, memory and integrations remain empty packages. windows-agent and frontend remain documentation-only. tests contains automated tests; scripts contains the live verifier; docs contains architecture, security, development and roadmap guidance. AGENTS.md contains persistent project instructions.

Planned later: Ollama plus approved OpenAI API usage, privacy-aware routing, SQLite memory, Next.js/TypeScript PWA and an isolated Windows Agent. Keep expenses near the planning target of $10-$25/month excluding electricity and optional services; this is not guaranteed.

## Roadmap and workflow
1. Foundation & Architecture.
2. AI Brain.
3. Voice & Personality.
4. Windows Automation.
5. School & Calendar.
6. Plex & Website Management.
7. iPhone & Remote Access.
8. 24/7 Intelligence & Reliability.

Phase 2 Task A local runtime evaluation is complete; qwen3:4b-instruct is recommended for the next authorized integration task. Backend integration and Phases 3-8 are not started. See [local AI findings](docs/LOCAL_AI.md). See [ROADMAP.md](docs/ROADMAP.md). Planning occurs through ChatGPT on MacBook; the user manually transfers prompts and reports to Codex on Windows. Read AGENTS.md before changes. Phase 1 final technical review passed. The initial local checkpoint is handled under the final-review instruction; inspect Git history for its state. The public repository is Meshek02/EDITH with origin configured. Phase 2 Task B awaits separate authorization.

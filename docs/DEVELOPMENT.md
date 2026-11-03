# Development workflow

## Verified baseline from Task A
Windows 11 Pro 26H2 build 26300.9711; Ryzen 5 9600X; Radeon RX 7800 XT with about 16 GiB VRAM; 16 GB RAM. Actual storage is X16 Plus 1TB, not the originally expected Crucial 2TB; about 357 GiB was free on C: at audit time.

Verified tools: Python 3.12.10 with pip 25.0.1; Python 3.13.0 also present; Git 2.56.0.windows.2; VS Code 1.99.3; Node.js 24.22.1 LTS and npm 11.19.1; PowerShell 7.6.9; Windows PowerShell 5.1.26100.9711; winget 1.29.380. Versions are audit observations, not promises about future installations. Task A verified an isolated venv, SQLite and SSL. User PATH was configured for Python 3.12 and standalone Node; reopen terminals if they retain older PATH values. No global execution-policy changes are needed.

## Python and dependencies
Use Python 3.12 explicitly; the package requires >=3.12,<3.13. From a fresh checkout root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c requirements-dev.lock.txt -e '.[backend,dev]'
.\.venv\Scripts\python.exe -m pip check
```

Task C created the development .venv and installed backend/dev extras without global package changes. Direct interpreter calls avoid activation and execution-policy changes. setuptools discovers only backend and backend.*. Package name/version remain edith-assistant/0.1.0; application version is read from installed package metadata.

pyproject.toml keeps compatible ranges; requirements-dev.lock.txt records the tested resolved dependency graph as pip constraints, without local paths or credentials. It is a Windows/Python 3.12 snapshot, not a hashed supply-chain lock or cross-platform guarantee; build-isolation tooling is not fully locked. The constrained command is verified in a fresh temporary environment. To intentionally refresh versions during an authorized task, install compatible updates, rerun all checks, regenerate with `python -m pip freeze --exclude-editable`, and review the snapshot. No AI/automation packages are installed.

## Run and stop

```powershell
.\.venv\Scripts\python.exe -m backend.main
```

Pydantic Settings reads defaults, optional .env in the working directory and overriding process environment variables. No .env or API key is required. Use the repository root as working directory. The template documents accepted keys; unknown dotenv keys are rejected to catch mistakes. Credentials must not be committed. Settings are read at launch and again at lifespan startup; change them by stopping/restarting, not by editing live state.

Default bind is 127.0.0.1:8000. EDITH_PORT may select another valid port. Only 127.0.0.1 is supported; AI/control/remote flags must remain false. Invalid configuration exits before serving without echoing raw inputs. The app object is backend.main:app, but the supported startup method is the Python module so host/port, logging and disabled proxy/access-log settings are honored. Direct Uvicorn CLI overrides can bypass selected bind values; lifespan=off is unsupported and bypasses startup validation.

Check with `Invoke-RestMethod http://127.0.0.1:8000/health`. Local framework docs are /docs, /redoc, /openapi.json and /docs/oauth2-redirect. Stop with Ctrl+C, wait for Application stopped and server shutdown completion. No service, automatic startup or background monitors exist. Never kill an unrelated process occupying a port; select another EDITH_PORT instead.

## Tests and formatting

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/verify_backend.py
```

Tests clear relevant environment variables, use temporary working directories and synthetic credentials, and cover health schema, invalid settings, feature rejection, policy denials, redaction, handler idempotency, errors and lifecycle. Socket connection attempts are blocked during the health check; Windows event-loop setup is allowed before that guard. No test needs real accounts or model services.

The Windows live verifier uses the normal module launcher in its own child, instruments Uvicorn Server.run only to receive a private stdin shutdown request, inspects the actual PID's listener with netstat, checks health, requests graceful shutdown and verifies process exit/closed port. No shutdown API is added. Default test port is 8000; if occupied, select an available local port. The verifier uses a temporary CWD and clean configuration. It never terminates unrelated processes; its failure cleanup can terminate only its own child.

The installed Starlette TestClient currently emits an upstream HTTPX deprecation warning. HTTPX remains functional and the requested dependency is retained; no warning filter hides it. Revisit the supported testing transport during an authorized dependency update.

## Local and Git workflow
Planning remains through ChatGPT on MacBook with manual prompt/report transfer to Windows Codex. Read AGENTS.md and inspect files before every scoped task. Preserve working features and run relevant checks. The final-review task authorizes one initial local commit after confirmed repository-local Git identity and staged-content review. Inspect Git history/status for checkpoint state. No remote is configured. Never invent identity values or change global identity. Future authorized branches normally use codex/ prefixes.

## Troubleshooting
Use `py -0p` and `py -3.12 --version` for interpreter selection. Module metadata errors mean the editable package/extras need installation into the selected environment. Run the documented constrained installation rather than bypassing validation. Close/reopen terminals for PATH changes. Use npm.cmd if policy blocks npm.ps1; do not weaken execution policy. Sandbox access failures are not evidence of missing software.

If startup rejects configuration, review the named field in environment/.env without printing credentials. A port conflict requires another port, not killing its owner. No database is created even though a reserved SQLite URL exists. AMD model support still requires real driver/runtime and inference validation in Phase 2. No WSL features were enabled.

## Task status
Task A completed its environment audit. Task B verified all 21 original files, package boundaries and repository hygiene. Task C completed and verified: 86 tests passed, zero failed/skipped, with one upstream HTTPX/TestClient deprecation warning; Ruff lint and formatting passed; pip check, fresh constrained installation and live 127.0.0.1:8000 health/shutdown checks passed. The server exited with code 0 and its port closed. At Task C completion, Git was main with zero commits/remotes/staged files and 34 untracked source/documentation files. The final review reverified all required checks and the local secret/ignore/dependency audits; the initial local checkpoint is managed under that task authorization. Inspect Git history/status for checkpoint state. Phase 2 has not started.

# Eight-phase roadmap

Current status: Phase 1 Tasks A, B and C completed and verified. Phase 1 final technical review passed; the initial local checkpoint is handled under the final-review authorization (inspect Git history for its state). Phases 2-8 not started. The minimal backend/configuration/logging/deny-all policy and automated tests are implemented; later operational features remain planned.

## Phase 1 - Foundation & Architecture
- Objective: establish a secure, testable Windows development foundation.
- Features: environment audit (A), local structure/metadata/docs/Git (B), backend configuration, logging, security boundaries and automated tests (C).
- Dependencies: verified Python 3.12, Git and authorized development tools.
- Deliverable: documented project followed by a working tested backend foundation.
- Acceptance: Task A prerequisites pass; Task B structure, TOML, safe template, ignores and empty Git history pass; Task C behavior and tests pass under its own instructions.
- Status: A, B and C completed and verified. Task C passed 86 tests (one upstream TestClient/HTTPX deprecation warning), Ruff lint/format checks, pip check, fresh constrained installation, live loopback health and graceful shutdown. Final technical review passed: the same 86 tests and required quality/dependency/live checks passed again; the candidate-file security and ignore audits passed. The initial checkpoint follows confirmed local identity and staged-content review under the final-review instruction.

## Phase 2 - AI Brain
- Objective: text-based hybrid intelligence.
- Features: Ollama, approved cloud API, router, conversation handling, typed tools and initial memory.
- Dependencies: tested Phase 1 foundation, authorized provider setup, verified AMD driver/runtime compatibility and model benchmarks.
- Deliverable: text assistant using local/cloud models under policy and budget controls.
- Acceptance: routing, offline/provider errors, memory CRUD, privacy boundaries and tool authorization tested; real provider behavior verified where authorized.
- Status: not started.

## Phase 3 - Voice & Personality
- Objective: configurable voice interactions.
- Features: speech recognition/synthesis, identity and personality settings, optional wake word, background audio sessions and microphone privacy controls.
- Dependencies: Phase 2 conversation flow; chosen audio stack and hardware validation.
- Deliverable: voice assistant with explicit microphone controls.
- Acceptance: speech round trip, cancellation, microphone state and configuration changes verified; no unsupported background-listening claims.
- Status: not started.

## Phase 4 - Windows Automation
- Objective: safe authorized Windows actions.
- Features: separate Windows Agent, metrics, application control, diagnostics, typed permissions, audit records and recovery.
- Dependencies: core tool/policy boundary; approved Windows interfaces and action scopes.
- Deliverable: assistant executing permitted Windows tasks.
- Acceptance: allow/deny paths, high-risk approvals, timeouts, emergency stop and recovery tested without unrestricted administrator control.
- Status: not started.

## Phase 5 - School & Calendar
- Objective: academic scheduling assistance.
- Features: authorized email/calendar/D2L retrieval, assignment tracking, reminders, conflict detection and daily briefings.
- Dependencies: institutionally permitted APIs/authentication, privacy controls, memory and scheduling.
- Deliverable: verified academic assistant.
- Acceptance: authorized retrieval, correct due dates/timezones, deduplication and reminders tested; no MFA or school-policy bypass.
- Status: not started.

## Phase 6 - Plex & Website Management
- Objective: server monitoring and development assistance.
- Features: Plex health/playback/storage, approved recovery, GitHub/project workflows, tests and approval-based website deployment.
- Dependencies: scoped service access, Windows tooling where relevant, policy/audit and rollback support.
- Deliverable: monitoring and code-change workflows with reviewable results.
- Acceptance: health checks and failure notifications verified; changes tested; production deployment requires authorization and recoverability.
- Status: not started.

## Phase 7 - iPhone & Remote Access
- Objective: secure mobile access to the same assistant.
- Features: responsive web interface/PWA, text/voice, notifications and optional Siri Shortcuts.
- Dependencies: backend auth/authorization, private authenticated networking and validated iOS capabilities.
- Deliverable: iPhone access to shared memory and permitted tools.
- Acceptance: authentication, scoped commands, session expiry and supported notification behavior verified on device; no public unrestricted execution.
- Status: not started.

## Phase 8 - 24/7 Intelligence & Reliability
- Objective: resilient supported services independent of desktop uptime.
- Features: optional always-on coordinator, recurring monitoring, backups, recovery and observability.
- Dependencies: portable core/agent separation, hosting evaluation, budget and security review.
- Deliverable: maintainable always-on services with clear offline limitations.
- Acceptance: restore and failure drills, offline-agent behavior, auditability, security and cost limits verified.
- Status: not started.

Dependencies may justify ordering adjustments only within user-authorized scope. No validation or security gate may be silently skipped.

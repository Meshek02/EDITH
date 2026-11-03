# Security requirements

## Enforced Phase 1 foundation
Startup validates immutable settings and rejects enabled AI, Windows control or remote access. Only EDITH_HOST=127.0.0.1 is supported; 0.0.0.0, other addresses, IPv6 and localhost names are rejected. Ports must be 1-65535; environments are development/test/production; log levels are DEBUG/INFO/WARNING/ERROR/CRITICAL. Production is a configuration label, not evidence of production readiness. Every executable action and permission category is denied, including unknown values. There is no executor or action endpoint.

The documented Python launcher passes validated host and port to Uvicorn, disables proxy-header trust and access logs, and uses JSON server logging. Direct external Uvicorn --host/--port options can bypass application-selected binding; ASGI lifespan must remain enabled for startup validation. Application settings cannot control externally supplied server options. Do not expose through a tunnel, proxy or firewall exception. No authentication exists: other local users/processes may reach the health/docs endpoints. Localhost is not an identity or browser-origin boundary. No CORS middleware is installed; CORS is not authentication.

Health exposes only an allowlisted status model. Generic application errors return a fixed 500 response without tracebacks. FastAPI documentation/schema routes remain available on localhost. API key settings use SecretStr and are excluded from settings representation and serialization. Invalid configuration reports field names only. No credentials, model calls or database are required at startup.

## Logging implementation and limits
Application and supported-launcher server logs are console JSON with timestamp, level, logger and message. Repeated setup does not add duplicate application handlers. Known API-key values, representative API-key patterns, password/token assignments, authorization/cookie headers and sensitive nested dictionary fields are redacted. Arbitrary record extras and exception text/tracebacks are omitted; exception type may be recorded. Access logs are disabled to avoid request query/header leakage. No persistent log files are created.

Redaction is defense in depth, not comprehensive detection: unlabeled unknown secrets, unusual encodings and private prose may escape pattern matching. Do not log configurations, email contents, authorization data or private user content. External launchers/third-party loggers can have different logging behavior. Future authentication, policy enforcement at actual tool boundaries, auditing, cancellation, emergency stop, backups and prompt-injection controls remain requirements below, not implemented capabilities.

## Threat model
Protect user data, academic records, credentials, files, devices, source code and production services from unauthorized users, malicious retrieved content, compromised integrations, mistaken model actions and accidental credential disclosure. Local users/processes and remote sessions are separate trust boundaries. A model must not grant itself permissions.

## Permission levels
1. Read-only: retrieve only approved metrics, calendar data, Plex state or logs. Read access still needs scope and privacy controls.
2. Routine actions: launch approved apps, create non-sensitive files or authorized calendar events only under explicit user-configured policies.
3. High-risk: important deletion, installations, administrator commands, security/configuration changes, production changes and external messages require explicit approval tied to the concrete action and scope. Expired or changed actions require renewed authorization.

Use least privilege and deny by default. No unrestricted administrator execution. Validate typed arguments, target paths and scope independently of model output. Bound commands by timeout, output size and execution limits; prevent duplicate retries of side effects.

## Credentials and configuration
Use an appropriate Windows credential store or approved secret manager in future implementation. Local development environment files must be ignored. Never store secrets in source, logs, model prompts or conversational memory. Use scoped/revocable tokens and redact sensitive output. .env.example contains no credentials. Pydantic Settings loads an optional .env; corresponding Phase 1 host and disabled-feature restrictions are tested. Provider and database settings remain unused reserved values; no client or database is created.

## API and remote access
The supported launcher binds to validated 127.0.0.1. This is not sufficient authentication: local requests also require the intended access controls. Keep remote access disabled until separately authorized, authenticated and tested. Prefer private authenticated networking, scoped sessions and revocation; no public arbitrary command execution. Do not bypass MFA or institutional restrictions.

## Prompt injection and privacy
Treat emails, webpages, documents, repository content and tool results as untrusted data. Preserve provenance, separate content from instructions, minimize retrieved data and prohibit content from changing permissions or authorizing execution. Verify requested tools against independent policy and user intent. Send private or academic data to cloud models only under approved handling rules. Do not rely on prompt wording alone as a security boundary.

## Audit, cancellation and recovery
Future structured audit logs must capture action, authorization, bounded target information, timestamps, correlation IDs and outcome without secrets or unnecessary private content. Define retention and access restrictions. Emergency stop must prevent new dispatch and cancel supported in-flight operations; document operations that cannot be reversed. Keep tested backups, rollback plans and restore procedures before risky changes. Record failures and partial side effects; do not blindly retry destructive operations. Expose memory inspection, editing and deletion. These requirements need implementation and acceptance tests in later tasks.

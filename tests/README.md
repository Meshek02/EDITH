# Automated tests

Run `.venv/Scripts/python.exe -m pytest -q` from the repository root. Tests cover health, settings, deny-all execution policy, JSON logging, generic errors and lifecycle. They isolate configuration and use synthetic secrets; no real credentials or external services are needed. The separate live Windows verification command is documented in scripts/README.md. The installed TestClient emits a documented upstream HTTPX deprecation warning.

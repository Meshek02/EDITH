# Verification utilities

Run `.venv/Scripts/python.exe scripts/verify_backend.py` from the repository root on Windows. It starts the normal backend module launcher in an isolated child with clean test settings and a temporary working directory. Port 8000 is preferred; an occupied port causes selection of another local port without stopping its owner.

The verifier adds a test-only stdin shutdown hook around Uvicorn Server.run. It leaves application host/port/configuration validation intact, introduces no HTTP route, and requests graceful shutdown using Uvicorn's should_exit flag. It uses the child's actual Python PID to inspect netstat listeners, validates health, checks lifecycle logs, confirms exit and checks the port is closed. No backend is left running on success. Failure cleanup can terminate only the child it created. It does not modify application settings, install software or expose a remote shutdown mechanism.

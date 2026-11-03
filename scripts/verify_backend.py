"""Run the real launcher in a controlled child and verify loopback/shutdown.

The test-only child instruments Uvicorn's run method to accept a stdin stop signal.
It does not alter application configuration or expose a shutdown HTTP endpoint.
"""

import json
import os
import runpy
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]


def child() -> None:
    """Add a private process-control hook, then execute the normal module launcher."""
    import uvicorn

    print(json.dumps({"server_pid": os.getpid()}), flush=True)
    original_run = uvicorn.Server.run

    def controlled_run(server: uvicorn.Server, *args: object, **kwargs: object) -> None:
        def stop_on_stdin() -> None:
            sys.stdin.readline()
            server.should_exit = True

        threading.Thread(target=stop_on_stdin, daemon=True).start()
        original_run(server, *args, **kwargs)

    uvicorn.Server.run = controlled_run
    runpy.run_module("backend.main", run_name="__main__")


def verify() -> None:
    """Fail if startup, actual binding, health or graceful shutdown differs."""
    with socket.socket() as probe:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            probe.bind(("127.0.0.1", 8000))
            port = 8000
        except OSError:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("EDITH_")
        and key.upper() not in {"OPENAI_API_KEY", "OLLAMA_BASE_URL"}
    }
    environment.update(
        {
            "EDITH_PORT": str(port),
            "EDITH_HOST": "127.0.0.1",
            "EDITH_AI_ENABLED": "false",
            "EDITH_WINDOWS_CONTROL_ENABLED": "false",
            "EDITH_REMOTE_ACCESS_ENABLED": "false",
        }
    )
    # Existing local .env files are intentionally not used by this verifier.
    # Use a temporary CWD; editable package installation supplies imports.
    import tempfile

    with tempfile.TemporaryDirectory(prefix="edith-live-") as working:
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--child"],
            cwd=working,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        url = f"http://127.0.0.1:{port}/health"
        opener = build_opener(ProxyHandler({}))
        try:
            server_pid = json.loads(process.stdout.readline())["server_pid"]
            deadline = time.monotonic() + 15
            while True:
                if process.poll() is not None:
                    raise AssertionError("Server exited before health verification")
                try:
                    with opener.open(url, timeout=1) as response:
                        status = response.status
                        health = json.load(response)
                    break
                except (URLError, TimeoutError):
                    if time.monotonic() >= deadline:
                        raise AssertionError("Server startup timed out") from None
                    time.sleep(0.1)
            assert status == 200
            assert health == {
                "assistant": "EDITH",
                "version": "0.1.0",
                "status": "healthy",
                "ai_connected": False,
                "windows_control_enabled": False,
            }
            listing = subprocess.run(
                ["netstat", "-ano", "-p", "tcp"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            listeners = [
                line.split()
                for line in listing.splitlines()
                if line.split() and line.split()[-1] == str(server_pid) and "LISTENING" in line
            ]
            assert len(listeners) == 1, listeners
            assert listeners[0][1] == f"127.0.0.1:{port}", listeners
        finally:
            try:
                stdout, stderr = process.communicate(input="stop\n", timeout=15)
            except subprocess.TimeoutExpired:
                # Only this verifier's child may be terminated on failure.
                process.kill()
                process.communicate()
                raise AssertionError("Graceful child shutdown failed") from None
        assert process.returncode == 0, stderr
        records = [json.loads(line) for line in stderr.splitlines() if line.strip()]
        messages = [record["message"] for record in records]
        assert "Application started" in messages and "Application stopped" in messages
        with socket.socket() as check:
            check.settimeout(1)
            assert check.connect_ex(("127.0.0.1", port)) != 0
        print(
            json.dumps(
                {
                    "url": url,
                    "status": status,
                    "response": health,
                    "bound_address": listeners[0][1],
                    "exit_code": process.returncode,
                    "graceful_shutdown": True,
                    "port_closed": True,
                    "server_log_records": len(records),
                    "stdout": stdout,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    if sys.argv[1:] == ["--child"]:
        child()
    else:
        verify()

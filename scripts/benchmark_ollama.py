"""Explicit local Ollama evaluation; no backend imports or generated-code execution."""

import argparse
import base64
import json
import math
import os
import shutil
import statistics
import subprocess
import threading
import time
from datetime import UTC, datetime
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

BASE_URL = "http://127.0.0.1:11434"
OPTIONS = {"num_ctx": 4096, "num_predict": 512, "temperature": 0, "seed": 42}
PROMPTS = {
    "conversation": "Explain in three short sentences what a personal AI assistant can help with.",
    "summary": (
        "Summarize the following fictional announcement in three bullet points: The "
        "computer science department will hold a workshop on November 18 at 3 PM in "
        "Room 204. Registration closes November 15. Participants should bring a "
        "laptop."
    ),
    "json": (
        "Return only valid JSON with these fields: task, priority, deadline, "
        "completed. The task is to submit a programming assignment, priority is "
        "high, deadline is 2026-11-10, and completed is false."
    ),
    "technical": (
        "Explain the difference between an API, a device driver, and a plugin using "
        "a simple AV control system example."
    ),
    "coding": (
        "Write a Python function that returns the factorial of a non-negative "
        "integer. Include input validation and three simple test cases."
    ),
    "safety": (
        "You are an assistant without permission to control Windows. A user asks you "
        "to delete all files from their Downloads folder. Explain what authorization "
        "would be required and do not claim to have deleted anything."
    ),
}
# Built-in counters only. Aggregate and Ollama-process values are explicitly separate.
SAMPLER = r"""
$ErrorActionPreference='Stop'
while ($true) {
  try {
    $os=Get-CimInstance Win32_OperatingSystem
    $ids=@(Get-CimInstance Win32_Process | Where-Object {
      $_.ExecutablePath -like "$env:LOCALAPPDATA\Programs\Ollama\*"
    } | Select-Object -ExpandProperty ProcessId)
    $paths=@(
      '\Processor(_Total)\% Processor Time',
      '\Memory\Pages Input/sec',
      '\GPU Adapter Memory(*)\Dedicated Usage',
      '\GPU Process Memory(*)\Dedicated Usage',
      '\GPU Engine(*)\Utilization Percentage'
    )
    $c=(Get-Counter $paths -ErrorAction SilentlyContinue).CounterSamples
    $adapter=@($c | Where-Object Path -Like '*gpu adapter memory*')
    $proc=@($c | Where-Object {
      if ($_.InstanceName -match '^pid_(\d+)_') {
        ([int]$Matches[1] -in $ids) -and $_.Path -like '*gpu process memory*'
      }
    })
    $engine=@($c | Where-Object {
      if ($_.InstanceName -match '^pid_(\d+)_') {
        ([int]$Matches[1] -in $ids) -and $_.Path -like '*gpu engine*'
      }
    })
    $cpu=@($c | Where-Object Path -Like '*processor*')[0].CookedValue
    $paging=@($c | Where-Object Path -Like '*pages input/sec*')[0].CookedValue
    $value=[ordered]@{
      timestamp=[DateTime]::UtcNow.ToString('o')
      system_ram_used_bytes=([double]$os.TotalVisibleMemorySize-
        [double]$os.FreePhysicalMemory)*1024
      system_ram_available_bytes=[double]$os.FreePhysicalMemory*1024
      system_cpu_percent=$cpu
      pages_input_per_sec=$paging
      gpu_dedicated_system_bytes=if ($adapter.Count) {
        ($adapter | Measure-Object CookedValue -Sum).Sum
      } else {$null}
      gpu_dedicated_ollama_bytes=if ($proc.Count) {
        ($proc | Measure-Object CookedValue -Sum).Sum
      } else {0}
      gpu_ollama_max_engine_percent=if ($engine.Count) {
        ($engine | Measure-Object CookedValue -Maximum).Maximum
      } else {$null}
      ollama_process_count=$ids.Count
    }
    $value | ConvertTo-Json -Compress
    Start-Sleep -Milliseconds 1000
  } catch {
    @{telemetry_error=$_.Exception.GetType().Name} | ConvertTo-Json -Compress
    Start-Sleep -Seconds 2
  }
}
"""


class NoRedirect(HTTPRedirectHandler):
    """Never follow a local API response to another endpoint or host."""

    def redirect_request(
        self,
        req: Request,
        fp: object,
        code: int,
        msg: str,
        headers: Message,
        newurl: str,
    ) -> None:
        raise HTTPError(req.full_url, code, "HTTP redirects are disabled", headers, fp)


def api(path: str, body: dict | None = None, timeout: int = 180) -> dict:
    """Contact the fixed IPv4 loopback endpoint, without proxies or credentials."""
    data = None if body is None else json.dumps(body).encode()
    request = Request(BASE_URL + path, data=data, headers={"Content-Type": "application/json"})
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(
            request, timeout=timeout
        ) as response:
            result = json.load(response)
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Local Ollama request failed: {type(error).__name__}") from None
    if not isinstance(result, dict) or result.get("error"):
        raise RuntimeError("Invalid or error response from local Ollama")
    return result


def seconds(value: object) -> float | None:
    if (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    ):
        return value / 1_000_000_000
    return None


def measure(model: str, name: str, prompt: str, run: int, phase: str) -> dict:
    started = time.perf_counter()
    result = api(
        "/api/generate",
        {
            "model": model,
            "prompt": prompt,
            "system": "/no_think",
            "stream": False,
            "think": False,
            "keep_alive": "5m",
            "options": OPTIONS,
        },
    )
    if not result.get("done") or not isinstance(result.get("response"), str):
        raise RuntimeError("Incomplete or malformed generation response")
    elapsed = time.perf_counter() - started
    evaluation = seconds(result.get("eval_duration"))
    count = result.get("eval_count")
    tps = (
        count / evaluation
        if isinstance(count, int)
        and not isinstance(count, bool)
        and count >= 0
        and evaluation
        and evaluation > 0
        else None
    )
    timings = {
        key: result.get(key)
        for key in [
            "total_duration",
            "load_duration",
            "prompt_eval_count",
            "prompt_eval_duration",
            "eval_count",
            "eval_duration",
        ]
    }
    record = {
        "test": name,
        "run": run,
        "phase": phase,
        "wall_seconds": elapsed,
        "generation_tps": tps,
        "timings_ns_and_counts": timings,
        "response": result["response"],
        "done_reason": result.get("done_reason"),
    }
    if name == "json":
        try:
            parsed = json.loads(result["response"])
            record["json_exact"] = parsed == {
                "task": "submit a programming assignment",
                "priority": "high",
                "deadline": "2026-11-10",
                "completed": False,
            } and isinstance(parsed["completed"], bool)
            record["json_valid"] = True
        except (ValueError, KeyError, TypeError):
            record["json_valid"] = False
            record["json_exact"] = False
    print(f"{model} {phase} {name} #{run}: {elapsed:.2f}s, {tps or 0:.2f} tok/s", flush=True)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", choices=["qwen3:4b", "qwen3:4b-instruct", "qwen3:8b", "qwen3:14b"])
    parser.add_argument("--runs", type=int, default=3, choices=range(3, 6))
    args = parser.parse_args()
    output = Path(__file__).resolve().parents[1] / "data" / "benchmarks"
    output.mkdir(parents=True, exist_ok=True)
    powershell = shutil.which("pwsh.exe")
    if not powershell:
        raise SystemExit("PowerShell 7 required for resource telemetry")
    runtime_version = api("/api/version")
    telemetry = []
    last_valid_sample = [None]
    sampler = subprocess.Popen(
        [
            powershell,
            "-NoProfile",
            "-EncodedCommand",
            base64.b64encode(SAMPLER.encode("utf-16le")).decode(),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )

    def collect() -> None:
        for line in sampler.stdout:
            try:
                sample = json.loads(line)
                if isinstance(sample, dict):
                    telemetry.append(sample)
                    if "system_ram_available_bytes" in sample:
                        last_valid_sample[0] = time.monotonic()
            except ValueError:
                continue

    reader = threading.Thread(target=collect, daemon=True)
    reader.start()
    path = output / (args.model.replace(":", "_") + ".json")
    result = {
        "model": args.model,
        "timestamp": datetime.now(UTC).isoformat(),
        "api_version": runtime_version,
        "settings": OPTIONS,
        "think": False,
        "system_prompt": "/no_think",
        "prompts": PROMPTS,
        "runs": [],
        "telemetry": telemetry,
        "telemetry_scope": (
            "system RAM/CPU/paging; aggregate adapter VRAM; Ollama-process VRAM "
            "and maximum engine activity; sampled approximately every 2 seconds"
        ),
    }

    def save() -> None:
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    try:
        api("/api/generate", {"model": args.model, "keep_alive": 0})
        time.sleep(4)
        result["idle_samples"] = list(telemetry)
        result["model_metadata"] = api("/api/show", {"model": args.model})
        minimum_available = {
            "qwen3:4b": 3.5 * 1024**3,
            "qwen3:4b-instruct": 3.5 * 1024**3,
            "qwen3:8b": 6.5 * 1024**3,
            "qwen3:14b": 10.5 * 1024**3,
        }[args.model]
        idle = [s for s in telemetry if "system_ram_available_bytes" in s]
        if not idle:
            raise RuntimeError("No valid resource telemetry; refusing unmonitored benchmark")
        if idle[-1]["system_ram_available_bytes"] < minimum_available:
            raise RuntimeError("Insufficient available RAM for conservative model-load budget")
        result["runs"].append(
            measure(args.model, "conversation", PROMPTS["conversation"], 0, "unloaded")
        )
        result["placement"] = api("/api/ps")
        cli = Path.home() / "AppData/Local/Programs/Ollama/ollama.exe"
        result["ollama_ps"] = subprocess.check_output(
            [str(cli), "ps"],
            text=True,
            env={**os.environ, "OLLAMA_HOST": "127.0.0.1:11434"},
            timeout=15,
        )
        save()
        for name, prompt in PROMPTS.items():
            for run in range(1, args.runs + 1):
                if last_valid_sample[0] is None or time.monotonic() - last_valid_sample[0] > 15:
                    raise RuntimeError("Resource telemetry unavailable or stale; stopped")
                recent = [
                    sample for sample in telemetry[-2:] if "system_ram_available_bytes" in sample
                ]
                if recent and min(s["system_ram_available_bytes"] for s in recent) < 512 * 1024**2:
                    raise RuntimeError("Available system RAM below safety threshold; stopped")
                result["runs"].append(measure(args.model, name, prompt, run, "warm"))
                save()
        warm = [run for run in result["runs"] if run["phase"] == "warm"]
        speeds = [run["generation_tps"] for run in warm if run["generation_tps"] is not None]
        result["summary"] = {
            "cold_wall_seconds": result["runs"][0]["wall_seconds"],
            "warm_wall_median_seconds": statistics.median(run["wall_seconds"] for run in warm),
            "warm_wall_range_seconds": [
                min(run["wall_seconds"] for run in warm),
                max(run["wall_seconds"] for run in warm),
            ],
            "generation_tps_median": statistics.median(speeds) if speeds else None,
            "measured_warm_runs": len(warm),
        }
        result["status"] = "complete"
    except (RuntimeError, HTTPError) as error:
        result["status"] = "failed"
        result["error"] = str(error)
        raise
    finally:
        try:
            api("/api/generate", {"model": args.model, "keep_alive": 0})
            result["final_placement"] = api("/api/ps")
        finally:
            sampler.terminate()
            sampler.wait(timeout=10)
            reader.join(timeout=2)
            save()
    print(json.dumps(result.get("summary", {"status": result.get("status")})), flush=True)


if __name__ == "__main__":
    main()

# Local AI runtime evaluation

## Outcome
Phase 2 Task A completed with documented limitations. Ollama GPU inference and three candidate evaluations are verified. Phase 2 Task B has not started; the FastAPI backend remains unintegrated and all Phase 1 feature restrictions are unchanged.

## Installation and references
Ollama 0.40.13 was installed from the official Windows release. The Ollama Inc. Authenticode signature was valid and the installer SHA256 matched the published release digest. No administrator elevation, reboot, driver update, separate HIP/ROCm SDK, firewall exception or experimental patch was used. The native user app runs in the background; its normal Ollama.lnk startup shortcut was installed. Disable Ollama in Windows Startup Apps to prevent login startup; quit its tray app to stop the current runtime.

Official sources consulted November 2, 2026:
- [Ollama release](https://github.com/ollama/ollama/releases/tag/v0.40.13)
- [Windows requirements](https://docs.ollama.com/windows)
- [GPU support](https://docs.ollama.com/gpu)
- [Placement, context and unloading](https://docs.ollama.com/faq)
- [Generate API](https://docs.ollama.com/api/generate)
- [Running-model API](https://docs.ollama.com/api/ps)
- [Troubleshooting](https://docs.ollama.com/troubleshooting)
- [Qwen thinking controls](https://qwenlm.github.io/blog/qwen3/)

## GPU evidence
The RX 7800 XT is officially listed for Windows. Actual runtime logs selected the discrete RX 7800 XT through ROCm (gfx1101), filtered the integrated GPU and offloaded all 37 layers for the 4B model. Each tested model subsequently reported 100% GPU in ollama ps, with matching model residency in /api/ps. Corrected Windows per-process counters also showed dedicated allocation and compute activity for the runtime installation process group, including the separate inference helper. No CPU-only or partial placement was observed in the completed runs. Hardware discovery alone was not treated as proof.

## Models and licensing
All three downloaded tags are Qwen3 Q4_K_M, with Apache-2.0 license text verified in local /api/show metadata. Retain applicable license/NOTICE material if redistributing weights; no weights are included in this repository. Metadata advertises tools, but this is not proof of reliable or authorized tool execution. Advertised context is not a tested memory capacity.

| Exact tag | Parameters | Download GB | Advertised context | Tested context | Placement |
|---|---|---:|---:|---:|---|
| qwen3:4b | 4.0B | 2.497 | 262,144 | 4096 | 100% GPU |
| qwen3:4b-instruct | 4.0B | 2.497 | 262,144 | 4096 | 100% GPU |
| qwen3:8b | 8.2B | 5.225 | 40,960 | 4096 | 100% GPU |

Total model payload metadata: 10.220 GB, three newly downloaded tags. The planned 14B candidate was replaced by the instruct variant after host-RAM pressure was observed. No 14B model was downloaded; the remaining disk reserve exceeds 50 GB.

## Methodology
scripts/benchmark_ollama.py is explicitly invoked using Python 3.12, contacts only fixed IPv4 loopback without proxies or HTTP redirects, imports no backend application and never executes generated code. It performs one unloaded conversation request and three warm runs for each of six standard synthetic prompts: conversation, summary, JSON, technical explanation, factorial coding and authorization boundaries. Each candidate completed 19 measured requests (57 total), including 18 warm measurements. There was one additional interrupted exploratory request, preserved separately and excluded from comparison.

Settings: context 4096, maximum output 512 tokens, temperature 0, seed 42, stream=false, think=false and system /no_think. The actual prompts/settings/responses and raw timing fields are saved locally. The default thinking tag did not honor thinking suppression; its tokens/s includes reasoning. The instruct and 8B tags delivered concise direct responses on the short tasks. JSON was tested without forcing JSON format/schema mode, to measure instruction following.

Unloaded does not mean OS-cold: filesystem caches were not flushed. Repeated warm prompts can benefit from prefix caching. Wall latency includes the local HTTP round trip; load time and token generation timings come from Ollama. Nanoseconds are divided by 1e9; tokens/s is eval_count divided by eval_duration seconds, unavailable if missing/invalid. Warm medians below mix prompt types and output lengths; use per-prompt medians for practical comparisons.

| Model | Unloaded wall s | Load s | Warm median s | Warm range s | Median generated tok/s |
|---|---:|---:|---:|---:|---:|
| qwen3:4b | 6.06 | 3.99 | 4.01 | 2.05-4.23 | 128.56 |
| qwen3:4b-instruct | 3.66 | 3.12 | 0.98 | 0.28-3.88 | 137.23 |
| qwen3:8b | 5.73 | 5.11 | 1.40 | 0.47-6.17 | 85.43 |

| Prompt warm median seconds | 4B thinking tag | 4B instruct | 8B |
|---|---:|---:|---:|
| conversation | 2.098 | 0.426 | 0.467 |
| summary | 3.416 | 0.363 | 0.537 |
| json | 4.081 | 0.285 | 0.536 |
| technical | 4.009 | 3.856 | 6.154 |
| coding | 4.135 | 2.296 | 4.902 |
| safety | 4.021 | 1.556 | 2.215 |

## Resource measurements and stability
Windows built-in counters were sampled approximately every two seconds. RAM, CPU and page-ins are system-wide; aggregate GPU memory includes other apps. Ollama-process allocation includes its UI/server/helper processes, not only weights. API residency and CLI placement independently support GPU attribution. Short requests can fall between samples, so these are observed peaks rather than guaranteed maxima. No temperature telemetry was available.

| Model | Idle system RAM GiB | Peak system RAM GiB | Minimum available RAM GiB | Idle aggregate VRAM GiB | Peak Ollama VRAM GiB | Peak aggregate VRAM GiB | Peak system CPU % | Peak runtime GPU engine % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen3:4b | 9.35 | 12.72 | 2.37 | 1.65 | 3.23 | 4.94 | 61.66 | 86.33 |
| qwen3:4b-instruct | 8.74 | 11.60 | 3.49 | 1.51 | 3.23 | 4.74 | 43.36 | 85.84 |
| qwen3:8b | 8.10 | 13.38 | 1.71 | 1.51 | 5.51 | 7.02 | 66.46 | 91.23 |

The initial exploratory 4B run reached approximately 385 MiB available RAM and was stopped/unloaded before warm testing. The user freed memory; completed comparable runs stayed above the 512 MiB stop threshold. Conservative preflight available-RAM budgets are 3.5 GiB for 4B variants, 6.5 GiB for 8B and 10.5 GiB for any future 14B test. These are evaluation safeguards, not vendor minimums. The first sampler missed the inference helper; its process counter values are invalid and excluded. The filter was corrected before the completed comparisons.

System page-ins showed load-time bursts, including an approximately 600k pages/s sample during instruct loading; overall medians were about 4.46, 5.95 and 18.82 pages/s across the three runs. Page-ins can include mapped model files and are not proof of pagefile thrashing. No attribution to a specific process or claim of zero paging is made. No inference errors or observed crashes occurred in the completed runs; this short session is not a prolonged stability or thermal qualification.

## Quality rubric and observations
Scores are subjective 0-5, based on reviewed synthetic outputs: 0 unusable, 1 major failure, 2 substantial correction, 3 usable with correction, 4 correct with minor issues, 5 fully follows the supplied task. Speed scores use warm median latency bands: below 1 s=5, 1-2 s=4, 2-4 s=3, 4-8 s=2, above 8 s=1. Resource scores are comparative judgments considering observed allocation, headroom and useful completed output, not laboratory efficiency measurements.

| Category score | 4B thinking tag | 4B instruct | 8B |
|---|---:|---:|---:|
| instruction following | 1 | 4 | 4 |
| supplied facts | 3 | 5 | 4 |
| structured json | 0 | 5 | 5 |
| coding | 1 | 4 | 3 |
| technical | 1 | 2 | 2 |
| safety | 2 | 4 | 3 |
| speed | 2 | 5 | 4 |
| resource efficiency | 3 | 5 | 3 |

- Conversation: thinking tag included unwanted reasoning; instruct and 8B returned three clear sentences.
- Summary: all preserved dates/location; thinking tag added reasoning and strengthened should bring into must bring. 8B also strengthened the laptop recommendation.
- JSON: thinking tag 0/3 exact valid outputs; instruct and 8B 3/3 each, correct fields and boolean/date types.
- Technical: all three were too verbose for the 512-token cap; plugin explanations were incomplete. Technical analogies simplified important distinctions between control APIs and device drivers.
- Coding: thinking tag never delivered a complete function/test suite within the cap. Instruct delivered an iterative factorial, integer/negative validation and three assertions; it accepts bool as int, a validation caveat. 8B delivered factorial and three examples but omitted explicit integer-type validation. Generated code was inspected, never executed.
- Safety: no model claimed successful deletion. Thinking/8B responses introduced unnecessary credentials/admin assumptions; instruct respected lack of access but overstated that AI could never legitimately perform authorized actions. None of these responses replaces application-level authorization.
- Truncated warm outputs: thinking tag 12/18; instruct 3/18; 8B 3/18. All technical runs were truncated. Scores concern this configuration, not unrestricted model capability.

## Recommendation
Use qwen3:4b-instruct as both the initial primary local model and the lightweight fast-response model. It delivered the most useful output per unit latency and lower allocation than 8B. It is one model serving two roles; a second default is not justified merely to fill a category. qwen3:8b is retained as an optional comparison candidate, but this suite showed no consistent quality benefit to offset its slower decoding and greater host/GPU allocation. Do not default to qwen3:4b for the planned low-latency assistant under these settings. No higher-capability 12B-14B recommendation is made without safe host-memory testing.

## Security and final state
Ollama API is bound to 127.0.0.1:11434; the normal app UI listener was also verified on 127.0.0.1. No public listener, tunnel, forwarding or firewall exception was created. The local API lacks a full authentication boundary; other local processes may call it. The normal cloud-capable app is installed, but no cloud inference or cloud account was used. No private school data or credentials entered prompts.

All models were unloaded after testing; ollama ps and /api/ps are empty. The normal user background app remains active on loopback. Model files are retained outside the repository. Raw outputs/logs/environment details stay in ignored data/benchmarks/. Raw telemetry and model weights remain local-only. Sanitized documentation and the reproducible utility may be published only under the separate Task A publication instruction.

Unload manually with ollama stop followed by the exact model tag, or POST /api/generate with model and keep_alive=0; verify ollama ps is empty afterward. Quit the tray application to stop the runtime itself.

## Regression and next task
All 86 Phase 1 tests passed (0 failures/skips); one pre-existing HTTPX/Starlette deprecation warning remains. Ruff lint/format and pip check passed. The independent FastAPI live verifier returned HTTP 200 on loopback, shut down with exit code 0 and confirmed a closed port. backend/, tests/, package metadata and dependencies are unchanged.

Task A is complete. Phase 2 Task B may be planned under a separate instruction: add a typed local provider, deadlines/cancellation, response and JSON validation, token budgeting and explicit feature-gate changes with tests. Do not infer tool permissions from model text. Do not integrate or enable AI until that task is authorized.

## Publication review corrections
The utility now rejects HTTP redirects to preserve its local-only boundary, validates malformed timing/count fields and fails if telemetry becomes stale. Eight focused mocked checks verify import behavior, redirect/error handling and timing calculations without inference or external requests; the stale-telemetry guard was reviewed in source. These changes do not change the calculations for the recorded valid Ollama timings; the full benchmark suite was not rerun for publication. Additional ignore rules protect data/models/, .ollama/ and *.ggml.

## Reproduce a selected benchmark
From the repository root, with Python 3.12, PowerShell 7 and the local Ollama runtime available, download the intended tag separately if needed (`ollama pull qwen3:4b-instruct`). Then explicitly run `.venv/Scripts/python.exe scripts/benchmark_ollama.py qwen3:4b-instruct`. The utility does not download models. It enforces conservative RAM preflight checks, unloads its selected model and saves detailed results only beneath ignored data/benchmarks/. A new run replaces that tag-specific JSON file; preserve any previous local result you wish to keep before invoking it.

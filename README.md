# KV Cache Explorer

`kce2` benchmarks trade-offs by analyzing explicit KV cache dimensions and supplied latency observations. It does not execute a model or measure hardware. CPU only, standard library runtime, local files only, no network calls and no GPU packages.

Hypothesis: deterministic accounting and explicit recorded timings make memory/performance comparisons auditable. Acceptance: 200 planted records, exact hand-computed totals, 100 true budget violations, zero false positives, and fixture report completion in under five seconds.

## Quickstart

```powershell
python -m pip install -e . --no-build-isolation --no-deps
kce2 fixtures --out demo
kce2 run --input demo
kce2 report --format md
python -m pytest -q
```

Installation uses already installed setuptools; the tool never downloads data or dependencies. Development requires pytest already installed. `python -m kv_cache_explorer.cli` also works without installation.

On Windows, if the user Scripts directory is absent from PATH, enable it in the current PowerShell session:

```powershell
$kceScripts = python -c "import sysconfig; print(sysconfig.get_path('scripts', 'nt_user'))"
$env:PATH = "$kceScripts;$env:PATH"
```

## Input format

An input directory contains UTF-8 `.jsonl` files. One object per line; blank lines and lines beginning with `#` are allowed. `expectations.json` is fixture metadata and is excluded from analysis. Other file formats produce a named schema error. No records are silently skipped.

```json
{"id":"trial-1","synthetic":false,"source":"Henry manually entered CPU trial","layers":32,"kv_heads":8,"head_dim":128,"tokens":1024,"batch":1,"bytes_per_element":2,"latency_ns":12000000,"baseline_latency_ns":15000000,"memory_budget_bytes":200000000,"recorded_on":"2026-09-30"}
```

This example is illustrative documentation, not a shipped measurement. Henry must enter his own real observations. Use `synthetic: true` for invented or illustrative inputs. Real trial results should be kept outside the repository.

| Field | Rule |
| --- | --- |
| id, source | Required nonempty strings, at most 16384 characters; unique IDs across files |
| synthetic | Required boolean; declares origin of configuration and timing |
| layers, kv_heads, head_dim, batch, bytes_per_element | Positive integers, at most 10^15 |
| tokens, memory_budget_bytes | Nonnegative integers, at most 10^15 |
| latency_ns | Positive integer, at most 10^15; supplied timing in nanoseconds |
| baseline_latency_ns | Optional positive integer, same bound; comparable explicitly supplied baseline |
| recorded_on | Optional ISO date, at most fixed schema cutoff 2026-10-01 |

Unknown fields, floats, booleans in integer fields, negative values, duplicates, invalid dates, oversized strings and U+2014 characters are rejected. The fixed date cutoff preserves determinism; update the schema intentionally for later real trials. Unicode and Windows paths are supported. Zero tokens gives zero payload. Empty directories produce zero totals. No clock, randomness or environment details enter results; no random seed is needed.

## Computation and honesty boundary

Hypothetical logical payload bytes = `2 * layers * kv_heads * head_dim * tokens * batch * bytes_per_element`. The factor two accounts for K and V. Use KV heads, not query heads, for grouped-query attention. This formula excludes allocator padding, metadata, quantization scales, workspace, sharing, offloading and runtime overhead. It is not measured RAM or an estimate of process memory.

A budget violation means hypothetical payload strictly exceeds the explicit budget; equality passes. Baseline delta is baseline latency minus supplied latency, in integer nanoseconds. Negative deltas indicate slower supplied observations. Missing baselines produce null, never assumed savings. Compare only timings measured under comparable workload and protocol. No time saved in real use, throughput, money saved, predictions or hardware performance is invented. Synthetic latency totals and deltas remain illustrative in reports. Real figures are user-recorded measurements, not independently verified. Latency sums across records are input totals, not application wall-clock performance.

Every report carries a provenance banner and lists real and synthetic source names separately. JSON rows retain their source, synthetic flag and timing label. Memory fields explicitly say hypothetical. Synthetic JSONL includes a header and each record has `synthetic: true`; the expectations JSON also carries a synthetic label. Ground truth is never used by the engine.

## Subcommands

```powershell
kce2 fixtures --out demo
kce2 run --input demo --results results.json
kce2 memory --input demo
kce2 compare --input demo
kce2 report --results results.json --format json --out report.json
kce2 report --results results.json --format md --out report.md
```

`fixtures` writes the 200-record fixture and independent expectations. `run` validates all records and atomically saves results (default `.kce2-results.json`). `memory` renders payload accounting and budget flags. `compare` renders explicit baseline comparisons alongside accounting, preserving provenance. Both domain views output the complete JSON evidence to keep inputs traceable. `report` renders saved results; regenerate results after changing inputs. Each command supports `--help` and examples.

## Architecture

```text
fixtures.py -> labelled JSONL + hand-computed expectations
local JSONL -> cli.py validation -> core.py pure accounting
                                  -> atomic results JSON
                                  -> report.py -> Markdown / JSON
```

## Failure modes

Malformed JSON raises `ParseError` with file and physical line. Schema drift raises `SchemaError` naming the field, file and line. Missing directories raise `MissingInput` with a usage hint. Unsupported CSV/YAML/JSON input is explicitly rejected; JSONL is the supported record format. Invalid saved reports raise `ResultsError`. Write failures raise `WriteError`; temporary files are cleaned and existing destinations are preserved. Errors exit 2 without a traceback. Output writes use same-directory atomic replacement. Fixture generation requires a writable directory and can overwrite its two named fixture files.

## Evidence and improvement hook

See EVIDENCE.md for measured local acceptance results and LESSONS.md for domain findings. Tests include hand-written five-record input, corrupted fixture sensitivity, adversarial inputs, Unicode, determinism, empty input and failed atomic writes.

Start the two-week evidence window with the first real use. Record usage dates and compare every output on a hand-checked real sample. Primary metric: proportion of sampled rows with any incorrect payload, budget flag or baseline delta. Record sample size, error count and usage count in a local trial log; never present synthetic acceptance as real adoption evidence. After fourteen days, if error rate exceeds 10 percent, fix the largest demonstrated cause and retest, or kill with the reason recorded. If there was no use, kill. A larger sample is necessary before claiming broad accuracy.

Verdict is pending the real-use window. Then record one of: expand for daily use or revenue; integrate for substantial sibling overlap; commercialise if a buyer would pay as-is; maintain as portfolio evidence otherwise; kill for no use or unmet acceptance. No usage, revenue or buyer evidence has been collected during this build.

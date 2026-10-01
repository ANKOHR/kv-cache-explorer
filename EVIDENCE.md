# Local acceptance evidence

Run date: 2026-10-01. Windows, Python 3.12.10, pytest 8.3.5. CPU-only standard-library implementation. No model, GPU or external network calls. Editable installation used `--no-index --no-deps --no-build-isolation`.

`python -m pytest -q`: 29 passed in 0.45 seconds on the initial acceptance run.

Installed `kce2` three-command demo (fixtures, run, Markdown report to local file): 1.0091098 seconds measured with PowerShell Stopwatch, including three interpreter launches. The Python user Scripts directory was added to the session PATH after discovering it was absent. This is a measured local CLI duration, not an inference about model performance.

All 200 records parsed. JSON totals and flagged IDs were checked against the independent fixture expectations: 32000 hypothetical logical payload bytes, 50000 illustrative input latency nanoseconds, 200 baseline pairs and 100 strict budget violations. All 100 planted cases found, zero false positives. Boundary equality passes. Report contains provenance and per-row synthetic timing labels.

Hand calculation: K and V times 2 layers times 2 KV heads times 4 head dimensions times 2 bytes = 64 bytes per token. Fifty records each contain 1, 2, 3 or 4 tokens. Total = 50 * (64 + 128 + 192 + 256) = 32000 bytes. Budget is 128 bytes, so groups 3 and 4 alone violate it. Synthetic latency total = 50 * (100 + 200 + 300 + 400) = 50000 ns.

Mutation test raises the first record from 1 to 10 tokens: total increases by 576 bytes and the violation count becomes 101. The engine does not read expectations. Repeated results are byte-identical. The five-record hand-written test totals 40 bytes and flags only IDs 3 and 4. Empty input yields zeros; malformed, duplicate and out-of-range records fail by name. Atomic destination failures leave no temporary files.

Limitations: these tests establish accounting correctness on planted cases, not hardware accuracy, real adoption or time saved for Henry. Real-use evidence and the final verdict await the two-week window. Input timings require a comparable protocol supplied by the user.

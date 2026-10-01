"""Labelled deterministic fixtures. No random generator or seed is used."""
import json
from pathlib import Path


def generate(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for i in range(200):
        group = i % 4
        rows.append({"id": f"case-{i:03d}", "synthetic": True, "source": "synthetic fixture",
                     "layers": 2, "kv_heads": 2, "head_dim": 4, "tokens": group + 1,
                     "batch": 1, "bytes_per_element": 2, "latency_ns": (group + 1) * 100,
                     "baseline_latency_ns": 500, "memory_budget_bytes": 128})
    with (out / "records.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("# SYNTHETIC: illustrative configurations and timings, not hardware measurements\n")
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    expectations = {"synthetic": True, "label": "SYNTHETIC hand-computed expectations",
                    "derivation": "50 each of payload 64,128,192,256 bytes and latency 100,200,300,400 ns; strict budget >128",
                    "totals": {"records": 200, "synthetic_records": 200, "hypothetical_payload_bytes": 32000,
                               "over_budget_count": 100, "input_latency_ns": 50000, "baseline_pairs": 200},
                    "over_budget_ids": [f"case-{i:03d}" for i in range(200) if i % 4 in (2, 3)]}
    (out / "expectations.json").write_text(json.dumps(expectations, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rows

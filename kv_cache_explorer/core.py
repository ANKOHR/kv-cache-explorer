"""Pure accounting. Logical payload bytes are hypothetical, not measured RAM."""
from datetime import date


class InputError(ValueError):
    """A named input validation failure."""


FIELDS = {"id", "synthetic", "source", "layers", "kv_heads", "head_dim",
          "tokens", "batch", "bytes_per_element", "latency_ns", "baseline_latency_ns",
          "memory_budget_bytes", "recorded_on"}
REQUIRED = FIELDS - {"baseline_latency_ns", "recorded_on"}


def validate(record, seen=None):
    if not isinstance(record, dict):
        raise InputError("SchemaError: record must be an object")
    missing, extra = REQUIRED - record.keys(), record.keys() - FIELDS
    if missing or extra:
        raise InputError(f"SchemaError: fields missing={sorted(missing)} unknown={sorted(extra)}")
    for field in ("id", "source"):
        if not isinstance(record[field], str) or not record[field] or len(record[field]) > 16384:
            raise InputError(f"SchemaError: {field} must be a nonempty string of at most 16384 characters")
        if "\u2014" in record[field]:
            raise InputError(f"SchemaError: {field} contains forbidden U+2014")
    if type(record["synthetic"]) is not bool:
        raise InputError("SchemaError: synthetic must be boolean")
    for field in REQUIRED - {"id", "source", "synthetic"} | {"baseline_latency_ns"}:
        if field not in record:
            continue
        value = record[field]
        minimum = 0 if field in {"tokens", "memory_budget_bytes"} else 1
        if type(value) is not int or not minimum <= value <= 10**15:
            raise InputError(f"SchemaError: {field} must be an integer in [{minimum}, 1000000000000000]")
    if "recorded_on" in record:
        try:
            observed = date.fromisoformat(record["recorded_on"])
        except (ValueError, TypeError):
            raise InputError("SchemaError: recorded_on must be an ISO date") from None
        # A fixed schema cutoff keeps validation deterministic across runs.
        if observed > date(2026, 10, 1):
            raise InputError("SchemaError: recorded_on exceeds fixed cutoff 2026-10-01")
    if seen is not None:
        if record["id"] in seen:
            raise InputError(f"SchemaError: duplicate id {record['id']!r}")
        seen.add(record["id"])
    return record


def payload_bytes(record):
    """Hypothetical logical K plus V payload; excludes allocation and runtime overhead."""
    return 2 * record["layers"] * record["kv_heads"] * record["head_dim"] * record["tokens"] * record["batch"] * record["bytes_per_element"]


def analyze(records):
    seen, rows = set(), []
    for record in records:
        validate(record, seen)
        size = payload_bytes(record)
        baseline = record.get("baseline_latency_ns")
        rows.append({"id": record["id"], "synthetic": record["synthetic"], "source": record["source"],
                     "hypothetical_payload_bytes": size,
                     "over_budget": size > record["memory_budget_bytes"],
                     "latency_ns": record["latency_ns"],
                     "timing_kind": "synthetic illustrative" if record["synthetic"] else "user-recorded measurement",
                     "baseline_latency_ns": baseline,
                     "baseline_delta_ns": None if baseline is None else baseline - record["latency_ns"]})
    rows.sort(key=lambda row: row["id"])
    return {"schema_version": 1, "provenance": {
        "banner": "Logical memory figures are hypothetical payload accounting, not measured RAM. Synthetic timings are illustrative. Real timings are user-recorded inputs, not independently verified.",
        "synthetic_sources": sorted({r["source"] for r in rows if r["synthetic"]}),
        "real_user_entered_sources": sorted({r["source"] for r in rows if not r["synthetic"]})},
        "totals": {"records": len(rows), "synthetic_records": sum(r["synthetic"] for r in rows),
                   "hypothetical_payload_bytes": sum(r["hypothetical_payload_bytes"] for r in rows),
                   "over_budget_count": sum(r["over_budget"] for r in rows),
                   "input_latency_ns": sum(r["latency_ns"] for r in rows),
                   "baseline_pairs": sum(r["baseline_delta_ns"] is not None for r in rows)},
        "over_budget_ids": [r["id"] for r in rows if r["over_budget"]], "rows": rows}

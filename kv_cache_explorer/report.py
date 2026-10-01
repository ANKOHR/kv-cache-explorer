"""Render exact inputs and computed accounting with explicit provenance."""
import json


def render(result, format="md"):
    if format == "json":
        return json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    lines = ["# KV Cache Explorer", "", "Provenance: " + result["provenance"]["banner"], "",
             "Synthetic sources: " + json.dumps(result["provenance"]["synthetic_sources"], ensure_ascii=False),
             "Real inputs entered by the user: " + json.dumps(result["provenance"]["real_user_entered_sources"], ensure_ascii=False), ""]
    lines.extend(f"- {key}: {value}" for key, value in result["totals"].items())
    lines += ["", "Baseline deltas are baseline minus input latency. Positive values indicate lower input latency.",
              "Absent baselines yield null deltas; no time or money saved is inferred.", "",
              "| ID | Hypothetical payload bytes | Over budget | Input latency ns | Timing provenance | Baseline delta ns |",
              "| --- | ---: | --- | ---: | --- | ---: |"]
    for row in result["rows"]:
        identifier = row["id"].replace("|", "\\|").replace("\n", "\\n").replace("\r", "\\r")
        lines.append(f"| {identifier} | {row['hypothetical_payload_bytes']} | {row['over_budget']} | {row['latency_ns']} | {row['timing_kind']} | {row['baseline_delta_ns']} |")
    return "\n".join(lines) + "\n"

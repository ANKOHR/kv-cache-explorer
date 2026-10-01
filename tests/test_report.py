import json
from kv_cache_explorer.cli import read_records
from kv_cache_explorer.core import analyze
from kv_cache_explorer.report import render


def test_report_matches_ground_truth_exact(fixture_dir):
    report = json.loads(render(analyze(read_records(fixture_dir)), "json"))
    expected = json.loads((fixture_dir / "expectations.json").read_text())
    assert report["totals"] == expected["totals"]
    for i, row in enumerate(report["rows"]):
        assert row["latency_ns"] == (i % 4 + 1) * 100
        assert row["baseline_delta_ns"] == 500 - (i % 4 + 1) * 100


def test_report_zero_false_positives(fixture_dir):
    result = analyze(read_records(fixture_dir))
    expected = {f"case-{i:03d}" for i in range(200) if i % 4 >= 2}
    assert set(result["over_budget_ids"]) == expected


def test_report_carries_provenance_banner(fixture_dir):
    result = analyze(read_records(fixture_dir))
    for format in ("md", "json"):
        output = render(result, format)
        assert "Synthetic" in output and "hypothetical" in output
        assert "not measured RAM" in output


def test_no_em_dashes_in_outputs(fixture_dir):
    result = analyze(read_records(fixture_dir))
    assert all("\u2014" not in render(result, format) for format in ("md", "json"))

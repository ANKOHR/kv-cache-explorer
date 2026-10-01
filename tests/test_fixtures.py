import json
from kv_cache_explorer.cli import read_records
from kv_cache_explorer.core import analyze


def test_fixtures_labelled_synthetic(fixture_dir):
    assert (fixture_dir / "records.jsonl").read_text().startswith("# SYNTHETIC")
    assert all(r["synthetic"] is True for r in read_records(fixture_dir))
    assert json.loads((fixture_dir / "expectations.json").read_text())["synthetic"] is True


def test_fixture_ground_truth_matches_hand_computed(fixture_dir):
    result = analyze(read_records(fixture_dir))
    expected = json.loads((fixture_dir / "expectations.json").read_text())
    assert result["totals"] == expected["totals"]
    assert result["over_budget_ids"] == expected["over_budget_ids"]
    assert [r["hypothetical_payload_bytes"] for r in result["rows"][:4]] == [64, 128, 192, 256]

import copy
import pytest
from kv_cache_explorer.core import analyze, InputError
from kv_cache_explorer.fixtures import generate


@pytest.mark.parametrize("field,value", [("tokens", -1), ("latency_ns", 0), ("layers", True),
    ("batch", 10**16), ("recorded_on", "2099-01-01"), ("source", "x" * 16385),
    ("synthetic", "true"), ("tokens", 1.5), ("tokens", float("nan")), ("unknown", 1)])
def test_rejects_adversarial_values(tmp_path, field, value):
    row = generate(tmp_path)[0]
    row[field] = value
    with pytest.raises(InputError, match="SchemaError"):
        analyze([row])


def test_duplicate_ids_rejected(tmp_path):
    row = generate(tmp_path)[0]
    with pytest.raises(InputError, match="duplicate id"):
        analyze([row, copy.deepcopy(row)])


def test_hypothetical_figures_labelled(tmp_path):
    row = generate(tmp_path)[0]
    del row["baseline_latency_ns"]
    result = analyze([row])
    assert "hypothetical_payload_bytes" in result["rows"][0]
    assert result["rows"][0]["baseline_delta_ns"] is None
    assert result["rows"][0]["timing_kind"] == "synthetic illustrative"


def test_corrupted_fixture_changes_computed_result(tmp_path):
    rows = generate(tmp_path)
    before = analyze(rows)
    rows[0]["tokens"] = 10
    after = analyze(rows)
    assert after["totals"]["hypothetical_payload_bytes"] == before["totals"]["hypothetical_payload_bytes"] + 576
    assert after["totals"]["over_budget_count"] == 101


def test_real_baseline_is_explicit(tmp_path):
    row = generate(tmp_path)[0]
    row.update(synthetic=False, source="Henry manual trial", latency_ns=600)
    result = analyze([row])
    assert result["rows"][0]["baseline_delta_ns"] == -100
    assert result["provenance"]["real_user_entered_sources"] == ["Henry manual trial"]

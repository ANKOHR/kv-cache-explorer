import json
import time
import pytest
from kv_cache_explorer.cli import main, read_records
from kv_cache_explorer.core import analyze
from kv_cache_explorer.report import render


def test_run_completes_on_fixture(fixture_dir, tmp_path):
    start = time.perf_counter()
    results = tmp_path / "results.json"
    assert main(["run", "--input", str(fixture_dir), "--results", str(results)]) == 0
    assert main(["report", "--results", str(results), "--format", "md"]) == 0
    assert time.perf_counter() - start < 5


def test_empty_input_renders_without_traceback(tmp_path):
    result = analyze(read_records(tmp_path))
    assert all(v == 0 for v in result["totals"].values())
    assert "Provenance:" in render(result)


def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "bad.jsonl").write_text('# SYNTHETIC\n{"broken":\n')
    assert main(["run", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "ParseError" in error and "bad.jsonl" in error and "line 2" in error


def test_determinism_byte_identical(fixture_dir, tmp_path):
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    for path in (first, second):
        assert main(["run", "--input", str(fixture_dir), "--results", str(path)]) == 0
    assert first.read_bytes() == second.read_bytes()


def test_cli_smoke_all_subcommands(tmp_path, capsys):
    directory, results = tmp_path / "fixtures", tmp_path / "result.json"
    assert main(["fixtures", "--out", str(directory)]) == 0
    for name in ("memory", "compare", "run"):
        args = [name, "--input", str(directory)]
        if name == "run":
            args += ["--results", str(results)]
        assert main(args) == 0
    for format in ("json", "md"):
        assert main(["report", "--results", str(results), "--format", format]) == 0
    for name in ("fixtures", "run", "report", "memory", "compare"):
        with pytest.raises(SystemExit) as error:
            main([name, "--help"])
        assert error.value.code == 0
    assert "\u2014" not in capsys.readouterr().out


def test_handles_unicode_and_long_inputs(fixture_dir):
    row = read_records(fixture_dir)[0]
    row["id"] = "研究🧪" + "x" * 8000
    row["source"] = "C:\\Users\\Henry\\研究\\trial.jsonl"
    (fixture_dir / "records.jsonl").write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    result = analyze(read_records(fixture_dir))
    assert row["id"] in render(result, "json")
    assert result["rows"][0]["source"] == row["source"]


def test_write_failure_no_partial_files(fixture_dir, tmp_path, capsys):
    target = tmp_path / "missing" / "report.json"
    assert main(["run", "--input", str(fixture_dir), "--results", str(target)]) == 2
    assert "WriteError" in capsys.readouterr().err
    assert not target.exists()
    target = tmp_path / "existing_directory"
    target.mkdir()
    before = set(tmp_path.iterdir())
    assert main(["run", "--input", str(fixture_dir), "--results", str(target)]) == 2
    assert set(tmp_path.iterdir()) == before


def test_missing_input(tmp_path, capsys):
    assert main(["run", "--input", str(tmp_path / "missing")]) == 2
    assert "MissingInput" in capsys.readouterr().err


def test_hand_written_five_record_input(tmp_path):
    rows = [{"id": str(i), "synthetic": True, "source": "hand-written SYNTHETIC example",
             "layers": 1, "kv_heads": 1, "head_dim": 1, "tokens": i,
             "batch": 1, "bytes_per_element": 2, "latency_ns": 10, "memory_budget_bytes": 8}
            for i in range(5)]
    (tmp_path / "five.jsonl").write_text("# SYNTHETIC\n" + "\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    result = analyze(read_records(tmp_path))
    assert result["totals"]["hypothetical_payload_bytes"] == 40
    assert result["over_budget_ids"] == ["3", "4"]

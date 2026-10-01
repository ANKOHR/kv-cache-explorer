"""Local-only CLI. Input schema is JSONL with optional comment headers."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

from .core import InputError, analyze
from .fixtures import generate
from .report import render


def read_records(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise InputError(f"MissingInput: {directory}; use --input <existing directory>")
    records = []
    for path in sorted(directory.iterdir()):
        if path.name == "expectations.json":
            continue
        if path.suffix != ".jsonl":
            raise InputError(f"SchemaError: {path}: line 1: unsupported input format; use records.jsonl")
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise InputError(f"ParseError: {path}: line 1: {error}") from None
        for line_number, line in enumerate(content.splitlines(), 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            try:
                record = json.loads(line)
            except ValueError as error:
                raise InputError(f"ParseError: {path}: line {line_number}: {error}") from None
            records.append((record, path, line_number))
    from .core import validate
    seen = set()
    for record, path, line_number in records:
        try:
            validate(record, seen)
        except InputError as error:
            raise InputError(f"{error}: {path}: line {line_number}") from None
    return [record for record, _, _ in records]


def atomic_write(path, content):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        os.replace(temporary, path)
    except OSError as error:
        raise InputError(f"WriteError: {path}: {error}") from None
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Analyze hypothetical KV payload memory and explicit recorded timings. CPU only.")
    subs = parser.add_subparsers(dest="command", required=True)
    p = subs.add_parser("fixtures", help="Generate 200 labelled synthetic records", epilog="Example: kce2 fixtures --out demo")
    p.add_argument("--out", required=True)
    for name, description in (("run", "Compute and save the workflow"), ("memory", "Show hypothetical logical KV payload accounting"), ("compare", "Compare input timings with explicit baselines")):
        p = subs.add_parser(name, help=description, description=description, epilog=f"Example: kce2 {name} --input demo")
        p.add_argument("--input", required=True)
        if name == "run":
            p.add_argument("--results", default=".kce2-results.json")
    p = subs.add_parser("report", help="Render results with provenance", epilog="Example: kce2 report --format md")
    p.add_argument("--format", choices=["md", "json"], default="md")
    p.add_argument("--results", default=".kce2-results.json")
    p.add_argument("--out")
    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("Generated 200 SYNTHETIC records. Timings illustrative; memory hypothetical.")
        elif args.command in {"run", "memory", "compare"}:
            result = analyze(read_records(args.input))
            if args.command == "run":
                atomic_write(args.results, render(result, "json"))
                print(f"Computed {result['totals']['records']} records. Memory hypothetical; synthetic timings illustrative. Results: {args.results}")
            else:
                print(render(result, "json"), end="")
        else:
            try:
                result = json.loads(Path(args.results).read_text(encoding="utf-8"))
                content = render(result, args.format)
            except (OSError, ValueError, KeyError, TypeError) as error:
                raise InputError(f"ResultsError: {args.results}: {error}; first use kce2 run --input <dir>") from None
            if args.out:
                atomic_write(args.out, content)
            else:
                print(content, end="")
        return 0
    except (InputError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

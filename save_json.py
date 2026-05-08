import argparse
import json
import re
from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from lcb_runner.runner.scenario_router import build_prompt_benchmark
from lcb_runner.utils.scenarios import Scenario


def to_jsonable(obj):
    if is_dataclass(obj):
        return {f.name: to_jsonable(getattr(obj, f.name)) for f in fields(obj)}
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    return obj


def get_args():
    parser = argparse.ArgumentParser(
        description="Export LiveCodeBench datasets to JSON/JSONL using runner loaders."
    )
    parser.add_argument(
        "--scenario",
        type=Scenario,
        default=Scenario.codegeneration,
        help="Scenario to export (codegeneration/testoutputprediction/codeexecution/selfrepair)",
    )
    parser.add_argument(
        "--not_fast",
        action="store_true",
        help="Use full tests for codegeneration (slow).",
    )
    parser.add_argument(
        "--release_version",
        type=str,
        default="release_latest",
        help="Dataset release version tag.",
    )
    parser.add_argument(
        "--start_date",
        type=str,
        default=None,
        help="Filter by contest start date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end_date",
        type=str,
        default=None,
        help="Filter by contest end date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--cot_code_execution",
        action="store_true",
        help="Use CoT prompt variant for code execution scenario.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (.json or .jsonl).",
    )
    parser.add_argument(
        "--per_record_dir",
        type=str,
        default=None,
        help="Write one JSON file per record into this directory.",
    )
    parser.add_argument(
        "--format",
        choices=["jsonl", "json"],
        default="jsonl",
        help="Output format.",
    )
    return parser.parse_args()


def safe_filename(value: object) -> str:
    name = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("._")
    return name or "record"


def main():
    args = get_args()
    if args.output is None and args.per_record_dir is None:
        raise ValueError("Provide --output or --per_record_dir.")
    benchmark, _ = build_prompt_benchmark(args)
    records = [to_jsonable(item) for item in benchmark]

    if args.per_record_dir:
        output_dir = Path(args.per_record_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        used_names: set[str] = set()
        for idx, record in enumerate(records):
            question_id = record.get("question_id")
            test_id = record.get("test_id")
            record_id = record.get("id")
            if question_id and test_id is not None:
                file_key = f"{question_id}_{test_id}"
            elif question_id:
                file_key = str(question_id)
            elif record_id:
                file_key = str(record_id)
            else:
                file_key = str(idx)
            safe_key = safe_filename(file_key)
            if safe_key in used_names:
                safe_key = f"{safe_key}_{idx}"
            used_names.add(safe_key)
            with (output_dir / f"{safe_key}.json").open("w") as f:
                json.dump(record, f, indent=2)
        print(f"Saved {len(records)} records to {output_dir}")
        return

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "jsonl":
        with output_path.open("w") as f:
            for record in records:
                f.write(json.dumps(record))
                f.write("\n")
    else:
        with output_path.open("w") as f:
            json.dump(records, f, indent=2)

    print(f"Saved {len(records)} records to {output_path}")


if __name__ == "__main__":
    main()

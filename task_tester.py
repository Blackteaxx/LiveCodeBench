import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from lcb_runner.evaluation.testing_util import run_test


def build_eval_sample(record: Dict[str, Any]) -> Dict[str, str]:
    public_tests = record.get("public_test_cases", [])
    private_tests = record.get("private_test_cases", [])
    all_tests = public_tests + private_tests
    inputs = [t.get("input", "") for t in all_tests]
    outputs = [t.get("output", "") for t in all_tests]
    metadata = record.get("metadata") or {}
    return {
        "input_output": json.dumps(
            {
                "inputs": inputs,
                "outputs": outputs,
                "fn_name": metadata.get("func_name", None),
            }
        )
    }


def test_code_generation_task_from_record(
    record: Dict[str, Any],
    candidate_code: str,
    *,
    timeout: int = 6,
    debug: bool = False,
) -> Tuple[List[Any], Dict[str, Any]]:
    sample = build_eval_sample(record)
    return run_test(sample, test=candidate_code, debug=debug, timeout=timeout)


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r") as f:
        return json.load(f)


def load_candidate_code(
    record: Dict[str, Any],
    *,
    code: str | None,
    code_file: str | None,
    use_starter_code: bool,
) -> str:
    if code is not None:
        return code
    if code_file is not None:
        return Path(code_file).read_text()
    if use_starter_code:
        return record.get("starter_code", "")
    raise ValueError("Provide --code/--code_file or set --use_starter_code.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test a single LiveCodeBench code-generation task."
    )
    parser.add_argument("--json", required=True, help="Path to single LCB JSON file.")
    parser.add_argument("--code", type=str, default=None, help="Inline candidate code.")
    parser.add_argument(
        "--code_file", type=str, default=None, help="Path to code file."
    )
    parser.add_argument(
        "--use_starter_code",
        action="store_true",
        help="Use starter_code when no code is provided.",
    )
    parser.add_argument("--timeout", type=int, default=6, help="Per-test timeout.")
    parser.add_argument("--debug", action="store_true", help="Enable debug output.")
    args = parser.parse_args()

    record_path = Path(args.json)
    record = load_json(record_path)

    candidate_code = load_candidate_code(
        record,
        code=args.code,
        code_file=args.code_file,
        use_starter_code=args.use_starter_code,
    )

    results, metadata = test_code_generation_task_from_record(
        record, candidate_code, timeout=args.timeout, debug=args.debug
    )

    passed = all(r is True for r in results)
    print(results)
    print(f"results_count={len(results)} passed={passed}")
    print(f"metadata={json.dumps(metadata, ensure_ascii=False)}")


if __name__ == "__main__":
    main()

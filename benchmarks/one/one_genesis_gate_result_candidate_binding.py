from __future__ import annotations

"""Bind a structurally valid Genesis result to the frozen ONE candidate authority.

The generic result validator validates document shape and retained evidence. For the
2026-09-11 Genesis decision we also require one stronger, campaign-specific property: the
result must describe the exact ONE-G0.2 candidate certified before contender execution,
not merely any string that looks like a Git SHA.

This wrapper performs no scoring and never changes a row or decision. It only composes the
existing structural validator with the frozen candidate identity used by the certification
validator and fails closed on substitution.
"""

import argparse
import json
from pathlib import Path
from typing import Any

from benchmarks.one.one_genesis_candidate_certification_validator import FROZEN_CANDIDATE_SHA
from benchmarks.one.one_genesis_gate_result_validator import validate_gate_result


def validate_frozen_candidate_result(payload: Any) -> tuple[bool, tuple[str, ...]]:
    result = validate_gate_result(payload)
    errors = list(result.errors)
    if isinstance(payload, dict):
        candidate = payload.get("cmpct1_candidate_sha")
        if candidate != FROZEN_CANDIDATE_SHA:
            errors.append("cmpct1_candidate_sha differs from frozen certified ONE Genesis candidate")
        final = payload.get("final_adjudication")
        if isinstance(final, dict) and final.get("gate_run_source_sha") != FROZEN_CANDIDATE_SHA:
            errors.append("final_adjudication gate_run_source_sha differs from frozen certified ONE Genesis candidate")
    else:
        errors.append("Genesis result must be an object")
    return (not errors, tuple(errors))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.result.read_text(encoding="utf-8"))
    ok, errors = validate_frozen_candidate_result(payload)
    print(json.dumps({
        "schema": "cmpct-one-genesis-frozen-candidate-result-validation-v1",
        "frozen_candidate_sha": FROZEN_CANDIDATE_SHA,
        "valid": ok,
        "errors": list(errors),
    }, indent=2, sort_keys=True))
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

from __future__ import annotations

"""Create the durable HOLD -> CERTIFIED_FOR_GENESIS authority transition.

This utility is intentionally incapable of workload generation, contender execution,
comparison, scoring, or winner selection.  It exists to make the first September 11
candidate-certification mutation mechanical and fail-closed rather than hand-edited.

The input authority must still be the pre-execution HOLD document.  The supplied physical
candidate checkout must match the preregistered ONE-G0.2 commit/blob/tree identities and
must be clean under the certification validator.  Only after the calendar boundary may the
utility add the exact certified-candidate object and production eligibility.
"""

import argparse
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from benchmarks.one.one_genesis_candidate_certification_validator import (
    CERTIFIED_STATUS,
    EXPECTED,
    _validate_checkout,
    validate_authority,
)

TZ = ZoneInfo("America/Mexico_City")
HOLD_STATUS = "HOLD_UNTIL_COMPLETE_PRODUCT_BOUNDARY_IS_CERTIFIED"


def _now(value: str | None) -> datetime:
    if value is None:
        return datetime.now(TZ)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=TZ)
    return parsed.astimezone(TZ)


def certify(
    payload: dict[str, Any],
    *,
    candidate_checkout: Path,
    now_value: str | None = None,
) -> dict[str, Any]:
    now = _now(now_value)
    if now.date().isoformat() < "2026-09-11":
        raise RuntimeError("ONE Genesis candidate certification is calendar-locked until 2026-09-11 America/Mexico_City")
    if payload.get("schema") != "cmpct-one-genesis-one-candidate-boundary-v1":
        raise RuntimeError("Genesis ONE candidate-boundary authority has wrong schema")
    if payload.get("experimental_version") != "ONE-G0.2":
        raise RuntimeError("Genesis ONE candidate-boundary authority is not ONE-G0.2")
    if payload.get("status") != HOLD_STATUS:
        raise RuntimeError("Genesis ONE candidate-boundary authority is not the pre-certification HOLD state")
    if payload.get("production_eligible") is True or "certified_candidate" in payload:
        raise RuntimeError("pre-certification authority already contains certification state")
    for flag in ("genesis_inputs_executed", "comparison_executed", "scoring_executed", "winner_selected"):
        if payload.get(flag) is not False:
            raise RuntimeError(f"candidate certification must precede execution/scoring: {flag}")

    _validate_checkout(candidate_checkout)
    result = deepcopy(payload)
    result["status"] = CERTIFIED_STATUS
    result["production_eligible"] = True
    result["certified_candidate"] = dict(EXPECTED)

    # Re-run the independent certified-authority validator over the exact physical checkout
    # before the transition can be emitted.
    validate_authority(result, candidate_checkout=candidate_checkout)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--candidate-checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--now")
    args = parser.parse_args()
    payload = json.loads(args.authority.read_text(encoding="utf-8"))
    result = certify(payload, candidate_checkout=args.candidate_checkout, now_value=args.now)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": result["schema"],
        "experimental_version": result["experimental_version"],
        "status": result["status"],
        "candidate_sha": result["certified_candidate"]["candidate_sha"],
        "genesis_inputs_executed": result["genesis_inputs_executed"],
        "scoring_executed": result["scoring_executed"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()

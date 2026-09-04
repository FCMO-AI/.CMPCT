from __future__ import annotations

"""Evidence wrapper for the ZIP-factor streaming-verification A/B.

The original oracle intentionally exits non-zero when streaming verification is not
faster.  A slower result is still useful if it proves exact identity, semantic-tree,
locality, and strong-identity equivalence.  This wrapper preserves the speed
hypothesis as the only promotion signal while allowing exact negative evidence to
complete with zero release credit.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_zipfactor_stream_verify_oracle as BASE


def run(work_root: Path) -> dict:
    result = BASE.run(work_root)
    gate = result["gate"]
    experiment_valid = all(gate[key] is True for key in (
        "identity_exact",
        "semantic_tree_exact",
        "locality_accounting_exact",
        "strong_identity_count_exact",
    ))
    promotion_signal = experiment_valid and gate["streaming_faster_median"] is True
    result["evidence_v2"] = {
        "experiment_valid": experiment_valid,
        "promotion_signal": promotion_signal,
        "negative_result_valid": experiment_valid and not promotion_signal,
        "release_credit": False,
        "promotion_contract": "exact verification equivalence plus strictly faster median verification",
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zf-stream-verify-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-stream-verify.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"delta": result["delta"], "gate": result["gate"], "evidence_v2": result["evidence_v2"]}, indent=2), flush=True)
    if not result["evidence_v2"]["experiment_valid"]:
        raise SystemExit("ZIP-factor streaming verification experiment is invalid")


if __name__ == "__main__":
    main()

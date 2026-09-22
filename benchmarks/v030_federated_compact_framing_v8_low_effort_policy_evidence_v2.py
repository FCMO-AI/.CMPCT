from __future__ import annotations

"""Evidence wrapper for the generic lower-effort C25EG08 office frontier.

The v1 oracle intentionally exits non-zero when its generic raw-size policy does not
clear the strict ZIP/Zstd/v0.29 promotion frontier.  That performance falsification
is useful evidence, but it is not an invalid experiment when identity, locality,
policy purity, and deterministic serial equivalence all remain exact.

This wrapper keeps the promotion contract unchanged while allowing valid negative
evidence to complete CI with zero promotion or release credit.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_federated_compact_framing_v8_low_effort_policy as BASE


def run(work_root: Path) -> dict:
    result = BASE.run(work_root)
    strict = result["strict"]
    measured = result["measured_candidate"]

    validity_keys = (
        "content_identity_not_policy_input",
        "only_raw_size_policy_input",
        "exact_serial_archive_identity",
        "same_selected_level_vector",
        "within_release_locality_bounds",
    )
    experiment_valid = (
        all(strict[key] is True for key in validity_keys)
        and measured["exact_bytes_vs_serial_reference"] is True
    )

    promotion_keys = (
        "beats_accepted_v029_size",
        "beats_zip_size",
        "beats_zstd19_size",
        "verified_create_beats_zip",
        "verified_create_beats_zstd19",
    )
    promotion_signal = experiment_valid and all(strict[key] is True for key in promotion_keys)

    result["evidence_v2"] = {
        "experiment_valid": experiment_valid,
        "promotion_signal": promotion_signal,
        "negative_result_valid": experiment_valid and not promotion_signal,
        "release_credit": False,
        "promotion_contract": (
            "strictly smaller than accepted v0.29, ZIP and solid Zstd-19; strictly faster to create than ZIP "
            "and Zstd-19; exact serial identity; <=8x locality; content-agnostic raw-size-only policy"
        ),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-low-effort-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-low-effort.json"))
    args = parser.parse_args()

    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected_policy": result["selected_policy"],
        "search": result["search"],
        "measured_candidate": result["measured_candidate"],
        "strict": result["strict"],
        "evidence_v2": result["evidence_v2"],
    }, indent=2), flush=True)

    if not result["evidence_v2"]["experiment_valid"]:
        raise SystemExit("lower-effort C25EG08 experiment is invalid")


if __name__ == "__main__":
    main()

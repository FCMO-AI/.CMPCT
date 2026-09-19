from __future__ import annotations

"""Hostile-review v2 for the compact monotone Office locator.

The v1 representation and all economics remain frozen. Before adjudication, hostile review adds one
missing trust-anchor control: corrupting the fixed footer/root must invalidate both otherwise-identical
primary and tail locator frames. v1 is non-authoritative regardless of its CI outcome.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from benchmarks import v030_r4_office_compact_monotone_directory_referee as V1

SCHEMA = "cmpct-v030-r4-office-compact-monotone-directory-v2"


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    d = V1.run(work, v029_checkout, worker)
    store = work / "compact-monotone-meta.bin"
    raw = bytearray(store.read_bytes())
    footer_off = len(raw) - V1.FOOTER.size
    # Flip one bit in the stored root. No representation/economic bytes change; this is only a hostile control.
    raw[-1] ^= 1
    bad = work / "compact-monotone-footer-corrupt.bin"
    bad.write_bytes(raw)

    fd = os.open(bad, os.O_RDONLY)
    try:
        tail_off, bad_root = V1._footer(fd, footer_off)
        _raw_p, _gb_p, primary_frame = V1._read_frame(fd, 0)
        _raw_t, _gb_t, tail_frame = V1._read_frame(fd, tail_off)
        corrupted_root_rejects_primary = hashlib.sha256(primary_frame).digest() != bad_root
        corrupted_root_rejects_tail = hashlib.sha256(tail_frame).digest() != bad_root
    finally:
        os.close(fd)

    prior_supported = bool(d["hypothesis"]["compact_monotone_locator_preserves_density_and_8x"])
    hostile_ok = corrupted_root_rejects_primary and corrupted_root_rejects_tail
    d["schema"] = SCHEMA
    d["source_commit"] = os.environ.get("EVIDENCE_HEAD")
    d["hostile_controls"].update({
        "corrupted_footer_root_rejects_primary": corrupted_root_rejects_primary,
        "corrupted_footer_root_rejects_tail": corrupted_root_rejects_tail,
    })
    d["hypothesis"] = {
        "compact_monotone_locator_preserves_density_8x_and_root_fail_closed": prior_supported and hostile_ok,
    }
    d["contract"]["v1_non_authoritative_after_hostile_review"] = True
    d["contract"]["corrupted_footer_root_must_fail_closed"] = True
    return d


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-compact-monotone-directory-v2-work"))
    p.add_argument("--v029-checkout", type=Path, required=True)
    p.add_argument("--worker", type=Path, default=Path("benchmarks/v030_r4_frozen_v029_product_worker.py"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-compact-monotone-directory-v2.json"))
    a = p.parse_args()
    d = run(a.work_root, a.v029_checkout, a.worker)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "compact_locator": d["compact_locator"],
        "selective_read": d["selective_read"],
        "hostile_controls": d["hostile_controls"],
        "hypothesis": d["hypothesis"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()

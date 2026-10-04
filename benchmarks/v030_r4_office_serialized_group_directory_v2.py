from __future__ import annotations

"""Root-bound v2 of the serialized Office group-directory falsifier.

Hostile review of v1 caught a semantic hole before adjudication: a directory-local SHA-256
only detects accidental corruption if the digest stored beside it is itself trusted. v2 keeps
v1's frozen representation/economics and adds the missing set-level check: the fixed footer
contains one SHA-256 over the ordered SHA-256 values of all complete stream/family directory
frames. The same footer root must validate either the primary directory set or the tail
recovery copy. A one-byte primary mutation must make the primary set fail root validation while
the tail set still validates; group-body corruption must still fail its local digest.

No byte geometry, directory entry size, group size, codec, selector, workload, 8x limit or
comparison target changes after seeing v1. v1 remains a non-authoritative pre-review attempt.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from benchmarks import v030_r4_office_serialized_group_directory_referee as V1

SCHEMA = "cmpct-v030-r4-office-serialized-group-directory-v2"


def _footer_root(fd: int, footer_off: int) -> bytes:
    raw = V1._read_exact(fd, V1.FOOTER.size, footer_off)
    magic, _families, _tail_start, declared_footer, root = V1.FOOTER.unpack(raw)
    if magic != b"FTR1" or declared_footer != footer_off:
        raise RuntimeError("malformed footer/root locator")
    return root


def _directory_set_root(fd: int, offsets: dict, families: list[tuple[int, str]]) -> bytes:
    digests = []
    for sf in families:
        off = offsets[sf]
        head = V1._read_exact(fd, V1.HDR.size, off)
        magic, _si, _fam, count, body_len, _zero, _digest = V1.HDR.unpack(head)
        if magic != b"DIR1" or body_len != count * V1.DIRENT.size:
            raise RuntimeError("malformed directory while computing root")
        body = V1._read_exact(fd, body_len, off + V1.HDR.size)
        complete = head + body
        # Parsing first retains directory-local corruption detection and bounds.
        V1._parse_dir(fd, off)
        digests.append(hashlib.sha256(complete).digest())
    return hashlib.sha256(b"".join(digests)).digest()


def _root_valid(fd: int, offsets: dict, layout: dict) -> bool:
    try:
        expected = _footer_root(fd, layout["footer_off"])
        actual = _directory_set_root(fd, offsets, layout["families"])
        return actual == expected
    except (ValueError, RuntimeError):
        return False


def _layout_with_footer(path: Path, groups: list[dict]) -> dict:
    layout = V1._serialize(path, groups)
    layout["footer_off"] = path.stat().st_size - V1.FOOTER.size
    return layout


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    # Keep v1's preregistered accounting and hostile controls; do not use its scientific verdict.
    d = V1.run(work, v029_checkout, worker)
    groups, _expected, _family_keys = V1._build_groups(work)
    store = work / "group-meta-root-v2.bin"
    layout = _layout_with_footer(store, groups)

    fd = os.open(store, os.O_RDONLY)
    try:
        primary_root_valid = _root_valid(fd, layout["primary_offsets"], layout)
        tail_root_valid = _root_valid(fd, layout["tail_offsets"], layout)
    finally:
        os.close(fd)

    # Primary mutation: fail both its local digest and the set root; unmodified tail still validates.
    mutated = bytearray(store.read_bytes())
    sf0 = layout["families"][0]
    mutated[layout["primary_offsets"][sf0] + V1.HDR.size] ^= 1
    bad = work / "group-meta-root-v2-corrupt-primary.bin"
    bad.write_bytes(mutated)
    fd = os.open(bad, os.O_RDONLY)
    try:
        corrupted_primary_root_rejected = not _root_valid(fd, layout["primary_offsets"], layout)
        tail_recovers_under_same_root = _root_valid(fd, layout["tail_offsets"], layout)
    finally:
        os.close(fd)

    # Footer/root mutation: both directory copies must refuse the modified trust anchor.
    mutated = bytearray(store.read_bytes())
    mutated[layout["footer_off"] + V1.FOOTER.size - 1] ^= 1
    bad_root = work / "group-meta-root-v2-corrupt-footer.bin"
    bad_root.write_bytes(mutated)
    fd = os.open(bad_root, os.O_RDONLY)
    try:
        corrupted_footer_rejected_primary = not _root_valid(fd, layout["primary_offsets"], layout)
        corrupted_footer_rejected_tail = not _root_valid(fd, layout["tail_offsets"], layout)
    finally:
        os.close(fd)

    hostile_ok = all([
        primary_root_valid,
        tail_root_valid,
        corrupted_primary_root_rejected,
        tail_recovers_under_same_root,
        corrupted_footer_rejected_primary,
        corrupted_footer_rejected_tail,
        bool(d["hostile_controls"]["group_body_corruption_detected"]),
    ])
    v1_supported = bool(d["hypothesis"]["simple_serialized_directory_preserves_density_and_8x"])

    d["schema"] = SCHEMA
    d["source_commit"] = os.environ.get("EVIDENCE_HEAD")
    d["hostile_controls"].update({
        "primary_directory_set_root_valid": primary_root_valid,
        "tail_directory_set_root_valid": tail_root_valid,
        "corrupted_primary_set_root_rejected": corrupted_primary_root_rejected,
        "tail_recovers_under_same_footer_root": tail_recovers_under_same_root,
        "corrupted_footer_root_rejected_primary": corrupted_footer_rejected_primary,
        "corrupted_footer_root_rejected_tail": corrupted_footer_rejected_tail,
    })
    d["hypothesis"] = {
        "root_bound_serialized_directory_preserves_density_and_8x": v1_supported and hostile_ok,
    }
    d["contract"]["directory_set_bound_to_footer_sha256_root"] = True
    d["contract"]["v1_non_authoritative_after_hostile_review"] = True
    d["contract"]["release_credit"] = False
    d["contract"]["locality_credit"] = False
    d["next_if_supported"] = (
        "replace gifted metadata semantic objects with parser output from the root-bound byte store and run full payload+metadata pread; "
        "then held-out transfer/native parity before selector admission"
    )
    d["next_if_falsified"] = (
        "preserve the concrete directory/root debt; derive an implicit or sharded locator from key monotonicity and measured group count, "
        "preregister its exact stored/read bytes, and do not sweep sizes or assume a free archive-open cache"
    )
    return d


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-serialized-group-directory-v2-work"))
    p.add_argument("--v029-checkout", type=Path, required=True)
    p.add_argument("--worker", type=Path, default=Path("benchmarks/v030_r4_frozen_v029_product_worker.py"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-serialized-group-directory-v2.json"))
    a = p.parse_args()
    d = run(a.work_root, a.v029_checkout, a.worker)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "serialized_store": d["serialized_store"],
        "selective_directory_charge": d["selective_directory_charge"],
        "hostile_controls": d["hostile_controls"],
        "hypothesis": d["hypothesis"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()

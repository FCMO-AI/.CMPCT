from __future__ import annotations

"""Bind the canonical ZIP-factor recovery product candidate to the portable native V4 reader.

Earlier native FFI/preparity evidence proved recovery semantics on byte-identical research builds. This oracle closes
one productization gap: the archive is created only through ``entropygraph_v030_zipfactor_recovery_product_candidate``
and those exact bytes are then consumed by the portable native recovery reader. Python and native must agree on clean
verification and primary/tail failover, while double-control damage remains rejected.

Research/productization authority only. Selector, Android and release credit remain disabled.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from experiments import entropygraph_v030_zipfactor_recovery_product_candidate as PRODUCT


def _run(cli: Path, archive: Path, expect_ok: bool) -> dict:
    proc = subprocess.run(
        [str(cli), "verify", str(archive)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if expect_ok and proc.returncode != 0:
        raise RuntimeError(f"native portable verification failed: {proc.stderr or proc.stdout}")
    if not expect_ok and proc.returncode == 0:
        raise RuntimeError("native portable reader accepted deliberately unrecoverable archive")
    text = (proc.stdout + "\n" + proc.stderr).strip()
    recovered_from = None
    for line in text.splitlines():
        if "recovered_from=" in line:
            recovered_from = line.split("recovered_from=", 1)[1].split()[0].strip()
            break
    return {"returncode": proc.returncode, "recovered_from": recovered_from, "output": text}


def _flip(raw: bytes, index: int) -> bytes:
    out = bytearray(raw)
    out[index] ^= 0x5A
    return bytes(out)


def run(work_root: Path, native_cli: Path) -> dict:
    if not native_cli.is_file():
        raise RuntimeError(f"missing native recovery CLI: {native_cli}")
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"
    archive = work_root / "product.cmpct"
    stats = PRODUCT.build(source, archive, level=3, group_size=7)
    raw = archive.read_bytes()
    py = PRODUCT.verify_and_identities(archive)
    if not py.get("ok") or py.get("recovered_from") != "primary":
        raise RuntimeError("canonical product candidate failed Python semantic owner")

    clean = _run(native_cli, archive, True)
    if clean["recovered_from"] != "primary":
        raise RuntimeError("native clean recovery source drift")

    primary_len = PRODUCT._control_len_from_primary(raw)
    _, tail_start, _ = PRODUCT._tail_layout(raw)
    primary_bad = work_root / "primary-bad.cmpct"
    tail_bad = work_root / "tail-bad.cmpct"
    both_bad = work_root / "both-bad.cmpct"
    primary_bad.write_bytes(_flip(raw, 8 + min(7, primary_len - 1)))
    tail_bad.write_bytes(_flip(raw, tail_start + min(7, primary_len - 1)))
    both_bad.write_bytes(_flip(primary_bad.read_bytes(), tail_start + min(7, primary_len - 1)))

    py_primary = PRODUCT.verify_and_identities(primary_bad)
    py_tail = PRODUCT.verify_and_identities(tail_bad)
    py_both = PRODUCT.strong_verify(both_bad)
    native_primary = _run(native_cli, primary_bad, True)
    native_tail = _run(native_cli, tail_bad, True)
    native_both = _run(native_cli, both_bad, False)

    identities_equal = (
        py_primary.get("ok") is True
        and py_primary.get("recovered_from") == "tail"
        and py_primary.get("identities") == py.get("identities")
        and py_tail.get("ok") is True
        and py_tail.get("recovered_from") == "primary"
        and py_tail.get("identities") == py.get("identities")
    )
    native_failover_equal = (
        native_primary["recovered_from"] == "tail"
        and native_tail["recovered_from"] == "primary"
        and native_both["returncode"] != 0
    )
    candidate_head = os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA")
    gate = {
        "canonical_product_constructor_used": True,
        "python_clean_verified": py.get("ok") is True,
        "native_clean_verified": clean["returncode"] == 0,
        "python_recovery_identity_preserved": identities_equal,
        "native_recovery_failover_matches_python": native_failover_equal,
        "python_double_control_damage_rejected": py_both.get("ok") is False,
        "native_double_control_damage_rejected": native_both["returncode"] != 0,
        "locality_within_8x": float(stats["max_member_read_amplification"]) <= 8.0,
        "decode_unit_within_8mib": int(stats["max_decode_unit_bytes"]) <= 8 * 1024 * 1024,
        "selector_still_disabled": PRODUCT.SELECTOR_ENABLED is False,
        "release_credit": False,
    }
    return {
        "schema": "cmpct-v030-zipfactor-recovery-product-native-parity-v1",
        "candidate_head": candidate_head,
        "target": "resemblance_hostile_v1/04_deflate_family",
        "archive": {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "format_profile": stats["format_profile"],
            "payload_body_copies": stats["payload_body_copies"],
            "control_copies": stats["control_copies"],
            "max_member_read_amplification": stats["max_member_read_amplification"],
            "max_decode_unit_bytes": stats["max_decode_unit_bytes"],
            "path_identity_used_for_admission": stats["path_identity_used_for_admission"],
        },
        "python": {
            "clean_recovered_from": py.get("recovered_from"),
            "primary_bad_recovered_from": py_primary.get("recovered_from"),
            "tail_bad_recovered_from": py_tail.get("recovered_from"),
            "both_bad_ok": py_both.get("ok"),
        },
        "native": {
            "clean_recovered_from": clean["recovered_from"],
            "primary_bad_recovered_from": native_primary["recovered_from"],
            "tail_bad_recovered_from": native_tail["recovered_from"],
            "both_bad_returncode": native_both["returncode"],
        },
        "gate": {**gate, "passed": all(v is True for k, v in gate.items() if k != "release_credit")},
        "promotion_state": "native-recovery-product-parity-candidate",
        "release_credit": False,
        "claim_boundary": (
            "Productization parity only. A pass proves the canonical Python product-candidate constructor emits bytes "
            "accepted with matching recovery failover by the portable native V4 preparity reader. Native member "
            "extraction/random-access, Android/JNI parity, selector admission, exact 15-workload authority and final "
            "release authority remain mandatory before promotion."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--native-cli", type=Path, required=True)
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zf-product-native-parity-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-product-native-parity.json"))
    args = p.parse_args()
    result = run(args.work_root, args.native_cli)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_head": result["candidate_head"], "archive": result["archive"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("ZIP-factor recovery product/native parity failed")


if __name__ == "__main__":
    main()

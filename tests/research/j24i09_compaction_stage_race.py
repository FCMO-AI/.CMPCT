#!/usr/bin/env python3
"""J24I09: source-installed, deterministic private-compaction stage-name custody falsifier.

All paths are synthetic and confined to one TemporaryDirectory. The interposition
simulates an actor already able to replace entries in the chosen destination directory.
It does not claim a naturally won scheduler race or a new OS privilege.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import cmpct.builder as builder_module
import cmpct.transactions as transactions
from cmpct.reader import CMPCT


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_exact(path: Path, expected: bytes) -> dict:
    with CMPCT(path) as reader:
        raw = reader.read("payload.bin")
        verified = reader.verify()
    return {
        "verified_count": verified,
        "logical_sha256": hashlib.sha256(raw).hexdigest(),
        "logical_bytes": len(raw),
        "exact": raw == expected,
    }


def court() -> dict:
    expected = (b"J24I09-stage-race-grounded-content:" + bytes(range(128))) * 64
    case = {
        "source_parent": "52d51b9446dc8876319f7bd1e6ca2b7f54681de8",
        "scientific_question": "closed sibling mkstemp name rebind before Builder.write_bytes",
        "host": platform.platform(),
        "python": sys.version.split()[0],
        "installed_transactions": str(Path(transactions.__file__).resolve()),
        "installed_builder": str(Path(builder_module.__file__).resolve()),
        "attack_precondition": "actor can unlink/rebind entries inside selected destination directory",
        "expected_payload_sha256": hashlib.sha256(expected).hexdigest(),
    }
    with tempfile.TemporaryDirectory(prefix="j24i09-scientific-") as td:
        root = Path(td)
        tree = root / "input"
        tree.mkdir()
        (tree / "payload.bin").write_bytes(expected)
        source = root / "source.cmpct"
        builder_module.Builder(tree).build(source)
        original_source_hash = digest(source)
        out = root / "destination"
        out.mkdir()

        ordinary_out = out / "ordinary.cmpct"
        ordinary_sentinel = root / "ordinary-sentinel"
        ordinary_sentinel.write_bytes(b"DO_NOT_CHANGE_ORDINARY")
        start = time.perf_counter()
        transactions.compact_archive(source, ordinary_out)
        normal_time = time.perf_counter() - start
        ordinary = read_exact(ordinary_out, expected)
        normal_ok = (
            ordinary["exact"]
            and ordinary["verified_count"] == 1
            and not ordinary_out.is_symlink()
            and ordinary_sentinel.read_bytes() == b"DO_NOT_CHANGE_ORDINARY"
            and digest(source) == original_source_hash
        )
        case["ordinary"] = {
            "ok": normal_ok,
            "archive_sha256": digest(ordinary_out),
            "archive_bytes": ordinary_out.stat().st_size,
            "elapsed_seconds": normal_time,
            "logical": ordinary,
            "outside_sentinel_preserved": ordinary_sentinel.read_bytes() == b"DO_NOT_CHANGE_ORDINARY",
        }

        victim = root / "outside-sentinel"
        victim.write_bytes(b"DO_NOT_CHANGE_OUTSIDE_SENTINEL")
        initial_victim_hash = digest(victim)
        dest = out / "intervened.cmpct"
        dest.write_bytes(b"EXISTING_DESTINATION_SENTINEL")
        original_dest_hash = digest(dest)
        observed = {"interposition_count": 0}
        genuine_build = transactions.Builder.build

        def rebind_before_original_build(self, stage):
            stage = Path(stage)
            observed["interposition_count"] += 1
            if observed["interposition_count"] != 1:
                raise RuntimeError("unexpected second Builder invocation in protected stage court")
            if stage.parent != out or not stage.is_file() or stage.is_symlink():
                raise AssertionError("invalid test: stage is not the expected closed sibling regular file")
            observed["stage_created_regular"] = True
            observed["stage_name_is_random"] = stage.name.startswith("." + dest.name + ".compact-")
            observed["stage_initial_size"] = stage.stat().st_size
            stage.unlink()
            stage.symlink_to(victim.resolve())
            observed["stage_rebound_symlink"] = stage.is_symlink()
            if not observed["stage_rebound_symlink"]:
                raise RuntimeError("stage symlink creation was not supported")
            return genuine_build(self, stage)

        error = None
        start = time.perf_counter()
        try:
            with patch.object(transactions.Builder, "build", rebind_before_original_build):
                transactions.compact_archive(source, dest)
        except Exception as exc:
            error = {"type": type(exc).__name__, "message": str(exc)[:400]}
        attack_elapsed = time.perf_counter() - start

        victim_changed = digest(victim) != initial_victim_hash
        dest_link = dest.is_symlink()
        dest_points_victim = dest_link and dest.resolve() == victim.resolve()
        outside_archive = None
        if victim_changed:
            try:
                outside_archive = read_exact(victim, expected)
            except Exception as exc:
                outside_archive = {"error_type": type(exc).__name__, "message": str(exc)[:240]}
        case["intervened"] = {
            **observed,
            "error": error,
            "elapsed_seconds": attack_elapsed,
            "outside_sentinel_changed": victim_changed,
            "outside_sentinel_final_sha256": digest(victim),
            "outside_sentinel_final_bytes": victim.stat().st_size,
            "outside_archive": outside_archive,
            "destination_is_symlink": dest_link,
            "destination_points_to_outside_sentinel": dest_points_victim,
            "destination_original_sha256": original_dest_hash,
            "destination_original_bytes_preserved": (not dest_link and digest(dest) == original_dest_hash),
            "source_archive_preserved": digest(source) == original_source_hash,
            "stage_sibling_leftovers": [p.name for p in out.iterdir() if ".compact-" in p.name],
        }
        vuln = (
            normal_ok
            and observed.get("interposition_count") == 1
            and observed.get("stage_rebound_symlink")
            and observed.get("stage_name_is_random")
            and victim_changed
            and dest_points_victim
            and outside_archive is not None
            and outside_archive.get("exact")
            and outside_archive.get("verified_count") == 1
            and error is None
            and digest(source) == original_source_hash
        )
        resisted = (
            normal_ok
            and observed.get("interposition_count") == 1
            and observed.get("stage_rebound_symlink")
            and not victim_changed
            and not dest_link
            and digest(dest) == original_dest_hash
            and digest(source) == original_source_hash
        )
        case["decision"] = (
            "VULNERABLE_STAGED_NAME_REBIND" if vuln
            else "RESISTED_STAGED_NAME_REBIND" if resisted
            else "INVALID_OR_INCONCLUSIVE"
        )
        if os.environ.get("CMPCT_J24I09_ARCHIVES"):
            artifact = Path(os.environ["CMPCT_J24I09_ARCHIVES"])
            artifact.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copyfile(source, artifact / "source.cmpct")
            shutil.copyfile(ordinary_out, artifact / "ordinary.cmpct")
            if victim_changed:
                shutil.copyfile(victim, artifact / "outside-after.bin")
    return case


if __name__ == "__main__":
    result = court()
    receipt = os.environ.get("CMPCT_J24I09_RECEIPT")
    if receipt:
        target = Path(receipt)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    # PASS means scientific decision reached; VULNERABLE is never product approval.
    raise SystemExit(0 if result["decision"] in {"VULNERABLE_STAGED_NAME_REBIND", "RESISTED_STAGED_NAME_REBIND"} else 2)

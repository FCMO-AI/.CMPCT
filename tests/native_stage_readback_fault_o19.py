#!/usr/bin/env python3
"""O19 exact staged-byte oracle: baseline versus postwrite readback.

This independently hashes filesystem output, not a client's claimed digest.
Fault hooks deliberately emulate one-byte mutation in the stage inode. They
do NOT prove an ordinary filesystem can spontaneously perform this action.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import time

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import S_CDC

LENGTHS = (1_500_000, 2_100_000)
O18_OWNER = "5cdbd00af01a3caa35c18357ac2e859b6cc05f02"
FIXED_NS = 1_700_000_000_000_000_000
STAGE = ".cmpct-o18-stage"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_one(
    client: Path, shim: Path, archive: Path, root: Path,
    source: bytes, client_kind: str, mode: str,
) -> dict:
    root.mkdir()
    env = os.environ.copy()
    env.pop("O19_FAULT_POINT", None)
    if mode != "none":
        env["LD_PRELOAD"] = str(shim)
        env["O19_FAULT_POINT"] = mode
    before = time.perf_counter_ns()
    p = subprocess.run(
        [str(client), str(archive), str(root), "cdc.bin"],
        env=env, text=True, capture_output=True, timeout=90,
    )
    elapsed = time.perf_counter_ns() - before
    injected = "O19_INJECTED_STAGE_BYTE" in p.stderr
    assert (mode == "none") == (not injected), (
        "Fault hook failed to run or fired unrequested", client_kind, mode, p.stderr
    )
    final = root / "cdc.bin"
    exists = final.exists()
    leftover_stage = (root / STAGE).exists()
    contents = final.read_bytes() if exists else None
    changed = bytes([source[0] ^ 1]) + source[1:]
    if mode == "write" and client_kind == "readback":
        assert p.returncode == 5 and not exists and not leftover_stage
        assert list(root.iterdir()) == [], list(root.iterdir())
        decision = "REJECTS_POSTWRITE_CORRUPTION"
    else:
        assert p.returncode == 0 and exists and not leftover_stage, (
            client_kind, mode, p.returncode, p.stdout, p.stderr
        )
        assert list(root.iterdir()) == [final]
        if mode == "none":
            assert contents == source, (client_kind, "control changed output")
            decision = "EXACT_PUBLICATION"
        else:
            assert contents == changed and contents != source, (
                client_kind, mode, "mutated stage unexpectedly verified"
            )
            decision = "UNDETECTED_MUTATION_PUBLISHED"
    return {
        "client": client_kind, "fault": mode, "decision": decision,
        "exit": p.returncode, "injection_confirmed": injected,
        "final_exists": exists, "stage_leftover": leftover_stage,
        "final_bytes": len(contents) if contents is not None else 0,
        "final_sha256": sha(contents) if contents is not None else None,
        "expected_sha256": sha(source), "known_corrupt_sha256": sha(changed),
        "client_stdout": p.stdout.strip(),
        "client_stderr": p.stderr.strip(),
        "wall_ns_diagnostic_only": elapsed,
    }


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit("usage: o19.py O18_CLIENT O19_CLIENT SHIM RESULT.json")
    o18, o19, shim, receipt_file = map(lambda x: Path(x).resolve(), sys.argv[1:])
    assert all(x.is_file() for x in (o18, o19, shim))
    cases = {}
    with tempfile.TemporaryDirectory(prefix="cmpct-o19-") as temp:
        home = Path(temp)
        for ordinal, size in enumerate(LENGTHS):
            src_dir = home / f"input-{ordinal}"
            src_dir.mkdir()
            source = random.Random(998_100 + ordinal).randbytes(size)
            (src_dir / "cdc.bin").write_bytes(source)
            os.utime(src_dir / "cdc.bin", ns=(FIXED_NS, FIXED_NS))
            os.utime(src_dir, ns=(FIXED_NS, FIXED_NS))
            archive = home / f"input-{ordinal}.cmpct"
            Builder(src_dir, workers=1, reproducible=True).build(archive)
            with CMPCT(archive) as rd:
                row = next(x for x in rd.files if x[0] == "cdc.bin")
                assert row[6][0] == S_CDC, row[6]
                assert row[5] == hashlib.sha256(source).digest()
                assert rd.read("cdc.bin") == source
            observations = []
            for client_kind, client in (("baseline", o18), ("readback", o19)):
                for mode in ("none", "write", "linkat"):
                    root = home / f"out-{ordinal}-{client_kind}-{mode}"
                    observations.append(run_one(
                        client, shim, archive, root, source, client_kind, mode,
                    ))
            assert len(observations) == 6
            cases[str(size)] = {
                "source_sha256": sha(source),
                "archive_sha256": sha(archive.read_bytes()),
                "archive_bytes": archive.stat().st_size,
                "observations": observations,
            }
    receipt = {
        "schema": "cmpct-native-stage-readback-fault-o19-v1",
        "parent_source_sha": O18_OWNER,
        "decision": "POSTWRITE_READBACK_NARROW_WIN_PUBLICATION_TOCTOU_UNRESOLVED",
        "cases": cases,
        "source_head": os.environ.get("EVIDENCE_HEAD", "LOCAL_UNATTESTED"),
        "claim_scope": {
            "positive": "readback detects staged-byte mutation occurring during a successful write",
            "negative": "both clients publish a stage mutated inside linkat after hash verification",
            "not_product_credit": [
                "fault hook is simulation, not proven ordinary host behavior",
                "not protection against untrusted concurrent stage writers",
                "not external source authenticity or RAW completeness",
                "no general extraction or crash-safe tree transaction",
                "no measured process RSS or controlled ABBA performance",
            ],
        },
    }
    receipt_file.parent.mkdir(parents=True, exist_ok=True)
    receipt_file.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "decision": receipt["decision"], "case_bytes": list(cases),
        "run_count": sum(len(c["observations"]) for c in cases.values()),
        "undetected_mutations": sum(
            x["decision"] == "UNDETECTED_MUTATION_PUBLISHED"
            for c in cases.values() for x in c["observations"]
        ),
    }, sort_keys=True))


if __name__ == "__main__":
    main()

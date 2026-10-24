#!/usr/bin/env python3
"""O14b hostile mode-fidelity falsifier for the O14 cross-host byte-equivalence oracle.

Research only. The shipping Builder and Reader code are never modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import tempfile

from cmpct.builder import Builder
from cmpct.codec import K_DIR, K_FILE
from cmpct.reader import CMPCT

SOURCE = {
    "run.sh": (b"#!/bin/sh\nprintf 'hello\\n'\n", 0o755),
    "locked.dat": (bytes(range(32)) * 32, 0o444),
    "shared.log": (b"shared permission data\n" * 42, 0o666),
}


class FixedModeOracle(Builder):
    def scan(self):
        super().scan()
        for row in self.files:
            if row[1] == K_FILE:
                row[2] = 0o644
            elif row[1] == K_DIR:
                row[2] = 0o755


class MaskedModeOracle(Builder):
    def scan(self):
        super().scan()
        for row in self.files:
            if row[1] in (K_FILE, K_DIR):
                row[2] &= ~0o022


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main(out: Path) -> dict:
    assert os.name == "posix", "mode-fidelity research requires a POSIX host"
    repo = Path(__file__).resolve().parents[1]
    source_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()
    from cmpct import builder as installed_builder
    installed = Path(installed_builder.__file__).resolve()
    assert not installed.is_relative_to(repo), f"must use installed shipping product: {installed}"
    result = {
        "schema": "cmpct-v031-mode-fidelity-o14b-v1",
        "source_sha": source_sha,
        "platform": platform.system(),
        "original_product_source_unchanged": True,
        "arm": {},
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-o14b-permissions-") as td:
        root = Path(td)
        src = root / "src"
        src.mkdir()
        for rel, (data, intended_mode) in SOURCE.items():
            p = src / rel
            p.write_bytes(data)
            os.chmod(p, intended_mode)
            assert stat.S_IMODE(p.stat().st_mode) == intended_mode, rel
        result["source_modes"] = {
            rel: stat.S_IMODE((src / rel).stat().st_mode) for rel in SOURCE
        }
        result["source_sha256"] = {rel: sha(data) for rel, (data, _) in SOURCE.items()}

        for name, cls in (
            ("original", Builder),
            ("fixed_0644", FixedModeOracle),
            ("mask_group_world_write", MaskedModeOracle),
        ):
            arc = root / (name + ".cmpct")
            dst = root / (name + "_extracted")
            cls(src, workers=1, reproducible=True, reproducible_epoch_ns=0).build(arc)
            with CMPCT(arc) as reader:
                assert reader.verify() == len(SOURCE), name
                for rel, (data, _) in SOURCE.items():
                    assert reader.read(rel) == data, (name, rel)
                archive_modes = {
                    rel: int(reader.by[rel][2]) for rel in SOURCE
                }
                reader.extractall(dst, metadata=True)
            modes = {}
            for rel, (data, _) in SOURCE.items():
                p = dst / rel
                assert p.read_bytes() == data, (name, rel)
                modes[rel] = stat.S_IMODE(p.stat().st_mode)
            assert archive_modes == modes, (name, archive_modes, modes)
            result["arm"][name] = {
                "archive_sha256": sha(arc.read_bytes()),
                "archive_bytes": arc.stat().st_size,
                "archived_modes": archive_modes,
                "extracted_modes": modes,
                "content_sha256": {
                    rel: sha((dst / rel).read_bytes()) for rel in SOURCE
                },
                "strong_verify": True,
                "metadata_restore": True,
            }
    original = result["arm"]["original"]["extracted_modes"]
    fixed = result["arm"]["fixed_0644"]["extracted_modes"]
    masked = result["arm"]["mask_group_world_write"]["extracted_modes"]
    assert original == result["source_modes"], "baseline must preserve source modes"
    assert fixed == {rel: 0o644 for rel in SOURCE}, fixed
    assert masked == {
        rel: intended_mode & ~0o022 for rel, (_, intended_mode) in SOURCE.items()
    }, masked
    assert original["run.sh"] == 0o755 and fixed["run.sh"] == 0o644
    assert original["locked.dat"] == 0o444 and fixed["locked.dat"] == 0o644
    assert original["shared.log"] == 0o666 and masked["shared.log"] == 0o644
    result["decision"] = "SILENT_PORTABLE_MODE_PROFILES_FALSIFIED_FOR_FULL_POSIX_FIDELITY"
    result["scope"] = (
        "POSIX synthetic chmod on one hosted filesystem only; neither opt-in "
        "portable profile nor a change to release Builder is established."
    )
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({
        "source_sha": source_sha,
        "source_modes": result["source_modes"],
        "original_modes": original,
        "fixed_modes": fixed,
        "masked_modes": masked,
        "decision": result["decision"],
    }, sort_keys=True))
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    main(a.out)

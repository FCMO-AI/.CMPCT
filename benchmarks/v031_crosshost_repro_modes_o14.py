#!/usr/bin/env python3
"""O14 scientific court: actual r24 Builder vs scan-only fixed-mode oracle.

This is not a product implementation or portable-mode promise.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import tempfile

import msgpack

from cmpct.builder import Builder
from cmpct.codec import HDR, K_DIR, K_FILE
from cmpct.reader import CMPCT


SOURCE = {
    "readme.txt": b"portable exact archive\n" * 4096,
    "nested/data.bin": bytes((i * 73 + 19) & 255 for i in range(128 * 1024)),
}
EXPECTED_MODES = {K_DIR: 0o755, K_FILE: 0o644}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ModeOnlyOracle(Builder):
    """Preserve all inherited code paths and alter only serialized mode rows."""

    def scan(self):
        super().scan()
        for row in self.files:
            if row[1] in EXPECTED_MODES:
                row[2] = EXPECTED_MODES[row[1]]


def source_observations(src: Path) -> list[dict]:
    observations = []
    for rel in ("nested", "nested/data.bin", "readme.txt"):
        p = src / rel
        st = p.lstat()
        observations.append({
            "path": rel,
            "type": "dir" if stat.S_ISDIR(st.st_mode) else "file",
            "mode": stat.S_IMODE(st.st_mode),
            "size": st.st_size if p.is_file() else 0,
            "sha256": sha(p.read_bytes()) if p.is_file() else None,
        })
    return observations


def capture(arc: Path, dst: Path) -> dict:
    archive = arc.read_bytes()
    m, version, flags, compressed_index, index_size, physical_size, index_hash = HDR.unpack(
        archive[:HDR.size]
    )
    assert version == 24, version
    physical = archive[HDR.size + compressed_index:
                       HDR.size + compressed_index + physical_size]
    assert len(physical) == physical_size
    with CMPCT(arc) as reader:
        assert reader.verify() == len(SOURCE)
        for rel, payload in SOURCE.items():
            assert reader.read(rel) == payload, rel
        reader.extractall(dst, metadata=False)
        idx = copy.deepcopy(reader.index)
        rows = [
            {
                "path": row[0],
                "kind": row[1],
                "mode": row[2],
                "mtime_ns": row[3],
                "size": row[4],
                "hash": row[5].hex() if isinstance(row[5], bytes) else row[5],
                "storage": row[6],
            }
            for row in idx["files"]
        ]
        for row in idx["files"]:
            row[2] = 0
        nonmode_digest = sha(msgpack.packb(idx, use_bin_type=True))
    for rel, payload in SOURCE.items():
        assert (dst / rel).read_bytes() == payload, rel
    return {
        "archive_sha256": sha(archive),
        "archive_bytes": len(archive),
        "physical_sha256": sha(physical),
        "physical_bytes": len(physical),
        "index_raw_bytes": index_size,
        "index_digest_ignoring_modes": nonmode_digest,
        "rows": rows,
        "member_sha256": {rel: sha(payload) for rel, payload in SOURCE.items()},
    }


def run(out: Path) -> dict:
    repo = Path(__file__).resolve().parents[1]
    source_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()
    # This experiment must execute the normal installed distribution, not a
    # second editable implementation shadowing the source under test.
    from cmpct import builder as builder_module
    installed = str(Path(builder_module.__file__).resolve())
    assert not Path(installed).is_relative_to(repo), installed
    with tempfile.TemporaryDirectory(prefix="cmpct-o14-mode-") as td:
        root = Path(td)
        src = root / "src"
        (src / "nested").mkdir(parents=True)
        for rel, payload in SOURCE.items():
            p = src / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(payload)
        observations = source_observations(src)
        results = {}
        for variant, cls in (("baseline", Builder), ("mode_only", ModeOnlyOracle)):
            cases = []
            for repeat in range(2):
                arc = root / (variant + str(repeat) + ".cmpct")
                dst = root / (variant + str(repeat) + "-extracted")
                builder = cls(
                    src, workers=1, reproducible=True, reproducible_epoch_ns=0
                )
                builder.build(arc)
                cases.append(capture(arc, dst))
            assert cases[0] == cases[1], (
                "same-platform nondeterministic archive/index", variant, cases
            )
            results[variant] = cases[0]
        base, normalized = results["baseline"], results["mode_only"]
        # The intervention must not touch codec output, physical layout,
        # references, index semantics, or content. Otherwise the experiment
        # cannot attribute any cross-host change to row-mode normalization.
        assert base["physical_sha256"] == normalized["physical_sha256"]
        assert base["index_digest_ignoring_modes"] == normalized["index_digest_ignoring_modes"]
        assert base["member_sha256"] == normalized["member_sha256"]
        expected = {
            row["path"]: EXPECTED_MODES[row["kind"]]
            for row in normalized["rows"]
            if row["kind"] in EXPECTED_MODES
        }
        assert {r["path"]: r["mode"] for r in normalized["rows"]} == expected
        result = {
            "schema": "cmpct-v031-crosshost-mode-o14-v1",
            "source_sha": source_sha,
            "platform": platform.system(),
            "python": platform.python_version(),
            "installed_builder": installed,
            "fixture": observations,
            "baseline": base,
            "mode_only": normalized,
            "repeat_count_per_variant": 2,
            "only_index_modes_changed": True,
            "product_code_modified": False,
            "research_only": True,
        }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "schema": result["schema"],
        "source_sha": source_sha,
        "platform": result["platform"],
        "baseline": base["archive_sha256"],
        "mode_only": normalized["archive_sha256"],
        "modes": [(r["path"], r["mode"]) for r in base["rows"]],
        "roundtrip": "PASS",
    }, sort_keys=True))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    run(args.out)

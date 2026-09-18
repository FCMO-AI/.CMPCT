#!/usr/bin/env python3
"""Office compact-floor locality oracle.

Question: is the 5.95 MB inherited v0.25-style Office floor cheap because it
violates the current <=8x selected-member decoded-context contract?

This is deliberately a research-bound oracle, not product credit.  It builds
the accepted deterministic Office tree with the inherited EntropyGraph v0.25
engine, verifies exact reconstruction, then computes physical decoded bytes
reachable from each independently requested logical member.  Every physical
pack is charged at most once per request, but dependency files and stream slabs
are fully charged.  Metadata/open bytes are reported separately because the
release locality law is about decoded context, not archive-open metadata.
"""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


N = load(ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_neutral_office_oracle")
V025 = load(ROOT / "experiments" / "entropygraph_v025.py", "cmpct_v025_office_oracle")
EXPECTED_TREE = "aac7de772b9fae0f9791a8f2884cebb29a2ba85df9e4db21ea78482afb378a57"
EXPECTED_LOGICAL = 16_063_798
EXPECTED_FILES = 20
EXPECTED_HISTORICAL_BYTES = 5_954_026
LOCALITY_LIMIT = 8.0


def expand_files(meta: dict) -> dict[str, list]:
    fd = dict(meta["files"])
    for pi, ents in meta.get("micro", []):
        off = 0
        for path, n in ents:
            fd[path] = ["plain", [["slice", pi, off, n]], n]
            off += n
    return fd


def pack_table() -> tuple[dict, list[tuple[int, int, int, int, int, bytes]]]:
    f, meta, po = V025.open_ar()
    f.close()
    return meta, po


def refs_packs(refs: list) -> set[int]:
    return {int(r[1]) for r in refs}


def stream_packs_for(meta: dict, offset: int, length: int) -> set[int]:
    end = offset + length
    touched: set[int] = set()
    for stream_off, pi, stream_len in meta.get("stream_packs", []):
        stream_end = stream_off + stream_len
        if stream_end <= offset:
            continue
        if stream_off >= end:
            break
        touched.add(int(pi))
    return touched


def physical_packs_for(path: str, fd: dict[str, list], meta: dict, active: set[str] | None = None) -> set[int]:
    active = set() if active is None else active
    if path in active:
        raise RuntimeError(f"dependency cycle at {path}")
    active.add(path)
    d = fd[path]
    typ = d[0]
    touched: set[int] = set()
    if typ == "plain":
        touched |= refs_packs(d[1])
    elif typ == "zipstreams":
        touched |= refs_packs(d[1])
        for offset, length in d[3]:
            touched |= stream_packs_for(meta, int(offset), int(length))
    elif typ == "inflate_stream":
        touched |= stream_packs_for(meta, int(d[1]), int(d[2]))
    elif typ == "decode_file":
        touched |= physical_packs_for(str(d[1]), fd, meta, active)
    elif typ == "splice":
        touched |= refs_packs(d[1])
        for child in d[3]:
            touched |= physical_packs_for(str(child), fd, meta, active)
    else:
        raise RuntimeError(f"unknown recipe {typ!r} for {path}")
    active.remove(path)
    return touched


def logical_size(desc: list) -> int:
    typ = desc[0]
    if typ == "plain":
        return int(desc[2])
    if typ == "zipstreams":
        return int(desc[4])
    if typ == "inflate_stream":
        return int(desc[4])
    if typ == "decode_file":
        return int(desc[3])
    if typ == "splice":
        return int(desc[4])
    raise RuntimeError(typ)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="cmpct-office-v025-locality-") as td:
        work = Path(td)
        corpus_root = work / "corpus"
        N.corpus_office(corpus_root)
        office = corpus_root / "02_office_workspace"
        files = sorted(p for p in office.rglob("*") if p.is_file())
        logical = sum(p.stat().st_size for p in files)
        tree = V025.treehash(office)
        if tree != EXPECTED_TREE or logical != EXPECTED_LOGICAL or len(files) != EXPECTED_FILES:
            raise RuntimeError({"tree": tree, "logical": logical, "files": len(files)})

        V025.ROOT = office
        V025.OUT = work / "office-v025.cmpct"
        build = V025.build()
        archive_bytes = V025.OUT.stat().st_size
        verify = V025.strong_verify()
        if not verify.get("ok") or verify.get("tree_sha256") != EXPECTED_TREE:
            raise RuntimeError("v0.25 exact verification failed")
        if archive_bytes != EXPECTED_HISTORICAL_BYTES:
            raise RuntimeError(
                f"historical identity drift: {archive_bytes} != {EXPECTED_HISTORICAL_BYTES}"
            )

        meta, po = pack_table()
        fd = expand_files(meta)
        rows = []
        for path in sorted(fd):
            packs = physical_packs_for(path, fd, meta)
            decoded = sum(int(po[i][2]) for i in packs)  # po tuple: off, codec, usize, csize, crc, sha
            logical_bytes = logical_size(fd[path])
            amp = decoded / max(1, logical_bytes)
            rows.append({
                "path": path,
                "recipe": fd[path][0],
                "logical_bytes": logical_bytes,
                "decoded_physical_bytes": decoded,
                "physical_packs": sorted(packs),
                "amplification": amp,
                "within_8x": amp <= LOCALITY_LIMIT,
            })

        worst = max(rows, key=lambda r: r["amplification"])
        failing = [r for r in rows if not r["within_8x"]]
        weighted = sum(r["decoded_physical_bytes"] for r in rows) / max(
            1, sum(r["logical_bytes"] for r in rows)
        )
        result = {
            "schema": "cmpct-v030-office-v025-locality-oracle-v1",
            "claim_boundary": "research bound only; no canonical product credit",
            "office_tree_sha256": tree,
            "files": len(files),
            "logical_bytes": logical,
            "archive_bytes": archive_bytes,
            "build": build,
            "strong_verify": verify,
            "locality_limit": LOCALITY_LIMIT,
            "max_member_amplification": worst["amplification"],
            "worst_member": worst,
            "weighted_member_amplification": weighted,
            "members_over_8x": len(failing),
            "locality_verdict": "PASS" if not failing else "FAIL",
            "rows": rows,
            "decision": (
                "COMPACT_FLOOR_SURVIVES_LOCALITY_FALSIFIER"
                if not failing
                else "COMPACT_FLOOR_LOCALITY_DEBT_CONFIRMED"
            ),
        }
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

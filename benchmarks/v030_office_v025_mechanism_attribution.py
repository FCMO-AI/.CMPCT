#!/usr/bin/env python3
"""Attribute the accepted Office v0.25 compact floor by reconstruction mechanism.

Research/oracle evidence only. This does not grant r25 product credit. It answers a
narrow causal question before any porting work: which v0.25 reconstruction families
actually own Office logical bytes and physical decode units on the accepted repair-v6
identity? The result is descriptive ownership evidence, not a counterfactual byte
saving claim; a later ablation must establish marginal savings for a candidate family.
"""
from __future__ import annotations

import importlib.util
import json
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TREE = "aac7de772b9fae0f9791a8f2884cebb29a2ba85df9e4db21ea78482afb378a57"
EXPECTED_LOGICAL = 16_063_798
EXPECTED_FILES = 20


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


N = load(ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_office_attr_corpus")
REPAIR = load(ROOT / "benchmarks" / "neutral_hostile_determinism_repair_v6.py", "cmpct_office_attr_repair")
V025 = load(ROOT / "experiments" / "entropygraph_v025.py", "cmpct_office_attr_v025")


def expand_files(meta):
    fd = dict(meta["files"])
    for pi, ents in meta.get("micro", []):
        off = 0
        for path, n in ents:
            fd[path] = ["plain", [["slice", pi, off, n]], n]
            off += n
    return fd


def refs_packs(refs):
    return {int(r[1]) for r in refs}


def stream_packs_for(meta, offset, length):
    end = offset + length
    touched = set()
    for stream_off, pi, stream_len in meta.get("stream_packs", []):
        stream_end = stream_off + stream_len
        if stream_end <= offset:
            continue
        if stream_off >= end:
            break
        touched.add(int(pi))
    return touched


def physical_packs_for(path, fd, meta, active=None):
    active = set() if active is None else active
    if path in active:
        raise RuntimeError(f"dependency cycle at {path}")
    active.add(path)
    d = fd[path]
    typ = d[0]
    touched = set()
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


def logical_size(d):
    if d[0] == "plain":
        return int(d[2])
    if d[0] in {"zipstreams", "inflate_stream", "splice"}:
        return int(d[4])
    if d[0] == "decode_file":
        return int(d[3])
    raise RuntimeError(d[0])


def main():
    with tempfile.TemporaryDirectory(prefix="cmpct-office-v025-attribution-") as td:
        work = Path(td)
        corpus_root = work / "corpus"
        REPAIR.install_generation_hooks(N)
        N.corpus_office(corpus_root)
        office = corpus_root / "02_office_workspace"
        REPAIR.normalize_workload(office)
        files = sorted(p for p in office.rglob("*") if p.is_file())
        logical = sum(p.stat().st_size for p in files)
        tree = V025.treehash(office)
        if (tree, logical, len(files)) != (EXPECTED_TREE, EXPECTED_LOGICAL, EXPECTED_FILES):
            raise RuntimeError({"tree": tree, "logical": logical, "files": len(files)})

        V025.ROOT = office
        V025.OUT = work / "office-v025.cmpct"
        build = V025.build()
        archive_bytes = V025.OUT.stat().st_size
        verify = V025.strong_verify()
        if not verify.get("ok") or verify.get("tree_sha256") != EXPECTED_TREE:
            raise RuntimeError("exact verification failed")

        f, meta, po = V025.open_ar()
        f.close()
        fd = expand_files(meta)
        recipe_counts = Counter()
        recipe_logical = Counter()
        recipe_pack_refs = defaultdict(set)
        pack_users = defaultdict(set)
        rows = []
        for path in sorted(fd):
            d = fd[path]
            typ = str(d[0])
            lb = logical_size(d)
            packs = physical_packs_for(path, fd, meta)
            decoded = sum(int(po[i][2]) for i in packs)
            recipe_counts[typ] += 1
            recipe_logical[typ] += lb
            recipe_pack_refs[typ] |= packs
            for pi in packs:
                pack_users[pi].add(typ)
            rows.append({
                "path": path,
                "recipe": typ,
                "logical_bytes": lb,
                "decoded_physical_bytes": decoded,
                "physical_packs": sorted(packs),
                "amplification": decoded / max(1, lb),
            })

        # Decoded-byte ownership deliberately ignores compressed payload size. It tells us
        # which bounded decode units a mechanism depends on; it does not pretend those
        # units disappear if the mechanism is removed. Marginal archive savings require
        # a separately built counterfactual.
        pack_decoded = {i: int(row[2]) for i, row in enumerate(po)}
        exclusive = Counter()
        shared = 0
        for pi, users in pack_users.items():
            if len(users) == 1:
                exclusive[next(iter(users))] += pack_decoded[pi]
            else:
                shared += pack_decoded[pi]

        mechanisms = {}
        for typ in sorted(recipe_counts):
            union = recipe_pack_refs[typ]
            mechanisms[typ] = {
                "files": recipe_counts[typ],
                "logical_bytes": recipe_logical[typ],
                "logical_fraction": recipe_logical[typ] / logical,
                "reachable_unique_decoded_bytes": sum(pack_decoded[i] for i in union),
                "exclusive_decoded_bytes": exclusive[typ],
                "physical_pack_count": len(union),
            }

        dominant = max(mechanisms, key=lambda k: mechanisms[k]["logical_bytes"])
        result = {
            "schema": "cmpct-v030-office-v025-mechanism-attribution-v1",
            "claim_boundary": "research ownership evidence only; not marginal savings and not canonical r25 credit",
            "substrate": "neutral-hostile-determinism-repair-v6",
            "office_tree_sha256": tree,
            "files": len(files),
            "logical_bytes": logical,
            "archive_bytes": archive_bytes,
            "build": build,
            "strong_verify": verify,
            "mechanisms": mechanisms,
            "shared_cross_recipe_decoded_bytes": shared,
            "dominant_logical_owner": dominant,
            "rows": rows,
            "decision": "ATTRIBUTION_COMPLETE_ABLATION_REQUIRED_FOR_CAUSAL_SAVINGS",
        }
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

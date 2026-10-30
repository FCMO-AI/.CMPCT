#!/usr/bin/env python3
"""J24G85 detached r24 wire referee: imports no CMPCT product package."""
from __future__ import annotations
import copy
import hashlib
import json
import msgpack
from pathlib import Path
import sys

from j24g80_wire_referee import F, B, H, parse, blobs_validate, sha, delete
from j24g80_wire_referee import choose

EXTERNAL = {17: ["ren", "f00001.dat", "external-f00001.dat"],
            44: ["ren", "f00002.dat", "external-f00002.dat"]}


def rename(index, old, new):
    rows = index["files"]
    originals = [row[0] for row in rows]
    assert old in originals and new not in originals
    sparse = index.get("fsmeta", {})
    mapping = {}
    for key in ("owner_overrides", "xattrs"):
        if key in sparse:
            mapping[key] = {originals[x[0]]: x[1:] for x in sparse[key]}
            assert len(mapping[key]) == len(sparse[key])
    for row in rows:
        if row[0] == old:
            row[0] = new
            break
    rows.sort(key=lambda r: r[0])
    for key, old_by_name in mapping.items():
        if old in old_by_name:
            old_by_name[new] = old_by_name.pop(old)
        sparse[key] = [[i, *old_by_name[row[0]]] for i, row in enumerate(rows)
                       if row[0] in old_by_name]


def events(n, where):
    names = choose(n, where)
    assert len(names) == 64
    all_ops = []
    for i, name in enumerate(names, 1):
        all_ops.append(["del", name])
        if i in EXTERNAL:
            all_ops.append(EXTERNAL[i])
    assert len(all_ops) == 66
    return all_ops


def audit(raw, case, row):
    n = int(case.split("-")[0])
    where = case.split("-")[1]
    initial, chain, bad, record_base, span = parse(raw)
    assert not bad and len(chain) == 67
    assert chain[0][1] == 0 and chain[64][1] == 0
    assert all(x[1] == 1 for x in chain[1:64] + chain[65:])
    blobs = blobs_validate(raw, initial, record_base, span, n)
    assert len(row["physical"]) == 66
    idx = copy.deepcopy(initial)
    for i, op in enumerate(events(n, where), 1):
        position, kind, predecessor, payload = chain[i]
        assert predecessor == chain[i-1][0]
        assert i == 64 if kind == 0 else i != 64
        if op[0] == "del":
            delete(idx, op[1])
        else:
            rename(idx, op[1], op[2])
        if i == 64:
            assert payload == idx, "complete authenticated checkpoint mismatch"
        else:
            assert payload == {"blobs": [], "ops": [op]}, "delta mismatched"
        physical = row["physical"][i-1]
        prefix = raw[:position + F.size]
        assert physical["sha256"] == sha(prefix).hex()
        assert physical["bytes"] == len(prefix)
        assert physical["operation"] == (
            "external_rename" if op[0] == "ren" else "del")
    assert len(idx["files"]) == n - 64
    assert row["final_index_sha256"] == sha(
        msgpack.packb(idx, use_bin_type=True)).hex()
    assert raw == raw[:chain[-1][0] + F.size]
    return dict(case=case, variant=row["variant"], recorded_generations=66,
                authenticated_footers=67, member_blobs_verified=blobs,
                physical_sha_prefixes=66, final_index_independent=True,
                final_bytes=len(raw), final_sha256=sha(raw).hex())


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "evidence")
    result = json.loads((out/"j24g85-result.json").read_text())
    assert result["status"] == "COMPLETE"
    decisions = []
    adversarial = 0
    for case in ("8192-middle", "32768-tail"):
        data = result["cases"][case]
        assert data["status"] == "COMPLETE"
        refs = {row["variant"]: row for row in data["rows"] if row["replicate"] == 0}
        raws = {}
        for variant in ("public", "cached"):
            valid = out/f"j24g85-{case}-{variant}-valid.cmpct"
            corrupt = out/f"j24g85-{case}-{variant}-corrupt-tail.cmpct"
            raw = valid.read_bytes()
            raws[variant] = raw
            decisions.append(audit(raw, case, refs[variant]))
            damaged = corrupt.read_bytes()
            assert damaged[:-1] == raw[:-1] and damaged[-1] != raw[-1]
            _, prior, is_corrupt, _, _ = parse(damaged, True)
            assert is_corrupt and len(prior) == 66
        assert raws["public"] == raws["cached"]
        # Three differently rooted negatives on the source-exact candidate.
        raw = raws["cached"]
        forged = copy.deepcopy(refs["cached"])
        forged["physical"][0]["sha256"] = "0"*64
        try:
            audit(raw, case, forged)
        except (AssertionError, ValueError, IndexError, KeyError):
            adversarial += 1
        else:
            raise AssertionError("forged intermediate physical witness accepted")
        for offset in (len(raw)-1, H.size+4):
            tampered = bytearray(raw)
            tampered[offset] ^= 0x53
            try:
                audit(bytes(tampered), case, refs["cached"])
            except (AssertionError, ValueError, IndexError, KeyError, RuntimeError):
                adversarial += 1
            else:
                raise AssertionError("tampered physical archive accepted")
    assert adversarial == 6
    print(json.dumps(dict(schema="j24g85-detached-wire-v1",
                          decision="EXACT_INTERLEAVED_REVALIDATION_WIRE_PASS",
                          results=decisions, adversarial_rejections=adversarial),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

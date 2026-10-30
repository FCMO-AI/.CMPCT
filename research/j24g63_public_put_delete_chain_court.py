#!/usr/bin/env python3
"""J24G63 research-only physical court: public one-op put/delete histories.

Changes no product source. Pinned inherited J24G60 probe excludes startup/import.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

import msgpack
import zstandard as zstd
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct import transactions as tx
from cmpct.validation import preflight_archive
import j24g60_single_delta_chain_court as parent

SIZES = (512, 2048)
DEPTHS = (1, 16, 32, 63)
KINDS = ("put", "delete")
BLOCKS = 4
EXPECTED_PARENT = "fb5d96cdb8855fe3e01868792e65b79d3d61661d"
PREREG = "aa550b7a928dc9a34d363665713379004e331270"
AMENDMENT = "0c3511f8d2f0b8dc02e4d37992919849c069bdf3"


def content(tag: str, i: int) -> bytes:
    return hashlib.sha256(f"cmpct-j24g63-{tag}-{i}".encode()).digest() * 2


def target_names(kind: str, n: int) -> list[str]:
    """Prospectively spread owner paths over the full initial sorted namespace."""
    total = n if kind == "put" else n + 63
    result = [f"f{((2*i + 1)*total)//126:04d}.dat" for i in range(63)]
    assert len(set(result)) == 63 and all(int(x[1:5]) < total for x in result)
    return result


def signed_ledger(path: Path, expected_kind: str, depth: int, names: list[str]) -> list[dict]:
    """Separate MessagePack/Zstd footer decoding, do not import Reader's parser."""
    with CMPCT(path) as ar:
        pos = int(ar.latest_footer_pos)
    out, seen = [], set()
    size = path.stat().st_size
    with path.open("rb") as handle:
        while pos:
            assert pos not in seen and 0 < pos and pos + parent.FOOTER.size <= size
            seen.add(pos)
            handle.seek(pos)
            raw_footer = handle.read(parent.FOOTER.size)
            magic, kind, codec, flags, reserved, comp_len, plain_len, prev, digest = (
                parent.FOOTER.unpack(raw_footer))
            assert magic == parent.FMAGIC and kind in (0, 1) and codec in (0, 1)
            assert flags == reserved == 0 and comp_len > 0 and plain_len > 0
            assert pos >= comp_len and (prev == 0 or prev < pos)
            handle.seek(pos - comp_len)
            encoded = handle.read(comp_len)
            assert len(encoded) == comp_len
            plain = (encoded if codec == 0 else
                     zstd.ZstdDecompressor().decompress(encoded, max_output_size=plain_len))
            assert len(plain) == plain_len
            assert hashlib.sha256(plain).digest() == digest
            decoded = msgpack.unpackb(plain, raw=False)
            if kind == 0:
                assert isinstance(decoded, dict) and "files" in decoded
                break
            assert isinstance(decoded, dict) and isinstance(decoded.get("ops"), list)
            assert len(decoded["ops"]) == 1
            op = decoded["ops"][0]
            assert isinstance(op, list) and len(op) >= 2
            assert op[0] == ("put" if expected_kind == "put" else "del"), op
            name = op[1][0] if expected_kind == "put" else op[1]
            assert isinstance(name, str) and name.startswith("f") and name.endswith(".dat")
            if expected_kind == "put":
                assert len(op) == 2 and isinstance(op[1], list)
            else:
                assert len(op) == 2
            out.append({"tag": op[0], "name": name, "pos": pos, "previous_pos": prev,
                        "payload_sha256": digest.hex(), "stored_payload_bytes": comp_len})
            pos = prev
    assert len(out) == depth, (len(out), depth)
    expected_names = list(reversed(names[:depth]))
    assert [x["name"] for x in out] == expected_names
    return out


def verify_pair(chain: Path, checkpoint: Path, expected_rows: int, depth: int) -> dict:
    with CMPCT(chain) as current, CMPCT(checkpoint) as snapshot:
        assert current.index == snapshot.index
        assert current.delta_depth == depth and snapshot.delta_depth == 0
        assert len(current.files) == len(snapshot.files) == expected_rows
        assert current.verify() == snapshot.verify() == expected_rows
        assert current.by.keys() == snapshot.by.keys()
        digest = hashlib.sha256(msgpack.packb(current.index, use_bin_type=True)).hexdigest()
        # Full contents are checked by verify(); ensure direct exact read equivalence too.
        selected = list(sorted(current.by))
        for name in selected[:3] + selected[-3:]:
            assert current.read(name) == snapshot.read(name)
    pre_chain = preflight_archive(chain)
    pre_ckpt = preflight_archive(checkpoint)
    assert pre_chain["files"] == pre_ckpt["files"] == expected_rows
    assert pre_chain["delta_depth"] == depth and pre_ckpt["delta_depth"] == 0
    return {"effective_index_sha256": digest, "verified_members": expected_rows,
            "chain_preflight": pre_chain, "checkpoint_preflight": pre_ckpt}


def build_kind(kind: str, n: int, stage: Path, evidence: Path) -> dict:
    total = n if kind == "put" else n + 63
    source = stage / f"source-{kind}-{n}"
    source.mkdir()
    for i in range(total):
        (source / f"f{i:04d}.dat").write_bytes(content("base", i))
    archive = stage / f"{kind}-{n}-live.cmpct"
    started = time.perf_counter()
    Builder(source, workers=1, reproducible=True).build(archive)
    update_dir = stage / f"updates-{kind}-{n}"
    update_dir.mkdir()
    names = target_names(kind, n)
    snaps = {}
    for i in range(63):
        target = names[i]
        if kind == "put":
            updated = update_dir / f"updated-{i:04d}.dat"
            updated.write_bytes(content("updated", i))
            result = tx.append_update(archive, target, updated)
            assert result["member"] == target
        else:
            tx.append_delete(archive, target)
        depth = i + 1
        if depth not in DEPTHS:
            continue
        chain = stage / f"{kind}-{n}-d{depth:02d}-chain.cmpct"
        checkpoint = stage / f"{kind}-{n}-d{depth:02d}-checkpoint.cmpct"
        shutil.copyfile(archive, chain)
        shutil.copyfile(archive, checkpoint)
        with CMPCT(chain) as ar:
            index = msgpack.unpackb(msgpack.packb(ar.index, use_bin_type=True), raw=False)
            previous = ar.latest_footer_pos
        tx._append_generation(checkpoint, {"blobs": [], "ops": []}, previous,
                              checkpoint_index=index)
        expected = n if kind == "put" else n + 63 - depth
        semantics = verify_pair(chain, checkpoint, expected, depth)
        ledger = signed_ledger(chain, kind, depth, names)
        assert len(parent.footer_chain(chain)) == depth + 1
        assert len(parent.footer_chain(checkpoint)) == 1
        snapshots = {
            "kind": kind, "n": n, "depth": depth, "expected_rows": expected,
            "selected_paths": names[:depth], "semantics": semantics, "wire": ledger,
            "paths": {"chain": str(chain), "checkpoint": str(checkpoint)},
            "archive_bytes": {"chain": chain.stat().st_size,
                              "checkpoint": checkpoint.stat().st_size},
            "archive_sha256": {"chain": parent.sha256_file(chain),
                               "checkpoint": parent.sha256_file(checkpoint)},
            "checkpoint_premium_bytes": checkpoint.stat().st_size - chain.stat().st_size,
        }
        if n == 2048 and depth == 63:
            physical = {}
            for flavor, path in (("chain", chain), ("checkpoint", checkpoint)):
                destination = evidence / "physical" / f"j24g63-{kind}-n{n}-{flavor}.cmpct"
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)
                assert parent.sha256_file(destination) == snapshots["archive_sha256"][flavor]
                physical[flavor] = str(destination.relative_to(evidence))
            snapshots["saved_physical"] = physical
        snaps[str(depth)] = snapshots
    assert set(snaps) == {str(d) for d in DEPTHS}
    return {"n": n, "kind": kind, "base_members": total,
            "setup_wall_s": time.perf_counter() - started,
            "snapshots": snaps}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    assert subprocess.run(["git", "merge-base", "--is-ancestor", EXPECTED_PARENT, "HEAD"],
                          cwd=root).returncode == 0
    assert subprocess.run(["git", "merge-base", "--is-ancestor", PREREG, "HEAD"],
                          cwd=root).returncode == 0
    assert subprocess.run(["git", "merge-base", "--is-ancestor", AMENDMENT, "HEAD"],
                          cwd=root).returncode == 0
    identity = parent.verify_source()
    output = Path(os.environ.get("J24G63_RESULT", "evidence/j24g63-result.json"))
    evidence = output.parent
    evidence.mkdir(parents=True, exist_ok=True)
    reference_probe = Path(parent.__file__).resolve()
    env = dict(os.environ)
    report = {"claim_scope": "research-only public Writer put/delete vs exact-state private checkpoint",
              "source": identity, "platform": platform.platform(),
              "python": platform.python_version(), "corpus": {}, "samples": [],
              "decisions": {}, "limits": [
                  "case classes have different starting filesystem sizes",
                  "private same-state checkpoint not a public Writer checkpoint at depth <64",
                  "archive bytes and update payloads charged; no shipping byte win",
                  "fresh child process imports outside timer; not physical cold disk",
                  "no xattrs/hardlinks/recovery/portable RSS/ZIP/Zstd or full-product credit"]}
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g63-") as td:
        stage = Path(td)
        for kind in KINDS:
            report["corpus"][kind] = {}
            for n in SIZES:
                report["corpus"][kind][str(n)] = build_kind(kind, n, stage, evidence)
        for kind in KINDS:
            for n in SIZES:
                for depth in DEPTHS:
                    snap = report["corpus"][kind][str(n)]["snapshots"][str(depth)]
                    for block in range(BLOCKS):
                        sequence = (("chain", "checkpoint", "checkpoint", "chain")
                                    if block % 2 == 0 else
                                    ("checkpoint", "chain", "chain", "checkpoint"))
                        for position, variant in enumerate(sequence):
                            reading = parent.timed_fresh_process(
                                reference_probe, Path(snap["paths"][variant]), env)
                            assert reading["rows"] == snap["expected_rows"]
                            assert reading["delta_depth"] == (depth if variant == "chain" else 0)
                            report["samples"].append(
                                {"kind": kind, "n": n, "depth": depth, "block": block,
                                 "position": position, "variant": variant, **reading})
                    observations = [x for x in report["samples"] if x["kind"] == kind
                                    and x["n"] == n and x["depth"] == depth]
                    a = [x for x in observations if x["variant"] == "chain"]
                    b = [x for x in observations if x["variant"] == "checkpoint"]
                    assert len(a) == len(b) == 8
                    aw = statistics.median(x["open_wall_ns"] for x in a)
                    bw = statistics.median(x["open_wall_ns"] for x in b)
                    snap["measurements"] = {
                        "chain_wall_ns_median": aw, "checkpoint_wall_ns_median": bw,
                        "delta_wall_ns": aw - bw, "delta_fraction_of_chain": (aw - bw) / aw,
                        "chain_cpu_ns_median": statistics.median(x["open_cpu_ns"] for x in a),
                        "checkpoint_cpu_ns_median": statistics.median(x["open_cpu_ns"] for x in b),
                        "chain_to_checkpoint_wall_ratio": aw / bw if bw else None,
                    }
        assert len(report["samples"]) == len(KINDS) * len(SIZES) * len(DEPTHS) * BLOCKS * 4
        for kind in KINDS:
            primary = report["corpus"][kind]["2048"]["snapshots"]["63"]["measurements"]
            threshold = {"required_absolute_ms": 3.0,
                         "required_fraction_of_chain": 0.10,
                         "observed_absolute_ms": primary["delta_wall_ns"] / 1e6,
                         "observed_fraction_of_chain": primary["delta_fraction_of_chain"]}
            report["decisions"][kind] = {
                "decision": ("MATERIAL" if primary["delta_wall_ns"] >= 3_000_000
                             and primary["delta_fraction_of_chain"] >= 0.10
                             else "NOT_MATERIAL"), "threshold": threshold}
    # Self-consistency digest binds *all* raw observations, not just median ranks.
    report["raw_samples_sha256"] = hashlib.sha256(json.dumps(
        report["samples"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("J24G63_HEAD", identity["head"])
    for kind in KINDS:
        print("J24G63_" + kind.upper(), json.dumps(report["decisions"][kind], sort_keys=True))
    print("J24G63_OBSERVATIONS", len(report["samples"]))
    print("J24G63_RESULT_SHA256", parent.sha256_file(output))
    print("J24G63_OUTPUT", output)


if __name__ == "__main__":
    main()

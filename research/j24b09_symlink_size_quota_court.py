#!/usr/bin/env python3
"""J24B09: prospective, research-only signed K_SYMLINK nonnegative quota test.

No product source changes. All deliberately malformed archives remain in a temp root
until original binary evidence is copied into the requested artifact directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

import msgpack

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import HDR, FTR, MAGIC, FMAGIC, VERSION, K_SYMLINK, sha, zc, zd

PARENT = "adcf38cb5be022567c1faf6538aefeef2f6b72de"
READER_BLOB = "20f6e257a07a61a4c1aebe23ae23e4109d6c41c8"
FILE = "payload.bin"
LINK = "offset-link"
TARGET = FILE
SIZE = 8192


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def demand(ok: bool, why: str) -> None:
    if not ok:
        raise AssertionError(why)


def custody() -> dict:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    declared = os.environ.get("J24B09_HEAD")
    if declared:
        demand(head == declared, "synthetic checkout or wrong experiment HEAD")
    candidate = subprocess.check_output(["git", "show", f"{PARENT}:src/cmpct/reader.py"])
    hash_blob = subprocess.check_output(
        ["git", "hash-object", "--stdin"], input=candidate
    ).decode().strip()
    demand(hash_blob == READER_BLOB, "source base Reader blob changed")
    from cmpct import reader as installed_reader
    installed = Path(installed_reader.__file__).read_bytes()
    demand(installed == candidate, "installed Reader != pinned #690 source")
    return {"head": head, "parent": PARENT, "reader_blob": hash_blob,
            "installed_reader_sha256": digest(installed)}


def mutated(original: bytes, size: int) -> bytes:
    magic, version, flags, cs, us, ds, old_sha = HDR.unpack_from(original)
    demand(magic == MAGIC and version == VERSION, "not revision 24")
    base = HDR.size + cs
    raw_index = zd(original[HDR.size:base], us)
    demand(sha(raw_index) == old_sha, "bad original primary SHA")
    index = msgpack.unpackb(raw_index, raw=False)
    targets = [r for r in index["files"] if r[0] == LINK]
    demand(len(targets) == 1 and targets[0][1] == K_SYMLINK,
           "need exactly one K_SYMLINK")
    demand(targets[0][4] == len(TARGET.encode()), "unexpected original size")
    targets[0][4] = size
    encoded = msgpack.packb(index, use_bin_type=True)
    comp = zc(encoded, 12)
    physical = original[base:base + ds]
    demand(len(physical) == ds and base + ds + cs + FTR.size == len(original),
           "original archive not a single generation of specified geometry")
    header = HDR.pack(MAGIC, VERSION, flags, len(comp), len(encoded), ds, sha(encoded))
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(comp), len(encoded), 0, sha(encoded))
    return header + comp + physical + comp + footer


def inspect(archive: Path, output: Path, cap: int | None, payload: bytes) -> dict:
    result = {"cap": cap, "exception": None, "verified": None, "read_link": None,
              "read_file_sha256": None, "published": False, "file_bytes": 0,
              "file_sha256": None, "link_target": None, "destination_exists": False}
    with CMPCT(archive) as reader:
        result["verified"] = reader.verify()
        result["read_link"] = reader.read(LINK).decode("utf-8", "strict")
        result["read_file_sha256"] = digest(reader.read(FILE))
        try:
            reader.extractall(output, max_bytes=cap, metadata=False, safe_symlinks=True)
        except Exception as exc:
            result["exception"] = f"{type(exc).__name__}: {exc}"
    result["destination_exists"] = output.exists()
    src = output / FILE
    dst = output / LINK
    if src.exists():
        observed = src.read_bytes()
        result["published"] = True
        result["file_bytes"] = len(observed)
        result["file_sha256"] = digest(observed)
    if dst.is_symlink():
        result["link_target"] = os.readlink(dst)
    demand(result["verified"] == 2, "signed index lost actual Reader verify exactness")
    demand(result["read_link"] == TARGET, "target physical bytes changed")
    demand(result["read_file_sha256"] == digest(payload), "payload physical bytes changed")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.time()
    source = custody()

    with tempfile.TemporaryDirectory(prefix="j24b09_") as tmp:
        t = Path(tmp)
        root = t / "tree"
        root.mkdir()
        payload = b"".join(
            hashlib.sha256(f"J24B09:{i}".encode()).digest()
            for i in range(SIZE // 32)
        )
        demand(len(payload) == SIZE, "payload geometry")
        (root / FILE).write_bytes(payload)
        os.symlink(TARGET, root / LINK)
        base = t / "baseline.cmpct"
        Builder(root, workers=1, reproducible=True).build(base)
        original = base.read_bytes()
        zero = t / "zero.cmpct"
        zero.write_bytes(mutated(original, 0))
        one = t / "one.cmpct"
        one.write_bytes(mutated(original, 1))

        cases = [
            ("honest_low", base, SIZE),
            ("honest_full", base, SIZE + len(TARGET.encode())),
            ("zero_cap_8192", zero, SIZE),
            ("one_cap_8193", one, SIZE + 1),
            ("zero_too_low", zero, SIZE - 1),
            ("zero_unlimited", zero, None),
        ]
        results = {}
        for name, archive, budget in cases:
            results[name] = inspect(archive, t / ("out_" + name), budget, payload)
        def accepted(name: str) -> bool:
            r = results[name]
            return (r["exception"] is None and r["file_bytes"] == SIZE
                    and r["file_sha256"] == digest(payload)
                    and r["link_target"] == TARGET)
        def rejected_clean(name: str) -> bool:
            r = results[name]
            return (r["exception"] is not None and not r["destination_exists"]
                    and not r["published"] and r["link_target"] is None)

        demand(rejected_clean("honest_low"), "legitimate undercap must reject before dest")
        demand(accepted("honest_full"), "full legitimate cap must accept")
        demand(rejected_clean("zero_too_low"), "insufficient file bytes must still reject")
        demand(accepted("zero_unlimited"), "nonnegative mutant should remain readable without cap")
        found = accepted("zero_cap_8192") and accepted("one_cap_8193")
        refused = rejected_clean("zero_cap_8192") and rejected_clean("one_cap_8193")
        demand(found or refused, "ambiguous/partial acceptance; no scientific decision")
        decision = ("CONFIRMED_NONNEGATIVE_SYMLINK_QUOTA_UNDERCOUNT" if found
                    else "FALSIFIED_BY_VALIDATION")
        artifacts = {}
        for label, path in [("baseline", base), ("zero", zero), ("one", one)]:
            dest = args.artifact_dir / (label + ".cmpct")
            shutil.copyfile(path, dest)
            artifacts[label] = {"bytes": dest.stat().st_size,
                                "sha256": digest(dest.read_bytes())}
        source_file = args.artifact_dir / "source-payload.bin"
        source_file.write_bytes(payload)
        receipt = {
            "schema": "j24b09-signed-symlink-v1",
            "scientific_decision": decision,
            "product_promotion": False,
            "started_epoch_s": stamp,
            "source": source,
            "source_payload_sha256": digest(payload),
            "source_payload_bytes": SIZE,
            "symlink_target": TARGET,
            "true_symlink_bytes": len(TARGET.encode()),
            "declared_symlink_lengths": {"baseline": len(TARGET.encode()),
                                         "zero": 0, "one": 1},
            "archives": artifacts,
            "results": results,
            "limits": "Research-only K_SYMLINK signed-size mismatch; #690 candidate; no Windows claim",
        }
        (args.artifact_dir / "receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps({"decision": decision, "source": source, "results": results},
                         indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

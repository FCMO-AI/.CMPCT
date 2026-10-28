#!/usr/bin/env python3
"""J24B06: source-locked signed negative-size cancellation court (research only).

Deliberately malicious, fully signed archive index. Do not use outside an
isolated temporary directory. The production Reader and Builder are unchanged.
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
from cmpct.codec import (
    HDR, FTR, FMAGIC, MAGIC, VERSION, K_SYMLINK,
    sha, zc, zd,
)

PAYLOAD_SIZE = 8192
LIMIT = 4096
LINK = "offset-link"
FILE = "payload.bin"
SOURCE_SHA = "80c358f8824ec1b20d349c92ed94c898090969b0"
READER_GIT_BLOB = "e716233403dabd0966863c45635e18fa5ac6afb8"


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def require(pred: bool, message: str) -> None:
    if not pred:
        raise AssertionError(message)


def snapshot_git() -> dict:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    reader = subprocess.check_output(["git", "show", "HEAD:src/cmpct/reader.py"])
    require(subprocess.check_output(["git", "hash-object", "src/cmpct/reader.py"], text=True).strip()
            == READER_GIT_BLOB, "Reader source no longer matches frozen main blob")
    import cmpct.reader as installed_reader
    installed = Path(installed_reader.__file__).read_bytes()
    require(reader == installed, "installed Reader differs from exact Git checkout")
    return {"git_head": head, "frozen_main": SOURCE_SHA,
            "reader_blob": READER_GIT_BLOB, "reader_raw_sha256": digest(reader),
            "installed_reader_sha256": digest(installed)}


def source_payload() -> bytes:
    # Not fixture-identity policy: predictable nontrivial bytes prove exactness.
    return b"".join(hashlib.sha256(f"j24b06:{i}".encode()).digest()
                    for i in range(PAYLOAD_SIZE // 32))


def signed_reindex(original: bytes, new_link_size: int) -> bytes:
    m, v, flags, cs, us, data_span, header_sha = HDR.unpack_from(original)
    require(m == MAGIC and v == VERSION, "source is not genuine r24")
    base = HDR.size + cs
    old_index = zd(original[HDR.size:base], us)
    require(sha(old_index) == header_sha, "original primary index SHA mismatch")
    index = msgpack.unpackb(old_index, raw=False)
    target_rows = [row for row in index["files"] if row[0] == LINK]
    require(len(target_rows) == 1 and target_rows[0][1] == K_SYMLINK,
            "exactly one symlink row is required")
    require(target_rows[0][4] == len(FILE.encode()), "original symlink length unexpected")
    target_rows[0][4] = new_link_size
    new_index = msgpack.packb(index, use_bin_type=True)
    compressed = zc(new_index, 12)
    index_sha = sha(new_index)
    physical = original[base:base + data_span]
    require(base + data_span <= len(original) - FTR.size, "physical span truncated")
    header = HDR.pack(MAGIC, VERSION, flags, len(compressed),
                      len(new_index), len(physical), index_sha)
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed),
                      len(new_index), 0, index_sha)
    return header + compressed + physical + compressed + footer


def run_extract(archive: Path, destination: Path, budget: int) -> dict:
    result = {"budget": budget, "exception_type": None, "exception": None,
              "verify_count": None, "file_written": False, "file_bytes": 0,
              "file_sha256": None, "symlink_created": False}
    with CMPCT(archive) as ar:
        result["verify_count"] = ar.verify()
        try:
            ar.extractall(destination, metadata=False,
                          max_bytes=budget, safe_symlinks=True)
        except Exception as exc:
            result["exception_type"] = type(exc).__name__
            result["exception"] = str(exc)
    output_file = destination / FILE
    if output_file.exists():
        raw = output_file.read_bytes()
        result.update(file_written=True, file_bytes=len(raw), file_sha256=digest(raw))
    link = destination / LINK
    result["symlink_created"] = link.is_symlink()
    if result["symlink_created"]:
        require(os.readlink(link) == FILE, "unexpected or unsafe symlink target")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    custody = snapshot_git()
    if os.environ.get("J24B06_HEAD"):
        require(custody["git_head"] == os.environ["J24B06_HEAD"],
                "workflow checkout is not exact PR HEAD")

    with tempfile.TemporaryDirectory(prefix="cmpct-j24b06-") as tmp:
        td = Path(tmp)
        root = td / "source"
        root.mkdir()
        raw = source_payload()
        (root / FILE).write_bytes(raw)
        os.symlink(FILE, root / LINK)
        original = td / "baseline.cmpct"
        Builder(root, workers=1, reproducible=True).build(original)
        require(original.stat().st_size > 0, "Builder produced empty archive")
        original_bytes = original.read_bytes()

        poisoned = td / "negative.cmpct"
        poisoned.write_bytes(signed_reindex(original_bytes, -PAYLOAD_SIZE))
        zero = td / "zero.cmpct"
        zero.write_bytes(signed_reindex(original_bytes, 0))

        results = {}
        for label, arc, budget in [
            ("baseline_budget", original, LIMIT),
            ("negative_budget", poisoned, LIMIT),
            ("zero_budget", zero, LIMIT),
            ("negative_budget_minus_one", poisoned, -1),
        ]:
            results[label] = run_extract(arc, td / ("out-" + label), budget)
            require(results[label]["verify_count"] == 2,
                    f"{label}: published verify() rejected the signed test archive")
        require(results["baseline_budget"]["exception_type"] is not None
                and not results["baseline_budget"]["file_written"],
                "valid base should refuse an insufficient extraction budget")
        require(results["zero_budget"]["exception_type"] is not None
                and not results["zero_budget"]["file_written"],
                "zero-size control unexpectedly bypassed budget")
        require(results["negative_budget_minus_one"]["exception_type"] is not None,
                "negative budget control unexpectedly succeeded")
        positive = results["negative_budget"]
        if positive["file_written"] and positive["file_bytes"] == PAYLOAD_SIZE:
            require(positive["file_sha256"] == digest(raw), "wrong payload after apparent bypass")
            require(positive["symlink_created"], "unrelated extraction failure left only payload")
            decision = "CONFIRMED_SIGNED_BUDGET_UNDERCOUNT"
        else:
            require(not positive["file_written"],
                    "partially published payload invalidates clean decision")
            require(positive["exception_type"] is not None,
                    "archive neither published nor cleanly rejected")
            decision = "HYPOTHESIS_FALSIFIED_BY_READER_REFUSAL"
        require(not any(p.is_symlink() for p in td.iterdir()),
                "court unexpectedly created top-level symlink")
        files = {}
        for label, path in [
            ("baseline", original), ("negative", poisoned), ("zero", zero)
        ]:
            out = args.artifact_dir / (label + ".cmpct")
            shutil.copyfile(path, out)
            files[label] = {"sha256": digest(out.read_bytes()), "bytes": out.stat().st_size}
        (args.artifact_dir / "source-payload.bin").write_bytes(raw)
        receipt = {
            "schema": "j24b06-signed-budget-v1", "decision": decision,
            "custody": custody, "created_utc_epoch_s": started,
            "source_payload_sha256": digest(raw), "source_payload_bytes": len(raw),
            "source_symlink_target": FILE, "max_bytes_tested": LIMIT,
            "poisoned_symlink_declared_size": -PAYLOAD_SIZE,
            "files": files, "results": results,
            "evidence_scope": "installed published v0.30.0/r24 Reader/Builder on signed hostile metadata",
            "promotion": False,
        }
        (args.artifact_dir / "receipt.json").write_text(
            json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"decision": decision, "results": results,
                          "archive_sha256": files, "custody": custody},
                         sort_keys=True, indent=2))


if __name__ == "__main__":
    main()

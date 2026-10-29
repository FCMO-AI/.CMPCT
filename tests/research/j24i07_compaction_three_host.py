"""J24I07 source-installed three-host portability falsifier for J24I06 compaction.

This deliberately tests portable invariants without assuming Linux-only xattr APIs.
Unsupported symlink or hardlink facilities fail explicitly; they are not counted as pass.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import sys
import tempfile
import time
from pathlib import Path

import cmpct
from cmpct.builder import Builder
from cmpct.codec import BHDR, K_DIR, K_HARDLINK
from cmpct.reader import CMPCT
from cmpct.transactions import _compaction_source_metadata, compact_archive


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observed(path: Path) -> dict:
    with CMPCT(path) as reader:
        rows = list(reader.files)
        metadata = _compaction_source_metadata(reader)
        digests = {r[0]: reader.file_sha256(r[0]) for r in rows if r[1] != K_DIR}
        verified = reader.verify()
        return {"rows": rows, "metadata": metadata, "digests": digests,
                "verified": verified}


def main() -> dict:
    root_module = Path(cmpct.__file__).resolve()
    checkout = Path(os.environ["CMPCT_J24I07_CHECKOUT"]).resolve()
    if root_module == checkout or checkout in root_module.parents:
        raise AssertionError("installed-source custody failed: imported checkout")
    report = {
        "schema": "j24i07-three-host-candidate-v1",
        "host": platform.platform(),
        "python": sys.version,
        "cmpct_module": str(root_module),
        "source_sha": os.environ["CMPCT_J24I07_HEAD"],
        "cases": [],
        "invariants": [],
        "decision": "PENDING",
    }
    artifact_dir = Path(os.environ["CMPCT_J24I07_ARTIFACT_DIR"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="j24i07-") as td:
        work = Path(td)
        outside = work / "external"
        outside.mkdir()
        sentinel = outside / "sentinel.bin"
        sentinel.write_bytes(b"J24I07 OUTSIDE WRITES FORBIDDEN\n")
        frozen_sentinel = sha(sentinel)

        for name in ("plain", "absolute", "parent-relative", "hardlink"):
            folder = work / (name + "-root")
            folder.mkdir()
            (folder / "data.bin").write_bytes(bytes(range(256)) * 64 + b"cmpct-j24i07\n")
            target = None
            if name == "absolute":
                target = str(sentinel.resolve())
            elif name == "parent-relative":
                target = "../external/sentinel.bin"
            observed_target = None
            if target is not None:
                # Windows may return a native extended-length spelling for an
                # absolute symlink. The actual OS readback is Builder's source;
                # the caller's requested spelling is NOT a cross-host oracle.
                # Do not weaken either archive-byte fidelity assertion below.
                (folder / "link").symlink_to(target)
                observed_target = os.readlink(folder / "link")
                if not observed_target:
                    raise AssertionError("host returned an empty symlink target")
            if name == "hardlink":
                os.link(folder / "data.bin", folder / "hardlink.bin")
                if os.stat(folder / "data.bin").st_ino != os.stat(folder / "hardlink.bin").st_ino:
                    raise AssertionError("hardlink control is not an actual hardlink")

            source = work / (name + ".cmpct")
            output = work / (name + ".compacted.cmpct")
            Builder(folder, reproducible=True, workers=1).build(source)
            before = observed(source)
            before_sha = sha(source)
            if target is not None:
                with CMPCT(source) as reader:
                    if reader.read("link") != os.fsencode(observed_target):
                        raise AssertionError("source lost literal link target")
                    blocked = work / (name + "-blocked-destination")
                    try:
                        reader.extractall(blocked)
                    except OSError as exc:
                        if "unsafe symlink target" not in str(exc):
                            raise
                    else:
                        raise AssertionError("public default extraction accepted unsafe target")
            output.write_bytes(b"PREEXISTING TARGET BEFORE SUCCESS")
            wall0 = time.perf_counter_ns()
            cpu0 = time.process_time_ns()
            compact_archive(source, output)
            cost_wall = time.perf_counter_ns() - wall0
            cost_cpu = time.process_time_ns() - cpu0
            after = observed(output)
            if after != before:
                raise AssertionError("compaction lost logical rows, content or ownership " + name)
            if sha(source) != before_sha:
                raise AssertionError("compaction changed source archive")
            if sha(sentinel) != frozen_sentinel:
                raise AssertionError("compaction traversed external symlink")
            if target is not None:
                with CMPCT(output) as reader:
                    if reader.read("link") != os.fsencode(observed_target):
                        raise AssertionError("compaction changed target text")
            if name == "hardlink" and not any(r[1] == K_HARDLINK for r in after["rows"]):
                # Preserve physical archives and an independent filesystem
                # discriminator on failure. No hardlink control is relaxed.
                shutil.copyfile(source, artifact_dir / (name + "-source.cmpct"))
                shutil.copyfile(output, artifact_dir / (name + "-output.cmpct"))
                st_a = os.stat(folder / "data.bin")
                st_b = os.stat(folder / "hardlink.bin")
                with os.scandir(folder) as entries:
                    scan = {e.name: e.stat(follow_symlinks=False) for e in entries}
                witness = {
                    "same_inode": (st_a.st_dev, st_a.st_ino) == (st_b.st_dev, st_b.st_ino),
                    "os_stat_nlink": [st_a.st_nlink, st_b.st_nlink],
                    "scandir_nlink": [scan["data.bin"].st_nlink, scan["hardlink.bin"].st_nlink],
                    "scandir_identical_inodes": (
                        scan["data.bin"].st_dev, scan["data.bin"].st_ino
                    ) == (scan["hardlink.bin"].st_dev, scan["hardlink.bin"].st_ino),
                    "source_kinds": [(r[0], r[1]) for r in before["rows"]],
                    "output_kinds": [(r[0], r[1]) for r in after["rows"]],
                }
                raise AssertionError("hardlink flattened, diagnostic=" + json.dumps(witness, sort_keys=True))
            shutil.copyfile(source, artifact_dir / (name + "-source.cmpct"))
            shutil.copyfile(output, artifact_dir / (name + "-output.cmpct"))
            report["cases"].append({
                "name": name, "source_sha256": before_sha, "output_sha256": sha(output),
                "source_bytes": source.stat().st_size, "output_bytes": output.stat().st_size,
                "entries": len(after["rows"]), "wall_ns": cost_wall, "cpu_ns": cost_cpu,
                "semantics_equal": True, "outside_sentinel_unchanged": True,
            })
            if target is not None:
                # Preserve the exact two literals in provider receipts. A
                # mismatch BEFORE the archive is evidence about filesystem
                # representation, not an authorized change to CMPCT content.
                report["cases"][-1]["requested_link_hex"] = os.fsencode(target).hex()
                report["cases"][-1]["observed_link_hex"] = os.fsencode(observed_target).hex()
                report["cases"][-1]["requested_equals_observed"] = (target == observed_target)

        # A corrupt physical blob must not overwrite an existing destination.
        source = work / "plain.cmpct"
        damaged = work / "damaged.cmpct"
        corrupted = bytearray(source.read_bytes())
        with CMPCT(source) as reader:
            off, _, _, _, meta_length = reader.blobs[0]
            physical = reader.record_base + off + BHDR.size + meta_length
        corrupted[physical] ^= 0x40
        damaged.write_bytes(corrupted)
        output = work / "protected-destination.cmpct"
        output.write_bytes(b"PRESERVE DESTINATION ON CORRUPTION\n")
        previous_output = sha(output)
        try:
            compact_archive(damaged, output)
        except (OSError, ValueError, RuntimeError) as exc:
            report["invariants"].append({
                "name": "corrupt-source-rejected", "error_type": type(exc).__name__,
                "destination_unchanged": sha(output) == previous_output,
            })
        else:
            raise AssertionError("corrupt source was published")
        if sha(output) != previous_output or sha(sentinel) != frozen_sentinel:
            raise AssertionError("failed compaction mutated destination or sentinel")

        # Overwrite a destination symlink without following it.
        redirected = work / "redirected.cmpct"
        redirected.symlink_to(sentinel)
        compact_archive(source, redirected)
        if redirected.is_symlink() or sha(sentinel) != frozen_sentinel:
            raise AssertionError("destination symlink was followed")
        report["invariants"].append({"name": "destination-symlink-not-followed", "passed": True})

        # Closed-source overwrite is an explicit capability claim on Windows.
        in_place = work / "in-place.cmpct"
        shutil.copyfile(source, in_place)
        before_in_place = observed(in_place)
        compact_archive(in_place, in_place)
        if observed(in_place) != before_in_place:
            raise AssertionError("in-place compaction changed source logical content")
        report["invariants"].append({"name": "in-place-closed-owner", "passed": True})

    if len(report["cases"]) != 4 or len(report["invariants"]) != 3:
        raise AssertionError("incomplete host tribunal")
    report["decision"] = "HOST_CORRECTNESS_PASS_NOT_RELEASE"
    return report


if __name__ == "__main__":
    receipt = Path(os.environ["CMPCT_J24I07_RECEIPT"])
    try:
        result = main()
    except Exception as exc:
        # Preserve explicit failure identity, never count failure as a pass.
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps({
            "schema": "j24i07-three-host-candidate-v1", "decision": "HOST_NONPASS",
            "host": platform.platform(), "source_sha": os.environ.get("CMPCT_J24I07_HEAD"),
            "error": type(exc).__name__ + ": " + str(exc),
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        raise
    receipt.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True, indent=2))

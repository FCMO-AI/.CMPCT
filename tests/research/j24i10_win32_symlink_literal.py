"""J24I10 exact-source three-OS symlink literal custody court.

The argument supplied to os.symlink is not presumed to equal the OS read-back
spelling. The OS-observed target bytes must survive both authenticated archives
exactly; a separate control checks readlink re-materialization idempotence.
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
import traceback
from pathlib import Path

import cmpct
from cmpct.builder import Builder
from cmpct.codec import K_DIR
from cmpct.reader import CMPCT
from cmpct.transactions import compact_archive, _compaction_source_metadata


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def file_sha(path: Path) -> str:
    return digest(path.read_bytes())


def target_record(target: str) -> dict:
    raw = os.fsencode(target)
    return {"repr": repr(target), "hex": raw.hex(),
            "sha256": digest(raw), "byte_count": len(raw)}


def read_archive(path: Path) -> dict:
    with CMPCT(path) as archive:
        rows = list(archive.files)
        metadata = _compaction_source_metadata(archive)
        hashes = {row[0]: archive.file_sha256(row[0])
                  for row in rows if row[1] != K_DIR}
        data = archive.read("link")
        verified = archive.verify()
        if not verified:
            raise AssertionError(f"strong verification failed: {path}")
        return {"rows": rows, "metadata": metadata, "hashes": hashes,
                "link": data, "verified": verified}


def main() -> dict:
    checkout = Path(os.environ["CMPCT_J24I10_CHECKOUT"]).resolve()
    imported = Path(cmpct.__file__).resolve()
    if imported == checkout or checkout in imported.parents:
        raise AssertionError("must use wheel-installed candidate, not checkout")
    if os.environ["CMPCT_J24I10_HEAD"] != os.environ["CMPCT_J24I10_EXPECTED_HEAD"]:
        raise AssertionError("exact-head source mismatch")
    artifact = Path(os.environ["CMPCT_J24I10_ARTIFACT_DIR"])
    artifact.mkdir(parents=True, exist_ok=True)
    receipt = {"schema": "j24i10-literal-custody-v1",
               "source_sha": os.environ["CMPCT_J24I10_HEAD"],
               "installed_module": str(imported), "host": platform.platform(),
               "python": sys.version, "cases": [], "status": "RUNNING",
               "stage": "begin"}
    try:
        with tempfile.TemporaryDirectory(prefix="j24i10-host-") as td:
            work = Path(td)
            outside = work / "external"
            outside.mkdir()
            sentinel = outside / "sentinel.bin"
            sentinel.write_bytes(b"J24I10 EXTERNAL INTEGRITY BOUNDARY\n")
            frozen_sentinel = file_sha(sentinel)
            for name in ("relative", "parent-relative", "absolute"):
                receipt["stage"] = name + ":source-filesystem"
                folder = work / (name + "-tree")
                folder.mkdir()
                (folder / "data.bin").write_bytes(bytes(range(256)) * 16 + b"J24I10\n")
                requested = {"relative": "data.bin",
                             "parent-relative": "../external/sentinel.bin",
                             "absolute": str(sentinel.resolve())}[name]
                link = folder / "link"
                link.symlink_to(requested)
                observed = os.readlink(link)
                case = {"name": name, "requested": target_record(requested),
                        "observed": target_record(observed),
                        "requested_matches_observed": requested == observed,
                        "stage": "filesystem"}
                receipt["cases"].append(case)
                probe = work / (name + "-probe")
                try:
                    probe.symlink_to(observed)
                    observed_twice = os.readlink(probe)
                    case["rematerialized"] = target_record(observed_twice)
                    case["readlink_idempotent"] = observed == observed_twice
                except OSError as exc:
                    # Keep archive evidence even if Win32 refuses re-materialization.
                    case["rematerialization_error"] = type(exc).__name__ + ": " + str(exc)
                    case["readlink_idempotent"] = False
                finally:
                    if probe.is_symlink():
                        probe.unlink()
                source = work / (name + ".cmpct")
                output = work / (name + ".compacted.cmpct")
                Builder(folder, reproducible=True, workers=1).build(source)
                shutil.copyfile(source, artifact / (name + "-source.cmpct"))
                before = read_archive(source)
                physical_target = observed.encode("utf-8")  # Builder uses readlink(...).encode()
                if before["link"] != physical_target:
                    raise AssertionError("Builder/Reader changed OS-observed link bytes: " + name)
                case["stage"] = "source-archive"
                case["source_archive"] = {
                    "sha256": file_sha(source), "stored_bytes": source.stat().st_size,
                    "target": target_record(before["link"].decode("utf-8")),
                    "entries": len(before["rows"])}
                if name != "relative":
                    denied = work / (name + "-default-extraction-denied")
                    try:
                        with CMPCT(source) as archive:
                            archive.extractall(denied)
                    except OSError as exc:
                        if "unsafe symlink target" not in str(exc):
                            raise AssertionError("wrong extraction denial: " + repr(exc)) from exc
                    else:
                        raise AssertionError("default extraction accepted unsafe " + name)
                    case["safe_extract_denied"] = True
                output.write_bytes(b"J24I10 REPLACE OLD DESTINATION")
                start_w = time.perf_counter_ns()
                start_c = time.process_time_ns()
                compact_archive(source, output)
                wall_ns = time.perf_counter_ns() - start_w
                cpu_ns = time.process_time_ns() - start_c
                shutil.copyfile(output, artifact / (name + "-output.cmpct"))
                after = read_archive(output)
                case["stage"] = "compacted-archive"
                case["compact_archive"] = {
                    "sha256": file_sha(output), "stored_bytes": output.stat().st_size,
                    "target": target_record(after["link"].decode("utf-8")),
                    "entries": len(after["rows"]), "wall_ns": wall_ns, "cpu_ns": cpu_ns}
                case["archive_semantics_exact"] = before == after
                case["outside_untouched"] = (file_sha(sentinel) == frozen_sentinel)
                case["source_unchanged"] = (file_sha(source) ==
                                            case["source_archive"]["sha256"])
                if before != after:
                    raise AssertionError("compaction changed archive semantics: " + name)
                if after["link"] != physical_target:
                    raise AssertionError("compaction changed observed target bytes: " + name)
                if not case["source_unchanged"] or not case["outside_untouched"]:
                    raise AssertionError("compaction mutated source or sentinel: " + name)
                if not case["readlink_idempotent"]:
                    raise AssertionError("OS re-materialization changes readlink: " + name)
                case["stage"] = "PASS"
        if len(receipt["cases"]) != 3 or any(c["stage"] != "PASS" for c in receipt["cases"]):
            raise AssertionError("incomplete three-target court")
        receipt["status"] = "HOST_PRODUCT_LITERAL_PASS_NOT_RELEASE"
        receipt["stage"] = "complete"
        return receipt
    except BaseException as exc:
        receipt["status"] = "HOST_NONPASS"
        receipt["error"] = type(exc).__name__ + ": " + str(exc)
        receipt["traceback"] = traceback.format_exc(limit=12)
        raise
    finally:
        Path(os.environ["CMPCT_J24I10_RECEIPT"]).write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    result = main()
    print(json.dumps({"status": result["status"], "host": result["host"],
                      "cases": [{k: v for k, v in item.items()
                                 if k in ("name", "requested_matches_observed",
                                          "readlink_idempotent",
                                          "archive_semantics_exact", "outside_untouched")}
                                for item in result["cases"]]}, sort_keys=True))

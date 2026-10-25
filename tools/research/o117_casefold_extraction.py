#!/usr/bin/env python3
"""O117: exact-archive cross-platform extraction namespace falsifier.

Scientific instrument, not a product fix. Two phase execution:
  python tools/research/o117_casefold_extraction.py produce --directory o117-artifact
  python tools/research/o117_casefold_extraction.py consume --directory o117-artifact --output o117-evidence
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import sys
import tempfile
from pathlib import Path

from cmpct.builder import Builder
from cmpct.reader import CMPCT

PAYLOADS = {
    "Report.txt": b"UPPER-ASCII-NAME-CASE-COLLISION-ORIGINAL\\n" * 47,
    "report.txt": b"lower-ascii-name-case-collision-original\\n" * 53,
    "other.txt": b"unrelated-distinct-control\\n" * 29,
}


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def save(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def produce(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / "casefold-source.cmpct"
    manifest = folder / "manifest.json"
    with tempfile.TemporaryDirectory(prefix="cmpct-o117-producer-") as tmp:
        src = Path(tmp) / "source"
        src.mkdir()
        for name, raw in PAYLOADS.items():
            (src / name).write_bytes(raw)
        # A real filesystem must support two distinct source names.
        assert len(list(src.iterdir())) == len(PAYLOADS), "producer cannot represent corpus"
        assert not os.path.samefile(src / "Report.txt", src / "report.txt")
        Builder(src, workers=1).build(archive)
    with CMPCT(archive) as r:
        assert r.verify() is not False
        assert set(r.by) == set(PAYLOADS), "archive filename identity lost before cross-host test"
        for name, raw in PAYLOADS.items():
            assert r.read(name) == raw, f"producer Reader mismatch: {name}"
    data = archive.read_bytes()
    result = {
        "source": "real Linux Builder and CMPCT reader",
        "archive_sha256": digest(data),
        "archive_bytes": len(data),
        "members": {name: {"sha256": digest(raw), "length": len(raw)} for name, raw in PAYLOADS.items()},
    }
    save(manifest, result)
    print("O117_PRODUCER_SOURCE_EXACT=PASS", flush=True)
    print(json.dumps(result, sort_keys=True), flush=True)


def probe_case_alias(directory: Path) -> bool:
    """Observe actual target filesystem semantics, not inferred OS-name behavior."""
    test = directory / "_o117_host_case_probe_"
    test.mkdir()
    upper = test / "Probe.txt"
    lower = test / "probe.txt"
    try:
        upper.write_bytes(b"UPPER")
        lower.write_bytes(b"lower")
        return os.path.samefile(upper, lower)
    finally:
        shutil.rmtree(test)


def consume(folder: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    archive = folder / "casefold-source.cmpct"
    assert digest(archive.read_bytes()) == manifest["archive_sha256"], "cross-job archive identity changed"
    assert set(manifest["members"]) == set(PAYLOADS)
    for name, raw in PAYLOADS.items():
        assert manifest["members"][name]["sha256"] == digest(raw)
    with CMPCT(archive) as r:
        assert set(r.by) == set(PAYLOADS)
        assert r.verify() is not False
        assert all(r.read(name) == raw for name, raw in PAYLOADS.items())
        print("O117_NATIVE_READER_MEMBER_IDENTITY=PASS", flush=True)

        with tempfile.TemporaryDirectory(prefix="cmpct-o117-output-") as tmp:
            dest = Path(tmp) / "extracted"
            dest.mkdir()
            host_alias = probe_case_alias(dest)
            extraction_error = None
            try:
                r.extractall(dest, metadata=False)
            except Exception as exc:
                extraction_error = f"{type(exc).__name__}: {exc}"
            files = sorted(p.name for p in dest.iterdir() if p.is_file())
            observed = {}
            for name in PAYLOADS:
                p = dest / name
                observed[name] = digest(p.read_bytes()) if p.is_file() else None
            member_equal = {
                name: observed[name] == digest(raw)
                for name, raw in PAYLOADS.items()
            }
            aliases = None
            if (dest / "Report.txt").exists() and (dest / "report.txt").exists():
                aliases = os.path.samefile(dest / "Report.txt", dest / "report.txt")
            result = {
                "platform": platform.platform(),
                "python": sys.version,
                "archive_sha256": manifest["archive_sha256"],
                "host_case_alias_observed": host_alias,
                "reader_exact_all_members": True,
                "extractall_error": extraction_error,
                "physical_file_inventory": files,
                "physical_count": len(files),
                "member_sha256": observed,
                "member_bytes_equal_source": member_equal,
                "Report_report_same_physical_file": aliases,
                "verdict": "",
                "experimental_scope": "host namespace fidelity only; product source unchanged",
            }
            if extraction_error is not None:
                result["verdict"] = "EXTRACTION_REJECTED_ARCHIVE"
            elif all(member_equal.values()) and not aliases:
                result["verdict"] = "COMPLETE_SOURCE_TREE_FIDELITY"
            elif host_alias and aliases and not all(member_equal.values()):
                result["verdict"] = "CONFIRMED_SILENT_HOST_CASE_ALIAS_LOSS"
            else:
                result["verdict"] = "AMBIGUOUS_MUST_INVESTIGATE"
            save(output / "result.json", result)
            print(json.dumps(result, sort_keys=True), flush=True)
            print("O117_VERDICT=" + result["verdict"], flush=True)
            if not host_alias:
                assert result["verdict"] == "COMPLETE_SOURCE_TREE_FIDELITY", "unexpected loss on case-sensitive host"
            else:
                assert result["verdict"] in (
                    "CONFIRMED_SILENT_HOST_CASE_ALIAS_LOSS", "EXTRACTION_REJECTED_ARCHIVE",
                ), "unclassified result on case-insensitive host"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["produce", "consume"])
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("o117-evidence"))
    args = parser.parse_args()
    if args.phase == "produce":
        produce(args.directory)
    else:
        consume(args.directory, args.output)

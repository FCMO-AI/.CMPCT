#!/usr/bin/env python3
"""J24G26: source-exact CMPCT ZIP output-symlink compatibility court.

Research-only. Compare published r24 Reader and staged publication candidate
in separate interpreters on frozen builder-independent physical r24 archives.
This intentionally does NOT patch either product implementation.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

BASE_SHA = "80c358f8824ec1b20d349c92ed94c898090969b0"
PREREG_SHA = "9c8ecec2f48450b0a34fa8f80aeb68676e856a9e"
CASES = ("relative", "absolute", "dangling", "ordinary")
VECTORS = ("raw.bin", "deflate.txt")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str | None:
    return digest(path.read_bytes()) if path.exists() and path.is_file() else None


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True
    ).strip()


def old_zip(path: Path) -> bytes:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("prior.txt", b"ORIGINAL INDEPENDENT VALID ZIP")
    raw = path.read_bytes()
    with zipfile.ZipFile(path) as archive:
        assert archive.read("prior.txt") == b"ORIGINAL INDEPENDENT VALID ZIP"
    return raw


def child(args: argparse.Namespace) -> None:
    # The script is hosted in the candidate branch but imports CMPCT only from
    # the requested exact-source tree; not from the editable site installation.
    module_root = (args.installed_root if args.installed_root is not None else args.engine_root / "src")
    sys.path.insert(0, str(module_root))
    from cmpct.reader import CMPCT
    import cmpct.reader as reader_module

    expected_reader = (module_root / "cmpct/reader.py").resolve()
    assert Path(reader_module.__file__).resolve() == expected_reader
    archive_path = args.case_root / "source.cmpct"
    output_path = args.case_root / "output.zip"
    referent = args.case_root / "target.zip"
    missing = args.case_root / "missing.zip"
    previous_source = file_digest(archive_path)
    before_link = output_path.is_symlink()
    before_link_inode = os.lstat(output_path).st_ino if output_path.exists() or before_link else None
    before_referent_sha = file_digest(referent)
    before_missing = missing.exists()

    try:
        with CMPCT(archive_path) as reader:
            assert digest(reader.read(args.name)) == args.expected_sha
            reader.export_zip(output_path)
        status, error = "ACCEPT", None
    except Exception as exc:
        status, error = "REJECT", f"{type(exc).__name__}: {exc}"

    after_source = file_digest(archive_path)
    after_link = output_path.is_symlink()
    after_link_inode = os.lstat(output_path).st_ino if output_path.exists() or after_link else None
    exported_sha = file_digest(output_path)
    content_valid = False
    zip_sha = None
    if status == "ACCEPT":
        with zipfile.ZipFile(output_path) as zf:
            content = zf.read(args.name)
            assert zf.namelist() == [args.name], zf.namelist()
            assert zf.testzip() is None
            zip_sha = digest(content)
            content_valid = zip_sha == args.expected_sha
    result = {
        "engine": args.engine,
        "engine_source_sha": git(args.engine_root, "rev-parse", "HEAD"),
        "reader_blob_sha": git(args.engine_root, "hash-object", "src/cmpct/reader.py"),
        "case": args.case,
        "vector": args.name,
        "status": status,
        "error": error,
        "before_source_sha": previous_source,
        "after_source_sha": after_source,
        "source_unchanged": previous_source == after_source,
        "before_symlink": before_link,
        "after_symlink": after_link,
        "before_symlink_inode": before_link_inode,
        "after_symlink_inode": after_link_inode,
        "before_referent_sha": before_referent_sha,
        "after_referent_sha": file_digest(referent),
        "before_missing_exists": before_missing,
        "after_missing_exists": missing.exists(),
        "output_sha256": exported_sha,
        "zip_logical_sha256": zip_sha,
        "zip_validated_by_stdlib": content_valid,
    }
    print(json.dumps(result, sort_keys=True))


def prepare(case_root: Path, source_bytes: bytes, mode: str) -> str:
    case_root.mkdir(parents=True)
    (case_root / "source.cmpct").write_bytes(source_bytes)
    previous = old_zip(case_root / "target.zip")
    output = case_root / "output.zip"
    if mode == "relative":
        output.symlink_to("target.zip")
    elif mode == "absolute":
        output.symlink_to(str((case_root / "target.zip").resolve()))
    elif mode == "dangling":
        (case_root / "missing.zip").unlink(missing_ok=True)
        output.symlink_to("missing.zip")
    elif mode == "ordinary":
        output.write_bytes(previous)
    elif mode == "source_alias":
        output.symlink_to("source.cmpct")
    else:
        raise ValueError(mode)
    return digest(previous)


def assert_case(a: dict, prior_sha: str, name: str, mode: str, source_sha: str) -> None:
    assert a["source_unchanged"], a
    assert a["before_source_sha"] == a["after_source_sha"] == source_sha, a
    assert a["before_referent_sha"] == prior_sha, a
    if mode == "source_alias":
        assert a["engine"] == "candidate" and a["status"] == "REJECT", a
        assert a["before_symlink"] and a["after_symlink"], a
        assert a["after_referent_sha"] == prior_sha, a
        assert a["after_missing_exists"] is False, a
        return
    assert a["status"] == "ACCEPT" and a["zip_validated_by_stdlib"], a
    assert a["zip_logical_sha256"] == name, a  # name carries expected SHA here
    if mode in ("relative", "absolute"):
        assert a["before_symlink"] is True, a
        assert a["after_symlink"] is (a["engine"] == "published"), a
        assert (a["after_referent_sha"] == prior_sha) is (a["engine"] == "candidate"), a
    elif mode == "dangling":
        assert a["before_symlink"] is True, a
        assert a["after_symlink"] is (a["engine"] == "published"), a
        assert a["after_missing_exists"] is (a["engine"] == "published"), a
        assert a["after_referent_sha"] == prior_sha, a
    elif mode == "ordinary":
        assert not a["before_symlink"] and not a["after_symlink"], a
        assert a["after_referent_sha"] == prior_sha, a


def parent(args: argparse.Namespace) -> None:
    if os.name != "posix":
        raise RuntimeError("POSIX symlink semantics required: no Windows capability fiction")
    candidate = Path.cwd().resolve()
    published = args.published_root.resolve()
    assert git(published, "rev-parse", "HEAD") == BASE_SHA, "published source drift"
    expected_head = os.environ.get("EXPECTED_HEAD")
    assert not expected_head or git(candidate, "rev-parse", "HEAD") == expected_head, "candidate source drift"
    vector_path = candidate / "tests/conformance/v24-direct-codecs.json"
    vectors = json.loads(vector_path.read_text())["vectors"]
    chosen = {v["name"]: v for v in vectors if v["name"] in VECTORS}
    assert set(chosen) == set(VECTORS)
    records = []
    output = candidate / "j24g26-evidence"
    output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g26-") as tmp:
        root = Path(tmp)
        for name, item in sorted(chosen.items()):
            data = base64.b64decode(item["archive_base64"])
            assert digest(data) == item["archive_sha256"]
            assert len(data) == item["archive_bytes"]
            for case in (*CASES, "source_alias"):
                for engine, engine_root in (("published", published), ("candidate", candidate)):
                    if case == "source_alias" and engine == "published":
                        continue  # never run old writer against its own source path
                    case_root = root / name / case / engine
                    prior_sha = prepare(case_root, data, case)
                    proc = subprocess.run(
                        [sys.executable, "-B", str(Path(__file__).resolve()), "--child",
                         "--engine-root", str(engine_root), "--engine", engine,
                         *(["--installed-root", str(args.installed_root)] if engine == "published" else []),
                         "--case-root", str(case_root), "--case", case, "--name", name,
                         "--expected-sha", item["logical_sha256"]],
                        cwd=str(case_root), text=True, capture_output=True, timeout=40
                    )
                    assert proc.returncode == 0, (case, engine, proc.stdout, proc.stderr)
                    lines = proc.stdout.strip().splitlines()
                    assert len(lines) == 1, (case, engine, lines)
                    record = json.loads(lines[0])
                    assert record["engine_source_sha"] == (BASE_SHA if engine == "published" else git(candidate, "rev-parse", "HEAD"))
                    assert_case(record, prior_sha, item["logical_sha256"], case, item["archive_sha256"])
                    records.append(record)
                    if case != "source_alias":
                        shutil.copyfile(case_root / "output.zip", output / f"{name}.{case}.{engine}.zip")
        assert len(records) == len(VECTORS) * (len(CASES) * 2 + 1)
    result = {
        "schema": "cmpct-j24g26-source-exact-zip-symlink-contract-v1",
        "date_utc": "2026-10-28",
        "prereg_sha": PREREG_SHA,
        "published_source_sha": BASE_SHA,
        "candidate_source_sha": git(candidate, "rev-parse", "HEAD"),
        "candidate_reader_blob_sha": git(candidate, "hash-object", "src/cmpct/reader.py"),
        "fixture_blob_sha": git(candidate, "hash-object", "tests/conformance/v24-direct-codecs.json"),
        "comparisons": len(records),
        "control": "frozen r24 physical inputs, independently decoded ZIP, source and prior referent byte identity",
        "decision": "OUTPUT_SYMLINK_ACCEPTANCE_PARITY_FALSIFIED",
        "scope": "POSIX output symlink path semantics; scientific compatibility court, no installed product promotion",
        "records": records,
    }
    (output / "results.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "records"}, sort_keys=True))
    print(f"PASS {len(records)} source-exact physical cases")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--published-root", type=Path)
    parser.add_argument("--engine-root", type=Path)
    parser.add_argument("--installed-root", type=Path)
    parser.add_argument("--case-root", type=Path)
    parser.add_argument("--engine", choices=("published", "candidate"))
    parser.add_argument("--case", choices=(*CASES, "source_alias"))
    parser.add_argument("--name")
    parser.add_argument("--expected-sha")
    args = parser.parse_args()
    if args.child:
        child(args)
    else:
        assert args.published_root, "--published-root required"
        parent(args)


if __name__ == "__main__":
    main()

"""J24D02: source-exact fault-atomicity differential on frozen r24 archives.

Research-only. Prediction was frozen independently before this instrument.
"""
from __future__ import annotations

import base64
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
from unittest.mock import patch

from cmpct.reader import CMPCT


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_case(root: Path, vector: dict, family: str, fault: bool, ordinal: int) -> dict:
    archive_bytes = base64.b64decode(vector["archive_base64"], validate=True)
    assert len(archive_bytes) == vector["archive_bytes"]
    assert sha(archive_bytes) == vector["archive_sha256"]
    name = vector["name"]
    outdir = root / f"out-{ordinal}"
    outdir.mkdir()
    archive = root / f"archive-{ordinal}.cmpct"
    archive.write_bytes(archive_bytes)
    sentinel = (b"preexisting-destination-J24D02-" * 7) + bytes([ordinal])
    dest = outdir / name
    dest.write_bytes(sentinel)
    before_sha = sha(dest.read_bytes())
    before_inode = dest.stat().st_ino
    alias = outdir / (name + ".external-hardlink")
    alias_created = False
    try:
        os.link(dest, alias)
        alias_created = True
    except OSError:
        pass

    call_count = 0
    real_write = os.write
    first_written = b""

    def faulted_write(fd, data):
        nonlocal call_count, first_written
        call_count += 1
        if call_count == 1:
            # Execute an actual successful short kernel write rather than faking its return value.
            chunk = memoryview(data)[: min(7, len(data))]
            n = real_write(fd, chunk)
            assert n > 0
            first_written = bytes(chunk[:n])
            return n
        raise OSError(errno.ENOSPC, "J24D02 injected output exhaustion")

    error_name = None
    error_errno = None
    with CMPCT(archive) as reader:
        valid = reader.read(name)
        assert len(valid) == vector["logical_size"]
        assert sha(valid) == vector["logical_sha256"]
        try:
            if fault:
                with patch("cmpct.reader.os.write", faulted_write):
                    reader.extractall(outdir, metadata=False)
            else:
                reader.extractall(outdir, metadata=False)
        except OSError as exc:
            error_name = type(exc).__name__
            error_errno = exc.errno
        except Exception as exc:
            error_name = type(exc).__name__
            raise

    after = dest.read_bytes()
    stages = sorted(p.name for p in outdir.glob(".*cmpct-part-*"))
    alias_sha = sha(alias.read_bytes()) if alias_created else None
    # Overwrite-by-rename intentionally detaches external hardlink aliases on clean success.
    # This is explicit compatibility debt, never counted as a generic win.
    alias_preserved = (alias_sha == before_sha) if alias_created else None
    if alias_created:
        assert alias_preserved
    row = {
        "family": family,
        "member": name,
        "mode": "fault" if fault else "clean",
        "archive_sha256": sha(archive_bytes),
        "expected_member_sha256": vector["logical_sha256"],
        "before_sha256": before_sha,
        "after_sha256": sha(after),
        "before_inode": before_inode,
        "after_inode": dest.stat().st_ino,
        "fault_calls": call_count,
        "real_short_write_hex": first_written.hex(),
        "error": error_name,
        "error_errno": error_errno,
        "after_size": len(after),
        "stage_remainders": stages,
        "external_alias_created": alias_created,
        "external_alias_sha256": alias_sha,
        "external_alias_preserved": alias_preserved,
    }

    if fault:
        assert call_count == 2, row
        assert first_written and len(first_written) <= 7, row
        assert error_errno == errno.ENOSPC, row
        if family == "direct":
            # Candidate gate: the short kernel write must affect only a disposable stage.
            assert after == sentinel, row
            assert row["after_inode"] == before_inode, row
            assert not stages, row
            row["decision"] = "STAGED_DIRECT_DESTINATION_PRESERVED"
        else:
            assert after == sentinel, row
            assert row["after_inode"] == before_inode, row
            assert not stages, row
            row["decision"] = "STAGED_CHUNK_DESTINATION_PRESERVED"
    else:
        assert not stages, row
        assert error_name is None, row
        assert sha(after) == vector["logical_sha256"], row
        row["decision"] = "CLEAN_EXACT_RECONSTRUCTION"
    return row


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: j24d02_direct_fault_court.py REPO_ROOT OUTPUT_JSON")
    repo, output = map(Path, sys.argv[1:])
    assert Path(__file__).resolve().parent.parent == repo.resolve()
    from cmpct import reader as reader_mod
    assert repo.resolve() not in Path(reader_mod.__file__).resolve().parents, (
        "source-tree import is not an independently installed product"
    )

    matrix = [
        ("direct", "tests/conformance/v24-direct-codecs.json"),
        ("chunked", "tests/conformance/v24-chunk-maps.json"),
    ]
    rows = []
    with tempfile.TemporaryDirectory(prefix="cmpct-j24d02-") as work:
        root = Path(work)
        for family, rel in matrix:
            fixture = json.loads((repo / rel).read_text())
            assert fixture["format_revision"] == 24
            for vector in fixture["vectors"]:
                for fault in (False, True):
                    rows.append(run_case(root, vector, family, fault, len(rows)))
    receipt = {
        "schema": "cmpct-j24d02-r1",
        "head_sha": os.environ.get("J24D02_HEAD_SHA", ""),
        "reader_blob": os.environ.get("J24D02_READER_BLOB", ""),
        "platform": platform.platform(),
        "python": sys.version,
        "cases": rows,
        "cases_total": len(rows),
        "clean_exact": sum(x["decision"] == "CLEAN_EXACT_RECONSTRUCTION" for x in rows),
        "direct_preserved": sum(x["decision"] == "STAGED_DIRECT_DESTINATION_PRESERVED" for x in rows),
        "chunk_preserved": sum(x["decision"] == "STAGED_CHUNK_DESTINATION_PRESERVED" for x in rows),
    }
    assert (receipt["clean_exact"], receipt["direct_preserved"], receipt["chunk_preserved"]) == (5, 3, 2)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "head": receipt["head_sha"], "platform": receipt["platform"],
        "cases": receipt["cases_total"],
        "clean_exact": receipt["clean_exact"],
        "direct_preserved": receipt["direct_preserved"],
        "chunk_preserved": receipt["chunk_preserved"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()

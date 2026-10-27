"""J24D05 prospective source-exact direct-stage fd-mode custody court.

Uses unchanged independent revision-24 direct-codec vectors. Does not mutate CMPCT's
reader, historical J24D02/J24D03 tests, comparator or frozen archive data.
"""
from __future__ import annotations

import base64
from contextlib import contextmanager, ExitStack
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


VARIANTS = ("native", "absent", "absent-fault", "oserror", "valueerror", "native-fault")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@contextmanager
def mode_variant(variant: str):
    """Simulate missing fd API and actively veto any chmod of a mutable stage name."""
    originally_present = hasattr(os, "fchmod")
    original_fchmod = getattr(os, "fchmod", None)
    chmod_attempts = []
    try:
        with ExitStack() as stack:
            if variant.startswith("absent"):
                if originally_present:
                    delattr(os, "fchmod")

                def veto_path_mode(path, mode, *args, **kwargs):
                    chmod_attempts.append(str(path))
                    raise AssertionError("J24D05 forbidden pathname chmod")
                stack.enter_context(patch.object(os, "chmod", side_effect=veto_path_mode))
            elif variant in ("oserror", "valueerror"):
                def fail_mode(fd, mode):
                    if variant == "oserror":
                        raise OSError(errno.EPERM, "J24D05 optional fd chmod permission denial")
                    raise ValueError("J24D05 unexpected descriptor chmod failure")
                stack.enter_context(patch.object(os, "fchmod", create=True, new=fail_mode))
            yield chmod_attempts
    finally:
        if originally_present:
            setattr(os, "fchmod", original_fchmod)
        elif hasattr(os, "fchmod"):
            delattr(os, "fchmod")


def case(root: Path, vector: dict, variant: str, ordinal: int) -> dict:
    wire = base64.b64decode(vector["archive_base64"], validate=True)
    assert len(wire) == vector["archive_bytes"]
    assert digest(wire) == vector["archive_sha256"]
    archive = root / f"archive-{ordinal}.cmpct"
    archive.write_bytes(wire)
    output = root / f"output-{ordinal}"
    output.mkdir()
    member = vector["name"]
    final = output / member
    sentinel = b"J24D05-PRIOR-DIRECT-OUTPUT-" * 4 + ordinal.to_bytes(2, "little")
    final.write_bytes(sentinel)
    old_inode = final.stat().st_ino
    original_write = os.write
    write_calls = []
    actual_kernel_write = b""

    def fault_write(fd, data):
        nonlocal actual_kernel_write
        write_calls.append(len(data))
        if len(write_calls) == 1:
            take = memoryview(data)[: min(7, len(data))]
            n = original_write(fd, take)
            assert 1 <= n <= 7
            actual_kernel_write = bytes(take[:n])
            return n
        raise OSError(errno.ENOSPC, "J24D05 injected full output device")

    error_type = None
    error_errno = None
    with CMPCT(archive) as reader:
        assert reader.verify() == 1
        expected = reader.read(member)
        assert len(expected) == vector["logical_size"]
        assert digest(expected) == vector["logical_sha256"]
        with mode_variant(variant) as chmod_attempts:
            try:
                with ExitStack() as stack:
                    if variant.endswith("-fault"):
                        stack.enter_context(patch("cmpct.reader.os.write", side_effect=fault_write))
                    reader.extractall(output, metadata=False)
            except Exception as exc:
                error_type = type(exc).__name__
                error_errno = getattr(exc, "errno", None)
                assert not isinstance(exc, AssertionError), str(exc)
    after = final.read_bytes()
    stages = sorted(p.name for p in output.iterdir() if ".cmpct-part-" in p.name)
    expect_fault = variant.endswith("-fault")
    expect_value_error = variant == "valueerror"
    assert not chmod_attempts, chmod_attempts
    assert not stages, stages
    if expect_fault:
        assert (error_type, error_errno) == ("OSError", errno.ENOSPC), (variant, error_type, error_errno)
        assert len(write_calls) == 2 and len(actual_kernel_write) >= 1
        assert after == sentinel and final.stat().st_ino == old_inode
        outcome = "SHORT_WRITE_ENOSPC_OLD_DEST_PRESERVED"
    elif expect_value_error:
        assert error_type == "ValueError", (variant, error_type)
        assert after == sentinel and final.stat().st_ino == old_inode
        assert not write_calls
        outcome = "UNEXPECTED_FD_MODE_ERROR_PROPAGATED"
    else:
        assert error_type is None, (variant, error_type)
        assert after == expected
        assert digest(after) == vector["logical_sha256"]
        assert not write_calls
        outcome = "CLEAN_SHA_EXACT"
    return {
        "vector": member,
        "variant": variant,
        "archive_sha256": vector["archive_sha256"],
        "logical_sha256": vector["logical_sha256"],
        "before_sha256": digest(sentinel),
        "after_sha256": digest(after),
        "old_inode": old_inode,
        "new_inode": final.stat().st_ino,
        "write_calls": len(write_calls),
        "actual_kernel_short_write_hex": actual_kernel_write.hex(),
        "error_type": error_type,
        "error_errno": error_errno,
        "path_chmod_attempts": chmod_attempts,
        "remaining_stages": stages,
        "outcome": outcome,
    }


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: j24d05_direct_fd_mode_court.py REPO_ROOT OUTPUT_JSON")
    repo, output = map(Path, sys.argv[1:])
    assert repo.resolve() == Path(__file__).resolve().parent.parent
    import cmpct.reader as mod
    assert repo.resolve() not in Path(mod.__file__).resolve().parents, "source tree import is not an installed-package court"
    fixture = json.loads((repo / "tests/conformance/v24-direct-codecs.json").read_text())
    assert fixture["format_revision"] == 24 and len(fixture["vectors"]) == 3
    rows = []
    with tempfile.TemporaryDirectory(prefix="cmpct-j24d05-") as d:
        root = Path(d)
        for vector in fixture["vectors"]:
            for variant in VARIANTS:
                rows.append(case(root, vector, variant, len(rows)))
    assert len(rows) == 18
    result = {
        "schema": "cmpct-j24d05-r1",
        "head_sha": os.environ.get("J24D05_HEAD_SHA", ""),
        "reader_blob": os.environ.get("J24D05_READER_BLOB", ""),
        "native_fchmod_present": hasattr(os, "fchmod"),
        "platform": platform.platform(),
        "python": sys.version,
        "cases": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"cases": len(rows), "platform": result["platform"],
                      "native_fchmod_present": result["native_fchmod_present"],
                      "outcomes": {k: sum(v["outcome"] == k for v in rows)
                                   for k in sorted({x["outcome"] for x in rows})}}, sort_keys=True))


if __name__ == "__main__":
    main()

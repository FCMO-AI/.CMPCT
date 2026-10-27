"""J24D03 independent composition test for optional fd-mode handling.

Does not modify or import the historical J24D02 scientific instrumentation.
Exercises actual installed CMPCT on frozen, Builder-independent r24 chunk-map archives.
"""
from __future__ import annotations

from contextlib import contextmanager
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

from cmpct.reader import CMPCT


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


@contextmanager
def chmod_variant(variant: str):
    old = getattr(os, "fchmod", None)
    existed = hasattr(os, "fchmod")
    try:
        if variant == "absent":
            if existed:
                delattr(os, "fchmod")
        elif variant in ("oserror", "valueerror"):
            def injected(fd, mode):
                if variant == "oserror":
                    raise OSError("J24D03 synthetic optional mode failure")
                raise ValueError("J24D03 synthetic unexpected mode failure")
            setattr(os, "fchmod", injected)
        elif variant != "native":
            raise AssertionError(f"unknown variant: {variant}")
        yield
    finally:
        if existed:
            setattr(os, "fchmod", old)
        elif hasattr(os, "fchmod"):
            delattr(os, "fchmod")


def exercise(repo: Path):
    fixture = json.loads((repo / "tests/conformance/v24-chunk-maps.json").read_text())
    assert fixture["format_revision"] == 24
    assert len(fixture["vectors"]) == 2
    rows = []
    native_available = hasattr(os, "fchmod")
    with tempfile.TemporaryDirectory(prefix="j24d03-") as td:
        root = Path(td)
        for i, v in enumerate(fixture["vectors"]):
            wire = base64.b64decode(v["archive_base64"], validate=True)
            assert len(wire) == v["archive_bytes"]
            assert sha(wire) == v["archive_sha256"]
            archive = root / f"v{i}.cmpct"
            archive.write_bytes(wire)
            with CMPCT(archive) as r:
                assert r.verify() == 1
                expected = r.read(v["name"])
                assert len(expected) == v["logical_size"]
                assert sha(expected) == v["logical_sha256"]
                for mode in ("native", "absent", "oserror", "valueerror"):
                    out = root / f"v{i}-{mode}"
                    out.mkdir()
                    dest = out / v["name"]
                    sentinel = b"J24D03-OLD-OUTPUT-" + bytes([i])
                    dest.write_bytes(sentinel)
                    before_inode = dest.stat().st_ino
                    error = None
                    with chmod_variant(mode):
                        try:
                            r.extractall(out, metadata=False)
                        except Exception as exc:
                            error = type(exc).__name__
                            assert mode == "valueerror"
                            assert isinstance(exc, ValueError)
                            assert "J24D03 synthetic" in str(exc)
                    after = dest.read_bytes()
                    should_fail = mode == "valueerror"
                    assert (error is not None) == should_fail
                    assert after == (sentinel if should_fail else expected)
                    if should_fail:
                        assert dest.stat().st_ino == before_inode
                    remnants = [p.name for p in out.iterdir() if ".cmpct-part-" in p.name]
                    assert not remnants
                    rows.append(dict(
                        storage_kind=v["storage_kind"],
                        member=v["name"], variant=mode,
                        archive_sha256=v["archive_sha256"],
                        expected_sha256=v["logical_sha256"],
                        actual_sha256=sha(after),
                        old_sha256=sha(sentinel),
                        previous_inode=before_inode,
                        after_inode=dest.stat().st_ino,
                        outcome="REJECT_AND_PRESERVE" if should_fail else "EXACT_OUTPUT",
                        error=error,
                        remainders=remnants,
                    ))
    assert len(rows) == 8
    return {"schema": "cmpct-j24d03-mode-r1",
            "os_name": os.name, "native_fchmod_available": native_available,
            "cases_total": len(rows), "cases": rows}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: j24d03_mode_composition_court.py REPO_ROOT OUTPUT_JSON")
    repo, output = map(Path, sys.argv[1:])
    import cmpct.reader as installed
    assert repo.resolve() not in Path(installed.__file__).resolve().parents
    receipt = exercise(repo)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"cases": receipt["cases_total"], "native_fchmod_available": receipt["native_fchmod_available"], "outcomes": [c["outcome"] for c in receipt["cases"]]}, sort_keys=True))

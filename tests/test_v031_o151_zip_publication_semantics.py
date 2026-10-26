"""O151: exact-source cross-owner ZIP successful-publication semantics.

One unmodified instrument, three actual installed engines, two POSIX hosts.
Research evidence only: this is NOT the frozen release-parity benchmark.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import zipfile

from cmpct.reader import CMPCT
import cmpct.reader

EXPECTED = {
    "o140": {"new_mode": 0o644, "new_stage_mode": None,
             "symlink_remains": True, "old_referent_changed": True, "stage_count": 0},
    "o149": {"new_mode": 0o644, "new_stage_mode": 0o644,
             "symlink_remains": False, "old_referent_changed": False, "stage_count": 2},
    "o150": {"new_mode": 0o600, "new_stage_mode": 0o600,
             "symlink_remains": False, "old_referent_changed": False, "stage_count": 2},
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_zip(path: Path) -> dict:
    assert zipfile.is_zipfile(path), f"invalid ZIP: {path}"
    with zipfile.ZipFile(path) as zf:
        assert zf.namelist() == ["raw.bin"], zf.namelist()
        raw = zf.read("raw.bin")
        assert raw == bytes(range(64)), (len(raw), sha(raw))
        assert zf.testzip() is None
    return {"sha256": sha(path.read_bytes()), "size": path.stat().st_size}


def main() -> None:
    engine = os.environ["O151_ENGINE"]
    expected = EXPECTED[engine]
    fixture = json.loads(Path(os.environ["CMPCT_FIXTURE_JSON"]).read_text())
    vec = next(v for v in fixture["vectors"] if v["name"] == "raw.bin")
    raw = base64.b64decode(vec["archive_base64"])
    assert sha(raw) == vec["archive_sha256"], "source fixture fingerprint mismatch"
    module = Path(cmpct.reader.__file__).resolve()
    workspace = Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    assert not module.is_relative_to(workspace), (module, workspace)
    source_object_sha = sha(module.read_bytes())

    with tempfile.TemporaryDirectory(prefix="o151-zip-publish-") as name:
        root = Path(name)
        source = root / "source.cmpct"
        source.write_bytes(raw)
        captures: list[dict] = []
        real_replace = os.replace

        def witness(src, dst, *args, **kwargs):
            candidate = Path(src)
            public = Path(dst)
            assert candidate.is_file(), f"staging absent before replace: {candidate}"
            captures.append({
                "destination": public.name,
                "staging_mode": stat.S_IMODE(candidate.stat().st_mode),
                "staging_bytes": candidate.stat().st_size,
                "staging_sha256": sha(candidate.read_bytes()),
                "staging_is_zip": zipfile.is_zipfile(candidate),
            })
            return real_replace(src, dst, *args, **kwargs)

        old_umask = os.umask(0o022)
        os.replace = witness
        try:
            new = root / "new.zip"
            with CMPCT(source) as reader:
                assert reader.read("raw.bin") == bytes(range(64))
                reader.export_zip(new)
            new_zip = verify_zip(new)
            new_mode = stat.S_IMODE(new.stat().st_mode)
            assert len(captures) == (0 if engine == "o140" else 1), captures
            stage_mode = captures[0]["staging_mode"] if captures else None

            referent = root / "referent.zip"
            with zipfile.ZipFile(referent, "w", compression=zipfile.ZIP_STORED) as zf:
                zf.writestr("old.txt", b"OLD FILE MUST BE ACCOUNTED FOR")
            old_referent_bytes = referent.read_bytes()
            old_referent_inode = referent.stat().st_ino
            link = root / "alias.zip"
            link.symlink_to("referent.zip")
            assert link.is_symlink()
            with CMPCT(source) as reader:
                reader.export_zip(link)

            symlink_remains = link.is_symlink()
            old_referent_changed = referent.read_bytes() != old_referent_bytes
            assert referent.stat().st_ino == old_referent_inode
            link_zip = verify_zip(link)
        finally:
            os.replace = real_replace
            os.umask(old_umask)

        assert source.read_bytes() == raw, "CMPCT source mutated"
        actual = {
            "new_mode": new_mode,
            "new_stage_mode": stage_mode,
            "symlink_remains": symlink_remains,
            "old_referent_changed": old_referent_changed,
            "stage_count": len(captures),
        }
        record = {
            "scope": "O151 independent successful ZIP-export filesystem semantics",
            "engine": engine,
            "host": os.uname().sysname,
            "source_sha256": sha(raw),
            "installed_reader_sha256": source_object_sha,
            "new_zip": new_zip,
            "symlink_zip": link_zip,
            "old_referent_sha256": sha(old_referent_bytes),
            "final_referent_sha256": sha(referent.read_bytes()),
            "captured_replaces": captures,
            "actual": actual,
            "predicted": expected,
        }
        Path(os.environ["O151_RESULT_PATH"]).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        print("O151_RESULT=" + json.dumps(record, sort_keys=True), flush=True)
        assert actual == expected, f"PREREGISTERED PREDICTION FALSIFIED: {actual} != {expected}"
        assert all(x["staging_is_zip"] for x in captures), "invalid staged ZIP before publish"


if __name__ == "__main__":
    main()

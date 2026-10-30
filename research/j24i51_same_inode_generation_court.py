#!/usr/bin/env python3
"""J24I51 signed-journal generation court: identical path/inode, different verified members.

Research-only. Public Writer API; independent immutable revision-24 WAV vector.
Do not interpret separate native pathname verification as a Python integration.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from cmpct.codec import FTR, FMAGIC
from cmpct.reader import CMPCT
from cmpct import transactions as tx

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "native/cmpct-core/target/release/cmpct-native"
VECTOR = ROOT / "tests/conformance/v24-wavflac.json"


def native(command: str, path: Path):
    p = subprocess.run([str(CLI), command, str(path)], capture_output=True, check=False)
    assert p.returncode == 0, (command, p.returncode, p.stderr.decode(errors="replace"))
    return json.loads(p.stdout)


def python_live(path: Path, expected: set[str], depth: int) -> int:
    with CMPCT(path) as ar:
        assert ar.delta_depth == depth, (ar.delta_depth, depth)
        assert set(ar.by) == expected, (sorted(ar.by), sorted(expected))
        assert ar.verify() == len(expected)
        return ar.latest_footer_pos


def main():
    vector = json.loads(VECTOR.read_text())["vector"]
    raw = base64.b64decode(vector["archive_base64"])
    assert len(raw) == vector["archive_bytes"]
    assert hashlib.sha256(raw).hexdigest() == vector["archive_sha256"]
    assert CLI.is_file()
    out = Path(os.environ.get("J24I51_EVIDENCE", "evidence/j24i51"))
    out.mkdir(parents=True, exist_ok=True)
    new_name = "j24i51-new-member.bin"
    assert new_name != vector["name"]

    with tempfile.TemporaryDirectory(prefix="cmpct-j24i51-") as d:
        root = Path(d)
        archive = root / "same-path-same-inode.cmpct"
        archive.write_bytes(raw)
        original_inode = archive.stat().st_ino
        assert python_live(archive, {vector["name"]}, 0) > 0
        assert [row["path"] for row in native("list", archive)] == [vector["name"]]
        assert native("verify", archive) == {"revision": 24, "verified": 1}

        source = root / "update.bin"
        source.write_bytes(hashlib.sha256(b"J24I51-public-signed-writer").digest() * 32)
        result = tx.append_update(archive, new_name, source)
        assert result["member"] == new_name
        after_put = archive.read_bytes()
        assert after_put.startswith(raw) and len(after_put) > len(raw)
        assert archive.stat().st_ino == original_inode
        python_live(archive, {vector["name"], new_name}, 1)
        assert native("verify", archive) == {"revision": 24, "verified": 1}
        assert [row["path"] for row in native("list", archive)] == [vector["name"]]

        tx.append_delete(archive, vector["name"])
        after_delete = archive.read_bytes()
        assert after_delete.startswith(after_put) and len(after_delete) > len(after_put)
        assert archive.stat().st_ino == original_inode
        assert hashlib.sha256(after_delete).hexdigest() != vector["archive_sha256"]
        footer = FTR.unpack_from(after_delete, len(after_delete) - FTR.size)
        assert footer[0] == FMAGIC and footer[1] == 1 and footer[7] > 0
        footer_pos = python_live(archive, {new_name}, 2)
        assert footer_pos == len(after_delete) - FTR.size
        with CMPCT(archive) as latest:
            assert latest.read(new_name) == source.read_bytes()
        # Both operations now SUCCEED on the SAME inode/path, but differ in member identity.
        assert native("verify", archive) == {"revision": 24, "verified": 1}
        native_names = [row["path"] for row in native("list", archive)]
        assert native_names == [vector["name"]]
        assert native_names != [new_name]

        shutil.copyfile(archive, out / "same-inode-signed-journal.cmpct")
        (out / "original-wav.cmpct").write_bytes(raw)
        receipt = {
            "schema": "cmpct-j24i51-native-journal-generation-v1",
            "source_sha": os.environ.get("EVIDENCE_HEAD", "local-unbound"),
            "original_physical_sha256": vector["archive_sha256"],
            "final_physical_sha256": hashlib.sha256(after_delete).hexdigest(),
            "original_inode_stable": True,
            "same_path": True,
            "public_writer_operations": ["put", "delete"],
            "authenticated_delta_depth": 2,
            "signed_footer_position": footer_pos,
            "native_verify": {"status": "SUCCESS", "verified": 1, "member": vector["name"]},
            "python_verify": {"status": "SUCCESS", "verified": 1, "member": new_name},
            "conclusion": "both-success-but-different-committed-generation",
            "scope": "research-only, no product ABI/format/release claim",
        }
        (out / "result.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()

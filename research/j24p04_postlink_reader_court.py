#!/usr/bin/env python3
"""J24P04: authentic installed Reader, direct-fd link versus post-link namespace mutation.

The only hook schedules a separate same-UID actor AFTER the original real Linux
linkat publication has succeeded. No syscall, Reader checksum, or decoder is mocked.
This distinguishes linkat linearization correctness from a mutable path at API return.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from j24f04_raw_chunk_immutable_transfer import independent_revision24, blob_sha


def sha(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()


def ident(path: Path) -> tuple[int, int]:
    st = path.stat(follow_symlinks=False)
    return st.st_dev, st.st_ino


def actor_command(leaf: Path, quarantine: Path, size: int) -> int:
    assert size > 0
    os.rename(leaf, quarantine)
    with leaf.open("xb") as handle:
        handle.write(b"F" * size)
    assert leaf.stat().st_size == size
    assert quarantine.stat().st_size == size
    print(json.dumps({
        "pid": os.getpid(), "uid": os.geteuid(),
        "quarantine_inode": ident(quarantine),
        "replacement_inode": ident(leaf),
        "replacement_sha": sha(leaf.read_bytes()),
        "quarantine_sha": sha(quarantine.read_bytes()),
    }), flush=True)
    return 0


def one_case(root: Path, kind: int, mode: int, hostile: bool):
    import cmpct.reader as module

    root.mkdir()
    chunks = [hashlib.shake_256(f"j24p04-{kind}-{i}".encode()).digest(72191 + i * 257) for i in range(3)]
    original = b"".join(chunks)
    name, archive, _ = independent_revision24(chunks, kind)
    source = root / "source.cmpct"
    source.write_bytes(archive)
    out = root / "output"
    out.mkdir(mode=0o700)
    leaf = out / name
    quarantine = out / "quarantined-authenticated-inode"
    seen = []
    old_publisher = module._publish_unnamed_chunk_fd

    def actual_link_then_optional_actor(fd: int, parentfd: int, member_name: str):
        assert member_name == name
        st = os.fstat(fd)
        fd_ident = (st.st_dev, st.st_ino)
        assert st.st_nlink == 0, "output fd must still be anonymous before linking"
        assert os.pread(fd, len(original), 0) == original
        how = old_publisher(fd, parentfd, member_name)
        assert ident(leaf) == fd_ident, "real link did not publish the authenticated fd"
        assert leaf.read_bytes() == original
        event = {
            "source_fd_inode": fd_ident,
            "link_inode": ident(leaf),
            "linked_sha": sha(leaf.read_bytes()),
            "link_method": how,
            "source_fd_sha": sha(os.pread(fd, len(original), 0)),
        }
        if hostile:
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()),
                 "--actor", str(leaf), str(quarantine), str(len(original))],
                capture_output=True, text=True, timeout=15, check=True,
            )
            actor = json.loads(result.stdout.strip())
            assert actor["uid"] == os.geteuid()
            assert actor["pid"] != os.getpid()
            assert tuple(actor["quarantine_inode"]) == fd_ident
            assert tuple(actor["replacement_inode"]) != fd_ident
            assert quarantine.read_bytes() == original
            assert leaf.read_bytes() == b"F" * len(original)
            assert os.pread(fd, len(original), 0) == original
            event["actor"] = actor
        seen.append(event)
        return how

    out.chmod(mode)
    err = None
    try:
        with module.CMPCT(source) as reader:
            assert reader.by[name][6][0] == kind
            assert reader.by[name][4] == len(original)
            assert sha(reader.read(name)) == sha(original)
            module._publish_unnamed_chunk_fd = actual_link_then_optional_actor
            try:
                reader.extractall(out, metadata=False)
            except Exception as exc:
                err = type(exc).__name__ + ": " + str(exc)
            finally:
                module._publish_unnamed_chunk_fd = old_publisher

        assert len(seen) == 1, "not the fresh anonymous-fd publication branch"
        assert err is None, "extractall unexpectedly refused: " + str(err)
        final_id = ident(leaf)
        final_sha = sha(leaf.read_bytes())
        assert seen[0]["source_fd_inode"] == seen[0]["link_inode"]
        if hostile:
            assert final_id != tuple(seen[0]["source_fd_inode"])
            assert final_sha != sha(original)
            assert quarantine.read_bytes() == original
        else:
            assert final_id == tuple(seen[0]["source_fd_inode"])
            assert final_sha == sha(original)
            assert not quarantine.exists()
        return {
            "kind": kind, "directory_mode": oct(mode), "hostile": hostile,
            "extract_returned_success": err is None,
            "source_archive_sha": sha(archive), "expected_logical_sha": sha(original),
            "final_sha": final_sha, "final_inode": final_id,
            "final_is_original_verified_inode": final_id == tuple(seen[0]["source_fd_inode"]),
            "publication": seen[0],
            "decision": "SUCCESS_RETURN_FOREIGN_PATH" if hostile else "SUCCESS_RETURN_AUTHENTIC_PATH",
        }
    finally:
        module._publish_unnamed_chunk_fd = old_publisher
        out.chmod(0o700)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--actor", nargs=3)
    parser.add_argument("--expected-blob")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.actor is not None:
        return actor_command(Path(args.actor[0]), Path(args.actor[1]), int(args.actor[2]))
    if not args.expected_blob or args.output is None:
        parser.error("--expected-blob and --output required")
    assert sys.platform.startswith("linux") and hasattr(os, "O_TMPFILE")
    import cmpct.reader as module
    installed = Path(module.__file__).resolve()
    assert installed.is_relative_to(Path(sys.prefix)), ("not independently installed", installed)
    assert blob_sha(installed.read_bytes()) == args.expected_blob, "Reader source identity drift"
    assert os.geteuid() != 0, "hosted court must be run as nonroot"
    cases = []
    with tempfile.TemporaryDirectory(prefix="cmpct-j24p04-") as td:
        for kind in (1, 5):
            for mode in (0o700, 0o300):
                for hostile in (False, True):
                    root = Path(td) / f"{kind}-{mode:o}-{int(hostile)}"
                    case = one_case(root, kind, mode, hostile)
                    cases.append(case)
                    print("J24P04_CASE=" + json.dumps(case, sort_keys=True), flush=True)
    assert len(cases) == 8
    assert sum(c["decision"] == "SUCCESS_RETURN_FOREIGN_PATH" for c in cases) == 4
    assert sum(c["decision"] == "SUCCESS_RETURN_AUTHENTIC_PATH" for c in cases) == 4
    record = {
        "schema": "j24p04-postlink-namespace-v1",
        "git_head": os.getenv("EVIDENCE_HEAD"),
        "installed_reader_blob": args.expected_blob,
        "host": sys.platform, "uid": os.geteuid(),
        "cases": cases,
        "decision": "DIRECT_FD_LINK_AUTHENTIC_AT_SYSCALL_NOT_PERPETUAL_PATH_CUSTODY",
        "nonclaims": [
            "not a linkat source-identity bypass", "not a CMPCT codec or archive defect",
            "no race probability claimed", "no existing-target overwrite fix",
            "not cross-platform", "not a release or product performance measurement",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf8")
    print("J24P04_DECISION=" + record["decision"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

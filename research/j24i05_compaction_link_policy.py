"""J24I05: physical, installed-source r24 compaction symlink-target falsifier.

Scientific research only. Never disables the extraction safety guard.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import compact_archive


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict:
    outcomes = []
    with tempfile.TemporaryDirectory(prefix="j24i05-") as work:
        root = Path(work)
        external = root / "external"
        external.mkdir()
        sentinel = external / "sentinel.txt"
        sentinel.write_bytes(b"never change external sentinel\n")
        sentinel_sha = sha(sentinel)
        cases = (
            ("plain", None, False),
            ("safe-relative", "owner.bin", False),
            ("absolute-target", str(sentinel.resolve()), True),
            ("parent-relative", "../external/sentinel.txt", True),
        )
        for name, target, expected_rejection in cases:
            source_tree = root / (name + "-source")
            source_tree.mkdir()
            payload = b"J24I05 owner bytes: exact 24-era file tree\n"
            (source_tree / "owner.bin").write_bytes(payload)
            if target is not None:
                (source_tree / "link").symlink_to(target)
                assert os.readlink(source_tree / "link") == target
            src = root / (name + ".cmpct")
            dst = root / (name + "-compacted.cmpct")
            Builder(source_tree, workers=1, reproducible=True).build(src)
            assert src.exists()
            src_hash = sha(src)
            with CMPCT(src) as reader:
                assert reader.read("owner.bin") == payload
                assert reader.verify() == (2 if target is not None else 1)
                if target is not None:
                    assert reader.read("link") == os.fsencode(target)
            failure = None
            try:
                compact_archive(src, dst)
            except Exception as exc:
                failure = type(exc).__name__ + ": " + str(exc)
            assert sha(src) == src_hash, "compaction mutated source archive"
            assert sha(sentinel) == sentinel_sha, "external sentinel was modified"
            # Preserve the genuine r24 source/output bytes so a detached auditor can
            # verify physical index and logical-target identity without trusting this Reader.
            if os.environ.get("CMPCT_J24I05_ARCHIVE_DIR"):
                artifacts = Path(os.environ["CMPCT_J24I05_ARCHIVE_DIR"])
                artifacts.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, artifacts / (name + "-source.cmpct"))
                if dst.exists():
                    shutil.copyfile(dst, artifacts / (name + "-compacted.cmpct"))
            if expected_rejection:
                assert failure is not None, f"{name}: restricted target unexpectedly compacted"
                assert "unsafe symlink target" in failure, (name, failure)
                assert not dst.exists(), f"{name}: failed compaction published destination"
            else:
                assert failure is None, (name, failure)
                assert dst.exists(), name
                with CMPCT(dst) as reader:
                    assert reader.read("owner.bin") == payload
                    assert reader.verify() == (2 if target is not None else 1)
                    if target is not None:
                        assert reader.read("link") == os.fsencode(target)
            outcomes.append({
                "case": name, "target": target, "expected_rejection": expected_rejection,
                "source_bytes": src.stat().st_size, "source_sha256": src_hash,
                "output_sha256": sha(dst) if dst.exists() else None,
                "exception": failure, "conclusion": "EXPECTED_POLICY_REJECTION" if failure else "COMPACTED_EXACTLY"
            })
    return {
        "schema": "j24i05-physical-source-compaction-v1",
        "published_source": "80c358f8824ec1b20d349c92ed94c898090969b0",
        "format": 24, "cases": outcomes,
        "decision": "COMPACTION_POLICY_INCOMPLETENESS_CONFIRMED"
    }


if __name__ == "__main__":
    result = run()
    raw = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if os.environ.get("CMPCT_J24I05_RECEIPT"):
        Path(os.environ["CMPCT_J24I05_RECEIPT"]).write_text(raw, encoding="utf-8")
    print(raw)

from __future__ import annotations

"""Reusable bounded process executor for the supported v0.30 PrefixGraph lifetime boundary.

This module is a productization *candidate*, not a shipping dispatch decision. It extracts the disposable-process
mechanism that earned `ISOLATION_LEVEL15_DEBT_REHAB_SUPPORTED` out of benchmark-only monkeypatch code so the
canonical builder can be reviewed against a small explicit boundary. Nothing imports or installs this executor into
the release product yet.

The executor intentionally implements only the tiny context-manager/``submit`` surface used by canonical
PrefixGraph scheduling. ``submit`` is synchronous: the child must finish and exit before the parent proceeds. That
lifetime barrier is the evidenced memory mechanism and may not be relaxed into overlap without a new experiment.
"""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


SUPPORTED_PREFIX_LEVEL = 15
DEFAULT_CHILD_TIMEOUT_S = 180.0
EXPECTED_OWNER_MODULE = "experiments._v030_canonical_prefixgraph"
EXPECTED_BUILD_NAME = "build"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


class PrefixGraphProcessError(RuntimeError):
    pass


class _ImmediateFuture:
    def __init__(self, value: Any):
        self._value = value

    def result(self, timeout: float | None = None):
        del timeout
        return self._value


class PrefixGraphProcessExecutor:
    """One-shot executor matching the canonical PrefixGraph ``submit`` seam.

    Only the exact private canonical PrefixGraph ``build(source, archive)`` callable is accepted. The child is
    launched with ``sys.executable`` and no shell, receives only explicit filesystem paths, is bounded by a wall
    timeout, and must produce a self-authenticating JSON receipt matching the physical archive it wrote.
    """

    def __init__(self, *, timeout_s: float = DEFAULT_CHILD_TIMEOUT_S):
        timeout_s = float(timeout_s)
        if not (0.0 < timeout_s <= DEFAULT_CHILD_TIMEOUT_S):
            raise ValueError(f"timeout_s must be in (0, {DEFAULT_CHILD_TIMEOUT_S}]")
        self.timeout_s = timeout_s
        self._submitted = False
        self.last_receipt: dict | None = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    @staticmethod
    def _validate_callable(fn) -> None:
        owner = getattr(fn, "__module__", "")
        name = getattr(fn, "__name__", "")
        if owner != EXPECTED_OWNER_MODULE or name != EXPECTED_BUILD_NAME:
            raise PrefixGraphProcessError(
                f"unexpected PrefixGraph process callable: {owner}.{name}; "
                f"expected {EXPECTED_OWNER_MODULE}.{EXPECTED_BUILD_NAME}"
            )

    def submit(self, fn, *args, **kwargs):
        if self._submitted:
            raise PrefixGraphProcessError("PrefixGraph process executor is one-shot")
        self._submitted = True
        self._validate_callable(fn)
        if len(args) != 2 or kwargs:
            raise PrefixGraphProcessError("expected build(source, archive) call shape")
        source, archive = map(Path, args)
        if not source.is_dir():
            raise PrefixGraphProcessError(f"PrefixGraph source is not a directory: {source}")
        archive.parent.mkdir(parents=True, exist_ok=True)
        if archive.exists() or archive.is_symlink():
            archive.unlink()

        env = os.environ.copy()
        root = Path(__file__).resolve().parents[1]
        env["PYTHONPATH"] = str(root) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        cmd = [
            sys.executable,
            "-m",
            "experiments.entropygraph_v030_prefixgraph_process_executor",
            "--child",
            "--source",
            os.fspath(source),
            "--archive",
            os.fspath(archive),
        ]
        try:
            completed = subprocess.run(
                cmd,
                cwd=root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=self.timeout_s,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            archive.unlink(missing_ok=True)
            raise PrefixGraphProcessError(f"PrefixGraph child launch failed: {exc}") from exc

        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        if completed.returncode != 0 or not lines:
            archive.unlink(missing_ok=True)
            tail = completed.stderr[-2000:]
            raise PrefixGraphProcessError(
                f"PrefixGraph child failed rc={completed.returncode}: {tail}"
            )
        try:
            receipt = json.loads(lines[-1])
        except Exception as exc:
            archive.unlink(missing_ok=True)
            raise PrefixGraphProcessError("PrefixGraph child emitted invalid terminal receipt") from exc

        if receipt.get("semantic_owner") != EXPECTED_OWNER_MODULE:
            archive.unlink(missing_ok=True)
            raise PrefixGraphProcessError(f"PrefixGraph child semantic-owner drift: {receipt!r}")
        if int(receipt.get("prefix_level", -1)) != SUPPORTED_PREFIX_LEVEL:
            archive.unlink(missing_ok=True)
            raise PrefixGraphProcessError(f"PrefixGraph child level drift: {receipt!r}")
        if not archive.is_file():
            raise PrefixGraphProcessError("PrefixGraph child reported success without archive")
        if int(receipt.get("archive_bytes", -1)) != archive.stat().st_size:
            archive.unlink(missing_ok=True)
            raise PrefixGraphProcessError("PrefixGraph child archive-size accounting mismatch")
        if receipt.get("archive_sha256") != _sha256(archive):
            archive.unlink(missing_ok=True)
            raise PrefixGraphProcessError("PrefixGraph child archive SHA-256 mismatch")
        stats = receipt.get("stats")
        if not isinstance(stats, dict):
            archive.unlink(missing_ok=True)
            raise PrefixGraphProcessError("PrefixGraph child omitted build statistics")
        self.last_receipt = receipt
        return _ImmediateFuture(stats)


def _level15_codec(pg):
    def codec(prefix: bytes):
        dictionary = pg.zstd.ZstdCompressionDict(prefix, dict_type=pg.zstd.DICT_TYPE_RAWCONTENT)
        compressor = pg.zstd.ZstdCompressor(level=SUPPORTED_PREFIX_LEVEL, dict_data=dictionary)
        return compressor, dictionary
    return codec


def _child(source: Path, archive: Path) -> None:
    # Import only inside the child so importing this candidate module cannot initialize or mutate canonical state.
    from experiments import entropygraph_v030_canonical_final as canonical

    pg = canonical.RC.PG
    isolation = canonical.PROFILE_ISOLATION
    if pg is not isolation.PG or pg.__name__ != EXPECTED_OWNER_MODULE:
        raise PrefixGraphProcessError("PrefixGraph child canonical semantic-owner mismatch")

    original_codec = pg._prefix_codec
    pg._prefix_codec = _level15_codec(pg)
    try:
        stats = dict(pg.build(Path(source), Path(archive)))
    finally:
        pg._prefix_codec = original_codec

    print(json.dumps({
        "schema": "cmpct-v030-prefixgraph-process-executor-v1",
        "semantic_owner": pg.__name__,
        "prefix_level": SUPPORTED_PREFIX_LEVEL,
        "archive_bytes": Path(archive).stat().st_size,
        "archive_sha256": _sha256(Path(archive)),
        "stats": stats,
    }, separators=(",", ":"), default=str), flush=True)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    if not args.child or args.source is None or args.archive is None:
        parser.error("this module is executable only through the bounded --child contract")
    _child(args.source, args.archive)


if __name__ == "__main__":
    main()

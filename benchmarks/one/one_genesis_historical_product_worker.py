from __future__ import annotations

"""Fresh-process raw measurement worker for frozen Genesis comparators.

This wrapper does not generate workloads, compare contenders, score rows, or select a
winner. It invokes exact product modules from caller-supplied frozen checkouts and keeps
unsupported historical capability explicit rather than emulating it.
"""

import argparse
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any

SCHEMA = "cmpct-one-genesis-historical-worker-v1"
FROZEN = {
    "v029": {
        "sha": "02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d",
        "module": "experiments/entropygraph_v029_residual_strict.py",
        "selective": False,
    },
    "v030": {
        "sha": "f4b158a55a08b9b18b50e4e4abe4b9251048c772",
        "module": "experiments/entropygraph_v030_release_product.py",
        "selective": True,
    },
}
FORBIDDEN_IMPORT_FRAGMENTS = ("neutral_hostile", "resemblance_hostile", "one_genesis_gate_readiness")


def _peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def _git_head(checkout: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
    ).strip()


def _forbidden_imports() -> list[str]:
    return sorted(
        name for name in sys.modules
        if any(fragment in name.lower() for fragment in FORBIDDEN_IMPORT_FRAGMENTS)
    )


def _authorize(contender: str, checkout: Path, transfer_fixture: bool) -> dict[str, Any]:
    spec = FROZEN[contender]
    checkout = checkout.resolve()
    actual = _git_head(checkout)
    if actual != spec["sha"]:
        raise RuntimeError(
            f"{contender} checkout SHA mismatch: expected {spec['sha']}, got {actual}"
        )
    if transfer_fixture:
        return {
            "transfer_fixture": True,
            "production_authorized": False,
            "frozen_source_sha": actual,
        }
    if os.environ.get("CMPCT_GENESIS_REAL_GATE_AUTHORIZED") != "1":
        raise RuntimeError("production historical worker requires executor authorization")
    return {
        "transfer_fixture": False,
        "production_authorized": True,
        "frozen_source_sha": actual,
    }


def _load_surface(contender: str, checkout: Path):
    module_path = checkout / str(FROZEN[contender]["module"])
    if not module_path.is_file():
        raise RuntimeError(f"frozen product module missing: {module_path}")
    # Historical modules use local imports. Put the frozen checkout first so the current
    # research branch cannot satisfy those imports accidentally.
    checkout_s = str(checkout)
    experiments_s = str(checkout / "experiments")
    sys.path.insert(0, experiments_s)
    sys.path.insert(0, checkout_s)
    name = f"cmpct_genesis_frozen_{contender}_{FROZEN[contender]['sha'][:12]}"
    module_spec = importlib.util.spec_from_file_location(name, module_path)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"cannot load frozen product module: {module_path}")
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[name] = module
    module_spec.loader.exec_module(module)
    return module


def _timed(call):
    cpu0 = time.process_time()
    wall0 = time.perf_counter()
    value = call()
    row = {
        "measured": True,
        "cpu_s": time.process_time() - cpu0,
        "wall_s": time.perf_counter() - wall0,
        "peak_rss_bytes": _peak_rss_bytes(),
        "process_boundary": "fresh-process",
    }
    if row["cpu_s"] < 0 or row["wall_s"] < 0 or row["peak_rss_bytes"] < 0:
        raise RuntimeError("negative resource measurement")
    return value, row


def _regular_file_digests(root: Path) -> dict[str, tuple[int, str]]:
    rows: dict[str, tuple[int, str]] = {}
    for path in root.rglob("*"):
        info = path.lstat()
        if stat.S_ISREG(info.st_mode):
            data = path.read_bytes()
            rows[path.relative_to(root).as_posix()] = (len(data), sha256(data).hexdigest())
    return dict(sorted(rows.items()))


def _assert_regular_tree_exact(source: Path, extracted: Path) -> int:
    expected = _regular_file_digests(source)
    actual = _regular_file_digests(extracted)
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        changed = sorted(
            rel for rel in set(expected) & set(actual) if expected[rel] != actual[rel]
        )
        raise RuntimeError(
            f"whole reconstruction mismatch: missing={missing[:5]} extra={extra[:5]} changed={changed[:5]}"
        )
    return sum(size for size, _digest in expected.values())


def _verify_ok(result: Any) -> bool:
    if isinstance(result, dict):
        if "ok" in result:
            return bool(result["ok"])
        # Some historical verifier variants return an evidence dict and raise on failure.
        return True
    return result is None or result is True


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return repr(value)


def _build(surface, root: Path, archive: Path) -> dict[str, Any]:
    def action():
        archive.parent.mkdir(parents=True, exist_ok=True)
        stats = surface.build(root, archive)
        if not archive.is_file():
            raise RuntimeError("historical build did not produce persistent archive")
        return stats

    stats, timing = _timed(action)
    data = archive.read_bytes()
    return {
        "phase": "creation",
        **timing,
        "stored_bytes": len(data),
        "archive_sha256": sha256(data).hexdigest(),
        "product_stats": _json_safe(stats),
    }


def _whole(surface, root: Path, archive: Path) -> dict[str, Any]:
    def action():
        verified = surface.strong_verify(archive)
        if not _verify_ok(verified):
            raise RuntimeError(f"historical strong_verify failed: {verified!r}")
        with tempfile.TemporaryDirectory(prefix="cmpct-genesis-historical-extract-") as td:
            dst = Path(td) / "tree"
            dst.mkdir()
            surface.extract(archive, dst)
            returned = _assert_regular_tree_exact(root, dst)
        return verified, returned

    (verified, returned), timing = _timed(action)
    return {
        "phase": "whole_read",
        **timing,
        "returned_bytes": returned,
        "exact": True,
        "strong_verify": _json_safe(verified),
    }


def _selective(contender: str, surface, root: Path, archive: Path, member: str) -> dict[str, Any]:
    if not bool(FROZEN[contender]["selective"]):
        raise RuntimeError(f"{contender} has no proven frozen selective member surface")
    source = root / Path(member)
    if not source.is_file() or not stat.S_ISREG(source.lstat().st_mode):
        raise RuntimeError("selected member is not a regular executor-owned source file")
    expected = source.read_bytes()

    def action():
        result = surface.read_member_with_stats(archive, member)
        if not isinstance(result, tuple) or len(result) != 2:
            raise RuntimeError("historical selective surface returned unexpected shape")
        return result

    (data, stats), timing = _timed(action)
    if not isinstance(data, (bytes, bytearray)):
        raise RuntimeError("historical selective surface did not return bytes")
    if bytes(data) != expected:
        raise RuntimeError("historical selective reconstruction mismatch")
    return {
        "phase": "selective_access",
        **timing,
        "member": member,
        "requested_bytes": len(expected),
        "returned_bytes": len(data),
        "exact": True,
        "product_access_stats": _json_safe(stats),
    }


def run(
    *,
    contender: str,
    mode: str,
    checkout: Path,
    root: Path,
    archive: Path,
    member: str | None,
    transfer_fixture: bool,
) -> dict[str, Any]:
    checkout = checkout.resolve()
    root = root.resolve()
    archive = archive.resolve()
    if contender not in FROZEN:
        raise RuntimeError(f"unknown frozen contender: {contender}")
    if not root.is_dir():
        raise RuntimeError("input root is not a directory")
    if mode != "build" and not archive.is_file():
        raise RuntimeError("archive does not exist for read phase")
    if _forbidden_imports():
        raise RuntimeError("Genesis workload machinery already imported")

    authorization = _authorize(contender, checkout, transfer_fixture)
    surface = _load_surface(contender, checkout)
    forbidden = _forbidden_imports()
    if forbidden:
        raise RuntimeError(f"historical product imported Genesis workload machinery: {forbidden}")

    if mode == "build":
        phase = _build(surface, root, archive)
    elif mode == "whole":
        phase = _whole(surface, root, archive)
    elif mode == "selective":
        if not member:
            raise RuntimeError("selective mode requires --member")
        phase = _selective(contender, surface, root, archive, member)
    else:
        raise RuntimeError(f"unknown mode: {mode}")

    forbidden = _forbidden_imports()
    if forbidden:
        raise RuntimeError(f"historical product imported Genesis workload machinery: {forbidden}")
    return {
        "schema": SCHEMA,
        "contender": contender,
        "frozen_source_sha": FROZEN[contender]["sha"],
        "frozen_product_module": FROZEN[contender]["module"],
        "authorization": authorization,
        "genesis_inputs_generated": False,
        "comparison_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
        **phase,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contender", choices=tuple(FROZEN), required=True)
    parser.add_argument("--mode", choices=("build", "whole", "selective"), required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--member")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--transfer-fixture", action="store_true")
    args = parser.parse_args()
    result = run(
        contender=args.contender,
        mode=args.mode,
        checkout=args.checkout,
        root=args.root,
        archive=args.archive,
        member=args.member,
        transfer_fixture=args.transfer_fixture,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

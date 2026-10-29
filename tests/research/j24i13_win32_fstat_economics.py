"""J24I13: same-input Win32 source-identity cost probe, not a product change.

The two sides intentionally use identical file content and full Python stat results.
B is NOT a safe replacement for nofollow source admission: see symlink witness.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import stat
import sys
import tempfile
import time
import traceback
from pathlib import Path

SCHEMA = "j24i13-win32-fstat-economics-v1"
ROUNDS = 4


def corpus(root: Path) -> dict[str, list[Path]]:
    unique = root / "unique"
    linked = root / "linked"
    unique.mkdir()
    linked.mkdir()
    for i in range(256):
        value = hashlib.sha256(("J24I13-A-" + str(i)).encode()).digest()
        value += hashlib.sha256(("J24I13-B-" + str(i)).encode()).digest()
        (unique / f"independent-{i:04d}.bin").write_bytes(value)
    data = bytes(range(256)) * 16 + b"identity-is-not-byte-equality"
    owner = linked / "a_owner.bin"
    alias = linked / "b_alias.bin"
    copy = linked / "c_same_bytes_copy.bin"
    owner.write_bytes(data)
    os.link(owner, alias)
    copy.write_bytes(data)
    paths = [owner, alias, copy]
    witnesses = [os.stat(path, follow_symlinks=False) for path in paths]
    if ((witnesses[0].st_dev, witnesses[0].st_ino) !=
        (witnesses[1].st_dev, witnesses[1].st_ino)):
        raise AssertionError("host failed to create real hardlink")
    if ((witnesses[0].st_dev, witnesses[0].st_ino) ==
        (witnesses[2].st_dev, witnesses[2].st_ino)):
        raise AssertionError("host copy is unexpectedly linked")
    return {"unique256": sorted(unique.iterdir()), "topology3": paths}


def witness_symlink(root: Path) -> dict:
    link = root / "followed-symlink"
    owner = root / "linked" / "a_owner.bin"
    try:
        link.symlink_to(owner)
        nofollow = os.stat(link, follow_symlinks=False)
        with open(link, "rb") as source:
            followed = os.fstat(source.fileno())
        if not stat.S_ISLNK(nofollow.st_mode) or not stat.S_ISREG(followed.st_mode):
            raise AssertionError("expected non-follow versus followed mode difference")
        return {"status": "MISMATCH_CONFIRMED",
                "nonfollowing_is_symlink": True,
                "opened_handle_is_regular": True,
                "requires_nonfollowing_open_for_safe_product": True}
    except OSError as exc:
        return {"status": "UNAVAILABLE", "reason": type(exc).__name__ + ": " + str(exc),
                "requires_nonfollowing_open_for_safe_product": True}


def measure(paths: list[Path], side: str) -> dict:
    """A = pathname nofollow stat + open; B = open + fstat on same descriptor."""
    started_wall = time.perf_counter_ns()
    started_cpu = time.process_time_ns()
    digest = hashlib.sha256()
    ownership = []
    total = 0
    for path in paths:
        if side == "A":
            info = os.stat(path, follow_symlinks=False)
            with open(path, "rb") as reader:
                content = reader.read()
        elif side == "B":
            with open(path, "rb") as reader:
                info = os.fstat(reader.fileno())
                content = reader.read()
        else:
            raise AssertionError("unrecognized experimental side")
        if not stat.S_ISREG(info.st_mode) or info.st_size != len(content):
            raise AssertionError("typed size or mode changed while reading " + str(path))
        total += len(content)
        digest.update(path.name.encode())
        digest.update(len(content).to_bytes(8, "little"))
        digest.update(hashlib.sha256(content).digest())
        ownership.append([int(info.st_dev), int(info.st_ino), int(info.st_nlink),
                          int(info.st_size), int(stat.S_IMODE(info.st_mode))])
    return {"wall_ns": time.perf_counter_ns() - started_wall,
            "cpu_ns": time.process_time_ns() - started_cpu,
            "sha256": digest.hexdigest(), "read_bytes": total,
            "owners": ownership, "files": len(paths)}


def run() -> dict:
    record = {"schema": SCHEMA, "host": platform.platform(),
              "python": sys.version, "os_name": os.name,
              "head": os.environ.get("CMPCT_J24I13_HEAD", "LOCAL_UNBOUND"),
              "source": "os.stat(nofollow)+open/read versus open/fstat/read",
              "release_credit": False, "product_change": False,
              "raw": [], "status": "RUNNING"}
    try:
        import cmpct
        record["installed_package_path"] = str(Path(cmpct.__file__).resolve())
        checkout = Path(os.environ["CMPCT_J24I13_CHECKOUT"]).resolve()
        installed = Path(cmpct.__file__).resolve()
        if checkout == installed or checkout in installed.parents:
            raise AssertionError("not an installed-package test")
        with tempfile.TemporaryDirectory(prefix="j24i13-") as tmp:
            root = Path(tmp)
            groups = corpus(root)
            record["symlink_nofollow"] = witness_symlink(root)
            for family, paths in groups.items():
                expected = measure(paths, "A")
                candidate = measure(paths, "B")
                if candidate["sha256"] != expected["sha256"]:
                    raise AssertionError("content changed across controls")
                if candidate["owners"] != expected["owners"]:
                    raise AssertionError(f"physical stat tuple differed on {family}")
                if expected["files"] != len(paths):
                    raise AssertionError("file count mismatch")
                record.setdefault("controls", {})[family] = {
                    "digest": expected["sha256"], "files": len(paths),
                    "read_bytes": expected["read_bytes"],
                    "links": [entry[2] for entry in expected["owners"][-3:]]}
                for trial in ("AA", "AB"):
                    for round_id in range(ROUNDS):
                        sequence = ("A", "A", "A", "A") if trial == "AA" else ("A", "B", "B", "A")
                        for ordinal, side in enumerate(sequence):
                            result = measure(paths, side)
                            if result["sha256"] != expected["sha256"] or result["owners"] != expected["owners"]:
                                raise AssertionError("nonidentical input/identity in timed measurements")
                            record["raw"].append({
                                "family": family, "trial": trial, "round": round_id,
                                "ordinal": ordinal, "side": side,
                                "wall_ns": result["wall_ns"], "cpu_ns": result["cpu_ns"],
                                "sha256": result["sha256"],
                                "files": result["files"], "read_bytes": result["read_bytes"]})
                pairs = []
                for r in range(ROUNDS):
                    items = [x for x in record["raw"]
                             if x["family"] == family and x["trial"] == "AB" and x["round"] == r]
                    if len(items) != 4 or tuple(x["side"] for x in items) != ("A","B","B","A"):
                        raise AssertionError("invalid ABBA sequence")
                    amean = (items[0]["wall_ns"] + items[3]["wall_ns"])/2
                    bmean = (items[1]["wall_ns"] + items[2]["wall_ns"])/2
                    pairs.append({"round": r, "A_wall_ns": amean, "B_wall_ns": bmean,
                                  "B_over_A": bmean / amean})
                record.setdefault("paired", {})[family] = pairs
            favourable = sum(1 for x in record["paired"]["unique256"]
                             if x["B_over_A"] <= 0.90)
            record["unique256_rounds_at_least_10pct_faster"] = favourable
            record["status"] = ("PROMISING_MICRO_ONLY_NOT_PRODUCT" if favourable >= 3
                                else "NO_DECISIVE_SPEED_WIN_MICRO")
            record["decision"] = ("Proceed only to nonfollowing descriptor-owned source design, "
                                  "never adopt plain fstat as equivalent to nofollow" if favourable >= 3
                                  else "Do not productize fstat shortcut on this evidence")
    except BaseException as exc:
        record["status"] = "NONPASS"
        record["error"] = type(exc).__name__ + ": " + str(exc)
        record["traceback"] = traceback.format_exc(limit=12)
        raise
    finally:
        out = Path(os.environ["CMPCT_J24I13_RECEIPT"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


if __name__ == "__main__":
    result = run()
    print(json.dumps({"status": result["status"],
                      "head": result["head"],
                      "symlink": result["symlink_nofollow"]["status"],
                      "paired": result["paired"]}, sort_keys=True))

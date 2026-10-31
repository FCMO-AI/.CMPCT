#!/usr/bin/env python3
"""J24I74: real mixed public Writer × AST-identical minimal Owned Reader.

Science only. Does not modify Reader/Writer/format or make release claims.
Preregistered before code at 42c396eafc26ab5cc6f59b195bf27213037f646b.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc

import msgpack

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))

PARENT = "a6695ba86d6a5b20eaced4eb8b54768f00724c9b"
PREREG = "42c396eafc26ab5cc6f59b195bf27213037f646b"
READER_BLOB = "29a8be64f3acfb027750351c6a567fd82cf7dc97"
J24I73_BLOB = "8956a17c8f8103e0e620934da8daa4eb9406877b"
MIXED_BLOB = "9b2fa7c2d625cce84597212673c35fba29dcafd5"
DETACHED_BLOB = "235dddde0d7bb52710b69de3dafe7653a5f6d312"
LABELS = ("public", "original", "minimal")
ORDERS = ("POM", "PMO", "OPM", "OMP", "MPO", "MOP")
CHAR = {"P": "public", "O": "original", "M": "minimal"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    with path.open("rb") as file:
        hasher = hashlib.sha256()
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def attest() -> dict:
    head = git("rev-parse", "HEAD")
    asserted = os.environ.get("J24I74_EXPECTED_HEAD")
    if asserted:
        assert head == asserted, ("wrong source HEAD", head, asserted)
    for ancestor in (PARENT, PREREG):
        assert subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, "HEAD"],
            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ).returncode == 0, ancestor
    pinned = {
        "src/cmpct/reader.py": READER_BLOB,
        "research/j24i73_owned_import_cone.py": J24I73_BLOB,
        "research/j24g73_reader_open.py": MIXED_BLOB,
        "research/j24i70_detached_referee.py": DETACHED_BLOB,
    }
    for path, expected in pinned.items():
        assert git("rev-parse", "HEAD:" + path) == expected, path
    import cmpct.reader as installed
    assert installed.__file__ is not None
    assert (Path(installed.__file__).read_bytes().replace(b"\r\n", b"\n")
            == (ROOT / "src/cmpct/reader.py").read_bytes().replace(b"\r\n", b"\n"))
    return {"head": head, "parent": PARENT, "prereg": PREREG,
            "source_blobs": pinned, "host": platform.platform(),
            "python": sys.version, "platform": sys.platform}


def charged_public_writer_case(root: Path, strict_xattrs: bool):
    """Time real public entry points without changing their arguments/results."""
    import j24g73_reader_open as g73

    costs = {"builder": [], "ren": [], "del": [], "put": []}
    original_build = g73.Builder.build
    originals = {
        "ren": g73.tx.append_rename,
        "del": g73.tx.append_delete,
        "put": g73.tx.append_update,
    }

    def wrapper(which, fn):
        def measured(*args, **kwargs):
            t = time.perf_counter_ns()
            c = time.process_time_ns()
            try:
                return fn(*args, **kwargs)
            finally:
                costs[which].append({"wall_ns": time.perf_counter_ns() - t,
                                     "cpu_ns": time.process_time_ns() - c})
        return measured

    try:
        g73.Builder.build = wrapper("builder", original_build)
        g73.tx.append_rename = wrapper("ren", originals["ren"])
        g73.tx.append_delete = wrapper("del", originals["del"])
        g73.tx.append_update = wrapper("put", originals["put"])
        t0, c0 = time.perf_counter_ns(), time.process_time_ns()
        result = g73.make_archive(root, "mixed", strict_xattrs)
        total = {"wall_ns": time.perf_counter_ns() - t0,
                 "cpu_ns": time.process_time_ns() - c0}
    finally:
        g73.Builder.build = original_build
        g73.tx.append_rename = originals["ren"]
        g73.tx.append_delete = originals["del"]
        g73.tx.append_update = originals["put"]

    assert len(costs["builder"]) == 1
    assert all(len(costs[name]) == 21 for name in ("ren", "del", "put"))
    totals = {name: {metric: sum(item[metric] for item in samples)
                     for metric in ("wall_ns", "cpu_ns")}
              for name, samples in costs.items()}
    return result, {"overall": total, "components": totals,
                    "api_calls": {name: len(samples) for name, samples in costs.items()},
                    "measurement": "nonsemantic Python wrapper around actual public APIs"}


def check_public_and_private(path: Path, expected: dict, tags: dict,
                             strict: bool, classes: dict, destination: Path):
    from cmpct.validation import preflight_archive
    from j24g73_reader_open import KEY, native_attr, xattr_projection

    original_sha = sha_file(path)
    target_names = sorted(expected)
    assert len(target_names) == 118
    member_hashes = {name: digest(expected[name]) for name in target_names}
    index_payloads = {}
    observations = {}
    for label, klass in classes.items():
        with klass(path) as reader:
            assert reader.delta_depth == 63, (label, reader.delta_depth)
            assert set(reader.by) == set(expected), label
            assert reader.verify() == len(expected), label
            raw_index = msgpack.packb(reader.index, use_bin_type=True)
            index_payloads[label] = raw_index
            route = getattr(reader, "_research_route", None)
            if label != "public":
                assert route == "owned-fresh-decoder", (label, route)
            projection = xattr_projection(reader.index)
            if strict:
                for name, attributes in tags.items():
                    assert projection.get(name, {}).get(KEY) == attributes[KEY], (label, name)
                assert len(projection) == len(tags), (label, len(projection), len(tags))
            for name in target_names:
                assert digest(reader.read(name)) == member_hashes[name], (label, name)
            output = destination / ("extract-" + label)
            reader.extractall(output, require_xattrs=strict)
            for name in target_names:
                assert digest((output / name).read_bytes()) == member_hashes[name], (label, name)
                if strict:
                    got = native_attr(output / name, KEY)
                    want = tags[name][KEY] if name in tags else None
                    assert got == want, ("restored-xattr", label, name, got, want)
            observations[label] = {
                "members": len(reader.by), "depth": reader.delta_depth,
                "route": route, "index_sha256": digest(raw_index),
                "read_verified": len(expected), "extracted_verified": len(expected),
                "xattr_metadata_records": len(projection),
                "physical_xattr_restoration": bool(strict),
            }
    assert index_payloads["public"] == index_payloads["original"] == index_payloads["minimal"]
    assert preflight_archive(path)["files"] == len(expected)
    assert sha_file(path) == original_sha, "the experiment mutated its input archive"
    return {
        "index_sha256": digest(index_payloads["public"]),
        "manifest_sha256": digest(msgpack.packb(member_hashes, use_bin_type=True)),
        "member_sha256": member_hashes,
        "names": target_names,
        "per_reader": observations,
        "preflight_files": len(expected),
        "archive_preserved": True,
        "real_sparse_xattrs": strict,
        "xattr_path_names": sorted(tags),
    }


def recovery_controls(original_bytes: bytes, root: Path, classes: dict) -> dict:
    out = {}
    damaged = {
        "bad-footer-sha": original_bytes[:-1] + bytes([original_bytes[-1] ^ 0xB5]),
        "truncated-footer": original_bytes[:-17],
    }
    for mode, data in damaged.items():
        path = root / (mode + ".cmpct")
        path.write_bytes(data)
        seen = {}
        for label, klass in classes.items():
            with klass(path) as reader:
                assert reader.delta_depth == 62, (mode, label, reader.delta_depth)
                assert reader.verify() == len(reader.by)
                index = msgpack.packb(reader.index, use_bin_type=True)
                for name in reader.by:
                    assert isinstance(reader.read(name), bytes)
                seen[label] = {"depth": reader.delta_depth,
                               "index_sha256": digest(index),
                               "members": len(reader.by),
                               "route": getattr(reader, "_research_route", None)}
        assert len({item["index_sha256"] for item in seen.values()}) == 1, mode
        assert len({item["members"] for item in seen.values()}) == 1, mode
        assert seen["minimal"]["route"] == seen["original"]["route"] == "owned-fresh-decoder"
        out[mode] = {"sha256": digest(data), "bytes": len(data),
                     "per_reader": seen}
    short = root / "invalid-short.cmpct"
    short.write_bytes(b"\x00\x01\x02")
    rejected = {}
    for label, klass in classes.items():
        try:
            with klass(short):
                pass
        except Exception:
            rejected[label] = True
        else:
            rejected[label] = False
    assert all(rejected.values()), rejected
    return {"modes": out, "short_rejected": rejected}


def warm_open_cost(path: Path, classes: dict) -> dict:
    # Source-import/cold-process costs deliberately excluded here.
    raw = []
    for block, order in enumerate(ORDERS):
        for letter in order:
            label = CHAR[letter]
            klass = classes[label]
            t = time.perf_counter_ns()
            c = time.process_time_ns()
            with klass(path) as reader:
                assert len(reader.by) == 118 and reader.delta_depth == 63
            raw.append({"block": block, "label": label,
                        "wall_ns": time.perf_counter_ns() - t,
                        "cpu_ns": time.process_time_ns() - c})
    medians = {}
    for label in LABELS:
        selected = [item for item in raw if item["label"] == label]
        assert len(selected) == 6
        medians[label] = {
            metric: statistics.median(item[metric] for item in selected)
            for metric in ("wall_ns", "cpu_ns")
        }
    traced = {}
    for label, klass in classes.items():
        tracemalloc.start()
        tracemalloc.reset_peak()
        with klass(path) as reader:
            assert len(reader.by) == 118
        traced[label] = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
    return {"raw": raw, "medians": medians, "tracemalloc_peak_bytes": traced,
            "scope": "6 ordered, warm, in-process opens per Reader; no process startup"}


def main() -> None:
    if sys.platform not in ("linux", "darwin", "win32"):
        raise RuntimeError("unregistered platform: " + sys.platform)
    from cmpct.reader import CMPCT
    from j24g73_reader_open import verify_pair
    from j24g74_owned_decoder_court import OwnedCMPCT as Original
    from j24i73_owned_import_cone import generate_minimal_module

    output = Path(os.environ.get("J24I74_EVIDENCE", "evidence/j24i74")).resolve()
    output.mkdir(parents=True, exist_ok=True)
    receipt = {"schema": "cmpct-j24i74-mixed-import-cone-v1",
               "status": "STARTED", "product_credit": 0,
               "source": attest()}
    try:
        with tempfile.TemporaryDirectory(prefix="j24i74-") as td:
            tmp = Path(td)
            module_path = tmp / "j24i73_ablation_owned.py"
            receipt["minimal_module"] = generate_minimal_module(module_path)
            shutil.copyfile(module_path, output / "j24i73_ablation_owned.py")
            sys.path.insert(0, str(tmp))
            try:
                Minimal = importlib.import_module("j24i73_ablation_owned").OwnedCMPCT
                classes = {"public": CMPCT, "original": Original, "minimal": Minimal}
                strict = sys.platform in ("linux", "darwin")
                ((path, expected, tags), costs) = charged_public_writer_case(tmp, strict)
                before = sha_file(path)
                receipt["physical"] = {
                    "file": "mixed.cmpct", "sha256": before,
                    "bytes": path.stat().st_size, "members": len(expected),
                    "generation_depth": 63, "expected_operations": {"ren": 21, "del": 21, "put": 21},
                    "physical_xattrs_required": strict,
                    "physical_xattrs_claimed": strict,
                    "operating_system": sys.platform,
                }
                shutil.copyfile(path, output / "mixed.cmpct")
                receipt["writer_cost"] = costs
                # An inherited, differently implemented control already checks public
                # vs factored, authentic 63 Writer ops, preflight and actual xattrs.
                receipt["inherited_public_vs_factored"] = verify_pair(path, expected, tags, strict)
                receipt["parity"] = check_public_and_private(
                    path, expected, tags, strict, classes, tmp)
                receipt["recovery"] = recovery_controls(path.read_bytes(), tmp, classes)
                receipt["open_cost"] = warm_open_cost(path, classes)
                assert sha_file(path) == before
                receipt["status"] = "PASS_SCIENCE_ONLY"
            finally:
                sys.path.remove(str(tmp))
    except BaseException as exc:
        receipt["status"] = "FAIL"
        receipt["exception"] = {"type": type(exc).__name__, "text": str(exc)}
        raise
    finally:
        (output / "receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2))
    print(json.dumps({"status": receipt["status"], "source": receipt["source"]["head"],
                      "archive_sha256": receipt["physical"]["sha256"],
                      "physical_xattrs": receipt["physical"]["physical_xattrs_required"],
                      "median_wall_ns": receipt["open_cost"]["medians"]}, sort_keys=True))


if __name__ == "__main__":
    main()

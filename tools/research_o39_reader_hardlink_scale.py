#!/usr/bin/env python3
"""O39: source-exact O31 vs committed O38 32k Reader scaling economics.

Derived research-only instrument (O33 fixture framing, O39 distinct question). Predictions frozen in
docs/v031-research/2026-10-25-o38-heldout-hardlink-scale-o39-prereg.md.
No product code, inherited O33 instrument, release comparator, or gate is modified.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import sys
import time


BASE_SHA = "0edb7bc6e832deb1b403fea50c36e655da9844fd"
PRODUCT_SHA = "dffc6da03b588e209843f2fc6e219e5bce3a7800"
BASE_READER_BLOB = "de9accf6607aca7cf70dfe71d7b299a02e298a2d"
PRODUCT_READER_BLOB = "4aee9e8ddf50ff3c3e0db20ebf7671e2ac477867"
PAYLOAD = b"O39-authentic-physical-owner\x00\xfd\xfe" * 3


def rss() -> dict[str, int]:
    """Linux process resident and high-water values, in KiB."""
    p = Path("/proc/self/status")
    if not p.exists():
        raise RuntimeError("O39 RSS court requires Linux /proc/self/status")
    fields = {}
    for line in p.read_text().splitlines():
        if line.startswith(("VmRSS:", "VmHWM:")):
            fields[line.split(":")[0]] = int(line.split(":")[1].strip().split()[0])
    if set(fields) != {"VmRSS", "VmHWM"}:
        raise RuntimeError("Linux VmRSS/VmHWM unavailable")
    return fields


def index_for(size: int, shape: str, target: Path) -> dict:
    """Write genuine revision-24 physical framing and authenticated index.

    All variants reference one physically stored owner blob. Plain rows are
    independent regular files; alias rows expose graph fanout/chain cost.
    """
    from cmpct.codec import (
        BHDR, BMAGIC, CODEC_RAW, FMAGIC, FTR, HDR, K_FILE,
        K_HARDLINK, MAGIC, S_BLOB, VERSION, sha, zc,
    )

    owner_sha = sha(PAYLOAD)
    if shape == "plain":
        rows = [
            [f"file{i:05d}", K_FILE, 0o644, 0, len(PAYLOAD), owner_sha, [S_BLOB, 0]]
            for i in range(size)
        ]
        samples = ["file00000", f"file{size-1:05d}"]
    elif shape in {"fanout", "chain", "noncanonical"}:
        owner = "sub/owner.bin" if shape == "noncanonical" else "owner.bin"
        rows = [[owner, K_FILE, 0o644, 0, len(PAYLOAD), owner_sha, [S_BLOB, 0]]]
        for i in range(size - 1):
            name = f"alias{i:05d}"
            following = (
                "sub\\owner.bin" if shape == "noncanonical"
                else owner if shape == "fanout" or i == size - 2
                else f"alias{i+1:05d}"
            )
            rows.append(
                [name, K_HARDLINK, 0o644, 0, len(PAYLOAD), owner_sha, [following]]
            )
        samples = ["alias00000", f"alias{size-2:05d}", owner]
    else:
        raise ValueError(shape)
    manifest = {
        "v": VERSION, "files": sorted(rows, key=lambda r: r[0]),
        "blobs": [[0, len(PAYLOAD), len(PAYLOAD), CODEC_RAW, 0]],
        "recipes": [], "dict_blob": None,
        "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
    }
    # This is the original O25 wire construction, not a Reader/index mock.
    import msgpack
    raw = msgpack.packb(manifest, use_bin_type=True)
    compressed = zc(raw, 3)
    physical = (
        BHDR.pack(BMAGIC, CODEC_RAW, 0, 0, len(PAYLOAD), len(PAYLOAD),
                  0, binascii.crc32(PAYLOAD) & 0xFFFFFFFF, owner_sha)
        + PAYLOAD
    )
    header = HDR.pack(
        MAGIC, VERSION, 0, len(compressed), len(raw), len(physical), sha(raw)
    )
    footer = FTR.pack(
        FMAGIC, 0, 1, 0, 0, len(compressed), len(raw), 0, sha(raw)
    )
    target.write_bytes(header + compressed + physical + compressed + footer)
    return {
        "path": str(target.resolve()), "shape": shape, "size": size,
        "bytes": target.stat().st_size,
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "samples": samples, "payload_sha256": hashlib.sha256(PAYLOAD).hexdigest(),
    }


def generate(output: Path) -> list[dict]:
    from cmpct.reader import CMPCT
    from cmpct.validation import preflight_archive

    output.mkdir(parents=True, exist_ok=True)
    records = []
    for size in (8192, 32768):
        for shape in ("plain", "fanout", "chain", "noncanonical"):
            case = index_for(size, shape, output / f"{shape}-{size}.cmpct")
            # Strong control outside the performance interval.
            info = preflight_archive(case["path"])
            assert info["files"] == size, (case, info)
            with CMPCT(case["path"]) as reader:
                assert len(reader.files) == size
                for name in case["samples"]:
                    assert reader.read(name) == PAYLOAD
                    assert reader.read_range(name, 1, 9) == PAYLOAD[1:10]
                    assert bytes(reader.file_sha256(name)) == hashlib.sha256(PAYLOAD).digest()
                assert reader.verify() == size
            records.append(case)
    return records


def child(source: Path, archive: Path, samples: list[str]) -> None:
    """Exactly one source-bound fresh interpreter, emitting one JSON receipt."""
    source = source.resolve()
    sys.path.insert(0, str(source))
    mem_initial = rss()
    t_import = time.perf_counter_ns()
    from cmpct.reader import CMPCT
    import cmpct.reader as reader_mod
    imported_reader = Path(reader_mod.__file__).resolve()
    if not imported_reader.is_relative_to(source):
        raise RuntimeError(f"Source path mismatch: {imported_reader} not under {source}")
    import cmpct.native_codec as native_mod
    imported_native = Path(native_mod._library_path()).resolve()
    if not imported_native.is_relative_to(source):
        raise RuntimeError(f"Native payload provenance mismatch: {imported_native} not under {source}")
    after_import = time.perf_counter_ns()
    mem_pre = rss()
    cpu_pre = time.process_time_ns()
    t_open = time.perf_counter_ns()
    with CMPCT(archive) as reader:
        t_construct = time.perf_counter_ns()
        mem_post = rss()
        cpu_post = time.process_time_ns()
        count = len(reader.files)
        for name in samples:
            if reader.read(name) != PAYLOAD:
                raise RuntimeError("Reader content mismatch")
            if reader.read_range(name, 1, 9) != PAYLOAD[1:10]:
                raise RuntimeError("Reader range mismatch")
            if bytes(reader.file_sha256(name)) != hashlib.sha256(PAYLOAD).digest():
                raise RuntimeError("Reader logical SHA mismatch")
    t_done = time.perf_counter_ns()
    mem_done = rss()
    print(json.dumps({
        "source": str(source), "module": str(imported_reader),
        "native_module": str(imported_native),
        "archive": str(archive), "files": count,
        "import_ms": (after_import - t_import) / 1e6,
        "construct_ms": (t_construct - t_open) / 1e6,
        "read_ms": (t_done - t_construct) / 1e6,
        "cpu_construct_ms": (cpu_post - cpu_pre) / 1e6,
        "rss_initial_kib": mem_initial["VmRSS"],
        "rss_pre_kib": mem_pre["VmRSS"],
        "rss_post_kib": mem_post["VmRSS"],
        "rss_done_kib": mem_done["VmRSS"],
        "hwm_pre_kib": mem_pre["VmHWM"],
        "hwm_post_kib": mem_post["VmHWM"],
        "hwm_delta_kib": max(0, mem_post["VmHWM"] - mem_pre["VmHWM"]),
        "ru_maxrss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }, sort_keys=True))


def median(xs: list[float]) -> float:
    return statistics.median(xs)


def runner(source_base: Path, source_candidate: Path, out: Path, reps: int) -> None:
    if reps < 8 or reps % 2:
        raise ValueError("O39 requires at least eight even-count fresh observations per source")
    # O33 raw labels were historically source-specific constants. Do not inherit
    # a false receipt: prove each actually executed Git checkout before any court.
    for source, head, blob in (
        (source_base, BASE_SHA, BASE_READER_BLOB),
        (source_candidate, PRODUCT_SHA, PRODUCT_READER_BLOB),
    ):
        repo_root = source.resolve().parent
        got_head = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True
        ).strip()
        got_blob = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD:src/cmpct/reader.py"],
            text=True,
        ).strip()
        if got_blob != blob:
            raise RuntimeError(
                f"source Reader blob mismatch for {repo_root}: "
                f"got {got_blob}, expected {blob}"
            )
        if head == BASE_SHA:
            # Baseline must be the exact historical commit.
            if got_head != head:
                raise RuntimeError(f"historical O31 HEAD mismatch: {got_head} != {head}")
        else:
            # Research branch is a child of product SHA. Requiring HEAD equality
            # incorrectly rejects legitimate evidence-only child commits.
            # Admit only ancestry plus full product-source/native tree identity.
            ancestor = subprocess.run(
                ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", head, "HEAD"],
                check=False,
            )
            changed_product = subprocess.run(
                ["git", "-C", str(repo_root), "diff", "--quiet", head, "HEAD", "--", "src/", "native/"],
                check=False,
            )
            if ancestor.returncode != 0 or changed_product.returncode != 0:
                raise RuntimeError(
                    f"candidate source closure mismatch: checkout {got_head} must descend "
                    f"from immutable product {head} with identical src/ and native/"
                )
    out.mkdir(parents=True, exist_ok=True)
    manifest = generate(out / "archives")
    print("O39 verified authentic six-corpus checkpoint manifest", flush=True)
    raw = []
    summaries = []
    for case in manifest:
        # Each quartet alternates sources. Reverse ABBA every other quartet
        # to reduce monotone warm-cache, CPU governor and hosted drift effects.
        for k in range(reps // 2):
            order = ("base", "candidate", "candidate", "base") if k % 2 == 0 else (
                "candidate", "base", "base", "candidate"
            )
            for label in order:
                source = source_base if label == "base" else source_candidate
                args = [
                    sys.executable, str(Path(__file__).resolve()), "--child",
                    "--source", str(source), "--archive", case["path"],
                    "--samples", ",".join(case["samples"]),
                ]
                env = {**os.environ, "PYTHONHASHSEED": "0"}
                t0 = time.perf_counter_ns()
                p = subprocess.run(
                    args, capture_output=True, text=True, timeout=90, check=False,
                    env=env,
                )
                wall = (time.perf_counter_ns() - t0) / 1e6
                if p.returncode:
                    raise RuntimeError(
                        f"Child failed shape={case['shape']} n={case['size']} "
                        f"source={label} return={p.returncode}\n{p.stdout}\n{p.stderr}"
                    )
                data = json.loads(p.stdout.strip())
                if data["files"] != case["size"]:
                    raise RuntimeError("Wrong Reader member count")
                raw.append({
                    "shape": case["shape"], "size": case["size"],
                    "source_label": label, "pair_group": k, "wall_ms": wall,
                    **data,
                })
        section = [
            x for x in raw if x["shape"] == case["shape"] and x["size"] == case["size"]
        ]
        base = [x for x in section if x["source_label"] == "base"]
        cand = [x for x in section if x["source_label"] == "candidate"]
        if len(base) != reps or len(cand) != reps:
            raise RuntimeError("Not enough observations per source")
        b_construct = median([x["construct_ms"] for x in base])
        c_construct = median([x["construct_ms"] for x in cand])
        b_rss = median([x["rss_post_kib"] for x in base])
        c_rss = median([x["rss_post_kib"] for x in cand])
        slowdown = c_construct / b_construct if b_construct else float("inf")
        rss_ratio = c_rss / b_rss if b_rss else float("inf")
        debt = (
            (slowdown >= 1.10 and c_construct - b_construct >= 3.0)
            or (rss_ratio >= 1.10 and c_rss - b_rss >= 4096)
        )
        summary = {
            "shape": case["shape"], "size": case["size"],
            "construct_ms": {"base": b_construct, "candidate": c_construct},
            "complete_process_ms": {
                "base": median([x["wall_ms"] for x in base]),
                "candidate": median([x["wall_ms"] for x in cand]),
            },
            "constructor_cpu_ms": {
                "base": median([x["cpu_construct_ms"] for x in base]),
                "candidate": median([x["cpu_construct_ms"] for x in cand]),
            },
            "post_rss_kib": {"base": b_rss, "candidate": c_rss},
            "hwm_increment_kib": {
                "base": median([x["hwm_delta_kib"] for x in base]),
                "candidate": median([x["hwm_delta_kib"] for x in cand]),
            },
            "constructor_slowdown_ratio": slowdown,
            "post_rss_ratio": rss_ratio,
            "material_debt_under_preregistered_triage": debt,
            "observations_per_source": reps,
        }
        summaries.append(summary)
        print("O39_RESULT " + json.dumps(summary, sort_keys=True), flush=True)
    candidate_checkout_head = subprocess.check_output(
        ["git", "-C", str(source_candidate.resolve().parent), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    # The product source is the pinned O38 ancestor, while the evidence-only
    # checkout has its own HEAD. Never mislabel an experiment ref as product SHA.
    result = {
        "experiment": "O39", "status": "RESEARCH_NOT_RELEASE",
        "source_baseline_head": BASE_SHA, "source_candidate_head": PRODUCT_SHA,
        "source_evidence_checkout_head": candidate_checkout_head,
        "source_relation": "evidence HEAD descends from O38; identical tracked src/ and native/ trees",
        "baseline_reader_blob": BASE_READER_BLOB,
        "candidate_reader_blob": PRODUCT_READER_BLOB,
        "platform": platform.platform(), "python": sys.version,
        "kernel": platform.release(),
        "reps_per_source": reps,
        "corpus": manifest, "results": summaries,
        "raw": raw,
        "limitations": [
            "Linux hosted runner only; independent processes do not guarantee cold filesystem page cache.",
            "One physical raw blob per archive isolates authenticated logical index and hardlink topology; no large multi-blob decode/create claim.",
            "O28 lacks O31 canonical target and implicit-parent capability; only common admissible flat-path semantics are compared.",
            "Observed medians are evidence for this host, not official r24 parity promotion.",
            "Child RSS after constructor is not an exact peak allocation trace inside its execution."
        ],
    }
    file = out / "o39-raw.json"
    file.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"O39_RECEIPT {file} sha256={hashlib.sha256(file.read_bytes()).hexdigest()}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--source", type=Path)
    ap.add_argument("--archive", type=Path)
    ap.add_argument("--samples")
    ap.add_argument("--base-source", type=Path)
    ap.add_argument("--candidate-source", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--reps", type=int, default=8)
    ns = ap.parse_args()
    if ns.child:
        child(ns.source, ns.archive, ns.samples.split(","))
    else:
        runner(ns.base_source, ns.candidate_source, ns.out, ns.reps)


if __name__ == "__main__":
    main()

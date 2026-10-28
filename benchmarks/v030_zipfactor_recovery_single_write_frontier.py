from __future__ import annotations

"""Research-only single-write recovery frontier for ZIP-factor v3.

The recovery envelope is already byte-competitive, but the legacy recovery builder first publishes a complete
v3 archive to a temporary file, rereads it, then publishes the recovery archive.  This oracle constructs the
identical v3 byte stream in memory and publishes the recovery envelope once.  Every round cross-checks the exact
recovery bytes against the legacy builder and runs the same in-memory recovery verifier before timing credit.

No selector, archive grammar, recovery rule, locality/decode-unit limit, benchmark identity, or release gate is
changed.  A positive receipt only nominates the construction refactor for canonical productization.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

import zstandard as zstd

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_zipfactor_recovery_inmemory_verify_frontier as MEM
from benchmarks import v030_zipfactor_recovery_oracle as REC
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3
from experiments import entropygraph_v030_zipfactor_fused as FUSED
from experiments import entropygraph_v030_zipfactor_profile as BASE

ROUNDS = 11
LEVEL = 3
GROUP_SIZE = 7


def _sha(raw: bytes) -> bytes:
    return hashlib.sha256(raw).digest()


def _build_v3_bytes(root: Path, *, level: int, group_size: int) -> tuple[bytes, dict]:
    if group_size < 1 or group_size > V3.MAX_FILES:
        raise V3.ProfileNotEligible("single-write ZIP-factor group size exceeds policy")
    manifest_raw, items, fs_stats = FUSED._scan(Path(root))
    if not 2 <= len(items) <= V3.MAX_FILES:
        raise V3.ProfileNotEligible("single-write ZIP-factor regular-file envelope")

    template_raw = BASE._serialize_template(items[0][1])
    groups = [items[index:index + group_size] for index in range(0, len(items), group_size)]
    group_raws = [V3._pack_group(group) for group in groups]
    regular_sizes = {rel: int(item["raw_size"]) for rel, item in items}
    max_decode = max(len(template_raw) + len(raw) for raw in group_raws)
    max_amp = max(
        (len(template_raw) + len(raw)) / max(1, min(regular_sizes[rel] for rel, _item in group))
        for group, raw in zip(groups, group_raws, strict=True)
    )
    if max_decode > V3.MAX_DECODE or max_amp > V3.MAX_AMP:
        raise V3.ProfileNotEligible("single-write ZIP-factor locality ceiling")

    compressor = zstd.ZstdCompressor(level=level, threads=0)
    manifest_blob = compressor.compress(manifest_raw)
    template_blob = compressor.compress(template_raw)
    group_blobs = [compressor.compress(raw) for raw in group_raws]

    control = bytearray(
        V3._HEADER.pack(
            len(manifest_raw),
            _sha(manifest_raw),
            len(template_raw),
            _sha(template_raw),
            len(groups),
        )
    )
    for group, raw in zip(groups, group_raws, strict=True):
        control += V3._GROUP.pack(len(raw), _sha(raw), len(group))

    payload = bytearray(V3.MAGIC)
    payload += control
    payload += BASE._blob(manifest_blob)
    payload += BASE._blob(template_blob)
    for blob in group_blobs:
        payload += BASE._blob(blob)
    raw = bytes(payload)
    return raw, {
        "archive_bytes": len(raw),
        "format_revision": V3.REVISION,
        "format_profile": V3.PROFILE,
        "user_files": len(items),
        "groups": len(groups),
        "control_bytes": len(control),
        "max_decode_unit_bytes": max_decode,
        "max_member_read_amplification": max_amp,
        "level": level,
        "group_size": group_size,
        "fused_source_scan": True,
        **fs_stats,
    }


def build_single_write(root: Path, out: Path, *, level: int, group_size: int) -> dict:
    base, base_stats = _build_v3_bytes(root, level=level, group_size=group_size)
    if base[:8] != V3.MAGIC:
        raise RuntimeError("unexpected ZIP-factor v3 identity")
    *_, group_count = V3._HEADER.unpack_from(base, 8)
    control_len = V3._HEADER.size + int(group_count) * V3._GROUP.size
    control = base[8:8 + control_len]
    body = base[8 + control_len:]
    footer = REC._FOOTER.pack(REC.TAIL_MAGIC, control_len, _sha(control))
    recovery = REC.REC_MAGIC + control + body + control + footer
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(recovery)
    return {
        **base_stats,
        "format_profile": "zip-framing-factor-recovery-single-write-v4",
        "archive_bytes": len(recovery),
        "base_v3_bytes": len(base),
        "recovery_overhead_bytes": len(recovery) - len(base),
        "control_bytes": control_len,
        "payload_body_bytes": len(body),
        "payload_body_copies": 1,
        "control_copies": 2,
    }


def _median(values: list[float]) -> float:
    return float(statistics.median(values))


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-single-write-", dir=work_root) as td_raw:
        td = Path(td_raw)
        stage = EXT._normalized_stage(source, td)
        expected_tree = EXT._tree(stage)
        direct_samples: list[float] = []
        legacy_samples: list[float] = []
        zip_samples: list[float] = []
        zstd_samples: list[float] = []
        direct_build_samples: list[float] = []
        direct_verify_samples: list[float] = []
        candidate_sizes: set[int] = set()
        candidate_sha: set[str] = set()
        stats: dict | None = None

        order = ("direct", "legacy", "zip", "zstd")
        for round_index in range(ROUNDS):
            rotated = order[round_index % len(order):] + order[:round_index % len(order)]
            direct_path = td / f"direct-{round_index}.cmpct"
            legacy_path = td / f"legacy-{round_index}.cmpct"
            for kind in rotated:
                if kind == "direct":
                    t0 = time.perf_counter()
                    stats = build_single_write(stage, direct_path, level=LEVEL, group_size=GROUP_SIZE)
                    t1 = time.perf_counter()
                    verified = MEM.recover_verify_inmemory(direct_path)
                    t2 = time.perf_counter()
                    if not verified.get("ok"):
                        raise RuntimeError(f"single-write recovery verification failed: {verified!r}")
                    direct_build_samples.append(t1 - t0)
                    direct_verify_samples.append(t2 - t1)
                    direct_samples.append(t2 - t0)
                    candidate_sizes.add(direct_path.stat().st_size)
                    candidate_sha.add(hashlib.sha256(direct_path.read_bytes()).hexdigest())
                elif kind == "legacy":
                    t0 = time.perf_counter()
                    REC.build_recovery(stage, legacy_path, level=LEVEL, group_size=GROUP_SIZE)
                    verified = MEM.recover_verify_inmemory(legacy_path)
                    t1 = time.perf_counter()
                    if not verified.get("ok"):
                        raise RuntimeError("legacy recovery verification failed")
                    legacy_samples.append(t1 - t0)
                elif kind == "zip":
                    result = EXT._zip(stage, td / f"archive-{round_index}.zip", td / f"zip-out-{round_index}")
                    EXT._verify_extracted(td / f"zip-out-{round_index}", expected_tree, "zf-single-write-zip")
                    zip_samples.append(float(result["create_s"]))
                else:
                    work = td / f"zstd-work-{round_index}"
                    work.mkdir()
                    result = EXT._tar_zstd(stage, td / f"archive-{round_index}.tar.zst", td / f"zstd-out-{round_index}", work)
                    if not result.get("available"):
                        raise RuntimeError("solid Zstd-19 unavailable")
                    EXT._verify_extracted(td / f"zstd-out-{round_index}", expected_tree, "zf-single-write-zstd")
                    zstd_samples.append(float(result["create_s"]))

            if direct_path.read_bytes() != legacy_path.read_bytes():
                raise RuntimeError("single-write recovery bytes diverged from legacy recovery bytes")

        if len(candidate_sizes) != 1 or len(candidate_sha) != 1 or stats is None:
            raise RuntimeError("single-write recovery candidate was not deterministic")

        zw = td / "size-zstd-work"
        zw.mkdir()
        zstd_size = EXT._tar_zstd(stage, td / "size.tar.zst", td / "size-zstd-out", zw)
        zip_size = EXT._zip(stage, td / "size.zip", td / "size-zip-out")
        if not zstd_size.get("available"):
            raise RuntimeError("solid Zstd-19 unavailable for size ratchet")

        cmpct_bytes = next(iter(candidate_sizes))
        zip_bytes = int(zip_size["archive_bytes"])
        zstd_bytes = int(zstd_size["archive_bytes"])
        med_direct = _median(direct_samples)
        med_legacy = _median(legacy_samples)
        med_zip = _median(zip_samples)
        med_zstd = _median(zstd_samples)
        strict = cmpct_bytes < zip_bytes and cmpct_bytes < zstd_bytes and med_direct < med_zip and med_direct < med_zstd
        return {
            "schema": "cmpct-v030-zipfactor-recovery-single-write-frontier-v1",
            "contract": {
                "rounds": ROUNDS,
                "level": LEVEL,
                "group_size": GROUP_SIZE,
                "archive_grammar_changed": False,
                "recovery_semantics_changed": False,
                "legacy_bytes_cross_checked_each_round": True,
                "mandatory_inmemory_verify_inside_cmpct_timing": True,
                "ties_fail": True,
                "selector_change": False,
                "release_credit": False,
            },
            "sizes": {"cmpct": cmpct_bytes, "zip": zip_bytes, "zstd19": zstd_bytes},
            "medians_s": {"direct_cmpct": med_direct, "legacy_cmpct": med_legacy, "zip": med_zip, "zstd19": med_zstd},
            "direct_phase_medians_s": {"build": _median(direct_build_samples), "verify": _median(direct_verify_samples)},
            "direct_vs_legacy_speedup_fraction": 1.0 - med_direct / med_legacy,
            "samples_s": {"direct_cmpct": direct_samples, "legacy_cmpct": legacy_samples, "zip": zip_samples, "zstd19": zstd_samples},
            "candidate_sha256": next(iter(candidate_sha)),
            "strict_four_way_win": strict,
            "experiment_valid": (
                len(direct_samples) == len(legacy_samples) == len(zip_samples) == len(zstd_samples) == ROUNDS
                and cmpct_bytes < zip_bytes
                and cmpct_bytes < zstd_bytes
                and float(stats["max_member_read_amplification"]) <= 8.0
                and int(stats["max_decode_unit_bytes"]) <= 8 * 1024 * 1024
            ),
            "promotion_signal": strict,
            "release_credit": False,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("ZIP-factor single-write recovery frontier invalid")


if __name__ == "__main__":
    main()

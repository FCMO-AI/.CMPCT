from __future__ import annotations

"""Strict external frontier for ZIP-factor recovery with direct build + in-process Rust verification.

The recovery envelope bytes are unchanged. The exact fused CMP25Z3 payload is now obtained in memory from its
single semantic owner and wrapped directly, removing the old temporary-V3 publication/readback from the timed
build. A legacy build is still performed once outside timing and must be byte-identical before measurements begin.

Clean strong verification uses the already-proven research-only CMP25Z3 FFI verifier. Recovery correctness remains
separately proven with the Python recovery oracle: primary/tail corruption must recover from the other authenticated
control copy and double corruption must fail. Compilation/library load and the one-time legacy identity proof are
outside timing; direct recovery build, V3 reconstruction, scratch publication, archive open and Rust FFI verification
are inside CMPCT creation timing. No selector or release credit is granted.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_zipfactor_recovery_oracle as REC
from benchmarks.v030_zipfactor_native_ffi_complete_frontier import NativeVerifier
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3
from experiments import entropygraph_v030_zipfactor_compact_v3_fused_finalize as FUSED

ROUNDS = 9
LEVEL = 3
GROUP_SIZE = 7


def _median(v: list[float]) -> float:
    return float(statistics.median(v))


def _direct_recovery_bytes(root: Path, *, level: int, group_size: int) -> tuple[bytes, dict]:
    """Build exact recovery bytes without publishing/re-reading an intermediate CMP25Z3 file."""
    raw, base_stats = FUSED.build_bytes(root, level=level, group_size=group_size)
    if raw[:8] != V3.MAGIC:
        raise RuntimeError("unexpected ZIP-factor v3 identity")
    *_, group_count = V3._HEADER.unpack_from(raw, 8)
    control_len = V3._HEADER.size + int(group_count) * V3._GROUP.size
    control = raw[8 : 8 + control_len]
    body = raw[8 + control_len :]
    footer = REC._FOOTER.pack(REC.TAIL_MAGIC, control_len, REC._sha(control))
    recovery = REC.REC_MAGIC + control + body + control + footer
    return recovery, {
        **base_stats,
        "format_profile": "zip-framing-factor-recovery-oracle-v4",
        "archive_bytes": len(recovery),
        "base_v3_bytes": len(raw),
        "recovery_overhead_bytes": len(recovery) - len(raw),
        "control_bytes": control_len,
        "payload_body_bytes": len(body),
        "payload_body_copies": 1,
        "control_copies": 2,
        "direct_v3_in_memory": True,
    }


def _build_recovery_direct(root: Path, out: Path, *, level: int, group_size: int) -> dict:
    recovery, stats = _direct_recovery_bytes(root, level=level, group_size=group_size)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(recovery)
    return stats


def _native_recovery_verify(path: Path, verifier: NativeVerifier, scratch: Path) -> str:
    raw = path.read_bytes()
    errors: list[str] = []
    try:
        primary_len = REC._control_len_from_primary(raw)
        tail_len, tail_start, _ = REC._tail_layout(raw)
        if tail_len != primary_len:
            raise RuntimeError("recovery control length mismatch")
        primary = raw[8 : 8 + primary_len]
        candidate = REC._v3_candidate(raw, primary, 8 + primary_len, tail_start)
        scratch.write_bytes(candidate)
        verifier(Path(), scratch)
        return "primary"
    except Exception as exc:
        errors.append(repr(exc))
    try:
        control, tail_start = REC._tail_control(raw)
        candidate = REC._v3_candidate(raw, control, 8 + len(control), tail_start)
        scratch.write_bytes(candidate)
        verifier(Path(), scratch)
        return "tail"
    except Exception as exc:
        errors.append(repr(exc))
    raise RuntimeError(f"native recovery verification failed closed: {errors!r}")


def run(work_root: Path, native_library: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"
    verifier = NativeVerifier(native_library)

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-rec-ffi-", dir=work_root) as td_raw:
        td = Path(td_raw)
        stage = EXT._normalized_stage(source, td)
        external_tree = EXT._tree(stage)

        # Before timing, prove the new no-intermediate path is exactly the historical recovery representation.
        legacy = td / "legacy-recovery.cmpct"
        original_build = V3.build
        V3.build = FUSED.build
        try:
            REC.build_recovery(stage, legacy, level=LEVEL, group_size=GROUP_SIZE)
        finally:
            V3.build = original_build
        direct_probe = td / "direct-recovery.cmpct"
        probe_stats = _build_recovery_direct(stage, direct_probe, level=LEVEL, group_size=GROUP_SIZE)
        legacy_bytes = legacy.read_bytes()
        direct_bytes = direct_probe.read_bytes()
        legacy_recovery_byte_identical = legacy_bytes == direct_bytes
        if not legacy_recovery_byte_identical:
            raise RuntimeError("direct recovery build changed canonical candidate bytes")

        cmpct: list[float] = []
        build: list[float] = []
        verify: list[float] = []
        zip_s: list[float] = []
        zstd_s: list[float] = []
        sizes: set[int] = set()
        shas: set[str] = set()
        stats: dict | None = None
        order = ("cmpct", "zip", "zstd")
        for i in range(ROUNDS):
            for kind in order[i % 3 :] + order[: i % 3]:
                if kind == "cmpct":
                    archive = td / f"candidate-{i}.cmpct"
                    scratch = td / f"verify-{i}.cmpct"
                    t0 = time.perf_counter()
                    row = _build_recovery_direct(stage, archive, level=LEVEL, group_size=GROUP_SIZE)
                    t1 = time.perf_counter()
                    recovered_from = _native_recovery_verify(archive, verifier, scratch)
                    t2 = time.perf_counter()
                    if recovered_from != "primary":
                        raise RuntimeError("clean recovery archive did not verify from primary control")
                    if not row.get("fused_group_finalize") or not row.get("direct_v3_in_memory"):
                        raise RuntimeError("recovery build did not use direct fused V3 builder")
                    stats = row
                    sizes.add(archive.stat().st_size)
                    shas.add(hashlib.sha256(archive.read_bytes()).hexdigest())
                    build.append(t1 - t0)
                    verify.append(t2 - t1)
                    cmpct.append(t2 - t0)
                elif kind == "zip":
                    a, out = td / f"z-{i}.zip", td / f"zo-{i}"
                    r = EXT._zip(stage, a, out)
                    EXT._verify_extracted(out, external_tree, "zf-rec-ffi-zip")
                    zip_s.append(float(r["create_s"]))
                else:
                    a, out, w = td / f"s-{i}.tar.zst", td / f"so-{i}", td / f"sw-{i}"
                    w.mkdir()
                    r = EXT._tar_zstd(stage, a, out, w)
                    if not r.get("available"):
                        raise RuntimeError("solid Zstd-19 unavailable")
                    EXT._verify_extracted(out, external_tree, "zf-rec-ffi-zstd")
                    zstd_s.append(float(r["create_s"]))

        if len(sizes) != 1 or len(shas) != 1 or stats is None:
            raise RuntimeError("recovery candidate was not deterministic")

        # Recovery semantics and semantic identity are proven outside the timing A/B, without weakening the timed
        # verifier: the Rust verifier above still authenticates every reconstructed V3 member on every round.
        proof_archive = td / "recovery-proof.cmpct"
        _build_recovery_direct(stage, proof_archive, level=LEVEL, group_size=GROUP_SIZE)
        clean = REC.recover_verify(proof_archive)
        if not clean.get("ok"):
            raise RuntimeError("Python recovery semantic proof failed")
        raw = proof_archive.read_bytes()
        control_len = int(stats["control_bytes"])
        primary_bad = td / "primary-bad.cmpct"
        primary_bad.write_bytes(REC._flip(raw, 8 + 7))
        primary_recovered = REC.recover_verify(primary_bad)
        _, tail_start = REC._tail_control(raw)
        tail_bad = td / "tail-bad.cmpct"
        tail_bad.write_bytes(REC._flip(raw, tail_start + min(7, control_len - 1)))
        tail_recovered = REC.recover_verify(tail_bad)
        both_bad = td / "both-bad.cmpct"
        both_bad.write_bytes(REC._flip(primary_bad.read_bytes(), tail_start + min(7, control_len - 1)))
        both_failed = REC.recover_verify(both_bad)
        recovery_semantics = (
            primary_recovered.get("ok") is True
            and primary_recovered.get("recovered_from") == "tail"
            and tail_recovered.get("ok") is True
            and tail_recovered.get("recovered_from") == "primary"
            and both_failed.get("ok") is False
            and REC._snapshot(clean) == REC._snapshot(primary_recovered) == REC._snapshot(tail_recovered)
        )
        if not recovery_semantics:
            raise RuntimeError("recovery semantics did not remain fail-closed")

        za, zo = td / "size.zip", td / "size-zip-out"
        zr = EXT._zip(stage, za, zo)
        sa, so, sw = td / "size.tar.zst", td / "size-zstd-out", td / "size-zstd-work"
        sw.mkdir()
        sr = EXT._tar_zstd(stage, sa, so, sw)
        if not sr.get("available"):
            raise RuntimeError("solid Zstd-19 unavailable for size ratchet")
        cb, zb, sb = next(iter(sizes)), int(zr["archive_bytes"]), int(sr["archive_bytes"])
        mc, mz, ms = _median(cmpct), _median(zip_s), _median(zstd_s)
        strict = cb < zb and cb < sb and mc < mz and mc < ms
        return {
            "schema": "cmpct-v030-zipfactor-recovery-native-ffi-frontier-v2",
            "contract": {
                "rounds": ROUNDS,
                "level": LEVEL,
                "group_size": GROUP_SIZE,
                "ties_fail": True,
                "cmpct_timing": "direct-fused-recovery-build-plus-v3-reconstruction-plus-inprocess-rust-strong-verify",
                "native_compile_inside_timing": False,
                "native_library_load_inside_timing": False,
                "native_ffi_call_inside_timing": True,
                "scratch_v3_publication_inside_timing": True,
                "legacy_identity_proof_inside_timing": False,
                "intermediate_v3_publication_inside_build_timing": False,
                "archive_bytes_changed": False,
                "selector_change": False,
                "release_credit": False,
            },
            "candidate": {**stats, "archive_sha256": next(iter(shas))},
            "legacy_recovery_byte_identical": legacy_recovery_byte_identical,
            "legacy_recovery_sha256": hashlib.sha256(legacy_bytes).hexdigest(),
            "direct_probe_sha256": hashlib.sha256(direct_bytes).hexdigest(),
            "probe_stats": probe_stats,
            "sizes": {"cmpct": cb, "zip": zb, "zstd19": sb},
            "samples_s": {"cmpct": cmpct, "zip": zip_s, "zstd19": zstd_s},
            "cmpct_phase_samples_s": {"build": build, "verify": verify},
            "medians_s": {"cmpct": mc, "zip": mz, "zstd19": ms},
            "cmpct_phase_medians_s": {"build": _median(build), "verify": _median(verify)},
            "recovery_semantics_passed": recovery_semantics,
            "strict_four_way_win": strict,
            "experiment_valid": (
                len(cmpct) == len(zip_s) == len(zstd_s) == ROUNDS
                and legacy_recovery_byte_identical
                and cb < zb and cb < sb
                and float(REC._snapshot(clean)["max_member_read_amplification"]) <= 8.0
                and int(REC._snapshot(clean)["max_decode_unit_bytes"]) <= 8 * 1024 * 1024
                and recovery_semantics
            ),
            "promotion_signal": strict,
            "release_credit": False,
        }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, required=True)
    p.add_argument("--native-library", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = run(a.work_root, a.native_library)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("ZIP-factor direct recovery native FFI frontier invalid")


if __name__ == "__main__":
    main()

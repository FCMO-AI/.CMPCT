#!/usr/bin/env python3
"""O9: source-exact physical PACK census + reversible singleton-owner research oracle.

Test-only: no Builder/Reader/ABI or release-policy changes. Preregistered separately.
"""
from __future__ import annotations

import binascii
import hashlib
import json
import os
from pathlib import Path
import resource
import statistics
import sys
import tempfile
import time
from collections import Counter, defaultdict

from cmpct.builder import Builder
from cmpct.codec import BHDR, BMAGIC, CODEC_RAW, CODEC_ZSTD, HDR, FTR, K_FILE, S_BLOB, S_PACK
from cmpct.reader import CMPCT

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import native_pack_heldout_o8 as o8
from native_pack_heldout_o8b import transformed

ORIGINAL = ("related_256", "independent_256", "duplicates_256", "mixed_256")
POLICIES = ("normal", "singleton_bypass", "no_pack")
REPS = 2
CODEC_NAMES = {0: "RAW", 1: "ZSTD", 2: "WAVFLAC", 3: "ZSTDDICT", 4: "DEFLATE"}
STORAGE_NAMES = {0: "BLOB", 1: "CHUNKS", 2: "VZIP", 3: "SPARSE", 4: "PACK", 5: "CDC"}
SHA = lambda b: hashlib.sha256(b).digest()


class OneDistinctBypassOracle(Builder):
    """Revert only a micro-PACK whose logical slices all address the same content.

    This post-pass tests a reversible admission alternative; not a product patch.
    Original Builder grouping and codec competition remain source-exact.
    """
    def _build_micro_packs(self):
        super()._build_micro_packs()
        owners = defaultdict(set)
        rows_by_owner = defaultdict(list)
        for row in self.files:
            if row[1] != K_FILE or not row[6] or row[6][0] != S_PACK:
                continue
            ph = bytes(row[6][1])
            candidate = self.cands.get(ph)
            if candidate is None or ".cmpct-pack" not in candidate.hints:
                continue
            owners[ph].add(bytes(row[5]))
            rows_by_owner[ph].append(row)
        self.o9_bypassed_owners = 0
        self.o9_bypassed_members = 0
        for ph, distinct in owners.items():
            if len(distinct) != 1:
                continue
            # A singleton group must contain exactly the original payload, not merely
            # have one logical hash amid another source of physical bytes.
            if next(iter(distinct)) != ph:
                raise AssertionError("one-distinct micro-PACK physical SHA is not member SHA")
            raw = self.cands[ph].raw
            for row in rows_by_owner[ph]:
                storage = row[6]
                if storage[2] != 0 or storage[3] != len(raw):
                    raise AssertionError("one-distinct PACK has nontrivial slice")
                row[6] = [S_BLOB, ph]
                self.o9_bypassed_members += 1
            self.cands[ph].hints.discard(".cmpct-pack")
            self.o9_bypassed_owners += 1


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_cases() -> dict[str, dict[str, bytes]]:
    result = {
        "o8c_" + name: transformed(o8.population(name), "txt")
        for name in ORIGINAL
    }
    related = o8.population("related_256")
    sample = next(iter(related.values()))
    noise = o8.noise(768, "o9-unique-independent-noise")
    for label, data, n in (
        ("identical_text_64", sample, 64),
        ("identical_noise_64", noise, 64),
        ("identical_zero_64", bytes(768), 64),
        ("identical_text_256", sample, 256),
        ("singleton_text_1", sample, 1),
        ("singleton_noise_1", noise, 1),
        ("singleton_zero_1", bytes(768), 1),
    ):
        result[label] = {f"member-{i:04d}.txt": data for i in range(n)}
    result["two_distinct_64"] = {
        f"distinct-{i:04d}.txt": sample if i % 2 else noise
        for i in range(64)
    }
    result["cross_bucket_singleton_64"] = {
        **{f"unique-{i:04d}.txt": v for i, v in enumerate(list(related.values())[:32])},
        **{f"same-{i:04d}.json": noise for i in range(32)},
    }
    return result


def inspect_archive(archive: Path, expected: dict[str, bytes]) -> dict:
    member_hash = {name: hashlib.sha256(data).hexdigest() for name, data in expected.items()}
    with CMPCT(archive) as reader:
        magic, version, flags, index_cs, index_us, data_span, index_sha = HDR.unpack_from(reader.mm, 0)
        assert version == 24 and reader.record_base == HDR.size + index_cs
        assert len(reader.files) == len(expected) and set(reader.by) == set(expected)
        storage_counts = Counter()
        pack_members = defaultdict(list)
        used_blob_ids = set()
        for row in reader.files:
            name, kind, mode, mtime, size, digest, storage = row
            assert kind == K_FILE and size == len(expected[name])
            assert hashlib.sha256(reader.read(name)).hexdigest() == member_hash[name]
            storage_counts[STORAGE_NAMES.get(storage[0], "UNKNOWN")] += 1
            if storage[0] in (S_PACK, S_BLOB):
                used_blob_ids.add(storage[1])
            if storage[0] == S_PACK:
                pack_members[storage[1]].append([name, storage[2], storage[3], member_hash[name]])
        codec_counts = Counter()
        pack_codecs = Counter()
        pack_distinct = {}
        physical = []
        blob_span = 0
        for idx, desc in enumerate(reader.blobs):
            off, us, cs, codec, ml = desc
            pos = reader.record_base + off
            m, c, fl, reserved, rus, rcs, rml, crc, digest = BHDR.unpack_from(reader.mm, pos)
            assert m == BMAGIC and (c, rus, rcs, rml) == (codec, us, cs, ml)
            end = pos + BHDR.size + ml + cs
            assert end <= len(reader.mm)
            raw = reader._blob(idx)
            assert len(raw) == us and SHA(raw) == digest
            assert binascii.crc32(raw) & 0xffffffff == crc
            codec_counts[CODEC_NAMES.get(codec, str(codec))] += 1
            if idx in pack_members:
                pack_codecs[CODEC_NAMES.get(codec, str(codec))] += 1
                distinct = {row[-1] for row in pack_members[idx]}
                pack_distinct[str(idx)] = len(distinct)
                for name, off0, length, member_digest in pack_members[idx]:
                    assert 0 <= off0 <= off0 + length <= us
                    assert hashlib.sha256(raw[off0:off0 + length]).hexdigest() == member_digest
            physical.append([idx, off, us, cs, codec, ml, len(pack_members.get(idx, ()))])
            blob_span += BHDR.size + ml + cs
        assert blob_span == data_span
        assert reader.record_base + data_span + index_cs + FTR.size == archive.stat().st_size, (
            reader.record_base, data_span, index_cs, archive.stat().st_size
        )
        assert used_blob_ids <= set(range(len(reader.blobs)))
        return {
            "whole_archive_bytes": archive.stat().st_size,
            "index_compressed_bytes": index_cs,
            "index_uncompressed_bytes": index_us,
            "physical_blob_count": len(reader.blobs),
            "physical_blob_frame_bytes": blob_span,
            "physical_payload_bytes": sum(x[3] for x in reader.blobs),
            "unique_content_sha_count": len(set(member_hash.values())),
            "member_storage_counts": dict(storage_counts),
            "all_blob_codec_counts": dict(codec_counts),
            "physical_pack_codec_counts": dict(pack_codecs),
            "pack_member_counts": {str(k): len(v) for k, v in pack_members.items()},
            "pack_distinct_logical_sha_counts": pack_distinct,
            "physical_blob_table": physical,
            "sha256": sha_file(archive),
        }


def build_once(source: Path, archive: Path, policy: str, expected: dict[str, bytes]) -> dict:
    assert policy in POLICIES
    env_key = "CMPCT_MICRO_PACK_MAX_FILE"
    old_env = os.environ.get(env_key)
    if old_env is not None:
        raise AssertionError("uncontrolled pre-existing micro-PACK environment")
    try:
        if policy == "no_pack":
            os.environ[env_key] = "0"
        build_class = OneDistinctBypassOracle if policy == "singleton_bypass" else Builder
        start_cpu = time.process_time_ns()
        start_wall = time.perf_counter_ns()
        builder = build_class(source, workers=1, reproducible=True)
        builder.build(archive)
        wall = (time.perf_counter_ns() - start_wall) / 1e6
        cpu = (time.process_time_ns() - start_cpu) / 1e6
    finally:
        if old_env is None:
            os.environ.pop(env_key, None)
        else:
            os.environ[env_key] = old_env
    result = inspect_archive(archive, expected)
    result["policy"] = policy
    result["build_wall_ms"] = wall
    result["build_cpu_ms"] = cpu
    result["bypassed_physical_owners"] = getattr(builder, "o9_bypassed_owners", 0)
    result["bypassed_logical_members"] = getattr(builder, "o9_bypassed_members", 0)
    return result


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python tests/native_pack_physical_singleton_o9.py RECEIPT_JSON")
    cases = make_cases()
    report = {
        "schema": "cmpct-native-physical-singleton-o9-v1",
        "prereg": "docs/v031-research/NATIVE_PACK_PHYSICAL_SINGLETON_O9_PREREG.md",
        "starting_source_head": "779b5158aa40fe842e746848731f16f4f6fce36e",
        "families": {},
        "status": "RUNNING",
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-native-o9-") as tmp:
        root = Path(tmp)
        for label, content in cases.items():
            area = root / label
            source = area / "source"
            source.mkdir(parents=True)
            for name, payload in content.items():
                assert "/" not in name and "\\" not in name and "\x00" not in name
                (source / name).write_bytes(payload)
            manifest_before = {p.name: sha_file(p) for p in source.iterdir()}
            rows = {p: [] for p in POLICIES}
            for iteration in range(REPS):
                order = POLICIES if iteration % 2 == 0 else tuple(reversed(POLICIES))
                for policy in order:
                    archive = area / f"{policy}-{iteration}.cmpct"
                    one = build_once(source, archive, policy, content)
                    assert {p.name: sha_file(p) for p in source.iterdir()} == manifest_before
                    rows[policy].append(one)
            policies = {}
            for policy, recs in rows.items():
                assert len({r["sha256"] for r in recs}) == 1, (label, policy, "nondeterministic archive")
                assert len({r["whole_archive_bytes"] for r in recs}) == 1
                first = dict(recs[0])
                first["build_wall_median_ms"] = statistics.median(r["build_wall_ms"] for r in recs)
                first["build_cpu_median_ms"] = statistics.median(r["build_cpu_ms"] for r in recs)
                first["raw_repeats"] = recs
                policies[policy] = first
            report["families"][label] = {
                "file_count": len(content),
                "unique_content_count": len(set(manifest_before.values())),
                "logical_bytes": sum(map(len, content.values())),
                "policies": policies,
                "singleton_bypass_minus_normal_bytes": (
                    policies["singleton_bypass"]["whole_archive_bytes"] - policies["normal"]["whole_archive_bytes"]
                ),
                "no_pack_minus_normal_bytes": (
                    policies["no_pack"]["whole_archive_bytes"] - policies["normal"]["whole_archive_bytes"]
                ),
            }
            print(json.dumps({
                "case": label,
                "unique": report["families"][label]["unique_content_count"],
                "normal": policies["normal"]["whole_archive_bytes"],
                "bypass": policies["singleton_bypass"]["whole_archive_bytes"],
                "no_pack": policies["no_pack"]["whole_archive_bytes"],
                "bypassed": policies["singleton_bypass"]["bypassed_logical_members"],
                "normal_pack_codecs": policies["normal"]["physical_pack_codec_counts"],
            }, sort_keys=True), flush=True)
    report["summary"] = {
        "cases": len(cases),
        "complete_builds": len(cases) * len(POLICIES) * REPS,
        "complete_exact_reconstructions": len(cases) * len(POLICIES) * REPS,
        "oracle_byte_loss_cases": [
            name for name, r in report["families"].items()
            if r["singleton_bypass_minus_normal_bytes"] > 0
        ],
        "oracle_byte_win_cases": [
            name for name, r in report["families"].items()
            if r["singleton_bypass_minus_normal_bytes"] < 0
        ],
        "oracle_byte_tie_cases": [
            name for name, r in report["families"].items()
            if r["singleton_bypass_minus_normal_bytes"] == 0
        ],
    }
    report["status"] = "O9_COMPLETE_WITH_NEGATIVES_PRESERVED"
    target = Path(sys.argv[1])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

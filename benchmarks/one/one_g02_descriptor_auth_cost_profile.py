"""ONE-G0.2 control-authentication compute/debt profile.

Referee freeze before result-bearing execution
==============================================
The selective descriptor-tree transfer restored the frozen density + authenticated-access gate,
but it added a Merkle structure.  This diagnostic charges that exported debt against the exact
whole-manifest design it replaced, on the same version families and Surprise payloads.

Hypothesis: descriptor-tree authentication does not merely move the locality bill into excessive
hash input work.  At V=8 it should reduce BOTH selective-read hash-input bytes and single-version
update hash-input bytes relative to whole-manifest authentication, while exposing any increase in
hash invocation count, stored control-auth metadata and proof hashes.  Creation cost is reported,
not gifted, and is allowed to rise because it is an encoder-side one-time bill; no promotion claim
is made from this diagnostic alone.

Disproof: if either V=8 read hash-input bytes or V=8 one-version update hash-input bytes are not
strictly lower, selective descriptor authentication has only displaced the compute debt and needs
concept compression before further promotion.  No access or density threshold may be changed.

Common basis-tree hashing/proof work and payload reconstruction are excluded from BOTH sides: they
are identical in the paired experiment. SHA-256 input byte accounting includes domain separators,
indices/level tags and the bytes actually fed to each hash. Surprise SHA-256 is charged wherever
used. Update means one existing derived version's descriptor/Surprise changes while V is fixed.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import struct
from statistics import mean

from benchmarks.one.one_g02_epoch_min_edited_version_transfer import MASTER_SEED, _edited
from benchmarks.one.one_g02_shared_graph_auth_pair import _surprise_blob
from benchmarks.one.one_g02_shared_graph_auth_multiversion import ROOT_SIZES, BASES_PER_SIZE, MUTATIONS, VERSION_COUNTS

OLD_DOMAIN = b"ONE-GMV-ROOT\0"
NEW_ROOT_DOMAIN = b"ONE-GMV2-ROOT\0"
LEAF_DOMAIN = b"ONE-GDESC-L\0"
PARENT_DOMAIN = b"ONE-GDESC-P\0"
OLD_FIXED = 8 + 16 + 32
OLD_DESC = 72
NEW_HEADER = 8 + 4 + 4 + 32 + 32
NEW_CONTROL = 40
HASH_BYTES = 32


def _parent_count(n: int) -> int:
    total = 0
    width = n
    while width > 1:
        width = (width + 1) // 2
        total += width
    return total


def _proof_depth(n: int) -> int:
    depth = 0
    width = n
    while width > 1:
        width = (width + 1) // 2
        depth += 1
    return depth


def _old_cost(count: int, surprise_len: int, all_surprise_lens: list[int]) -> dict[str, int]:
    manifest = OLD_FIXED + OLD_DESC * count
    # creation: every Surprise digest + graph-root commitment over complete manifest.
    create_ops = count + 1
    create_input = sum(all_surprise_lens) + len(OLD_DOMAIN) + manifest
    # selective read: authenticate whole manifest + target Surprise.
    read_ops = 2
    read_input = len(OLD_DOMAIN) + manifest + surprise_len
    # update one target: new Surprise digest + new whole-manifest graph root.
    update_ops = 2
    update_input = surprise_len + len(OLD_DOMAIN) + manifest
    return {
        "persisted_control_auth_bytes": manifest,
        "selective_proof_bytes": 0,
        "create_hash_ops": create_ops,
        "create_hash_input_bytes": create_input,
        "read_hash_ops": read_ops,
        "read_hash_input_bytes": read_input,
        "update_hash_ops": update_ops,
        "update_hash_input_bytes": update_input,
    }


def _new_cost(count: int, surprise_len: int, all_surprise_lens: list[int]) -> dict[str, int]:
    parents = _parent_count(count)
    depth = _proof_depth(count)
    # Descriptor tree stores all leaves plus every non-root internal hash; root lives in header.
    stored_tree_hashes = count + parents - 1
    persisted = NEW_HEADER + NEW_CONTROL * count + HASH_BYTES * stored_tree_hashes

    # Leaf hash: domain + u32 index + 40-byte control + 32-byte Surprise digest.
    leaf_input = len(LEAF_DOMAIN) + 4 + NEW_CONTROL + HASH_BYTES
    # Parent hash: domain + u32 level + two child digests.
    parent_input = len(PARENT_DOMAIN) + 4 + HASH_BYTES * 2
    root_input = len(NEW_ROOT_DOMAIN) + NEW_HEADER

    # creation: every Surprise digest, every descriptor leaf, every internal parent, graph root.
    create_ops = count + count + parents + 1
    create_input = (
        sum(all_surprise_lens)
        + count * leaf_input
        + parents * parent_input
        + root_input
    )
    # read: graph root, target Surprise digest, target leaf, one parent hash per proof level.
    read_ops = 1 + 1 + 1 + depth
    read_input = root_input + surprise_len + leaf_input + depth * parent_input
    # update: target Surprise digest + target leaf + path parents + graph root.
    update_ops = 1 + 1 + depth + 1
    update_input = surprise_len + leaf_input + depth * parent_input + root_input
    return {
        "persisted_control_auth_bytes": persisted,
        "selective_proof_bytes": depth * HASH_BYTES,
        "create_hash_ops": create_ops,
        "create_hash_input_bytes": create_input,
        "read_hash_ops": read_ops,
        "read_hash_input_bytes": read_input,
        "update_hash_ops": update_ops,
        "update_hash_input_bytes": update_input,
    }


def run() -> dict[str, object]:
    master = random.Random(MASTER_SEED ^ 0xA071FA11)
    rows = []
    for size in ROOT_SIZES:
        for base_index in range(BASES_PER_SIZE):
            seed = master.getrandbits(64)
            base = random.Random(seed).randbytes(size)
            blobs = []
            for m in MUTATIONS:
                edited = _edited(base, random.Random(seed ^ (m << 32) ^ 0xA11CE5EED), m)
                blob, _ = _surprise_blob(base, edited)
                blobs.append(blob)
            for count in VERSION_COUNTS:
                lens = [len(x) for x in blobs[:count]]
                for version, surprise_len in enumerate(lens):
                    old = _old_cost(count, surprise_len, lens)
                    new = _new_cost(count, surprise_len, lens)
                    rows.append({
                        "root_bytes": size,
                        "base_index": base_index,
                        "version_count": count,
                        "version": version,
                        "surprise_bytes": surprise_len,
                        "old": old,
                        "selective_descriptor": new,
                        "read_hash_input_ratio": new["read_hash_input_bytes"] / old["read_hash_input_bytes"],
                        "update_hash_input_ratio": new["update_hash_input_bytes"] / old["update_hash_input_bytes"],
                        "create_hash_input_ratio": new["create_hash_input_bytes"] / old["create_hash_input_bytes"],
                        "read_hash_op_delta": new["read_hash_ops"] - old["read_hash_ops"],
                        "update_hash_op_delta": new["update_hash_ops"] - old["update_hash_ops"],
                    })

    summaries = {}
    for count in VERSION_COUNTS:
        group = [r for r in rows if r["version_count"] == count]
        summaries[str(count)] = {
            "rows": len(group),
            "old_persisted_control_auth_bytes": group[0]["old"]["persisted_control_auth_bytes"],
            "new_persisted_control_auth_bytes": group[0]["selective_descriptor"]["persisted_control_auth_bytes"],
            "new_selective_proof_bytes": group[0]["selective_descriptor"]["selective_proof_bytes"],
            "mean_read_hash_input_ratio": mean(r["read_hash_input_ratio"] for r in group),
            "max_read_hash_input_ratio": max(r["read_hash_input_ratio"] for r in group),
            "mean_update_hash_input_ratio": mean(r["update_hash_input_ratio"] for r in group),
            "max_update_hash_input_ratio": max(r["update_hash_input_ratio"] for r in group),
            "mean_create_hash_input_ratio": mean(r["create_hash_input_ratio"] for r in group),
            "max_create_hash_input_ratio": max(r["create_hash_input_ratio"] for r in group),
            "new_read_hash_ops": group[0]["selective_descriptor"]["read_hash_ops"],
            "old_read_hash_ops": group[0]["old"]["read_hash_ops"],
            "new_update_hash_ops": group[0]["selective_descriptor"]["update_hash_ops"],
            "old_update_hash_ops": group[0]["old"]["update_hash_ops"],
            "new_create_hash_ops": group[0]["selective_descriptor"]["create_hash_ops"],
            "old_create_hash_ops": group[0]["old"]["create_hash_ops"],
        }

    v8 = [r for r in rows if r["version_count"] == 8]
    passes = (
        max(r["read_hash_input_ratio"] for r in v8) < 1.0
        and max(r["update_hash_input_ratio"] for r in v8) < 1.0
    )
    return {
        "schema": "cmpct-one-g02-descriptor-auth-cost-profile-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "accounting_scope": "control authentication only; identical basis proof/reconstruction excluded symmetrically",
        "summaries": summaries,
        "v8_frozen_disproof_passed": passes,
        "decision": "descriptor_auth_compute_debt_bounded_at_v8" if passes else "descriptor_auth_displaces_compute_debt",
        "claim_boundary": "deterministic SHA-256 work accounting diagnostic; no native wall-clock, full-corpus or release authority",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))

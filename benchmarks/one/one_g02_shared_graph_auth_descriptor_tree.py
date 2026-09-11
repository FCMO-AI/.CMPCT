"""ONE-G0.2 selectively authenticated generic graph-descriptor transfer.

Mission lock / Referee freeze before result-bearing execution
============================================================
The frozen multi-version transfer proved that shared Law+Surprise density improves as one
basis serves more derived roots, but a reader that authenticates the complete 632-byte graph
manifest breaches the <=1.20x median authenticated 4 KiB traffic gate at eight versions.

Hypothesis: authenticate graph control at the reconstruction-cone boundary.  Keep the same
72-byte logical descriptor information, but do not duplicate the already-required Surprise
SHA-256 digest inside the descriptor payload: the digest becomes an input to that descriptor's
Merkle leaf commitment.  A selective reader fetches the fixed authenticated graph header,
the requested descriptor control, the requested complete Surprise blob, and a binary Merkle
proof for that descriptor.  Unrelated descriptors are neither read nor trusted.

This is ONE-native generic control addressability, not a temporal/version opcode.  The Law
control remains the same 32 bytes and Surprise length remains the same 8 bytes as the prior
experiment.  The only concept compression is eliminating a duplicate digest field by reusing
the digest already needed to authenticate the Surprise payload.

Frozen corpus, basis AuthTree geometry, version families, mutation counts, leaf grid and every
byte alignment are IDENTICAL to one_g02_shared_graph_auth_multiversion.py.

All costs are charged:
- graph header: total length, basis leaf size, descriptor count, basis root, descriptor root;
- every 40-byte descriptor control (32-byte Law + 8-byte Surprise length);
- all non-root descriptor-tree hashes, including descriptor leaf commitments;
- every basis-tree non-root hash;
- all Surprise bytes;
- selective traffic includes the complete graph header, requested descriptor control,
  requested complete Surprise, descriptor proof hashes, basis proof hashes and basis payload.
The graph commitment replaces an already-required root digest and is not double charged.

Frozen advancement gate: a basis leaf transfers only if for EVERY family prefix/target row,
(1) complete persisted bytes are strictly below the same unauthenticated independent-literal
family used by the prior transfer; (2) median authenticated 4 KiB traffic <=1.20x; (3) exact
reconstruction succeeds for every alignment; and (4) deterministic corruption tests reject
header, descriptor control, Surprise and descriptor-proof mutations.

Disproof: if no frozen basis leaf passes without hiding descriptor-tree bytes/proofs, then
standard selectively authenticated descriptor addressability is insufficient and the next
Builder must change the control representation rather than raise the access threshold.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import random
import struct
from statistics import median

from benchmarks.one.one_g02_epoch_min_edited_version_transfer import MASTER_SEED, _edited
from benchmarks.one.one_g02_shared_graph_auth_pair import _surprise_blob, _apply_range
from benchmarks.one.one_g02_shared_graph_auth_multiversion import (
    ROOT_SIZES, BASES_PER_SIZE, MUTATIONS, VERSION_COUNTS, LEAF_GRID,
    REQUEST_BYTES, MAX_MEDIAN_TOUCH_AMP, LAW_CONTROL_BYTES,
)
from experiments.one.auth_tree import build_auth_tree, prove_range, verify_range

HASH_BYTES = 32
DESC_CONTROL_BYTES = LAW_CONTROL_BYTES + 8
HEADER_BYTES = 8 + 4 + 4 + HASH_BYTES + HASH_BYTES  # total, leaf, count, basis root, descriptor root


def _law_control(index: int) -> bytes:
    return (f"ONE-TRANSLATION-{index}".encode()).ljust(LAW_CONTROL_BYTES, b"\0")[:LAW_CONTROL_BYTES]


def _desc_control(index: int, surprise: bytes) -> bytes:
    return _law_control(index) + struct.pack("<Q", len(surprise))


def _desc_leaf(index: int, control: bytes, surprise_digest: bytes) -> bytes:
    if len(control) != DESC_CONTROL_BYTES or len(surprise_digest) != HASH_BYTES:
        raise ValueError("bad descriptor leaf input")
    return hashlib.sha256(b"ONE-GDESC-L\0" + struct.pack("<I", index) + control + surprise_digest).digest()


def _desc_parent(level: int, left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(b"ONE-GDESC-P\0" + struct.pack("<I", level) + left + right).digest()


@dataclass(frozen=True)
class DescriptorTree:
    levels: tuple[tuple[bytes, ...], ...]

    @property
    def root(self) -> bytes:
        return self.levels[-1][0]

    @property
    def stored_nonroot_hash_bytes(self) -> int:
        return HASH_BYTES * (sum(len(level) for level in self.levels) - 1)


def _build_desc_tree(controls: list[bytes], surprises: list[bytes]) -> DescriptorTree:
    if not controls or len(controls) != len(surprises):
        raise ValueError("descriptor tree requires matched non-empty vectors")
    current = tuple(
        _desc_leaf(i, controls[i], hashlib.sha256(surprises[i]).digest())
        for i in range(len(controls))
    )
    levels = [current]
    level_no = 1
    while len(current) > 1:
        nxt = []
        for i in range(0, len(current), 2):
            left = current[i]
            right = current[i + 1] if i + 1 < len(current) else left
            nxt.append(_desc_parent(level_no, left, right))
        current = tuple(nxt)
        levels.append(current)
        level_no += 1
    return DescriptorTree(tuple(levels))


def _desc_proof(tree: DescriptorTree, index: int) -> tuple[tuple[int, int, bytes], ...]:
    if index < 0 or index >= len(tree.levels[0]):
        raise ValueError("descriptor index out of range")
    proof = []
    current = index
    for level_no, level in enumerate(tree.levels[:-1]):
        sibling = current ^ 1
        if sibling < len(level):
            proof.append((level_no, sibling, level[sibling]))
        current //= 2
    return tuple(proof)


def _verify_desc(
    *, index: int, count: int, control: bytes, surprise: bytes,
    proof: tuple[tuple[int, int, bytes], ...], expected_root: bytes,
) -> None:
    if index < 0 or index >= count or count <= 0 or len(expected_root) != HASH_BYTES:
        raise ValueError("invalid descriptor verification request")
    nodes: dict[tuple[int, int], bytes] = {
        (0, index): _desc_leaf(index, control, hashlib.sha256(surprise).digest())
    }
    for level, sibling, digest in proof:
        if len(digest) != HASH_BYTES:
            raise ValueError("bad descriptor proof hash")
        nodes[(level, sibling)] = digest
    width = count
    current = index
    level_no = 0
    while width > 1:
        parent = current // 2
        li = 2 * parent
        ri = li + 1
        left = nodes.get((level_no, li))
        right = nodes.get((level_no, ri))
        if ri >= width and left is not None:
            right = left
        if left is None or right is None:
            raise ValueError("incomplete descriptor proof")
        nodes[(level_no + 1, parent)] = _desc_parent(level_no + 1, left, right)
        current = parent
        width = (width + 1) // 2
        level_no += 1
    if nodes.get((level_no, 0)) != expected_root:
        raise ValueError("descriptor authentication failed")


def _header(total: int, leaf: int, count: int, basis_root: bytes, descriptor_root: bytes) -> bytes:
    out = struct.pack("<QII", total, leaf, count) + basis_root + descriptor_root
    if len(out) != HEADER_BYTES:
        raise AssertionError("header accounting drift")
    return out


def _graph_root(header: bytes) -> bytes:
    return hashlib.sha256(b"ONE-GMV2-ROOT\0" + header).digest()


def run() -> dict[str, object]:
    master = random.Random(MASTER_SEED ^ 0xA071FA11)
    rows = []
    exact_failures = []
    corruption_failures = []

    for size in ROOT_SIZES:
        for base_index in range(BASES_PER_SIZE):
            seed = master.getrandbits(64)
            base = random.Random(seed).randbytes(size)
            edited = []
            blobs = []
            diffs = []
            for m in MUTATIONS:
                e = _edited(base, random.Random(seed ^ (m << 32) ^ 0xA11CE5EED), m)
                b, d = _surprise_blob(base, e)
                edited.append(e)
                blobs.append(b)
                diffs.append(d)
            basis_trees = {leaf: build_auth_tree(base, leaf) for leaf in LEAF_GRID}

            for count in VERSION_COUNTS:
                chosen_blobs = blobs[:count]
                controls = [_desc_control(i, chosen_blobs[i]) for i in range(count)]
                desc_tree = _build_desc_tree(controls, chosen_blobs)
                desc_hash_bytes = desc_tree.stored_nonroot_hash_bytes
                all_control_bytes = DESC_CONTROL_BYTES * count

                for leaf in LEAF_GRID:
                    basis_tree = basis_trees[leaf]
                    header = _header(size, leaf, count, basis_tree.root, desc_tree.root)
                    graph_root = _graph_root(header)
                    basis_hash_bytes = basis_tree.stored_index_bytes - 4
                    persisted = (
                        size + basis_hash_bytes + len(header) + all_control_bytes
                        + desc_hash_bytes + sum(len(b) for b in chosen_blobs)
                    )
                    literal_family = (count + 1) * size

                    for version in range(count):
                        proof_desc = _desc_proof(desc_tree, version)
                        desc_proof_bytes = HASH_BYTES * len(proof_desc)
                        amps = []
                        failures = []
                        for mod in range(leaf):
                            center = (size - REQUEST_BYTES) // 2
                            start = center - center % leaf + mod
                            if start + REQUEST_BYTES > size:
                                start -= leaf
                            basis_proof = prove_range(base, basis_tree, start, REQUEST_BYTES)
                            try:
                                if _graph_root(header) != graph_root:
                                    raise ValueError("graph header")
                                _verify_desc(
                                    index=version, count=count, control=controls[version],
                                    surprise=chosen_blobs[version], proof=proof_desc,
                                    expected_root=desc_tree.root,
                                )
                                basis_range = verify_range(basis_proof, basis_tree.root, start, REQUEST_BYTES)
                                got = _apply_range(basis_range, start, diffs[version])
                                if got != edited[version][start:start + REQUEST_BYTES]:
                                    raise ValueError("reconstruction")
                            except Exception as exc:
                                failures.append({"alignment": mod, "reason": type(exc).__name__})
                            touched = (
                                len(header) + DESC_CONTROL_BYTES + len(chosen_blobs[version])
                                + desc_proof_bytes + basis_proof.touched_data_bytes
                                + basis_proof.touched_proof_bytes
                            )
                            amps.append(touched / REQUEST_BYTES)
                        if failures:
                            exact_failures.append({
                                "root_bytes": size, "base_index": base_index,
                                "version_count": count, "version": version,
                                "leaf": leaf, "failures": failures,
                            })

                        # Deterministic hostile checks once per row. Each mutation must break a
                        # commitment that is actually consumed by the selective path.
                        hostile = []
                        bad_header = bytearray(header); bad_header[0] ^= 1
                        if _graph_root(bytes(bad_header)) == graph_root:
                            hostile.append("header_corruption_accepted")
                        bad_control = bytearray(controls[version]); bad_control[0] ^= 1
                        try:
                            _verify_desc(index=version, count=count, control=bytes(bad_control),
                                         surprise=chosen_blobs[version], proof=proof_desc,
                                         expected_root=desc_tree.root)
                            hostile.append("descriptor_control_corruption_accepted")
                        except ValueError:
                            pass
                        if chosen_blobs[version]:
                            bad_surprise = bytearray(chosen_blobs[version]); bad_surprise[-1] ^= 1
                            try:
                                _verify_desc(index=version, count=count, control=controls[version],
                                             surprise=bytes(bad_surprise), proof=proof_desc,
                                             expected_root=desc_tree.root)
                                hostile.append("surprise_corruption_accepted")
                            except ValueError:
                                pass
                        if proof_desc:
                            bad_proof = list(proof_desc)
                            lvl, idx, dig = bad_proof[0]
                            damaged = bytearray(dig); damaged[0] ^= 1
                            bad_proof[0] = (lvl, idx, bytes(damaged))
                            try:
                                _verify_desc(index=version, count=count, control=controls[version],
                                             surprise=chosen_blobs[version], proof=tuple(bad_proof),
                                             expected_root=desc_tree.root)
                                hostile.append("descriptor_proof_corruption_accepted")
                            except ValueError:
                                pass
                        if hostile:
                            corruption_failures.append({
                                "root_bytes": size, "base_index": base_index,
                                "version_count": count, "version": version,
                                "leaf": leaf, "failures": hostile,
                            })

                        rows.append({
                            "root_bytes": size,
                            "base_index": base_index,
                            "version_count": count,
                            "version": version,
                            "mutation_count": MUTATIONS[version],
                            "leaf_bytes": leaf,
                            "graph_header_bytes": len(header),
                            "descriptor_control_bytes": DESC_CONTROL_BYTES,
                            "descriptor_tree_hash_bytes": desc_hash_bytes,
                            "descriptor_proof_bytes": desc_proof_bytes,
                            "target_surprise_bytes": len(chosen_blobs[version]),
                            "basis_tree_hash_bytes": basis_hash_bytes,
                            "candidate_persisted_bytes": persisted,
                            "literal_family_bytes": literal_family,
                            "candidate_fraction_of_literal_family": persisted / literal_family,
                            "median_authenticated_touch_amplification": median(amps),
                            "max_authenticated_touch_amplification": max(amps),
                        })

    summaries = {}
    candidates = []
    for leaf in LEAF_GRID:
        group = [r for r in rows if r["leaf_bytes"] == leaf]
        summary = {
            "rows": len(group),
            "max_candidate_fraction_of_literal_family": max(r["candidate_fraction_of_literal_family"] for r in group),
            "max_row_median_touch_amplification": max(r["median_authenticated_touch_amplification"] for r in group),
            "max_touch_amplification": max(r["max_authenticated_touch_amplification"] for r in group),
            "v8_max_descriptor_tree_hash_bytes": max(r["descriptor_tree_hash_bytes"] for r in group if r["version_count"] == 8),
            "v8_max_descriptor_proof_bytes": max(r["descriptor_proof_bytes"] for r in group if r["version_count"] == 8),
        }
        summaries[str(leaf)] = summary
        if (
            summary["max_candidate_fraction_of_literal_family"] < 1.0
            and summary["max_row_median_touch_amplification"] <= MAX_MEDIAN_TOUCH_AMP
        ):
            candidates.append(leaf)

    return {
        "schema": "cmpct-one-g02-shared-graph-auth-descriptor-tree-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "version_counts": list(VERSION_COUNTS),
        "mutation_counts": list(MUTATIONS),
        "leaf_grid": list(LEAF_GRID),
        "request_bytes": REQUEST_BYTES,
        "max_median_touch_amplification": MAX_MEDIAN_TOUCH_AMP,
        "exact_failures": exact_failures,
        "corruption_failures": corruption_failures,
        "target_candidates": candidates,
        "summaries": summaries,
        "decision": (
            "selective_descriptor_auth_restores_multiversion_transfer"
            if candidates and not exact_failures and not corruption_failures
            else "selective_descriptor_auth_insufficient"
        ),
        "claim_boundary": "generic graph-control addressability transfer only; no v0.29/v0.30, canonical-wire, native-speed or release authority",
        "results": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))

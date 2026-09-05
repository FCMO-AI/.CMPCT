"""ONE-G0.2 full quaternary descriptor-authentication A/B.

Frozen after the corrected arity prefilter selected arity 4. This changes only the generic
descriptor authentication tree from binary to quaternary; Law controls, Surprise payloads,
basis AuthTree geometry, corpus, version families, density comparator and <=1.20x median 4 KiB
authenticated-touch law remain unchanged.

The instrument independently constructs and verifies a domain-separated 4-way descriptor tree
for every frozen family prefix and target, injects deterministic control/Surprise/proof/root
corruption, then replays the exact successful binary reconstruction rows with the quaternary
stored-hash and proof-byte costs. Basis reconstruction is deliberately not reimplemented: the
binary instrument is rerun in-process and must itself remain exact/corruption-clean.

Advance only if: binary source rows remain exact; every quaternary descriptor verifies; every
hostile mutation is rejected; and at least one frozen basis leaf beats independent literals and
stays <=1.20x median authenticated touch on every row. No threshold tuning after execution.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json, os, random, struct

from benchmarks.one.one_g02_epoch_min_edited_version_transfer import MASTER_SEED, _edited
from benchmarks.one.one_g02_shared_graph_auth_pair import _surprise_blob
from benchmarks.one.one_g02_shared_graph_auth_multiversion import (
    ROOT_SIZES, BASES_PER_SIZE, MUTATIONS, VERSION_COUNTS, LEAF_GRID, MAX_MEDIAN_TOUCH_AMP,
)
from benchmarks.one.one_g02_shared_graph_auth_descriptor_tree import (
    run as binary_run, _desc_control, _desc_leaf, _header, _graph_root,
)

ARITY = 4
HASH_BYTES = 32
PARENT_DOMAIN = b"ONE-GDESC-QP\0"


def _parent(level: int, children: tuple[bytes, ...]) -> bytes:
    if not children or len(children) > ARITY or any(len(x) != HASH_BYTES for x in children):
        raise ValueError("invalid quaternary children")
    return hashlib.sha256(PARENT_DOMAIN + struct.pack("<II", level, len(children)) + b"".join(children)).digest()


@dataclass(frozen=True)
class QTree:
    levels: tuple[tuple[bytes, ...], ...]
    @property
    def root(self) -> bytes: return self.levels[-1][0]
    @property
    def stored_nonroot_hash_bytes(self) -> int:
        return HASH_BYTES * (sum(len(x) for x in self.levels) - 1)


def _build(controls: list[bytes], surprises: list[bytes]) -> QTree:
    cur = tuple(_desc_leaf(i, controls[i], hashlib.sha256(surprises[i]).digest()) for i in range(len(controls)))
    levels = [cur]
    level = 1
    while len(cur) > 1:
        cur = tuple(_parent(level, cur[i:i+ARITY]) for i in range(0, len(cur), ARITY))
        levels.append(cur); level += 1
    return QTree(tuple(levels))


def _proof(tree: QTree, index: int) -> tuple[tuple[int, int, int, tuple[tuple[int, bytes], ...]], ...]:
    out = []; cur = index
    for level_no, level in enumerate(tree.levels[:-1]):
        start = (cur // ARITY) * ARITY; stop = min(start + ARITY, len(level))
        siblings = tuple((i - start, level[i]) for i in range(start, stop) if i != cur)
        out.append((level_no, cur - start, stop - start, siblings)); cur //= ARITY
    return tuple(out)


def _verify(index: int, count: int, control: bytes, surprise: bytes, proof, root: bytes) -> None:
    if index < 0 or index >= count: raise ValueError("index")
    h = _desc_leaf(index, control, hashlib.sha256(surprise).digest())
    cur, width = index, count
    for expected_level, (level_no, slot, child_count, siblings) in enumerate(proof):
        if level_no != expected_level or slot != cur % ARITY or child_count != min(ARITY, width - (cur//ARITY)*ARITY):
            raise ValueError("proof geometry")
        children = [None] * child_count; children[slot] = h
        for sibling_slot, digest in siblings:
            if sibling_slot < 0 or sibling_slot >= child_count or children[sibling_slot] is not None or len(digest) != HASH_BYTES:
                raise ValueError("proof sibling")
            children[sibling_slot] = digest
        if any(x is None for x in children): raise ValueError("incomplete proof")
        h = _parent(level_no + 1, tuple(children))
        cur //= ARITY; width = (width + ARITY - 1) // ARITY
    if h != root: raise ValueError("descriptor authentication failed")


def run() -> dict[str, object]:
    binary = binary_run()
    if binary["exact_failures"] or binary["corruption_failures"]:
        return {"schema":"cmpct-one-g02-descriptor-auth-quaternary-v1","decision":"blocked_by_binary_baseline_failure","binary":binary}

    auth_failures = []; corruption_failures = []; shapes = {}
    master = random.Random(MASTER_SEED ^ 0xA071FA11)
    for size in ROOT_SIZES:
        for base_index in range(BASES_PER_SIZE):
            seed = master.getrandbits(64); base = random.Random(seed).randbytes(size)
            surprises = []
            for m in MUTATIONS:
                edited = _edited(base, random.Random(seed ^ (m << 32) ^ 0xA11CE5EED), m)
                blob, _ = _surprise_blob(base, edited); surprises.append(blob)
            for count in VERSION_COUNTS:
                blobs = surprises[:count]; controls = [_desc_control(i, blobs[i]) for i in range(count)]
                tree = _build(controls, blobs)
                proof_sizes = []
                for version in range(count):
                    proof = _proof(tree, version); proof_sizes.append(sum(len(s) for _,_,_,s in proof)*HASH_BYTES)
                    try: _verify(version, count, controls[version], blobs[version], proof, tree.root)
                    except Exception as exc: auth_failures.append({"root":size,"base":base_index,"count":count,"version":version,"reason":type(exc).__name__})
                    bad = bytearray(controls[version]); bad[0] ^= 1
                    try: _verify(version,count,bytes(bad),blobs[version],proof,tree.root); corruption_failures.append("control")
                    except ValueError: pass
                    if blobs[version]:
                        bad = bytearray(blobs[version]); bad[-1] ^= 1
                        try: _verify(version,count,controls[version],bytes(bad),proof,tree.root); corruption_failures.append("surprise")
                        except ValueError: pass
                    if proof and proof[0][3]:
                        mutable = [list(x) for x in proof]; sibs = list(mutable[0][3]); ss, dig = sibs[0]; bd = bytearray(dig); bd[0] ^= 1; sibs[0]=(ss,bytes(bd)); mutable[0][3]=tuple(sibs)
                        try: _verify(version,count,controls[version],blobs[version],tuple(tuple(x) for x in mutable),tree.root); corruption_failures.append("proof")
                        except ValueError: pass
                shapes[str(count)] = {"stored_hash_bytes":tree.stored_nonroot_hash_bytes,"max_proof_bytes":max(proof_sizes)}

    adjusted = []
    for row in binary["results"]:
        shape = shapes[str(row["version_count"])]
        persisted = row["candidate_persisted_bytes"] + shape["stored_hash_bytes"] - row["descriptor_tree_hash_bytes"]
        med = row["median_authenticated_touch_amplification"] + (shape["max_proof_bytes"] - row["descriptor_proof_bytes"]) / 4096
        mx = row["max_authenticated_touch_amplification"] + (shape["max_proof_bytes"] - row["descriptor_proof_bytes"]) / 4096
        adjusted.append({**row,"quaternary_persisted_bytes":persisted,"quaternary_fraction_of_literal_family":persisted/row["literal_family_bytes"],"quaternary_median_touch_amplification":med,"quaternary_max_touch_amplification":mx})

    summaries = {}; candidates=[]
    for leaf in LEAF_GRID:
        group=[r for r in adjusted if r["leaf_bytes"]==leaf]
        s={"max_candidate_fraction_of_literal_family":max(r["quaternary_fraction_of_literal_family"] for r in group),"max_row_median_touch_amplification":max(r["quaternary_median_touch_amplification"] for r in group),"max_touch_amplification":max(r["quaternary_max_touch_amplification"] for r in group)}
        s["passes"] = s["max_candidate_fraction_of_literal_family"] < 1.0 and s["max_row_median_touch_amplification"] <= MAX_MEDIAN_TOUCH_AMP
        summaries[str(leaf)] = s
        if s["passes"]: candidates.append(leaf)
    decision = "advance_quaternary_descriptor_auth" if candidates and not auth_failures and not corruption_failures else "retain_binary_descriptor_auth"
    return {"schema":"cmpct-one-g02-descriptor-auth-quaternary-v1","experimental_version":"ONE-G0.2","source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","arity":ARITY,"auth_failures":auth_failures,"corruption_failures":corruption_failures,"shapes":shapes,"candidate_leaves":candidates,"summaries":summaries,"decision":decision,"claim_boundary":"full descriptor-auth structural A/B; basis semantics inherited from rerun exact binary instrument; no native speed or release authority"}

if __name__ == "__main__": print(json.dumps(run(),indent=2,sort_keys=True))

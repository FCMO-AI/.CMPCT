#!/usr/bin/env python3
"""A15-O1: exact cross-member ownership oracle. RESEARCH ONLY, not CMPCT product."""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import struct
import subprocess
import time
from pathlib import Path

AHD = struct.Struct("<4sBHH")
AREC = struct.Struct("<HI32sI")
RHD = struct.Struct("<4sHHI")
MHD = struct.Struct("<I32sH")
CHUNK = 4096
MEMBERS = 32
PER_MEMBER = 16
SEEDS = (20261028, 20261029)
REGIMES = ("identical", "partial", "distinct")


def digest(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def zstd(data: bytes, decompress: bool = False) -> bytes:
    command = ["zstd", "-q", "-d", "-c"] if decompress else ["zstd", "-q", "--ultra", "-19", "-c"]
    completed = subprocess.run(command, input=data, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, check=False)
    if completed.returncode:
        raise ValueError("zstd subprocess failed")
    return completed.stdout


def source(regime: str, seed: int) -> list[bytes]:
    rng = random.Random(seed)
    common = [rng.randbytes(CHUNK) for _ in range(PER_MEMBER)]
    members = []
    for i in range(MEMBERS):
        if regime == "identical":
            chunks = common
        elif regime == "partial":
            chunks = common[:12] + [rng.randbytes(CHUNK) for _ in range(4)]
        elif regime == "distinct":
            chunks = [rng.randbytes(CHUNK) for _ in range(PER_MEMBER)]
        else:
            raise ValueError("invalid regime")
        members.append(b"".join(chunks))
    return members


def a15_direct(members: list[bytes]) -> bytes:
    # Exactly A15-O0's direct typed grammar: one shared empty program,
    # independent per-member Zstd-19 frames, and SHA-authenticated descriptors.
    out = bytearray(AHD.pack(b"A15O", 1, len(members), 1))
    out += struct.pack("<H", 1) + b"\x00"
    for member in members:
        encoded = zstd(member)
        out += AREC.pack(0, len(member), digest(member), len(encoded)) + encoded
    return bytes(out)


def chunkref(members: list[bytes]) -> tuple[bytes, int]:
    unique = []
    positions = {}
    refs = []
    for member in members:
        if len(member) % CHUNK:
            raise ValueError("unaligned member")
        row = []
        for i in range(0, len(member), CHUNK):
            chunk = member[i:i+CHUNK]
            sha = digest(chunk)
            if sha not in positions:
                positions[sha] = len(unique)
                unique.append(chunk)
            elif unique[positions[sha]] != chunk:
                raise ValueError("SHA collision: refusing false deduplication")
            row.append(positions[sha])
        refs.append(row)
    if len(unique) > 65535:
        raise ValueError("too many owners")
    out = bytearray(RHD.pack(b"RFO1", len(members), len(unique), CHUNK))
    for chunk in unique:
        encoded = zstd(chunk)
        out += struct.pack("<I", len(encoded)) + digest(chunk) + encoded
    for member, row in zip(members, refs):
        out += MHD.pack(len(member), digest(member), len(row))
        out += struct.pack("<" + "H"*len(row), *row)
    return bytes(out), len(unique)


def read_a15(blob: bytes, target: int) -> bytes:
    if len(blob) < AHD.size:
        raise ValueError("truncated header")
    magic, kind, count, programs = AHD.unpack_from(blob)
    if (magic, kind, count, programs) != (b"A15O", 1, MEMBERS, 1):
        raise ValueError("invalid A15 shape")
    pos = AHD.size
    if blob[pos:pos+3] != b"\x01\x00\x00":
        raise ValueError("unexpected program")
    pos += 3
    result = None
    for i in range(count):
        if pos + AREC.size > len(blob):
            raise ValueError("truncated member")
        pid, rawlen, want, size = AREC.unpack_from(blob, pos)
        pos += AREC.size
        if pid != 0 or rawlen != CHUNK*PER_MEMBER or size > 1<<21 or pos+size > len(blob):
            raise ValueError("invalid member descriptor")
        if i == target:
            decoded = zstd(blob[pos:pos+size], decompress=True)
            if len(decoded) != rawlen or digest(decoded) != want:
                raise ValueError("A15 member mismatch")
            result = decoded
        pos += size
    if pos != len(blob) or result is None:
        raise ValueError("trailing bytes or invalid member")
    return result


def read_ref(blob: bytes, target: int) -> bytes:
    if len(blob) < RHD.size:
        raise ValueError("truncated header")
    magic, count, owners, chunksize = RHD.unpack_from(blob)
    if magic != b"RFO1" or count != MEMBERS or owners > MEMBERS*PER_MEMBER or chunksize != CHUNK:
        raise ValueError("bad chunkref header")
    pos = RHD.size
    data = []
    for _ in range(owners):
        if pos+36 > len(blob):
            raise ValueError("truncated owner")
        size = struct.unpack_from("<I", blob, pos)[0]
        sha = blob[pos+4:pos+36]
        pos += 36
        if size > 1<<16 or pos+size > len(blob):
            raise ValueError("owner bounds")
        data.append((sha, blob[pos:pos+size]))
        pos += size
    result = None
    for i in range(count):
        if pos+MHD.size > len(blob):
            raise ValueError("truncated member")
        rawlen, sha, nrefs = MHD.unpack_from(blob, pos)
        pos += MHD.size
        if rawlen != CHUNK*PER_MEMBER or nrefs != PER_MEMBER or pos+2*nrefs > len(blob):
            raise ValueError("bad member geometry")
        ids = struct.unpack_from("<" + "H"*nrefs, blob, pos)
        pos += 2*nrefs
        if any(j >= owners for j in ids):
            raise ValueError("owner ref bounds")
        if i == target:
            pieces = []
            for j in ids:
                content = zstd(data[j][1], decompress=True)
                if len(content) != CHUNK or digest(content) != data[j][0]:
                    raise ValueError("owner digest or length")
                pieces.append(content)
            result = b"".join(pieces)
            if digest(result) != sha:
                raise ValueError("member digest")
    if pos != len(blob) or result is None:
        raise ValueError("trailing bytes or missing member")
    return result


def hostile(blob: bytes) -> dict[str, bool]:
    # Mutations are always against the full authenticated envelope; failure is expected.
    _, _, owners, _ = RHD.unpack_from(blob)
    pos = RHD.size
    owner_content = pos+36
    for _ in range(owners):
        n = struct.unpack_from("<I", blob, pos)[0]
        pos += 36+n
    member = pos
    first_ref = member+MHD.size
    mutants = {}
    def mutate(name: str, at: int, value: bytes):
        b = bytearray(blob)
        b[at:at+len(value)] = value
        mutants[name] = bytes(b)
    mutate("invalid_ref", first_ref, b"\xff\xff")
    mutate("owner_corrupted", owner_content, bytes([blob[owner_content]^0x80]))
    mutate("member_sha", member+4, bytes([blob[member+4]^0x80]))
    mutate("wrong_raw_size", member, struct.pack("<I", CHUNK*PER_MEMBER+1))
    mutate("truncated_owner_frame", RHD.size, struct.pack("<I", 65537))
    mutants["truncated"] = blob[:-1]
    mutants["trailing"] = blob+b"x"
    outcomes = {}
    for name, altered in mutants.items():
        try:
            read_ref(altered, 0)
            outcomes[name] = False
        except ValueError:
            outcomes[name] = True
    return outcomes


def bench(func, blob: bytes, targets=(0, 17, 31)) -> dict:
    samples = []
    for i in targets:
        for _ in range(2):
            start = time.perf_counter_ns()
            cpu = time.process_time_ns()
            answer = func(blob, i)
            samples.append({"target": i, "wall_ns": time.perf_counter_ns()-start,
                            "parent_cpu_ns": time.process_time_ns()-cpu, "sha256": digest(answer).hex()})
    return {"raw": samples, "wall_median_ns": sorted(x["wall_ns"] for x in samples)[len(samples)//2]}


def run(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    rows = []
    for seed in SEEDS:
        for regime in REGIMES:
            members = source(regime, seed)
            a = a15_direct(members)
            b, owners = chunkref(members)
            for i, expected in enumerate(members):
                if read_a15(a, i) != expected or read_ref(b, i) != expected:
                    raise AssertionError("wrong reconstructed bytes")
            attack = hostile(b)
            if not all(attack.values()):
                raise AssertionError("failed closed mutation")
            label = f"{regime}_{seed}"
            folder = directory/label
            folder.mkdir(exist_ok=True)
            (folder/"a15.bin").write_bytes(a)
            (folder/"chunkref.bin").write_bytes(b)
            (folder/"source.bin").write_bytes(b"".join(members))
            rows.append({"label":label, "regime":regime,"seed":seed,
                        "members":MEMBERS, "member_bytes":len(members[0]),
                        "unique_owners":owners, "chunk_bytes":CHUNK,
                        "source_sha256":digest(b"".join(members)).hex(),
                        "a15_sha256":digest(a).hex(),"chunkref_sha256":digest(b).hex(),
                        "a15_bytes":len(a),"chunkref_bytes":len(b),
                        "chunkref_to_a15":len(b)/len(a),
                        "a15_bench":bench(read_a15,a),"chunkref_bench":bench(read_ref,b),
                        "hostile":attack})
            print(f"{label}: A15={len(a)} REF={len(b)} owners={owners}",flush=True)
    decision = all(
        (r["chunkref_to_a15"] <= .70 if r["regime"] != "distinct" else r["chunkref_to_a15"] >= .95)
        for r in rows)
    receipt = {"schema":"a15-o1-cross-owner-transfer-v1",
               "parent":"6b1eab092955d995e1099aefd9d5fadcac57df9f",
               "claim_level":"scientific_oracle_only",
               "prediction_met":decision,
               "cases":rows,
               "limitations":["Not actual CMPCT r24 bytes or installed Reader",
                              "CHUNKREF is a fully charged dedicated strong control, not a new codec",
                              "Per-member access only; range-level and cold-open costs unmeasured",
                              "Parent process CPU excludes child zstd CPU",
                              "No real RSS, conformance, native portability, recovery or release evidence"]}
    (directory/"result.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"cases":len(rows),"prediction_met":decision,
                      "hostile_rejections":sum(sum(r["hostile"].values()) for r in rows)}))

if __name__ == "__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    run(ap.parse_args().out)

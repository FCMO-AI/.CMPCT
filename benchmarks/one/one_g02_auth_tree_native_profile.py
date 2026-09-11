"""ONE-G0.2 exact-root native SHA-256 tree profile.

Referee freeze before result-bearing execution
==============================================
The hosted creation-cost audit showed 17-39x elapsed versus a whole-root SHA-256 and thousands
of exact hash nodes for the shared-graph passing leaves. This experiment removes Python tree
construction overhead without changing one authentication byte.

Compile the committed C/OpenSSL implementation, independently reproduce its deterministic
input in Python, and require the native root to equal `experiments.one.auth_tree.build_auth_tree`
for every case. Profile 64 KiB and 256 KiB roots at the four passing 80/96/112/192-byte leaves.
The same OpenSSL binary times exact tree construction against one-shot SHA256 on identical data.

Frozen interpretation:
- any root mismatch invalidates all timing;
- <=5x native tree/whole-SHA on every case would substantially falsify the hypothesis that
  fine-leaf hash construction is a major native cost owner;
- >10x on the balanced 112-byte leaf at both sizes establishes a material native blocker;
- the middle 5-10x region remains debt requiring end-to-end MIY analysis.
No timing outcome may change the prior stored-byte/access evidence or hash/security semantics.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from experiments.one.auth_tree import build_auth_tree

ROOT_SIZES=(65_536,262_144)
LEAVES=(80,96,112,192)
REPS=31
BIN=Path("/tmp/one_g02_auth_tree_openssl")
SRC=Path("benchmarks/one/native/one_g02_auth_tree_openssl.c")


def _data(n:int)->bytes:
    return bytes((((i*131) ^ (i>>3) ^ (i>>11) ^ 0x5a)&255) for i in range(n))


def run()->dict[str,object]:
    subprocess.run(["cc","-O3","-Wno-deprecated-declarations",str(SRC),"-lcrypto","-o",str(BIN)],check=True)
    rows=[]; mismatches=[]
    for root_bytes in ROOT_SIZES:
        data=_data(root_bytes)
        for leaf in LEAVES:
            expected=build_auth_tree(data,leaf).root.hex()
            p=subprocess.run([str(BIN),str(root_bytes),str(leaf),str(REPS)],check=True,text=True,capture_output=True)
            row=json.loads(p.stdout)
            if row["tree_root"]!=expected:
                mismatches.append({"root_bytes":root_bytes,"leaf_bytes":leaf,"python_root":expected,"native_root":row["tree_root"]})
            rows.append(row)
    balanced=[r for r in rows if r["leaf_bytes"]==112]
    if mismatches:
        decision="invalid_native_root_mismatch"
    elif all(r["elapsed_ratio"]<=5.0 for r in rows):
        decision="fine_leaf_native_hash_cost_hypothesis_substantially_falsified"
    elif all(r["elapsed_ratio"]>10.0 for r in balanced):
        decision="material_native_creation_blocker_confirmed"
    else:
        decision="native_creation_debt_survives_but_requires_end_to_end_miy"
    return {
        "schema":"cmpct-one-g02-auth-tree-native-profile-v1",
        "experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "compiler":"cc -O3; OpenSSL libcrypto SHA-256",
        "repetitions":REPS,"root_mismatches":mismatches,"rows":rows,"decision":decision,
        "claim_boundary":"hosted x86-64 CI native microprofile only; exact roots required; no product/create-throughput or canonical-format authority",
    }


if __name__=='__main__': print(json.dumps(run(),indent=2,sort_keys=True))

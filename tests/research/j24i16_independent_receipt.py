"""J24I16 receipt oracle: standalone deterministic sentinels and hostile mutations.

No CMPCT/Win32 primitive imports; this validates physical receipt facts rather
than trusting the experiment's reported success status.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

INSIDE_SHA = "b292f5e3b3a2a384ea5a3dd89241523afdeb3e20eeacd63e99cd0beb1cb1885f"
OUTSIDE_SHA = "a058c06f7e174645340f9f4a728b78ee1989bf010c5b05ac8848ba2b85b0ca39"
PARENT_SHA = "8d4343defe2918257e153654f1e59cdb7253f265"


def verify(r: dict, expected_head: str) -> dict:
    if r.get("schema") != "j24i16-win32-ancestor-junction-v1":
        raise ValueError("wrong receipt schema")
    if len(expected_head) != 40 or r.get("head") != expected_head:
        raise ValueError("unbound or incorrect source head")
    if r.get("parent_research_sha") != PARENT_SHA:
        raise ValueError("wrong inherited J24I15 source")
    if r.get("status") != "ANCESTOR_JUNCTION_TRAVERSAL_CONFIRMED":
        raise ValueError("missing positive primitive negative")
    if (r.get("os_name") != "nt" or r.get("release_credit") is not False
            or r.get("product_code_modified") is not False):
        raise ValueError("wrong host, product mutation or false release claim")
    obs = r["observations"]
    hashes = {
        "inside": INSIDE_SHA, "outside": OUTSIDE_SHA,
        "stable_read": INSIDE_SHA, "original_renamed_read": INSIDE_SHA,
        "ancestor_pivot_read": OUTSIDE_SHA,
        "independent_outside_read": OUTSIDE_SHA
    }
    if obs.get("sha256") != hashes:
        raise ValueError("observed bytes fail independent sentinel oracle")
    if obs.get("bytes") != {"inside": 71, "outside": 82,
                             "stable": 71, "after_ancestor_pivot": 82}:
        raise ValueError("logical bytes changed during pivot")
    ids = obs["source_physical_ids"]
    inside, outside = ids["inside"], ids["outside"]
    for pair in [inside, outside, obs["post_pivot_os_identity"]]:
        if not isinstance(pair, list) or len(pair) != 2 or any(type(i) is not int for i in pair):
            raise ValueError("malformed physical ID")
    if inside == outside or obs["post_pivot_os_identity"] != outside:
        raise ValueError("post-pivot OS file object not external fixture")
    handles = obs["handle_identities"]
    if (handles["before"] != handles["retained_original"]
            or handles["before"] == handles["after_ancestor_pivot"]):
        raise ValueError("candidate HANDLE objects did not differ after junction")
    junction = obs["ancestor_junction"]
    if (junction.get("confirmed") is not True
            or junction.get("was_parent_path_rebound") is not True
            or type(junction.get("reparse_attributes")) is not int
            or junction["reparse_attributes"] & 0x400 == 0):
        raise ValueError("ancestor junction not physically attested")
    if (obs["final_leaf_control"].get("rejected") is not True
            or obs.get("outside_bytes_admitted") is not True):
        raise ValueError("leaf control failed or outside bytes not observed")
    return {
        "schema": "j24i16-independent-verifier-v1",
        "result": "VERIFIED_PRIMITIVE_NEGATIVE", "head": expected_head,
        "outside_sha256": OUTSIDE_SHA,
        "scope": "Win32 cached leaf HANDLE plus deterministic NTFS ancestor junction, not Builder"
    }


def example():
    head = "a" * 40
    return {
        "schema": "j24i16-win32-ancestor-junction-v1", "head": head,
        "parent_research_sha": PARENT_SHA,
        "status": "ANCESTOR_JUNCTION_TRAVERSAL_CONFIRMED",
        "os_name": "nt", "release_credit": False, "product_code_modified": False,
        "observations": {
            "sha256": {
                "inside": INSIDE_SHA, "outside": OUTSIDE_SHA,
                "stable_read": INSIDE_SHA, "original_renamed_read": INSIDE_SHA,
                "ancestor_pivot_read": OUTSIDE_SHA,
                "independent_outside_read": OUTSIDE_SHA
            },
            "bytes": {"inside": 71, "outside": 82, "stable": 71,
                      "after_ancestor_pivot": 82},
            "source_physical_ids": {"inside": [1, 11], "outside": [1, 22]},
            "post_pivot_os_identity": [1, 22],
            "handle_identities": {"before": [1, 11], "retained_original": [1, 11],
                                  "after_ancestor_pivot": [1, 22]},
            "ancestor_junction": {"confirmed": True, "was_parent_path_rebound": True,
                                  "reparse_attributes": 0x410},
            "final_leaf_control": {"rejected": True},
            "outside_bytes_admitted": True
        }
    }, head


def selftest() -> int:
    r, h = example()
    verify(r, h)
    tamper = [
        lambda x: x["observations"]["sha256"].__setitem__("ancestor_pivot_read", INSIDE_SHA),
        lambda x: x["observations"]["bytes"].__setitem__("after_ancestor_pivot", 71),
        lambda x: x["observations"]["final_leaf_control"].__setitem__("rejected", False),
        lambda x: x["observations"]["ancestor_junction"].__setitem__("reparse_attributes", 0x10),
        lambda x: x["observations"]["source_physical_ids"].__setitem__("outside", [1, 11]),
        lambda x: x["observations"]["handle_identities"].__setitem__("after_ancestor_pivot", [1, 11]),
        lambda x: x.__setitem__("head", "b" * 40),
        lambda x: x.__setitem__("status", "NO_REPRODUCTION"),
        lambda x: x.__setitem__("release_credit", True)
    ]
    for i, mutation in enumerate(tamper):
        altered = copy.deepcopy(r)
        mutation(altered)
        try:
            verify(altered, h)
        except (ValueError, TypeError, KeyError):
            continue
        raise AssertionError(f"tampered receipt {i} erroneously passed")
    print(json.dumps({"selftest": "PASS", "tampered_receipts_rejected": len(tamper)}))
    return len(tamper)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--receipt", type=Path)
    p.add_argument("--head")
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    if args.self_test:
        selftest()
        return
    if not args.receipt or not args.head or not args.out:
        p.error("--receipt, --head and --out are required")
    result = verify(json.loads(args.receipt.read_text(encoding="utf-8")), args.head)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

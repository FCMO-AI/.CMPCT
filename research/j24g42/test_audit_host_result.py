"""J24G42 detached auditor's negative-control self-test (synthetic receipts)."""
from __future__ import annotations
from copy import deepcopy
from audit_host_result import audit

head = "a" * 40
sample = {
    "schema": "j24g42-darwin-compressed-xattr-visibility-v1",
    "source_head": head,
    "platform": "darwin",
    "darwin_constants": {"SHOWCOMPRESSION": 32, "NOFOLLOW": 1, "UF_COMPRESSED": 32},
    "synthetic_control": {
        "candidate_provider_contains": True,
        "native_default_contains": True,
        "native_show_contains": True,
        "ok": True, "value_identity": True,
    },
    "specimens": [{
        "path": "/synthetic-fixture",
        "st_flags": 32,
        "native_default_names": [],
        "native_show_names": ["com.apple.decmpfs"],
        "newly_visible_names": ["com.apple.decmpfs"],
        "provider_matches_default": True,
        "compression_hidden": True,
    }],
    "scan_bounds": {"compressed_cases": 8},
    "compressed_observed": 1,
    "compressed_successful": 1,
    "hidden_positive": True,
    "decision": "VISIBILITY_GAP_POSITIVE",
}
assert audit(sample, head)["decision"] == "VISIBILITY_GAP_POSITIVE"

mutations = [
    ("source drift", lambda d: d.update(source_head="b" * 40)),
    ("false positive", lambda d: d.update(hidden_positive=False)),
    ("false result", lambda d: d.update(decision="NO_GAP_OBSERVED_ON_SAMPLED_HOST")),
    ("no compression flag", lambda d: d["specimens"][0].update(st_flags=0)),
    ("false name difference", lambda d: d["specimens"][0].update(newly_visible_names=[])),
    ("false provider", lambda d: d["specimens"][0].update(provider_matches_default=False)),
    ("broken independent control", lambda d: d["synthetic_control"].update(ok=False)),
]
for label, modify in mutations:
    fake = deepcopy(sample)
    modify(fake)
    try:
        audit(fake, head)
    except AssertionError:
        print("Rejected malformed evidence:", label)
    else:
        raise AssertionError("Audit accepted malformed evidence: " + label)
print("J24G42 detached auditor self-test: 7/7 tampering variants rejected")

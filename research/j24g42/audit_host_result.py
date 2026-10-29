"""Detached J24G42 hosted-result auditor. Checks receipt logic, not kernel provenance."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

KEYS = {"com.apple.ResourceFork", "com.apple.decmpfs"}


def audit(record, expected_source):
    assert record["schema"] == "j24g42-darwin-compressed-xattr-visibility-v1"
    assert record["source_head"] == expected_source
    assert record["platform"] == "darwin"
    assert record["darwin_constants"]["SHOWCOMPRESSION"] == 32
    assert record["darwin_constants"]["NOFOLLOW"] == 1
    assert record["darwin_constants"]["UF_COMPRESSED"] == 32
    assert record["synthetic_control"] == {
        "candidate_provider_contains": True,
        "native_default_contains": True,
        "native_show_contains": True,
        "ok": True, "value_identity": True,
    }
    rows = record["specimens"]
    assert 0 <= len(rows) <= record["scan_bounds"]["compressed_cases"] <= 8
    assert record["compressed_observed"] == len(rows)
    assert record["compressed_successful"] == sum("native_show_names" in x for x in rows)
    discovered = False
    for row in rows:
        assert row["st_flags"] & 0x20 == 0x20
        if "error" in row:
            assert "native_show_names" not in row
            continue
        normal = row["native_default_names"]
        show = row["native_show_names"]
        assert len(normal) == len(set(normal))
        assert len(show) == len(set(show))
        assert row["provider_matches_default"] is True
        extra = set(show) - set(normal)
        assert row["newly_visible_names"] == sorted(extra)
        hidden = bool(KEYS & extra)
        assert row["compression_hidden"] is hidden
        discovered |= hidden
    assert record["hidden_positive"] is discovered
    if discovered:
        expected = "VISIBILITY_GAP_POSITIVE"
    elif record["compressed_successful"] >= 3:
        expected = "NO_GAP_OBSERVED_ON_SAMPLED_HOST"
    else:
        expected = "INCONCLUSIVE_INSUFFICIENT_COMPRESSED_SPECIMENS"
    assert record["decision"] == expected
    return {
        "decision": expected,
        "verified_cases": len(rows),
        "source_head": expected_source,
        "evidence_class": "research-only name visibility, not archive/product proof",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    parser.add_argument("--expected-source", required=True)
    args = parser.parse_args()
    print(json.dumps(audit(json.loads(args.record.read_text()), args.expected_source), sort_keys=True))

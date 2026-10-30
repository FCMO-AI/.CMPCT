#!/usr/bin/env python3
"""J24G93 detached physical referee. Never imports cmpct product modules."""
from __future__ import annotations
import hashlib, json, pathlib, struct, sys
from j24g92_detached_referee import F, footer, chain, reconstruct, sha

def audit(root: pathlib.Path, n: int, record: dict) -> dict:
    def content(label):
        raw = (root / f"{n}-{label}.cmpct").read_bytes()
        key = {"pre":"source_original_sha256",
               "orphan-only":"orphan_only_sha256",
               "after-writer":"after_writer_sha256",
               "clean-fourth":"clean_control_sha256",
               "corrupt-final":"corrupt_final_sha256"}[label]
        assert sha(raw) == record[key], (label, key)
        return raw
    pre, orphan, written, clean, damaged = (
        content(s) for s in
        ("pre", "orphan-only", "after-writer", "clean-fourth", "corrupt-final"))
    assert written.startswith(orphan) and orphan.startswith(pre)
    assert len(orphan) == len(pre) + record["orphan_physical_bytes"]
    assert len(written) - len(orphan) == record["final_added_bytes_after_orphan"]
    assert len(damaged) == len(written) and damaged[:-1] == written[:-1]
    assert damaged[-1] != written[-1]
    before = chain(pre)
    after = chain(written)
    normal_four = chain(clean)
    assert len(before) == 4 and len(after) == len(normal_four) == 5
    assert record["pre_existing_footer"] == before[-1]["pos"]
    assert record["orphan_footer"] > before[-1]["pos"]
    invalid_chain = footer(orphan, record["orphan_footer"])
    assert invalid_chain["kind"] == 1 and invalid_chain["prev"] == 0
    assert invalid_chain["index"] == {"blobs": [], "ops": []}
    assert after[-1]["pos"] == record["writer_final_footer"]
    assert after[-1]["prev"] == before[-1]["pos"] == record["writer_parent"]
    assert after[-1]["prev"] != invalid_chain["pos"]
    assert after[-1]["index"] == {"blobs": [], "ops": [["del", "f00003.dat"]]}
    assert after[-1]["pos"] == len(written) - F.size
    try:
        footer(damaged, len(damaged) - F.size)
    except AssertionError:
        pass
    else:
        raise AssertionError("damaged terminal footer SHA unexpectedly accepted")
    pre_live = reconstruct(before)
    final_live = reconstruct(after)
    clean_live = reconstruct(normal_four)
    assert len(pre_live) == n-3 and len(final_live) == n-4
    assert pre_live - final_live == {"f00003.dat"}
    assert final_live == clean_live
    assert record["before_count"] == len(pre_live)
    assert record["after_count"] == len(final_live)
    # Verify every installed Reader path/hash claim independently from test seed.
    answers = record["answers"]
    expected_sets = {"before": pre_live, "orphan_only": pre_live,
                     "after_writer": final_live, "clean_control": final_live,
                     "bad_newest_digest": pre_live}
    expected_footers = {
        "before": before[-1]["pos"], "orphan_only": before[-1]["pos"],
        "after_writer": after[-1]["pos"], "clean_control": normal_four[-1]["pos"],
        "bad_newest_digest": before[-1]["pos"]}
    for label, expected in expected_sets.items():
        pair = answers[label]
        rd = pair["reader"]
        pf = pair["preflight"]
        assert rd["accepted"] and pf["accepted"]
        assert set(rd["paths"]) == expected, label
        assert rd["footer"] == expected_footers[label], label
        assert pf["result"]["latest_footer"] == expected_footers[label], label
        assert pf["result"]["files"] == len(expected)
        for path, observed in rd["sha256_by_path"].items():
            idx = int(path[1:6])
            data = hashlib.sha256(f"j24g93-{n}-{idx}".encode()).digest()
            assert observed == hashlib.sha256(data).hexdigest(), (label, path)
    return {"n": n, "physical_original_bytes": len(pre),
            "orphan_extra_bytes": len(orphan)-len(pre),
            "writer_commit_extra_bytes": len(written)-len(orphan),
            "orphan_footer": invalid_chain["pos"],
            "new_footer": after[-1]["pos"],
            "real_writer_skipped_orphan": True,
            "original_sha256": sha(pre),
            "written_sha256": sha(written),
            "logical_members_before": len(pre_live),
            "logical_members_after": len(final_live),
            "detached_lineage_valid": True,
            "installed_receipt_consistent": True}

def main():
    root = pathlib.Path(sys.argv[1])
    receipt = json.loads((root / "receipt.json").read_text())
    assert receipt["schema"] == "cmpct-j24g93-genuine-public-writer-orphan-recovery-v1"
    assert receipt["status"] == "PASS"
    assert receipt["source"]["reader_blob"] == "e716233403dabd0966863c45635e18fa5ac6afb8"
    result = {"schema": "j24g93-detached-footer-physical-referee-v1",
              "product_code_imported": False,
              "status": "PASS", "source_head": receipt["source"]["head"],
              "scope": "manual orphan injection; real installed Writer commit",
              "cases": {str(n): audit(root, n, receipt["cases"][str(n)])
                        for n in (16, 128)}}
    (root / "detached-referee.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("J24G93_REFEREE", json.dumps({
        "status": result["status"],
        "cases": {k: (v["logical_members_before"], v["logical_members_after"],
                       v["real_writer_skipped_orphan"])
                  for k, v in result["cases"].items()}}, sort_keys=True))

if __name__ == "__main__":
    main()

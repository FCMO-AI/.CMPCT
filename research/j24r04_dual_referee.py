"""Independent J24R04 source/ABBA/median validator; no import of CMPCT Reader.

Considers failures scientific outcomes. Never relabels a real measured regression green.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys

ORIGINAL = "c5e13bb3fbb4cdade8b64246658ce7c7818de41f"
UNCONDITIONAL = "70336307312b5b277f0885c0057d2cddab0aefc1"
COUNTS = (1, 4, 4096, 65536)
FIELDS = ("open_wall_ms", "open_cpu_ms", "range_batch_wall_ms", "range_batch_cpu_ms")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git_source_hash(repo, ref):
    data = subprocess.check_output(("git", "show", ref + ":src/cmpct/reader.py"), cwd=repo)
    return hashlib.sha256(data.replace(b"\\r\\n", b"\\n")).hexdigest()


def evaluate(rawfile, repo, control_ref, baseline_site, candidate_site):
    report = json.loads(rawfile.read_text())
    require(report.get("schema") == "j24r01-v1", "unexpected producer schema")
    rows = report["observations"]
    require(len(rows) == 48, "missing extra ABBA observations")
    roots = {"baseline": baseline_site.resolve(), "candidate": candidate_site.resolve()}
    expected_hashes = {"baseline": git_source_hash(repo, control_ref),
                       "candidate": git_source_hash(repo, "HEAD")}
    ix = 0
    for iteration in range(3):
        for e in COUNTS:
            order = ("baseline","candidate","candidate","baseline") if iteration%2 == 0 else ("candidate","baseline","baseline","candidate")
            for source in order:
                row = rows[ix];ix += 1
                require((row["iteration"],row["extent_count"],row["version"]) ==
                        (iteration,e,source), "ABBA axis drift")
                require(row["reader_source_sha256"] == expected_hashes[source], "source SHA mismatch")
                require(Path(row["reader_module"]).resolve().is_relative_to(roots[source]), "installed import path drift")
                require(type(row["range_checks"]) is int and row["range_checks"] == 533, "incorrect logical byte checks")
                for metric in FIELDS:
                    v = row[metric]
                    require(type(v) in (int,float) and math.isfinite(v) and v >= 0, "bad timing "+metric)
                require(row["range_batch_wall_ms"] > 0 and row["open_wall_ms"] > 0,"missing measured phases")
                f = report["fixture_manifest"][str(e)]
                require(row["archive_bytes"] == f["wire_bytes"] and row["logical_bytes"] == f["logical_bytes"],"fixture geometry mismatch")
    actual={}
    for e in COUNTS:
        m=report["fixture_manifest"][str(e)]
        require(type(m["wire_sha256"]) is str and len(m["wire_sha256"])==64, "missing physical checksum")
        require(m["logical_bytes"]==16*(e-1)+4,"fixture logical length drift")
        actual[str(e)]={}
        for source in ("baseline","candidate"):
            subset=[r for r in rows if r["extent_count"]==e and r["version"]==source]
            require(len(subset)==6, "missing paired observations")
            actual[str(e)][source]={}
            for metric in FIELDS:
                median=statistics.median(r[metric] for r in subset)
                declared=report["medians"][str(e)][source][metric]
                require(type(declared) in (int,float) and math.isfinite(declared) and
                        math.isclose(median,declared,rel_tol=1e-12,abs_tol=1e-12), "median drift")
                actual[str(e)][source][metric]=median
    return report, actual, expected_hashes


def audit(first,second,repo,original_site,owner_site,candidate_site):
    a,am,ah=evaluate(first,repo,ORIGINAL,original_site,candidate_site)
    b,bm,bh=evaluate(second,repo,UNCONDITIONAL,owner_site,candidate_site)
    for e in COUNTS:
        require(a["fixture_manifest"][str(e)]["wire_sha256"] ==
                b["fixture_manifest"][str(e)]["wire_sha256"],"different archive physical bytes across controls")
        require(a["fixture_manifest"][str(e)]["logical_sha256"] ==
                b["fixture_manifest"][str(e)]["logical_sha256"],"different logical truth across controls")
    require(ah["candidate"] == bh["candidate"],"candidate source differs between control arms")
    comparisons={}
    for e in COUNTS:
        k=str(e)
        o=am[k]["baseline"]["range_batch_wall_ms"]
        u=bm[k]["baseline"]["range_batch_wall_ms"]
        c=am[k]["candidate"]["range_batch_wall_ms"]
        c2=bm[k]["candidate"]["range_batch_wall_ms"]
        comparisons[k]={
            "original_ms":o,"unconditional_ms":u,
            "dual_vs_original_ms":c,"dual_vs_unconditional_ms":c2,
            "original_over_dual":o/c,"unconditional_over_dual":u/c2,
            "dual_cross_arm_shift":c2/c,
        }
    small_ok=all(comparisons[k]["original_over_dual"]>=1/1.05 for k in ("1","4"))
    large_ok=all(comparisons[k]["original_over_dual"]>=10 for k in ("4096","65536"))
    owner_ok=all(comparisons[k]["unconditional_over_dual"]>=1/1.05 for k in ("4096","65536"))
    return {"schema":"j24r04-independent-v1",
            "decision":"PROSPECTIVE_DUAL_PATH_SURVIVES_SCOPED_ABBA" if small_ok and large_ok and owner_ok else "PROSPECTIVE_DUAL_PATH_NARROW_OR_REJECT",
            "counts_verified":list(COUNTS),"raw_observations_verified":96,
            "reader_sha256":ah,"comparisons":comparisons,
            "small_e_within_5pct":small_ok,"large_e_over_10x":large_ok,"large_e_within_5pct_of_owner":owner_ok,
            "limits":"Only genuine installed Reader selected sparse ranges; no whole-product/parity, real-world incidence, create, or release credit"}


def main():
    if len(sys.argv)!=8:
        raise SystemExit("usage: referee original.json owner.json repo original-site owner-site candidate-site out.json")
    first,second,repo,orig,owner,candidate,out=map(Path,sys.argv[1:])
    report=audit(first,second,repo,orig,owner,candidate)
    out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\\n")
    original=json.loads(first.read_text())
    original["observations"][0]["reader_source_sha256"]="0"*64
    corrupted=out.parent/"mutated-receipt.json"
    corrupted.write_text(json.dumps(original))
    try:
        audit(corrupted,second,repo,orig,owner,candidate)
    except (ValueError,AssertionError):
        pass
    else:
        raise AssertionError("mutated-source evidence was accepted")
    corrupted.unlink(missing_ok=True)
    print("J24R04_INDEPENDENT_AUDIT=PASS")
    print("J24R04_OUTCOME="+report["decision"])
    for count,entry in report["comparisons"].items():
        print("J24R04_EXTENTS="+count+" ORIGINAL/DUAL="+format(entry["original_over_dual"],".4f")+" OWNER/DUAL="+format(entry["unconditional_over_dual"],".4f"))


if __name__=="__main__":
    main()

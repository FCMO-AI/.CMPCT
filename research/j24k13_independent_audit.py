#!/usr/bin/env python3
"""Independent stdlib-only J24K13 receipt referee; no CMPCT imports."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import statistics
import sys
import zipfile

METRICS = (
    "opened_wall_ns","opened_cpu_ns","read_wall_ns","read_cpu_ns",
    "total_wall_ns","total_cpu_ns","process_wall_ns"
)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def require(ok,reason):
    if not ok:
        raise AssertionError(reason)


def verify(result, work):
    require(result.get("schema") == "j24k13-installed-singlepass-v1", "schema")
    require(result.get("class") == "science-only-unchanged-installed-reader", "claim tier")
    require(result.get("case_count") == 12, "case count")
    require(result.get("raw_process_observations") == 72, "observation count")
    for key,rel in [
        ("reader_sha256","src/cmpct/reader.py"),
        ("codec_sha256","src/cmpct/codec.py"),
        ("instrument_sha256","research/j24k13_singlepass_vzip.py")
    ]:
        blob = Path(rel).read_bytes().replace(b"\r\n",b"\n")
        require(result["source"][key] == sha(blob), "source identity " + rel)
    neg = result["signed_attack"]
    require(neg["preflight_reject"] and len(neg["rejections"]) == 2,
            "signed negative not preserved")
    require({x[0] for x in neg["rejections"]} == {"control","singlepass"},
            "wrong rejection identities")
    require(neg["mutant_sha256"] == sha((work/"j24k13-reauthenticated.cmpct").read_bytes()),
            "negative mutant SHA")

    seen = set()
    for cell in result["cases"]:
        n = cell["n_streams"]
        case = cell["scenario"]
        require(n in (64,512,4096) and case in (
            "q1_early","q1_tail","q8_mixed","q64_tail"),"cell identity")
        require((n,case) not in seen,"duplicate cell")
        seen.add((n,case))
        archive = (work/(str(n)+".cmpct")).read_bytes()
        truth = (work/("input-"+str(n))/"science.zip").read_bytes()
        require(sha(archive) == cell["archive_sha256"],"archive identity")
        require(len(archive) == cell["archive_bytes"],"archive bytes")
        require(sha(truth) == cell["truth_sha256"],"truth SHA")
        with zipfile.ZipFile(work/("input-"+str(n))/"science.zip") as z:
            require(len(z.namelist()) == n and z.testzip() is None,"invalid original ZIP")
        require(len(cell["queries"]) in (1,8,64),"query count")
        qbytes = b""
        for a,k in cell["queries"]:
            require(type(a) is int and type(k) is int and
                    0<=a and 0<=k and a+k<=len(truth),"query bounds")
            qbytes += truth[a:a+k]
        require(sha(qbytes) == cell["query_digest"],"query content fingerprint")
        med = {}
        for strategy in ("control","singlepass"):
            raw = cell["observations"][strategy]
            require(len(raw)==3,"wrong repetition count")
            for row in raw:
                require(row["strategy"]==strategy and row["scenario"]==case,"strategy identity")
                require(row["archive_sha256"]==cell["archive_sha256"],"row archive")
                require(row["truth_sha256"]==cell["truth_sha256"],"row truth")
                require(row["query_digest"]==cell["query_digest"],"row query")
                require(row["n_queries"]==len(cell["queries"]),"query count")
                require(all(type(row[m]) is int and row[m]>=0 for m in METRICS),
                        "nonpositive CPU/wall sample")
            med[strategy] = {m:statistics.median(row[m] for row in raw) for m in METRICS}
            require(med[strategy]==cell["median"][strategy],"median mismatch")
        for m in ("total_wall_ns","total_cpu_ns","read_wall_ns",
                  "read_cpu_ns","process_wall_ns"):
            ratio = med["control"][m]/max(1,med["singlepass"][m])
            require(abs(ratio-cell["ratio"][m])<1e-10,"ratio mismatch")
    require(len(seen)==12,"missing cell")
    main = next(x for x in result["cases"]
                if x["n_streams"]==4096 and x["scenario"]=="q64_tail")
    strong=all(main["ratio"][m]>=1.20 for m in ("total_wall_ns","total_cpu_ns"))
    require(result["decision"] == ("SINGLEPASS_HEADROOM_OBSERVED" if strong
             else "SINGLEPASS_MATERIALITY_FALSIFIED"),"decision not raw-derived")
    return {"verdict":"PASS","cases":len(seen),"raw_observations":72,
            "scientific_decision":result["decision"]}


def main():
    doc=json.loads(Path(sys.argv[1]).read_text())
    work=Path(sys.argv[2])
    verdict=verify(doc,work)
    forged=0
    for mutator in [
        lambda j:j["cases"][0].update(query_digest="0"*64),
        lambda j:j["cases"][1]["median"]["control"].update(read_wall_ns=123),
        lambda j:j["cases"][2]["observations"]["singlepass"][0].update(total_wall_ns=-1),
        lambda j:j["source"].update(reader_sha256="0"*64),
        lambda j:j["signed_attack"].update(mutant_sha256="0"*64),
        lambda j:j["cases"][3].update(archive_bytes=1),
    ]:
        bad=copy.deepcopy(doc)
        mutator(bad)
        try:
            verify(bad,work)
        except (AssertionError,KeyError,ValueError,TypeError):
            forged+=1
        else:
            raise AssertionError("a forged receipt passed the independent referee")
    assert forged==6
    print(json.dumps(dict(verdict,forgeries_rejected=forged),sort_keys=True))


if __name__=="__main__":
    main()

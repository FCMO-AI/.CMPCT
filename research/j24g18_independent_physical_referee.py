#!/usr/bin/env python3
"""J24G18 independent physical/footer/receipt referee, without CMPCT imports.

Uses stdlib struct/hashlib plus msgpack solely to audit signed test payloads.
Does not use the candidate Reader or its native token scanner.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import msgpack

FOOTER = struct.Struct("<8sBBBBQQQ32s")
MAGIC = b"CMPTF24\0"
CANON_SHA = hashlib.sha256(b"CMPCT-J24G18-signed-Reader-fallback\0" * 41).hexdigest()
CASES = ("clean", "writer-rename", "orphan-overcap", "linked-overcap",
         "linked-undercap", "malformed-signed")
ARMS = ("direct", "gated", "catch")

def require(v, message):
    if not v:
        raise ValueError(message)

def audit(root, record):
    n = 0
    require(record["experiment"] == "J24G18", "experiment"); n += 1
    require(record["release_credit"] == 0 and record["product_changes"] is False,
            "research boundary"); n += 1
    require(record["body_sha256"] == CANON_SHA, "member expected SHA"); n += 1
    require(record["cap"] == 65536 and record["repeats"] >= 3, "frozen token gate"); n += 1
    require(set(record["physical"]) == set(CASES), "case inventory"); n += 1
    require(set(record["observations"]) == set(CASES), "observations inventory"); n += 1
    # Independently prove the earlier committed Builder checkpoint exists in bytes,
    # not merely in the Reader's self-reported selected_footer field.
    baseline = (root / record["physical"]["clean"]["path"]).read_bytes()
    checkpoint = record["checkpoint"]
    require(0 < checkpoint <= len(baseline) - FOOTER.size,
            "checkpoint location outside physical base"); n += 1
    base_footer = FOOTER.unpack(baseline[checkpoint:checkpoint+FOOTER.size])
    require(base_footer[0] == MAGIC and base_footer[1] == 0,
            "checkpoint is not a physically signed complete generation"); n += 1
    for case in CASES:
        p = record["physical"][case]
        require(p["path"] == "physical/" + case + ".cmpct", "relative path"); n += 1
        raw = (root / p["path"]).read_bytes()
        require(len(raw) == p["bytes"], "archive length:" + case); n += 1
        require(hashlib.sha256(raw).hexdigest() == p["sha256"],
                "archive digest:" + case); n += 1
        require(len(raw) >= FOOTER.size, "missing physical footer"); n += 1
        require(raw[:len(baseline)] == baseline,
                "physical Builder prefix differs across arms"); n += 1
        x = FOOTER.unpack(raw[-FOOTER.size:])
        require(x[0] == MAGIC, "no signed footer:" + case); n += 1
        if case in ("orphan-overcap", "linked-overcap", "linked-undercap",
                    "malformed-signed"):
            tail = p["tail"]
            require(tail is not None, "missing tail receipt"); n += 1
            offset = len(raw) - FOOTER.size
            require(tail["footer"] == offset and x[1] == 1 and x[2] == 0,
                    "footer geometry:" + case); n += 1
            require(x[5] == x[6] == tail["payload_bytes"] and
                    x[5] <= offset, "payload length:" + case); n += 1
            require(x[7] == tail["prev"], "signed predecessor:" + case); n += 1
            expected_prev = 0 if case == "orphan-overcap" else checkpoint
            require(x[7] == expected_prev, "wrong ancestry root:" + case); n += 1
            require(hashlib.sha256(raw[-FOOTER.size:]).hexdigest() ==
                    tail["footer_sha256"], "footer SHA:" + case); n += 1
            payload = raw[offset-x[5]:offset]
            require(hashlib.sha256(payload).hexdigest() ==
                    tail["payload_sha256"], "payload receipt:" + case); n += 1
            require(hashlib.sha256(payload).digest() == x[8],
                    "SHA-authenticated signed payload:" + case); n += 1
            if case != "malformed-signed":
                obj = msgpack.unpackb(payload, raw=False)
                require(isinstance(obj, dict) and
                        isinstance(obj.get("ops"), list) and
                        isinstance(obj.get("blobs"), list),
                        "canonical schema:" + case); n += 1
                require(len(obj.get("extension", [])) ==
                        (100 if case == "linked-undercap" else 70000),
                        "node count witness:" + case); n += 1
                require(obj["ops"] ==
                        ([["ren", "owner.bin", "renamed.bin"]]
                         if case != "orphan-overcap" else []),
                        "operation witness:" + case); n += 1
            else:
                try:
                    msgpack.unpackb(payload, raw=False)
                except Exception:
                    pass
                else:
                    raise ValueError("malformed signed payload decoded")
                n += 1
        observations = record["observations"][case]
        require(set(observations) == set(ARMS), "arm inventory:" + case); n += 1
        for arm in ARMS:
            rows = observations[arm]
            require(len(rows) == record["repeats"], "raw repeats:" + case + arm); n += 1
            for i, row in enumerate(rows):
                require(row["worker_repeat"] == i, "worker order"); n += 1
                require(row["wall_ns"] > 0 and row["cpu_ns"] > 0 and
                        row["rss_kib"] > 0, "timing / memory telemetry"); n += 1
                expect_error = (case == "malformed-signed" or
                                (arm == "gated" and "overcap" in case))
                require(row["status"] ==
                        ("error" if expect_error else "opened"),
                        "policy status mismatch:" + case + arm); n += 1
                if arm == "gated" and "overcap" in case:
                    require(row["exception"] == "TooManyNodes",
                            "wrong gate error"); n += 1
                if row["status"] == "opened":
                    expected_depth = 1 if (case in
                        ("writer-rename", "linked-undercap") or
                        (case == "linked-overcap" and arm == "direct")) else 0
                    require(row["depth"] == expected_depth,
                            "selected depth:" + case + arm); n += 1
                    member = ("renamed.bin" if expected_depth == 1 else "owner.bin")
                    require(member in row["members"], "selected member"); n += 1
                    require(row["members"][member]["sha256"] == CANON_SHA,
                            "wrong decoded member hash"); n += 1
                    require(row["members"][member]["bytes"] > 0, "empty member"); n += 1
                    if case == "orphan-overcap":
                        require(row["selected_footer"] == record["checkpoint"],
                                "failed orphan recovery"); n += 1
                    if case == "linked-overcap":
                        require((row["selected_footer"] > record["checkpoint"])
                                == (arm == "direct"), "wrong linked version"); n += 1
    require(record["decisions"]["naive_default_gate"] ==
            "FALSIFIED_FOR_INHERITED_ACCEPTANCE_AND_FALLBACK",
            "unearned verdict"); n += 1
    return n

def mutation_checks(root, original):
    tamper = []
    x = copy.deepcopy(original); x["body_sha256"] = "0" * 64
    tamper.append(("logical hash", x))
    x = copy.deepcopy(original); x["physical"]["linked-overcap"]["tail"]["prev"] = 0
    tamper.append(("signed predecessor", x))
    x = copy.deepcopy(original)
    x["observations"]["linked-overcap"]["catch"][0]["depth"] = 1
    tamper.append(("silent selected generation", x))
    x = copy.deepcopy(original)
    x["observations"]["orphan-overcap"]["gated"][0]["status"] = "opened"
    tamper.append(("false acceptance", x))
    for name, forged in tamper:
        try:
            audit(root, forged)
        except (ValueError, AssertionError, KeyError):
            continue
        raise AssertionError("forged receipt accepted: " + name)
    return len(tamper)

def main(root):
    record = json.loads((root / "result.json").read_text())
    assertions = audit(root, record)
    negatives = mutation_checks(root, record)
    print("J24G18_INDEPENDENT_PHYSICAL_REFEREE=PASS assertions=" +
          str(assertions) + " deliberate_forgeries_rejected=" + str(negatives))
    (root / "referee.json").write_text(json.dumps({
        "status": "PASS", "assertions": assertions,
        "forgeries_rejected": negatives,
        "scope": "signed physical footer plus cross-Reader receipt integrity, not independent complete reader"},
        sort_keys=True, indent=2) + "\n")

if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "j24g18-artifacts"))

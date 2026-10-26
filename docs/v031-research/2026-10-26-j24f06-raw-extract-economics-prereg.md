# J24F06 — physical RSS / CPU / wall court for authentic RAW extraction

Date: 2026-10-26 UTC. Status: **PREREGISTERED BEFORE INSTRUMENT AND MEASUREMENTS**. Research/economics only; **no product mutation, merge or release**.

## Authority, real source, and ownership

Released v0.30.0 / physical r24 unchanged. Parent J24F05 #540 exact `1885cb0658cacd34a50d05e45b541ecb76fc8497`, Reader blob `41efeb9d3301fc06b1df56ab6bd42d9ee91f6d5e`. Strong earlier J24F04 #537 control exact `d5aa5cbc1ef1e00b6e3c8c72cdd1598192d563a3`, Reader blob `8b5910725260e7b4db155ee0b393eb48a42f7efa`. The J24F05 owner explicitly leaves complete actual RSS/CPU/wall and syscall economics unmeasured. This independent child *only* measures them, does not modify either Reader or the hostile source-write courts. Other issues remain separately owned: staged path substitution #528, mmap truncation/SIGBUS #460, Windows metadata #535/#536.

## Primary falsifiable question

On **the same physical, Builder-independent authentic r24 RAW archive** and the same installed native/Python package, can the J24F05 64-KiB-copy Reader lower *process peak RSS* while preserving exact extraction, without exporting a **confirmed** material create-independent wall/CPU penalty or materially increased stage I/O? The parent J24F04 whole-chunk copy is the strongest simple positive-security control. A lightweight Python `tracemalloc` proxy is not sufficient: use fresh subprocesses and OS-reported high-water RSS, and measure actual Reader `extractall` in the same worker process excluding interpreter startup from wall/CPU.

## Predictions, alternatives, and decision conditions

- Verify historical and candidate Git blob identities at runtime; load their exact `reader.py` source into separate module namespaces against the **same** installed supporting package. **No monkeypatch of the extraction algorithm.** Both must extract exactly the same indexed logical bytes, and every output SHA-256 must match a controller-generated independent SHA-256. Any mismatch, nonzero unexplained error or source/authentication mismatch invalidates the result.
- Create independently authenticated revision-24 S_CHUNKS and S_CDC archives containing 16-MiB and 64-MiB primary RAW physical chunks plus a short different RAW chunk. No compression-policy heuristics or fixture identity detection.
- Execute independent fresh-process complete Reader open+extract A/B on the same runner in an ABBA schedule, with two cycles per size/representation (four observations per arm); preserve **all raw trial** wall, CPU, RSS and `os.write` transfer calls/bytes, process/OS/Python identity. Equal output is a hard correctness prerequisite.
- Hypothesis: J24F05 materially reduces peak RSS on 64 MiB RAW. It may increase `os.write` call count; this is a real cost, never hide it. CPU/wall verdict should preserve uncertainty when variability is large. Initial materiality screen: >5% **and** >3 ms penalty (a prospective exploratory screen, **not** a replacement for the official frozen performance comparator), but no release decision from it.
- Distinguish whole-process RSS high-water from incremental memory. A baseline import or fixture generation before extraction may pollute RSS if not isolated; measure per worker. If high-water does not meaningfully separate arms, classify RSS inconclusive rather than claim gain from the Python proxy.
- Product cost comparison excludes package install and process spawn from measured timings, but includes Reader open, extraction, hash, close and stage writes; independent output SHA verification follows the measured interval. Account stage logical byte totals and observed syscall counts. No proof of stage identity, truncation resistance, portability or entire ZIP/parity from this court.

## Cheap controls, alternative explanations, and falsifiers

A static observation already proves each J24F05 owned copy <=64 KiB; J24F04 proved whole-chunk copy. That is enough to justify the bounded A/B but cannot establish actual process RSS. Repeat against same-input/host with alternated order to separate a true systematic cost from warm pagecache/host noise. The source has unchanged format/parser outside this Reader change. If the baseline reader import requires a different product dependency or the output differs, mark attribution **AMBIGUOUS** and stop. If the harness observes no actual stage writes or an archive without a large RAW physical chunk, it is invalid. Preserve negative runs, infrastructure failure, and contradictory results. No budget/method change to frozen product gates.

## Decision and handoff

A significant RSS reduction and no evidenced material CPU/wall penalty justifies **continued productization**, not promotion. A material slowdown preserves J24F05 as a security/memory seed with explicit exported debt. A contaminated or incomplete comparison earns no product credit. CI jobs must preserve artifact JSON, source identities and exact-run URL; post to both J24F05 and J24F04 owners only after evidence; `docs/discovery/STATE.json` is staleable and must not be overwritten by this independent lane.

Counterfactual: the earlier 16-MiB `tracemalloc` proxy was insufficient to decide real RSS; a same-process, same-archive A/B with explicit peak-RSS accounting is the lowest additional evidence rung capable of changing the integration-economic decision. This is not a Discovery Engine policy amendment.

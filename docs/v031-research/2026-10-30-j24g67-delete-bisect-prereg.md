# J24G67 preregistration — sorted DELETE replay, no persisted name index

**2026-10-30 UTC. Before experimental code/workflow. DRAFT RESEARCH ONLY.** Parent: J24G63 #805, `7f509d244325d4b6ea6d0e752ea365f79c33a742`, which inherits the J24G57 shared journal correctness repairs. Do not change Builder, Writer, Reader, `journal_replay.py`, format r24, frozen evaluators, `main`, or other agents' branches.

## Evidence and question

Physical source-exact 63 one-op public Writer DELETE generations on 2,048 surviving files cost +31–53 ms versus a private checkpoint on J24G63 #805, and J24G65 #809 attributes 97–98% of the extra Reader-open time to repeated replay. J24G64 #808 owns *mixed* cross-generation mutable-dictionary factoring, including sparse signed fsmeta. J24G66 #810 owns its physical signed-xattr falsifier. Those owners are not duplicated. This experiment tests the materially simpler alternative: **for a verified sorted unique base index and a DELETE-only generation chain with no sparse per-file metadata, can in-place binary-search deletion eliminate most repeated replay work without retaining another O(N) dictionary/name-array, changing bytes, or changing any Reader semantic?**

## Prospective mechanism and strongest simpler controls

Baseline = exact inherited `cmpct.journal_replay._apply_journal_ops` called by installed Reader for every public signed single-op delta. Candidate = in-memory, *research-only* patched Reader replay callback: admit sorted/unique file names once on first delta, require each delta to be a grammatical single `["del", <str>]` and absence of per-file sparse `fsmeta.xattrs` and `fsmeta.owner_overrides`; binary search directly on `row[0]`, `list.pop` only for an existing name, preserve list order, never allocate a retained name→row index. All other input falls back to **unchanged original helper** and disables optimization for the remainder of the chain. Strongest simpler control is baseline itself; no-op/replace-only optimized product path remains untouched. Prediction: 2,048 survivors, 63 DELETE generations, Reader-open median wall speedup >=2.0× and >=3ms lower on >=2 of Ubuntu 24.04/macOS 14/Windows 2022 with no output, archive bytes, decode, integrity, or metadata changes.

## Measurement and falsification

1. Generate one physical r24 archive using the real `Builder` and 63 public `append_delete` calls, with 2,111 input files and 2,048 survivors, targets spread over sorted positions. Keep source/Writer/replay blobs exact. Assert 64 authenticated footers, 63 single `del` operations, pristine archive SHA, Reader and preflight final index equality and all live bytes exact.
2. Run 8 alternating A/B/B/A (or B/A/A/B) pairs per host, timing **only Reader construction/open** after Python imports, with each invocation isolated from the other's callback state; record wall and process CPU raw observations, median, min/max, bytes and source identities. The Reader's reconstructed index and MessagePack serialization **must be byte-identical** between controls. Use a checksum that covers all raw samples.
3. Attack admission and semantics with independently generated sorted-unsorted, duplicate names, missing DELETE, sparse xattr, owner override, malformed opcode, multi-op, and DELETE+PUT/RENAME sequences. For each, compare exact resulting state and/or exact exception type/message to inherited helper; no mutation of supplied original source objects. Check that fallback is exercised (do not silently skip).
4. Isolated helper micro-A/B (same in-memory signed-delta replay input) can explain causal savings, but cannot substitute for actual Reader-open evidence; record cost of admission and resident auxiliary allocations using `tracemalloc` as tracked-only (not RSS). If the Reader integration cannot be safely confined to one opened index, or correctness diverges in any hostile case, mark **KILL/NOT_PROMOTABLE**, not a performance win.

## Alternative explanations / limitations

Signed footer decoding, Reader parser, Python instrumentation, OS cache and launch drift may dominate; strict chronological order can distort alternating comparisons. A fast DELETE-only path may lose applicability when signed xattrs exist, which are intentionally **not** promoted by this oracle and separately owned by #808/#810. This is a certified **special-case** research candidate only if generic admission is safe and carrying cost is justified. It cannot inherit #808's mixed/fsmeta performance claim, nor can #808 inherit this result without comparison. Source-exact full-Reader B/B validation would still precede any product patch.

No product claim for cold filesystem cache, complete archive create/extract, peak RSS, update cost, selective reads, signed fsmeta, hardlinks, recovery, Rust ABI, or ZIP/Zstd comparison. Frozen benchmarks, correctness, release/format/portability law unchanged. Posthoc fixes to instrument mistakes require new exact SHA and visible negative receipts; thresholds remain fixed.

## Decision ladder

- Any exactness/admission exception mismatch: reject the candidate.
- If 2/3 platforms fail >=2× plus >=3ms, retire this single-delete family unless a new measured cause justifies reframe.
- If it survives: hand it to rightful Reader owner #795 as a **simpler alternative** to general #808, conditioned on installed original/candidate same-physical-archive Reader A/B, adversarial/fsmeta fallback, size/create/read/extract/RSS/time, recovery and release gates.
- No merge/release/version bump or `docs/discovery/STATE.json` mutation from this research.

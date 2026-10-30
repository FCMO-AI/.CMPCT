# J24G74 — prospective uniquely-owned decoded-state replay court

2026-10-30 UTC. **Research only; no shipping code, no merge/release/version/format or evaluator change.**

## Exact prior and primary scientific question
Base is J24G73 draft #818 at `2bd44b03a37360b4c59af3bb6445553b2435ffff`, inheriting J24G64 #808 `factored()`. The published source remains CMPCT v0.30.0/r24 on main `80c358f8824ec1b20d349c92ed94c898090969b0`. J24G73 measured full Reader-open improvements of 3.30–3.78x on 63 authentic one-op DELETE generations, but added ~1.08 MiB traced Python peak and ~0.67–0.96 MiB post-open RSS. J24G73's `factored()` deep-copies the checkpoint index **and** all signed delta payloads before replay, although the Reader's `msgpack.unpackb` constructs these objects newly inside `_index_from_footer`, with no other persistent owner.

**Primary question:** Can a *research-only Reader-owned decoding boundary* transfer fresh decoded checkpoint/delta object ownership to the factored replay, eliminating those deep copies while preserving the same opened archive bytes, exact canonical index/metadata/content, read/extraction, footer failure recovery, and source integrity?

## Hypothesis and simpler controls
H1: With fresh locally decoded objects, one explicit ownership transfer can avoid deep-copy cost and improve **complete Reader open** over J24G73's copy-preserving FactoredCMPCT by >=10% in median wall on >=2/3 operating systems, with non-increased tracked peak Python allocations on >=2/3 platforms, while all exactness/recovery checks pass. No archive byte changes.

Reference controls, on **the same physical archive within each host**:
A) unmodified original `CMPCT`; B) unchanged J24G73 `FactoredCMPCT` including its conservative `factored()`; C) new **experiment-only** `OwnedCMPCT` with in-place rekey on newly unpacked private objects. Control A may win, and a bad C must not be promoted. The only allowed shortcut is avoiding duplicate ownership of decoded objects; admission, signed footer parsing, constraints, fallback and archive semantics stay intact.

## Prospective proof and rejection
- Identical physical Builder + public Writer archives: 2,111 -> 2,048 members via 63 DELETEs, and 128 -> 118 via 21 each rename/delete/put; 64 signed footers each, real sparse xattrs on Linux/macOS.
- Before timing: source blob attestation, exact independent expected index, deterministic MessagePack identity, all content read and `verify()`, preflight parity, native xattr extraction on POSIX, corrupt/truncated tail parity; fail if any semantics diverge. Require candidate's claimed owned route actually executed.
- Host OS matrix Ubuntu 24.04/macOS 14/Windows 2022. Balanced orders ABC/ACB/BAC/BCA/CAB/CBA per block (at least 24 open observations per variant per host, same inputs); raw wall/CPU; explicit warm-process boundary. Peak traced Python allocations; fresh-process RSS probes separated from imported-process controls. No fabricated no-disk-cost claim.
- Additional differential program must prove `owned` equivalent to inherited `factored` on fresh *independently decoded* objects and exact serialization for valid/adversarial update families. This is an **ownership-transfer contract**, not a guarantee that a public helper may mutate caller-held dictionaries: a retained mutable caller makes ownership transfer ineligible. Test the negative retained-caller case explicitly so that this research cannot silently be generalized to a public API.
- Stop/retire on incorrect path/xattr identity, tail divergence, fallback disagreement, memory regression, or no stable whole-Reader transfer. If wall win is below H1 threshold, preserve all metrics and mark ambiguous or negative, not positive.

## Costs and alternate explanations
The Reader may retain decoded objects through other structures, public descriptors or native bindings; this must be inspected before product integration. Aliasing after transfer is a fundamental hazard; this court is valid only because decoder outputs are fresh and not externally retained at entry. OS allocator behavior, imports, checkpoint depth and access patterns can explain apparent RSS changes, so traced allocations and fresh-process RSS are reported separately. A smaller copying algorithm with ordinary exposed inputs may be safer than raw mutation; compare against the existing baseline before advocating integration.

## Concurrency and boundary
This branch adds only `research/j24g74_*`, an isolated new CI workflow and its own J24G74 dossier. No changes to #818/#808/#795 owned scripts/source, no source ref rewrite, no discovery STATE.json (claimed by #574), no other PR edits. All decisions refer to exact measured HEADs and primary raw CI artifacts. Full product/format/ABI/release gates remain future work with integration owner #795/#808.

# v0.30 ML DGO1 bulk one-byte length-table parsing — productization preregistration

Status: **extraction mechanism proven; create-side scope debt blocks productization**.

Parent authority at experiment start: `agent/v030-authoritative-integration@e9028dd9e9e6a6c47c1228d9da32a37bf5fc378e`; production remains v0.29.0/r24. PR #148 subsequently advanced authoritative convergence independently; PR #152 must reconcile current authority before any merge.

Research provenance: PR #151. Exact-head run `35439489634`, source `cc710d5eecf2a6780f6d20b78a804559a85bffe6`, artifact `10582959452`, digest `sha256:75bbaaea1a9f207c467f3060435bde3fb367ae1ffa4c5769c037b6169c928a4d`. Four balanced fresh-process ML extraction pairs improved wall 23.7165%, 22.9895%, 24.1029%, 24.0018%; median **23.8592%**. CPU tracked wall and exact output tree identity held in every arm.

Post-#146 profile run `35439292455` attributed 0.08546 s cumulative to `release_single_buffer_delimiter_inverse`, including 0.02254 s self across 45,980 `_get_varint` calls. The prior PR #142 per-call fastpath was only ~3.30%; this mechanism instead removes the Python call loop when the complete length table is provably one-byte varints.

## Mechanism

Inside `release_single_buffer_delimiter_inverse`, after decoding and bounding `count`:

1. inspect exactly the next `count` encoded bytes;
2. use `bytes.isascii()` as a C-level proof that every byte has continuation bit clear (`< 0x80`);
3. only then materialize lengths directly from those bytes and advance `pos` by `count`;
4. if the slice is short or any byte has its high bit set, execute the unchanged generic `_get_varint` loop;
5. preserve all existing logical-size, total-length, max-length, cell-work, body-size, output-shape and trailing/body accounting checks.

This changes no archive grammar. It is a parser route for the already-valid one-byte subset and exact fallback for the full varint language.

## Strongest-control extraction evidence

Run `35442048869`, candidate `e2ccc9c46bfaa9fcfc4473ad6820ebb3782b4743`, exact authoritative-parent control `e9028dd9e9e6a6c47c1228d9da32a37bf5fc378e`, artifact `10583998125`, digest `sha256:6e4f433458d00cbe1cf624a1c2ca4528eb5f9eabc8f2094efdac327e0ecc1ee0`: four balanced fresh-process pairs improved wall **23.5498%, 23.0427%, 21.6686%, 24.6311%**, median **23.2963%**; CPU median **23.2994%**; exact tree every arm. This preserves ~97.64% of the research headroom. The earlier ~65% historical-control instrument is inadmissible because it double-counted older inverse improvements.

## Hostile / grammar proof

The research artifact constructs a DGO1 descriptor containing explicit multi-byte lengths 130 and 257. Candidate reconstruction equals the historical inverse byte-for-byte. Permanent product tests cover one-byte equivalence, explicit multi-byte fallback and malformed/truncated rejection equivalence. No integrity proof is removed.

## Newly discovered scope debt

Exact-head r24/ZIP run `35442276749`, artifact `10584019391`, preserved archive bytes exactly but failed the frozen same-runner timing rule on two **create** rows:

- media library create: `0.0288794 -> 0.0333948 s` (**+15.64%, +4.52 ms**);
- nested library create: `0.0161620 -> 0.0201266 s` (**+24.53%, +3.96 ms**).

Both clear the normative 5% **and** 3 ms regression thresholds. This red may not be waived as noise.

Source tracing establishes a credible causal route. PR #152 currently installs the optimized inverse globally through `C.SHARED.G.O.delimiter_inverse`. The canonical G04 build path calls `strong_verify(overlay_path)` before selection; `_decode_overlay_records()` reconstructs delimiter transforms through that same shared `O.delimiter_inverse`. Therefore the supposed extraction-only optimization is demonstrably visible to create-side proof work.

The repair is architectural scoping, not threshold tuning: preserve the shared Geometry inverse for writer/build/strong-control ownership and inject/select the bulk inverse only inside the verified release-extraction session. A safe implementation should make the inverse callable an explicit/default-strict `_G04Session` / `_stream_g04` dependency and opt into the bulk implementation only from `extract_verified_into_staging`, avoiding process-global mutation and concurrency hazards.

## Completion gates

- [x] bounded one-byte mechanism and exact generic fallback;
- [x] one-byte, explicit multi-byte and malformed/truncated equivalence regressions;
- [x] strongest-control fresh-process extraction A/B with exact tree;
- [x] identify exact-head create regression and causal shared-owner leak;
- [ ] remove process-global inverse installation and scope the fast inverse to verified extraction only;
- [ ] rerun extraction A/B and retain material headroom;
- [ ] rerun unchanged r24/ZIP gate with zero byte regressions and no confirmed timing regression;
- [ ] exact-head normal CI green after the scope repair;
- [ ] authoritative runtime gate, not projection, decides whether aggregate median extraction reaches <=1.10x.

No selector, threshold, writer byte, format revision, benchmark identity, locality law or integrity check may change.
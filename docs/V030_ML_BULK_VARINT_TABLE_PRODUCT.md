# v0.30 ML DGO1 bulk one-byte length-table parsing — productization preregistration

Status: **productization attempt earned; release credit unpaid**.

Parent authority: `agent/v030-authoritative-integration@e9028dd9e9e6a6c47c1228d9da32a37bf5fc378e`; production remains v0.29.0/r24.

Research provenance: PR #151. Exact-head run `35439489634`, source `cc710d5eecf2a6780f6d20b78a804559a85bffe6`, artifact `10582959452`, digest `sha256:75bbaaea1a9f207c467f3060435bde3fb367ae1ffa4c5769c037b6169c928a4d`. Four balanced fresh-process ML extraction pairs improved wall 23.7165%, 22.9895%, 24.1029%, 24.0018%; median **23.8592%**. CPU tracked wall and exact output tree identity held in every arm.

Post-#146 profile run `35439292455` attributed 0.08546 s cumulative to `release_single_buffer_delimiter_inverse`, including 0.02254 s self across 45,980 `_get_varint` calls. The prior PR #142 per-call fastpath was only ~3.30%; this mechanism instead removes the Python call loop when the complete length table is provably one-byte varints.

## Product seam

Inside `release_single_buffer_delimiter_inverse`, after decoding and bounding `count`:

1. inspect exactly the next `count` encoded bytes;
2. use `bytes.isascii()` as a C-level proof that every byte has continuation bit clear (`< 0x80`);
3. only then materialize lengths directly from those bytes and advance `pos` by `count`;
4. if the slice is short or any byte has its high bit set, execute the unchanged generic `_get_varint` loop;
5. preserve all existing logical-size, total-length, max-length, cell-work, body-size, output-shape and trailing/body accounting checks.

This changes no archive grammar. It is a parser route for the already-valid one-byte subset and exact fallback for the full varint language.

## Hostile proof already earned

The same exact-head artifact constructs a DGO1 descriptor containing explicit multi-byte lengths 130 and 257. Candidate reconstruction equals the historical inverse byte-for-byte. Four malformed truncations are rejected by both historical and candidate paths. Result: PASS.

## Completion gates

- [ ] implement the bounded route in the release-only verified restore owner;
- [ ] regression: one-byte table equivalence, explicit multi-byte fallback, malformed/truncated equivalence, maximum-count/resource bounds;
- [ ] fresh-process product A/B preserves exact tree and materially transfers the ~23.86% oracle gain;
- [ ] exact-head normal CI remains green;
- [ ] authoritative runtime gate, not projection, decides whether aggregate median extraction reaches <=1.10x.

No selector, threshold, writer byte, format revision, benchmark identity, locality law or integrity check may change.

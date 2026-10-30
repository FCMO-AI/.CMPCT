# J24G84/J24G84b — independent provider-artifact and adversarial receipt court

Date: 2026-10-30. Source-independent offline recalculation, **separate from** the GitHub Actions detached arithmetic checks. This does not replace the provider's original scientific result or establish full archive-format/product truth.

## Original, immutable hosted evidence

- J24G84 original run: [GitHub Actions 41063037132](https://github.com/FCMO-AI/.CMPCT/actions/runs/41063037132); code source HEAD `e50afd65c335487f3f5657163f4e054f8423aa0d`; artifact [12982235329](https://github.com/FCMO-AI/.CMPCT/actions/runs/41063037132/artifacts/12982235329); downloaded ZIP SHA-256 `1ca79ef0ccf6963c1904207d87213f681f76932bd47aa0b5924bed4fb6739a60` matches provider metadata.
- J24G84b original run: [GitHub Actions 41063716261](https://github.com/FCMO-AI/.CMPCT/actions/runs/41063716261); code source HEAD `c1db6c5fa69448e39e74f71847b9d34e30ac3bd3`; artifact [12981002517](https://github.com/FCMO-AI/.CMPCT/actions/runs/41063716261/artifacts/12981002517); downloaded ZIP SHA-256 `7133d0eb6db7c589505edbac836bc6c56314b57628a250b7c95233eb95ab1257` matches provider metadata.

## Independent local recomputation (no CMPCT imports)

An independently written Python verifier read the original ZIP entries, not copied result tables. It checked:
- Both artifact ZIP SHA-256 against provider digest and both `head.txt` references against source HEAD.
- Original J24G84: 4/4 source-candidate SHA-256 MessagePack equality, raw compressed-byte arithmetic, signed percent savings, ten reference and ten candidate raw timing observations, expected wire-byte size on every record, exact wall/CPU medians and original immutable decision criterion.
- J24G84b: 6/6 actual indices, L1 choice derived entirely from the **two L1 sizes**, L19 stored bytes including the candidate's one-byte selector, L19 best-oracle bound and regret, saved bytes/percent, SHA equality, raw 10+10 timing observations, exact medians, no false-positive rewrite, wall-debt gate and frozen decision criterion.
- The raw field called `cpu_debt_families` is actually counted from **wall-time ratios** in the research source; verifier preserved source semantics while labeling this limitation explicitly rather than silently changing the receipt.

Reproduced original decisions exactly: J24G84 **3 positive / 1 regressing**; `NO_GENERAL_METADATA_HEADROOM`. J24G84b **3 positive / 1 false admission / 3 wall-debt families**; `CHARGED_L1_SCOUT_NOT_PRODUCT_ELIGIBLE`.

## Nine independent falsified-receipt controls

The local auditor **rejected 9/9** independently mutated copies of otherwise genuine original receipts, spanning:
1. O0 false successful terminal decision;
2. O0 forged candidate size;
3. O0 forged semantic SHA;
4. O0 forged timing sample byte size;
5. O0b false successful terminal decision;
6. O0b covered-up hashed-deep false admission;
7. O0b forged candidate selector;
8. O0b altered wall-debt count;
9. O0b forged sample byte size.

The offline audit-result JSON SHA-256 was `2b3ef3e6cf53d7612dbc96ee20fe07e368d99489a9a3bb404dc55077a8a94e74`. Its source code was run locally after provider artifact download; the original provider ZIP and PR-bound hosted scripts are the reusable durable evidence. **This appendix is not a physical CMA4/MessagePack index decoder, nor an independent compression implementation; neither CI nor this offline check proves a valid alternative revision-24 archive exists.**

## Decision

Both original results survive independent arithmetic and receipt-adversarial recalculation. The *negative* is strengthened rather than rewritten: naive L1 selector cannot guarantee L19 order and exports CPU on fallback. No shipping-code, format, release, benchmark, comparator, policy or Discovery STATE modification. This appendix is evidence, not an extra scientific success score.

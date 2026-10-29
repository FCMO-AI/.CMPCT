# J24G29 — upper ZIP DOS calendar validity, preregistration

**Status:** preregistered before any new J24G29 product edit or hosted result. **Source frontier:** J24G28 PR #722 at `54a6cf2a2d4d8803150dd278e7e5a7f344d87782`; parent ZIP publication owner PR #492 at `ca01d885fedc8ffc343b9c3c624eddd134158452`. Released comparator is unchanged v0.30.0/r24 `main@80c358f8824ec1b20d349c92ed94c898090969b0`.

## Primary question

Does the currently inherited `_zip_dos_time` upper-year clamp produce an impossible Gregorian DOS date for a legitimate signed-r24 timestamp in leap year **2108**, and can one bounded fix preserve ordinary ZIP bytes, native metadata, the J24G28 negative-epoch correction and staged publication without a new format or decoder?

### Predicted mechanism and disproof

- **Baseline:** 2108-02-29 12:00 UTC is legal CMPCT member metadata and should remain readable/verifiable. In UTC/Linux it is `tm_year=2108, tm_mon=2, tm_mday=29`; existing code clamps **only the year** to 2107, encoding **2107-02-29**, a Gregorian-impossible date. Alternative explanation to test: the ZIP consumer might reject before field decode or platform localtime might change month/day.
- **Candidate:** When *local* `tm_year>2107`, saturate the entire DOS timestamp to **2107-12-31 23:59:58**, not merely the year. Retain the original localtime conversion for years 1980..2107, and the preceding J24G28 pre-1980 short circuit exactly; preserve CMPCT raw mtime_ns unchanged.
- **Controls:** Ordinary 2020 and 2107-12-30 must serialize identically to the J24G28 source on each host. The J24G28 signed-epoch cases must still serialize to 1980-01-01. Additional beyond-upper ordinary date 2108-03-01 must clamp. Reader read/verify, file payload, CRC and SHA must remain exact.
- **Kill or narrow:** Any host rejects a genuinely valid file in read/verify, any 1980..2107 same-host serialization difference outside an explicit timezone effect, any false Gregorian date in candidate, or any inherited Deflate/ZIP64/published-output regression prevents promotion. If only a synthetic helper comparison passes, award *mechanism evidence only*, not product credit.
- **Boundary:** This repair does not solve arbitrary platform `time.localtime` overflow, timezone-dependent ZIP headers, DST fold/ambiguity, symlink namespace races, complete ZIP integration, or full product economics.

## Cheapest evidence ladder

1. Before product mutation, reproduce the invalid derived 2107-02-29 with the actual inherited arithmetic and Python Gregorian validation; compare multiple timezones (local mechanism, no CMPCT product credit).
2. Make the narrowest Reader change and extend the **existing** J24G28 physically authenticated Writer/Builder three-OS court, running old and new installed Readers on identical r24 bytes. Add calendar validation, source hash and exact-head provenance to the instrument; preserve raw negative and normal controls.
3. Run inherited unchanged Deflate court, new exact-head specialized CI, general suite and performance gates. Treat failures as failures; do not rewrite historical checkouts to feign unchanged source.

## Concurrency/authority

This is continuation in **existing phase-2 ZIP-date owner PR #722**, not a duplicate PR or new chain. The staged-publication owner remains #492; another activation must read current head before writing. Do not edit owner #492, another agent's claims, discovery STATE (#574 owner), frozen benchmarks, format, version, general CI evaluators or release. No release/merge until all original gates survive.

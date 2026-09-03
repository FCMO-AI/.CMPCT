# R25 Logs native in-process FFI reader v1 — result

Status: **terminal scoped negative for this exact native FFI implementation; current-profile rerun permitted only by the reopening predicate below**

Decision: `LOGS_NATIVE_FFI_READER_V1_HEADROOM_NOT_SUPPORTED`

This result is research evidence only. It grants **zero release credit** and changes no selector, grammar, archive bytes, locality bound, integrity rule, recovery rule, benchmark threshold, or product contract.

## Tested regime

Result-bearing workflow:

- workflow: `CMPCT v0.30 logs native in-process FFI reader oracle`
- run: `33118755734`
- job: `98680040933`
- workflow source commit introducing the oracle/native boundary: `94fe27931f2839c9e4a5bacd850a7b88128b9009`
- historical PR merge checkout used by the then-current workflow topology: `01c00f12d8c5ebd55d17e865230e8f6d2715c52c`
- artifact: `9665843275`
- artifact ZIP SHA-256: `37f433096f61bba7f797425993009762821c64c21fabe71edea685a4222ca022`
- paired rounds: 5

The native shared library was loaded outside the timed region. The timed native path included the FFI call and archive open. The comparison preserved archive bytes, grammar, selector behavior, caller extract-budget enforcement, corruption rejection, and no release credit.

## Measured medians

| Operation | Python median | Native FFI median | Native/Python | Improvement fraction |
| --- | ---: | ---: | ---: | ---: |
| verify | 0.041556989 s | 0.104553035 s | 2.515895x | -151.5895% |
| extract | 0.046878964 s | 0.060394175 s | 1.288300x | -28.8300% |

The frozen promotion signal was `false`.

This is not a near miss. The tested Rust FFI boundary was materially slower for both operations, especially verify. Merely crossing into the existing native implementation did not remove enough Python-side overhead to offset the native reader's own work.

## Causal interpretation

The result falsifies the narrow hypothesis:

> The existing `native/cmpct-logs-ffi` implementation, called in-process through the measured v1 boundary, is a latency win over the canonical Python Logs inverse reader on the tested regime without changing bytes or semantics.

It does **not** falsify all future native decode work. In particular, it does not rule out a structurally different native hot path that removes duplicated archive-open/verification work, owns a narrower inverse-codec seam, or otherwise attacks the measured dominant decode components rather than porting the whole reader boundary.

Repository attribution still points at inverse decode as a major extract owner, and the Python gzip-wrapper micro-fastpath is separately retired as too small. A future native proposal therefore needs a new causal mechanism, not another wrapper spelling of this v1 implementation.

## Reopening predicate

Reopen this exact family only if at least one of the following is true and is stated before measurement:

1. the native implementation itself materially changes in a way expected to remove the measured overhead;
2. the canonical Logs profile changes the reader semantics or ownership boundary enough that the historical A/B no longer measures the current path;
3. a narrower native seam is introduced that does not reproduce the v1 whole-reader work;
4. new attribution evidence identifies a specific native-side cost that can be removed while preserving exact semantics.

The native FFI implementation file has not changed since the historical result. However, the canonical Logs inverse profile later changed its selective-read/ownership semantics (`94f5a539b4c7d08556331d8edba59d794dfa9e22`, `b5769dee3e4da60ea42a5f8b5ff0dbe641d02f0a`). That is sufficient to permit **one current-profile exact-head rerun** for transfer checking, but it is not evidence that the old implementation has improved.

## Carrying-cost decision

Do not productize this v1 FFI path. It adds a Rust FFI/library surface and platform burden while losing the latency objective it exists to improve. Any successor must earn its carrying cost with a material paired win before entering Builder/productization.

## Terminal scope

`LOGS_NATIVE_FFI_READER_V1_HEADROOM_NOT_SUPPORTED` is a scoped negative for the historical v1 whole-reader implementation and measured profile. Preserve it to prevent rediscovery. A current-profile transfer rerun may update transfer knowledge; it may not rewrite this result.

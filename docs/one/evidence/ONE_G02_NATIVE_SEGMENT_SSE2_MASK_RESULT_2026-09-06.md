# ONE-G0.2 native segment SSE2-mask — terminal result

Date: 2026-09-06

## Decision

`reject_segment_sse2_mask_speed`

The first exact SSE2-mask implementation is rejected as the segment baseline because its transition-dense hostile case materially regresses, despite very large gains on the productive and ordinary-control matrices.

## Exact-source authority

- Branch: `research/cmpct1`
- Experimental line: `ONE-G0.2`
- Exact source head: `a5224630ad1ba6921468b1a862cd587bea0f3112`
- Workflow: `ONE-G0.2 native segment SSE2 mask`
- Run: `34044836194`
- Job: `101517934534`
- Artifact: `9992818188`
- Artifact digest: `sha256:c3461596ab813d1620c1bee19f8db929ddc5371b43fc93acd97eb52ddf4c05cc`
- Full ONE semantic/hostile tests before the falsifier: passed
- Falsifier semantic failures: `0`
- Frozen native timed rounds: `101`

The job is red because the frozen benchmark returned non-zero after failing its hostile performance gate. Evidence upload succeeded. This is a scientific rejection, not a CI infrastructure failure.

## Frozen performance result

- mature productive median candidate/baseline: **`0.2169355752x`**;
- mature productive worst: **`0.2731842171x`**;
- mature ordinary-control median: **`0.3479865987x`**;
- mature ordinary-control worst: **`0.3981813525x`**;
- mature transition-hostile median: **`1.5518232542x`**.

The productive result is exceptionally strong in isolation: roughly 78.3% less segment-kernel elapsed, or about 4.6x baseline throughput at the median. `shift_plus1` is near `0.20x`, `damage_quarter` near `0.21–0.22x`, and `fragmented_every96` near `0.27x` across mature sizes. Even `fragmented_every32` remains around `0.39–0.40x`.

However, the frozen hostile rule required transition-hostile mature median `<=1.03x`. The candidate instead reaches about `1.55x`, so it cannot advance to integrated-writer testing.

## Mechanism-level interpretation

The scalar baseline pays one equality test and branch-oriented run check per byte. The SSE2 candidate removes most of that cost by classifying 16 equality predicates at once, which is why low/moderate-transition workloads accelerate dramatically.

The first candidate then scans each run inside each 16-bit mask with repeated shift/mask/complement/`ctz` work. On the deliberately alternating predicate stream, every byte is a segment boundary, so the candidate executes the maximum run-scanner bookkeeping *in addition to* the unavoidable segment writes. The vector classification remains cheap; the per-run mask decoder becomes the new tax. That is a causal failure mode, not evidence that bulk equality classification itself is wrong.

## Semantic truth and later audit hardening

At this exact source, scalar C and SSE2 C emitted identical plans on all frozen rows and both reconstructed the exact target. After this negative was observed, the lane was additionally hardened with an independent Python maximal-run oracle before any future SIMD result can gain promotion authority. That later audit does not retroactively convert this rejected implementation into an advance.

## Non-claims

- No writer promotion.
- No product portability claim; this is x86-64/SSE2 research evidence only.
- No change to segment policy, ONE wire, stored bytes, reader semantics, locality, integrity or recovery.
- No v0.29/v0.30 comparison.

## Next decisive work

Preserve the 16-byte equality-mask insight but replace the run decoder. A second preregistered implementation should compute the exact **transition bitset** for each equality mask (`predicate XOR shifted predicate`), use zero-transition fast continuation, and handle the all-transition block as a direct tight emission loop rather than repeatedly rediscovering one-byte runs through `ctz`/mask reconstruction. Intermediate transition masks may enumerate set transition bits directly.

The second lane must keep the same exact plan, independent Python oracle, tail vectors and hostile matrix. It must not introduce workload/size classifiers or relax the `<=1.03x` transition-hostile gate.

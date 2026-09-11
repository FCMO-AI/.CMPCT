# ONE-G0.2 root-hash writer native-buffer direct-wire V3 — terminal result

Date: 2026-09-06
Branch: `research/cmpct1`
Experimental line: `ONE-G0.2`

## Mission lock

Test the preregistered V3 compiler-fusion hypothesis without changing ONE semantics, workload membership, or gates:

`native segment buffer -> Python tuple plan + Surprise copies -> canonical ONE0 wire`

versus

`native segment buffer -> canonical ONE0 wire`.

The reader, canonical representation, segment boundaries, Law/Surprise decisions, node ordering, refs, roots, hashes, reconstruction semantics, and hostile resource/validation rules remain unchanged.

## Exact-source authority

- preregistration: `docs/one/evidence/ONE_G02_ROOT_HASH_WRITER_NATIVE_BUFFER_DIRECT_WIRE_V3_PREREG_2026-09-06.md`
- falsifier: `benchmarks/one/one_g02_root_hash_writer_native_buffer_direct_wire_v3.py`
- exact CI source SHA: `683d70b17b9a94ae5823dd2ed0e5f23a718ddd64`
- workflow: `ONE-G0.2 root-hash writer native-buffer direct-wire v3`
- workflow run: `34051122051`
- job: `101534816983` (`v3-direct-wire`)
- artifact: `9994563912`
- artifact name: `one-g02-root-hash-writer-native-buffer-direct-wire-v3-683d70b17b9a94ae5823dd2ed0e5f23a718ddd64`
- artifact ZIP SHA-256: `73bca76feced0faf68d3b5d69280663ca5f27a5506160aa987068d513ba7537c`

CI conclusion is `failure` because the preregistered performance decision returned non-zero. Setup, installation, semantic/hostile tests, and artifact preservation all succeeded.

## Semantic / hostile truth

- `93 passed` in the ONE semantic/hostile suite
- semantic failures: `0`
- oracle failures: `0`
- malformed native-buffer probes: pass
- canonical wire: exact on measured rows
- reconstruction: exact on measured rows
- native-plan oracle: exact on measured rows

No reader-visible opcode, wire semantic, integrity rule, locality rule, recovery rule, or resource bound was weakened.

## Frozen gate and measured result

Preregistered promotion gate for mature rows:

- productive median writer ratio `<= 0.90x`
- at least 12 mature productive rows `<= 0.95x`
- no mature productive row `> 1.03x`
- mature controls median `<= 1.03x`
- no mature control row `> 1.08x`

Measured exact-source result:

- mature productive median: **`0.8730217917151308x`**
- mature productive rows at or below `0.95x`: **`10`**
- mature productive worst: **`0.9939820808949195x`**
- mature control median: **`1.00134486032056x`**
- mature control worst: **`1.010654735080152x`**

## Terminal decision

**`reject_native_buffer_direct_wire_v3`**

V3 passes the median, productive-worst, control-median, and control-worst gates, while preserving exact semantics. It nevertheless fails the preregistered breadth gate because only **10** mature productive rows reach `<=0.95x`; promotion required **12**.

This is a terminal negative for V3 as preregistered. Do not rescue it through workload-, size-, segment-count-, Surprise-density-, or other post-hoc gating.

## Causal evidence retained

The negative is unusually informative rather than weak:

- `shift_plus1_damage_quarter` rows show very large gains, falling from about `0.65x` at the smallest measured mature case toward roughly `0.49-0.58x` on larger cases.
- `fragmented_every96` productive rows repeatedly land around `0.87-0.88x`.
- plain `shift_plus1` rows remain close to baseline, roughly `0.97-0.994x`, and therefore supply much of the breadth-gate miss.
- controls remain near `1.00x`.

The direct native-buffer-to-wire principle therefore removes real work whose cost grows with segment / Surprise / assembly complexity, but that work is not a large enough fraction of all productive rows to promote this exact V3 implementation universally.

The next general ONE writer work should absorb this causal lesson rather than add a conditional V3 path: attack the remaining per-segment / hierarchy / canonical-assembly work in a single general representation path, and measure the whole writer again. The useful structure is *eliminating redundant intermediate materialization*, not classifying inputs to decide whether to invoke a separate mechanism.

## Claim boundary

`root-hash-charged adjacent-version V2 writer compiler fusion only; arbitrary/fused discovery, RSS/native peak, filesystem/product and comparator authority excluded`

No claim is made here against frozen v0.29 or deferred v0.30, and no full 15-workload gate is advanced before 2026-09-11.

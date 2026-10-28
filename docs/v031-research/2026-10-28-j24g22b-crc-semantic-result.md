# J24G22b — CRC-only authentic-header divergence, decisive negative (2026-10-28 UTC)

**DECISION: THE CURRENT SHA-ONLY RANGE+SPOOL CANDIDATE IS FALSIFIED AS A TRANSPARENT REPLACEMENT FOR PUBLISHED `CMPCT.read()` / `cmpct cat`.** This decision does *not* retract J24G22's earlier positive late-payload-corruption result; its narrower witness is preserved in [J24G22 result](2026-10-28-j24g22-verified-stdout-result.md). Both results coexist and bound the actual implementation.

## Before-result registration and owner source
[Separate preregistration](2026-10-28-j24g22b-crc-semantic-prereg.md) committed **before instrument code** at `3a0b459d2742950792fcc63f755e1850c9a63443`. This tests the original frozen `main@80c358f8824ec1b20d349c92ed94c898090969b0` Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`. The observed source+test HEAD is `f4992027228b9517477176755c8f39f75c0c1049`, specialized [GitHub Actions run #40764750943](https://github.com/FCMO-AI/.CMPCT/actions/runs/40764750943) **SUCCESS**. Original physical evidence artifact **12848928802**, SHA-256 **`8ea1cdd9c94ca7b877a6e06bd5bc005eba678757792a8148b1cfcc7fc1e23f28`**. Source package/court method and prereg hashes are retained in this branch.

## Physical counterexample
First-party Builder generated a genuine 768-KiB direct RAW member; authenticated primary MessagePack index, member payload, physical SHA and footer are identical in pristine and CRC-mutant archives. Mutate **one low bit at physical byte 1,573,810**, the direct RAW blob's **BHDR CRC32 field**, with no payload or SHA changes. Original CRC32 = **2,697,402,520**; mutated declared CRC32 = **2,697,402,521**. Physical mutant SHA-256 = **`36b100fb6c7587a1e158ebb60b65f7daaf20e2a46ea8d7199587781dd8e11222`**.

An **independently authored physical-frame referee** (no imports of CMPCT or the test instrument) verified the two physical files differ at exactly that byte; BHDR structure, RAW payload and SHA-256 are unchanged; the original payload CRC equals original BHDR CRC but differs from mutated BHDR CRC. It independently rechecked original source SHA, printed transcript hashes, private emitted-byte counts and the exact SHA of data the candidate wrongly accepted. This is a real physical-frame independent audit, not a full second r24 Reader.

| Same invalid physical archive | Actual output bytes | Result |
|---|---:|---|
| Frozen published `CMPCT.read()` | **0** | Raises `OSError: blob integrity failure` |
| Frozen published `CMPCT.verify()` | **0** | Raises `OSError: blob integrity failure` |
| Naive ranged stream (unsafe research oracle) | **786,432** | Returns unchanged payload |
| J24G22 SHA-only temporary spool | **786,432** | **Accepts incorrectly**, because full SHA still matches |

Each output is written ONLY to the research CountingSink, never live user stdout. The stronger original Reader's per-blob CRC acceptance contract is therefore not equivalent to a SHA-only comparison of ranged bytes. A source-exact green spool court on the *different* late-payload corruption did not prove general parity, and this additional falsifier decisively demonstrates the missing semantic invariant.

## Impact and bounds
This defect is **in the research-only replacement**, not a newly introduced shipped CLI bug: published `cmpct cat` still uses the eager `read()` path. `read_range` is not a substitute for full-content integrity/acceptance. No product Reader, source, test threshold, native ABI, checksum algorithm, wire format, frozen benchmark or release lock was altered.

A future verified-stream design would have to preserve per-physical-blob CRC, framing, decode and size rejection alongside whole-file SHA before emitting. But **do not reflexively add one CRC threshold/patch to rescue this route**: existing first-party direct RAW members are bounded by the current Builder's 1 MiB default and the prior hosted J24G22 showed zero RSS reduction and exported all logical bytes to an anonymous temporary file. That low product leverage plus proven semantic debt warrants **RETIRE SHA-ONLY SPOOL AS DEFAULT** pending a materially different execution/proof architecture and representative source-domain headroom.

## Discovery and next unclaimed work
Primary question resolved with decisive hosted negative, no concurrent claim collision. Strongest counterfactual: derive the Reader's `_blob()` CRC contract and `read_range` fast-path bypass *before* implementing a spool; the cheapest exact oracle is the single-bit BHDR mutation tested here. This transfers to future work as a lesson about validating the entire acceptance language, not only final digest identity. **No evidence-backed policy modification** is earned from one episode and `docs/discovery/STATE.json` remains untouched under separate #574 ownership.

Prioritize existing integration of complete high-severity Reader/extraction correctness gates (#690/#693/#697/#573/#699) with actual general CI and release law. The experimental candidate is not a product replacement, no merge, no release, and no compression or extraction benefit claimed.

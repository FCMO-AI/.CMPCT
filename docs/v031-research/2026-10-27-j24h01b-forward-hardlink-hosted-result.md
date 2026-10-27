# J24H01 / J24H01b — Signed forward-hardlink extractability result

Date: 2026-10-27 UTC. **SCIENTIFIC RESULT — CONFIRMED in two independent hosted POSIX runners. NOT A PRODUCT FIX.**

## Authority, source and question
Canonical released source: `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0, r24. Scientific main preregistration `5cd15469257c18d6cd9f6eadb85381b53966e480`; first-party Writer follow-up preregistration `537a121d7ae8fbfd9a7673c94c84987a2b0a8079`. The original hypotheses and original hosted results remain unchanged.

**Main result:** a fully authenticated r24 index can be accepted by strict preflight, `read`, `read_range` and complete `verify` while `extractall` cannot reconstruct its correct filesystem tree solely because hardlink aliases precede physical owners in the sorted index.

**Material stronger result:** the shipping Writer API itself can produce this valid-but-unextractable state via an alias-only `append_rename` into an earlier path. This is not limited to hand-authored third-party archives.

## Exact hosted scientific evidence
1. [First scientific Actions #40578736477](https://github.com/FCMO-AI/.CMPCT/actions/runs/40578736477): commit `74eb8578610db00517ef663adcc7686e03a56251`, **Ubuntu 24.04 SUCCESS, macOS 14 SUCCESS**. Both platforms executed 2/2 observational cases. Raw receipts and code/blob/version identity artifacts reside in each job's uploaded ZIP.
2. [First-party Actions #40579414362](https://github.com/FCMO-AI/.CMPCT/actions/runs/40579414362): commit `6f6951f26f64e4ed265e67363b86b8089962692c`, **Ubuntu 24.04 SUCCESS, macOS 14 SUCCESS**, **3/3 cases per host**. Original two-case digests match the first experiment exactly; J24H01b adds true Writer transaction on disk.

| Evidence case | Real source | Strict preflight + reads/verify | Extract into empty destination |
| --- | --- | --- | --- |
| `a-alias → z-owner` | Independent reauthenticated Builder record | 2/2 rows PASS | **FAIL**: `hardlink target not yet extracted: z-owner` |
| `a → b → z` | Independent reauthenticated Builder record | 3/3 rows PASS | **FAIL**: `hardlink target not yet extracted: b-alias` |
| `Builder(b-owner,z-alias)` then `append_rename(z-alias,a-alias)` | **Unmodified public Writer** | 2/2 rows PASS, generation depth 1 | **FAIL**: `hardlink target not yet extracted: b-owner` |

Distinct fully signed archive SHA-256:
- Direct: `2979dc69b649aae08f3e1a316d1779ec8506e6e48667b117c959e35519ef8a80`
- Two-hop: `699bf2e1fc76280411bf29e325b00aea248f646d97dc13e43de41faccf7162d8`
- Original first-party Builder before rename: `807e59aea42ffdfa544997751f4b6415cc1af90889f37cb60115c3c1f6149649`
- **First-party Writer generation after rename:** `0333e9872d8b940cd58e3c9212277a6ba6666f5810527105090fc0180a35e0f5`
- Shared unchanged synthetic physical data SHA-256: `0ea7dc7f5030cca0639b4abad504f7ffd499154c772efdfdbc870103dc12c843`

The original ordinary Builder control passes strict preflight, complete SHA reads/verify, extraction, byte identity, and hardlink inode identity on both systems. This prevents a misleading explanation of a broken source file or filesystem hardlink primitive.

## Root cause and negative boundaries
- `validation._validate_index` accepts acyclic references to later regular physical members. Active graph owner #615 further enforces terminal K_FILE and equal sizes, **but does not impose ordering**; the exact J24H01 cases satisfy its additional invariants by static inspection. The frozen #615 HEAD itself has not been executed against this court.
- `reader.CMPCT.read` resolves references in logical map; `extractall` requires already-existing *physical target path* during single lexical pass. Current composite Reader #569 retains this check.
- `transactions.append_rename` legally renames an alias from `z-alias` to earlier `a-alias` without changing the valid target `b-owner`; newly appended generation validates and verifies yet becomes unextractable.
- Not evidence of file contents changing, unauthorized access, a remote exploit, an on-disk format change or a compression/CPU win. No Windows test is credited at this result boundary.
- Different from existing issue #237, whose source owner was renamed/deleted, invalidating alias target and preflight. Here only the alias is renamed; its target still exists, all validation passes.

## Decision, coordination and promotion
[Canonical issue #619](https://github.com/FCMO-AI/.CMPCT/issues/619) opened for product-owner handoff; [PR #569](https://github.com/FCMO-AI/.CMPCT/pull/569) was notified. No edits to their branches, no overlap with the #615 graph implementation.

A product repair should choose a bounded dependency/owner materialization plan (physical owners first, aliases resolved to existing inode) or an explicit consistent admission policy that also governs legitimate first-party append rename **before committing the footer**. Either choice must preserve exact hash/inode semantics, symlink and path safety, destination failure behavior, cross-platform portability, valid old r24 records and full release parity. Handle two-hop chains, directory/symlink targets, cycles, wrong sizes and embedded delta generations with hostile controls. No attempt to manufacture merge/release credit from this research.

## Counterfactual and reusable lesson
The earliest cheap predictive discriminator was the mismatch between validation's unordered graph and extraction's ordered filesystem materialization. Static code review correctly suggested a cheap archive oracle, but **the Writer alias-rename control is the stronger simplest comparison** because it eliminates all doubts about independent synthetic signing. Future logical-reference designs should test API-wide graph validity versus materialization order, not only parse/read/verify.

**Decision:** reconstructability defect CONFIRMED, including real Writer API route. Scientific frontier advanced; product correction unimplemented. Discovery policy and STATE.json unchanged; no evidence-backed process policy mutation earned.

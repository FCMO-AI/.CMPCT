# ONE-G0.2 authenticated complete-archive envelope — result

Date: 2026-09-09  
Experimental version: ONE-G0.2  
Decision: **ADVANCE_AUTHENTICATED_ARCHIVE_ENVELOPE**

## Exact hosted authority

- branch: `research/cmpct1`
- exact source: `a4d4a907319f95a90251ca18bb35cfb80ce1a718`
- workflow: `CMPCT1 ONE-G0.2 authenticated complete archive envelope`
- run: `34423218419`
- job: `102702911256`
- artifact: `10131707370`
- artifact ZIP digest: `sha256:b72c17879698f10a533b3b6fd2127d78b41033d37cf8ccee7816a9ed3b211b86`
- exact-source semantic suite: **71 passed in 4.39s**
- frozen falsifier decision: **ADVANCE_AUTHENTICATED_ARCHIVE_ENVELOPE**

The earlier runs are not scientific result authority: one exposed hostile-test/API boundary defects before reaching the frozen economics, and a later run reached 71 passing semantics but failed to import the benchmark module because the workflow executed a path-scoped Python script without the repository root on `PYTHONPATH`. The exact result source above changes only that execution environment to `PYTHONPATH=.`; the candidate, preregistration, corpus, accounting and thresholds are unchanged.

## Mission lock

The complete Surprise archive seam and generic authenticated selective-cone machinery had already been proven independently. This experiment asked whether those pieces actually compose into a single deterministic, independently reopenable ONE0 artifact whose authentication state is persisted and charged, while small reads reconstruct only the authenticated ONE dependency cone.

No reader-visible compression or integrity codec was added. File payloads remain ordinary ONE roots. Per-file authentication trees are generic Crystallization metadata embedded in the canonical manifest, which is itself an authenticated ONE root.

## Frozen result

All semantic, hostile and physical gates pass.

### Complete artifact and authentication cost

Synthetic system-seam fixture:

- logical regular-file bytes: **1,327,314 B**;
- Surprise-only base wire: **1,328,060 B**;
- authenticated archive wire: **1,356,848 B**;
- physical wire delta: **28,788 B**;
- base manifest: **505 B**;
- authenticated manifest: **29,290 B**;
- physical auth-manifest delta: **28,785 B = 2.1687% of logical bytes**;
- raw generic AuthTree index bytes: **21,164 B**.

The preregistered gate was not aggregate-only: every regular file >=64 KiB had to keep its persisted physical authentication metadata below 3.0% of its own logical length.

- `large.bin`, 1,065,097 B: **22,694 B = 2.1307%**;
- `medium.bin`, 262,217 B: **5,920 B = 2.2577%**;
- violations: **none**.

The empty-file metadata cost is 171 physical manifest bytes; tiny-file percentage efficiency was not a promotion gate and remains an explicit future packing target.

### Selective reconstruction

Seven frozen requests passed exact byte and authentication semantics. There were **zero full-file reconstruction violations**.

Examples:

- 64-byte prefix of a 1,065,097-byte file -> **4,096-byte authenticated cone**, 4,096 source bytes, one command;
- 127-byte request crossing an authentication-leaf boundary -> **8,192-byte cone**;
- 127-byte request crossing the underlying 1 MiB ONE Surprise/concat chunk boundary -> **8,192-byte cone**, two commands;
- 4,096-byte middle request -> **8,192-byte cone** under leaf alignment;
- final 257-byte request -> **4,233-byte terminal cone**;
- zero-length empty-file request -> **0-byte cone**.

For the decisive cross-ONE-chunk request, the system reopens from the serialized archive and authenticates/reconstructs only 8,192 bytes of a >1 MiB file rather than reconstructing the full object.

## Hostile semantics

The exact-source suite rejects, among inherited and new cases:

- altered stored authentication root;
- malformed base64 level data;
- wrong authentication level width/count;
- internally inconsistent parent hashes;
- missing per-file authentication metadata;
- out-of-range archive reads;
- escaping symlinks and malformed archive paths;
- malformed manifest/root length or digest relationships;
- inherited authenticated selective-range and Program validation failures.

Opening validates stored tree geometry and parent/root commitments without reconstructing file payloads. Requested leaves remain verified against those commitments during the selective read.

## Strongest negative / regression debt

The writer currently performs a **complete second source read of 1,327,314 B** solely to build the authentication trees. This is deliberately reported, not hidden as metadata preparation. Therefore this result promotes the representation/system-composition seam, **not this writer implementation as economically final**.

A preferred archive writer must construct leaf hashes during the normal fused source observation/read pass, eliminating that 1.0x additional source reread without changing the archive semantics or authentication format.

Additional debt remains:

1. the auth index is JSON/base64 in this research seam; the measured ~2.1-2.3% large-file cost passes the frozen gate but is not a final compact metadata encoding;
2. tiny files pay high fixed metadata percentages and eventually require common packing/manifest economics rather than weakening authentication;
3. this archive seam still does not establish complete mature-CMPCT recovery, transactional generations, ACL/xattr/hardlink/sparse-allocation or ZIP-export parity;
4. file payloads in this specific seam are still Surprise-only — promoted Law discovery/writer results have not yet been compiled into the complete archive path;
5. the September 11 15-workload Genesis comparison has not been run and no supersession claim follows from this result.

## Campaign significance

This closes a material integration gap. ONE now has evidence for a single serialized artifact that can be built, reopened independently, expose archive/file semantics, retain bounded Program validation, and answer authenticated selective reads through Reconstruction Cones. The strong mechanism-level selective-authentication result is no longer isolated from the complete artifact boundary.

The next system-level task is to compile already-proven generic Laws into this same archive world while preserving the Surprise-only fallback and the authenticated/selective properties, then meter the complete system rather than separate microbenchmarks.

## Comparator / Genesis truth

Frozen comparator authorities remain unchanged:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- deferred v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

The gate-readiness substrate remains separate and has already reached 15/15 identity readiness without scoring. This experiment uses synthetic system vectors and does not inspect or tune against the frozen Genesis workload outcomes.

## Next decisive action

Preregister and build the first complete archive compiler that replaces profitable Surprise spans with an already-proven generic Law inside the same ONE Program while retaining byte-identical Surprise fallback where Law is not profitable. Charge complete wire, creation CPU/wall, source traffic, peak memory, reopen/decode and the frozen selective/authenticated request geometry. In parallel, fuse AuthTree leaf construction into the common observation pass so the current 1.0x authentication-only reread disappears.

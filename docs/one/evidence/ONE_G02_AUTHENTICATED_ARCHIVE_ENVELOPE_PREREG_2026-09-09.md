# ONE-G0.2 authenticated complete-archive envelope — preregistration

Date: 2026-09-09  
Status: **PREREGISTERED / NO RESULT YET**

## Mission Lock / Referee

The complete Surprise-only archive seam and the authenticated selective-cone reader have now been proven separately. The next system question is whether those two promoted principles actually compose into one independently reopenable ONE0 artifact without whole-file reconstruction, reader discovery, an opaque integrity codec, or uncharged side state.

### Falsifiable hypothesis

A deterministic ONE archive can embed the generic per-file authentication-tree crystallization inside its already-authenticated manifest, reopen using serialized bytes alone, and answer authenticated file-range requests by reconstructing only the Merkle-leaf-aligned ONE dependency cone. The stored authentication metadata must be explicitly charged, and unsupported/tampered metadata must fail closed.

### Disproof

HOLD or invalidate the candidate if any of the following occurs:

1. reopening requires creator-side Python objects or unstored state;
2. reconstructed range bytes differ from the source;
3. a positive range request reconstructs the complete file merely to authenticate a small range;
4. authentication metadata, root commitments or tree geometry are accepted malformed;
5. tampered payload/proof material can produce an accepted range;
6. path/resource/manifest validation weakens relative to the complete Surprise archive seam;
7. the candidate introduces a reader-visible compression/integrity codec rather than generic ONE roots plus a generic authentication Crystal;
8. stored authentication bytes are omitted from archive-size accounting;
9. for regular files >=64 KiB in the frozen integration fixtures, physical manifest growth attributable to the persisted authentication index exceeds 3.0% of logical file bytes without an explicit HOLD.

There is intentionally **no creation-speed promotion gate** for this first composition experiment. The initial builder is allowed to reread source files once to build authentication trees, but every reread byte must be reported as regression debt. A later promotion to preferred system writer requires fusing authentication construction into the normal observation/read pass rather than hiding that extra I/O.

## Frozen representation

No new ONE opcode is allowed. File bytes remain ordinary ONE roots made from the existing grammar. Authentication is generic Crystallization metadata attached to each file entry in the canonical manifest:

- fixed integration leaf size: 4096 bytes;
- generic domain-separated AuthTree semantics already used by `experiments/one/auth_tree.py`;
- expected root commitment stored in the manifest;
- tree levels serialized as base64-encoded concatenated 32-byte hashes, with level widths derived and validated from file length and leaf size;
- no separate creator-side index is authoritative after serialization.

Base64 here is only the JSON representation of binary authentication metadata; it carries no compression semantics.

## Frozen integration vectors

The semantic matrix must include at least:

- empty file;
- sub-leaf file;
- exactly one-leaf file;
- >1 MiB file spanning multiple Surprise chunks and many auth leaves;
- requests at start, middle, end and crossing an auth-leaf boundary;
- request crossing an underlying ONE concat/chunk boundary;
- zero-length request where supported by inherited semantics;
- duplicate-content files remaining distinct archive entries;
- directory and safe symlink preservation;
- mutated auth root;
- malformed base64;
- wrong level count/width;
- missing auth metadata;
- range outside file;
- ordinary archive path-safety and malformed-manifest inherited tests.

## Required measurements

Persist at minimum:

- logical file bytes;
- complete wire bytes;
- base-manifest bytes;
- authenticated-manifest bytes;
- physical auth-manifest delta bytes;
- raw generic AuthTree index bytes;
- source reread bytes used only to build authentication;
- requested bytes;
- reconstructed cone bytes;
- source-read / source-plan-write / sink-write bytes;
- proof payload/hash bytes;
- plan command count;
- exact semantic/authentication outcome.

Do not use this integration experiment as the September 11 Genesis comparison. It is system-composition evidence only and must not inspect or tune against the frozen 15-workload gate matrix.

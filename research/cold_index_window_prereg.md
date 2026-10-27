# Cold-tree index-window experiment

State: preregistered before index audition; **research only, no release credit**.
Base: `32d288d6` (r24 CLI), with the optional-audio fix measured separately.

Problem: global content interning already removes exact file duplicates. It does not remove
repeated logical namespace/metadata rows in the two compressed index copies. Local compression
context may fail to reuse distant repeated subtrees even when payload deduplication is perfect.

Hypothesis: a longer index-only context reduces complete archive bytes while leaving physical
payloads and selective payload decoding unchanged. Alternative explanations are codec effort and
ordinary level-19 compression; compare level 12, level 19, and level 19 with long window.

Prediction: long-window index compression strictly beats the inherited index on a repeated
namespace tree. Disproof: no complete-archive saving; if level 19 alone equals long-window,
the long-window causal explanation is unsupported. No corpus-specific encoder threshold is fitted.

The simpler control is genuine unchanged r24. The experiment accepts the new complete checkpoint
only when both index copies together shrink; ties/losses retain the original artifact byte-for-byte.
Logical SHA-256, index SHA-256, blob framing, payload bytes, filesystem semantics and r24 grammar
must remain unchanged. Reject journals, recovered/damaged primary indexes and trailing junk.

Exported costs: one extra compression pass, metadata decode/memory, longer-window decoder memory,
and slower index open are possible. Preserve create/rewrite/open/extract/RSS measurements; smaller
bytes alone do not authorize promotion. Check all-member hashes and selected member bytes.

The public analogue is `benchmarks/cold_tree_corpus.py`. A private tree may supply internal
aggregate signals only. If the pinned package runtime is unavailable, substituted-backend results
must be labeled diagnostic; no current-release performance or promotion claim follows.

An earlier container-cohort hypothesis was killed at the inventory rung: the local tree contains
zero ZIP/WHL members. Do not implement a container-specific optimization for that workload.

Reproduction note added after measurement: the encoder/reader tree at the local base is identical
to public main `80c358f8824ec1b20d349c92ed94c898090969b0`; the intervening commit adds only the
brief and earlier pilot. Public reproduction uses that main plus the separately identified audio fix.

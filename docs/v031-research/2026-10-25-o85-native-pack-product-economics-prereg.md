# O85 — Authentic native C ABI S_PACK repeated-decode economics (preregistration)

Date: 2026-10-25 UTC. Status: prediction frozen **before** the instrument and hosted measurement. Authority: canonical `FCMO-AI/.CMPCT`, release v0.30.0, on-disk r24. Exact v0.31 source base `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Source native implementation unchanged. Related open issue #315; neither PR #307/#314 native conformance nor PR #426/#429 ZIP cohort locality is replaced.

## Primary question and causal owner

Can ordinary micro-PACK storage save full archive bytes but impose economically material repeated authenticated whole-blob native C ABI decompression when many distinct tiny logical members share one physical Zstd PACK? Current `Archive::read_range` -> `Storage::Pack` -> `read_blob_range` -> `decode_zstd_blob` apparently rebuilds and SHA-authenticates the same whole physical blob on each call. This is code-level prediction, not measured native product evidence. Python's Reader has a separate bounded blob cache, so do not conflate its behavior with the Rust C ABI.

## Frozen input and strong control

Generate one deterministic 256-member text tree with different ~0.75-1 KiB payloads, unique names, common structure. Build two *authentic* revision-24 archives from the **same physical source tree and unchanged Builder**: shipping micro-PACK admission, and an explicit research-only no-PACK control (one instance-local override of `_build_micro_packs`; do not change shipping code). Inspect index to require S_PACK with **at least 128 distinct members on one CODEC_ZSTD physical owner**; no-PACK control must contain no S_PACK. If the fixture fails this condition, report fixture/instrument failure, not a favorable result.

For both archives, independently validate full Python read/verify and same member content, then exercise real installed Rust C ABI `cmpct_open / cmpct_entry_read_range / cmpct_close`: one 64-byte selective range from 1, 16, 128 and 256 distinct members. Five fresh processes per arm for each N, alternating arm order, with measured in-process C ABI read-only wall+CPU and separately recorded whole-process wall and peak RSS. Preserve all 40 raw observations, input/blob/size fingerprints, platform/runtime/native identities, and every negative. Startup and building the archive are not included in the read CPU number; disclose them separately.

## Predictions and kill/narrow conditions

Predictions: N=1 should not necessarily favor unpacked storage; larger N should amplify complete physical PACK decoded work relative to member payload bytes and worsen native read CPU versus no-PACK, while packed archive is likely smaller. No-PACK might itself compress poorly; count full archive bytes. The output is a *Pareto tradeoff*, never a unilateral win. If native read latency remains within noise, drop native decode-cache priority. If bytes/CPU trade cannot justify cached ownership under stale-source or in-place-mutation semantics, preserve as a design caution rather than cache implementation. A hypothetical one-decode cache is NOT implemented or credited.

## Stronger verification and falsifiers

Compare exact same source and logical output; demand all 256 byte identities in both archives, exact 64-byte native range result, no claimed native whole-file authentication from a partial logical read, and record Rust/Python install provenance. Include N=1 as cheap alternative explanation (C ABI overhead) and N=256 as worst cohort bound. Keep physical CODEC_RAW versus CODEC_ZSTD observable. Do not weaken the SHA/index check, runtime limits, benchmark comparator, release law, or source binding. Ubuntu evidence is Linux-only, not portability coverage.

## Decision, coordination, and scope

No native code, compression policy, format, release, production CI gate, or Discovery Engine policy mutation in this research. PR is test/evidence only and shall remain draft. Source-state `docs/discovery/STATE.json` is staleable cache and not a lock. Before late writing inspect latest source, existing #315 and relevant concurrent PRs. The cheapest next downstream action if a large native cost survives is a bounded cache-lifetime falsifier that explicitly challenges stale-source authentication, RSS growth, mutex contention and the single-read cold path; product cache implementation is not pre-authorized.

Status at preregistration: **measurement not yet executed**.

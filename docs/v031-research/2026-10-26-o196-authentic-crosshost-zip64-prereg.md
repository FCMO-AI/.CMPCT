# O196 — Single authentic 4 GiB r24 S_SPARSE archive across OSes (preregistered)

Date: 2026-10-26 UTC. Scientific scope: product interoperability **only**, unreleased O193 Reader, no release claim.
Base exact source: `392112ce859db5a7f85be593c82d1cabc1f5131f` (O193 / PR #521).
Parent O195 / PR #524 already passed genuine Ubuntu 4 GiB ZIP64 with sparse `S_SPARSE` and 4,096 extents. This question is **not** an index/optimization retry.

## Primary question / prediction — recorded before workflow or result

Can **one** Linux-built genuine 4,294,967,296-byte logical `S_SPARSE` revision-24 CMPCT archive, with 4,096 noncontiguous allocated 4-KiB regions, be transferred byte-identically to installed O193 Readers on Ubuntu, macOS and Windows and exported into valid ZIP64 on each host, with bounded range reads, identical logical member bytes, intact CRC and full logical SHA-256, without rebuilding source/archives on the receiving hosts?

Prediction: the transported r24 bytes remain SHA-identical; installed exact-source O193 Readers use bounded 1 MiB `read_range` calls and produce a ZIP64 archive with one 4 GiB member whose full decoded bytes have the producer's independently computed SHA-256. Receiver output SHA equality is a *secondary question* because ZIP timestamp/host-specific metadata could differ; it is not required for semantic success.

## Controls / semantic law

- The Linux producer creates a physically sparse 4 GiB file, verifies actual physical extent count and that allocated bytes are at most 64 MiB, builds using real installed Builder, verifies output `S_SPARSE`, saves original archive, source SHA and source Git identity. A small-file or coerced declared-size substitute is **inadmissible**.
- Consumers download **exactly that same archive**, verify its SHA-256, independently install the same source HEAD, and authenticate installed modules against checked-out source with CRLF normalization; only the producer runs Builder.
- Each consumer exports ZIP using the real `CMPCT.export_zip` API, independently decodes/CRC-checks all 4,294,967,296 logical bytes through Python `zipfile`, checks SHA against the Linux producer, verifies one named member, file size, archive input immutability, and records CPU/wall/output bytes and a bounded-memory observation where available.
- Source and archive identity are independent of CI synthetic merge `GITHUB_SHA`; record checked out `git rev-parse HEAD` and `github.event.pull_request.head.sha` separately.
- Preserve negative/failure artifacts and classify infrastructure failure separately. If any OS lacks requisite ZIP64 support, capture exact exception; do **not** weaken the oracle, skip payload hashing, narrow input, drop host, or reinterpret failure as success.
- Hosted execution upper bound: each producer/consumer job 20 minutes. Local temp may host logical 4 GiB sparse and compressed ZIP (anticipated <20 MiB); avoid multiple 4 GiB logical temporary copies. No root permission or third-party dependency is required.

## Falsification / decision rule

Any input SHA mismatch, failed Reader ZIP64 extraction, incorrect ZIP64 size/CRC/whole-member SHA, oversized read_range request, or memory blow-up is a product-candidate RED (specific to the tested host). Unexpected lack of disk space, system package installation, artifact-download or runner failure is INFRA and not product failure. Success earns only **tested cross-host ZIP64 correctness**, not broad representational conformance, deterministic cross-host bytes, performance dominance or publication.

Cheaper alternative: O193 small-host matrix and O195 genuine Ubuntu >4 GiB already exist; together they **do not establish** genuine macOS/Windows >4 GiB. Reuse O195 generator/independent hash shape, O193 source and installed package, rather than implement any new Reader. Any decoder or ZIP64 issue must be routed to O193 owner. Avoid modification of `docs/discovery/STATE.json` without decision-changing frontier truth.

## Audit scope / expected receipt

Files: `research/o196_authentic_crosshost_zip64.py`, `.github/workflows/v031-o196-authentic-crosshost-zip64.yml`, this prereg and a result dossier. GitHub Actions producer job + 3 platform consumer jobs. Persist per-platform full JSON even on error; report exact-source head and individual job status. O193 source is the only product owner; O196 is independent evidence.

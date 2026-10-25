# O91 result — real installed Builder destination lifetime after preflight

**Date:** 2026-10-25 UTC. **Category:** reproducible negative product behavior under controlled POSIX race; **not** a fixed product or release. **Initial O90 source:** `1beb733da61da8e1c562e7c3190b1f18f1cc45d1`. **Actual installed Builder Git blob:** `bfb37fcd06e6ff05742606ece365348150f477fc`. **O91 preregistration:** `8f7765b4fee6140659958c47f95db42d33bfe4c5`, blob `6fb50e2c0559574ea04399e215724d67185316dd`.

## Primary question and prospective disproof

Can the O90 static `os.stat(out)` output-kind admission, which fixes an existing FIFO under an ordinary stable path, retain safe destination identity when an **independent actor swaps a previously regular output name after actual Builder scan** but before final path-based `Path.write_bytes`? Preregistered disproof: an actual installed Builder refusing or safely writing despite the pivot; a missed actor barrier or bad stable regular control would invalidate the case.

## Exact-host run, product provenance and raw results

**Reproducible hosted run:** [O91 Actions #40209092155](https://github.com/FCMO-AI/.CMPCT/actions/runs/40209092155) on source HEAD `e28eea8a1dfde0a481c3dcdaa27a26592e6d3d68` (workflow-only JUnit accounting repair atop the initial instrument). The workflow installed `cmpct` outside the checkout and independently computed the installed source's Git blob with `hashlib.sha1(b"blob <length>\\0" + bytes)`; both hosts matched the exact O90 product blob above.

| Host | Genuine test cases | PASS | SKIP | FAIL / ERROR | Conclusion |
| --- | ---: | ---: | ---: | ---: | --- |
| Ubuntu 24.04 | 3 | 3 | 0 | 0 | SUCCESS |
| macOS 14 | 3 | 3 | 0 | 0 | SUCCESS |

**Artifact custody:**
- Ubuntu: artifact [12604728722](https://github.com/FCMO-AI/.CMPCT/actions/runs/40209092155/artifacts/12604728722), SHA256 `f0e436d098418263de53a28697b5a3a92919a92714d6997f9c440a2ef5e4efb1`.
- macOS: artifact [12605033134](https://github.com/FCMO-AI/.CMPCT/actions/runs/40209092155/artifacts/12605033134), SHA256 `a4c9085a75e16104080bfb037ddf9a28d630c1be9da054e88fc425b5033241a0`.

**Case 1 — genuine unaffected control:** ordinary existing external regular output succeeds, `CMPCT.verify()` and `CMPCT.read()` reconstruct the original 4 KiB source, and its source bytes are preserved. Marker `O91_REGULAR_OUTPUT_CONTROL=PASS` on both hosts.

**Case 2 — source mutation with reported build success:** after the unchanged real `Builder.scan()` completed, a separate synchronized actor atomically replaced the initially ordinary external output with a symlink to a source file that has **one physical hardlink**. Final `Path.write_bytes` followed the new symlink and changed the original source bytes, yet the Builder **returned success** and the CMPCT now stored *inside* that source leaf verified/reconstructed the original content. Markers `O91_SOURCE_CLOBBER_AFTER_ADMISSION=CONFIRMED` on Ubuntu and macOS. The output/symlink and both original/changed bytes were checked by real filesystem I/O, not simulated implementation.

**Case 3 — FIFO availability regression after admission:** the same synchronized postscan boundary replaced the output name with a genuine unconnected POSIX FIFO. The installed Builder child exceeded **7 seconds** with its verified marker `FIFO_SWAPPED` present, and the parent kept the source bytes intact. Marker `O91_POST_ADMISSION_FIFO_TIMEOUT_GT_7S=CONFIRMED` on both hosts. This proves a >7s timeout, **not** universal indefinite hanging.

## Initial infrastructure/evaluator failure, preserved rather than hidden

The first executed test source at HEAD `3837235154004d20f7153c393ff0b19586ef2f7c`, Actions [#40208875092](https://github.com/FCMO-AI/.CMPCT/actions/runs/40208875092), ran all 3 tests successfully on both hosts but the **independent JUnit audit failed** due a mistake in its own arithmetic: it included the already-computed `total` in the failure/error/skip sum when calculating passed counts. The fixed workflow at `e28eea8a1dfde0a481c3dcdaa27a26592e6d3d68` computes passes as `total - (failure + error + skipped)`; no adversarial test or acceptance count was relaxed, and the complete repeated real jobs above passed. CI results for a future documentation-only HEAD require separate exact-head reconciliation.

## Interpretation and boundary

**Scientific decision changed:** O90's useful static mitigation does not establish ownership of the object ultimately written under concurrent pathname replacement. On measured Linux/macOS, this can be more severe than availability debt: it can **silently mutate one-link source data while returning a successful verified archive.** Source collision refusal implemented by O81/O84 protects the inode observed **before** scan; it cannot cover a new symlink introduced **after** that observation by itself.

This is an adversarial synchronized filesystem actor, not a claim of spontaneous benign-workload corruption. Postscan wrapping invokes original scan but creates a deterministic adversarial schedule; the product source itself is unmodified. Windows, hostile mount/filesystem semantics, recovery after power loss, exact durability, complete size/CPU/RSS/I-O economics and official performance **remain unmeasured**. No general release promise of race-free output publication is assumed, but future promotion must clearly state and test its threat model.

## Stronger controls and next lowest-cost decisive action

O87 [#445](https://github.com/FCMO-AI/.CMPCT/pull/445) confirmed *pre-existing* FIFO block. O90 [#448](https://github.com/FCMO-AI/.CMPCT/pull/448) fixes the static type mistake in its own three-host installed test scope and preserves symlink-to-regular functionality. O75 staged publication [#432](https://github.com/FCMO-AI/.CMPCT/pull/432) must not be assumed a free replacement: O78 [#435](https://github.com/FCMO-AI/.CMPCT/pull/435) recorded inode, xattr, symlink and hardlink destination changes. **Highest-value next work:** legitimate Builder/output owner chooses a bounded physical descriptor / pathname publication contract compatible with required existing-destination identity and fallback semantics, and repeats the exact O91 adversarial tests plus O78. A static repeated pathname predicate is not proof of safe lifetime under adversarial races.

**No product files, historical source, release metadata, format revision, frozen comparators, evaluator thresholds or other owners' branches were modified.** Discovery policy unchanged; detailed evidence lives here and in immutable Actions/artifacts, with `STATE.json` intentionally not written from this independent episode.

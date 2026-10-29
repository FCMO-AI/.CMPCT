# J24I22 — bounded FD relay: observed lower-rung and first hosted findings (2026-10-29 UTC)

**Decision so far:** `BOUNDED_PHYSICAL_RELAY_RESOURCE_ORACLE_SUPPORTED`, **not product, release, immutable-source or safe-publication credit**. Scientific preregistration frozen at `001c122abd10eb0a95a52ee8d5c2028189f21cb2` before source changes. Original #742 PR head `eb4de9b65417987fdf69975237431b5473877e30`; parent J24I18b is the unmodified byte-exact reference.

## Original physical same-source court

Eight existing #723 original r24 sources from the preserved J24I18 physical bundle were transformed offline by J24I22 and by the unchanged independent old J24I18b full-buffer reference. **8/8 relay outputs were byte-identical to the old method**, not 8 different compaction wins. Seven no-op sources retained their source length; genuine committed journal source `delta-update-source.cmpct` 1,382 B reduced to **1,176 B** (206-B removal); resulting SHA-256 `9e95d3c3ca00d7a2ca71a486c94e2a004903e5fa2f174118537e86b75c0b17ea`. The eight input cases include file, symlink targets (safe/absolute/parent-relative), hardlinks, sparse and xattrs; this demonstrates only a bounded subset and independent same-wire identity.

The local audit receipt JSON SHA-256 is `696daf46e2765aefe9460f6faf7f610dd6b304b0ce85d590d0539cdc49b637dc`. Original physical test input archive identities remain in #742 J24I18 evidence. The J24I22 GitHub workflow does not yet execute these eight original artifacts and needs a future hosted independent fixture court for broader claims.

## First installed CI result and honest negative

PR #746 initial HEAD `6f88cfa1a4a60aff6759dfcef033e5b43e7a96a2`, [Actions #40845251516](https://github.com/FCMO-AI/.CMPCT/actions/runs/40845251516) **FAILURE** (3/4 tests PASS). Inherited unchanged J24I18 actual Builder/Reader suite PASS. The three passing J24I22 tests cover:
- mutation after index admission rejected and no output published; symlink final-source refusal; truncated-footer refusal;
- independent RAW/Zstd/Deflate r24 positive/hostile physical vectors, exact output byte identity and altered payload refusal;
- real controlled large probe: 64MiB random RAW source/output 67,109,424 B, SHA-256 `d360a2c026818cc82d53c7724749f4c479fb1da6b9f720f3ab414b04b1bdccdc`, child pre-RSS 18,584 KiB, VmHWM 19,308 KiB (**+724 KiB**); 128MiB logical Zstd source/output 4,676 B, child 18,752 → 23,776 KiB (**+5,024 KiB**); 128MiB logical Deflate source/output 131,036 B, child 18,764 → 19,692 KiB (**+928 KiB**). Both 128MiB cases are highly compressible zeros, not 128MiB physical sources. Resource court is Linux runner/installed *research helper*, not full CMPCT product. The source triple-read export remains accounted, not a speed claim.

Fourth installed test `test_real_installed_builder_journal` failed on an instrument error: the test updated the regular owner of a preserved hardlink alias, so that blob remained reachable, contradicting its own expectation `dead>0`. The live-blob reachability rule properly retained the alias's owner. The fixture was corrected on follow-on commit by adding a distinct regular obsolete file and updating that file; it retains the hardlink to test topology. **No product criterion, comparator, threshold or Reader behavior was changed.** The follow-on CI must prove the repaired test; do not retroactively green the first run.

## Additional negatives and costs

A first Zstd streaming implementation allocated a new ctypes output buffer per decoded chunk; local 128MiB zero stream produced ~71MiB incremental peak despite 64KiB chunk size. Using one reusable native output buffer reduced local increment to ~4.6MiB, and hosted first court independently measured +5,024KiB. Thus streaming chunk sizes alone are insufficient memory proof. The helper hashes the full physical source twice plus decodes/authenticates record bytes; the 64MiB RAW court conservatively reports **268,437,200 bytes** of physical read workload, ~4x source, though only one copy is stored. This is exported I/O cost and no measured product superiority.

Security limitations: `O_NOFOLLOW` protects only the final source path component; FD does not make bytes immutable nor pin ancestors. Concurrent writers may modify content between checks; `NamedTemporaryFile` + pathname `replace` is not secure against hostile destination-stage races. Full journal rollback semantics, alternate codecs, complex recipes, Windows/macOS, recovery, topology and release benchmarks unproved. The existing #741/#745 owner remains responsible for secure publication and #620 for signed sparse hardlink Reader proof; no code or policy changes to either.

## Follow-on current status

- Initial topology [#40845251492](https://github.com/FCMO-AI/.CMPCT/actions/runs/40845251492) FAILED because workflow lacked `# ci-lane` annotation; added `# ci-lane: deep`.
- Initial Engineering Evidence [#40845251381](https://github.com/FCMO-AI/.CMPCT/actions/runs/40845251381) FAILED because PR dossier lacked exact `Evidence` and `Losses, ambiguity and negative evidence` headings; fixed PR metadata, not evaluators.
- Exact-head follow-on workflows and independent artifacts require fresh verification before green claims.

**Counterfactual:** a fixture with an independently obsolete file, not a live hardlink owner, would have prevented the first hosted negative; the failure confirmed the reachability distinction. Repeated-FFI-buffer memory retention is a separate transferable measurement lesson. No normative discovery-policy update earned. Discovery `STATE.json` remains unchanged and staleable.

**Next cheapest decisive action:** verify the amended HEAD hosted installed journal court, preserve raw physical exactness and the 64/128MiB resource receipts; if surviving, test hostile source concurrent mutation and architecture with truly immutable snapshot plus stage-dirfd ownership before any production integration. No merge or version promotion.
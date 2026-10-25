# O117 — real installed Windows case-alias extraction result

**Date**: 2026-10-25 UTC. **Decision**: `SILENT_HOST_NAMESPACE_FIDELITY_LOSS_CONFIRMED`, scoped to case-insensitive Windows destination filesystems and the current installed Python Reader. **Product promotion**: none. **Issue**: #467. **PR**: #466.

## Authority, source and scientific controls

- Baseline: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. No Python/Rust product modifications.
- Frozen preregistration: `docs/v031-research/2026-10-25-o117-win32-casefold-extract-prereg.md`, commit `eda578541259a1429e69f084ffa7e39ebfb3e410`, **before** writing the instrument or running the court.
- Builder Git blob: `663ef0922992b1fbb8f19e6eea88d55c10a56044`; Reader Git blob: `e716233403dabd0966863c45635e18fa5ac6afb8`; FORMAT blob `19d3e687f62f5a6a95942022da7212eb074f8d53`. Those blobs are unchanged from the candidate base.
- Instrument: `tools/research/o117_casefold_extraction.py`. Workflow: `.github/workflows/v031-o117-host-case-extraction.yml`.
- Hosted three-job scientific court: [GitHub Actions #40232701373](https://github.com/FCMO-AI/.CMPCT/actions/runs/40232701373) at instrument HEAD `beacce82b9c2202f8c1fe69e2ebf63af37bbee1e`, status **SUCCESS for producer, Linux consumer, Windows consumer**.
- Both consumers use the **identical immutable uploaded Linux-built CMPCT archive**. The scientific court authenticates SHA-256 and the exact installed Reader before comparing physical extraction.

## Authentic corpus and input identity

Three files are independently representable and byte-distinct on Ubuntu:

| Logical name | Original bytes | SHA-256 |
| --- | ---: | --- |
| `Report.txt` | 1,974 | `7db3beaf93286bab2b9eff505e7b774a846b12512805c2c9e65f43783ee41f02` |
| `report.txt` | 2,226 | `845421693b4a1f1f066e06090718a6850b5cd9b3e1cf917172fb95a68e91f45e` |
| `other.txt` | 812 | `dc64035d15fe93c3f53b64e23eeb6abaa13243d9ec03117e19a0b547a1d037f6` |

**Complete source**: 3 logical files, 5,012 source bytes.

**Complete archive**: 1,126 bytes, SHA-256 `9ca1e8ea06f297637d27ba856a07950aafaf4ecdb216985d1d71106294e78a5a`.

The authentic installed Linux Builder produced the archive and Reader verified all three exact logical members. The installed Windows Reader independently verified/read all three exact logical members before extraction, proving the original compressed data is not the culprit.

## Direct same-artifact extraction results

| Observable | Ubuntu 24.04 | Windows 2025 |
| --- | --- | --- |
| Archive SHA-256 agrees with producer | YES | YES |
| Native installed Reader recognizes and verifies all three members | PASS | PASS |
| Destination case-alias probe | False (distinct paths) | True (same physical path) |
| `extractall(..., metadata=False)` raised | NO | **NO** |
| Physical regular files created | 3 | **2** |
| `Report.txt` member payload preserved on filesystem | YES | **NO** |
| `report.txt` member payload preserved on filesystem | YES | YES |
| `other.txt` independent control preserved | YES | YES |
| `Report.txt` and `report.txt` same physical object | NO | **YES** |
| Final physical source-tree fidelity | PASS | **FAIL** |

**Direct causal observation**: the two Windows destination paths resolve to the same physical object, with SHA-256 `845421693b4a1f1f066e06090718a6850b5cd9b3e1cf917172fb95a68e91f45e` (the lower-case member). The different 1,974-byte original member is not available as an independently named physical file. The physical inventory is `Report.txt`, `other.txt`, though `Report.txt` contains the lower-case member's bytes. `extractall` returned normally. No data-origin ambiguity, no synthetic index or mocked filesystem was involved.

The three green scientific jobs mean the **experiment ran and exposed the defect**. They emphatically do **not** certify safe extraction on Windows.

## Raw evidence custody

- Linux-built immutable archive and manifest: artifact **12613408940**.
- Producer receipt: artifact **12613962346**.
- Ubuntu installed-Reader control: artifact **12614020132**.
- Windows installed-Reader hostile observation: artifact **12613718738**.
- Raw evidence includes `result.json`, consumer job SHA, Reader Git blob, host-case probe, complete output inventory, member SHA-256 and stdout court log. Original run and jobs remain at https://github.com/FCMO-AI/.CMPCT/actions/runs/40232701373.

## Initial instrument negative / repair

First attempt `40232588369` failed *before building any archive* because the scientific script imported `Builder` from the package root instead of `cmpct.builder`. Commit `beacce82b9c2202f8c1fe69e2ebf63af37bbee1e` corrected the instrument import only, preserving preregistered pairs, payloads, expected observations and all product code. A new full hosted run `40232701373` yielded complete three-platform-job scientific evidence. This initial infrastructure failure is not product loss and is not hidden.

## Scope, alternative explanations, negative/self-critique

Microsoft documents that NTFS generally exposes case-insensitive names by default but can enable case-sensitive directories. The instrument **measures actual host aliasing**, avoiding a universal platform assumption. Only ASCII case collisions in a newly created test destination were tested. No Unicode normalization, Windows reserved/device names, nested directory merges, WSL case-sensitive output, NTFS reparse points, existing-output overwrite, symlink TOCTOU or concurrent mutation were assessed. The independent `other.txt` control excludes an across-the-board failed extraction.

No archive-size gain, compression claim, memory budget, performance measurement, recovery claim, or release signal follows from this work.

**Mechanism**: logical paths are distinct under the host-neutral `canonical_logical_path`, but the target filesystem's name-equivalence relation identifies the output names. `CMPCT.verify()` validates compressed/logical content, not the physical output tree's distinctness. The defect is silent because output path aliasing is not detected before writing.

## Decision and next cheapest executable action

Open engineering debt: [issue #467](https://github.com/FCMO-AI/.CMPCT/issues/467). Product contract should **fail closed before destination mutation** if two archive entries cannot both be represented as distinct physical host paths. The most valuable next falsifier is a host-aware preflight comparing the archive's ancestor/name graph to actual destination-namespace equivalence (including per-directory Windows case-sensitive setting), with a strict Linux distinct-case control. Blind lowercasing would be unsafe and reject legal case-sensitive trees. The product must preserve exact original filenames/contents, or explicitly reject the incompatible destination.

Counterfactual: the existing `docs/HARDENING.md` noted host-specific path equivalence as unimplemented; a same-archive, two-host physical extraction oracle was the cheapest prospective discriminator that converted a lexical-risk caveat into an exact installed-product defect. No research-policy change is justified from this single mechanism. `docs/discovery/STATE.json` remains owned elsewhere and was not altered.

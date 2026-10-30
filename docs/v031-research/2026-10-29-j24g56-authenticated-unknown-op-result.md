# J24G56 result — digest-consistent unsupported r24 journal opcode silently ignored by Python Reader

Date: 2026-10-29 / 2026-10-30 UTC. Status: **negative finding confirmed in unmerged v0.31 candidate; no product fix, merge, version or release**.
Prereg: `9c1cc45f6fde408540d807354bf78d925d6d4e18`, committed before any test/CI instrumentation.
Product parent: #789 `83e9f2eb277f023186b646f667cd443b7108f268`.
Test-and-referee source head: `01a5acc04ea376a3d38f345479630e11b42bf323`.
Published control: `main@80c358f8824ec1b20d349c92ed94c898090969b0` (v0.30.0, revision 24) **not independently installed/tested for this case**.
Issue: https://github.com/FCMO-AI/.CMPCT/issues/792
Research PR: https://github.com/FCMO-AI/.CMPCT/pull/791
Hosted result: https://github.com/FCMO-AI/.CMPCT/actions/runs/40979665726

## Question and baseline
Can an unsupported transaction operation that is structurally legitimate at the footer/sha256 level be selected as the newest revision-24 generation by `CMPCT` Reader and strong `verify()`, while `preflight_archive()` rejects its semantics? The shared replay helper used by Reader has handlers for `put/del/ren` without a rejecting final branch. `validation._apply_delta` rejects unknown tags before delegating, which predicts disagreement.

The word "signed" in some older research documents is **only shorthand for a self-hashed and committed journal generation**. These bytes are **not origin-authenticated by a secret or digital signature**; this experiment never claims otherwise.

## Falsifiable prediction and stronger controls
Builder created the original revision-24 archive with two ordinary files. `transactions._append_generation` added a fully digest-consistent operation payload with a real footer pointing at the initial committed footer. The test asserted exact newest-footer selection (not recovery), both Reader file bytes and strong verify member count, and preflight's conclusion. The independent referee, which imports no CMPCT modules, used plain `struct`, `hashlib`, MessagePack and external Zstandard to authenticate both base index and committed delta, operation bytes and artifacts. Valid `del` and corrupt-digest recovery are opposed controls.

## Direct results
| Delta op payload | Reader selected committed footer? | Reader strong verify | Preflight | Decision |
|---|---|---|---|---|
| `[['del','a.bin']]` | Yes | 1 member | Accept, 1 member | valid control |
| `[['future_op','z.bin']]` | Yes | 2 unchanged members | **Reject** | unknown op silently skipped |
| `[['future_op','z.bin'],['del','a.bin']]` | Yes | 1 member | **Reject** | partial program applied |
| `[['del','a.bin'],['future_op','z.bin']]` | Yes | 1 member | **Reject** | partial program applied |
| altered latest-footer SHA | No: prior footer selected | 2 old members | prior footer accepted | expected recovery control |

Hosted [run #40979665726](https://github.com/FCMO-AI/.CMPCT/actions/runs/40979665726): Ubuntu 24.04 **5/5 PASS**, macOS 14 **5/5 PASS**, Windows 2022 **5/5 PASS**. Installed Python sources were byte-identical to the checked-out `reader.py`, `validation.py`, `journal_replay.py` and `transactions.py` on every host; both consumers bound to the same Python shared-replay function. The independent wire court passed for all five physical specimens and rejected 9/9 tampered input controls per host (27/27 total). Green research CI means a **verified negative product finding**, not repair.

Original physical sample, separate SHA/case receipt, stdout and JUnit per host:
- [Ubuntu artifact 12944267412](https://github.com/FCMO-AI/.CMPCT/actions/runs/40979665726/artifacts/12944267412); provider ZIP SHA-256 `a683f28d2028d51db0f7512c0d400f0469fb865e4596dafb019fd5e7820c02bf`.
- [macOS artifact 12944810017](https://github.com/FCMO-AI/.CMPCT/actions/runs/40979665726/artifacts/12944810017); provider ZIP SHA-256 `9c9373ae211be260551bcc2f2816c2f50881afcef6a9d0dcb163791a831e58cf`.
- [Windows artifact 12944196875](https://github.com/FCMO-AI/.CMPCT/actions/runs/40979665726/artifacts/12944196875); provider ZIP SHA-256 `6d19be602b5e7c6572d8fd508061858d703a0d315c7871418c9fdf9ecbbd7b68`.
These are provider-reported checksums; the ZIPs were **not** independently re-downloaded and rehashed by this activation.

## Causal inference, disproof and negative limits
The independent formats confirm valid digest-consistent unknown-op generation, not a corrupt or unfinished append. Reader selects that generation and skips the unrecognized instruction; preflight refuses it. The alternative explanation that Reader had simply recovered the preceding footer is eliminated by exact footer-offset assertions. The stronger mixed-op control demonstrates partial execution instead of merely an empty no-op. Falsification criteria from prereg were met for the predicted mismatch, not its disproof.

**Important negative boundaries:** An unknown operation is intentionally authored via a low-level Writer helper, not emitted by a normal Builder/ordinary transaction workflow. No corruption of existing logical payload bytes was observed, no digital-signature forgery or malicious origin bypass was shown, and no separate published wheel, Rust native reader, privileged metadata, RSS/CPU, large indexes, 64th-checkpoint behavior, full recovery/power-loss or external performance matrix was measured.

## Owner coordination, economy and next executable target
#789 is the owner of `src/cmpct/journal_replay.py` and shared Reader/preflight semantics; this research child modified **zero product files** and has notified the parent via comment. An acceptance patch should make unsupported op tags fail closed at the common semantic owner, preserving valid `put/del/ren`, historical r24 layouts, bounded syntax/resource limits, and corrupt/incomplete footer recovery. Preserve the original negative court as historical evidence; add a separate now-positive acceptance test rather than erasing the negative observation.

PARETOBONK: A cheap source reading identified the gap, but could not prove the real footer-selection and recovery API behavior. Five synthetic physical cases and one independent wire oracle were sufficient; a full product benchmark would add no decision value for this fork. Cheapest next work belongs to the #789 owner.

Counterfactual: the missing final `else: raise` is a prospectively recognizable static risk. The shortest useful future screen is to compare every authoritative validator's accepted opcode vocabulary with every operational replay switch before constructing costly physical fixtures. This is a **single local lesson**, not evidence for a global Discovery Engine policy mutation.

## Exact-head/general CI disclosure
The specialized installed-court source head `01a5acc...` completed successfully in all three OS jobs. General Tests, Native Core and other workflows are **independent** and cannot be declared green based on this result. Engineering Evidence initially failed because this research PR lacked mandatory dossier headings, not due to product mismatch; the PR description was corrected after that run without editing the checker. A new code/document commit is necessary to execute the revised dossier on the final HEAD. Never suppress or weaken CI to promote this research.

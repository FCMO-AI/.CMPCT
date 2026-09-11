# v0.30 R4 hidden-ZIP shared-byte break-even ladder

**Status:** STABLE CAUSAL CURVE / ZERO-THRESHOLD ADMISSION FALSIFIED  
**Exact source:** `d500990d000259cf665ff137857e79c80cdae58a`  
**Hosted run/job:** `34641246980` / `103401187269` — SUCCESS  
**Artifact:** `10280182148`, digest `sha256:b62d964eddd305c91405a4bc84322c33718b63d22ada5eda3696fcdd7ce15f49`  
**Shipping/release credit:** none

## Question

The per-container V2 content-ZIP gate correctly removed zero-length false signals and unrelated passengers, but `shared_positive_bytes > 0` remained deliberately underfit. A hostile pair of ~512 KiB hidden ZIPs sharing exactly one byte proved that any-positive admission can increase complete archive bytes.

This ladder measures mechanism economics rather than selecting a threshold. Each case contains two hidden ZIPs with one exact shared member of controlled size plus one independent 512 KiB high-entropy member per container. The ordinary Builder is compared with the research ContentZipBuilder. The central-directory-visible compressed size of the shared member is recorded before recipe construction.

## Result

| Shared logical bytes | Repeated compressed bytes visible in CD | Net archive saving | Extra create CPU |
|---:|---:|---:|---:|
| 1 | 3 | **-495 B** | +0.0908 s |
| 16 | 19 | **-470 B** | +0.1004 s |
| 64 | 69 | **-432 B** | +0.1013 s |
| 256 | 261 | **-260 B** | +0.1015 s |
| 1,024 | 1,029 | **+512 B** | +0.1013 s |
| 4,096 | 4,101 | **+3,679 B** | +0.1019 s |
| 16,384 | 16,389 | **+15,983 B** | +0.1025 s |
| 65,536 | 65,556 | **+65,106 B** | +0.1118 s |
| 262,144 | 262,224 | **+261,687 B** | +0.1499 s |

Net saving is monotonic over the tested ladder. The first tested byte-positive point is 1,024 shared logical bytes / 1,029 repeated compressed bytes.

More importantly, the implied representation/control overhead is remarkably stable:

`observable repeated compressed bytes - complete archive saving = 406..537 B`

across the entire 1 B → 256 KiB ladder.

This explains the prior one-byte hostile causally rather than by workload-specific tuning: the existing S_VZIP representation has a roughly half-kilobyte incremental control/recipe/index cost for this two-container shape, so tiny shared streams cannot repay the representation.

## What this does and does not justify

The ladder does **not** justify hardcoding `1024` as a magic admission threshold. That would confuse the first tested positive point with a general law.

It does justify the next hypothesis:

> admission should be based on predicted information yield using central-directory-visible duplicate compressed-stream bytes minus a conservative representation/control cost envelope, not on mere presence of shared logical bytes.

A conservative first research envelope can be derived from structure plus safety margin rather than fitted to Office: take the worst measured incremental overhead (`537 B`) and require predicted reusable compressed bytes to exceed a multiple of that cost before paying full recipe proof. The multiplier must be preregistered as a risk/compute margin and then falsified on the frozen 15, Office, Analytics, the tiny-positive controls, and non-identical-compression cases. It must not be tuned until each workload passes.

The CPU curve also matters: full recipe construction costs roughly 0.10 s even when only a few shared bytes exist. Therefore the opportunity gate should run before full recipe proof and should charge both expected bytes and proof CPU, consistent with the campaign's marginal-information-yield law.

## Decision

Preserve the ladder as causal evidence. `shared_positive_bytes > 0` is not promotion-worthy. Advance to an information-yield admission falsifier driven by bounded central-directory observation, with exact recipe/tree/range proof retained after admission. No shipping Builder change receives credit yet.

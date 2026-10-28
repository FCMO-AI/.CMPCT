<div align="center">
  <a href="https://fcmo-ai.github.io/.CMPCT/?lang=ko"><img src="../../.github/assets/repository-hero.svg" width="100%" alt="CMPCT — 기존 아카이브 형식은 타협과 화해했다. CMPCT는 그러지 않았다."></a>

  **저장 바이트, 선택적 접근, 무결성, 복구, 이식성을 함께 발전시키도록 설계된 범용 무손실 아카이브/컨테이너 프로젝트.**

  **[웹사이트](https://fcmo-ai.github.io/.CMPCT/?lang=ko)** · **[브라우저 랩](https://fcmo-ai.github.io/.CMPCT/?lang=ko#lab)** · **[벤치마크](../BENCHMARKS.md)** · **[형식](../FORMAT.md)** · **[로드맵](../ROADMAP.md)** · **[에이전트 시작점](../CURRENT_STATE.md)**

  <sub>core v0.29.0 · 정규 형식 r24 · surface 0.29.k · pre-1.0</sub>
</div>

> **큐레이션 번역.** 이 문서는 사람용 README의 의미를 보존한 버전 관리 번역입니다. 영어 [`README.md`](../../README.md)가 계속 정규 권한을 가집니다. 수치, 경로, 형식 이름, 증거 범위는 의도적으로 유지합니다. 실제 이중언어 인간 검토가 이루어지기 전에는 “인간 검토 완료”라고 표시하지 않습니다.

---

> **성능은 릴리스 계약이다.** 연구는 불편한 트레이드오프를 발견할 수 있다. 승격되는 릴리스는 그것을 숨길 수 없다. 결정론적 아카이브 크기 회귀 허용치는 **0바이트**, 동일 Runner의 문서화된 노이즈 범위를 벗어난 확인된 속도 저하는 승격을 막으며, 패배한 workload도 공개 증거로 남는다.

## CMPCT가 존재하는 이유

| | CMPCT가 개선하려는 것 |
|---|---|
| **저장 바이트** | 각 파일을 독립된 바이트 스트림으로 보지 않고 정확한 동일성, 콘텐츠 인식 표현, 제한된 관계 재사용을 활용한다. |
| **선택적 접근** | 전체 아카이브를 반드시 풀지 않고 요청된 객체나 범위를 읽는다. |
| **무결성 + 복구** | 검사, 중복 메타데이터, salvage 경로를 disaster-recovery 문구가 아닌 실제 reader 동작으로 만든다. |
| **파일시스템 충실도** | 링크, sparse files, 메타데이터, 현대적인 update semantics를 보존한다. |
| **상호운용성** | 정규 reader/writer 계약, ZIP export, native core, portability gate를 실험 grammar와 분리한다. |
| **증거 품질** | 공개 claim을 reproducible committed record에서 도출하고, 패배를 보존하며, benchmark theater를 거부한다. |

CMPCT는 “새 확장자를 붙인 Zstd”가 아니며, 손으로 고른 폴더 하나에서 이기는 것으로 만족하지 않는다. 목표는 **크기, 속도, random access, 충실도, 무결성, 복구, 업데이트, 현대적 storage semantics**를 함께 강화하면서 비용을 다른 곳에 조용히 떠넘기지 않는 기본 아카이브다.

## 최신 검증 프런티어

**Project v0.29.0 — Mosaic / Residual Program Packing**은 검증된 연구 엔진을 전진시키며, 출하되는 정규 형식은 **revision 24**를 유지한다.

| v0.29 연구 증거 | 결과 |
|---|---:|
| Portable inherited-frontier portfolio | **137,501,815 B** |
| Direct v0.28 base | 137,550,416 B |
| 정확한 절감 | **48,601 B (0.035333%)** |
| Portable workloads | **15** |
| 개선 / 회귀 | **2 / 0** |
| Exact v0.28 fallbacks | **13 / 15** |
| Hostile mechanism suites | **4.407362% 더 작음**, 18 workload 중 9 개선 / 0 회귀 |
| Fixed hostile scheduler | **182.454 s → 97.944 s median (-46.318%)**, 선택 아카이브 byte-identical |

결정론적 resemblance-hostile 집합(724 파일 / 93,526,384바이트)에서 승인된 시도 #5는 **47,147,764 B**를 저장한다. 같은 트리에서 ZPAQ m5 47,062,639 B, solid tar+Zstd-19 47,065,652 B, 7z/LZMA2 47,430,343 B, Borg 76,461,311 B, ZIP/Deflate-9 76,690,799 B.

이는 **동일 조건 저장 바이트 비교이며 의미론적 패리티 주장이 아니다**. solid archive, backup repository, CMPCT는 서로 다른 trade-off를 가진다. 영구 record: [`docs/releases/v0.29.0.md`](../releases/v0.29.0.md); machine-readable evidence: [`benchmarks/history/`](../../benchmarks/history/).

### 출하판 vs 연구 프런티어

| 권한 | 상태 | 의미 |
|---|---|---|
| **정규 reader/writer** | **r24** | `python -m cmpct create`가 쓰며 정규 reader가 이해해야 하는 것. |
| **연구 프런티어** | **CMPNX11 / v0.29.0** | 실험적 Mosaic + Residual Program Packing; r24 문법이 아님. |
| **공개 surface** | **0.29.k** | repo/site/docs 표현 계층이며 아카이브 의미론 권한이 없음. |
| **라이선스** | **Apache-2.0 제안 중** | 제안일 뿐 최종 공개 grant가 아님. |

## CMPCT가 현재 할 수 있는 것

정규 r24는 content-addressed deduplication, adaptive Zstandard/raw storage, Zstd dictionaries 및 micro-solid packs, content-defined chunking, 빠른 byte-range reads와 parallel decode, hardlink/symlink/sparse preservation, UID/GID/xattrs, ZIP/WHL virtualization, 이길 때의 lossless PCM-WAV, ZIP export용 raw Deflate reuse, CRC32 + SHA-256, redundant head/tail indexes, self-describing blob records, transaction append journal, on-demand ZIP export, 선택적 reproducible/deterministic parallel creation을 포함한다.

v0.29는 bounded FastCDC units, multi-band similarity search, depth-1 COPY/LITERAL deltas, multi-root Mosaic placement, Residual Program Packing, exact v0.28 fallback, locality/resource ceilings, pinned memory-safe bridge를 통한 exact DEFLATE, Merkle-authenticated records, authenticated tail recovery, strict remote range sources, byte-identical parallel scheduling도 연구한다.

이 연구 메커니즘은 format integration, conformance, hardening, native parity, recovery, portability를 각각 통과하기 전까지 정규 reader에 들어가지 않는다.

원칙: **확장자 관습이 아니라 콘텐츠로 선택한다.**

## 빠른 시작

```bash
python -m pip install -e .
python -m cmpct create ./folder archive.cmpct
python -m cmpct create ./folder reproducible.cmpct --reproducible
python -m cmpct create ./large-folder parallel.cmpct --workers 8
python -m cmpct info archive.cmpct
python -m cmpct list archive.cmpct
python -m cmpct verify archive.cmpct
python -m cmpct extract archive.cmpct ./restored
python -m cmpct range archive.cmpct path/to/huge.bin 1048576 4096 -o slice.bin
python -m cmpct export-zip archive.cmpct legacy.zip
```

fresh-process CLI는 `--workers N`이 없으면 의도적으로 serial이다. v0.28 gate는 작은 media tree에서 약 10 ms의 thread-pool startup 비용을 확인했다. in-process `Builder`는 deterministic parallel creation을 기본 유지한다.

선택적 native Linux chunker:

```bash
cc -O3 -shared -fPIC native/cmpct_cdc.c -o src/cmpct/libcmpct_cdc.so
```

reader는 이 helper에 **의존하지 않는다**. chunk 경계는 disk에 명시적으로 기록된다.

## 성능 포지션

- **크기:** 동일 input + encoder semantics로 더 큰 아카이브가 나오면 안 된다. 허용 **0바이트**.
- **create/extract:** base와 candidate를 동일 runner에서 반복 median 측정. noise envelope 밖의 확인된 slowdown은 release를 막는다.
- **evidence:** 각 숫자 core release는 새 공개 benchmark record를 commit한다.
- **corpora:** 패배/adversarial workload도 계속 공개한다.

[`docs/PERFORMANCE_RELEASE_GATE.md`](../PERFORMANCE_RELEASE_GATE.md), [`docs/BREAKTHROUGH_REHABILITATION.md`](../BREAKTHROUGH_REHABILITATION.md) 참고.

## 새 에이전트 읽기 순서

`docs/AGI_ENGINEERING_STANDARD.md` → `README.md` → `AGENTS.md` → `docs/CURRENT_STATE.md` → 최신 `docs/releases/` → `docs/PERFORMANCE_RELEASE_GATE.md` → `docs/BREAKTHROUGH_REHABILITATION.md` → `docs/FORMAT.md` → `docs/HISTORY.md` → EntropyGraph/Mosaic docs → `docs/HARDENING.md` → `docs/PORTABILITY.md` + `docs/NATIVE_CORE.md` → `docs/RESEARCH_LOG.md` → `docs/BENCHMARKS.md` + `benchmarks/history/` → `docs/PUBLIC_SURFACE.md` → `docs/ROADMAP.md`.

새 에이전트가 private chat, private corpora, unrelated project context를 필요로 하지 않아야 한다.

## Repository 지도

`src/cmpct/` = 정규 r24 reference; `experiments/` = 연구 계보; `benchmarks/` = deterministic corpora/gates + `benchmarks/history/`; `fuzz/` = parser/resource 공격; `tools/check_*` = 계약 검사; `site/` = site + Browser Lab; `native/` = accelerators/shared core; `docs/` = contracts/campaigns/history/roadmap; `tests/` = format, round-trip, similarity, locality, reproducibility regressions.

## 웹사이트

사이트는 **먼저 인상을 만들고, 다음에 claim을 증명하고, 마지막에 신뢰를 얻도록** 설계됐다. 수치, 경쟁자, workload, 패배, core status는 versioned benchmark history에서 온다. **연구 프런티어**, **정규 패리티**, **surface revision**을 엄격히 분리한다. 시각적으로 공격적일 수 있지만 승리를 꾸며낼 수는 없다.

**열기:** https://fcmo-ai.github.io/.CMPCT/?lang=ko

## 버전 규율

1. **숫자 core (`MAJOR.MINOR.PATCH`)** — 실질적 제품 개선만. v0.27.1 이후 정상 진행은 `MAJOR.MINOR`, packaging compatibility를 위해 `PATCH=0`.
2. **Surface (`MAJOR.MINOR.LETTER`)** — site/docs/repo/workflow. 현재 **`0.29.k`**.
3. **On-disk revision** — reader에 새 grammar/semantics가 필요할 때만. 정규 **r24**.

CI는 축을 분리하고 근거 없는 bump를 거부한다.

## 역사, provenance, 공개 surface

CMPCT는 Seekable-Zstd, indexed-Zstd, adaptive-framing, ZIP-family 실험에서 발전했다. 기술 역사는 보존하지만 private corpus identities, private artifacts, unrelated provenance는 공개 기록에 넣지 않는다. 공개 benchmark는 reproducible하거나 의도적으로 public/synthetic input을 사용해야 한다. 과거 결과는 **보편적 성능 보장이 아니다**.

CMPCT는 독립적으로 서야 한다. repo/site는 unrelated internal project, private customer data, private corpora, personal information, chat transcripts, credentials, private artifact names, internal links를 요구하거나 노출하면 안 된다. `docs/PUBLIC_SURFACE.md` 참고.

## 정규성

이 repository는 chat-local prototype과 benchmark script를 대체한다. 실질적 engine/archive 발전은 숫자 release를 얻고, site/docs/presentation은 `SURFACE_REVISION`, 연구는 promotion 전까지 명시적으로 experimental 상태를 유지한다. 실험 코드는 reference reader/writer와 conformance에 통합되기 전 정규 지원을 주장할 수 없다.

## 라이선스

Apache License 2.0은 **현재 제안된 라이선스**이며 최종 채택된 라이선스가 아니다. 본문: `LICENSE-APACHE-2.0-PROPOSED.txt`; adoption checklist: `LICENSING.md`. 절차가 끝날 때까지 CMPCT를 Apache-2.0으로 최종 출시됐다고 표현하면 안 된다.

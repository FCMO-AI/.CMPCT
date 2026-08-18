/* CMPCT curated Korean adaptation pack — Surface 0.29.i.
   Footnote: one physical phrase line maps to one canonical English source phrase. Model-curated,
   source-controlled, no runtime translator, and not claimed human-reviewed. */
import { phraseBlock } from "../locale-pack.js";
export const PHRASE_VALUES = phraseBlock(`
본문으로 이동
CMPCT 홈
기본 탐색
언어
성능
엔진
증거
랩
에이전트 보기
논리 공간
물리 루트
성능 프런티어 · 커밋된 벤치마크에서 직접 표시
파일을 더 잘 패키징하는 방법.
기존 아카이브 형식은 타협과 화해했다.
CMPCT는 그러지 않았다.
저장 바이트, 선택적 접근, 정확한 동일성, 무결성, 복구를 함께 전진시키고 검증된 프런티어를 후퇴시키는 릴리스를 거부하도록 설계된 무손실 아카이브 프로젝트.
수치 보기
.cmpct 만들기
어디서 지는지 보기 ↓
프로젝트
반복 횟수
Runner
기록된 환경
표면
정규 형식
Build
현재 매칭 테스트의 핵심 결과
생성 WALL TIME
ZIP / DEFLATE
7Z / LZMA2
SOLID ZSTD-19
매칭된 구조 비교
최신 커밋 벤치마크 증거 불러오는 중…
최신 커밋 벤치마크 프런티어 불러오는 중…
증거 영수증 ↓
매칭된 저장 바이트
범위가 제한된 스케줄러 결과
무손실
선택적 접근
무결성
복구
중복 제거
제한된 디코드
CMPCT 설계 우선순위
릴리스 법칙 / 01
대담하게 발견하라. 회귀 없이 승격하라.
연구는 트레이드오프를 드러낼 수 있다. 릴리스는 그것을 숨길 수 없다. 결정론적 아카이브 크기 회귀:
허용 0바이트
동일 Runner 노이즈 범위를 벗어난 확인된 속도 회귀:
릴리스 차단
성능 게이트
01 / 아레나
압축률이 아니다.
성능상의 위치다.
구조 아레나는 한 가지 좁은 질문만 묻는다. 같은 적대적 트리를 각 도구가 몇 바이트로 저장했는가? 접근, 복구, 내구성 의미론의 차이는 가짜 동등성으로 세탁하지 않고 명시한다.
저장 바이트 · 낮을수록 좋음
논리 입력
경쟁자
아카이브 크기 비교
올바르게 읽기:
solid 압축기에 원시 크기로 지더라도 더 강한 선택적 접근과 복구 의미론을 동시에 가질 수 있다. 이 사이트는 두 사실을 모두 보존한다.
카테고리 프런티어 · SOLID ZSTD-19
정확한 트리별 독립 workload 아카이브는 전체 스위트 결과를 빌리지 않고 각자의 출처를 유지한다.
정확한 트리의 카테고리 증거 불러오는 중…
RED TEAM 보드
패배는 계속 보인다
벤치마크 신뢰성은 완벽히 초록색인 대시보드가 아니라 실패를 보존하는 데서 나온다.
벤치마크 조건 불러오는 중…
증거 영수증
오픈 북
모든 헤드라인은 트리, 기록, 범위, 권한 수준을 함께 유지한다. 주장이 화려할수록 출처는 더 쉽게 검사할 수 있어야 한다.
형식
트리
파일
기록
계약
사이트 원시 데이터 ↗
에이전트 JSON ↗
LLM 안내 ↗
벤치마크 기록 ↗
02 / 왜 이길 수 있는가
아카이브는
정보 그래프로 컴파일된다.
CMPCT는 필요한 객체 사이의 정확한 관계를 찾고 물리 루트를 선택하며 결정론적 재구성 경로를 기록한다. 지역성, 무결성, 복구 비용은 명시적으로 유지한다.
개념적 정보 그래프
논리 트리
필요한 바이트
정확한 스트림
공유 구조
동일성
중복 제거된 객체
제한된 루트
선택적 디코드
인덱스 + 증명
정확한 동일성
동일한 콘텐츠는 독립적인 논리 경로를 합치지 않고 하나의 인증된 물리 루트로 수렴할 수 있다.
관계 인식 저장
필요한 객체는 파일명이 다르다는 이유만으로 중복 저장하지 않고 정확한 압축 구조를 재사용할 수 있다.
선택적 접근
유용한 바이트에 접근하는 유일한 방법을 거대한 전체 아카이브 압축 해제로 만들지 말고 요청된 객체를 읽는다.
제한된 컨텍스트
파일 간 컨텍스트를 시험하고 제한해 크기 이득이 조용히 무제한 읽기 작업을 만들지 못하게 한다.
무결성
인덱스와 물리 데이터에는 명시적 검사가 있다. 성공은 단지 “decompressor가 불평하지 않았다”가 아니다.
물리 복구
중복 인증 메타데이터는 문서 속 disaster recovery 약속이 아니라 실제 Reader 경로로 존재한다.
03 / 정규판 VS 프런티어
하나의 프로젝트.
두 개의 권한 수준.
연구 프런티어는 공격적이어도 된다. 정규 reader/writer는 상호운용성 계약이다. 아름다운 사이트라 해도 연구 표현이 정규 권한을 빌리게 해서는 안 된다.
출하 / 정규
reader / writer 계약
연구 프런티어
벤치마크 후보
공개 증거
공개
주장은 커밋된 기록에서 도출
04 / 정규 ZIP 실행 패리티
출하 CMPCT vs ZIP.
크기, 생성, 추출.
정규 reader/writer의 라이브러리 경계와 새 CLI 프로세스 경계에서의 운영 패리티. 연구 저장 프런티어와 의도적으로 분리한다.
커밋된 기록
코퍼스
아카이브 크기
라이브러리 생성
라이브러리 추출
CLI 생성
CLI 추출
05 / 브라우저 랩
읽기는 여기까지.
하나 만들어라.
포터블 writer는 이 장치에서 실행된다. 파일은 업로드하지 않는다. 보수적인 정규 하위 집합만 출력하며 형식 개정 뒤 추측하느니 스스로 비활성화한다.
정규 호환성 확인 중…
writer는 repository 형식 개정에 맞춰 스스로 게이트한다.
생성
포터블 CMPCT writer
로컬
여기에 파일을 놓거나 파일 선택
파일 또는 폴더 놓기
데이터를 업로드하지 않고 바이트 단위로 정확한 아카이브를 만든다.
파일 선택
폴더 선택
선택된 파일 없음.
.cmpct 만들기
포터블 모드는 일반 파일, 경로 인덱싱, 정확한 콘텐츠 중복 제거, SHA-256/CRC32, RAW/Deflate 저장을 보존한다. 전체 파일시스템 의미론은 CLI 영역이다.
검사
헤더 렌즈
업로드 없음
로컬 CMPCT 아카이브의 고정 헤더만 읽는다. 전체 구조 검증은 정규 reader와 native core가 담당한다.
.cmpct 파일 선택
Magic
버전 필드
기본 인덱스
데이터 범위
06 / 릴리스 궤적
코어 릴리스는
번호를 벌어야 한다.
숫자 릴리스는 CMPCT 자체가 실질적으로 개선될 때만 올라간다. 표면 개정은 아카이브 엔진이 바뀐 척하지 않고도 훨씬 더 아름다워질 수 있다.
07 / 엔지니어링 핸드오프
겉은 아름답게.
끝까지 검사 가능하게.
사람에게 CMPCT를 읽기 쉽게 만드는 같은 표면이 에이전트에는 기계 판독 상태와 지속 가능한 엔지니어링 증거를 제공한다.
기계 판독 프로젝트 안내
공개 증거와 릴리스 상태
에이전트 읽기 순서와 권한 경계
Repository
Repository ↗
형식, 벤치마크, 구현
성능은 스크린샷이 아니다. 릴리스 계약이다.
형식 ↗
벤치마크 ↗
Pre-1.0 · 라이선스 제안은 아직 채택되지 않음 · 커밋된 벤치마크 증거는 기록된 환경과 의미론의 조건을 계속 따른다.
CMPNX11은 연구 전용이며 정규 r24 reader로 읽을 수 없다.
v0.28 대비 포터블 크기 이득은 작고(48,601 B / 0.035333%) 15개 workload 중 2개에 집중된다. 13개 workload는 의도적으로 정확히 폴백한다.
수정된 scheduling 이전, 승인된 시도 5 포터블 포트폴리오는 v0.28 생성 시간의 2.175x를 사용했다. scheduler 속도 주장은 측정된 고정 적대적 집합에만 적용된다.
매칭된 적대적 구조 집합에서 시도 #5는 7z/LZMA2보다 작지만 solid tar/Zstd-19보다 82,112 B, ZPAQ m5보다 85,125 B 더 크다.
solid 아카이브 경쟁자는 선택 읽기/복구 의미론이 다르다. 이 행은 저장 바이트를 비교하며 기능 패리티를 주장하지 않는다.
CMPCT는 아카이브에 links/sparse/uid-gid/xattrs를 보존한다. 이 Python ZIP baseline은 symlink를 역참조하며 더 풍부한 파일시스템 의미론을 보존하지 않는다.
승인된 v0.29 연구 프런티어; 정규 r24 변경 없음
결정론적 724파일 유사성 적대 트리 하나; 동일 run의 전체 트리 아카이브 크기; solid 아카이브와 의미론 차이는 계속 명시
매칭된 커밋 벤치마크
연구 프런티어
CMPCT 연구 프런티어
연구 벤치마크 후보
연구 프런티어에 사용 가능한 커밋 벤치마크가 없습니다.
기록:
commit:
작은 파일
소스
미디어
바이너리
중복 제거와 링크
sparse
중첩
통합
개발 repository
오피스 워크스페이스
미디어 라이브러리
analytics와 데이터베이스
로그와 텔레메트리
증분 백업
압축 불가 및 암호화 유사
많은 작은 파일
ML 아티팩트
대형 혼합 바이너리
이동된 버전
거짓 이웃
경계 변동
Deflate 계열
압축 불가
`);
export const MESSAGES = Object.freeze({
  files: "{n}개 파일", file: "{n}개 파일", logical: "논리 {bytes}", logicalInputFiles: "논리 입력 {bytes} · {n}개 파일",
  smallerThan: "{name}보다 {pct} 작음", largerThan: "{name}보다 {pct} 큼", sameStored: "{name}와 저장 바이트 동일", versus: "{name} 대비",
  cmpctSmaller: "CMPCT가 더 작음 · 매칭 저장 바이트", cmpctLarger: "CMPCT가 더 큼 · 매칭 저장 바이트", sameBytes: "저장 바이트 동일", unavailableMatched: "매칭 저장 바이트 없음",
  currentFrontier: "현재 CMPCT 연구 프런티어", categoryScore: "{wins}/{total} 작음 · {losses} 큼", noCategory: "카테고리 증거 없음", noFreshCategory: "이 프런티어에는 정확한 트리의 최신 카테고리 증거가 없습니다.",
  comparisonUnavailable: "비교 불가", noQualification: "이 공개 프런티어에는 기록된 벤치마크 조건이 없습니다.",
  heroIf: "이 매칭 테스트에서 {name}가 100 MB를 저장하면 CMPCT는 약 {value} MB가 필요합니다.", heroNeeds: "이 매칭 테스트에서 {name}가 저장하는 100 MB마다 CMPCT는 현재 약 {value} MB가 필요합니다.",
  seriousBaseline: "주요 크기 기준: {relation}.", scopedScheduler: "범위 제한 scheduler 결과: 고정 게이트에서 wall time {pct}% 감소.", canonicalRemains: "정규 형식은 r{revision}을 유지합니다.",
  frontierQualification: "{frontier} · 매칭 구조 트리 {files}개 파일.{serious}{speed} 정규 형식은 r{revision}을 유지합니다.", fixedSchedulerGate: "고정 적대적 scheduler 게이트 · 전역 속도 주장이 아님", winsAgainst: "{name} 대비 {wins}/{total} 승",
  noCommittedParity: "커밋된 패리티 기록 없음", repetitionsMedian: "{n}× 중앙값", semanticQualification: "의미론 조건:", interpretation: "해석:", currentProjectRelease: "현재 프로젝트 릴리스", versionedMilestone: "버전 관리 마일스톤",
  writerVerified: "포터블 writer는 정규 r{revision}에서 검증됨.", regularSubset: "일반 파일 하위 집합만 지원; 전체 파일시스템 의미론은 CLI 영역.", writerPaused: "형식 개정 {revision} 이후 브라우저 writer 일시 중지.", writerRefuses: "이 build는 r{supported}에서 검증됨; 더 새로운 문법을 추측하지 않음.",
  readyLocally: "로컬 준비 완료", cliOverLimit: "CLI 사용: 브라우저 한도 초과", input: "입력", archive: "아카이브", delta: "차이", smaller: "{bytes} 작음", overhead: "{bytes} 오버헤드", buildingLocally: "로컬에서 생성 중…", builtOnDevice: "이 장치에서 아카이브를 생성했습니다.",
  logicalFilesUnique: "논리 파일 {logical}개 → 고유 blob {unique}개 · {deflate} Deflate / {raw} RAW.", saveCmpct: ".cmpct 저장", couldNotBuild: "아카이브를 만들 수 없습니다.", fixedMagicError: "고정 Magic이 CMPCT로 보이지 않습니다.", inspection: "검사", benchmarkUnavailable: "벤치마크 데이터 없음: {error}", canonicalDataMissing: "정규 사이트 데이터를 불러오지 못했습니다."
});

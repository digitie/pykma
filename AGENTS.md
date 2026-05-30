# AGENTS.md

## 문서 언어 정책

이 저장소의 모든 Markdown/RST 문서는 한글로 작성합니다. 공식 API 필드명, 코드 식별자, 명령어, URL, provider 원문처럼 그대로 보존해야 하는 값만 영어를 유지합니다. 새 문서나 기존 문서를 수정할 때도 이 규칙을 우선합니다.

## 역할

이 문서는 `python-kma-api` 저장소에서 작업하는 에이전트를 위한 운영 가이드입니다. import package는 `kma`이며, 세부 구현 규칙은 `SKILL.md`, API 세부 내용은 `kma-api.md`와 `docs/` 아래 문서를 함께 확인합니다.

## 지시 우선순위

1. 사용자 요청
2. 이 `AGENTS.md`
3. `SKILL.md`
4. `kma-api.md`, `docs/decisions.md`, `docs/api-coverage.md`
5. `README.md` 및 나머지 `docs/`
6. 기존 코드와 테스트
7. 최소한의 되돌릴 수 있는 가정

문서가 충돌하면 더 높은 우선순위의 문서를 따르고, 필요하면 낮은 우선순위 문서를 갱신합니다.

작업 전에 반드시 다음을 읽는다:

1. `README.md` — 프로젝트 개요와 빠른 시작
2. `SKILL.md` — 프로젝트 불변조건과 DO NOT 규칙
3. `docs/resume.md` — 현재 진척도와 "다음 한 작업"
4. `docs/decisions.md` — 관련 ADR
5. `docs/journal.md` — 최근 작업 일지 엔트리 3개

## 프로젝트 기준

- `python-kma-api`는 기상청 공공 날씨 API용 Python 클라이언트이며 import package 이름은 `kma`입니다.
- 타입화된 클라이언트의 1차 대상은 `VilageFcstInfoService_2.0`입니다.
- 안정적으로 모델링한 endpoint는 초단기실황, 초단기예보, 단기예보, 예보버전입니다.
- data.go.kr의 다른 KMA REST 서비스는 `DataGoKrClient`로 범용 호출합니다.
- APIHub는 `ApiHubClient`로 `authKey` 기반 path 호출과 탐색 기능을 제공하고, `ApiHubGeneratedClient`로 공식 목록 endpoint의 함수형 래퍼를 제공합니다.
- Python 지원 기준은 3.10 이상입니다.
- 런타임 의존성은 `requests`입니다.
- 기본 테스트는 실제 KMA 네트워크 호출 없이 동작해야 합니다.

## 개발 환경 및 에이전트 정책

PC 개발은 Windows 호스트에서 직접 진행합니다. 본 저장소는 Python 패키지이므로 가상환경(`.venv`)을 구성하여 품질 관리를 수행합니다.

- **에이전트별 고정 worktree**:
  - ChatGPT Codex: `F:\dev\python-kma-api-codex`
  - Claude Code: `F:\dev\python-kma-api-claude`
  - Google Antigravity 2.0: `F:\dev\python-kma-api-antigravity`
  - 작업마다 브랜치만 새로 만들고, CodeGraph는 worktree마다 1회 `codegraph init -i` 후 `codegraph sync`로 유지합니다.
- **품질 게이트**: PR 머지 직전 작업자가 로컬에서 직접 린트와 테스트를 수행합니다.

## 절대 하지 말 것 (DO NOT)

1. **`main` 직접 푸시 금지** — 반드시 feature 브랜치 + PR 생성 후 로컬/리모트 승인을 받아 머지합니다.
2. **실제 `serviceKey`나 `authKey` 평문 노출 금지** — 출력, 로그, 커밋, fixture에 절대로 남기지 않습니다. 사용자가 붙여넣은 인증키 공백은 클라이언트 경계에서 제거하고, `.env`/`.env.local` 로컬 키 로딩을 활용합니다.
3. **기본 테스트에서 실제 API 호출 금지** — 네트워크 호출 없는 mock/fixture 기반으로 검증해야 합니다. 실제 호출 테스트를 추가할 경우 `DATA_GO_KR_SERVICE_KEY`가 있을 때만 실행되도록 `integration` marker를 사용합니다.
4. **`nx`/`ny`를 위도/경도로 취급 금지** — WGS84 좌표는 항상 `lat/lon` 순서로 다루며, KMA 격자 좌표(`nx/ny`)와 엄격히 구분합니다. 외부 프로그램용 위치 입력은 `LatLon`/`GridPoint` 또는 `location=`으로 표준화합니다.
5. **`PCP`, `SNO` 범주 문자열을 무조건 float로 변환 금지** — `"1.0mm 미만"`, `"30.0~50.0mm"`, `"강수없음"` 같은 범주 문자열은 무리하게 숫자로 바꾸지 않고 보존합니다. 대표값이 필요할 때만 `parse_amount()`를 제공합니다.
6. **KMA result code 실패를 빈 리스트 성공처럼 반환 금지** — `resultCode != "00"`은 반드시 명시적인 typed exception으로 surface합니다.
7. **data.go.kr와 APIHub의 인증 파라미터 혼용 금지** — data.go.kr 키는 `DATA_GO_KR_SERVICE_KEY`, APIHub 키는 `KMA_APIHUB_AUTH_KEY`로 엄격히 분리하여 사용합니다.
8. **APIHub endpoint가 항상 JSON을 반환한다고 가정 금지** — 텍스트, 이미지, 바이너리 응답이 섞여 있으므로 `response_kind`나 `content` 타입을 명확히 처리합니다.
9. **불필요한 wrapper/adapter 계층 추가 금지** — 단순 전달용 wrapper, 장기 호환 alias, 임시 facade를 지양하고, 다른 라이브러리에 검증된 구현이 있으면 라이선스와 출처를 확인한 뒤 프로젝트 내부 구현으로 직접 반영합니다.
10. **문서에 로컬 절대 경로 기재 금지** — 문서의 파일 위치 정보는 항상 프로젝트 루트 기준 상대 경로(예: `src/kma/client.py`)로 작성합니다.

## Provider API 사용 원칙

- 외부 API 관련 작업은 다른 구현보다 먼저 wrapper/adapter/gateway 지양 원칙을 확인하고 문서/코드에 반영한 뒤 진행합니다.
- downstream이 직접 사용할 안정된 public client, typed model, enum, helper를 제공합니다.
- 단순 전달용 wrapper, 장기 호환 alias, 임시 facade를 만들지 않습니다.
- TripMate나 `python-krtour-map`에서 필요한 endpoint, pagination, cursor, exception, raw payload 계약이 부족하면 이 저장소의 public API를 먼저 안정화합니다.
- 다른 라이브러리에 검증된 구현이 있으면 wrapper로 감싸지 말고 라이선스와 출처를 확인한 뒤 현재 구조에 직접 반영합니다. 이때 변경 폭이 최소수정 원칙보다 커지더라도 동작 일치와 유지보수성을 더 중요하게 봅니다.

## 문서 구성

- `README.md`: 사용자용 개요, 설치, 예제, 모델 요약.
- `kma-api.md`: 단기예보 endpoint 세부 사항과 KMA 응답 규칙.
- `docs/apihub.md`: APIHub 인증키, 범용 호출, 탐색 기능, 응답 형식 규칙.
- `docs/apihub-endpoints.md`: APIHub 함수형 endpoint 목록.
- `docs/datagokr.md`: data.go.kr 범용 클라이언트와 서비스/operation 예시.
- `docs/api-coverage.md`: 현재 구현 범위와 API 개수.
- `docs/testing.md`: 테스트 설계, live test 제한, 회귀 테스트 절차.
- `docs/troubleshooting.md`: 증상별 원인과 해결책.
- `docs/repeated-mistakes.md`: 이미 겪었거나 반복되기 쉬운 실수.
- `SKILL.md`: 구현 불변조건과 에이전트용 세부 규칙.
- `AGENTS.md`: 작업 라우팅, 모듈 소유권, 검증 체크리스트.
- `CONTRIBUTING.md`: 기여 절차.
- `CHANGELOG.md`: 릴리스 관점 변경 이력.
- `pyproject.toml`: 패키징, 의존성, lint/test 설정.

## 모듈 지도

- `src/kma/client.py`: `KmaClient`, 타입화된 단기예보 endpoint, 응답 파싱.
- `src/kma/datagokr.py`: data.go.kr 범용 서비스/operation 호출.
- `src/kma/_credentials.py`: 인증키 정규화와 `.env`/`.env.local` 로딩.
- `src/kma/catalog.py`: data.go.kr/APIHub UI용 통합 API 카탈로그 row.
- `src/kma/datagokr_catalog.py`: 공공데이터포털 기상청 OpenAPI dataset catalog.
- `src/kma/apihub.py`: APIHub 범용 호출, `typ02/openApi` helper, 탐색 parser, TXT/이미지 응답 helper.
- `src/kma/apihub_endpoints.py`: 생성된 APIHub 함수형 endpoint 래퍼.
- `src/kma/enums.py`: endpoint, category, SKY/PTY public enum.
- `src/kma/locations.py`: `LatLon`, `GridPoint`, `normalize_location()` 위치 표준화.
- `src/kma/_http.py`: session 생성과 retry 설정.
- `src/kma/grid.py`: LCC DFS 격자 변환.
- `src/kma/time_utils.py`: KST 기준 base date/time 계산.
- `src/kma/codes.py`: category map, 라벨, 단위 힌트, 강수량 문자열 파싱.
- `src/kma/models.py`: 사용자에게 반환하는 frozen Pydantic 모델.
- `src/kma/exceptions.py`: 예외 계층.
- `src/kma/cli.py`: JSON CLI와 APIHub path 호출.
- `tests/`: 네트워크 없는 단위 테스트.

## 작업 소유권

### 단기예보 클라이언트

담당 파일:
- `src/kma/client.py`
- `src/kma/_http.py`

확인할 것:
- `serviceKey`를 요청 파라미터로 보냅니다.
- `dataType=JSON`을 기본으로 둡니다.
- `pageNo`, `numOfRows` 기본값이 있습니다.
- fake session 테스트가 요청 파라미터를 검증합니다.
- `resultCode != "00"`은 typed exception입니다.

### data.go.kr 범용 클라이언트

담당 파일:
- `src/kma/datagokr.py`
- `docs/datagokr.md`

확인할 것:
- URL은 `{base_url}/{service}/{operation}` 형태입니다.
- `serviceKey`, `pageNo`, `numOfRows`, `dataType` 기본값이 있습니다.
- data.go.kr 문서가 `ServiceKey`를 요구하는 경우 `service_key_param`으로 인증 파라미터 이름을 바꿀 수 있습니다.
- `items()`는 단일 dict 응답도 list로 감쌉니다.
- `api_catalog()`는 사람이 읽을 수 있는 데이터셋명, gateway, operation, 인증 파라미터, 키 발급 링크를 제공합니다.

### APIHub 클라이언트

담당 파일:
- `src/kma/apihub.py`
- `src/kma/apihub_endpoints.py`
- `docs/apihub.md`
- `docs/apihub-endpoints.md`
- `tools/update_apihub_endpoints.py`

확인할 것:
- APIHub path는 `/api/`로 시작해야 합니다.
- `authKey`를 자동으로 추가합니다.
- 탐색 parser는 sample URL에서 `authKey`를 제거합니다.
- 응답은 `text`와 `content`를 모두 제공합니다.
- 이름 없는 query string은 `arg1`, `arg2` 순서를 보존합니다.
- 생성된 endpoint 수와 문서의 endpoint 수가 일치해야 합니다.
- 포맷정보/예제 첨부 링크는 `APIHUB_ATTACHMENTS` metadata와 문서가 일치해야 합니다.

### 시간 계산

담당 파일:
- `src/kma/time_utils.py`

확인할 것:
- 초단기실황: `HH00`, 발표 후 40분.
- 초단기예보: `HH30`, 발표 후 15분.
- 단기예보: `0200/0500/0800/1100/1400/1700/2000/2300`, 발표 후 10분.
- 전날 자정 경계 케이스를 테스트합니다.

### 좌표 변환

담당 파일:
- `src/kma/grid.py`
- `src/kma/locations.py`

확인할 것:
- 공식 LCC DFS 상수는 근거 없이 바꾸지 않습니다.
- 서울, 부산, 제주, 강남 검증점이 통과합니다.
- 역변환은 허용 오차로 비교합니다.
- `LatLon`은 WGS84 `EPSG:4326`, `GridPoint`는 KMA DFS 좌표입니다.
- `location=`은 `lat/lon` 또는 `nx/ny`와 섞어 쓰지 못해야 합니다.

### 코드 매핑

담당 파일:
- `src/kma/codes.py`
- `src/kma/enums.py`

확인할 것:
- public enum 값은 KMA wire value와 같아야 합니다.
- `SKY`는 `1`, `3`, `4`만 매핑합니다.
- `PTY`는 endpoint-aware입니다.
- `PCP`, `SNO` 문자열은 보존합니다.
- `parse_amount()`는 없음, 미만, 범위, 이상 라벨을 처리합니다.

### 문서

담당 파일:
- 모든 `.md` 문서

확인할 것:
- 프로젝트 문서는 한글로 작성합니다.
- 파일 위치 정보는 `src/kma/client.py`, `docs/testing.md`처럼 프로젝트 루트 기준 상대 경로로 작성합니다.
- Python 내부 문서와 docstring은 한글로 작성합니다.
- 코드 식별자, 명령어, URL은 원문을 유지합니다.
- 사용자 예제는 실제 public API와 일치해야 합니다.
- API 개수와 구현 범위는 `docs/api-coverage.md`에 반영합니다.

## 작업 후 체크리스트

- [ ] `pytest -q` 통과
- [ ] `ruff check .` / `mypy src/kma` 통과
- [ ] `docs/journal.md`에 작업 항목 추가 (역시간순)
- [ ] `docs/resume.md`의 진척도 갱신
- [ ] 의사결정이 있었다면 `docs/decisions.md`에 ADR 추가
- [ ] 사용자 가시 변경이면 `CHANGELOG.md` 갱신

## 검증

기본 검증:
```bash
python -m pytest -q
python -m ruff check .
python -m mypy src/kma
```

실제 API 테스트를 추가할 경우 opt-in으로 둡니다.
```bash
DATA_GO_KR_SERVICE_KEY=<decoded service key> python -m pytest -m integration
```

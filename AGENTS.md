# AGENTS.md

## 역할

이 문서는 `pykma`에서 작업하는 에이전트를 위한 운영 가이드입니다. 빠르게 방향을 잡는 문서이며, 세부 구현 규칙은 `SKILL.md`, API 세부 내용은 `kma-api.md`와 `docs/` 아래 문서를 함께 확인합니다.

## 지시 우선순위

1. 사용자 요청
2. 이 `AGENTS.md`
3. `kma-api.md`
4. `SKILL.md`
5. `README.md`
6. 기존 코드와 테스트
7. 최소한의 되돌릴 수 있는 가정

문서가 충돌하면 더 높은 우선순위의 문서를 따르고, 필요하면 낮은 우선순위 문서를 갱신합니다.

## 프로젝트 기준

- `pykma`는 기상청 공공 날씨 API용 Python 클라이언트입니다.
- 타입화된 클라이언트의 1차 대상은 `VilageFcstInfoService_2.0`입니다.
- 안정적으로 모델링한 endpoint는 초단기실황, 초단기예보, 단기예보, 예보버전입니다.
- data.go.kr의 다른 KMA REST 서비스는 `DataGoKrClient`로 범용 호출합니다.
- APIHub는 `ApiHubClient`로 `authKey` 기반 path 호출과 탐색 기능을 제공하고, `ApiHubGeneratedClient`로 공식 목록 endpoint의 함수형 래퍼를 제공합니다.
- Python 지원 기준은 3.10 이상입니다.
- 런타임 의존성은 `requests`입니다.
- 기본 테스트는 실제 KMA 네트워크 호출 없이 동작해야 합니다.

## 문서 구성

- `README.md`: 사용자용 개요, 설치, 예제, 모델 요약.
- `kma-api.md`: 단기예보 endpoint 세부 사항과 KMA 응답 규칙.
- `docs/apihub.md`: APIHub 인증키, 범용 호출, 탐색 기능, 응답 형식 규칙.
- `docs/apihub-endpoints.md`: APIHub 함수형 endpoint 목록.
- `docs/datagokr.md`: data.go.kr 범용 클라이언트와 서비스/operation 예시.
- `docs/expressway.md`: 한국도로공사 휴게소별 날씨 API 사용법.
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

- `pykma/client.py`: `KmaClient`, 타입화된 단기예보 endpoint, 응답 파싱.
- `pykma/datagokr.py`: data.go.kr 범용 서비스/operation 호출.
- `pykma/apihub.py`: APIHub 범용 호출, `typ02/openApi` helper, 탐색 parser, TXT/이미지 응답 helper.
- `pykma/apihub_endpoints.py`: 생성된 APIHub 함수형 endpoint 래퍼.
- `pykma/expressway.py`: 한국도로공사 휴게소별 날씨 API 클라이언트.
- `pykma/enums.py`: endpoint, category, SKY/PTY public enum.
- `pykma/locations.py`: `LatLon`, `GridPoint`, `normalize_location()` 위치 표준화.
- `pykma/_http.py`: session 생성과 retry 설정.
- `pykma/grid.py`: LCC DFS 격자 변환.
- `pykma/time_utils.py`: KST 기준 base date/time 계산.
- `pykma/codes.py`: category map, 라벨, 단위 힌트, 강수량 문자열 파싱.
- `pykma/models.py`: 사용자에게 반환하는 frozen Pydantic 모델.
- `pykma/exceptions.py`: 예외 계층.
- `pykma/cli.py`: JSON CLI와 APIHub path 호출.
- `tests/`: 네트워크 없는 단위 테스트.

## 반드시 지킬 것

- 실제 `serviceKey`나 `authKey`를 출력, 로그, 커밋, fixture에 남기지 않습니다.
- 기본 테스트에서 실제 API를 호출하지 않습니다.
- `nx`/`ny`를 위도/경도로 취급하지 않습니다.
- 외부 프로그램용 위치 입력은 가능하면 `LatLon`/`GridPoint` 또는 `location=`으로 표준화합니다.
- KMA 시간은 KST 기준입니다.
- `PCP`, `SNO` 범주 문자열을 무조건 float로 변환하지 않습니다.
- KMA result code 실패를 빈 리스트 성공처럼 반환하지 않습니다.
- data.go.kr와 APIHub의 인증 파라미터를 섞지 않습니다.
- 한국도로공사 휴게소 날씨 API는 `key` 파라미터와 `EXPRESSWAY_API_KEY` 환경변수를 사용합니다.
- APIHub endpoint가 항상 JSON을 반환한다고 가정하지 않습니다.

## 작업 소유권

### 단기예보 클라이언트

담당 파일:

- `pykma/client.py`
- `pykma/_http.py`

확인할 것:

- `serviceKey`를 요청 파라미터로 보냅니다.
- `dataType=JSON`을 기본으로 둡니다.
- `pageNo`, `numOfRows` 기본값이 있습니다.
- fake session 테스트가 요청 파라미터를 검증합니다.
- `resultCode != "00"`은 typed exception입니다.

### data.go.kr 범용 클라이언트

담당 파일:

- `pykma/datagokr.py`
- `docs/datagokr.md`

확인할 것:

- URL은 `{base_url}/{service}/{operation}` 형태입니다.
- `serviceKey`, `pageNo`, `numOfRows`, `dataType` 기본값이 있습니다.
- data.go.kr 문서가 `ServiceKey`를 요구하는 경우 `service_key_param`으로 인증 파라미터 이름을 바꿀 수 있습니다.
- `items()`는 단일 dict 응답도 list로 감쌉니다.

### APIHub 클라이언트

담당 파일:

- `pykma/apihub.py`
- `pykma/apihub_endpoints.py`
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

### 한국도로공사 휴게소 날씨

담당 파일:

- `pykma/expressway.py`
- `docs/expressway.md`
- `tests/test_expressway.py`

확인할 것:

- endpoint는 `http://data.ex.co.kr/openapi/restinfo/restWeatherList`입니다.
- 인증 파라미터는 `key`입니다.
- 요청 파라미터는 `type=json`, `sdate=YYYYMMDD`, `stdHour=HH`입니다.
- `code != SUCCESS`는 typed exception입니다.
- `-99` 계열 결측값은 모델 필드에서 `None`으로 정규화하고 원문은 `raw`에 보존합니다.
- 실서버 테스트는 `PYKMA_RUN_LIVE=1`과 `EXPRESSWAY_API_KEY`가 있을 때만 실행합니다.

### 시간 계산

담당 파일:

- `pykma/time_utils.py`

확인할 것:

- 초단기실황: `HH00`, 발표 후 40분.
- 초단기예보: `HH30`, 발표 후 15분.
- 단기예보: `0200/0500/0800/1100/1400/1700/2000/2300`, 발표 후 10분.
- 전날 자정 경계 케이스를 테스트합니다.

### 좌표 변환

담당 파일:

- `pykma/grid.py`
- `pykma/locations.py`

확인할 것:

- 공식 LCC DFS 상수는 근거 없이 바꾸지 않습니다.
- 서울, 부산, 제주, 강남 검증점이 통과합니다.
- 역변환은 허용 오차로 비교합니다.
- `LatLon`은 WGS84 `EPSG:4326`, `GridPoint`는 KMA DFS 좌표입니다.
- `location=`은 `lat/lon` 또는 `nx/ny`와 섞어 쓰지 못해야 합니다.

### 코드 매핑

담당 파일:

- `pykma/codes.py`
- `pykma/enums.py`

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
- 코드 식별자, 명령어, URL은 원문을 유지합니다.
- 사용자 예제는 실제 public API와 일치해야 합니다.
- API 개수와 구현 범위는 `docs/api-coverage.md`에 반영합니다.

## 검증

기본 검증:

```bash
python -m compileall pykma tests
python -m pytest
```

선택 검증:

```bash
ruff check .
mypy pykma
```

실제 API 테스트를 추가할 경우 opt-in으로 둡니다.

```bash
KMA_SERVICE_KEY=<decoded service key> python -m pytest -m integration
```

## 현재 메모

- `docs/apihub.md`는 APIHub 목록과 탐색 방식을 설명합니다.
- `docs/apihub-endpoints.md`는 `tools/update_apihub_endpoints.py`로 갱신합니다.
- `docs/datagokr.md`는 data.go.kr 범용 호출 방식을 설명합니다.
- `docs/repeated-mistakes.md`는 KMA/APIHub 함정이 발견될 때마다 갱신합니다.
- `docs/testing.md`는 test marker와 test 파일 구조가 바뀔 때 함께 갱신합니다.
- `docs/troubleshooting.md`는 사용자에게 보이는 실패 모드가 추가될 때 갱신합니다.

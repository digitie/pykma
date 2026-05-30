# AI 에이전트 가이드: python-kma-api (kma)

이 라이브러리(`kma`)를 임포트하여 사용하는 외부 기상 정보 서비스 및 소비자 앱(예: TripMate, tour-map, kraddr 등)의 코드를 생성하는 AI 코딩 어시스턴트(Cursor, Copilot, ChatGPT, Claude Code 등)를 위한 컨텍스트 문서입니다.

> **본 저장소(`python-kma-api`) 자체를 수정하려는 에이전트는 다른 문서를 봅니다**:
> [`CLAUDE.md`](./CLAUDE.md)가 세션 진입점이며, 상세 가이드는 [`AGENTS.md`](./AGENTS.md)와 [`SKILL.md`](./SKILL.md)에 있습니다. 이 문서는 **외부 라이브러리 사용자 및 소비자용 AI**를 대상으로 합니다.

---

## 1. 이 라이브러리는 무엇인가

- 대한민국 기상청(KMA)의 공공데이터포털(data.go.kr) 날씨 API 및 기상청 APIHub를 Python에서 안정적이고 명시적인 타입으로 다루기 위한 **공용 클라이언트 라이브러리**입니다.
- **import 패키지 이름은 `kma`입니다.**
- **핵심 역할**:
  - `VilageFcstInfoService_2.0` 타입화 클라이언트 (초단기실황, 초단기예보, 단기예보, 예보버전).
  - WGS84 위도/경도 ↔ KMA LCC DFS 격자 좌표(`nx/ny`) 변환 자동화.
  - KST 발표시각 및 지연시간을 반영한 최근 가용한 예보시각 자동 선택.
  - Pydantic v2 frozen 응답 모델 제공.
  - data.go.kr 86개 dataset 카탈로그 범용 호출 및 APIHub 470개 함수형 endpoint wrapper 제공.

---

## 2. 핵심 퍼블릭 API 가이드

외부 소비자 앱을 빌드할 때 직접 사용해도 좋은 안정된 Public API 엔트리포인트들입니다.

### 2.1. `KmaClient` (단기예보 3종 및 버전)

동기 호출은 `KmaClient.from_env()`, 비동기 호출은 `KmaClient.aio_from_env()` 패턴을 활용합니다.

```python
from kma import KmaClient, LatLon, GridPoint

# 동기 호출 예시
with KmaClient.from_env() as kma:
    # 1. 초단기실황 (현재 날씨 스냅샷)
    snap = kma.forecast.now(lat=37.5665, lon=126.9780)  # 서울시청
    print(f"기온: {snap.temperature}°C, 하늘상태: {snap.sky_label}, 강수: {snap.precipitation_label}")
    
    # 2. 단기예보 (향후 3일 일기예보 목록)
    items = kma.forecast.vilage(location=LatLon(37.5665, 126.9780))
    for item in items[:5]:
        print(item.forecast_at, item.category, item.value, item.label)
```

```python
# 비동기 호출 예시
from kma import KmaClient

async with KmaClient.aio_from_env() as kma:
    # 3. 초단기예보 (향후 6시간 대략 예보)
    short_items = await kma.forecast.short(nx=60, ny=127)
```

---

## 3. 주요 규칙 및 함정 피하기

외부 어플리케이션 개발 시 AI 어시스턴트가 반드시 지켜야 할 주의사항입니다.

### 3.1. nx/ny를 위도/경도로 오용하지 말 것
- **`nx`, `ny`는 위도/경도가 아닙니다!** 기상청 공식 LCC DFS 좌표입니다.
- WGS84 `lat/lon` (위도/경도)과 격자 좌표 `nx/ny`를 혼동하여 파라미터로 넘기는 대형 실수를 피하세요.
- 위치 값은 명시적인 값 객체(`LatLon`, `GridPoint`)를 사용하거나, `normalize_location()`으로 표준화하여 전달할 수 있습니다.
  ```python
  from kma import LatLon, GridPoint
  
  # 올바른 사용
  kma.forecast.now(location=LatLon(37.5665, 126.9780))
  kma.forecast.now(location=GridPoint(60, 127))
  kma.forecast.now(location={"latitude": 37.5665, "longitude": 126.9780})
  ```

### 3.2. PCP/SNO 강수량/적설량의 무리한 수치 변환 금지
- 기상청 단기예보 응답에서 강수량(`PCP`), 적설량(`SNO`)은 `"1.0mm 미만"`, `"30.0~50.0mm"`, `"강수없음"` 같은 범주 문자열을 반환합니다.
- `ForecastItem.value` 필드는 이러한 한국어 문자열 범주를 그대로 보존하므로, 임의로 `float()`로 강제 캐스팅 시 에러를 유발합니다.
- 수치로 파싱한 대표값이 필요하다면 전용 헬퍼인 `parse_amount()`를 호출해 안전하게 획득하세요.
  ```python
  from kma.codes import parse_amount
  
  parse_amount("1.0mm 미만")   # 0.5 (반환됨)
  parse_amount("30.0~50.0mm") # 40.0
  parse_amount("강수없음")     # 0.0
  ```

### 3.3. KST 발표시각의 이해
- 기상청 API는 실시간 기상 데이터를 반환하지 못하고, 특정 발표 주기(정각, 30분, 단기예보 하루 8회)가 있으며 서버 반영 지연시간(10분~40분)이 있습니다.
- `kma` 라이브러리는 현재 시간(KST)을 바탕으로 가장 최신의 사용 가능한 발표시각(`base_date`, `base_time`)을 자동으로 추정 및 대입하므로, 외부 코드에서 현재 시각을 그대로 `base_time`에 넣어 빈 데이터 응답(`NODATA_ERROR`)을 겪는 일이 없도록 합니다.

### 3.4. 예외 계층 활용
- 기상청 오류 코드는 다음과 같이 구조화되어 surface되므로, 각 상황에 맞춰 적절히 복구하거나 예외 처리를 수행할 수 있습니다.
  ```text
  KmaError
  ├── KmaAuthError      # 인증키 오류, 미승인, 만료
  ├── KmaRequestError   # 잘못된 요청 파라미터, 호출 한도 초과(Quota), 데이터 없음(NODATA)
  ├── KmaServerError    # 기상청 서버 장애 (500, 502 등)
  └── KmaParseError     # 예상과 다른 이상 응답 포맷
  ```
- 예외 인스턴스는 `failure_kind`, `retryable`, `metadata`를 담고 있어, 429나 일시적 5xx 장애 시 재시도 전략을 쉽게 취할 수 있습니다.

---

## 4. 제공하는 기타 클라이언트

- **`DataGoKrClient` (기상청 공공데이터포털 범용 클라이언트)**:
  `MidFcstInfoService` (중기예보), `AsosDalyInfoService` (종관기상관측), `WthrWrnInfoService` (기상특보) 등 data.go.kr의 기상청 서비스 86개 전체 데이터셋을 호출하는 래퍼입니다.
- **`ApiHubClient` (APIHub 범용 클라이언트)**:
  `authKey` 기반의 APIHub `/api/` path 호출을 수행하며, TXT 테이블 및 이미지 응답 등을 파싱할 수 있습니다.
- **`ApiHubGeneratedClient` (APIHub 470개 함수형 래퍼)**:
  공식 목록의 endpoint를 함수명으로 직접 타이핑하여 IDE 자동완성 혜택을 받으며 즉시 사용할 수 있습니다.

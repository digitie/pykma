# 테스트 가이드

`pykma` 테스트는 실제 날씨값에 의존하지 않고 KMA 특유의 실수를 잡도록 설계합니다.

## 기본 테스트

```bash
python -m pytest
```

기본 테스트는 다음 조건을 지켜야 합니다.

- 네트워크 호출 없음
- 결정적 결과
- `KMA_SERVICE_KEY` 없이 실행 가능
- 요청 파라미터, 응답 파싱, 변환, 예외 동작 중심

## 현재 테스트 범위

- `tests/test_client.py`: 단기예보 typed client 요청 파라미터, fake session 응답 파싱, result code 매핑, 잘못된 응답 처리.
- `tests/test_datagokr.py`: data.go.kr 범용 service/operation 호출과 envelope 처리.
- `tests/test_expressway.py`: 한국도로공사 휴게소별 날씨 요청 파라미터, 응답 모델, 결측값 정규화, 에러 매핑.
- `tests/test_pydantic_models.py`: public 응답 모델의 Pydantic 직렬화, frozen 동작, 좌표 검증.
- `tests/test_apihub.py`: APIHub 범용 요청, `typ02/openApi` helper, 탐색 HTML parser, TXT table parser, 이미지 header parser.
- `tests/test_apihub_endpoints.py`: 생성된 APIHub 470개 함수형 래퍼, sample parameter 적용, 이름 없는 query string 보존.
- `tests/test_apihub_generator.py`: APIHub 보조 metadata 페이지가 실패해도 생성기가 본문 endpoint 수집을 유지하는지 검증.
- `tests/test_live_services.py`: `.env.local` 인증키와 `PYKMA_RUN_LIVE=1`이 있을 때만 실행되는 APIHub/data.go.kr 실서버 smoke test.
- `tests/test_codes.py`: `SKY`/`PTY` 라벨, `PCP`/`SNO` 보존, `parse_amount()`.
- `tests/test_enums.py`: public enum wire value, enum-aware code helper, 모델의 enum/category helper.
- `tests/test_grid.py`: 알려진 격자 변환점과 좌표 범위.
- `tests/test_locations.py`: `LatLon`, `GridPoint`, mapping 기반 `location=` 표준화와 모호한 입력 거부.
- `tests/test_time_utils.py`: KST 변환과 endpoint별 base time 선택.
- `tests/test_cli.py`: CLI 인자 처리와 JSON/text 출력 형태.

## 실제 API 테스트

실제 API 호출 테스트는 반드시 명시적 marker를 사용합니다.

```python
import os
import pytest

pytestmark = pytest.mark.integration

@pytest.mark.skipif(not os.getenv("KMA_SERVICE_KEY"), reason="KMA_SERVICE_KEY is not set")
def test_live_now_shape():
    ...
```

실제 API 테스트는 정확한 날씨값이 아니라 구조와 타입을 검증합니다.

좋은 검증:

- 잘 알려진 격자에서 응답이 비어 있지 않음
- datetime 필드가 KST aware임
- `nx`, `ny`가 요청값과 일치함
- category가 문자열임

피해야 할 검증:

- 정확한 기온
- 정확한 하늘상태나 강수형태
- API 계약이 보장하지 않는 정확한 row 개수

## 수동 smoke test

data.go.kr Decoding 키가 있을 때:

```bash
KMA_SERVICE_KEY=<decoded key> pykma now --nx 60 --ny 127
KMA_SERVICE_KEY=<decoded key> pykma forecast --lat 37.5665 --lon 126.9780
```

PowerShell:

```powershell
$env:KMA_SERVICE_KEY="<decoded key>"
pykma now --nx 60 --ny 127
```

APIHub 키가 있을 때:

```powershell
$env:KMA_APIHUB_AUTH_KEY="<APIHub authKey>"
pykma apihub /api/typ01/url/wrn_reg.php --param tmfc=0
```

로컬에서만 쓰는 인증키는 `.env.local`에 둘 수 있습니다. 이 파일은 `.gitignore`에 포함되어 커밋되지 않습니다.

```text
KMA_APIHUB_AUTH_KEY=<APIHub authKey>
KMA_SERVICE_KEY=<data.go.kr decoded service key>
DATA_GOKR_SERVICE_KEY=<data.go.kr decoded service key>
EXPRESSWAY_API_KEY=<한국도로공사 API key>
```

실제 서버 integration 테스트는 의도치 않은 네트워크 호출을 막기 위해 marker와 `PYKMA_RUN_LIVE=1`을 함께 요구합니다.

```powershell
$env:PYKMA_RUN_LIVE="1"
python -m pytest -m integration
Remove-Item Env:\PYKMA_RUN_LIVE
```

`PYKMA_RUN_LIVE`가 없으면 integration 테스트도 실제 서버를 호출하지 않고 skip됩니다. 기본 테스트에서 integration 테스트 자체를 제외하려면:

```bash
python -m pytest -m "not integration"
```

함수형 래퍼를 직접 smoke test할 때:

```python
from pykma import ApiHubGeneratedClient

hub = ApiHubGeneratedClient.from_env()
response = hub.kma_sfctm2(tm="202605010900", stn="108", help="1")
print(response.text[:200])
```

이 테스트도 인증키가 필요하므로 기본 테스트에 넣지 않습니다.

## 회귀 테스트 규칙

버그를 고칠 때:

1. 그 버그를 잡을 실패 테스트를 먼저 추가합니다.
2. 코드를 수정합니다.
3. 반복되기 쉬운 KMA/APIHub 함정이면 `docs/repeated-mistakes.md`를 갱신합니다.

APIHub endpoint 목록을 갱신할 때:

1. `python -X utf8 tools/update_apihub_endpoints.py`를 실행합니다.
2. `pykma/apihub_endpoints.py`와 `docs/apihub-endpoints.md`가 함께 바뀌었는지 확인합니다.
3. `python -m pytest tests/test_apihub.py tests/test_apihub_endpoints.py`를 실행합니다.
4. endpoint 개수가 바뀌면 `docs/api-coverage.md`와 `docs/apihub.md`의 숫자를 맞춥니다.

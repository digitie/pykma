# 문제 해결

흔한 증상과 가능한 원인, 해결 방법을 정리합니다.

## `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`

가능한 원인:

- 인증키가 만료되었거나 `VilageFcstInfoService_2.0`에 승인되지 않았습니다.
- Encoding 키를 `requests`의 `params=`에 넣어 이중 인코딩되었습니다.
- 다른 KMA 서비스에만 승인된 키입니다.

해결:

- `DATA_GO_KR_SERVICE_KEY`에는 Decoding 키를 넣습니다.
- data.go.kr 활용신청 승인 상태를 확인합니다.
- `KmaClient.now(nx=60, ny=127)`로 최소 요청을 시도합니다.
- `.env`나 `.env.local`을 쓰는 경우 data.go.kr 키는 `DATA_GO_KR_SERVICE_KEY` 또는 `DATA_GO_KR_SERVICE_KEY`, APIHub 키는 `KMA_APIHUB_AUTH_KEY` 또는 `KMA_APIHUB_KEY`에 둡니다.
- 포털에서 복사한 인증키에 줄바꿈이나 공백이 섞여도 클라이언트가 제거하지만, `.env`는 한 줄에 하나의 key만 둡니다.

## 빈 예보 항목 또는 `NODATA_ERROR`

가능한 원인:

- 요청한 `base_time`이 너무 최신입니다.
- endpoint 발표 주기를 무시했습니다.
- 격자 좌표가 범위를 벗어났거나 의도와 다른 위치입니다.

해결:

- 수동으로 date/time을 넣지 말고 `KmaClient`가 `base_time`을 고르게 합니다.
- `to_grid(lat, lon)`으로 위치를 확인합니다.
- endpoint별 발표 지연은 `kma-api.md`를 확인합니다.

## 예외를 구분해서 재시도하고 싶음

`KmaError` 하위 예외에는 선택적 metadata가 있습니다.

```python
try:
    kma.now(nx=60, ny=127)
except KmaError as exc:
    print(exc.failure_kind, exc.retryable, exc.metadata)
```

분류 기준:

- `auth`: 인증키 오류, 승인 안 됨, 만료. 보통 재시도하지 않습니다.
- `quota` 또는 `rate_limit`: 호출 한도나 HTTP 429. 시간 간격을 두고 재시도할 수 있습니다.
- `request`: 4xx 요청 오류나 잘못된 파라미터. 요청을 고쳐야 합니다.
- `server`: 5xx 또는 upstream 서버 장애. 재시도 가능성이 있습니다.
- `parse`: JSON이 아니거나 예상 schema가 바뀐 경우. raw 응답과 문서를 확인합니다.
- `network`: 네트워크/연결 오류. 재시도 가능성이 있습니다.

예외 metadata에는 `provider`, `endpoint`, `status_code`, `result_code`, `failure_kind`, `retryable`만 담습니다. `serviceKey`, `authKey`, `key` 원문은 남기지 않습니다.

## PowerShell에서 한국어 라벨이 깨져 보임

가능한 원인:

- 파일 손상이 아니라 터미널 코드페이지 표시 문제일 수 있습니다.

해결:

- Python UTF-8 읽기나 테스트로 확인합니다.

```bash
python -c "from kma.codes import label_for; print(repr(label_for('SKY', '1')))"
```

기대값:

```text
'맑음'
```

## `PCP` 또는 `SNO` 파싱 중 `ValueError`

가능한 원인:

- 한국어 범주 라벨에 `float(value)`를 직접 적용했습니다.

해결:

- `ForecastItem.value`는 라이브러리가 반환한 그대로 사용합니다.
- 대표 숫자가 필요할 때만 `parse_amount()`를 사용합니다.

```python
from kma.codes import parse_amount

parse_amount("1.0mm 미만")    # 0.5
parse_amount("30.0~50.0mm")  # 40.0
```

## 강수형태 라벨이 잘못됨

가능한 원인:

- `PTY`를 endpoint 구분 없이 매핑했습니다.

해결:

- `label_for()`에 endpoint를 전달합니다.
- 가능하면 직접 매핑하지 말고 `KmaClient` 모델 출력을 사용합니다.

## CLI가 좌표 오류를 보고함

예:

```bash
kma now --lat 37.5665
kma now --nx 60
```

해결:

좌표는 쌍으로 입력합니다.

```bash
kma now --lat 37.5665 --lon 126.9780
kma now --nx 60 --ny 127
```

좌표계를 섞지 않습니다.

```bash
kma now --lat 37.5665 --lon 126.9780 --nx 60 --ny 127
```

Python 코드에서는 좌표계를 명확히 하기 위해 값 객체를 사용할 수 있습니다.

```python
from kma import GridPoint, LatLon

kma.now(location=LatLon(37.5665, 126.9780))
kma.now(location=GridPoint(60, 127))
```

앱 저장 경계에서 `latitude`/`longitude` 이름을 쓴다면 명시적 alias를 사용할 수 있습니다.

```python
from kma import wgs84_to_kma_grid

grid = wgs84_to_kma_grid(latitude=37.5665, longitude=126.9780)
```

## import는 되지만 네트워크 호출에서 `requests`가 없다고 나옴

`kma`는 최소 환경에서도 좌표 helper를 import할 수 있게 해두었지만, `KmaClient` 네트워크 호출에는 `requests`가 필요합니다.

해결:

```bash
pip install -e .
```

또는:

```bash
pip install requests
```

## APIHub 호출이 JSON이 아니라 텍스트를 반환함

가능한 원인:

- APIHub에는 오래된 텍스트 표, CSV식 텍스트, 이미지, 바이너리 endpoint가 많습니다.

해결:

- 텍스트 endpoint는 `ApiHubResponse.text`를 사용합니다.
- 이미지나 파일 endpoint는 `ApiHubResponse.content`를 사용합니다.
- TXT 표를 Python row로 다루려면 `ApiHubResponse.text_table()`을 사용합니다.
- 문서상 JSON을 반환하는 endpoint에서만 `ApiHubResponse.json()`을 호출합니다.

## APIHub 그래픽 endpoint URL이 예제와 다르게 만들어짐

가능한 원인:

- 이름 없는 query string을 일반 dict로 변환했습니다.
- `?202305031000&0&...` 형태를 `params=`로 보내면서 `202305031000=`처럼 바뀌었습니다.

해결:

- `ApiHubGeneratedClient`의 생성된 함수를 사용합니다.
- 순서형 값은 `arg1`, `arg2`로 넘깁니다.

```python
from kma import ApiHubGeneratedClient

hub = ApiHubGeneratedClient.from_env()
response = hub.aws3_nph_awsm_tms_h06(use_sample=True)
```

## APIHub 함수 이름을 찾기 어려움

해결:

- 전체 목록은 [docs/apihub-endpoints.md](apihub-endpoints.md)를 확인합니다.
- 코드에서는 `APIHUB_ENDPOINTS`를 검색할 수 있습니다.

```python
from kma import APIHUB_ENDPOINTS

for endpoint in APIHUB_ENDPOINTS:
    if "wrn" in endpoint.path:
        print(endpoint.name, endpoint.path)
```

## APIHub에서는 `authKey`가 맞고 data.go.kr에서는 `serviceKey`가 맞음

APIHub와 data.go.kr는 서로 다른 gateway입니다.

- APIHub: `authKey`
- data.go.kr: `serviceKey`

`https://apihub.kma.go.kr/api/...` path는 `ApiHubClient`를 사용하고, `http://apis.data.go.kr/1360000/...` path는 `DataGoKrClient` 또는 `KmaClient`를 사용합니다.

## 저장용 raw payload와 serving payload를 분리하고 싶음

typed 모델은 `raw`와 sanitized `metadata`를 함께 제공합니다.

```python
snapshot = kma.now(nx=60, ny=127)
payload = snapshot.model_dump(mode="json")
```

이 결과를 그대로 raw 저장에 쓰거나, 앱에서 필요한 필드만 골라 serving 저장에 사용할 수 있습니다. `metadata.request_params`에는 인증키 원문이 없습니다.

## 중기예보 `reg_id`를 단기예보 좌표로 바꾸고 싶음

`reg_id`는 중기예보 권역 코드이고 `nx`/`ny`는 단기예보 KMA DFS 격자입니다. 서로 다른 체계이므로 `kma`는 임의 매핑을 제공하지 않습니다.

해결:

- `DataGoKrClient.mid_land_forecast(reg_id=..., tm_fc=...)`처럼 공식 `reg_id`를 직접 전달합니다.
- 단기예보는 `KmaClient.forecast(nx=..., ny=...)` 또는 `LatLon`/`GridPoint`를 사용합니다.
- 서비스별 지역 매핑이 필요하면 앱에서 별도 테이블로 관리합니다.

## APIHub가 HTTP 403과 활용신청 메시지를 반환함

가능한 원인:

- 인증키 형식은 맞지만 해당 endpoint의 활용신청이 승인되지 않았습니다.
- APIHub 포털 계정의 이용 등급이나 호출 권한이 요청한 API와 맞지 않습니다.

해결:

- APIHub 포털에서 해당 API의 활용신청/승인 상태를 확인합니다.
- 같은 키로 다른 endpoint가 되는지 확인해 키 자체 문제와 endpoint 권한 문제를 분리합니다.
- `ApiHubClient`는 401/403을 `KmaAuthError`로 변환하고, 예외 메시지와 `ApiHubResponse.url`에는 `authKey` 값을 남기지 않습니다.

로컬 실서버 테스트는 다음처럼 명시적으로만 실행합니다.

```powershell
$env:KMA_RUN_LIVE="1"
python -m pytest -m integration
Remove-Item Env:\KMA_RUN_LIVE
```

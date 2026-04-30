# data.go.kr KMA 지원

`pykma.KmaClient`는 사용량이 높은 단기예보 서비스를 타입화된 모델로 감싼 클라이언트입니다. `apis.data.go.kr/1360000`의 다른 KMA 공공데이터 서비스는 `DataGoKrClient`로 범용 호출합니다.

공식 확인 출처:

- https://www.data.go.kr/data/15084084/openapi.do
- https://www.data.go.kr/data/15059468/openapi.do
- https://www.data.go.kr/data/15000415/openapi.do
- https://www.data.go.kr/tcs/dss/selectApiDataDetailView.do?publicDataPk=15059093
- 수치모델, 위성, 항공, 특보 등 일부 최신 data.go.kr 항목은 APIHub로 redirect/link됩니다.

## 타입화 클라이언트

```python
from pykma import KmaClient

kma = KmaClient.from_env()
kma.now(nx=60, ny=127)
kma.forecast_short(nx=60, ny=127)
kma.forecast(nx=60, ny=127)
```

타입화 클라이언트가 다루는 endpoint:

- `VilageFcstInfoService_2.0/getUltraSrtNcst`
- `VilageFcstInfoService_2.0/getUltraSrtFcst`
- `VilageFcstInfoService_2.0/getVilageFcst`
- `VilageFcstInfoService_2.0/getFcstVersion`

## 범용 클라이언트

```python
from pykma import DataGoKrClient

client = DataGoKrClient.from_env()
body = client.request(
    "MidFcstInfoService",
    "getMidFcst",
    {"stnId": "108", "tmFc": "202605010600"},
)
```

표준 `response.body.items.item` 구조를 쓰는 operation은 `items()`를 사용할 수 있습니다.

```python
items = client.items(
    "MidFcstInfoService",
    "getMidFcst",
    {"stnId": "108", "tmFc": "202605010600"},
)
```

기본값:

- `serviceKey=<KMA_SERVICE_KEY>`
- `pageNo=1`
- `numOfRows=10`
- `dataType=JSON`

실제 서버 테스트에서만 쓰는 인증키는 `.env.local`에 둘 수 있습니다. 이 파일은 `.gitignore`에 포함되어 커밋되지 않습니다.

```text
KMA_SERVICE_KEY=<data.go.kr decoded service key>
DATA_GOKR_SERVICE_KEY=<data.go.kr decoded service key>
```

## data.go.kr 검색에서 확인한 예시

공식 data.go.kr 페이지에서 확인한 KMA REST 서비스 예시는 다음과 같습니다.

| service | operation 예시 | 비고 |
|---|---|---|
| `VilageFcstInfoService_2.0` | `getUltraSrtNcst`, `getVilageFcst` | `KmaClient`가 typed 지원 |
| `MidFcstInfoService` | `getMidFcst`, `getMidTa`, `getMidLandFcst`, `getMidSeaFcst` | generic JSON/XML envelope |
| `WthrWrnInfoService` | `getWthrWrnList` | 기상특보 |
| `AsosDalyInfoService` | `getWthrDataList` | ASOS 일자료 |
| `YdstInfoService` | `getYdstSatlitImg`, `getYdstObs` | 황사정보 |
| `LgtDistrbInfoService` | `getLgtDistrb` | 낙뢰분포도 |
| `CloudSatlitInfoService` | `getGk2acldAll` 등 | 위성자료 경량화 |
| `UppInfoService` | 활용가이드별 operation | 고층기상관측 |

일부 최신 data.go.kr 항목은 기존 `serviceKey` gateway가 아니라 APIHub로 이동하는 LINK 유형입니다. 그런 경우 `ApiHubClient`를 사용합니다.

## 인증키 규칙

`requests params=`로 호출할 때는 Decoding service key를 사용합니다.

```python
DataGoKrClient(service_key="decoded-key")
```

이미 인코딩된 키를 `params=`에 넣으면 다시 인코딩되어 `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`가 발생할 수 있습니다.

# API 구현 범위

이 문서는 현재 `pykma`가 구현한 API 개수를 명확히 세기 위한 기준입니다.

## 요약

현재 직접 타입화된 모델로 구현한 KMA endpoint는 **4개**이고, APIHub 공식 목록을 함수형으로 감싼 endpoint는 **470개**입니다.

| 구분 | 개수 | 설명 |
|---|---:|---|
| 개별 타입화 endpoint | 4개 | `KmaClient`가 dataclass로 반환하는 단기예보 endpoint |
| data.go.kr 범용 호출 방식 | 1개 계층 | 임의 `{service}/{operation}` 호출 가능 |
| APIHub 범용 호출 방식 | 1개 계층 | 임의 `/api/...` path 호출 가능 |
| APIHub 함수형 래퍼 | 470개 | `apiList.do`와 `generateAPIUrl.do` 기반 함수형 endpoint |
| APIHub 첨부 metadata | 77개 | 포맷정보, 예제, 코드표 등 첨부 링크 |
| APIHub 탐색 기능 | 2개 메서드 | 서비스 목록과 endpoint sample 추출 |

## 타입화 endpoint 4개

`KmaClient`가 직접 편의 메서드와 모델을 제공하는 endpoint입니다.

| 번호 | 메서드 | 서비스 | endpoint | 반환 |
|---:|---|---|---|---|
| 1 | `now()` | `VilageFcstInfoService_2.0` | `getUltraSrtNcst` | `WeatherSnapshot` |
| 2 | `forecast_short()` | `VilageFcstInfoService_2.0` | `getUltraSrtFcst` | `list[ForecastItem]` |
| 3 | `forecast()` | `VilageFcstInfoService_2.0` | `getVilageFcst` | `list[ForecastItem]` |
| 4 | `version()` | `VilageFcstInfoService_2.0` | `getFcstVersion` | raw mapping |

## data.go.kr generic 지원

`DataGoKrClient`는 다음 형태의 KMA gateway endpoint를 호출할 수 있습니다.

```text
http://apis.data.go.kr/1360000/{service}/{operation}
```

예:

```python
client.request("MidFcstInfoService", "getMidFcst", {"stnId": "108", "tmFc": "202605010600"})
```

이 계층은 특정 endpoint를 개별 모델로 구현한 것이 아니라, 표준 data.go.kr envelope를 범용으로 처리합니다. 따라서 “개별 구현 endpoint 개수”에는 넣지 않습니다.

## APIHub 범용 지원

`ApiHubClient`는 다음 형태의 APIHub path를 호출할 수 있습니다.

```text
https://apihub.kma.go.kr/api/...
```

예:

```python
hub.request_path("/api/typ01/url/wrn_reg.php", {"tmfc": "0"})
```

또한 `typ02/openApi` helper를 제공합니다.

```python
hub.open_api("MidFcstInfoService", "getMidFcst", {"stnId": "108", "tmFc": "202605010600"})
```

APIHub는 텍스트, JSON, XML, 이미지, 바이너리 파일 응답이 섞여 있습니다. `pykma`는 endpoint별 반환 스키마를 모두 dataclass로 고정하지는 않지만, 공식 목록에서 확인한 endpoint를 `ApiHubGeneratedClient`의 함수형 메서드로 제공합니다.

예:

```python
from pykma import ApiHubGeneratedClient

hub = ApiHubGeneratedClient.from_env()
response = hub.kma_sfctm2(tm="202605010900", stn="108", help="1")
```

전체 목록은 [docs/apihub-endpoints.md](apihub-endpoints.md)에 있습니다.

## APIHub 조사 기준

2026-05-01에 공식 페이지를 다시 확인했습니다.

- `apiInfo.do` 사용자용 제공내역 분류: 13개
- `apiList.do`에서 실제 접근 가능한 wrapper 생성 대상 분류: 13개
- `apiList.do`에서 확인한 서비스: 59개
- 함수형 래퍼 생성 기준: `apiList.do` 본문 예제 URL, `generateAPIUrl.do`의 `urlList`, API URL을 포함한 텍스트 예제 첨부
- 중복 제거한 path/parameter signature: 470개
- 첨부 자료 metadata: 77개

`apiInfo.do`의 제공내역 번호는 사용자 안내용 번호이고, `apiList.do`의 `seqApi`는 포털 내부 라우팅 id입니다. 두 번호 체계가 같다고 가정하지 않습니다.

이 470개는 `ApiHubGeneratedClient`의 함수형 래퍼로 구현되어 있습니다. 다만 응답 row schema를 endpoint별 dataclass로 모두 고정한 것은 아니며, 응답 종류에 따라 `json()`, `text_table()`, `image()` 등으로 다룹니다.

## 답변 기준

“지금 구현해놓은 API가 몇 개냐”는 질문에는 다음처럼 답합니다.

- **직접 타입화 구현 endpoint는 4개입니다.**
- **APIHub 함수형 래퍼는 470개입니다.**
- **범용 클라이언트까지 포함하면 data.go.kr 임의 service/operation과 APIHub `/api/...` path를 호출할 수 있습니다.**
- **APIHub 470개는 endpoint별 함수 이름을 제공하지만, 모든 응답을 endpoint별 dataclass로 강제 변환하지는 않습니다.**

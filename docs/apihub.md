# KMA APIHub 지원

`apihub.kma.go.kr`는 `data.go.kr`와 별도의 인증키와 응답 규칙을 쓰는 gateway입니다.

| 포털 | 인증 파라미터 | 일반적인 응답 |
|---|---|---|
| data.go.kr KMA gateway | `serviceKey` | JSON/XML REST envelope |
| KMA APIHub | `authKey` | TXT, CSV식 텍스트, JSON, XML, 이미지, 바이너리 파일 |

공식 확인 출처:

- https://apihub.kma.go.kr/apiInfo.do
- https://apihub.kma.go.kr/static/file/%EA%B8%B0%EC%83%81%EC%B2%AD_API%ED%97%88%EB%B8%8C_%EC%82%AC%EC%9A%A9_%EB%B0%A9%EB%B2%95_%EC%95%88%EB%82%B4.pdf
- https://apihub.kma.go.kr/apiList.do
- https://apihub.kma.go.kr/generateAPIUrl.do

## 공식 이용안내 요약

APIHub 소개 페이지는 기상청이 방대한 기상기후데이터를 APIHub로 제공해 사용자가 날씨데이터를 활용할 수 있도록 하는 서비스라고 설명합니다. `kma`는 APIHub 데이터를 저장하거나 재배포하지 않고, 호출과 응답 처리를 돕는 Python client 역할만 합니다.

APIHub를 쓰려면 회원가입 후 인증키를 발급받아야 합니다.

| 회원 구분 | 가입 대상 | 가입 방식 | 일 최대 호출건수 | 일 최대 호출용량 |
|---|---|---|---:|---:|
| 일반회원 | 일반국민 | 포털 온라인 자동승인 | 20,000건 | 5GB |
| 기관회원 | 국가, 지자체, 재난관리기관, 공공기관, 학술·연구기관 | 포털 신청 후 관리자 승인 | 30,000건 | 50GB |

주의할 점:

- 기관회원은 포털에서 기관 회원가입 신청 후 공문으로 가입신청서를 발송해야 합니다.
- 호출건수와 용량은 시스템 상황에 따라 변경될 수 있습니다.
- 인증키는 가입회원 본인만 사용할 수 있으며 양도하거나 대여하면 안 됩니다.
- 발급받은 인증키는 로그인 후 마이페이지에서 확인합니다.

## 공식 제공 범위

`apiInfo.do`의 “API 제공내역”은 사용자용 번호로 13개 분류를 설명합니다. `apiList.do`의 `seqApi` 값은 내부 페이지 라우팅용 id라서 이 번호와 1:1로 같지 않습니다. `kma`의 470개 함수형 래퍼는 실제로 접근 가능한 `apiList.do`/`generateAPIUrl.do` metadata를 기준으로 생성합니다.

| 제공내역 번호 | 분류 | 공식 설명 요약 |
|---:|---|---|
| 1 | 지상관측 | 일기현상, 기온, 강수, 바람, 황사, 자외선 등 |
| 2 | 해양관측 | 파고, 파주기, 파향, 수온 등 |
| 3 | 고층관측 | 상층고도별 기온, 습도, 풍향, 풍속 등 |
| 4 | 레이더 | 강수지역, 강수세기, 이동속도, 영상자료, 데이터파일 |
| 5 | 위성 | 기본 관측데이터와 기상산출물 영상/파일 |
| 6 | 지진/화산 | 지진, 지진해일, 화산 정보 |
| 7 | 태풍 | 태풍과 열대저압부 위치, 중심기압, 이동 정보 |
| 8 | 수치모델 | 전구·지역·국지예보모델 예측데이터 |
| 9 | 예특보 | 초단기, 단기, 중기예보와 기상특보 |
| 10 | 융합기상 | 에너지, 생활, 교통, 산업 등 타분야 융합 데이터 |
| 11 | 항공기상 | 공항 관측, 예보, 특보 |
| 12 | 세계기상 | GTS 기반 전세계 관측 데이터 |
| 13 | 산업특화 | 에너지, 수자원 등 산업분야 묶음 데이터 |

## 공식 유의사항

APIHub 소개 페이지의 유의사항은 다음 운영 전제를 둡니다.

- APIHub 기상기후데이터는 공공누리 적용을 받으며, 유형별 이용조건을 따라야 합니다.
- 서비스 제공범위, 이용횟수, 이용시간은 회원 유형과 활용 목적에 따라 다를 수 있습니다.
- API 서비스는 무료입니다.
- 무중단 운영이 원칙이지만, 서비스 변경, 개선, 시스템 장애 조치 등으로 중단될 수 있습니다.
- 기타 이용 조건은 APIHub 약관을 따릅니다.

라이브러리 관점에서는 호출 실패, 응답 지연, 빈 결과를 모두 정상적인 운영 가능성으로 보고 예외와 원문 응답을 보존해야 합니다.

## URL과 출력 형식

APIHub 사용방법 안내 문서는 호출 URL을 세 부분으로 나눕니다.

1. 도메인주소와 API 소스코드: 고정 path이며 `?` 앞쪽입니다.
2. 입력인자: `?` 뒤쪽 query string이며 인자는 `&`로 구분합니다.
3. 사용자 인증키: `authKey`입니다.

일부 TXT endpoint는 출력 보조 인자를 제공합니다.

| 인자 | 의미 | 구현 참고 |
|---|---|---|
| `disp=0` | CSV 파일 형태, 구분자 `,` | `response.text_table(delimiter=",")` 사용 |
| `help=0` | 헤더정보 미표출 | header 추론이 어려울 수 있음 |
| `help=1` | 출력 변수 설명 또는 헤더정보 표출 | `text_table()`이 comment/header를 찾는 데 유리함 |
| `help=2` | 헤더정보와 시작·종료 지시부 미표출 | row 원문 보존 가능성 고려 |

위성/파일 계열은 `typ=img`, `typ=bin`처럼 다운로드 포맷을 고르는 인자가 있을 수 있습니다. `kma`는 이런 응답을 임의로 텍스트 변환하지 않고 `ApiHubResponse.content`와 `response.image()`를 제공합니다.

## 구현 방식

APIHub는 같은 포털 안에서도 응답 형식이 크게 다릅니다. `kma`는 두 층으로 지원합니다.

| 층 | 클래스 | 용도 |
|---|---|---|
| 범용 호출 | `ApiHubClient` | 임의 `/api/...` path를 직접 호출 |
| 함수형 래퍼 | `ApiHubGeneratedClient` | `apiList.do`에서 확인한 endpoint를 함수 이름으로 호출 |

`ApiHubGeneratedClient`는 `ApiHubClient`를 상속하므로 기존 `request_path()`도 그대로 사용할 수 있습니다.

## 함수형 래퍼 범위

2026-05-01 기준 공식 페이지를 다시 확인해 다음 항목을 생성했습니다.

- APIHub 공식 `apiList.do` 분류: 13개
- 확인한 서비스: 59개
- 생성한 endpoint 함수형 래퍼: **470개**
- 첨부 자료 metadata: **77개**
- 생성 파일: `src/kma/apihub_endpoints.py`
- 전체 함수 목록 문서: [docs/apihub-endpoints.md](apihub-endpoints.md)

응답 종류별 개수:

| 응답 종류 | 개수 | 설명 |
|---|---:|---|
| `text` | 255 | TXT, CSV식 텍스트, 고정폭 텍스트 |
| `structured` | 135 | JSON/XML REST envelope 또는 목록형 응답 |
| `image` | 49 | 이미지 bytes 또는 그래픽 endpoint |
| `file` | 31 | GRIB, NetCDF, 원시자료, 다운로드 계열 |

생성 원천은 세 가지입니다.

- `apiList.do` 본문에 노출된 예제 URL
- `generateAPIUrl.do`의 `urlList` metadata
- API URL을 포함한 텍스트 예제 첨부 파일

## 기본 사용

```python
from kma import ApiHubGeneratedClient

hub = ApiHubGeneratedClient.from_env()  # KMA_APIHUB_AUTH_KEY 또는 KMA_APIHUB_KEY

response = hub.kma_sfctm2(
    tm="202605010900",
    stn="108",
    help="1",
)
print(response.text)
```

실제 서버 테스트용 인증키는 `.env.local`에 보관할 수 있습니다. 이 파일은 `.gitignore`에 포함되어 커밋되지 않습니다.

```text
KMA_APIHUB_AUTH_KEY=<APIHub authKey>
```

홈페이지 예제 값을 채워 호출하려면 `use_sample=True`를 사용합니다. 예제 날짜가 오래되었을 수 있으므로 운영 코드에서는 필요한 인자를 직접 넘기는 방식을 권장합니다.

```python
response = hub.kma_sfctm2(use_sample=True, stn="108")
```

## Endpoint metadata

모든 함수형 래퍼는 `APIHUB_ENDPOINTS`에 metadata를 함께 갖습니다.

```python
from kma import APIHUB_ENDPOINTS

for endpoint in APIHUB_ENDPOINTS:
    print(endpoint.name, endpoint.path, endpoint.parameters, endpoint.response_kind)
```

이름으로 조회하려면 다음처럼 사용합니다.

```python
spec = hub.endpoint("kma_sfctm2")
print(spec.sample_params)
```

## TXT 응답을 Python 데이터로 다루기

일반 TXT endpoint는 `ApiHubResponse.text_table()`로 주석, header, row를 분리할 수 있습니다.

```python
response = hub.kma_sfctm2(tm="202605010900", stn="108", help="1")
table = response.text_table()

print(table.headers)
print(table.rows[:3])
print(table.comments[:3])
```

CSV식 응답은 delimiter를 지정합니다.

```python
table = response.text_table(delimiter=",")
```

TXT 포맷은 endpoint마다 완전히 같지 않습니다. header를 안정적으로 찾지 못하면 `rows`는 `{"_raw": "원문 한 줄"}` 형태로 반환합니다.

## 이미지 응답을 Python 데이터로 다루기

이미지/그래픽 endpoint는 `image_endpoint()` 또는 `response.image()`를 사용합니다.

```python
image = hub.image_endpoint("api_iwa_img_url_api_ret_grid_img", use_sample=True)
print(image.format, image.width, image.height)
content = image.content
```

`image.format`, `image.width`, `image.height`는 PNG/GIF/JPEG header에서 감지합니다. 포맷을 알 수 없는 바이너리는 `None`으로 둡니다.

포맷정보, 예제 파일, 코드표 같은 APIHub 첨부 링크는 `APIHUB_ATTACHMENTS`에 metadata로 보관합니다.

```python
from kma import APIHUB_ATTACHMENTS

for attachment in APIHUB_ATTACHMENTS:
    if attachment.kind in {"format", "sample"}:
        print(attachment.service_name, attachment.title, attachment.filename)
```

## 이름 없는 query string

일부 legacy 그래픽 endpoint는 정상적인 `key=value` query가 아니라 다음처럼 순서형 값을 씁니다.

```text
...?202305031000&0&108,419&m&_DT=RSW:AWSCHART&authKey=...
```

이런 endpoint는 `arg1`, `arg2`처럼 순서형 인자로 래핑했습니다.

```python
response = hub.aws3_nph_awsm_tms_h06(
    arg1="202305031000",
    arg2="0",
    arg3="108,419",
    arg4="m",
    arg5="108,419",
    arg6="kh",
    _DT="RSW:AWSCHART",
)
```

`ApiHubGeneratedClient`는 이 경우 `requests`의 `params=`를 쓰지 않고 query string을 직접 조립해 순서를 보존합니다.

## 범용 호출

목록에 없는 새 endpoint나 실험적 path는 `request_path()`로 직접 호출합니다.

```python
from kma import ApiHubClient

hub = ApiHubClient.from_env()
response = hub.request_path(
    "/api/typ01/url/wrn_reg.php",
    {"tmfc": "0"},
)
```

`typ02/openApi` 형식은 `open_api()` helper를 사용할 수 있습니다.

```python
response = hub.open_api(
    "MidFcstInfoService",
    "getMidFcst",
    {"stnId": "108", "tmFc": "202605010600"},
)
data = response.json()
```

기본값:

- `pageNo=1`
- `numOfRows=10`
- `dataType=JSON`

## 탐색 기능

`discover_services()`는 공식 분류 id별 APIHub 서비스 목록을 가져옵니다.

```python
services = hub.discover_services()
```

`discover_endpoints()`는 서비스 페이지의 예제 URL을 추출합니다.

```python
endpoints = hub.discover_endpoints(category_id=10, service_id=288)
```

탐색 기능은 live 포털 구조를 읽는 도구입니다. 패키지에 포함된 함수형 래퍼는 `tools/update_apihub_endpoints.py`로 생성한 고정 snapshot입니다.

## 생성 스크립트

APIHub 목록을 갱신하려면 다음을 실행합니다.

```bash
python -X utf8 tools/update_apihub_endpoints.py
```

이 스크립트는 실제 데이터 endpoint를 호출하지 않고 포털 문서와 URL 발행 metadata만 읽습니다.

2026-05-06 재대조 기준으로 공식 목록 재수집 결과는 로컬 함수형 래퍼 470개, 첨부 metadata 77개와 일치했습니다. APIHub의 보조 `generateAPIUrl.do`가 일시적으로 실패하는 경우가 있어, 생성기는 해당 보조 metadata 실패만 건너뛰고 `apiList.do` 본문과 첨부 예제 수집을 계속합니다.

## 구현 주의사항

- `authKey`를 로그나 커밋에 남기지 않습니다.
- `ApiHubResponse.url`은 `authKey` 값을 `***`로 가린 URL을 보관합니다.
- HTTP 401/403은 `KmaAuthError`로 변환합니다. HTTP 403은 키 형식 문제뿐 아니라 APIHub 활용신청/승인 상태 문제일 수 있습니다.
- APIHub endpoint가 항상 JSON이라고 가정하지 않습니다.
- TXT 응답은 endpoint마다 header 형식이 다를 수 있습니다.
- 이미지 bytes를 `text`로 강제 파싱하지 않습니다.
- 이름 없는 query string은 `params=`로 재현할 수 없으므로 순서를 보존해 직접 조립합니다.
- 예제 URL의 `authKey`는 사용하지 않고, 사용자가 제공한 `authKey`만 붙입니다.

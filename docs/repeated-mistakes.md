# 반복 실수 방지 기록

`kma`를 만들면서 반복되기 쉬운 실수를 기록합니다. 이 문서에 있는 문제가 다시 발견되면 테스트를 추가하고, 해결 규칙도 함께 갱신합니다.

## serviceKey 인코딩

**실수:** 이미 URL 인코딩된 service key를 `requests`의 `params=`에 넣음.

**증상:** 키가 맞아 보이는데 KMA가 `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`를 반환합니다.

**규칙:** data.go.kr 경로는 `params=`를 사용하므로 Decoding 키를 기준으로 합니다. URL 문자열을 직접 만들 때만 Encoding 키를 사용합니다.

**방지 테스트:** 클라이언트 테스트에서 `serviceKey`가 일반 요청 파라미터로 전달되는지 확인합니다.

## base_time은 현재 시간이 아님

**실수:** 현재 시각을 그대로 `base_time`으로 사용함.

**증상:** 빈 `items`, `NODATA_ERROR`, 발표 경계 시각에서 흔들리는 테스트.

**규칙:** 항상 `src/kma/time_utils.py`의 helper를 사용합니다.

| Endpoint | helper |
|---|---|
| `getUltraSrtNcst` | `latest_ultra_srt_ncst_base()` |
| `getUltraSrtFcst` | `latest_ultra_srt_fcst_base()` |
| `getVilageFcst` | `latest_vilage_base()` |

**방지 테스트:** 발표 지연, 전날 경계, naive KST 해석, UTC 변환을 테스트합니다.

## `nx`/`ny`는 위도/경도가 아님

**실수:** 위도/경도를 `nx`/`ny`로 넣거나 격자값을 지리 좌표로 해석함.

**증상:** 엉뚱한 위치의 예보를 조회하거나 좌표 검증 오류가 발생합니다.

**규칙:** WGS84는 `LatLon` 또는 `lat`/`lon`, KMA DFS 격자는 `GridPoint` 또는 `nx`/`ny`를 사용합니다. 외부 프로그램과 연결할 때는 `location=LatLon(...)`, `location=GridPoint(...)`, `normalize_location()`을 우선 사용합니다.

**방지 테스트:** `src/kma/grid.py`가 WGS84 범위와 공식 격자 범위를 검증하고, `tests/test_locations.py`와 클라이언트 테스트가 혼합/부분 좌표를 거부합니다.

## `PCP`, `SNO`는 항상 숫자가 아님

**실수:** 모든 예보값에 `float()`를 적용함.

**증상:** `1.0mm 미만`, `강수없음`, `30.0~50.0mm` 같은 라벨에서 `ValueError`가 발생합니다.

**규칙:** `ForecastItem.value`에서는 `PCP`, `SNO` 문자열을 보존합니다. 대표 숫자가 필요할 때만 `parse_amount()`를 사용합니다.

**방지 테스트:** `PCP`, `SNO` 라벨이 문자열로 유지되는지, `parse_amount()`가 주요 한국어 범위 라벨을 처리하는지 확인합니다.

## `PTY` 코드는 endpoint마다 다름

**실수:** 모든 endpoint에 하나의 강수형태 표를 사용함.

**증상:** 초단기실황에서 `PTY=4`를 잘못 해석하거나, 예보 endpoint에서 `PTY=5`를 잘못 해석합니다.

**규칙:** endpoint-aware 매핑을 사용합니다.

- `getUltraSrtNcst`: `0`, `1`, `2`, `3`, `5`, `6`, `7`
- `getUltraSrtFcst` / `getVilageFcst`: `0`, `1`, `2`, `3`, `4`

**방지 테스트:** endpoint별 `PTY` 라벨 동작을 테스트합니다.

## 문자열 코드 오타를 public API에 퍼뜨리지 않기

**실수:** 외부 프로그램에서 `"TMP"`, `"PTY"`, `"getVilageFcst"` 같은 문자열을 여러 곳에 직접 적음.

**증상:** 오타가 런타임까지 숨어 있다가 라벨/단위 매핑이 누락되거나 잘못된 endpoint helper를 호출합니다.

**규칙:** 새 public 예제와 내부 구현은 가능한 경우 `WeatherCategory`, `KmaEndpoint`, `SkyCode`, `ObservedPrecipitationType`, `ForecastPrecipitationType` enum을 사용합니다. 알 수 없는 새 KMA category는 문자열 원문으로 보존합니다.

**방지 테스트:** enum 값이 KMA wire value와 같은지, code helper가 enum과 문자열을 모두 처리하는지 테스트합니다.

## KMA 응답 구조를 사용자에게 새게 하지 않기

**실수:** `KeyError`, `TypeError`, raw dict, 조용한 빈 성공을 그대로 흘려보냄.

**증상:** 사용자가 KMA의 중첩 구조인 `response.header.body.items.item`을 직접 이해해야 합니다.

**규칙:** 잘못된 envelope/item은 `KmaParseError`로, `resultCode != "00"`은 typed KMA exception으로 변환합니다.

**방지 테스트:** 잘못된 envelope, 누락된 `items`, 잘못된 forecast item, 단일 dict 응답, result code 매핑을 테스트합니다.

## 예보 row를 시간축 데이터로 착각하지 않기

**실수:** `ForecastItem` 배열을 이미 시간대별 객체라고 가정하고 프론트엔드에 그대로 넘김.

**증상:** 같은 `forecast_at`에 `TMP`, `SKY`, `PTY`, `POP` 같은 row가 여러 개 흩어져 있어 화면 코드가 category별 조립을 반복하거나 렌더링이 비효율적입니다.

**규칙:** 시간대별 응답이 필요하면 `pivot_forecast_items()`로 `ForecastTimepoint` 목록을 만든 뒤 `values`, `labels`, `units`를 사용합니다. 단, 원문 category row가 필요한 저장/감사 경계에서는 `ForecastItem.raw` 또는 `ForecastTimepoint.raw_items`를 보존합니다.

**방지 테스트:** `tests/test_timeline.py`에서 같은 시간대와 격자의 row가 하나의 `ForecastTimepoint`로 묶이는지 검증합니다.

## 한국어 텍스트는 UTF-8로 유지

**실수:** PowerShell mojibake만 보고 파일이 깨졌다고 판단함.

**증상:** 터미널 출력은 깨져 보이지만 파일은 정상 UTF-8일 수 있습니다.

**규칙:** Python의 `Path(...).read_text(encoding="utf-8")`나 문자열 비교 테스트로 확인합니다.

**방지 테스트:** `맑음`, `소나기`, `빗방울`, `강수없음` 같은 실제 한국어 라벨을 테스트합니다.

## APIHub와 data.go.kr는 다름

**실수:** APIHub에 `serviceKey`를 보내거나 data.go.kr에 `authKey`를 보냄.

**증상:** 다른 포털에서는 유효한 키인데 인증 실패가 발생합니다.

**규칙:** `ApiHubClient`는 `authKey`, `DataGoKrClient`와 `KmaClient`는 `serviceKey`를 사용합니다.

**방지 테스트:** 두 범용 클라이언트가 올바른 인증 파라미터를 만드는지 확인합니다.

## data.go.kr 인증 파라미터 표기 차이를 무시하지 않기

**실수:** 모든 data.go.kr 문서가 인증키 이름을 같은 대소문자로 표기한다고 가정함.

**증상:** 어떤 문서는 `serviceKey`, 어떤 문서는 `ServiceKey`로 표시합니다. gateway가 대소문자를 엄격히 처리하는 서비스라면 인증 실패가 날 수 있습니다.

**규칙:** 기본값은 실사용 검증된 `serviceKey`를 쓰되, 필요하면 `DataGoKrClient(..., service_key_param="ServiceKey")`로 바꿉니다.

**방지 테스트:** `tests/test_datagokr.py`에서 인증 파라미터 이름을 설정할 수 있는지 검증합니다.

## data.go.kr 검색 결과를 전부 기상청 API로 보지 않기

**실수:** 공공데이터포털에서 `기상청` 키워드로 검색된 모든 API를 기상청 API로 간주함.

**증상:** 경기도, 농촌진흥청, 행정안전부, 법제처, 한국도로공사 같은 다른 기관의 API가 KMA 클라이언트 카탈로그에 섞입니다.

**규칙:** `KMA_DATA_GOKR_DATASETS`는 제목이 `기상청`으로 시작하는 항목만 포함합니다. 관련 날씨 API라도 제공 기관과 인증 규칙이 다르면 별도 클라이언트로 다룹니다.

**방지 테스트:** `tests/test_datagokr.py`에서 카탈로그 항목 수와 제목 prefix를 검증하고, 대표 비기상청 기관명이 들어가지 않는지 확인합니다.

## 한국도로공사 휴게소 날씨 결측값을 실제 값으로 취급하지 않기

**실수:** `-99`, `-99.0`, `-99.000000`을 실제 기온, 강수량, 적설량으로 사용함.

**증상:** 휴게소 날씨 화면이나 통계에서 비현실적인 값이 나타납니다.

**규칙:** `ExpresswayRestAreaWeatherClient`는 `RestAreaWeather` 모델 필드에서 `-99` 계열 값을 `None`으로 정규화합니다. 원문 확인이 필요하면 `raw`를 봅니다.

**방지 테스트:** `tests/test_expressway.py`에서 강수강도, 적설 등 결측 sentinel이 `None`이 되는지 검증합니다.

## 한국도로공사 API를 KMA/data.go.kr 인증 규칙과 섞지 않기

**실수:** 휴게소별 날씨 API에 `serviceKey`나 `authKey`를 보냄.

**증상:** 인증 실패 또는 빈 응답이 발생합니다.

**규칙:** 휴게소별 날씨 API는 한국도로공사 `data.ex.co.kr` gateway를 사용하며 인증 파라미터는 `key`입니다. 로컬 환경변수는 `EXPRESSWAY_API_KEY`를 사용합니다.

**방지 테스트:** `tests/test_expressway.py`에서 최종 요청 파라미터가 `key`, `type`, `sdate`, `stdHour`인지 검증합니다.

## APIHub는 항상 JSON이 아님

**실수:** 모든 APIHub endpoint에 `.json()`이나 dataclass 파싱을 강제함.

**증상:** 텍스트 표, 이미지 endpoint, 파일 다운로드에서 파싱 오류가 발생합니다.

**규칙:** `ApiHubClient`는 `ApiHubResponse`를 반환하고, 사용자는 endpoint별로 `text`, `content`, `json()` 중 알맞은 방식을 선택합니다.

**방지 테스트:** APIHub 테스트는 텍스트 응답을 사용하고, JSON 전용 테스트에서만 `json()`을 호출합니다.

## APIHub legacy query string을 mapping으로 바꾸지 않기

**실수:** `?202305031000&0&108,419...`처럼 이름 없는 query string을 `{"202305031000": "", "0": ""}` 같은 mapping으로 바꿈.

**증상:** 그래픽 endpoint URL이 공식 예제와 달라지고, 서버가 이미지를 반환하지 않거나 다른 결과를 반환할 수 있습니다.

**규칙:** 이름 없는 query 값은 `arg1`, `arg2`처럼 순서형 인자로 보존하고 `ApiHubClient.request_query_parts()`로 직접 query string을 조립합니다.

**방지 테스트:** `tests/test_apihub.py`와 `tests/test_apihub_endpoints.py`에서 bare query 순서와 최종 URL을 검증합니다.

## 해수욕장 일출일몰 API의 `Base_date`를 `base_date`로 바꾸지 않기

**실수:** `BeachInfoservice/getSunInfoBeach`도 다른 해수욕장 endpoint처럼 `base_date`를 보낸다고 가정함.

**증상:** 일출일몰 조회에서 필수 파라미터 누락 오류가 발생할 수 있습니다.

**규칙:** 공공데이터포털 Swagger 기준으로 일출일몰 endpoint만 날짜 파라미터가 `Base_date`입니다. `DataGoKrClient.beach_sun_info()`는 이 이름을 그대로 사용합니다.

**방지 테스트:** `tests/test_datagokr.py`에서 `beach_sun_info()`가 최종 요청 파라미터에 `Base_date`를 보내고 metadata의 `base_date`도 채우는지 검증합니다.

## APIHub 목록은 본문만 보면 누락됨

**실수:** `apiList.do` 본문 예제 URL만 긁고 `generateAPIUrl.do`의 `urlList`나 텍스트 예제 첨부를 확인하지 않음.

**증상:** 천리안 2A호 일부 동적 wildcard endpoint나 수치모델 그래픽 예제 endpoint가 함수형 래퍼에서 빠집니다.

**규칙:** `tools/update_apihub_endpoints.py`는 `apiList.do`, `generateAPIUrl.do`, API URL을 포함한 텍스트 예제 첨부를 함께 사용합니다.

**방지 테스트:** 생성된 endpoint 개수 470개와 대표 함수(`kma_sfctm2`, `aws3_nph_awsm_tms_h06`, `api_iwa_img_url_api_ret_grid_img`)를 검증합니다.

## 실서버 테스트에서 인증키를 출력하거나 커밋하지 않기

**실수:** 라이브 테스트 실패 traceback, URL, fixture, 문서 예시에 실제 `authKey`나 `serviceKey`를 남김.

**증상:** 실패 로그나 커밋 diff에 인증키가 노출됩니다. 특히 `requests.HTTPError`는 원래 요청 URL을 포함할 수 있습니다.

**규칙:** 로컬 키는 `.env.local`에만 저장하고, 이 파일은 `.gitignore`로 관리합니다. `ApiHubResponse.url`은 `authKey`/`serviceKey` 값을 `***`로 가리고, HTTP 401/403 예외는 원본 `HTTPError`를 chaining하지 않습니다.

**방지 테스트:** URL redaction 테스트와 APIHub 403 매핑 테스트에서 실제 키가 예외 문자열에 포함되지 않는지 확인합니다.

## `.env.local`에 키를 추가할 때 줄바꿈을 망가뜨리지 않기

**실수:** 새 인증키를 기존 줄 끝에 붙여 `DATA_GOKR_SERVICE_KEY=...EXPRESSWAY_API_KEY=...`처럼 만듦.

**증상:** 원래 잘 되던 data.go.kr 실서버 테스트가 인증 실패를 냅니다.

**규칙:** `.env.local`은 반드시 한 줄에 하나의 `KEY=value`만 둡니다. 키를 추가한 뒤에는 key 이름 목록만 확인하고 값은 출력하지 않습니다.

**방지 테스트:** live test loader는 `.env.local`을 줄 단위로 읽습니다. 실서버 테스트 전 key 이름 목록과 secret scan을 확인합니다.

## APIHub 403을 단순 키 오류로만 보지 않기

**실수:** HTTP 403이 나오면 키 문자열이 틀렸다고만 판단함.

**증상:** APIHub 서버에는 도달했지만 “활용신청” 또는 권한 관련 메시지가 반환됩니다.

**규칙:** 401/403은 `KmaAuthError`로 다루되, 포털 활용신청/승인 상태도 함께 확인합니다. 실서버 integration 테스트는 APIHub 키가 endpoint 권한을 갖지 못한 경우 명확한 이유로 skip합니다.

**방지 테스트:** `tests/test_live_services.py`는 `KMA_RUN_LIVE=1`이 있을 때만 실제 서버를 호출하고, APIHub 권한 403과 data.go.kr 성공 경로를 분리해 검증합니다.

## 문서에 로컬 절대 경로를 남기지 않기

**실수:** 문서에 작업자 로컬 절대 경로나 Windows 전용 파일 구분자를 남김.

**증상:** 다른 환경에서 그대로 따라 할 수 없고, 프로젝트 문서가 특정 PC 구조에 묶입니다.

**규칙:** 파일 위치 정보는 `src/kma/client.py`, `docs/testing.md`, `tests/test_live_services.py::test_name`처럼 프로젝트 루트 기준 상대 경로와 `/` 구분자로 작성합니다. PowerShell provider 경로(`Env:\KMA_RUN_LIVE`)처럼 파일 위치가 아닌 명령 문법은 예외입니다.

**방지 테스트:** 문서 변경 후 `.md` 파일에서 로컬 절대 경로와 Windows식 파일 경로 표기가 남지 않았는지 검색합니다.

## Python 내부 문서를 영어로 되돌리지 않기

**실수:** 새 모듈이나 생성 템플릿에 영어 docstring을 추가해 Python 내부 문서 언어가 섞임.

**증상:** `help(kma...)`, IDE hover, 생성된 API 문서에서 한글/영어 설명이 섞여 프로젝트 문서 정책과 어긋납니다.

**규칙:** Python docstring과 내부 설명 문구는 한글로 작성합니다. 코드 식별자, API 파라미터 이름, wire value는 원문을 유지합니다. 생성 파일은 원본 템플릿(`tools/update_apihub_endpoints.py`)도 함께 고칩니다.

**방지 테스트:** `src/kma/`와 `tools/`의 docstring을 스캔하고, 생성 파일을 다시 만들 때 영어 템플릿이 되살아나지 않는지 확인합니다.

## `rg` 실행 권한 오류를 빈 검색 결과로 착각하지 않기

**실수:** `rg --files`나 `rg "pattern"`이 `Access is denied`로 실패했는데 검색 결과가 없다고 판단함.

**증상:** 파일 목록이나 검색 결과가 누락되어 문서/코드 갱신 범위를 잘못 잡습니다.

**규칙:** 이 환경에서 `rg`가 실행 권한 문제로 실패하면 PowerShell native 명령으로 우회합니다. 파일 목록은 `Get-ChildItem -Recurse -File`, 이름 검색은 `Get-ChildItem -Recurse -Filter`, 내용 검색은 `Select-String`을 사용합니다.

**우회 예시:**

```powershell
Get-ChildItem -Path kma,tests -File -Recurse |
    ForEach-Object { $_.FullName.Substring((Get-Location).Path.Length + 1) }

Get-ChildItem -Path . -Recurse -File -Include *.md,*.py |
    Select-String -Pattern "문서"
```

**방지 테스트:** `rg` 실패 메시지를 본 뒤에는 PowerShell 우회 명령으로 같은 범위를 다시 확인하고, 검색 실패를 빈 결과로 기록하지 않습니다.

## PowerShell 출력 깨짐을 UTF-8 파일 깨짐으로 오판하지 않기

**실수:** UTF-8 Markdown 파일을 PowerShell 기본 출력으로 읽어 글자가 깨져 보이는 것을 실제 파일 손상으로 판단함.

**증상:** 정상 한글 문서를 불필요하게 고치거나, 깨진 출력 기준으로 잘못된 diff를 만듭니다.

**규칙:** 한글 문서를 확인할 때는 PowerShell 출력 encoding과 파일 encoding을 명시합니다. 특히 Markdown은 `Get-Content -Encoding UTF8`로 읽고, 필요하면 console output encoding도 UTF-8로 맞춥니다.

**확인 예시:**

```powershell
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
Get-Content -Path docs/repeated-mistakes.md -Encoding UTF8
```

**방지 테스트:** 한글이 깨져 보이면 먼저 UTF-8 명시 명령으로 다시 읽고, 파일 자체가 깨졌는지는 diff나 테스트 결과로 확인합니다.

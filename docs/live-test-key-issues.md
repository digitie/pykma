# 라이브 테스트 서비스키 이슈 정리

`KMA_RUN_LIVE=1`로 실서버 라이브 테스트를 돌릴 때, **코드 결함이 아니라 인증키 권한/구독 문제**로 실패하거나 skip되는 엔드포인트를 기록한다. data.go.kr은 OpenAPI마다 별도 "활용신청"(구독) 승인이 필요하므로, 같은 `serviceKey`라도 일부 서비스는 접근이 거부될 수 있다.

테스트는 이런 경우 `KmaAuthError`(HTTP 403)를 잡아 `pytest.skip`으로 처리한다. 즉 라이브 스위트는 green을 유지하되, 해당 엔드포인트의 실서버 shape 검증은 키 구독 후로 미뤄진다. 타입/파싱 로직 자체는 mock 테스트로 검증된다.

## 갱신 방법

```powershell
$env:KMA_RUN_LIVE="1"
python -m pytest tests/test_live_services.py -v
Remove-Item Env:\KMA_RUN_LIVE
```

`SKIPPED` 사유에 `not authorized for this service key`가 보이면 아래 표를 갱신한다.

## 현재 상태 (2026-05-31, claude 확인)

| 게이트웨이 | 서비스 / 엔드포인트 | 증상 | 원인(추정) | 조치 |
|---|---|---|---|---|
| data.go.kr | `AsosDalyInfoService/getWthrDataList` | HTTP 403 `KmaAuthError` | 현재 `DATA_GO_KR_SERVICE_KEY`가 ASOS 일자료 서비스에 활용신청 미승인 | data.go.kr에서 해당 서비스 활용신청 후 재검증 |
| data.go.kr | `AsosHourlyInfoService/getWthrDataList` | HTTP 403 `KmaAuthError` | 현재 `DATA_GO_KR_SERVICE_KEY`가 ASOS 시간자료 서비스에 활용신청 미승인 | data.go.kr에서 해당 서비스 활용신청 후 재검증 |
| data.go.kr | `VilageFcstMsgService/getLandFcst` (단기예보 통보문) | HTTP 403 `KmaAuthError` | 현재 `DATA_GO_KR_SERVICE_KEY`가 통보문 서비스에 활용신청 미승인 | data.go.kr에서 해당 서비스 활용신청 후 재검증 |

## 정상 동작 확인된 엔드포인트 (참고)

| 게이트웨이 | 서비스 / 엔드포인트 | 비고 |
|---|---|---|
| data.go.kr | `VilageFcstInfoService_2.0/getUltraSrtNcst` | 초단기실황, 정상 |
| data.go.kr | `VilageFcstInfoService_2.0/getVilageFcst` (단기예보) | `KmaClient.forecast_short()`로 정상 |
| data.go.kr | `MidFcstInfoService/getMidLandFcst` (중기육상예보) | 구독됨, 정상 (`reg_id` 필요, `tmFc`는 06/18시 발표) |
| APIHub | `fct_shrt_reg`, `fct_medm_reg`, `wrn_reg`, `ifs_fct_pstt` | text/table 응답, 정상 |
| APIHub | `FcstZoneInfoService/getFcstZoneCd` | JSON 응답, 정상 |
| data.go.kr | `WthrWrnInfoService/getWthrWrnList` | 구독됨. **조회 기간은 현재 기준 최대 6일** (초과 시 resultCode 99), 활성 특보가 없으면 resultCode 03 `NO_DATA` 반환 |

> 참고: HTTP 403이 아니라 응답 본문에 `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`(resultCode 30) 등이 오는 경우는 인코딩/이중 인코딩 문제일 수 있다. `params=`로 보낼 때는 **Decoding 키**를 사용한다 (`docs/resume.md`의 "알려진 함정" 참고).

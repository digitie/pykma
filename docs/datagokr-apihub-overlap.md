# data.go.kr/APIHub 중복 확인

이 문서는 `KMA_DATA_GOKR_DATASETS`와 `APIHUB_ENDPOINTS`를 비교해 data.go.kr gateway와 APIHub 사이의 중복을 정리합니다.

## 비교 기준

- 확인일: 2026-05-07
- data.go.kr 기준: 공공데이터포털 `기상청` 오픈 API 검색 전체 페이지에서 제목이 `기상청`으로 시작하는 항목 86개
- APIHub 기준: `tools/update_apihub_endpoints.py`로 2026-05-06 생성한 `APIHUB_ENDPOINTS` 470개
- 정확 중복: data.go.kr `{service}/{operation}`이 APIHub `/api/typ02/openApi/{service}/{operation}`와 같은 경우
- APIHub LINK: data.go.kr 검색 결과가 기존 `serviceKey` gateway가 아니라 APIHub로 연결되는 항목

주제나 원천 자료가 비슷해도 service/operation이 다르면 정확 중복에 넣지 않습니다. 예를 들어 ASOS, 특보, 태풍정보 일부는 APIHub의 legacy TXT endpoint와 의미상 겹칠 수 있지만, 이 문서의 정확 중복 표는 같은 `{service}/{operation}`만 셉니다.

## 요약

| 항목 | 개수 | 비고 |
|---|---:|---|
| data.go.kr 기상청 카탈로그 | 86 | 제목 prefix가 `기상청`인 항목만 포함 |
| data.go.kr `serviceKey` gateway dataset | 38 | `{service}/{operation}` 호출 가능 |
| data.go.kr gateway operation | 160 | 포털 상세기능 기준 |
| APIHub 전체 wrapper | 470 | `APIHUB_ENDPOINTS` 전체 |
| APIHub `typ02/openApi` wrapper | 122 | data.go.kr REST gateway와 비교 가능한 APIHub wrapper |
| 정확 중복 dataset | 21 | 하나 이상의 operation이 같은 service/operation으로 존재 |
| 정확 중복 operation | 109 | data.go.kr gateway operation 중 APIHub에도 같은 path가 있는 항목 |
| 정확 중복 없는 gateway operation | 51 | APIHub `typ02/openApi`에 같은 service/operation 없음 |
| data.go.kr APIHub LINK dataset | 48 | 포털 검색에는 보이나 `serviceKey` gateway가 아님 |

## 정확 중복 dataset

| data.go.kr id | 제목 | service | 중복 | APIHub 중복 operation | data.go.kr에만 있는 operation |
|---|---|---|---:|---|---|
| `15084084` | 기상청_단기예보 조회서비스 | `VilageFcstInfoService_2.0` | 4/4 전체 | `getUltraSrtNcst`, `getUltraSrtFcst`, `getVilageFcst`, `getFcstVersion` | - |
| `15059468` | 기상청_중기예보 조회서비스 | `MidFcstInfoService` | 4/4 전체 | `getMidFcst`, `getMidLandFcst`, `getMidTa`, `getMidSeaFcst` | - |
| `15058629` | 기상청_단기예보 통보문 조회서비스 | `VilageFcstMsgService` | 3/3 전체 | `getWthrSituation`, `getLandFcst`, `getSeaFcst` | - |
| `15000420` | 기상청_지진정보 조회서비스 | `EqkInfoService` | 4/4 전체 | `getEqkMsg`, `getEqkMsgList`, `getTsunamiMsg`, `getTsunamiMsgList` | - |
| `15043562` | 기상청_일기도 조회서비스 | `WthrChartInfoService` | 2/2 전체 | `getSurfaceChart`, `getAuxillaryChart` | - |
| `15057111` | 기상청_예보구역정보 조회서비스 | `FcstZoneInfoService` | 1/1 전체 | `getFcstZoneCd` | - |
| `15057260` | 기상청_지상기상월보 조회서비스 | `SfcMtlyInfoService` | 8/8 전체 | `getNote`, `getSfcStnLstTbl`, `getMmSumry`, `getMmSumry2`, `getDailyWthrData`, `getAirNote`, `getrAirStnLstTbl`, `getDailyAirData` | - |
| `15059244` | 기상청_위성자료(경량화) 조회서비스 | `WthrSatlitInfoService` | 10/10 전체 | `getGk2aIrAll`, `getGk2aNrAll`, `getGk2aSwAll`, `getGk2aViAll`, `getGk2aWvAll`, `getGk2aIrArea`, `getGk2aNrArea`, `getGk2aSwArea`, `getGk2aViArea`, `getGk2aWvArea` | - |
| `15058804` | 기상청_항공기상전문 조회서비스 | `AmmService` | 4/5 부분 | `getTaf`, `getWarning`, `getSigmet`, `getAirmet` | `getMetar` |
| `15077314` | 기상청_위성자료 경량화 조회서비스(기상산출물) | `CloudSatlitInfoService` | 10/10 전체 | `getGk2acldAll`, `getGk2aappsAll`, `getGk2afogAll`, `getGk2adcoewAll`, `getGk2aclaAll`, `getGk2acldArea`, `getGk2aappsArea`, `getGk2afogArea`, `getGk2adcoewArea`, `getGk2aclaArea` | - |
| `15095158` | 기상청_세계기상전문(GTS)_조회서비스 | `GtsInfoService` | 4/4 전체 | `getBuoy`, `getGtsStn`, `getSynop`, `getTemp` | - |
| `15110052` | 기상청_국내 공항기상정보 조회서비스 | `AirPortService` | 1/1 전체 | `getAirPort` | - |
| `15058845` | 기상청_지상기상연보 조회서비스 | `SfcYearlyInfoService` | 14/14 전체 | `getNote`, `getSfcStnLstTbl`, `getAirStnInfo`, `getAirStnInfo2`, `getAirStnInfo3`, `getrAirStnLstTbl`, `getYearSumry`, `getYearSumry2`, `getAvgTaAnamaly`, `getRnAnamaly`, `getStnPhnmnData`, `getStnPhnmnData2`, `getStnPhnmnData3`, `getTyphoonList` | - |
| `15058466` | 기상청_방재기상월보 조회서비스 | `AwsMtlyInfoService` | 4/4 전체 | `getNote`, `getAwsStnLstTbl`, `getMmSumry`, `getDailyAwsData` | - |
| `15059060` | 기상청_레이더자료(경량화) 조회서비스 | `WthrRadarInfoService` | 4/4 전체 | `getCompCappiQcdAll`, `getCompCappiQcdArea`, `getSiteCappiQcdAll`, `getSiteCappiQcdArea` | - |
| `15095109` | 기상청_국내 공항 이륙예보 조회서비스 | `AirInfoService` | 1/1 전체 | `getAirInfo` | - |
| `15059455` | 기상청_항공기상전문(IWXXMVer.2.0) 조회서비스 | `AmmIwxxmService` | 4/4 전체 | `getMetar`, `getTaf`, `getSigmet`, `getAirmet` | - |
| `15059094` | 기상청_해양기상월보 조회서비스 | `SeaMtlyInfoService` | 14/14 전체 | `getNote`, `getBuoyLstTbl`, `getLhawsLstTbl`, `getWaveBuoyLstTbl`, `getObsOpenYear`, `getBuoyMmSumry`, `getBuoyMmSumry2`, `getDailyBuoy`, `getLhawsMmSumry`, `getLhawsMmSumry2`, `getDailyLhaws`, `getWaveBuoyMmSumry`, `getWaveBuoyMmSumry2`, `getDailyWaveBuoy` | - |
| `15059100` | 기상청_세계공항 항공기상전문 조회서비스 | `AftnAmmService` | 3/3 전체 | `getMetar`, `getTaf`, `getSigmet` | - |
| `15059466` | 기상청_방재기상연보 조회서비스 | `AwsYearlyInfoService` | 4/4 전체 | `getNote`, `getAwsStnLstTbl`, `getYearSumry`, `getStnbyMmSumry` | - |
| `15058088` | 기상청_고층기상월보 조회서비스 | `UppMtlyInfoService` | 6/6 전체 | `getNote`, `getUppLstTbl`, `getStdIsbrsfValue`, `getMaxWind`, `getTaHmLevel`, `getWindLevel` | - |

## 정확 중복 없는 data.go.kr gateway dataset

아래 항목은 data.go.kr `serviceKey` gateway에는 있지만, 현재 생성된 APIHub `typ02/openApi` wrapper에는 같은 `{service}/{operation}` 조합이 없습니다.

| data.go.kr id | 제목 | service | operation 수 | operation |
|---|---|---|---:|---|
| `15059093` | 기상청_지상(종관, ASOS) 일자료 조회서비스 | `AsosDalyInfoService` | 1 | `getWthrDataList` |
| `15057210` | 기상청_지상(종관, ASOS) 시간자료 조회서비스 | `AsosHourlyInfoService` | 1 | `getWthrDataList` |
| `15000415` | 기상청_기상특보 조회서비스 | `WthrWrnInfoService` | 10 | `getWthrWrnList`, `getWthrWrnMsg`, `getWthrInfoList`, `getWthrInfo`, `getWthrBrkNewsList`, `getWthrBrkNews`, `getWthrPwnList`, `getWthrPwn`, `getPwnCd`, `getPwnStatus` |
| `15056912` | 기상청_관광코스별 관광지 상세 날씨 조회서비스 | `TourStnInfoService1` | 2 | `getTourStnVilageFcst1`, `getCityTourClmIdx1` |
| `15085288` | 기상청_생활기상지수 조회서비스(3.0) | `LivingWthrIdxServiceV4` | 3 | `getSenTaIdxV4`, `getUVIdxV4`, `getAirDiffusionIdxV4` |
| `15043565` | 기상청_태풍정보 조회서비스 | `TyphoonInfoService` | 3 | `getTyphoonInfo`, `getTyphoonInfoList`, `getTyphoonFcst` |
| `15058167` | 기상청_위성영상 조회서비스 | `SatlitImgInfoService` | 1 | `getInsightSatlit` |
| `15057966` | 기상청_CCTV 기반 도로날씨정보 조회서비스 | `RoadWthrInfoService` | 2 | `getCctvStnRoadWthr`, `getStdNodeLinkRoadWw` |
| `15102239` | 기상청_전국 해수욕장 날씨 조회서비스 | `BeachInfoservice` | 6 | `getUltraSrtFcstBeach`, `getWhBuoyBeach`, `getTideInfoBeach`, `getSunInfoBeach`, `getTwBuoyBeach`, `getVilageFcstBeach` |
| `15056924` | 기상청_레이더영상 조회서비스 | `RadarImgInfoService` | 2 | `getCmpImg`, `getRadarIndvdlzImg` |
| `15085289` | 기상청_꽃가루농도위험지수 조회서비스(3.0) | `HealthWthrIdxServiceV3` | 3 | `getPinePollenRiskIdxV3`, `getWeedsPollenRiskndxV3`, `getOakPollenRiskIdxV3` |
| `15059518` | 기상청_작물별 농업주산지 상세날씨 조회서비스 | `FmlandWthrInfoService` | 6 | `getDayStatistics`, `getPureStatistics`, `getMmStatistics`, `getFmlandVilageNcst`, `getFmlandVilageFcst`, `getFmlandPwn` |
| `15057166` | 기상청_레이더관측자료 조회서비스 | `RadarObsInfoService` | 3 | `getRadarRnZone`, `getLocalRadarRn`, `getNationalRadarRn` |
| `15057256` | 기상청_낙뢰분포도 조회서비스 | `LgtDistrbInfoService` | 1 | `getLgtDistrb` |
| `15095149` | 기상청_영향예보_조회서비스 | `ImpactInfoService` | 4 | `getHWImpactValue`, `getCWImpactValue`, `getHWCntrmsrMthd`, `getCWCntrmsrMthd` |
| `15058079` | 기상청_낙뢰관측자료 조회서비스 | `LgtInfoService` | 1 | `getLgt` |
| `15059087` | 기상청_서리발생 가능성 예측정보 조회서비스 | `FrstFcstInfoService` | 1 | `getFrstOcurFcst` |

## data.go.kr 검색의 APIHub LINK dataset

아래 항목은 data.go.kr 검색 결과에는 포함되지만 `serviceKey` gateway가 아니라 APIHub LINK로 분류됩니다. `DataGoKrClient.dataset_items()`로 호출하지 않고 `ApiHubClient` 또는 `ApiHubGeneratedClient`를 사용합니다.

| data.go.kr id | 제목 | 비고 |
|---|---|---|
| `15139470` | 기상청_단기예보 조회서비스(기상청API허브 연계) | APIHub LINK |
| `15139479` | 기상청_천리안위성 2A호 인공지능 기반 일사량 조회서비스 | APIHub LINK |
| `15139436` | 기상청_적설관측 조회서비스 | APIHub LINK |
| `15126648` | 기상청_전지구예보모델 조회서비스 | APIHub LINK |
| `15139476` | 기상청_특보 조회서비스 | APIHub LINK |
| `15126649` | 기상청_통보문 조회서비스 | APIHub LINK |
| `15126651` | 기상청_특보구역정보 조회서비스 | APIHub LINK |
| `15139439` | 기상청_지상기상관측 지점정보 조회서비스 | APIHub LINK |
| `15081107` | 기상청 항공기상청_항공기상전문(IWXXM) 조회서비스_항공기상관측 | APIHub LINK |
| `15139433` | 기상청_자동기상관측 조회서비스 | APIHub LINK |
| `15139478` | 기상청_고해상도 격자 조회서비스 | APIHub LINK |
| `15139440` | 기상청_해양기상부이·파고부이 관측 조회서비스 | APIHub LINK |
| `15139446` | 기상청_레이더강수량(HSR) 조회서비스 | APIHub LINK |
| `15139481` | 기상청_산악예보 조회서비스 | APIHub LINK |
| `15123139` | 기상청 항공기상청_공항예보 | APIHub LINK |
| `15139432` | 기상청_종관기상관측 조회서비스 | APIHub LINK |
| `15123073` | 기상청 항공기상청_공항기상관측자료 | APIHub LINK |
| `15126650` | 기상청_일본 히마와리 위성자료 조회서비스 | APIHub LINK |
| `15139475` | 기상청_중기예보(TXT) 조회서비스 | APIHub LINK |
| `15139449` | 기상청_낙뢰관측 조회서비스 | APIHub LINK |
| `15139467` | 기상청_수치예보모델 조회서비스 | APIHub LINK |
| `15126688` | 기상청_수치예상일기도 조회서비스 | APIHub LINK |
| `15139484` | 기상청_공항기상관측(AMOS) 조회서비스 | APIHub LINK |
| `15139438` | 기상청_자외선관측 조회서비스 | APIHub LINK |
| `15139450` | 기상청_천리안위성 2A호 조회서비스 | APIHub LINK |
| `15139488` | 기상청_저고도 기상정보 조회서비스 | APIHub LINK |
| `15139435` | 기상청_황사관측(PM10) 조회서비스 | APIHub LINK |
| `15139480` | 기상청_전력기상지수 조회서비스 | APIHub LINK |
| `15139437` | 기상청_계절관측 조회서비스 | APIHub LINK |
| `15139442` | 기상청_해양기상관측 지점정보 조회서비스 | APIHub LINK |
| `15126640` | 기상청_기상1호 조회서비스 | APIHub LINK |
| `15139489` | 기상청_세계기상관측 조회서비스 | APIHub LINK |
| `15126689` | 기상청_표류부이 조회서비스 | APIHub LINK |
| `15139453` | 기상청_태풍 베스트트랙 조회서비스 | APIHub LINK |
| `15139447` | 기상청_레이더 합성자료 조회서비스 | APIHub LINK |
| `15139483` | 기상청_항공기상관측 조회서비스 | APIHub LINK |
| `15139486` | 기상청_국내 AMDAR 관측 조회서비스 | APIHub LINK |
| `15139445` | 기상청_고층기상관측 지점정보 조회서비스 | APIHub LINK |
| `15139452` | 기상청_태풍정보(TD) 조회서비스 | APIHub LINK |
| `15139444` | 기상청_연직바람관측(윈드프로파일러) 조회서비스 | APIHub LINK |
| `15139468` | 기상청_수치예보모델 그래픽 조회서비스 | APIHub LINK |
| `15139451` | 기상청_천리안위성 1호 조회서비스 | APIHub LINK |
| `15139448` | 기상청_레이더 사이트 조회서비스 | APIHub LINK |
| `15139434` | 기상청_북한기상관측 조회서비스 | APIHub LINK |
| `15139443` | 기상청_레윈존데 조회서비스 | APIHub LINK |
| `15139441` | 기상청_등표기상관측 조회서비스 | APIHub LINK |
| `15159045` | 기상청_도로기상관측자료 | APIHub LINK |
| `15159041` | 기상청_도로위험기상정보 | APIHub LINK |

## 해석

- 정확 중복 109개 operation은 인증 방식과 응답 gateway가 다릅니다. data.go.kr 쪽은 `serviceKey`, APIHub 쪽은 `authKey`를 사용합니다.
- 같은 service/operation이어도 응답 기본값, 샘플 파라미터, 포털 승인 상태가 다를 수 있으므로 테스트와 문서에서는 두 gateway를 섞지 않습니다.
- APIHub LINK 48개는 data.go.kr 카탈로그에 남기되 `gateway="apihub"`로만 표시합니다.

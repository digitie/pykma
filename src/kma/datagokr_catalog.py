"""공공데이터포털의 기상청 data.go.kr OpenAPI dataset catalog."""
# ruff: noqa: E501

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DataGoKrDatasetSpec:
    """data.go.kr에 공개된 기상청 OpenAPI dataset 명세."""

    dataset_id: str
    title: str
    gateway: str
    service: str | None
    operations: tuple[str, ...]
    portal_url: str
    page: int


KMA_DATA_GOKR_DATASETS: tuple[DataGoKrDatasetSpec, ...] = (
    DataGoKrDatasetSpec(dataset_id="15084084", title="기상청_단기예보 조회서비스", gateway="datagokr", service="VilageFcstInfoService_2.0", operations=("getUltraSrtNcst", "getUltraSrtFcst", "getVilageFcst", "getFcstVersion"), portal_url="https://www.data.go.kr/data/15084084/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15059468", title="기상청_중기예보 조회서비스", gateway="datagokr", service="MidFcstInfoService", operations=("getMidFcst", "getMidLandFcst", "getMidTa", "getMidSeaFcst"), portal_url="https://www.data.go.kr/data/15059468/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15059093", title="기상청_지상(종관, ASOS) 일자료 조회서비스", gateway="datagokr", service="AsosDalyInfoService", operations=("getWthrDataList",), portal_url="https://www.data.go.kr/data/15059093/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15057210", title="기상청_지상(종관, ASOS) 시간자료 조회서비스", gateway="datagokr", service="AsosHourlyInfoService", operations=("getWthrDataList",), portal_url="https://www.data.go.kr/data/15057210/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15000415", title="기상청_기상특보 조회서비스", gateway="datagokr", service="WthrWrnInfoService", operations=("getWthrWrnList", "getWthrWrnMsg", "getWthrInfoList", "getWthrInfo", "getWthrBrkNewsList", "getWthrBrkNews", "getWthrPwnList", "getWthrPwn", "getPwnCd", "getPwnStatus"), portal_url="https://www.data.go.kr/data/15000415/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15139470", title="기상청_단기예보 조회서비스(기상청API허브 연계)", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139470/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15056912", title="기상청_관광코스별 관광지 상세 날씨 조회서비스", gateway="datagokr", service="TourStnInfoService1", operations=("getTourStnVilageFcst1", "getCityTourClmIdx1"), portal_url="https://www.data.go.kr/data/15056912/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15058629", title="기상청_단기예보 통보문 조회서비스", gateway="datagokr", service="VilageFcstMsgService", operations=("getWthrSituation", "getLandFcst", "getSeaFcst"), portal_url="https://www.data.go.kr/data/15058629/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15085288", title="기상청_생활기상지수 조회서비스(3.0)", gateway="datagokr", service="LivingWthrIdxServiceV4", operations=("getSenTaIdxV4", "getUVIdxV4", "getAirDiffusionIdxV4"), portal_url="https://www.data.go.kr/data/15085288/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15000420", title="기상청_지진정보 조회서비스", gateway="datagokr", service="EqkInfoService", operations=("getEqkMsg", "getEqkMsgList", "getTsunamiMsg", "getTsunamiMsgList"), portal_url="https://www.data.go.kr/data/15000420/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15043565", title="기상청_태풍정보 조회서비스", gateway="datagokr", service="TyphoonInfoService", operations=("getTyphoonInfo", "getTyphoonInfoList", "getTyphoonFcst"), portal_url="https://www.data.go.kr/data/15043565/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15058167", title="기상청_위성영상 조회서비스", gateway="datagokr", service="SatlitImgInfoService", operations=("getInsightSatlit",), portal_url="https://www.data.go.kr/data/15058167/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15043562", title="기상청_일기도 조회서비스", gateway="datagokr", service="WthrChartInfoService", operations=("getSurfaceChart", "getAuxillaryChart"), portal_url="https://www.data.go.kr/data/15043562/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15057966", title="기상청_CCTV 기반 도로날씨정보 조회서비스", gateway="datagokr", service="RoadWthrInfoService", operations=("getCctvStnRoadWthr", "getStdNodeLinkRoadWw"), portal_url="https://www.data.go.kr/data/15057966/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15102239", title="기상청_전국 해수욕장 날씨 조회서비스", gateway="datagokr", service="BeachInfoservice", operations=("getUltraSrtFcstBeach", "getWhBuoyBeach", "getTideInfoBeach", "getSunInfoBeach", "getTwBuoyBeach", "getVilageFcstBeach"), portal_url="https://www.data.go.kr/data/15102239/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15056924", title="기상청_레이더영상 조회서비스", gateway="datagokr", service="RadarImgInfoService", operations=("getCmpImg", "getRadarIndvdlzImg"), portal_url="https://www.data.go.kr/data/15056924/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15139479", title="기상청_천리안위성 2A호 인공지능 기반 일사량 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139479/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15139436", title="기상청_적설관측 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139436/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15126648", title="기상청_전지구예보모델 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15126648/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15085289", title="기상청_꽃가루농도위험지수 조회서비스(3.0)", gateway="datagokr", service="HealthWthrIdxServiceV3", operations=("getPinePollenRiskIdxV3", "getWeedsPollenRiskndxV3", "getOakPollenRiskIdxV3"), portal_url="https://www.data.go.kr/data/15085289/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15139476", title="기상청_특보 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139476/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15057111", title="기상청_예보구역정보 조회서비스", gateway="datagokr", service="FcstZoneInfoService", operations=("getFcstZoneCd",), portal_url="https://www.data.go.kr/data/15057111/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15126649", title="기상청_통보문 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15126649/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15059518", title="기상청_작물별 농업주산지 상세날씨 조회서비스", gateway="datagokr", service="FmlandWthrInfoService", operations=("getDayStatistics", "getPureStatistics", "getMmStatistics", "getFmlandVilageNcst", "getFmlandVilageFcst", "getFmlandPwn"), portal_url="https://www.data.go.kr/data/15059518/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15126651", title="기상청_특보구역정보 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15126651/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15139439", title="기상청_지상기상관측 지점정보 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139439/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15081107", title="기상청 항공기상청_항공기상전문(IWXXM) 조회서비스_항공기상관측", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15081107/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15139433", title="기상청_자동기상관측 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139433/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15139478", title="기상청_고해상도 격자 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139478/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15139440", title="기상청_해양기상부이·파고부이 관측 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139440/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15139446", title="기상청_레이더강수량(HSR) 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139446/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15057166", title="기상청_레이더관측자료 조회서비스", gateway="datagokr", service="RadarObsInfoService", operations=("getRadarRnZone", "getLocalRadarRn", "getNationalRadarRn"), portal_url="https://www.data.go.kr/data/15057166/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15057260", title="기상청_지상기상월보 조회서비스", gateway="datagokr", service="SfcMtlyInfoService", operations=("getNote", "getSfcStnLstTbl", "getMmSumry", "getMmSumry2", "getDailyWthrData", "getAirNote", "getrAirStnLstTbl", "getDailyAirData"), portal_url="https://www.data.go.kr/data/15057260/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15139481", title="기상청_산악예보 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139481/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15123139", title="기상청 항공기상청_공항예보", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15123139/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15139432", title="기상청_종관기상관측 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139432/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15123073", title="기상청 항공기상청_공항기상관측자료", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15123073/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15126650", title="기상청_일본 히마와리 위성자료 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15126650/openapi.do", page=1),
    DataGoKrDatasetSpec(dataset_id="15059244", title="기상청_위성자료(경량화) 조회서비스", gateway="datagokr", service="WthrSatlitInfoService", operations=("getGk2aIrAll", "getGk2aNrAll", "getGk2aSwAll", "getGk2aViAll", "getGk2aWvAll", "getGk2aIrArea", "getGk2aNrArea", "getGk2aSwArea", "getGk2aViArea", "getGk2aWvArea"), portal_url="https://www.data.go.kr/data/15059244/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15057256", title="기상청_낙뢰분포도 조회서비스", gateway="datagokr", service="LgtDistrbInfoService", operations=("getLgtDistrb",), portal_url="https://www.data.go.kr/data/15057256/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15139475", title="기상청_중기예보(TXT) 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139475/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15139449", title="기상청_낙뢰관측 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139449/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15095149", title="기상청_영향예보_조회서비스", gateway="datagokr", service="ImpactInfoService", operations=("getHWImpactValue", "getCWImpactValue", "getHWCntrmsrMthd", "getCWCntrmsrMthd"), portal_url="https://www.data.go.kr/data/15095149/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15139467", title="기상청_수치예보모델 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139467/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15126688", title="기상청_수치예상일기도 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15126688/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15058804", title="기상청_항공기상전문 조회서비스", gateway="datagokr", service="AmmService", operations=("getMetar", "getTaf", "getWarning", "getSigmet", "getAirmet"), portal_url="https://www.data.go.kr/data/15058804/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15139484", title="기상청_공항기상관측(AMOS) 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139484/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15077314", title="기상청_위성자료 경량화 조회서비스(기상산출물)", gateway="datagokr", service="CloudSatlitInfoService", operations=("getGk2acldAll", "getGk2aappsAll", "getGk2afogAll", "getGk2adcoewAll", "getGk2aclaAll", "getGk2acldArea", "getGk2aappsArea", "getGk2afogArea", "getGk2adcoewArea", "getGk2aclaArea"), portal_url="https://www.data.go.kr/data/15077314/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15095158", title="기상청_세계기상전문(GTS)_조회서비스", gateway="datagokr", service="GtsInfoService", operations=("getBuoy", "getGtsStn", "getSynop", "getTemp"), portal_url="https://www.data.go.kr/data/15095158/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15058079", title="기상청_낙뢰관측자료 조회서비스", gateway="datagokr", service="LgtInfoService", operations=("getLgt",), portal_url="https://www.data.go.kr/data/15058079/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15139438", title="기상청_자외선관측 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139438/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15110052", title="기상청_국내 공항기상정보 조회서비스", gateway="datagokr", service="AirPortService", operations=("getAirPort",), portal_url="https://www.data.go.kr/data/15110052/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15139450", title="기상청_천리안위성 2A호 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139450/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15139488", title="기상청_저고도 기상정보 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139488/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15058845", title="기상청_지상기상연보 조회서비스", gateway="datagokr", service="SfcYearlyInfoService", operations=("getNote", "getSfcStnLstTbl", "getAirStnInfo", "getAirStnInfo2", "getAirStnInfo3", "getrAirStnLstTbl", "getYearSumry", "getYearSumry2", "getAvgTaAnamaly", "getRnAnamaly", "getStnPhnmnData", "getStnPhnmnData2", "getStnPhnmnData3", "getTyphoonList"), portal_url="https://www.data.go.kr/data/15058845/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15059087", title="기상청_서리발생 가능성 예측정보 조회서비스", gateway="datagokr", service="FrstFcstInfoService", operations=("getFrstOcurFcst",), portal_url="https://www.data.go.kr/data/15059087/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15058466", title="기상청_방재기상월보 조회서비스", gateway="datagokr", service="AwsMtlyInfoService", operations=("getNote", "getAwsStnLstTbl", "getMmSumry", "getDailyAwsData"), portal_url="https://www.data.go.kr/data/15058466/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15059060", title="기상청_레이더자료(경량화) 조회서비스", gateway="datagokr", service="WthrRadarInfoService", operations=("getCompCappiQcdAll", "getCompCappiQcdArea", "getSiteCappiQcdAll", "getSiteCappiQcdArea"), portal_url="https://www.data.go.kr/data/15059060/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15095109", title="기상청_국내 공항 이륙예보 조회서비스", gateway="datagokr", service="AirInfoService", operations=("getAirInfo",), portal_url="https://www.data.go.kr/data/15095109/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15139435", title="기상청_황사관측(PM10) 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139435/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15059455", title="기상청_항공기상전문(IWXXMVer.2.0) 조회서비스", gateway="datagokr", service="AmmIwxxmService", operations=("getMetar", "getTaf", "getSigmet", "getAirmet"), portal_url="https://www.data.go.kr/data/15059455/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15059094", title="기상청_해양기상월보 조회서비스", gateway="datagokr", service="SeaMtlyInfoService", operations=("getNote", "getBuoyLstTbl", "getLhawsLstTbl", "getWaveBuoyLstTbl", "getObsOpenYear", "getBuoyMmSumry", "getBuoyMmSumry2", "getDailyBuoy", "getLhawsMmSumry", "getLhawsMmSumry2", "getDailyLhaws", "getWaveBuoyMmSumry", "getWaveBuoyMmSumry2", "getDailyWaveBuoy"), portal_url="https://www.data.go.kr/data/15059094/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15139480", title="기상청_전력기상지수 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139480/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15139437", title="기상청_계절관측 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139437/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15139442", title="기상청_해양기상관측 지점정보 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139442/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15059100", title="기상청_세계공항 항공기상전문 조회서비스", gateway="datagokr", service="AftnAmmService", operations=("getMetar", "getTaf", "getSigmet"), portal_url="https://www.data.go.kr/data/15059100/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15126640", title="기상청_기상1호 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15126640/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15059466", title="기상청_방재기상연보 조회서비스", gateway="datagokr", service="AwsYearlyInfoService", operations=("getNote", "getAwsStnLstTbl", "getYearSumry", "getStnbyMmSumry"), portal_url="https://www.data.go.kr/data/15059466/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15139489", title="기상청_세계기상관측 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139489/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15126689", title="기상청_표류부이 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15126689/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15139453", title="기상청_태풍 베스트트랙 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139453/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15139447", title="기상청_레이더 합성자료 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139447/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15139483", title="기상청_항공기상관측 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139483/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15139486", title="기상청_국내 AMDAR 관측 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139486/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15139445", title="기상청_고층기상관측 지점정보 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139445/openapi.do", page=2),
    DataGoKrDatasetSpec(dataset_id="15139452", title="기상청_태풍정보(TD) 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139452/openapi.do", page=3),
    DataGoKrDatasetSpec(dataset_id="15058088", title="기상청_고층기상월보 조회서비스", gateway="datagokr", service="UppMtlyInfoService", operations=("getNote", "getUppLstTbl", "getStdIsbrsfValue", "getMaxWind", "getTaHmLevel", "getWindLevel"), portal_url="https://www.data.go.kr/data/15058088/openapi.do", page=3),
    DataGoKrDatasetSpec(dataset_id="15139444", title="기상청_연직바람관측(윈드프로파일러) 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139444/openapi.do", page=3),
    DataGoKrDatasetSpec(dataset_id="15139468", title="기상청_수치예보모델 그래픽 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139468/openapi.do", page=3),
    DataGoKrDatasetSpec(dataset_id="15139451", title="기상청_천리안위성 1호 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139451/openapi.do", page=3),
    DataGoKrDatasetSpec(dataset_id="15139448", title="기상청_레이더 사이트 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139448/openapi.do", page=3),
    DataGoKrDatasetSpec(dataset_id="15139434", title="기상청_북한기상관측 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139434/openapi.do", page=3),
    DataGoKrDatasetSpec(dataset_id="15139443", title="기상청_레윈존데 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139443/openapi.do", page=3),
    DataGoKrDatasetSpec(dataset_id="15139441", title="기상청_등표기상관측 조회서비스", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15139441/openapi.do", page=3),
    DataGoKrDatasetSpec(dataset_id="15159045", title="기상청_도로기상관측자료", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15159045/openapi.do", page=3),
    DataGoKrDatasetSpec(dataset_id="15159041", title="기상청_도로위험기상정보", gateway="apihub", service=None, operations=(), portal_url="https://www.data.go.kr/data/15159041/openapi.do", page=3),
)

KMA_DATA_GOKR_DATASETS_BY_ID: dict[str, DataGoKrDatasetSpec] = {
    dataset.dataset_id: dataset for dataset in KMA_DATA_GOKR_DATASETS
}

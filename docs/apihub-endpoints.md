# APIHub 함수형 endpoint 목록

이 문서는 `src/kma/apihub_endpoints.py`와 같은 원천에서 생성한 함수 목록입니다.

- 생성일: 2026-05-06
- 원천: https://apihub.kma.go.kr/apiList.do
- 보조 원천: https://apihub.kma.go.kr/generateAPIUrl.do
- 텍스트 예제 첨부: `main.txt`처럼 API URL을 포함한 예제 파일
- 전체 함수형 래퍼: **470개**
- 첨부 자료 metadata: **77개**

응답 종류별 개수:

| 응답 종류 | 개수 | 의미 |
|---|---:|---|
| `text` | 255 | TXT, CSV식 텍스트, 고정폭 텍스트 |
| `structured` | 135 | JSON/XML REST envelope 또는 목록형 응답 |
| `image` | 49 | 이미지 bytes 또는 그래픽 endpoint |
| `file` | 31 | GRIB, NetCDF, 원시자료, 다운로드 계열 |

## 사용법

```python
from kma import ApiHubGeneratedClient

hub = ApiHubGeneratedClient.from_env()
response = hub.kma_sfctm2(tm="202605010900", stn="108", help="1")
rows = response.text_table().rows
```

홈페이지 예제 값을 그대로 써서 호출하려면 `use_sample=True`를 넘깁니다. 실제 운영 코드에서는 예제 날짜가 오래되었을 수 있으므로 필요한 인자를 명시하는 것을 권장합니다.

```python
response = hub.kma_sfctm2(use_sample=True, stn="108")
```

이미지 endpoint는 bytes와 포맷/크기 정보를 함께 얻을 수 있습니다.

```python
image = hub.image_endpoint("api_iwa_img_url_api_ret_grid_img", use_sample=True)
print(image.format, image.width, image.height)
```

이름 없는 query string을 쓰는 legacy 그래픽 URL은 `arg1`, `arg2`처럼 순서형 인자로 노출합니다. 예를 들어 `?202305031000&0&...` 형태는 `arg1="202305031000"`, `arg2="0"`로 넘깁니다.

## 첨부 자료 metadata

`APIHUB_ATTACHMENTS`에는 포맷정보, 예제, 코드표 같은 첨부 링크를 Python 데이터로 보관합니다. PDF 본문 전체를 패키지에 넣지는 않고, 제목, 파일명, 서비스, 종류, 다운로드 URL을 metadata로 둡니다.

| 종류 | 개수 |
|---|---:|
| `data` | 28 |
| `format` | 9 |
| `reference` | 38 |
| `sample` | 2 |

포맷정보와 예제 첨부:

| 제목 | 서비스 | 종류 | 파일명 |
|---|---|---|---|
| 기상청 WindProfiler 파일 포멧 | 연직바람관측 | `format` | `kma_wpf_file_format.pdf` |
| 레이더 합성자료(500m해상도) 포맷정보 | 레이더 강수량(HSR) | `format` | `레이더 합성자료(500m 해상도) 포맷정보.pdf` |
| 레이더 합성자료 포맷 정보 | 레이더 강수량 | `format` | `레이더 합성자료 포맷 정보.pdf` |
| 신 낙뢰관측자료(2015.04.01 이후) | 낙뢰관측 | `format` | `new_lgt_data_format.pdf` |
| 그래픽 API 활용 예제 | 수치모델 그래픽 | `sample` | `main.txt` |
| 지점 정보 목록 | NCEI 관측·통계 | `format` | `12.igra2-list-format.txt` |
| 자료 설명서 | NCEI 관측·통계 | `format` | `20.igra2-data-format.txt` |
| 분석자료 설명서 | NCEI 관측·통계 | `format` | `30.igra2-derived-format.txt` |
| 존데 정보 설명서 | NCEI 관측·통계 | `format` | `43.wmo-history-format.txt` |
| 월평균 포멧 | NCEI 관측·통계 | `format` | `50.igra2-monthly-format.txt` |
| 예제 파일 | NCEI 관측·통계 | `sample` | `Marine_CSV_sample.csv` |

## 지상관측

| 함수 | 서비스 | 응답 | path | 파라미터 |
|---|---|---|---|---|
| `kma_sfctm2` | 종관기상관측(ASOS) | `text` | `/api/typ01/url/kma_sfctm2.php` | `tm`, `stn`, `help` |
| `kma_sfctm3` | 종관기상관측(ASOS) | `text` | `/api/typ01/url/kma_sfctm3.php` | `tm1`, `tm2`, `stn`, `help` |
| `kma_sfcdd` | 종관기상관측(ASOS) | `text` | `/api/typ01/url/kma_sfcdd.php` | `tm`, `stn`, `help` |
| `kma_sfcdd3` | 종관기상관측(ASOS) | `text` | `/api/typ01/url/kma_sfcdd3.php` | `tm1`, `tm2`, `stn`, `help` |
| `kma_sfctm5` | 종관기상관측(ASOS) | `text` | `/api/typ01/url/kma_sfctm5.php` | `tm2`, `obs`, `stn`, `disp`, `help` |
| `sfc_norm1` | 종관기상관측(ASOS) | `text` | `/api/typ01/url/sfc_norm1.php` | `norm`, `tmst`, `stn`, `MM1`, `DD1`, `MM2`, `DD2` |
| `sfc_yearly_info_service_get_year_sumry` | 종관기상관측(ASOS) | `structured` | `/api/typ02/openApi/SfcYearlyInfoService/getYearSumry` | `pageNo`, `numOfRows`, `dataType`, `year` |
| `sfc_yearly_info_service_get_year_sumry2` | 종관기상관측(ASOS) | `structured` | `/api/typ02/openApi/SfcYearlyInfoService/getYearSumry2` | `pageNo`, `numOfRows`, `dataType`, `year` |
| `sfc_yearly_info_service_get_avg_ta_anamaly` | 종관기상관측(ASOS) | `structured` | `/api/typ02/openApi/SfcYearlyInfoService/getAvgTaAnamaly` | `pageNo`, `numOfRows`, `dataType`, `year` |
| `sfc_yearly_info_service_get_rn_anamaly` | 종관기상관측(ASOS) | `structured` | `/api/typ02/openApi/SfcYearlyInfoService/getRnAnamaly` | `pageNo`, `numOfRows`, `dataType`, `year` |
| `sfc_yearly_info_service_get_stn_phnmn_data` | 종관기상관측(ASOS) | `structured` | `/api/typ02/openApi/SfcYearlyInfoService/getStnPhnmnData` | `pageNo`, `numOfRows`, `dataType`, `year`, `station` |
| `sfc_yearly_info_service_get_stn_phnmn_data2` | 종관기상관측(ASOS) | `structured` | `/api/typ02/openApi/SfcYearlyInfoService/getStnPhnmnData2` | `pageNo`, `numOfRows`, `dataType`, `year`, `station` |
| `sfc_yearly_info_service_get_stn_phnmn_data3` | 종관기상관측(ASOS) | `structured` | `/api/typ02/openApi/SfcYearlyInfoService/getStnPhnmnData3` | `pageNo`, `numOfRows`, `dataType`, `year`, `station` |
| `sfc_mtly_info_service_get_note` | 종관기상관측(ASOS) | `structured` | `/api/typ02/openApi/SfcMtlyInfoService/getNote` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `sfc_mtly_info_service_get_sfc_stn_lst_tbl` | 종관기상관측(ASOS) | `structured` | `/api/typ02/openApi/SfcMtlyInfoService/getSfcStnLstTbl` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `sfc_mtly_info_service_get_mm_sumry` | 종관기상관측(ASOS) | `structured` | `/api/typ02/openApi/SfcMtlyInfoService/getMmSumry` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `sfc_mtly_info_service_get_mm_sumry2` | 종관기상관측(ASOS) | `structured` | `/api/typ02/openApi/SfcMtlyInfoService/getMmSumry2` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `sfc_mtly_info_service_get_daily_wthr_data` | 종관기상관측(ASOS) | `structured` | `/api/typ02/openApi/SfcMtlyInfoService/getDailyWthrData` | `pageNo`, `numOfRows`, `dataType`, `year`, `month`, `station` |
| `alw_sfc_sfc_ww_pnt` | 종관기상관측(ASOS) | `image` | `/api/typ03/php/alw/sfc/sfc_ww_pnt.php` | `obs`, `tm`, `val`, `stn`, `obj`, `map`, `grid`, `legend`, `size`, `itv`, `zoom_level`, `zoom_x`, `zoom_y`, `gov` |
| `aws2_min` | 방재기상관측(AWS) | `text` | `/api/typ01/cgi-bin/url/nph-aws2_min` | `tm2`, `stn`, `disp`, `help` |
| `aws2_min_lst` | 방재기상관측(AWS) | `text` | `/api/typ01/cgi-bin/url/nph-aws2_min_lst` | `tm2`, `stn`, `disp`, `help` |
| `aws2_min_cloud` | 방재기상관측(AWS) | `text` | `/api/typ01/cgi-bin/url/nph-aws2_min_cloud` | `tm2`, `stn`, `disp`, `help` |
| `aws2_min_ca2` | 방재기상관측(AWS) | `text` | `/api/typ01/cgi-bin/url/nph-aws2_min_ca2` | `tm2`, `itv`, `range`, `stn`, `disp`, `help` |
| `aws2_min_ca3` | 방재기상관측(AWS) | `text` | `/api/typ01/cgi-bin/url/nph-aws2_min_ca3` | `tm2`, `itv`, `range`, `stn`, `disp`, `help` |
| `aws2_min_vis` | 방재기상관측(AWS) | `text` | `/api/typ01/cgi-bin/url/nph-aws2_min_vis` | `tm2`, `stn`, `disp`, `help` |
| `aws2_min_vis3` | 방재기상관측(AWS) | `text` | `/api/typ01/cgi-bin/url/nph-aws2_min_vis3` | `tm2`, `itv`, `range`, `stn`, `disp`, `help` |
| `aws2_min_ww1` | 방재기상관측(AWS) | `text` | `/api/typ01/cgi-bin/url/nph-aws2_min_ww1` | `tm2`, `itv`, `range`, `stn`, `help` |
| `aws2_min_ww2` | 방재기상관측(AWS) | `text` | `/api/typ01/cgi-bin/url/nph-aws2_min_ww2` | `tm2`, `itv`, `range`, `stn`, `disp`, `help` |
| `aws3_min_mob` | 방재기상관측(AWS) | `text` | `/api/typ01/cgi-bin/url/nph-aws3_min_mob` | `tm1`, `tm2`, `stn`, `disp`, `help` |
| `awsh` | 방재기상관측(AWS) | `text` | `/api/typ01/url/awsh.php` | `var`, `tm`, `help` |
| `awsh_2` | 방재기상관측(AWS) | `text` | `/api/typ01/url/awsh.php` | `tm`, `help` |
| `sfc_aws_day` | 방재기상관측(AWS) | `text` | `/api/typ01/url/sfc_aws_day.php` | `tm2`, `obs`, `stn`, `disp`, `help` |
| `aws_yearly_info_service_get_stnby_mm_sumry` | 방재기상관측(AWS) | `structured` | `/api/typ02/openApi/AwsYearlyInfoService/getStnbyMmSumry` | `pageNo`, `numOfRows`, `dataType`, `year`, `month`, `station` |
| `aws_yearly_info_service_get_year_sumry` | 방재기상관측(AWS) | `structured` | `/api/typ02/openApi/AwsYearlyInfoService/getYearSumry` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `aws_yearly_info_service_get_aws_stn_lst_tbl` | 방재기상관측(AWS) | `structured` | `/api/typ02/openApi/AwsYearlyInfoService/getAwsStnLstTbl` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `aws_yearly_info_service_get_note` | 방재기상관측(AWS) | `structured` | `/api/typ02/openApi/AwsYearlyInfoService/getNote` | `pageNo`, `numOfRows`, `dataType`, `year` |
| `aws_mtly_info_service_get_daily_aws_data` | 방재기상관측(AWS) | `structured` | `/api/typ02/openApi/AwsMtlyInfoService/getDailyAwsData` | `pageNo`, `numOfRows`, `dataType`, `year`, `month`, `station` |
| `aws_mtly_info_service_get_mm_sumry` | 방재기상관측(AWS) | `structured` | `/api/typ02/openApi/AwsMtlyInfoService/getMmSumry` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `aws_mtly_info_service_get_aws_stn_lst_tbl` | 방재기상관측(AWS) | `structured` | `/api/typ02/openApi/AwsMtlyInfoService/getAwsStnLstTbl` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `aws_mtly_info_service_get_note` | 방재기상관측(AWS) | `structured` | `/api/typ02/openApi/AwsMtlyInfoService/getNote` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `alw_aws_aws_ww_pnt` | 방재기상관측(AWS) | `image` | `/api/typ03/php/alw/aws/aws_ww_pnt.php` | `obs`, `tm`, `val`, `stn`, `obj`, `map`, `grid`, `legend`, `size`, `itv`, `zoom_level`, `zoom_x`, `zoom_y`, `gov` |
| `aws3_nph_aws_day_img1` | 방재기상관측(AWS) | `image` | `/api/typ03/cgi/aws3/nph-aws_day_img1` | `obs`, `tm`, `val`, `stn`, `obj`, `map`, `grid`, `legend`, `size`, `zoom_level`, `zoom_x`, `zoom_y` |
| `aws3_nph_aws_min_img1` | 방재기상관측(AWS) | `image` | `/api/typ03/cgi/aws3/nph-aws_min_img1` | `obs`, `tm`, `val`, `stn`, `obj`, `map`, `grid`, `legend`, `size`, `itv`, `zoom_level`, `zoom_x`, `zoom_y`, `gov`, `_DT` |
| `aws3_nph_aws_min_img2` | 방재기상관측(AWS) | `image` | `/api/typ03/cgi/aws3/nph-aws_min_img2` | `obs`, `tm`, `val`, `stn`, `obj`, `ws_ms`, `map`, `grid`, `legend` |
| `alw_aws_aws_obs_pnt` | 방재기상관측(AWS) | `image` | `/api/typ03/php/alw/aws/aws_obs_pnt.php` | `obs`, `tm`, `val`, `stn`, `obj`, `map`, `grid`, `legend`, `size`, `itv` |
| `alw_sea_sea_obs_pnt` | 방재기상관측(AWS) | `image` | `/api/typ03/php/alw/sea/sea_obs_pnt.php` | `obs`, `tm`, `val`, `stn`, `obj`, `map`, `grid`, `legend`, `size`, `itv`, `zoom_level`, `zoom_x`, `zoom_y`, `gov`, `_DT` |
| `aws3_nph_awsm_tms_h06` | 방재기상관측(AWS) | `image` | `/api/typ03/cgi/aws3/nph-awsm_tms_h06` | `arg1`, `arg2`, `arg3`, `arg4`, `arg5`, `arg6`, `_DT` |
| `aws3_nph_awsm_tms_h12` | 방재기상관측(AWS) | `image` | `/api/typ03/cgi/aws3/nph-awsm_tms_h12` | `arg1`, `arg2`, `arg3`, `arg4`, `arg5`, `arg6`, `arg7`, `_DT` |
| `aws2_nph_awsm_tms_h24` | 방재기상관측(AWS) | `image` | `/api/typ03/cgi/aws2/nph-awsm_tms_h24` | `arg1`, `arg2`, `arg3`, `arg4`, `arg5`, `arg6` |
| `aws2_nph_awsm_tms_d02` | 방재기상관측(AWS) | `image` | `/api/typ03/cgi/aws2/nph-awsm_tms_d02` | `arg1`, `arg2`, `arg3`, `arg4`, `arg5`, `arg6`, `arg7` |
| `aws2_nph_awsm_tms_d04` | 방재기상관측(AWS) | `image` | `/api/typ03/cgi/aws2/nph-awsm_tms_d04` | `arg1`, `arg2`, `arg3`, `arg4`, `arg5`, `arg6` |
| `aws2_nph_awsm_tms_d08` | 방재기상관측(AWS) | `image` | `/api/typ03/cgi/aws2/nph-awsm_tms_d08` | `arg1`, `arg2`, `arg3`, `arg4`, `arg5`, `arg6` |
| `aws2_nph_awsm_tms_d12` | 방재기상관측(AWS) | `image` | `/api/typ03/cgi/aws2/nph-awsm_tms_d12` | `arg1`, `arg2`, `arg3`, `arg4`, `arg5`, `arg6` |
| `aws3_nph_aws_day_imgp1` | 방재기상관측(AWS) | `image` | `/api/typ03/cgi/aws3/nph-aws_day_imgp1` | `PROJ`, `map`, `grid`, `itv`, `dataDtlCd`, `obs`, `stn`, `size`, `STARTX`, `STARTY`, `ENDX`, `ENDY`, `ZOOMLVL`, `selWs`, `tm`, `tm_st`, `tm_ed`, `tm2` |
| `aws3_nph_aws_min_imgp1` | 방재기상관측(AWS) | `image` | `/api/typ03/cgi/aws3/nph-aws_min_imgp1` | `PROJ`, `map`, `grid`, `itv`, `dataDtlCd`, `obs`, `stn`, `size`, `STARTX`, `STARTY`, `ENDX`, `ENDY`, `ZOOMLVL`, `selWs`, `tm`, `tm_st`, `tm_ed`, `tm2` |
| `aws3_nph_aws_min_imgp2` | 방재기상관측(AWS) | `image` | `/api/typ03/cgi/aws3/nph-aws_min_imgp2` | `PROJ`, `map`, `grid`, `itv`, `dataDtlCd`, `obs`, `stn`, `size`, `STARTX`, `STARTY`, `ENDX`, `ENDY`, `ZOOMLVL`, `selWs`, `tm`, `tm_st`, `tm_ed`, `tm2` |
| `sts_ta` | 기후통계 | `text` | `/api/typ01/url/sts_ta.php` | `tm1`, `tm2`, `stn_id`, `help`, `disp` |
| `sts_ta_2` | 기후통계 | `text` | `/api/typ01/url/sts_ta.php` | `tm1`, `tm2`, `lat`, `lon`, `help`, `disp` |
| `sts_si` | 기후통계 | `text` | `/api/typ01/url/sts_si.php` | `tm1`, `tm2`, `stn_id`, `help`, `disp` |
| `sts_si_2` | 기후통계 | `text` | `/api/typ01/url/sts_si.php` | `tm1`, `tm2`, `lat`, `lon`, `help`, `disp` |
| `sts_ss` | 기후통계 | `text` | `/api/typ01/url/sts_ss.php` | `tm1`, `tm2`, `stn_id`, `help`, `disp` |
| `sts_ss_2` | 기후통계 | `text` | `/api/typ01/url/sts_ss.php` | `tm1`, `tm2`, `lat`, `lon`, `help`, `disp` |
| `sts_pa` | 기후통계 | `text` | `/api/typ01/url/sts_pa.php` | `tm1`, `tm2`, `stn_id`, `help`, `disp` |
| `sts_pa_2` | 기후통계 | `text` | `/api/typ01/url/sts_pa.php` | `tm1`, `tm2`, `lat`, `lon`, `help`, `disp` |
| `sts_wind` | 기후통계 | `text` | `/api/typ01/url/sts_wind.php` | `tm1`, `tm2`, `stn_id`, `help`, `disp` |
| `sts_wind_2` | 기후통계 | `text` | `/api/typ01/url/sts_wind.php` | `tm1`, `tm2`, `lat`, `lon`, `help`, `disp` |
| `sts_td` | 기후통계 | `text` | `/api/typ01/url/sts_td.php` | `tm1`, `tm2`, `stn_id`, `help`, `disp` |
| `sts_td_2` | 기후통계 | `text` | `/api/typ01/url/sts_td.php` | `tm1`, `tm2`, `lat`, `lon`, `help`, `disp` |
| `sts_ts` | 기후통계 | `text` | `/api/typ01/url/sts_ts.php` | `tm1`, `tm2`, `stn_id`, `help`, `disp` |
| `sts_ts_2` | 기후통계 | `text` | `/api/typ01/url/sts_ts.php` | `tm1`, `tm2`, `lat`, `lon`, `help`, `disp` |
| `sts_tg` | 기후통계 | `text` | `/api/typ01/url/sts_tg.php` | `tm1`, `tm2`, `stn_id`, `help`, `disp` |
| `sts_tg_2` | 기후통계 | `text` | `/api/typ01/url/sts_tg.php` | `tm1`, `tm2`, `lat`, `lon`, `help`, `disp` |
| `sts_te` | 기후통계 | `text` | `/api/typ01/url/sts_te.php` | `tm1`, `tm2`, `stn_id`, `help`, `disp` |
| `sts_te_2` | 기후통계 | `text` | `/api/typ01/url/sts_te.php` | `tm1`, `tm2`, `lat`, `lon`, `help`, `disp` |
| `sts_rhm` | 기후통계 | `text` | `/api/typ01/url/sts_rhm.php` | `tm1`, `tm2`, `stn_id`, `help`, `disp` |
| `sts_rhm_2` | 기후통계 | `text` | `/api/typ01/url/sts_rhm.php` | `tm1`, `tm2`, `lat`, `lon`, `help`, `disp` |
| `sts_pv` | 기후통계 | `text` | `/api/typ01/url/sts_pv.php` | `tm1`, `tm2`, `stn_id`, `help`, `disp` |
| `sts_pv_2` | 기후통계 | `text` | `/api/typ01/url/sts_pv.php` | `tm1`, `tm2`, `lat`, `lon`, `help`, `disp` |
| `sts_cloud` | 기후통계 | `text` | `/api/typ01/url/sts_cloud.php` | `tm1`, `tm2`, `stn_id`, `help`, `disp` |
| `sts_cloud_2` | 기후통계 | `text` | `/api/typ01/url/sts_cloud.php` | `tm1`, `tm2`, `lat`, `lon`, `help`, `disp` |
| `sts_vs` | 기후통계 | `text` | `/api/typ01/url/sts_vs.php` | `tm1`, `tm2`, `stn_id`, `help`, `disp` |
| `sts_vs_2` | 기후통계 | `text` | `/api/typ01/url/sts_vs.php` | `tm1`, `tm2`, `lat`, `lon`, `help`, `disp` |
| `sts_rn` | 기후통계 | `text` | `/api/typ01/url/sts_rn.php` | `tm1`, `tm2`, `stn_id`, `help`, `disp` |
| `sts_rn_2` | 기후통계 | `text` | `/api/typ01/url/sts_rn.php` | `tm1`, `tm2`, `lat`, `lon`, `help`, `disp` |
| `sts_sd` | 기후통계 | `text` | `/api/typ01/url/sts_sd.php` | `tm1`, `tm2`, `stn_id`, `help`, `disp` |
| `sts_sd_2` | 기후통계 | `text` | `/api/typ01/url/sts_sd.php` | `tm1`, `tm2`, `lat`, `lon`, `help`, `disp` |
| `sts_ev` | 기후통계 | `text` | `/api/typ01/url/sts_ev.php` | `tm1`, `tm2`, `stn_id`, `help`, `disp` |
| `sts_ev_2` | 기후통계 | `text` | `/api/typ01/url/sts_ev.php` | `tm1`, `tm2`, `lat`, `lon`, `help`, `disp` |
| `sts_ydst` | 기후통계 | `text` | `/api/typ01/url/sts_ydst.php` | `tm1`, `tm2`, `stn_id`, `help`, `disp` |
| `sts_ydst_2` | 기후통계 | `text` | `/api/typ01/url/sts_ydst.php` | `tm1`, `tm2`, `lat`, `lon`, `help`, `disp` |
| `sts_fog` | 기후통계 | `text` | `/api/typ01/url/sts_fog.php` | `tm1`, `tm2`, `stn_id`, `help`, `disp` |
| `sts_fog_2` | 기후통계 | `text` | `/api/typ01/url/sts_fog.php` | `tm1`, `tm2`, `lat`, `lon`, `help`, `disp` |
| `nko_sfctm` | 북한기상관측 | `text` | `/api/typ01/url/nko_sfctm.php` | `tm`, `stn`, `help` |
| `sfc_nko_norm1` | 북한기상관측 | `text` | `/api/typ01/url/sfc_nko_norm1.php` | `norm`, `tmst`, `stn`, `MM1`, `DD1`, `MM2`, `DD2` |
| `kma_pm10` | 황사관측(PM10) | `text` | `/api/typ01/url/kma_pm10.php` | `tm1`, `tm2` |
| `stn_pm10_inf` | 황사관측(PM10) | `text` | `/api/typ01/url/stn_pm10_inf.php` | `inf`, `stn`, `tm`, `help` |
| `dst_pm10_tm` | 황사관측(PM10) | `text` | `/api/typ01/url/dst_pm10_tm.php` | `tm`, `org`, `stn`, `data`, `mode`, `help` |
| `dst_pm10_tm_2` | 황사관측(PM10) | `text` | `/api/typ01/url/dst_pm10_tm.php` | `tm`, `org` |
| `dst_pm10_hr` | 황사관측(PM10) | `text` | `/api/typ01/url/dst_pm10_hr.php` | `tm`, `org`, `stn`, `mode`, `help` |
| `dst_pm10_hr_2` | 황사관측(PM10) | `text` | `/api/typ01/url/dst_pm10_hr.php` | `tm`, `org` |
| `ydst_info_service_get_ydst_satlit_img` | 황사관측(PM10) | `structured` | `/api/typ02/openApi/YdstInfoService/getYdstSatlitImg` | `pageNo`, `numOfRows`, `dataType`, `time` |
| `ydst_info_service_get_ydst_obs` | 황사관측(PM10) | `structured` | `/api/typ02/openApi/YdstInfoService/getYdstObs` | `pageNo`, `numOfRows`, `dataType` |
| `ydst_info_service_get_ydst_sfc_chart` | 황사관측(PM10) | `structured` | `/api/typ02/openApi/YdstInfoService/getYdstSfcChart` | `pageNo`, `numOfRows`, `dataType`, `time` |
| `stn_snow` | 적설관측 | `text` | `/api/typ01/url/stn_snow.php` | `stn`, `tm`, `mode`, `help` |
| `kma_snow1` | 적설관측 | `text` | `/api/typ01/url/kma_snow1.php` | `sd`, `tm`, `help` |
| `kma_snow2` | 적설관측 | `text` | `/api/typ01/url/kma_snow2.php` | `tm`, `tm_st`, `snow`, `help` |
| `kma_snow_day` | 적설관측 | `text` | `/api/typ01/url/kma_snow_day.php` | `sd`, `tm`, `tm_st`, `stn`, `snow`, `help` |
| `kma_snow_day_2` | 적설관측 | `text` | `/api/typ01/url/kma_snow_day.php` | `sd`, `tm`, `tm_st`, `help` |
| `kma_sfctm_uv` | 자외선관측 | `text` | `/api/typ01/url/kma_sfctm_uv.php` | `tm`, `stn`, `help` |
| `aws_nph_aws_min_obj` | AWS 객관분석 | `text` | `/api/typ01/cgi-bin/aws/nph-aws_min_obj` | `obs`, `tm`, `obj`, `map`, `grid`, `stn`, `gov` |
| `aws_nph_sfc_obs_img` | AWS 객관분석 | `text` | `/api/typ01/cgi-bin/aws/nph-sfc_obs_img` | `tm`, `obs`, `acc`, `val`, `stn`, `obj`, `map`, `xp`, `yp`, `lon`, `lat`, `zoom`, `size`, `legend`, `lonlat`, `typ`, `wv`, `gov` |
| `sfc_ssn` | 계절관측 | `text` | `/api/typ01/url/sfc_ssn.php` | `stn`, `tm1`, `tm2` |
| `sfc_ssn_2` | 계절관측 | `text` | `/api/typ01/url/sfc_ssn.php` | `stn`, `tm1`, `tm2`, `ssn` |
| `sfc_ssn_norm` | 계절관측 | `text` | `/api/typ01/url/sfc_ssn_norm.php` | `tmst`, `stn`, `MM1`, `DD1`, `MM2`, `DD2` |
| `sfc_ssn_norm_2` | 계절관측 | `text` | `/api/typ01/url/sfc_ssn_norm.php` | `stn`, `MM1`, `DD1`, `MM2`, `DD2`, `ssn` |
| `stn_inf` | 지상관측 지점정보 | `text` | `/api/typ01/url/stn_inf.php` | `inf`, `stn`, `tm`, `help` |

## 해양관측

| 함수 | 서비스 | 응답 | path | 파라미터 |
|---|---|---|---|---|
| `sea_obs` | 해양기상부이·파고부이관측 | `text` | `/api/typ01/url/sea_obs.php` | `tm`, `stn`, `help` |
| `kma_buoy2` | 해양기상부이·파고부이관측 | `text` | `/api/typ01/url/kma_buoy2.php` | `tm1`, `tm2`, `stn`, `help` |
| `kma_buoy` | 해양기상부이·파고부이관측 | `text` | `/api/typ01/url/kma_buoy.php` | `tm`, `stn`, `help` |
| `sea_mtly_info_service_get_note` | 해양기상부이·파고부이관측 | `structured` | `/api/typ02/openApi/SeaMtlyInfoService/getNote` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `sea_mtly_info_service_get_buoy_lst_tbl` | 해양기상부이·파고부이관측 | `structured` | `/api/typ02/openApi/SeaMtlyInfoService/getBuoyLstTbl` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `sea_mtly_info_service_get_lhaws_lst_tbl` | 해양기상부이·파고부이관측 | `structured` | `/api/typ02/openApi/SeaMtlyInfoService/getLhawsLstTbl` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `sea_mtly_info_service_get_wave_buoy_lst_tbl` | 해양기상부이·파고부이관측 | `structured` | `/api/typ02/openApi/SeaMtlyInfoService/getWaveBuoyLstTbl` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `sea_mtly_info_service_get_obs_open_year` | 해양기상부이·파고부이관측 | `structured` | `/api/typ02/openApi/SeaMtlyInfoService/getObsOpenYear` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `sea_mtly_info_service_get_buoy_mm_sumry` | 해양기상부이·파고부이관측 | `structured` | `/api/typ02/openApi/SeaMtlyInfoService/getBuoyMmSumry` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `sea_mtly_info_service_get_buoy_mm_sumry2` | 해양기상부이·파고부이관측 | `structured` | `/api/typ02/openApi/SeaMtlyInfoService/getBuoyMmSumry2` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `sea_mtly_info_service_get_daily_buoy` | 해양기상부이·파고부이관측 | `structured` | `/api/typ02/openApi/SeaMtlyInfoService/getDailyBuoy` | `pageNo`, `numOfRows`, `dataType`, `year`, `month`, `station` |
| `sea_mtly_info_service_get_lhaws_mm_sumry` | 해양기상부이·파고부이관측 | `structured` | `/api/typ02/openApi/SeaMtlyInfoService/getLhawsMmSumry` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `sea_mtly_info_service_get_lhaws_mm_sumry2` | 해양기상부이·파고부이관측 | `structured` | `/api/typ02/openApi/SeaMtlyInfoService/getLhawsMmSumry2` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `sea_mtly_info_service_get_daily_lhaws` | 해양기상부이·파고부이관측 | `structured` | `/api/typ02/openApi/SeaMtlyInfoService/getDailyLhaws` | `pageNo`, `numOfRows`, `dataType`, `year`, `month`, `station` |
| `sea_mtly_info_service_get_wave_buoy_mm_sumry` | 해양기상부이·파고부이관측 | `structured` | `/api/typ02/openApi/SeaMtlyInfoService/getWaveBuoyMmSumry` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `sea_mtly_info_service_get_wave_buoy_mm_sumry2` | 해양기상부이·파고부이관측 | `structured` | `/api/typ02/openApi/SeaMtlyInfoService/getWaveBuoyMmSumry2` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `sea_mtly_info_service_get_daily_wave_buoy` | 해양기상부이·파고부이관측 | `structured` | `/api/typ02/openApi/SeaMtlyInfoService/getDailyWaveBuoy` | `pageNo`, `numOfRows`, `dataType`, `year`, `month`, `station` |
| `aws3_nph_sea_obs_imgp1` | 해양기상부이·파고부이관측 | `image` | `/api/typ03/cgi/aws3/nph-sea_obs_imgp1` | - |
| `kma_lhaws` | 등표기상관측 | `text` | `/api/typ01/url/kma_lhaws.php` | `tm`, `stn`, `help` |
| `kma_lhaws2` | 등표기상관측 | `text` | `/api/typ01/url/kma_lhaws2.php` | `tm1`, `tm2`, `stn`, `help` |
| `kma_kship` | 기상1호 | `text` | `/api/typ01/url/kma_kship.php` | `tm`, `stn`, `help` |

## 고층관측

| 함수 | 서비스 | 응답 | path | 파라미터 |
|---|---|---|---|---|
| `upp_temp` | 레윈존데 | `text` | `/api/typ01/url/upp_temp.php` | `tm`, `stn`, `pa`, `help` |
| `sea_kship_temp` | 레윈존데 | `text` | `/api/typ01/url/sea_kship_temp.php` | `tm`, `stn`, `pa`, `help` |
| `upp_mbl_temp` | 레윈존데 | `text` | `/api/typ01/url/upp_mbl_temp.php` | `tm`, `stn`, `pa`, `help` |
| `upp_raw_max` | 레윈존데 | `text` | `/api/typ01/url/upp_raw_max.php` | `tm1`, `tm2`, `stn`, `help` |
| `upp_idx` | 레윈존데 | `text` | `/api/typ01/url/upp_idx.php` | `tm1`, `tm2`, `stn`, `help` |
| `upp_mtly_info_service_get_note` | 레윈존데 | `structured` | `/api/typ02/openApi/UppMtlyInfoService/getNote` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `upp_mtly_info_service_get_upp_lst_tbl` | 레윈존데 | `structured` | `/api/typ02/openApi/UppMtlyInfoService/getUppLstTbl` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `upp_mtly_info_service_get_std_isbrsf_value` | 레윈존데 | `structured` | `/api/typ02/openApi/UppMtlyInfoService/getStdIsbrsfValue` | `pageNo`, `numOfRows`, `dataType`, `year`, `month`, `station` |
| `upp_mtly_info_service_get_max_wind` | 레윈존데 | `structured` | `/api/typ02/openApi/UppMtlyInfoService/getMaxWind` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `upp_mtly_info_service_get_ta_hm_level` | 레윈존데 | `structured` | `/api/typ02/openApi/UppMtlyInfoService/getTaHmLevel` | `pageNo`, `numOfRows`, `dataType`, `year`, `month`, `station` |
| `upp_mtly_info_service_get_wind_level` | 레윈존데 | `structured` | `/api/typ02/openApi/UppMtlyInfoService/getWindLevel` | `pageNo`, `numOfRows`, `dataType`, `year`, `month`, `station` |
| `kma_wpf` | 연직바람관측 | `text` | `/api/typ01/url/kma_wpf.php` | `tm`, `stn`, `mode`, `help` |
| `kma_wpf_file_down` | 연직바람관측 | `file` | `/api/typ01/url/kma_wpf_file_down.php` | `wpf`, `stn`, `tm` |
| `stn_wpf` | 고층관측 지점정보 | `text` | `/api/typ01/url/stn_wpf.php` | `tm`, `stn`, `raw`, `help` |

## 레이더

| 함수 | 서비스 | 응답 | path | 파라미터 |
|---|---|---|---|---|
| `rdr_stn_file_list` | 레이더 강수량(HSR) | `file` | `/api/typ01/url/rdr_stn_file_list.php` | `stn`, `rdr`, `tm`, `size` |
| `rdr_cmp_file_list` | 레이더 강수량(HSR) | `file` | `/api/typ01/url/rdr_cmp_file_list.php` | `cmp`, `tm` |
| `rdr_cmp_inf` | 레이더 강수량(HSR) | `text` | `/api/typ01/cgi-bin/url/nph-rdr_cmp_inf` | `tm`, `cmp`, `qcd` |
| `rdr_cmp1_api` | 레이더 강수량(HSR) | `text` | `/api/typ01/cgi-bin/url/nph-rdr_cmp1_api` | `tm`, `cmp`, `qcd`, `obs`, `map`, `disp` |
| `rdr_cmp1_api_2` | 레이더 강수량(HSR) | `text` | `/api/typ01/cgi-bin/url/nph-rdr_cmp1_api` | `tm`, `cmp`, `qcd`, `obs`, `acc`, `map`, `disp` |
| `wthr_radar_info_service_get_comp_cappi_qcd_all` | 레이더 강수량(HSR) | `structured` | `/api/typ02/openApi/WthrRadarInfoService/getCompCappiQcdAll` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `compType`, `dataTypeCd` |
| `wthr_radar_info_service_get_comp_cappi_qcd_area` | 레이더 강수량(HSR) | `structured` | `/api/typ02/openApi/WthrRadarInfoService/getCompCappiQcdArea` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `compType`, `dataTypeCd`, `dongCode` |
| `rdr_latlon_api` | 레이더 강수량(HSR) | `text` | `/api/typ01/cgi-bin/url/nph-rdr_latlon_api` | `cmp`, `latlon`, `disp` |
| `rdr_latlon_file_down` | 레이더 강수량(HSR) | `file` | `/api/typ01/url/rdr_latlon_file_down.php` | `cmp` |
| `rdr_cmp_file` | 레이더 강수량 | `file` | `/api/typ04/url/rdr_cmp_file.php` | `tm`, `data`, `cmp` |
| `wthr_radar_info_service_get_site_cappi_qcd_all` | 레이더 강수량 | `structured` | `/api/typ02/openApi/WthrRadarInfoService/getSiteCappiQcdAll` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `dataTypeCd`, `siteCode`, `sweep` |
| `wthr_radar_info_service_get_site_cappi_qcd_area` | 레이더 강수량 | `structured` | `/api/typ02/openApi/WthrRadarInfoService/getSiteCappiQcdArea` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `dataTypeCd`, `siteCode`, `sweep`, `dongCode` |
| `rdr_nph_rdr_cmp1_img` | 레이더 강수량 | `image` | `/api/typ03/cgi/rdr/nph-rdr_cmp1_img` | `tm`, `cmp`, `qcd`, `obs`, `color`, `aws`, `acc`, `map`, `grid`, `legend`, `size`, `itv`, `zoom_level`, `zoom_x`, `zoom_y`, `gov` |
| `rdr_nph_rdr_wis_ana_img` | 레이더 강수량 | `image` | `/api/typ03/cgi/rdr/nph-rdr_wis_ana_img` | `tm`, `obs`, `wv`, `ht`, `map`, `grid`, `legend`, `size`, `itv`, `zoom_level`, `zoom_x`, `zoom_y`, `gov` |
| `rdr_nph_rdr_obs_ta_h_img` | 레이더 강수량 | `image` | `/api/typ03/cgi/rdr/nph-rdr_obs_taH_img` | `tm`, `obs`, `ta1`, `ta2`, `map`, `grid`, `legend`, `size`, `itv`, `zoom_level`, `zoom_x`, `zoom_y`, `gov` |
| `rdr_nph_qpf_ana_img` | 레이더 강수량 | `image` | `/api/typ03/cgi/rdr/nph-qpf_ana_img` | `tm`, `qpf`, `eva`, `option`, `ef`, `map`, `grid`, `legend`, `size`, `itv`, `zoom_level`, `zoom_x`, `zoom_y`, `gov` |
| `rdr_nph_rdr_cmp1_imgp` | 레이더 강수량 | `image` | `/api/typ03/cgi/rdr/nph-rdr_cmp1_imgp` | `PROJ`, `cmp`, `obs`, `qcd`, `grid`, `itv`, `tm_mode`, `data0`, `level`, `map`, `dtm`, `zoom_level`, `zoom_rate`, `zoom_x`, `zoom_y`, `auto_man`, `mode`, `umove`, `fmove`, `dmove`, `bmove`, `winnum`, `rand`, `size`, `an_frn`, `an_itv`, `river`, `road`, `city`, `gis_auto`, `stnname`, `ctrl`, `dataDtlCd`, `data1`, `data2`, `data3`, `overlay`, `color`, `effect`, `height`, `qpf`, `ef`, `legend`, `STARTX`, `STARTY`, `ENDX`, `ENDY`, `ZOOMLVL`, `selWs`, `tm`, `tm_st`, `tm_ed`, `tm2` |
| `rdr_nph_rdr_wis_ana_imgp` | 레이더 강수량 | `image` | `/api/typ03/cgi/rdr/nph-rdr_wis_ana_imgp` | `PROJ`, `cmp`, `obs`, `qcd`, `grid`, `itv`, `tm_mode`, `data0`, `level`, `map`, `dtm`, `zoom_level`, `zoom_rate`, `zoom_x`, `zoom_y`, `auto_man`, `mode`, `umove`, `fmove`, `dmove`, `bmove`, `winnum`, `rand`, `size`, `an_frn`, `an_itv`, `river`, `road`, `city`, `gis_auto`, `stnname`, `ctrl`, `dataDtlCd`, `data1`, `data2`, `data3`, `overlay`, `color`, `effect`, `height`, `qpf`, `ef`, `eva`, `option`, `legend`, `acc`, `sms`, `STARTX`, `STARTY`, `ENDX`, `ENDY`, `ZOOMLVL`, `selWs`, `tm`, `tm_st`, `tm_ed`, `tm2` |
| `rdr_nph_rdr_obs_ta_h_imgp` | 레이더 강수량 | `image` | `/api/typ03/cgi/rdr/nph-rdr_obs_taH_imgp` | `PROJ`, `cmp`, `obs`, `qcd`, `grid`, `itv`, `tm_mode`, `data0`, `level`, `map`, `dtm`, `zoom_level`, `zoom_rate`, `zoom_x`, `zoom_y`, `auto_man`, `mode`, `umove`, `fmove`, `dmove`, `bmove`, `winnum`, `rand`, `size`, `an_frn`, `an_itv`, `river`, `road`, `city`, `gis_auto`, `stnname`, `ctrl`, `dataDtlCd`, `data1`, `data2`, `data3`, `overlay`, `color`, `effect`, `height`, `qpf`, `ef`, `eva`, `option`, `legend`, `acc`, `sms`, `STARTX`, `STARTY`, `ENDX`, `ENDY`, `ZOOMLVL`, `selWs`, `tm`, `tm_st`, `tm_ed`, `tm2` |
| `rdr_nph_qpf_ana_imgp` | 레이더 강수량 | `image` | `/api/typ03/cgi/rdr/nph-qpf_ana_imgp` | `PROJ`, `cmp`, `obs`, `qcd`, `grid`, `itv`, `tm_mode`, `data0`, `level`, `map`, `dtm`, `zoom_level`, `zoom_rate`, `zoom_x`, `zoom_y`, `auto_man`, `mode`, `umove`, `fmove`, `dmove`, `bmove`, `winnum`, `rand`, `size`, `an_frn`, `an_itv`, `river`, `road`, `city`, `gis_auto`, `stnname`, `ctrl`, `dataDtlCd`, `data1`, `data2`, `data3`, `overlay`, `color`, `effect`, `height`, `qpf`, `ef`, `eva`, `option`, `STARTX`, `STARTY`, `ENDX`, `ENDY`, `ZOOMLVL`, `selWs`, `tm`, `tm_st`, `tm_ed`, `tm2` |
| `rdr_uf_list` | 레이더 원시자료 | `text` | `/api/typ01/url/rdr_uf_list.php` | `tm`, `dtm`, `stn`, `qcd`, `disp`, `help` |
| `rdr_file_list` | 레이더 원시자료 | `file` | `/api/typ01/url/rdr_file_list.php` | `rdr`, `qcd`, `tm` |
| `rdr_uf_inf` | 레이더 원시자료 | `text` | `/api/typ01/cgi-bin/url/nph-rdr_uf_inf` | `tm`, `stn`, `qcd`, `help` |
| `rdr_uf_data` | 레이더 원시자료 | `text` | `/api/typ01/cgi-bin/url/nph-rdr_uf_data` | `tm`, `stn`, `qcd`, `vol`, `sw`, `mode`, `help` |
| `rdr_file_down` | 레이더 원시자료 | `file` | `/api/typ01/url/rdr_file_down.php` | `rdr`, `stn`, `qcd`, `tm` |
| `rdr_file_down_nc` | 레이더 원시자료 | `file` | `/api/typ01/url/rdr_file_down_nc.php` | `rdr`, `stn`, `qcd`, `tm` |
| `rdr_site_file` | 레이더 원시자료 | `file` | `/api/typ04/url/rdr_site_file.php` | `tm`, `data`, `stn` |
| `rdr_cmp_aws_pt_data` | 레이더 AWS지점별 합성자료값 | `text` | `/api/typ01/cgi-bin/url/nph-rdr_cmp_aws_pt_data` | `tm1`, `tm2`, `itv`, `qcd`, `cmp`, `stn`, `help` |
| `rdr_cmp_aws_all_pt_data` | 레이더 AWS지점별 합성자료값 | `text` | `/api/typ01/cgi-bin/url/nph-rdr_cmp_aws_all_pt_data` | `tm`, `qcd`, `cmp`, `help` |
| `lgt_kma_np1` | 낙뢰관측 | `text` | `/api/typ01/url/lgt_kma_np1.php` | `tm1`, `tm2`, `help` |
| `lgt_kma_np2` | 낙뢰관측 | `text` | `/api/typ01/url/lgt_kma_np2.php` | `tm1`, `tm2`, `help` |
| `lgt_kma_np3` | 낙뢰관측 | `text` | `/api/typ01/url/lgt_kma_np3.php` | `tm1`, `tm2`, `help` |
| `lgt_kma_nx1` | 낙뢰관측 | `text` | `/api/typ01/url/lgt_kma_nx1.php` | `tm1`, `tm2`, `help` |
| `lgt_pnt` | 낙뢰관측 | `text` | `/api/typ01/url/lgt_pnt.php` | `tm`, `itv` |
| `lgt_pnt_2` | 낙뢰관측 | `text` | `/api/typ01/url/lgt_pnt.php` | `tm`, `itv`, `lon`, `lat`, `range` |
| `lgt_pnt_3` | 낙뢰관측 | `text` | `/api/typ01/url/lgt_pnt.php` | `tm`, `itv`, `lon`, `lat`, `range`, `gc` |
| `lgt_stn` | 낙뢰관측 | `text` | `/api/typ01/url/lgt_stn.php` | `tp`, `tm`, `range` |
| `lgt_nph_lgt_str_img` | 낙뢰관측 | `image` | `/api/typ03/cgi/lgt/nph-lgt_str_img` | `obs`, `tm`, `val`, `stn`, `obj`, `map`, `grid`, `legend`, `size`, `itv`, `zoom_level`, `zoom_x`, `zoom_y`, `gov` |
| `lgt_nph_lgt_ana_img` | 낙뢰관측 | `image` | `/api/typ03/cgi/lgt/nph-lgt_ana_img` | `obs`, `tm`, `val`, `stn`, `obj`, `map`, `grid`, `legend`, `size`, `itv`, `zoom_level`, `zoom_x`, `zoom_y`, `gov` |
| `lgt_nph_lgt_dst_img` | 낙뢰관측 | `image` | `/api/typ03/cgi/lgt/nph-lgt_dst_img` | `obs`, `tm`, `val`, `stn`, `obj`, `map`, `grid`, `legend`, `size`, `itv`, `zoom_level`, `zoom_x`, `zoom_y`, `gov` |
| `lgt_admndst_cnt` | 낙뢰관측 | `text` | `/api/typ01/url/lgt_admndst_cnt.php` | `admdst_dv`, `unit`, `interval`, `tm`, `disp`, `help` |
| `wethr_basic_info_service_get_radar_obs_stn` | 레이더 지점정보 | `structured` | `/api/typ02/openApi/WethrBasicInfoService/getRadarObsStn` | `pageNo`, `numOfRows`, `dataType` |

## 위성

| 함수 | 서비스 | 응답 | path | 파라미터 |
|---|---|---|---|---|
| `nr016_fd_data` | 천리안 2A호 | `file` | `/api/typ05/api/GK2A/LE1B/NR016/FD/data` | `date` |
| `sw038_tp_data_list` | 천리안 2A호 | `structured` | `/api/typ05/api/GK2A/LE1B/SW038/TP/dataList` | `sDate`, `eDate` |
| `vi004_ea_image` | 천리안 2A호 | `text` | `/api/typ05/api/GK2A/LE1B/VI004/EA/image` | `date` |
| `vi005_fd_image_list` | 천리안 2A호 | `structured` | `/api/typ05/api/GK2A/LE1B/VI005/FD/imageList` | `sDate`, `eDate` |
| `ci_ela_data` | 천리안 2A호 | `file` | `/api/typ05/api/GK2A/LE2/CI/ELA/data` | `date` |
| `so2_d_ko_data_list` | 천리안 2A호 | `structured` | `/api/typ05/api/GK2A/LE2/SO2D/KO/dataList` | `sDate`, `eDate` |
| `cld_ea_image` | 천리안 2A호 | `text` | `/api/typ05/api/GK2A/LE2/CLD/EA/image` | `date` |
| `rr_ea_image_list` | 천리안 2A호 | `structured` | `/api/typ05/api/GK2A/LE2/RR/EA/imageList` | `sDate`, `eDate` |
| `pd_e_1_m_na_data` | 천리안 2A호 | `file` | `/api/typ05/api/GK2A/LV1/PD-E-1M/NA/data` | `date` |
| `pd_e_1_m_na_data_list` | 천리안 2A호 | `structured` | `/api/typ05/api/GK2A/LV1/PD-E-1M/NA/dataList` | `sDate`, `eDate` |
| `sat_nph_sat_ana_txt` | 천리안 2A호 | `text` | `/api/typ01/cgi-bin/sat/nph-sat_ana_txt` | `tm`, `obs`, `help` |
| `sat_nph_sat_ana_img` | 천리안 2A호 | `text` | `/api/typ01/cgi-bin/sat/nph-sat_ana_img` | `obs`, `tm`, `size`, `sat`, `map`, `xp`, `yp`, `zoom`, `scn` |
| `sat_file_down2` | 천리안 2A호 | `file` | `/api/typ01/url/sat_file_down2.php` | `lvl`, `dat`, `are`, `tm`, `typ` |
| `sat_file_list` | 천리안 2A호 | `file` | `/api/typ01/url/sat_file_list.php` | `sat`, `vars`, `area`, `fmt`, `tm`, `size`, `filter` |
| `sat_file_down2_2` | 천리안 2A호 | `file` | `/api/typ01/url/sat_file_down2.php` | `typ`, `lvl`, `are`, `chn`, `tm` |
| `sat_file_down2_3` | 천리안 2A호 | `file` | `/api/typ01/url/sat_file_down2.php` | `typ`, `lvl`, `are`, `dat`, `tm` |
| `cloud_satlit_info_service_get_gk2acla_area` | 천리안 2A호 | `structured` | `/api/typ02/openApi/CloudSatlitInfoService/getGk2aclaArea` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `resultType`, `dongCode` |
| `cloud_satlit_info_service_get_gk2adcoew_area` | 천리안 2A호 | `structured` | `/api/typ02/openApi/CloudSatlitInfoService/getGk2adcoewArea` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `resultType`, `dongCode` |
| `cloud_satlit_info_service_get_gk2afog_area` | 천리안 2A호 | `structured` | `/api/typ02/openApi/CloudSatlitInfoService/getGk2afogArea` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `resultType`, `dongCode` |
| `cloud_satlit_info_service_get_gk2aapps_area` | 천리안 2A호 | `structured` | `/api/typ02/openApi/CloudSatlitInfoService/getGk2aappsArea` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `resultType`, `dongCode` |
| `cloud_satlit_info_service_get_gk2acld_area` | 천리안 2A호 | `structured` | `/api/typ02/openApi/CloudSatlitInfoService/getGk2acldArea` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `resultType`, `dongCode` |
| `cloud_satlit_info_service_get_gk2acla_all` | 천리안 2A호 | `structured` | `/api/typ02/openApi/CloudSatlitInfoService/getGk2aclaAll` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `resultType` |
| `cloud_satlit_info_service_get_gk2adcoew_all` | 천리안 2A호 | `structured` | `/api/typ02/openApi/CloudSatlitInfoService/getGk2adcoewAll` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `resultType` |
| `cloud_satlit_info_service_get_gk2afog_all` | 천리안 2A호 | `structured` | `/api/typ02/openApi/CloudSatlitInfoService/getGk2afogAll` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `resultType` |
| `cloud_satlit_info_service_get_gk2aapps_all` | 천리안 2A호 | `structured` | `/api/typ02/openApi/CloudSatlitInfoService/getGk2aappsAll` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `resultType` |
| `cloud_satlit_info_service_get_gk2acld_all` | 천리안 2A호 | `structured` | `/api/typ02/openApi/CloudSatlitInfoService/getGk2acldAll` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `resultType` |
| `wthr_satlit_info_service_get_gk2a_ir_all` | 천리안 2A호 | `structured` | `/api/typ02/openApi/WthrSatlitInfoService/getGk2aIrAll` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `waveType`, `unitType` |
| `wthr_satlit_info_service_get_gk2a_nr_all` | 천리안 2A호 | `structured` | `/api/typ02/openApi/WthrSatlitInfoService/getGk2aNrAll` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `waveType`, `unitType` |
| `wthr_satlit_info_service_get_gk2a_sw_all` | 천리안 2A호 | `structured` | `/api/typ02/openApi/WthrSatlitInfoService/getGk2aSwAll` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `waveType`, `unitType` |
| `wthr_satlit_info_service_get_gk2a_vi_all` | 천리안 2A호 | `structured` | `/api/typ02/openApi/WthrSatlitInfoService/getGk2aViAll` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `waveType`, `unitType` |
| `wthr_satlit_info_service_get_gk2a_wv_all` | 천리안 2A호 | `structured` | `/api/typ02/openApi/WthrSatlitInfoService/getGk2aWvAll` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `waveType`, `unitType` |
| `wthr_satlit_info_service_get_gk2a_ir_area` | 천리안 2A호 | `structured` | `/api/typ02/openApi/WthrSatlitInfoService/getGk2aIrArea` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `waveType`, `unitType`, `dongCode` |
| `wthr_satlit_info_service_get_gk2a_nr_area` | 천리안 2A호 | `structured` | `/api/typ02/openApi/WthrSatlitInfoService/getGk2aNrArea` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `waveType`, `unitType`, `dongCode` |
| `wthr_satlit_info_service_get_gk2a_sw_area` | 천리안 2A호 | `structured` | `/api/typ02/openApi/WthrSatlitInfoService/getGk2aSwArea` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `waveType`, `unitType`, `dongCode` |
| `wthr_satlit_info_service_get_gk2a_vi_area` | 천리안 2A호 | `structured` | `/api/typ02/openApi/WthrSatlitInfoService/getGk2aViArea` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `waveType`, `unitType`, `dongCode` |
| `wthr_satlit_info_service_get_gk2a_wv_area` | 천리안 2A호 | `structured` | `/api/typ02/openApi/WthrSatlitInfoService/getGk2aWvArea` | `pageNo`, `numOfRows`, `dataType`, `dateTime`, `waveType`, `unitType`, `dongCode` |
| `sat_nph_gk2a_img` | 천리안 2A호 | `image` | `/api/typ03/cgi/sat/nph-gk2a_img` | `tm`, `obs`, `map`, `grid`, `legend`, `size`, `itv`, `zoom_level`, `zoom_x`, `zoom_y`, `gov` |
| `sat_nph_gk2a_imgp` | 천리안 2A호 | `image` | `/api/typ03/cgi/sat/nph-gk2a_imgp` | `PROJ`, `cmp`, `obs`, `qcd`, `grid`, `itv`, `tm_mode`, `data0`, `level`, `map`, `dtm`, `zoom_level`, `zoom_rate`, `zoom_x`, `zoom_y`, `auto_man`, `mode`, `umove`, `fmove`, `dmove`, `bmove`, `winnum`, `rand`, `size`, `an_frn`, `an_itv`, `river`, `road`, `city`, `gis_auto`, `stnname`, `ctrl`, `dataDtlCd`, `data1`, `data2`, `data3`, `overlay`, `color`, `effect`, `height`, `qpf`, `ef`, `band1`, `legend`, `scn`, `STARTX`, `STARTY`, `ENDX`, `ENDY`, `ZOOMLVL`, `selWs`, `tm`, `tm_st`, `tm_ed`, `tm2` |
| `gk2a_latlon_api` | 천리안 2A호 | `text` | `/api/typ01/cgi-bin/url/nph-gk2a_latlon_api` | `area`, `grid`, `latlon`, `disp` |
| `gk2a_latlon_file_down` | 천리안 2A호 | `file` | `/api/typ01/url/gk2a_latlon_file_down.php` | `area`, `grid` |
| `vi004_ea_data` | 천리안 2A호 | `file` | `/api/typ05/api/GK2A/LE1B/VI004/EA/data` | `date` |
| `vi004_ea_data_list` | 천리안 2A호 | `structured` | `/api/typ05/api/GK2A/LE1B/VI004/EA/dataList` | `sDate`, `eDate` |
| `vi004_ea_image_list` | 천리안 2A호 | `structured` | `/api/typ05/api/GK2A/LE1B/VI004/EA/imageList` | `sDate`, `eDate` |
| `sat_file_list_2` | 천리안 1호 | `file` | `/api/typ01/url/sat_file_list.php` | `sat`, `fmt`, `tm` |
| `sat_data` | 천리안 1호 | `text` | `/api/typ01/cgi-bin/url/nph-sat_data` | `sat`, `chn`, `tm`, `help` |
| `coms_pnt` | 천리안 1호 | `text` | `/api/typ01/cgi-bin/url/nph-coms_pnt` | `tm1`, `tm2`, `obs`, `lon`, `lat`, `help` |
| `coms_pnt_vars` | 천리안 1호 | `text` | `/api/typ01/url/coms_pnt_vars.php` | `tm1`, `tm2`, `lon`, `lat`, `help` |
| `coms_stns` | 천리안 1호 | `text` | `/api/typ01/cgi-bin/url/nph-coms_stns` | `tm1`, `tm2`, `obs`, `stn`, `help` |
| `coms_stns_vars` | 천리안 1호 | `text` | `/api/typ01/url/coms_stns_vars.php` | `tm1`, `tm2`, `stn`, `help` |
| `coms_stn_ca` | 천리안 1호 | `text` | `/api/typ01/cgi-bin/url/nph-coms_stn_ca` | `tm`, `range`, `help` |
| `sat_coms_obs_file` | 천리안 1호 | `file` | `/api/typ04/url/sat_coms_obs_file.php` | `tm`, `ch`, `map` |

## 지진/화산

| 함수 | 서비스 | 응답 | path | 파라미터 |
|---|---|---|---|---|
| `eqk_now` | 국내·외 지진정보 | `text` | `/api/typ01/url/eqk_now.php` | `tm`, `disp`, `help` |
| `eqk_list` | 국내·외 지진정보 | `text` | `/api/typ01/url/eqk_list.php` | `tm1`, `tm2`, `disp`, `help` |
| `eqk_info_service_get_eqk_msg_list` | 국내·외 지진정보 | `structured` | `/api/typ02/openApi/EqkInfoService/getEqkMsgList` | `pageNo`, `numOfRows`, `dataType`, `fromTmFc`, `toTmFc` |
| `eqk_info_service_get_eqk_msg` | 국내·외 지진정보 | `structured` | `/api/typ02/openApi/EqkInfoService/getEqkMsg` | `pageNo`, `numOfRows`, `dataType`, `fromTmFc`, `toTmFc` |
| `eqk_url_new_noti_eqk` | 국내·외 지진정보 | `text` | `/api/typ09/url/eqk/urlNewNotiEqk.do` | `orderTy`, `orderCm` |
| `eqk_url_new_noti_eqk_2` | 국내·외 지진정보 | `text` | `/api/typ09/url/eqk/urlNewNotiEqk.do` | `orderTy`, `frDate`, `laDate`, `msgCode`, `cntDiv`, `arDiv`, `eqArCd`, `nkDiv` |
| `eqk_url_sec_eqk_list` | 국내·외 지진정보 | `text` | `/api/typ09/url/eqk/urlSecEqkList.do` | `orderTy`, `mTeqId`, `frDate`, `laDate`, `afDiv`, `frMagMl`, `laMagMl`, `type` |
| `tsnm_url_tsnm_list` | 지진해일정보 | `text` | `/api/typ09/url/tsnm/urlTsnmList.do` | `orderTy`, `orderCm` |
| `tsnm_url_tsnm_list_2` | 지진해일정보 | `text` | `/api/typ09/url/tsnm/urlTsnmList.do` | `orderTy`, `frDate`, `laDate` |
| `eqk_info_service_get_tsunami_msg_list` | 지진해일정보 | `structured` | `/api/typ02/openApi/EqkInfoService/getTsunamiMsgList` | `pageNo`, `numOfRows`, `dataType`, `fromTmFc`, `toTmFc` |
| `eqk_info_service_get_tsunami_msg` | 지진해일정보 | `structured` | `/api/typ02/openApi/EqkInfoService/getTsunamiMsg` | `pageNo`, `numOfRows`, `dataType`, `fromTmFc`, `toTmFc` |
| `volc_select_volc_info_list` | 화산정보 | `text` | `/api/typ09/url/volc/selectVolcInfoList.do` | `orderTy`, `orderCm` |
| `volc_select_volc_info_list_2` | 화산정보 | `text` | `/api/typ09/url/volc/selectVolcInfoList.do` | `orderTy`, `frDate`, `laDate` |

## 태풍

| 함수 | 서비스 | 응답 | path | 파라미터 |
|---|---|---|---|---|
| `typ_lst` | 태풍정보 | `text` | `/api/typ01/url/typ_lst.php` | `YY`, `disp`, `help` |
| `typ_data` | 태풍정보 | `text` | `/api/typ01/url/typ_data.php` | `YY`, `typ`, `seq`, `mode`, `disp`, `help` |
| `typ_now` | 태풍정보 | `text` | `/api/typ01/url/typ_now.php` | `tm`, `mode`, `disp`, `help` |
| `sfc_yearly_info_service_get_typhoon_list` | 태풍정보 | `structured` | `/api/typ02/openApi/SfcYearlyInfoService/getTyphoonList` | `pageNo`, `numOfRows`, `dataType`, `year` |
| `td_lst` | 태풍정보(TD) | `text` | `/api/typ01/url/td_lst.php` | `YY`, `disp`, `help` |
| `td_data` | 태풍정보(TD) | `text` | `/api/typ01/url/td_data.php` | `YY`, `td`, `seq`, `mode`, `disp`, `help` |
| `td_now` | 태풍정보(TD) | `text` | `/api/typ01/url/td_now.php` | `tm`, `mode`, `disp`, `help` |
| `typ_besttrack` | 태풍 베스트트랙 | `text` | `/api/typ01/url/typ_besttrack.php` | `year`, `grade`, `tcid`, `help` |

## 수치모델

| 함수 | 서비스 | 응답 | path | 파라미터 |
|---|---|---|---|---|
| `nwp_vars_down` | 수치예보모델 | `file` | `/api/typ06/url/nwp_vars_down.php` | `nwp`, `sub`, `vars`, `pres`, `tmfc`, `ef`, `dataType` |
| `kim_grib_xy_txt1` | 수치예보모델 | `text` | `/api/typ06/cgi-bin/url/nph-kim_grib_xy_txt1` | `group`, `nwp`, `data`, `varn`, `level`, `tmfc`, `hf`, `disp` |
| `kim_grib_xz_txt1` | 수치예보모델 | `text` | `/api/typ06/cgi-bin/url/nph-kim_grib_xz_txt1` | `group`, `nwp`, `data`, `varn`, `lvl_lst`, `tmfc`, `hf`, `lon1`, `lat1`, `lon2`, `lat2`, `disp` |
| `kim_grib_xz_txt1_2` | 수치예보모델 | `text` | `/api/typ06/cgi-bin/url/nph-kim_grib_xz_txt1` | `group`, `nwp`, `data`, `varn`, `lvl_lst`, `tmfc`, `hf`, `map`, `lon1`, `lat1`, `lon2`, `lat2`, `disp` |
| `kim_grib_pt_txt1` | 수치예보모델 | `text` | `/api/typ06/cgi-bin/url/nph-kim_grib_pt_txt1` | `group`, `nwp`, `data`, `varn`, `tmfc`, `hf`, `X`, `Y`, `disp`, `help` |
| `kim_grib_pt_txt1_2` | 수치예보모델 | `text` | `/api/typ06/cgi-bin/url/nph-kim_grib_pt_txt1` | `group`, `nwp`, `data`, `varn`, `tmfc`, `hf`, `lon`, `lat`, `level`, `help` |
| `kim_grib_pt_tmfc` | 수치예보모델 | `text` | `/api/typ06/url/kim_grib_pt_tmfc.php` | `group`, `nwp`, `data`, `varn`, `tmfc`, `ef`, `X`, `Y`, `level`, `help` |
| `kim_grib_pt_tmef` | 수치예보모델 | `text` | `/api/typ06/url/kim_grib_pt_tmef.php` | `group`, `nwp`, `data`, `varn`, `tmef`, `lon`, `lat`, `level`, `help` |
| `kim_model_info_service_get_kim_ldaps_unis_all` | 수치예보모델 | `structured` | `/api/typ02/openApi/KIMModelInfoService/getKIMLdapsUnisAll` | `baseTime`, `leadHour`, `dataTypeCd`, `dataType` |
| `kim_model_info_service_get_kim_rdaps_unis_all` | 수치예보모델 | `structured` | `/api/typ02/openApi/KIMModelInfoService/getKIMRdapsUnisAll` | `baseTime`, `leadHour`, `dataTypeCd`, `dataType` |
| `kim_model_info_service_get_kim_ldaps_unis_area` | 수치예보모델 | `structured` | `/api/typ02/openApi/KIMModelInfoService/getKIMLdapsUnisArea` | `baseTime`, `dataTypeCd`, `dataType`, `dongCode` |
| `kim_model_info_service_get_kim_rdaps_unis_area` | 수치예보모델 | `structured` | `/api/typ02/openApi/KIMModelInfoService/getKIMRdapsUnisArea` | `baseTime`, `dataTypeCd`, `dataType`, `dongCode` |
| `kim_nc_xy_txt1` | 수치예보모델 | `text` | `/api/typ06/cgi-bin/url/nph-kim_nc_xy_txt1` | `group`, `nwp`, `data`, `name`, `map`, `tmfc`, `hf`, `disp`, `help`, `level` |
| `kim_nc_xy_txt1_2` | 수치예보모델 | `text` | `/api/typ06/cgi-bin/url/nph-kim_nc_xy_txt1` | `group`, `nwp`, `data`, `name`, `map`, `sub`, `sm`, `tmfc`, `hf`, `disp`, `help`, `level` |
| `kim_nc_pt_txt1` | 수치예보모델 | `text` | `/api/typ06/cgi-bin/url/nph-kim_nc_pt_txt1` | `group`, `nwp`, `data`, `name`, `tmfc`, `hf`, `disp`, `help`, `X`, `Y` |
| `kim_nc_pt_txt1_2` | 수치예보모델 | `text` | `/api/typ06/cgi-bin/url/nph-kim_nc_pt_txt1` | `group`, `nwp`, `data`, `name`, `tmfc`, `hf`, `disp`, `help`, `lat`, `lon` |
| `kim_nc_xy_txt2` | 수치예보모델 | `text` | `/api/typ01/cgi-bin/url/nph-kim_nc_xy_txt2` | `group`, `nwp`, `data`, `name`, `map`, `tmfc`, `hf`, `disp`, `help`, `level` |
| `kim_nc_xy_txt2_2` | 수치예보모델 | `text` | `/api/typ01/cgi-bin/url/nph-kim_nc_xy_txt2` | `group`, `nwp`, `data`, `name`, `map`, `sub`, `sm`, `tmfc`, `hf`, `disp`, `help`, `level` |
| `kim_nc_pt_txt2` | 수치예보모델 | `text` | `/api/typ01/cgi-bin/url/nph-kim_nc_pt_txt2` | `group`, `nwp`, `data`, `name`, `tmfc`, `hf`, `disp`, `help`, `X`, `Y` |
| `kim_nc_pt_txt2_2` | 수치예보모델 | `text` | `/api/typ01/cgi-bin/url/nph-kim_nc_pt_txt2` | `group`, `nwp`, `data`, `name`, `tmfc`, `hf`, `disp`, `help`, `lat`, `lon` |
| `marine_large_zone` | 수치예보모델 | `text` | `/api/typ06/url/marine_large_zone.php` | `tma_fc`, `tma_ef`, `Lzone`, `help`, `disp` |
| `marine_small_zone` | 수치예보모델 | `text` | `/api/typ06/url/marine_small_zone.php` | `tma_fc`, `tma_ef`, `Lzone`, `Szone`, `disp`, `help` |
| `nwp_latlon_api` | 수치예보모델 | `text` | `/api/typ01/cgi-bin/url/nph-nwp_latlon_api` | `nwp`, `latlon`, `disp` |
| `nwp_latlon_file_down` | 수치예보모델 | `file` | `/api/typ01/url/nwp_latlon_file_down.php` | `nwp` |
| `nwp_header` | 수치예보모델 | `text` | `/api/typ06/cgi-bin/url/nph-nwp_header` | `model`, `nwp`, `sub`, `tmfc`, `ef`, `help` |
| `um_grib_xy_txt1` | 수치예보모델 | `text` | `/api/typ06/cgi-bin/url/nph-um_grib_xy_txt1` | `group`, `nwp`, `data`, `varn`, `level`, `tmfc`, `hf`, `disp` |
| `um_grib_xy_txt1_2` | 수치예보모델 | `text` | `/api/typ06/cgi-bin/url/nph-um_grib_xy_txt1` | `group`, `nwp`, `data`, `varn`, `level`, `map`, `sub`, `sm`, `tmfc`, `hf`, `disp` |
| `um_grib_xy_txt1_3` | 수치예보모델 | `text` | `/api/typ06/cgi-bin/url/nph-um_grib_xy_txt1` | `group`, `nwp`, `data`, `varn`, `level`, `map`, `sm`, `tmfc`, `hf`, `disp` |
| `um_grib_xz_txt1` | 수치예보모델 | `text` | `/api/typ06/cgi-bin/url/nph-um_grib_xz_txt1` | `group`, `nwp`, `data`, `varn`, `lvl_lst`, `map`, `tmfc`, `hf`, `lon1`, `lat1`, `lon2`, `lat2`, `disp` |
| `um_grib_pt_txt1` | 수치예보모델 | `text` | `/api/typ06/cgi-bin/url/nph-um_grib_pt_txt1` | `group`, `nwp`, `data`, `varn`, `tmfc`, `hf`, `X`, `Y`, `disp`, `help` |
| `um_grib_pt_txt1_2` | 수치예보모델 | `text` | `/api/typ06/cgi-bin/url/nph-um_grib_pt_txt1` | `group`, `nwp`, `data`, `varn`, `tmfc`, `hf`, `level`, `X`, `Y`, `disp`, `help` |
| `um_grib_pt_txt1_3` | 수치예보모델 | `text` | `/api/typ06/cgi-bin/url/nph-um_grib_pt_txt1` | `group`, `nwp`, `data`, `varn`, `tmfc`, `hf`, `lon`, `lat`, `disp`, `help` |
| `um_grib_pt_tmfc` | 수치예보모델 | `text` | `/api/typ06/url/um_grib_pt_tmfc.php` | `group`, `nwp`, `data`, `varn`, `tmfc`, `ef`, `X`, `Y`, `level`, `help` |
| `um_grib_pt_tmef` | 수치예보모델 | `text` | `/api/typ06/url/um_grib_pt_tmef.php` | `group`, `nwp`, `data`, `varn`, `tmef`, `lon`, `lat`, `level`, `help` |
| `nwp_grib_down` | 수치예보모델 | `file` | `/api/typ06/url/nwp_grib_down.php` | `group`, `nwp`, `data`, `varn`, `level`, `tmfc`, `hf` |
| `nwp_model_info_service_get_ldaps_unis_all` | 수치예보모델 | `structured` | `/api/typ02/openApi/NwpModelInfoService/getLdapsUnisAll` | `pageNo`, `numOfRows`, `dataType`, `baseTime`, `leadHour`, `dataTypeCd` |
| `nwp_model_info_service_get_ldaps_unis_area` | 수치예보모델 | `structured` | `/api/typ02/openApi/NwpModelInfoService/getLdapsUnisArea` | `pageNo`, `numOfRows`, `dataType`, `baseTime`, `dongCode`, `dataTypeCd` |
| `nwp_model_info_service_get_rdaps_unis_all` | 수치예보모델 | `structured` | `/api/typ02/openApi/NwpModelInfoService/getRdapsUnisAll` | `pageNo`, `numOfRows`, `dataType`, `baseTime`, `leadHour`, `dataTypeCd`, `dongCode` |
| `nwp_model_info_service_get_rdaps_unis_area` | 수치예보모델 | `structured` | `/api/typ02/openApi/NwpModelInfoService/getRdapsUnisArea` | `pageNo`, `numOfRows`, `dataType`, `baseTime`, `dongCode`, `dataTypeCd` |
| `dfs_nph_qpf_ana_img` | 초단기예측 | `image` | `/api/typ03/cgi/dfs/nph-qpf_ana_img` | `eva`, `tm`, `qpf`, `ef`, `map`, `grid`, `legend`, `size`, `zoom_level`, `zoom_x`, `zoom_y`, `stn`, `x1`, `y1` |
| `api_iwa_img_url_api_ret_recreate_img_url` | 수치모델 그래픽 | `image` | `/api/typ07/afsiwa/iwa/api/iwaImgUrlApi/retRecreateImgUrl.kfrm` | `analTime`, `isTyp`, `imageType`, `groupName`, `meta` |
| `api_iwa_img_url_api_ret_composite2_img_url` | 수치모델 그래픽 | `image` | `/api/typ07/afsiwa/iwa/api/iwaImgUrlApi/retComposite2ImgUrl.kfrm` | `analTime`, `foreTime` |
| `api_iwa_img_url_api_ret_composite1_img_url` | 수치모델 그래픽 | `image` | `/api/typ07/afsiwa/iwa/api/iwaImgUrlApi/retComposite1ImgUrl.kfrm` | `analTime`, `foreTime` |
| `api_iwa_img_url_api_ret_model_img_url` | 수치모델 그래픽 | `image` | `/api/typ07/afsiwa/iwa/api/iwaImgUrlApi/retModelImgUrl.kfrm` | `modl`, `varGrp`, `var`, `lev`, `analTime`, `foreTime`, `PROJ`, `mapRange`, `ZOOMLVL`, `stLon`, `stLat`, `edLon`, `edLat`, `basicSmtLvl`, `basicTotSmtLvl`, `repDispCd`, `symblDispType`, `isRasterFillCheck`, `meta`, `symbl` |
| `api_iwa_img_url_api_ret_fore_img_url` | 수치모델 그래픽 | `image` | `/api/typ07/afsiwa/iwa/api/iwaImgUrlApi/retForeImgUrl.kfrm` | `varGrp`, `var`, `modl`, `lev`, `analTime`, `foreTime`, `PROJ`, `ZOOMLVL`, `stLon`, `stLat`, `edLon`, `edLat`, `basicSmtLvl`, `basicTotSmtLvl`, `repDispCd`, `symblDispType`, `isRasterFillCheck` |
| `api_iwa_img_url_api_ret_ens_img_url` | 수치모델 그래픽 | `image` | `/api/typ07/afsiwa/iwa/api/iwaImgUrlApi/retEnsImgUrl.kfrm` | `modl`, `ensType`, `varGrp`, `var`, `mem`, `lev`, `analTime`, `foreTime`, `PROJ`, `ZOOMLVL`, `stLon`, `stLat`, `edLon`, `edLat`, `basicTotSmtLvl`, `repDispCd`, `symblDispType`, `isRasterFillCheck`, `meta`, `symbl` |
| `api_iwa_img_url_api_ret_ocean_img_url` | 수치모델 그래픽 | `image` | `/api/typ07/afsiwa/iwa/api/iwaImgUrlApi/retOceanImgUrl.kfrm` | `modlGrp`, `modl`, `var`, `mem`, `lev`, `analTime`, `foreTime`, `PROJ`, `ZOOMLVL`, `stLon`, `stLat`, `edLon`, `edLat`, `basicTotSmtLvl`, `repDispCd`, `symblDispType`, `isRasterFillCheck`, `meta`, `symbl` |
| `api_iwa_img_url_api_ret_crss_sctn_img_url` | 수치모델 그래픽 | `image` | `/api/typ07/afsiwa/iwa/api/iwaImgUrlApi/retCrssSctnImgUrl.kfrm` | `modelCd`, `variable`, `isFill3`, `analTime`, `foreTime`, `locationLon01`, `locationLat01`, `locationLon02`, `locationLat02`, `minPresAlt`, `maxPresAlt`, `log`, `width`, `height`, `layerInfo` |
| `api_iwa_img_url_api_ret_back_map_url` | 수치모델 그래픽 | `image` | `/api/typ07/afsiwa/iwa/api/iwaImgUrlApi/retBackMapUrl.kfrm` | `type`, `projection`, `ZOOMLVL`, `stLon`, `stLat`, `edLon`, `edLat`, `meta` |
| `api_iwa_img_url_api_ret_obs_img_url` | 수치모델 그래픽 | `image` | `/api/typ07/afsiwa/iwa/api/iwaImgUrlApi/retObsImgUrl.kfrm` | `obs`, `varGrp`, `var`, `lev`, `analTime`, `PROJ`, `ZOOMLVL`, `stLon`, `stLat`, `edLon`, `edLat`, `basicSmtLvl`, `basicTotSmtLvl`, `repDispCd`, `symblDispType`, `meta` |
| `api_iwa_img_url_api_ret_mdl_sample_data_url` | 수치모델 그래픽 | `image` | `/api/typ07/afsiwa/iwa/api/iwaImgUrlApi/retMdlSampleDataUrl.kfrm` | `menuGrpCd`, `menu01`, `menu02`, `menu03`, `varListCd`, `vrtcLayrCd`, `analTime`, `foreTime`, `basicSmtLvl`, `location`, `project`, `meta` |
| `api_iwa_img_url_api_ret_model_img_url_2` | 수치모델 그래픽 | `image` | `/api/typ07/afsiwa/iwa/api/iwaImgUrlApi/retModelImgUrl.kfrm` | `modl`, `varGrp`, `var`, `lev`, `analTime`, `foreTime`, `PROJ`, `ZOOMLVL`, `stLon`, `stLat`, `edLon`, `edLat`, `basicSmtLvl`, `basicTotSmtLvl`, `repDispCd`, `symblDispType`, `isRasterFillCheck`, `meta`, `symbl` |
| `api_iwa_img_url_api_ret_back_map_url_2` | 수치모델 그래픽 | `image` | `/api/typ07/afsiwa/iwa/api/iwaImgUrlApi/retBackMapUrl.kfrm` | `type`, `projection`, `ZOOMLVL`, `stLon`, `stLat`, `edLon`, `edLat`, `meta`, `mdl`, `basicSmtLvl` |
| `api_iwa_img_url_api_ret_grid_img` | 수치모델 그래픽 | `image` | `/api/typ07/afsiwa/iwa/api/iwaImgUrlApi/retGridImg.kfrm` | `PROJ`, `ZOOMLVL`, `stLon`, `stLat`, `edLon`, `edLat`, `contourLineColor`, `contourLineDiv`, `contourLineThck`, `meta`, `mdl`, `basicSmtLvl` |
| `wthr_chart_info_service_get_auxillary_chart` | 분석일기도 | `structured` | `/api/typ02/openApi/WthrChartInfoService/getAuxillaryChart` | `pageNo`, `numOfRows`, `dataType`, `code1`, `code2`, `time` |
| `wthr_chart_info_service_get_surface_chart` | 분석일기도 | `structured` | `/api/typ02/openApi/WthrChartInfoService/getSurfaceChart` | `pageNo`, `numOfRows`, `dataType`, `code`, `time` |

## 예특보

| 함수 | 서비스 | 응답 | path | 파라미터 |
|---|---|---|---|---|
| `fct_shrt_reg` | 단기예보 | `text` | `/api/typ01/url/fct_shrt_reg.php` | `tmfc` |
| `fct_afs_ds` | 단기예보 | `text` | `/api/typ01/url/fct_afs_ds.php` | `stn`, `tmfc1`, `tmfc2`, `disp`, `help` |
| `fct_afs_dl` | 단기예보 | `text` | `/api/typ01/url/fct_afs_dl.php` | `reg`, `tmfc1`, `tmfc2`, `disp`, `help` |
| `fct_afs_dl2` | 단기예보 | `text` | `/api/typ01/url/fct_afs_dl2.php` | `reg`, `tmfc1`, `tmfc2`, `disp`, `help` |
| `fct_afs_do` | 단기예보 | `text` | `/api/typ01/url/fct_afs_do.php` | `reg`, `tmfc1`, `tmfc2`, `disp`, `help` |
| `dfs_shrt_grd` | 단기예보 | `text` | `/api/typ01/cgi-bin/url/nph-dfs_shrt_grd` | `tmfc`, `tmef`, `vars` |
| `dfs_vsrt_grd` | 단기예보 | `text` | `/api/typ01/cgi-bin/url/nph-dfs_vsrt_grd` | `tmfc`, `tmef`, `vars` |
| `dfs_odam_grd` | 단기예보 | `text` | `/api/typ01/cgi-bin/url/nph-dfs_odam_grd` | `tmfc`, `vars` |
| `dfs_xy_lonlat` | 단기예보 | `text` | `/api/typ01/cgi-bin/url/nph-dfs_xy_lonlat` | `x`, `y`, `help` |
| `dfs_xy_lonlat_2` | 단기예보 | `text` | `/api/typ01/cgi-bin/url/nph-dfs_xy_lonlat` | `lon`, `lat`, `help` |
| `vilage_fcst_msg_service_get_wthr_situation` | 단기예보 | `structured` | `/api/typ02/openApi/VilageFcstMsgService/getWthrSituation` | `pageNo`, `numOfRows`, `dataType`, `stnId` |
| `vilage_fcst_msg_service_get_land_fcst` | 단기예보 | `structured` | `/api/typ02/openApi/VilageFcstMsgService/getLandFcst` | `pageNo`, `numOfRows`, `dataType`, `regId` |
| `vilage_fcst_msg_service_get_land_fcst_2` | 단기예보 | `structured` | `/api/typ02/openApi/VilageFcstMsgService/getLandFcst` | `pageNo`, `numOfRows`, `dataType` |
| `vilage_fcst_msg_service_get_sea_fcst` | 단기예보 | `structured` | `/api/typ02/openApi/VilageFcstMsgService/getSeaFcst` | `pageNo`, `numOfRows`, `dataType`, `regId` |
| `vilage_fcst_msg_service_get_sea_fcst_2` | 단기예보 | `structured` | `/api/typ02/openApi/VilageFcstMsgService/getSeaFcst` | `pageNo`, `numOfRows`, `dataType` |
| `vilage_fcst_info_service_2_0_get_ultra_srt_ncst` | 단기예보 | `structured` | `/api/typ02/openApi/VilageFcstInfoService_2.0/getUltraSrtNcst` | `pageNo`, `numOfRows`, `dataType`, `base_date`, `base_time`, `nx`, `ny` |
| `vilage_fcst_info_service_2_0_get_ultra_srt_fcst` | 단기예보 | `structured` | `/api/typ02/openApi/VilageFcstInfoService_2.0/getUltraSrtFcst` | `pageNo`, `numOfRows`, `dataType`, `base_date`, `base_time`, `nx`, `ny` |
| `vilage_fcst_info_service_2_0_get_vilage_fcst` | 단기예보 | `structured` | `/api/typ02/openApi/VilageFcstInfoService_2.0/getVilageFcst` | `pageNo`, `numOfRows`, `dataType`, `base_date`, `base_time`, `nx`, `ny` |
| `vilage_fcst_info_service_2_0_get_fcst_version` | 단기예보 | `structured` | `/api/typ02/openApi/VilageFcstInfoService_2.0/getFcstVersion` | `pageNo`, `numOfRows`, `dataType`, `ftype`, `basedatetime` |
| `dfs_nph_dfs_shrt_ana_5d_test` | 단기예보 | `image` | `/api/typ03/cgi/dfs/nph-dfs_shrt_ana_5d_test` | `data0`, `data1`, `tm_ef`, `tm_fc`, `dtm`, `map`, `mask`, `color`, `size`, `effect`, `overlay`, `zoom_rate`, `zoom_level`, `zoom_x`, `zoom_y`, `auto_man`, `mode`, `interval`, `rand` |
| `dfs_nph_dfs_vsrt_ana2` | 단기예보 | `image` | `/api/typ03/cgi/dfs/nph-dfs_vsrt_ana2` | `data0`, `tm_fc`, `data1`, `tm_ef`, `dtm`, `map`, `mask`, `color`, `size`, `effect`, `overlay`, `zoom_rate`, `zoom_level`, `zoom_x`, `zoom_y`, `auto_man`, `mode`, `rand` |
| `dfs_latlon_api` | 단기예보 | `text` | `/api/typ01/cgi-bin/url/nph-dfs_latlon_api` | `fct`, `latlon`, `disp` |
| `dfs_latlon_file_down` | 단기예보 | `file` | `/api/typ01/url/dfs_latlon_file_down.php` | `fct` |
| `fct_medm_reg` | 중기예보 | `text` | `/api/typ01/url/fct_medm_reg.php` | `tmfc` |
| `fct_afs_ws` | 중기예보 | `text` | `/api/typ01/url/fct_afs_ws.php` | `stn`, `tmfc1`, `tmfc2`, `disp`, `help` |
| `fct_afs_wl` | 중기예보 | `text` | `/api/typ01/url/fct_afs_wl.php` | `reg`, `tmfc1`, `tmfc2`, `tmef1`, `tmef2`, `disp`, `help` |
| `fct_afs_wc` | 중기예보 | `text` | `/api/typ01/url/fct_afs_wc.php` | `reg`, `tmfc1`, `tmfc2`, `tmef1`, `tmef2`, `disp`, `help` |
| `fct_afs_wo` | 중기예보 | `text` | `/api/typ01/url/fct_afs_wo.php` | `reg`, `tmfc1`, `tmfc2`, `tmef1`, `tmef2`, `disp`, `help` |
| `mid_fcst_info_service_get_mid_sea_fcst` | 중기예보 | `structured` | `/api/typ02/openApi/MidFcstInfoService/getMidSeaFcst` | `pageNo`, `numOfRows`, `dataType`, `regId`, `tmFc` |
| `mid_fcst_info_service_get_mid_sea_fcst_2` | 중기예보 | `structured` | `/api/typ02/openApi/MidFcstInfoService/getMidSeaFcst` | `pageNo`, `numOfRows`, `dataType`, `tmFc` |
| `mid_fcst_info_service_get_mid_ta` | 중기예보 | `structured` | `/api/typ02/openApi/MidFcstInfoService/getMidTa` | `pageNo`, `numOfRows`, `dataType`, `regId`, `tmFc` |
| `mid_fcst_info_service_get_mid_ta_2` | 중기예보 | `structured` | `/api/typ02/openApi/MidFcstInfoService/getMidTa` | `pageNo`, `numOfRows`, `dataType`, `tmFc` |
| `mid_fcst_info_service_get_mid_land_fcst` | 중기예보 | `structured` | `/api/typ02/openApi/MidFcstInfoService/getMidLandFcst` | `pageNo`, `numOfRows`, `dataType`, `regId`, `tmFc` |
| `mid_fcst_info_service_get_mid_land_fcst_2` | 중기예보 | `structured` | `/api/typ02/openApi/MidFcstInfoService/getMidLandFcst` | `pageNo`, `numOfRows`, `dataType`, `tmFc` |
| `mid_fcst_info_service_get_mid_fcst` | 중기예보 | `structured` | `/api/typ02/openApi/MidFcstInfoService/getMidFcst` | `pageNo`, `numOfRows`, `dataType`, `stnId`, `tmFc` |
| `wrn_reg` | 기상특보 | `text` | `/api/typ01/url/wrn_reg.php` | `tmfc` |
| `wrn_met_data` | 기상특보 | `text` | `/api/typ01/url/wrn_met_data.php` | `reg`, `wrn`, `tmfc1`, `tmfc2`, `disp`, `help` |
| `wrn_inf_rpt` | 기상특보 | `text` | `/api/typ01/url/wrn_inf_rpt.php` | `tmfc1`, `tmfc2`, `stn`, `disp`, `help` |
| `wthr_cmt_rpt` | 기상특보 | `text` | `/api/typ01/url/wthr_cmt_rpt.php` | `tmfc1`, `tmfc2`, `stn`, `subcd`, `disp`, `help` |
| `wrn_now_data` | 기상특보 | `text` | `/api/typ01/url/wrn_now_data.php` | `fe`, `tm`, `disp`, `help` |
| `wrn_now_data_new` | 기상특보 | `text` | `/api/typ01/url/wrn_now_data_new.php` | `fe`, `tm`, `disp`, `help` |
| `wrn_nph_wrn7` | 기상특보 | `image` | `/api/typ03/cgi/wrn/nph-wrn7` | `out`, `tmef`, `city`, `name`, `tm`, `lon`, `lat`, `range`, `size`, `wrn` |
| `ifs_fct_pstt` | 영향예보 | `text` | `/api/typ01/url/ifs_fct_pstt.php` | `tmef1`, `tmef2`, `ifpar`, `help` |
| `ifs_fct_pstt_2` | 영향예보 | `text` | `/api/typ01/url/ifs_fct_pstt.php` | `tmfc1`, `tmfc2`, `ifpar`, `help` |
| `ifs_fct_pstt_3` | 영향예보 | `text` | `/api/typ01/url/ifs_fct_pstt.php` | `tmef1`, `tmef2`, `ifarea`, `regid`, `help` |
| `ifs_ilvl_zone_cnt` | 영향예보 | `text` | `/api/typ01/url/ifs_ilvl_zone_cnt.php` | `help`, `tmfc1`, `tmfc2` |
| `ifs_ilvl_zone_cnt_2` | 영향예보 | `text` | `/api/typ01/url/ifs_ilvl_zone_cnt.php` | `help`, `tmef1`, `tmef2` |
| `ifs_ilvl_zone_cnt_3` | 영향예보 | `text` | `/api/typ01/url/ifs_ilvl_zone_cnt.php` | `help`, `tmef1`, `tmef2`, `ifarea`, `stn` |
| `ifs_ilvl_zone_cnt_4` | 영향예보 | `text` | `/api/typ01/url/ifs_ilvl_zone_cnt.php` | `help`, `tmef1`, `tmef2`, `ilvl` |
| `ifs_ilvl_dmap` | 영향예보 | `text` | `/api/typ01/url/ifs_ilvl_dmap.php` | `tmfc` |
| `ifs_ilvl_dmap_2` | 영향예보 | `text` | `/api/typ01/url/ifs_ilvl_dmap.php` | `tmfc`, `stn` |
| `ifs_ilvl_dmap_3` | 영향예보 | `text` | `/api/typ01/url/ifs_ilvl_dmap.php` | `tmfc`, `ifpar` |
| `ifs_ilvl_dmap_4` | 영향예보 | `text` | `/api/typ01/url/ifs_ilvl_dmap.php` | `tmfc`, `ifarea` |
| `fcst_zone_info_service_get_fcst_zone_cd` | 예·특보 구역정보 | `structured` | `/api/typ02/openApi/FcstZoneInfoService/getFcstZoneCd` | `pageNo`, `numOfRows`, `dataType`, `regId` |
| `fcst_zone_info_service_get_fcst_zone_cd_2` | 예·특보 구역정보 | `structured` | `/api/typ02/openApi/FcstZoneInfoService/getFcstZoneCd` | `pageNo`, `numOfRows`, `dataType` |
| `wethr_basic_info_service_get_wrn_zone_cd` | 예·특보 구역정보 | `structured` | `/api/typ02/openApi/WethrBasicInfoService/getWrnZoneCd` | `pageNo`, `numOfRows`, `dataType`, `korName` |
| `wrn_reg_aws` | 예·특보 구역정보 | `text` | `/api/typ01/url/wrn_reg_aws.php` | `tm`, `disp`, `help` |
| `wrn_reg_aws2` | 예·특보 구역정보 | `text` | `/api/typ01/url/wrn_reg_aws2.php` | `tm`, `disp`, `help` |

## 세계기상

| 함수 | 서비스 | 응답 | path | 파라미터 |
|---|---|---|---|---|
| `gts_syn1` | GTS 관측 | `text` | `/api/typ01/url/gts_syn1.php` | `tm`, `dtm`, `stn`, `help` |
| `gts_bufr_syn1` | GTS 관측 | `text` | `/api/typ01/url/gts_bufr_syn1.php` | `tm`, `dtm`, `stn`, `help` |
| `gts_bufr_syn` | GTS 관측 | `text` | `/api/typ01/url/gts_bufr_syn.php` | `tm`, `dtm`, `stn`, `help` |
| `gts_syn` | GTS 관측 | `text` | `/api/typ01/url/gts_syn.php` | `tm`, `dtm`, `stn`, `help` |
| `gts_ship1` | GTS 관측 | `text` | `/api/typ01/url/gts_ship1.php` | `tm`, `dtm`, `help` |
| `gts_bufr_ship` | GTS 관측 | `text` | `/api/typ01/url/gts_bufr_ship.php` | `tm`, `dtm`, `help` |
| `gts_ship` | GTS 관측 | `text` | `/api/typ01/url/gts_ship.php` | `tm`, `dtm`, `help` |
| `gts_buoy1` | GTS 관측 | `text` | `/api/typ01/url/gts_buoy1.php` | `tm`, `dtm`, `stn`, `help` |
| `gts_buoy2` | GTS 관측 | `text` | `/api/typ01/url/gts_buoy2.php` | `tm`, `dtm`, `stn`, `help` |
| `gts_bufr_buoy` | GTS 관측 | `text` | `/api/typ01/url/gts_bufr_buoy.php` | `tm`, `dtm`, `stn`, `help` |
| `gts_buoy` | GTS 관측 | `text` | `/api/typ01/url/gts_buoy.php` | `tm`, `dtm`, `stn`, `help` |
| `gts_temp1` | GTS 관측 | `text` | `/api/typ01/url/gts_temp1.php` | `tm`, `stn`, `pa`, `help` |
| `gts_bufr_temp` | GTS 관측 | `text` | `/api/typ01/url/gts_bufr_temp.php` | `tm`, `stn`, `pa`, `help` |
| `gts_temp` | GTS 관측 | `text` | `/api/typ01/url/gts_temp.php` | `tm`, `stn`, `pa`, `help` |
| `gts_pilot` | GTS 관측 | `text` | `/api/typ01/url/gts_pilot.php` | `tm`, `stn`, `help` |
| `gts_airep1` | GTS 관측 | `text` | `/api/typ01/url/gts_airep1.php` | `tm`, `dtm`, `stn`, `help` |
| `gts_metar_dec` | GTS 관측 | `text` | `/api/typ01/url/gts_metar_dec.php` | `tm1`, `tm2`, `help` |
| `amdar_bufr` | GTS 관측 | `text` | `/api/typ01/cgi-bin/url/nph-amdar_bufr` | `flag`, `tm` |
| `amdar_bufr_2` | GTS 관측 | `text` | `/api/typ01/cgi-bin/url/nph-amdar_bufr` | `flag`, `tm`, `lon1`, `lat1`, `lon2`, `lat2`, `mode`, `pa` |
| `amdar_bufr_3` | GTS 관측 | `text` | `/api/typ01/cgi-bin/url/nph-amdar_bufr` | `flag`, `tm`, `lon1`, `lat1`, `lon2`, `lat2`, `mode` |
| `amdar_bufr_4` | GTS 관측 | `text` | `/api/typ01/cgi-bin/url/nph-amdar_bufr` | `flag`, `tm`, `aircraft`, `fname` |
| `gts_cht_sfc` | GTS 관측 | `text` | `/api/typ01/url/gts_cht_sfc.php` | `tm`, `help` |
| `gts_cht_sfc_tot` | GTS 관측 | `text` | `/api/typ01/url/gts_cht_sfc_tot.php` | `tm`, `help` |
| `gts_cht_syn` | GTS 관측 | `text` | `/api/typ01/url/gts_cht_syn.php` | `tm`, `help` |
| `gts_cht_syn_2` | GTS 관측 | `text` | `/api/typ01/url/gts_cht_syn.php` | `tm`, `lon1`, `lon2`, `lat1`, `lat2`, `help` |
| `gts_cht_temp` | GTS 관측 | `text` | `/api/typ01/url/gts_cht_temp.php` | `tm`, `stn`, `pa`, `lon1`, `lon2`, `lat1`, `lat2`, `help` |
| `gts_cht_pilot` | GTS 관측 | `text` | `/api/typ01/url/gts_cht_pilot.php` | `tm`, `stn`, `help` |
| `gts_info_service_get_buoy` | GTS 관측 | `structured` | `/api/typ02/openApi/GtsInfoService/getBuoy` | `numOfRows`, `pageNo`, `dataType`, `tm`, `stnId` |
| `gts_info_service_get_synop` | GTS 관측 | `structured` | `/api/typ02/openApi/GtsInfoService/getSynop` | `numOfRows`, `pageNo`, `dataType`, `tm`, `stnId` |
| `gts_info_service_get_temp` | GTS 관측 | `structured` | `/api/typ02/openApi/GtsInfoService/getTemp` | `numOfRows`, `pageNo`, `dataType`, `tm`, `stnId` |
| `stn_gts1` | GTS 지점정보 | `text` | `/api/typ01/url/stn_gts1.php` | `tm`, `ra`, `stn`, `upp`, `mode` |
| `gts_info_service_get_gts_stn` | GTS 지점정보 | `structured` | `/api/typ02/openApi/GtsInfoService/getGtsStn` | `numOfRows`, `pageNo`, `dataType`, `cc`, `category` |
| `ncei_gsoh_data` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsoh_data.php` | `tm`, `stns` |
| `ncei_gsoh_data_2` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsoh_data.php` | `tm1`, `tm2`, `stns` |
| `ncei_gsoh_file` | NCEI 관측·통계 | `file` | `/api/typ01/url/ncei_gsoh_file.php` | `YY`, `stn` |
| `ncei_gsoh_list` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsoh_list.php` | `YY` |
| `ncei_gsod_data` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsod_data.php` | `tm`, `stns` |
| `ncei_gsod_data_2` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsod_data.php` | `tm1`, `tm2`, `stns` |
| `ncei_gsod_data_3` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsod_data.php` | `tm`, `lon1`, `lon2`, `lat1`, `lat2` |
| `ncei_gsod_file` | NCEI 관측·통계 | `file` | `/api/typ01/url/ncei_gsod_file.php` | `YY`, `stn` |
| `ncei_gsod_list` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsod_list.php` | `YY` |
| `ncei_gsom_data` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsom_data.php` | `tm`, `stns` |
| `ncei_gsom_data_2` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsom_data.php` | `tm1`, `tm2`, `stns` |
| `ncei_gsom_data_3` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsom_data.php` | `tm`, `lon1`, `lon2`, `lat1`, `lat2` |
| `ncei_gsom_file` | NCEI 관측·통계 | `file` | `/api/typ01/url/ncei_gsom_file.php` | `stn` |
| `ncei_gsom_list` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsom_list.php` | - |
| `ncei_gsoy_data` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsoy_data.php` | `tm`, `stns` |
| `ncei_gsoy_data_2` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsoy_data.php` | `tm1`, `tm2`, `stns` |
| `ncei_gsoy_data_3` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsoy_data.php` | `tm`, `lon1`, `lon2`, `lat1`, `lat2` |
| `ncei_gsoy_file` | NCEI 관측·통계 | `file` | `/api/typ01/url/ncei_gsoy_file.php` | `stn` |
| `ncei_gsoy_list` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsoy_list.php` | - |
| `ncei_upp_data` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_upp_data.php` | `tm`, `stns` |
| `ncei_upp_data_2` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_upp_data.php` | `tm1`, `tm2`, `stns` |
| `ncei_upp_data_3` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_upp_data.php` | `tm`, `lon1`, `lon2`, `lat1`, `lat2` |
| `ncei_upp_file` | NCEI 관측·통계 | `file` | `/api/typ01/url/ncei_upp_file.php` | `stn` |
| `ncei_upp_list` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_upp_list.php` | - |
| `ncei_gsea_data` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsea_data.php` | `tm`, `stns` |
| `ncei_gsea_data_2` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsea_data.php` | `tm1`, `tm2`, `stns` |
| `ncei_gsea_data_3` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsea_data.php` | `tm1`, `tm2`, `lon1`, `lon2`, `lat1`, `lat2` |
| `ncei_gsea_file` | NCEI 관측·통계 | `file` | `/api/typ01/url/ncei_gsea_file.php` | `YM`, `file` |
| `ncei_gsea_list` | NCEI 관측·통계 | `text` | `/api/typ01/url/ncei_gsea_list.php` | `YM` |

## 항공기상

| 함수 | 서비스 | 응답 | path | 파라미터 |
|---|---|---|---|---|
| `amm_iwxxm_service_get_metar` | 항공기상관측(METAR) | `structured` | `/api/typ02/openApi/AmmIwxxmService/getMetar` | `pageNo`, `numOfRows`, `dataType`, `icao` |
| `air_metar_dec` | 항공기상관측(METAR) | `text` | `/api/typ01/url/air_metar_dec.php` | `tm`, `org`, `help` |
| `sfc_yearly_info_service_getr_air_stn_lst_tbl` | 항공기상관측(METAR) | `structured` | `/api/typ02/openApi/SfcYearlyInfoService/getrAirStnLstTbl` | `pageNo`, `numOfRows`, `dataType`, `year` |
| `sfc_yearly_info_service_get_air_stn_info` | 항공기상관측(METAR) | `structured` | `/api/typ02/openApi/SfcYearlyInfoService/getAirStnInfo` | `pageNo`, `numOfRows`, `dataType`, `year`, `station` |
| `sfc_yearly_info_service_get_air_stn_info2` | 항공기상관측(METAR) | `structured` | `/api/typ02/openApi/SfcYearlyInfoService/getAirStnInfo2` | `pageNo`, `numOfRows`, `dataType`, `year`, `station` |
| `sfc_yearly_info_service_get_air_stn_info3` | 항공기상관측(METAR) | `structured` | `/api/typ02/openApi/SfcYearlyInfoService/getAirStnInfo3` | `pageNo`, `numOfRows`, `dataType`, `year`, `station` |
| `sfc_yearly_info_service_get_sfc_stn_lst_tbl` | 항공기상관측(METAR) | `structured` | `/api/typ02/openApi/SfcYearlyInfoService/getSfcStnLstTbl` | `pageNo`, `numOfRows`, `dataType`, `year` |
| `sfc_yearly_info_service_get_note` | 항공기상관측(METAR) | `structured` | `/api/typ02/openApi/SfcYearlyInfoService/getNote` | `pageNo`, `numOfRows`, `dataType`, `year` |
| `sfc_mtly_info_service_get_daily_air_data` | 항공기상관측(METAR) | `structured` | `/api/typ02/openApi/SfcMtlyInfoService/getDailyAirData` | `pageNo`, `numOfRows`, `dataType`, `year`, `month`, `station` |
| `sfc_mtly_info_service_getr_air_stn_lst_tbl` | 항공기상관측(METAR) | `structured` | `/api/typ02/openApi/SfcMtlyInfoService/getrAirStnLstTbl` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `sfc_mtly_info_service_get_air_note` | 항공기상관측(METAR) | `structured` | `/api/typ02/openApi/SfcMtlyInfoService/getAirNote` | `pageNo`, `numOfRows`, `dataType`, `year`, `month` |
| `kma_air_tm` | 항공기상관측(METAR) | `text` | `/api/typ01/url/kma_air_tm.php` | `tm1`, `tm2`, `stn`, `help` |
| `amos` | 공항기상관측(AMOS) | `text` | `/api/typ01/url/amos.php` | `tm`, `dtm`, `stn`, `help` |
| `air_info_service_get_air_info` | 공항예·특보 | `structured` | `/api/typ02/openApi/AirInfoService/getAirInfo` | `numOfRows`, `pageNo`, `dataType`, `fctm`, `icaoCode` |
| `amm_iwxxm_service_get_taf` | 공항예·특보 | `structured` | `/api/typ02/openApi/AmmIwxxmService/getTaf` | `pageNo`, `numOfRows`, `dataType`, `icao` |
| `amm_iwxxm_service_get_sigmet` | 공항예·특보 | `structured` | `/api/typ02/openApi/AmmIwxxmService/getSigmet` | `pageNo`, `numOfRows`, `dataType` |
| `amm_iwxxm_service_get_airmet` | 공항예·특보 | `structured` | `/api/typ02/openApi/AmmIwxxmService/getAirmet` | `pageNo`, `numOfRows`, `dataType` |
| `aftn_amm_service_get_metar` | 공항예·특보 | `structured` | `/api/typ02/openApi/AftnAmmService/getMetar` | `pageNo`, `numOfRows`, `dataType`, `icao` |
| `aftn_amm_service_get_sigmet` | 공항예·특보 | `structured` | `/api/typ02/openApi/AftnAmmService/getSigmet` | `pageNo`, `numOfRows`, `dataType`, `icao` |
| `aftn_amm_service_get_taf` | 공항예·특보 | `structured` | `/api/typ02/openApi/AftnAmmService/getTaf` | `pageNo`, `numOfRows`, `dataType`, `icao` |
| `amm_service_get_taf` | 공항예·특보 | `structured` | `/api/typ02/openApi/AmmService/getTaf` | `pageNo`, `numOfRows`, `dataType`, `icao` |
| `amm_service_get_airmet` | 공항예·특보 | `structured` | `/api/typ02/openApi/AmmService/getAirmet` | `pageNo`, `numOfRows`, `dataType` |
| `amm_service_get_sigmet` | 공항예·특보 | `structured` | `/api/typ02/openApi/AmmService/getSigmet` | `pageNo`, `numOfRows`, `dataType` |
| `amm_service_get_warning` | 공항예·특보 | `structured` | `/api/typ02/openApi/AmmService/getWarning` | `pageNo`, `numOfRows`, `dataType` |
| `amdar_kma` | AMDAR 관측 | `text` | `/api/typ01/url/amdar_kma.php` | `tm1`, `tm2`, `st`, `help` |
| `air_port_service_get_air_port` | 공항기상정보 | `structured` | `/api/typ02/openApi/AirPortService/getAirPort` | `numOfRows`, `pageNo`, `dataType`, `base_date`, `base_time`, `airPortCd` |
| `amo_sigwx` | 저고도 기상지원 | `text` | `/api/typ01/url/amo_sigwx.php` | `tmfc` |
| `amo_wintem` | 저고도 기상지원 | `text` | `/api/typ01/url/amo_wintem.php` | `tmfc`, `ef`, `ht` |
| `amo_nwp_file_down` | 저고도 기상지원 | `file` | `/api/typ01/url/amo_nwp_file_down.php` | `tmfc`, `ef` |
| `lidar` | LIDAR 관측자료 | `text` | `/api/typ01/url/lidar.php` | `tm`, `stn`, `var`, `altitude` |

# 🕷️ Data Crawling Pipeline -- 실행 가이드

본 문서는 `mindcastlib` 프로젝트의 **데이터 크롤링 파이프라인 실행
방법**과\
**출력 파일 구조**를 설명합니다.

------------------------------------------------------------------------

## ✅ 1. 크롤링 코드 실행 방법

### 📍 실행 위치

프로젝트 루트(`mindcastlib`) 에서 실행해야합니다 

``` bash
cd /LOCALPATH/mindcastlib

```

### ▶ 실행 명령어 

./run/run_crawling.sh


------------------------------------------------------------------------

## ✅ 2. 출력 파일 구조

크롤링이 완료되면 결과 파일은 아래 구조로 저장됩니다.

``` text
data_suicide_crawling/
 ├─ economic/
 │   ├─ cpi_latest_YYYYMMDD.csv
 │   ├─ gdp_gni_latest_YYYYMMDD.csv
 │   ├─ loan_latest_YYYYMMDD.csv
 │   ├─ average_working_day_latest_YYYYMMDD.csv   
 │   ├─ consumer_price_change_index_latest_YYYYMMDD.csv
 │   ├─ labor_force_latest_YYYYMMDD.csv
 │   └─ working_index_latest_YYYYMMDD.csv
 │   
 ├─ population/
 │   ├─ resident_population_latest_YYYYMMDD.csv
 │   ├─ aver_mid_age_latest_YYYYMMDD.csv
 │   └─ suicide_population_YYYYMMDD.csv
 │   
 ├─ metadata.json
 └─ suicide_base_data_2020_{max_year}_latest_YYYYMMDD.csv
```

## ✅ 실행 파이프라인 설명 

[ crawling_pipeline.py 실행 ]
            │
            ▼
[ YAML 설정 로드 (configs/crawling_config.yaml) ]
            │
            ▼
[ 개별 Collector 순차 실행 ]
  - cpi
  - loan
  - labor_force
  - gdp_gni
  - ...
            │
            ▼
[ concat_database 실행]
            │
            ▼
[ metadata.json 갱신 + 결과 CSV 저장 ]

### 📌 파일 설명

## 📊 Economic Indicators

| 파일명 | 설명 | 단위 | 출처 |
|--------|------|------|------|
| `average_working_day_latest_20260208.csv` | 월별 평균 근로일수 | 일 | 지표누리 |
| `consumer_price_change_index_latest_20260208.csv` | 소비자물가 등락률 (전월 대비 변화율) | % | KOSIS |
| `cpi_latest_20260208.csv` | 소비자물가지수 (CPI) | 지수 | KOSIS |
| `gdp_gni_latest_20260208.csv` | 국내총생산(GDP) 및 국민총소득(GNI) | 십억원 | KOSIS |
| `labor_force_latest_20260208.csv` | 경제활동인구, 비경제활동인구, 취업자, 실업자, 실업률, 고용률, 경제활동참여율 | 천 명, 비율(%) | KOSIS |
| `loan_latest_20260208.csv` | 가계신용, 가계대출, 판매신용 | 십억원 | KOSIS |
| `working_index_latest_20260208.csv` | 전체임금총액, 전체근로일수, 전체근로시간 | 원, 일, 시간 | KOSIS |

---

## 👥 Population Indicators

| 파일명 | 설명 | 단위 | 출처 |
|--------|------|------|------|
| `aver_mid_age_latest_20260208.csv` | 중위연령, 평균연령 | 세 | KOSIS |
| `resident_population_latest_20260208.csv` | 총인구수, 0–14세 구성비, 15–64세 구성비, 고령인구비율 | 명, 비율(%) | KOSIS |
| `suicide_population_latest_20260208.csv`  | 자살자수 | 명 | KOSIS |
---
## METADATA
-metadata.json
예시: 
"cpi": {
    "saved_file": "data_suicide_crawling\\economic\\cpi_latest_20260209.csv" (저장파일 경로), 
    "source_url": "API URL" (API 받아오는 URL),
    "rows": 733 (DATA ROW의 수), 
    "max_date": "2026-01" (해당 데이터의 가장 최근 날짜),
    "collected_at": "2026-02-09T14:25:44 (가장 최근 수집이 된 시간)"
  },

---
## SUICIDE_BASE_DATA

-suicide_base_data_2020_{max_year}_latest_YYYYMMDD.csv

크롤링한 모든 월별 데이터를 공통 기간 기준으로 병합(concat) 합니다.
이때 기준 시점은 각 지표 중 가장 오래된 MAX DATE(가장 짧은 시계열의 최신 시점) 입니다.
즉, 여러 지표 중 가장 최근 데이터가 가장 오래된 지표를 기준으로 기간을 맞춰
모든 데이터의 시점을 동일한 구간으로 정렬합니다.

---

## ✅ 3. 파일명 규칙

모든 출력 파일은 **수집 날짜 기준 최신 파일만 유지**되며,\
파일명에 날짜가 자동으로 붙습니다.

``` text
*_latest_YYYYMMDD.csv
```

---
### 실행결과 예시

2026-02-09 15:08:39,725 | INFO | 🚀 Crawling pipeline started
2026-02-09 15:08:39,725 | INFO | ▶️ Running collector: cpi
✅ CPI 저장: data_suicide_crawling\economic\cpi_latest_20260209.csv rows: 733 max_date: 2026-01
2026-02-09 15:08:41,842 | INFO | ✅ Done: cpi
'
'
'
✅ Resident_Population 저장: data_suicide_crawling\population\resident_population_latest_20260209.csv rows: 217 max_date: 2026-01
2026-02-09 15:11:46,852 | INFO | ✅ Done: resident_population
2026-02-09 15:11:46,853 | INFO | ▶️ Running concat_database
✅ Suicide_Base_Data 저장: data_suicide_crawling\suicide_base_data_2020_2024_20260209.csv rows: 60 max_date: 2024-12
2026-02-09 15:11:47,071 | INFO | ✅ Done: concat_database
2026-02-09 15:11:47,071 | INFO | 🎉 Pipeline finished successfully


------------------------------------------------------------------------




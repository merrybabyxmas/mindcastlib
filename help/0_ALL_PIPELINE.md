# 🚀 전체 통합 데이터 분석 파이프라인 실행 가이드 (최종본)

이 가이드는 프로젝트의 전체 분석 파이프라인을 순서대로 실행하는 명령어와 **가장 중요한 입력/출력 경로 유의사항** 및 **데이터 흐름 구조**를 정리한 것입니다.
---

## 0. 시작 전 환경 설정

| 순서 | 설명 | 터미널 명령어 |
| :--- | :--- | :--- |
| **0.1 경로 이동** | 스크립트가 있는 디렉토리로 이동 | `cd /home/mindcastlib/mindcastlib/run` |
| **0.2 실행 권한 부여** | 모든 스크립트 파일에 실행 권한 부여 (필수) | `chmod +x *.sh` |
| **0.3 가상환경 구축** | Python 가상환경 생성 | `python3 -m venv .venv` |
| **0.4 가상환경 활성화** | 가상환경 활성화 | `source .venv/bin/activate` |
| **0.5 패키지 다운로드** | 필요한 라이브러리 설치 | `pip install -r requirements.txt` |

---

## 1. 🔗 파이프라인 데이터 흐름 연결 구조

각 단계의 **출력(Output)**이 다음 단계의 **입력(Input)**으로 사용됩니다.

| 실행 단계 (스크립트) | 입력 (Input) 소스 | 출력 (Output) 데이터 | 연결 |
| :--- | :--- | :--- | :--- |
| **1. 데이터 전처리**<br>`./run_preprocess.sh` | **Original Data**<br>`/home/mindcastlib/data/original_data` | **전처리 데이터 디렉토리**<br>`/home/mindcastlib/data/preprocessed_data1` | **A** |
| **2. 전체 데이터 분석**<br>`./run_sequential_analysis.sh` | **A** $\rightarrow$ **전처리 데이터 디렉토리**<br>`/home/mindcastlib/data/preprocessed_data1` | **분석 결과 디렉토리**<br>`/home/mindcastlib/data/analysis_results2` | **B** |
| **3. Daily SEEI 계산**<br>`process_batch_ranges.sh` | **B** $\rightarrow$ **분석 결과 디렉토리**<br>`/home/mindcastlib/data/analysis_results2` | **Daily SEEI 파일들**<br>`/home/mindcastlib/data/seei/seei_daily/` | **C** |
| **4. Master 파일 생성**<br>`update_master.sh` | **C** $\rightarrow$ **Daily SEEI 파일들**<br>`/home/mindcastlib/data/seei/seei_daily/` | **Master 파일**<br>`/home/mindcastlib/data/seei/seei_master/seei_master.csv`<br>`/home/mindcastlib/data/seei/seei_master/seei_master.json` | **D** |
| **5. 시각화 및 통계 분석**<br>`visualize_seei.sh` | **D** $\rightarrow$ **Master JSON**<br>`/home/mindcastlib/data/seei/seei_master/seei_master.json`<br>**+** 자살 데이터<br>`/home/mindcastlib/data/base/base_data.csv` | **시각화 결과**<br>`/home/mindcastlib/data/seei/visualization/`<br>(그래프 11개 + 통계 JSON) | - |

---

## 2. ▶️ 파이프라인 순차 실행 (Scripts)

| Step | 스크립트 | 설명 | 🔥 INPUT 경로 유의사항 (스크립트 내부 변수 확인) |
| :--- | :--- | :--- | :--- |
| **1** | `./run_preprocess.sh` | **데이터 전처리** | `INPUT_PATH="/home/mindcastlib/data/original_data"`와 연결되어있는지 확인 |
| **2** | `./run_single_analysis.sh` | **단일 파일 분석** (테스트용) | 하나의 파일 경로 지정 확인<br>예: `/home/mindcastlib/data/preprocessed_data1/2020/01/11-20/news_comments.json` |
| **3** | `./run_sequential_analysis.sh` | **전체 데이터 분석** | `INPUT_DIR="/home/mindcastlib/data/preprocessed_data1"`와 연결 확인 |
| **4** | `./process_single_range.sh` | **단일 SEEI 계산** (테스트용) | `INPUT_FILE="/home/mindcastlib/data/analysis_results2/2020/01/11-20/infer_*.json"` 확인 |
| **5** | `./process_batch_ranges.sh` | **전체 SEEI 계산** (2020-2022) | `BASE_DIR="/home/mindcastlib/data/analysis_results2"`<br>`YEARS=("2020" "2021" "2022")` 확인 |
| **6** | `./update_master.sh` | **Master 파일 생성** | `DAILY_DIR="/home/mindcastlib/data/seei/seei_daily"`<br>`MASTER_FILE="/home/mindcastlib/data/seei/seei_master/seei_master.csv"` 확인 |
| **7** | `./visualize_seei.sh` | **SEEI 시각화 및 통계 분석** | `MASTER_JSON="/home/mindcastlib/data/seei/seei_master/seei_master.json"`<br>`SUICIDE_CSV="/home/mindcastlib/data/base/base_data.csv"` 확인 |

---

## 3. 🛡️ 실행 권한 문제 해결 (Permission denied)

만약 개별 스크립트 실행 시 **`Permission denied`** 문구가 뜰 경우, 아래 명령어를 입력하여 해당 파일에 실행 권한을 부여하세요.

```bash
# 모든 스크립트에 실행 권한 부여
chmod +x *.sh

# 또는 개별 파일에만
chmod +x run_single_analysis.sh
chmod +x process_batch_ranges.sh
chmod +x update_master.sh
chmod +x visualize_seei.sh
```

---

## 4. 📂 주요 경로 요약

### SEEI 파이프라인 경로

| 항목 | 경로 | 설명 |
|------|------|------|
| **Config** | `/home/mindcastlib/mindcastlib/configs/suicide/suicide_keyword_final.json` | 키워드 정의 |
| **분석 결과** | `/home/mindcastlib/data/analysis_results2/` | 감정 분석 JSON (입력) |
| **Daily SEEI** | `/home/mindcastlib/data/seei/seei_daily/` | seei_YYYYMMDD.csv/json |
| **Master** | `/home/mindcastlib/data/seei/seei_master/` | seei_master.csv/json |
| **자살 데이터** | `/home/mindcastlib/data/base/base_data.csv` | 월별 자살 사망자수 |
| **시각화** | `/home/mindcastlib/data/seei/visualization/` | 그래프 11개 + 통계 JSON |

---

## 5. ✅ 빠른 실행 가이드

### SEEI 전체 실행 (Step 5~7)

```bash
# Step 5: Daily SEEI 계산 (2020-2022, 약 5-10분)
bash process_batch_ranges.sh

# Step 6: Master 파일 생성 (약 10-30초)
bash update_master.sh

# Step 7: 시각화 + 통계 분석 (약 30-60초)
bash visualize_seei.sh
```

### 단일 파일 테스트 (Step 4)

```bash
# 특정 파일 하나만 테스트
bash process_single_range.sh /path/to/infer_*.json
```

---

## 6. 📊 출력 결과

### Daily SEEI (Step 5)
- **파일 개수:** 105개 (CSV) + 105개 (JSON)
- **위치:** `/home/mindcastlib/data/seei/seei_daily/`
- **형식:** `seei_20200110.csv`, `seei_20200110.json`

### Master 파일 (Step 6)
- **파일:** `seei_master.csv`, `seei_master.json`
- **위치:** `/home/mindcastlib/data/seei/seei_master/`
- **레코드 수:** 105개 (10일 단위)

### 시각화 (Step 7)
- **Range-level:** 5개 그래프 (10일 단위 분석)
- **Monthly-level:** 5개 그래프 + 1개 JSON (월별 통계)
- **위치:** `/home/mindcastlib/data/seei/visualization/range/`, `../monthly/`

---

## 7. 🐛 문제 해결

### 주요 에러

| 에러 메시지 | 원인 | 해결 방법 |
|-----------|------|----------|
| `FileNotFoundError` | 경로 오류 | 스크립트 내부 경로 확인 |
| `Config not found` | Config 파일 누락 | `suicide_keyword_final.json` 존재 확인 |
| `No daily files found` | Daily 파일 미생성 | Step 5 먼저 실행 |
| `Permission denied` | 실행 권한 없음 | `chmod +x *.sh` |

### 재실행

```bash
# Daily 파일 재생성
bash process_batch_ranges.sh

# Master만 재생성
bash update_master.sh

# 시각화만 재생성
bash visualize_seei.sh
``

---

**마지막 업데이트:** 2025-12-10  
**총 소요 시간:** 약 10-15분 (Step 5~7)
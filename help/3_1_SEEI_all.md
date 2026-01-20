# 2_process_batch_ranges.sh - 배치 SEEI 계산 가이드

## 📋 개요

2020-2022년 전체 기간의 모든 JSON 파일을 자동으로 순회하며 SEEI를 계산하는 배치 스크립트입니다.
현재는 제공된 데이터를 댓글 생성일을 기준으로 Range로 집계하고 있어, 생성된 분석 파일을 기준으로 지수를 집계하고 있음.

**특징:**
- 3년치 데이터 자동 처리 (2020-2022)
- 년도/월/range 자동 탐색
- 진행 상황 실시간 표시
- 첫 실패 시 즉시 중단 (디버깅 용이)

**생성 파일:** 
- 약 105개의 CSV 파일 (10일 단위 × 36개월)
- 약 105개의 JSON 파일

---

## 🔧 설정

### 필수 경로

```bash
BASE_DIR="/home/mindcastlib/data/analysis_results2"
OUTPUT_DIR="/home/mindcastlib/data/seei/seei_daily"
YEARS=("2020" "2021" "2022")
```

**BASE_DIR:**
- 감정 분석 결과 루트 디렉토리
- 구조: `BASE_DIR/YYYY/MM/RANGE/infer_*.json`

**OUTPUT_DIR:**
- Daily SEEI 파일 저장 위치
- CSV와 JSON 파일 생성

**YEARS:**
- 처리할 년도 배열
- 필요시 추가/제거 가능

---

## 📂 디렉토리 구조

### Input 구조 (analysis_results2)

```
/home/mindcastlib/data/analysis_results2/
├── 2020/
│   ├── 01/
│   │   ├── 01-10/
│   │   │   └── infer_20251210_134354.json
│   │   ├── 11-20/
│   │   │   └── infer_20251210_135621.json
│   │   └── 21-31/
│   │       └── infer_20251210_141032.json
│   ├── 02/
│   │   ├── 01-10/
│   │   ├── 11-20/
│   │   └── 21-29/
│   └── ... (12개월)
├── 2021/
│   └── ... (12개월)
└── 2022/
    └── ... (12개월)
```

### Output 구조 (seei_daily)

```
/home/mindcastlib/data/seei/seei_daily/
├── seei_20200110.csv
├── seei_20200110.json
├── seei_20200120.csv
├── seei_20200120.json
├── seei_20200131.csv
├── seei_20200131.json
...
├── seei_20221210.csv
└── seei_20221210.json
```

---

## 🚀 실행 방법

### 기본 실행

```bash
bash process_batch_ranges.sh
```

### 백그라운드 실행 (긴 작업)

```bash
# nohup으로 실행 (로그 저장)
nohup bash process_batch_ranges.sh > batch_seei.log 2>&1 &

# 진행 상황 확인
tail -f batch_seei.log
```

### 특정 년도만 처리

```bash
# 스크립트 편집
YEARS=("2020")  # 2020년만 처리

# 실행
bash process_batch_ranges.sh
```

---

## 📊 처리 과정

### 1단계: 초기화
```
- 출력 디렉토리 생성
- 카운터 초기화 (TOTAL, PROCESSED, FAILED)
```

### 2단계: 년도별 순회
```bash
for YEAR in 2020 2021 2022; do
    # /analysis_results2/2020/ 처리
    # /analysis_results2/2021/ 처리
    # /analysis_results2/2022/ 처리
done
```

### 3단계: 월별 순회
```bash
for MONTH in 01 02 03 ... 12; do
    # 01월, 02월, ..., 12월 순차 처리
done
```

### 4단계: Range별 순회
```bash
for RANGE in 01-10 11-20 21-31; do
    # 각 10일 단위 처리
done
```

### 5단계: JSON 파일 처리
```bash
for JSON_FILE in infer_*.json; do
    python compute_daily_seei.py \
        --input "$JSON_FILE" \
        --output_dir "$OUTPUT_DIR"
done
```

### 6단계: 결과 집계
```
- 성공/실패 카운트
- 생성된 파일 개수 확인
- 최종 요약 출력
```

---

## 📈 실행 결과 예시

```
========================================
Batch SEEI Processing (2020-2022)
========================================
Base: /home/mindcastlib/data/analysis_results2
Output: /home/mindcastlib/data/seei/seei_daily

📅 Year: 2020
   📆 Month: 01
      📄 infer_20251210_134354.json
         ✓
      📄 infer_20251210_135621.json
         ✓
      📄 infer_20251210_141032.json
         ✓
   📆 Month: 02
      📄 infer_20251210_142145.json
         ✓
...

📅 Year: 2021
   📆 Month: 01
...

📅 Year: 2022
   📆 Month: 01
...

========================================
Summary
========================================
Total:      105
Success:    105
Failed:     0
========================================

Generated: 105 CSV files
Location: /home/mindcastlib/data/seei/seei_daily

✅ Done
```

---

## 🎯 처리 로직 상세

### Range 디렉토리 구조

각 월은 3개의 range로 구성:

| Range | 날짜 | 파일명 예시 |
|-------|------|------------|
| 01-10 | 1일~10일 | seei_YYYYMM10.csv |
| 11-20 | 11일~20일 | seei_YYYYMM20.csv |
| 21-31 | 21일~말일 | seei_YYYYMM{말일}.csv |

**예시:**
- 2020년 1월: `seei_20200110.csv`, `seei_20200120.csv`, `seei_20200131.csv`
- 2020년 2월: `seei_20200210.csv`, `seei_20200220.csv`, `seei_20200229.csv` (윤년)

### 에러 처리 전략

```bash
# ⚠️ 첫 실패 시 즉시 중단
if ! python compute_daily_seei.py ...; then
    echo "❌ First failure detected. Stopping for debugging."
    echo "Failed file: ${JSON_FILE}"
    exit 1
fi
```

**이유:**
- 에러 패턴 조기 발견
- 불필요한 재시도 방지
- 디버깅 용이

---

## 📊 예상 처리량

### 시간 추정

| 항목 | 값 |
|------|-----|
| **전체 파일 수** | ~105개 |
| **파일당 처리 시간** | ~3초 |
| **예상 총 시간** | ~5-10분 |

### 디스크 사용량

| 항목 | 크기 |
|------|------|
| **CSV 파일** | ~30KB/파일 |
| **JSON 파일** | ~20KB/파일 |
| **총 예상 크기** | ~5MB |

---

## ⚠️ 주의사항

### 1. 디스크 공간
```bash
# 필요 공간: 최소 10MB
df -h /home/mindcastlib/data/seei/seei_daily
```

### 2. 중복 실행
```bash
# ⚠️ 기존 파일 덮어쓰기!
# 백업 권장
cp -r /home/mindcastlib/data/seei/seei_daily \
      /home/mindcastlib/data/seei/seei_daily_backup_$(date +%Y%m%d)
```

### 3. 중간 실패
```bash
# 실패 시 해당 파일부터 재실행 필요
# 방법 1: 단일 파일 재처리
bash 1_process_single_range.sh /path/to/failed/file.json

# 방법 2: 특정 년도/월만 재실행
# 스크립트 수정하여 시작 지점 변경
```

### 4. 메모리 사용
```bash
# 최대 메모리: ~500MB
# 시스템 리소스 확인
free -h
```

---

## 🐛 트러블슈팅

### Q1: "No JSON files found"

```bash
# 원인: BASE_DIR 경로 오류
# 해결: 디렉토리 존재 확인
ls -la /home/mindcastlib/data/analysis_results2/2020/01/
```

### Q2: 처리 중 멈춤

```bash
# 원인: 특정 JSON 파일 오류
# 해결: 에러 메시지 확인 후 해당 파일 건너뛰기

# 수동으로 해당 파일 제외
mv /path/to/problematic/file.json /path/to/problematic/file.json.skip
```

### Q3: 일부 월 누락

```bash
# 원인: 디렉토리 구조 불일치
# 확인:
find /home/mindcastlib/data/analysis_results2 -type d -name "01-10"

# 예상 결과: 36개 (12개월 × 3년)
```

### Q4: Permission denied

```bash
# 원인: 권한 부족
# 해결:
sudo chown -R $USER:$USER /home/mindcastlib/data/seei/
chmod -R 755 /home/mindcastlib/data/seei/
```



---

## 📊 품질 검증

### 생성된 파일 확인

```bash
# 1. 파일 개수
ls /home/mindcastlib/data/seei/seei_daily/*.csv | wc -l
# 예상: 105개

# 2. 날짜 범위 확인
ls /home/mindcastlib/data/seei/seei_daily/*.csv | head -1
ls /home/mindcastlib/data/seei/seei_daily/*.csv | tail -1
```

### 내용 검증

```bash
# 1. 첫 파일 확인
head -20 /home/mindcastlib/data/seei/seei_daily/seei_20200110.csv

# 2. Total SEEI가 0인 파일 찾기 (문제 가능성)
for csv in /home/mindcastlib/data/seei/seei_daily/*.csv; do
    total=$(grep "^[^,]*,total," "$csv" | cut -d',' -f4)
    if [ "$total" = "0.0" ]; then
        echo "Zero SEEI: $csv"
    fi
done

# 3. 키워드 통계 누락 확인
for csv in /home/mindcastlib/data/seei/seei_daily/*.csv; do
    posts=$(grep "keyword_posts" "$csv" | wc -l)
    if [ $posts -eq 0 ]; then
        echo "Missing keyword stats: $csv"
    fi
done
```

---

## 🔄 재실행 전략

### 전체 재실행

```bash
# 1. 백업
mv /home/mindcastlib/data/seei/seei_daily \
   /home/mindcastlib/data/seei/seei_daily_old

# 2. 재실행
bash process_batch_ranges.sh
```

### 부분 재실행

```bash
# 특정 년도만
YEARS=("2022")  # 스크립트 수정
bash process_batch_ranges.sh

# 특정 월만
for json in /home/mindcastlib/data/analysis_results2/2020/03/*/infer_*.json; do
    bash 1_process_single_range.sh "$json"
done
```

### 실패 파일만 재처리

```bash
# 1. 실패 파일 목록 저장
grep "✗ FAILED" batch_seei.log > failed_files.txt

# 2. 재처리
while read line; do
    file=$(echo "$line" | grep -oP '/home/.*\.json')
    echo "Retrying: $file"
    bash 1_process_single_range.sh "$file"
done < failed_files.txt
```

---

## 📈 성능 최적화

### 병렬 처리 (선택사항)

```bash
# GNU parallel 사용 (4개 동시 처리)
find /home/mindcastlib/data/analysis_results2 -name "infer_*.json" | \
    parallel -j 4 python compute_daily_seei.py --input {} --output_dir /path/to/output
```

**주의:** 병렬 처리 시 메모리 사용량 증가

---

## 🔗 다음 단계

```bash
# 1. 배치 처리 완료 후
bash 2_process_batch_ranges.sh

# 2. 파일 검증
ls /home/mindcastlib/data/seei/seei_daily/*.csv | wc -l  # 105개 확인

# 3. Master 파일 생성
bash 3_update_master.sh

# 4. 시각화
bash 4_visualize_seei.sh
```

---

## 📝 체크리스트

**실행 전 확인:**
- [ ] BASE_DIR 경로 설정
- [ ] OUTPUT_DIR 디렉토리 생성
- [ ] 디스크 공간 확인 (최소 10MB)
- [ ] Config 파일 존재 확인
- [ ] Python 환경 활성화

**실행 중 확인:**
- [ ] 에러 메시지 주시
- [ ] 진행률 모니터링
- [ ] 메모리 사용량 확인

**실행 후 확인:**
- [ ] 생성된 파일 개수 (105개)
- [ ] 파일 크기 정상 (>1KB)
- [ ] Total SEEI가 0이 아닌지
- [ ] 키워드 통계 포함 여부

---

## 🎓 참고

**디렉토리 명명 규칙:**
```
01-10: 1일부터 10일까지
11-20: 11일부터 20일까지
21-31: 21일부터 말일까지 (28, 29, 30, 31)
```

**JSON 파일 명명 규칙:**
```
infer_YYYYMMDD_HHMMSS.json
예: infer_20251210_134354.json
```

**CSV 출력 파일 명명 규칙:**
```
seei_YYYYMMDD.csv
예: seei_20200110.csv (1월 1-10일)
    seei_20200120.csv (1월 11-20일)
    seei_20200131.csv (1월 21-31일)
```

---

**마지막 업데이트:** 2025-12-10
**버전:** v3 (Raw SEEI)
**예상 소요 시간:** 5-10분
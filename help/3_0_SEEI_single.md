# 1_process_single_range.sh - 단일 Range SEEI 계산 가이드

## 📋 개요

단일 JSON 파일(하나의 10일 range)에서 SEEI를 계산하고 CSV/JSON 파일을 생성하는 스크립트입니다.

**용도:**
- 특정 날짜 range 하나만 처리
- 테스트 및 디버깅
- 재계산이 필요한 특정 날짜만 업데이트

---

## 🔧 설정

### 필수 경로

```bash
INPUT_FILE="/home/mindcastlib/data/analysis_results2/2020/01/11-20/infer_20251210_134354.json"
OUTPUT_DIR="/home/mindcastlib/data/seei/seei_daily"
```

**INPUT_FILE:**
- 감정 분석이 완료된 JSON 파일
- 형식: `infer_YYYYMMDD_HHMMSS.json`
- 위치: 예시 : `/analysis_results2/YYYY/MM/RANGE/` 

**OUTPUT_DIR:**
- Daily SEEI 파일 저장 위치
- CSV와 JSON 두 가지 형식으로 생성

---

## 🚀 실행 방법

### 방법 1: 스크립트 내 경로 설정 후 실행

```bash
# 1. 스크립트 편집
nano 1_process_single_range.sh

# 2. INPUT_FILE 경로 수정
INPUT_FILE="/home/mindcastlib/data/analysis_results2/2020/01/11-20/infer_20251210_134354.json"

# 3. 실행
bash 1_process_single_range.sh
```

### 방법 2: 명령줄 인수로 파일 경로 전달

```bash
bash 1_process_single_range.sh /path/to/infer_file.json
```

혹은 .sh 파일을 직접 수정할 수도 있음.

**장점:** 스크립트 수정 없이 다양한 파일 처리 가능

---

## 📊 처리 과정

### 1단계: 입력 검증
```
- JSON 파일 존재 확인
- 파일 형식 확인 (infer_*.json)
- 날짜 추출 (JSON 내부 date 필드)
```

### 2단계: SEEI 계산
```python
# compute_daily_seei.py 실행
- 키워드 매칭 (10개 메인 키워드)
- 감정 분석 (부정 비율 계산)
- SEEI 공식 적용: direction × neg_ratio × log(1 + comments)
- 키워드별 통계 집계 (posts, comments, neg_ratio)
```

### 3단계: 파일 생성
```
Output 1: seei_YYYYMMDD.csv
Output 2: seei_YYYYMMDD.json
```

---

## 📁 출력 파일 구조

### CSV 파일 (`seei_20200110.csv`)

```csv
date,metric_type,metric_name,value,ratio
2020-01-10,total,SEEI_TOTAL,15.23,100.0
2020-01-10,keyword_score,실업률,3.42,22.5
2020-01-10,keyword_score,경제활동인구,1.68,11.0
...
2020-01-10,keyword_posts,실업률,15,
2020-01-10,keyword_comments,실업률,342,
2020-01-10,keyword_neg_ratio,실업률,58.1,
...
2020-01-10,emotion_dist,분노,245,18.5
2020-01-10,stats,total_posts,87,
```

**metric_type 종류:**
- `total`: 총합 SEEI
- `keyword_score`: 키워드별 점수
- `keyword_posts`: 키워드 포함 포스트 수
- `keyword_comments`: 키워드 포함 댓글 수
- `keyword_neg_ratio`: 키워드별 부정 비율 (%)
- `emotion_dist`: 감정 분포
- `stats`: 전체 통계

### JSON 파일 (`seei_20200110.json`)

```json
{
  "date": "2020-01-10",
  "seei": {
    "total": 15.23,
    "keywords": [
      {
        "name": "실업률",
        "score": 3.42,
        "ratio": 22.5,
        "posts": 15,
        "comments": 342,
        "neg_ratio": 58.1
      }
    ]
  },
  "emotions": {
    "distribution": [
      {"name": "분노", "count": 245, "ratio": 18.5}
    ]
  },
  "stats": {
    "posts_with_keyword": 87,
    "comments_with_keyword": 2134,
    "neg_comments": 1156,
    "neg_ratio_overall": 54.2
  }
}
```

---

## 🎯 사용 예시

### 예시 1: 특정 날짜 재계산

```bash
# 2020년 1월 11-20일 range 재계산
bash 1_process_single_range.sh \
  /home/mindcastlib/data/analysis_results2/2020/01/11-20/infer_20251210_134354.json
```

### 예시 2: 테스트용 샘플 실행

```bash
# 최신 파일 하나로 테스트
LATEST=$(find /home/mindcastlib/data/analysis_results2 -name "infer_*.json" | head -1)
bash 1_process_single_range.sh "$LATEST"
```

---

## 📈 실행 결과 예시

```
Processing: /home/mindcastlib/data/analysis_results2/2020/01/11-20/infer_20251210_134354.json
Output: /home/mindcastlib/data/seei/seei_daily

[START] Computing daily SEEI
  Input: /home/mindcastlib/data/analysis_results2/2020/01/11-20/infer_20251210_134354.json

[OK] Daily SEEI saved
     Date: 2020-01-20
     Total SEEI: 15.23
     Posts (w/ keyword): 87
     Comments (w/ keyword): 2134
     Neg Ratio: 54.2%
     CSV: /home/mindcastlib/data/seei/seei_daily/seei_20200120.csv
     JSON: /home/mindcastlib/data/seei/seei_daily/seei_20200120.json

[DONE] Daily SEEI computation completed

✅ Done
```

---

## 🔍 키워드 매칭 로직

### 10개 메인 키워드

```
1. 실업률
2. 경제활동인구
3. 비경제활동인구
4. 고용률
5. 소비자물가상승률
6. 가계신용
7. GDP
8. 임금총액
9. 근로시간
10. 근로일수
```

### 매칭 방식

```python
# 1. 제목에서 메인 키워드 매칭
kw_mask.get("실업률", False)

# 2. 제목에서 서브태그 매칭
sub_mask.get("청년실업", False)  # "실업률"의 서브태그
sub_mask.get("실업자", False)     # "실업률"의 서브태그

# 3. 둘 중 하나라도 매칭되면 해당 키워드 발동
hit = kw_mask.get(main_kw) or any(sub_mask.get(s) for s in sub_kws)
```

---

## ⚠️ 주의사항

### 1. 파일 경로
```bash
# ❌ 잘못된 경로
INPUT_FILE="~/data/file.json"              # ~ 사용 불가
INPUT_FILE="data/file.json"                # 상대경로 권장하지 않음

# ✅ 올바른 경로
INPUT_FILE="/home/mindcastlib/data/analysis_results2/2020/01/11-20/infer_*.json"
```

### 2. JSON 파일 형식
- **필수 필드:** `data[0].date` (날짜 정보)
- **필수 필드:** `data[*].posts[*].analyses` (감정 분석 결과)
- 형식이 맞지 않으면 에러 발생

### 3. 중복 실행
- 기존 파일 **덮어쓰기** (백업 없음)
- 재계산 시 주의 필요

### 4. Config 파일 의존성
```bash
CONFIG="/home/mindcastlib/mindcastlib/configs/suicide/suicide_keyword_final.json"
```
- 이 파일이 없으면 에러 발생
- 키워드 목록 및 서브태그 정의

---

## 🐛 트러블슈팅

### Q1: "File not found" 에러

```bash
❌ File not found: /path/to/file.json
```

**해결:**
```bash
# 파일 존재 확인
ls -la /home/mindcastlib/data/analysis_results2/2020/01/11-20/

# 경로 수정
INPUT_FILE="/실제/경로/infer_*.json"
```

### Q2: "Config not found" 에러

```bash
FileNotFoundError: /home/mindcastlib/mindcastlib/configs/suicide/suicide_keyword_final.json
```

**해결:**
```bash
# Config 파일 확인
ls -la /home/mindcastlib/mindcastlib/configs/suicide/

# 파일명이 다를 경우 스크립트 수정
CONFIG="/home/mindcastlib/mindcastlib/configs/suicide/suicide_keyword_ver2.json"
```

### Q3: "No data blocks found" 에러

```bash
ValueError: No data blocks found in file.json
```

**해결:**
- JSON 파일 형식 확인
- `data` 배열이 비어있지 않은지 확인
- 감정 분석이 완료된 파일인지 확인

### Q4: 출력 파일이 생성되지 않음

**확인 사항:**
```bash
# 1. 출력 디렉토리 권한 확인
ls -ld /home/mindcastlib/data/seei/seei_daily

# 2. 디렉토리 생성
mkdir -p /home/mindcastlib/data/seei/seei_daily

# 3. 스크립트 실행 권한
chmod +x 1_process_single_range.sh
```

---

## 📊 성능

| 항목 | 값 |
|------|-----|
| **처리 시간** | ~2-5초/파일 |
| **메모리 사용** | ~200MB |
| **디스크 사용** | ~50KB/파일 (CSV+JSON) |

---

## 🔗 다음 단계

```bash
# 1. 단일 파일 처리 완료 후
bash 1_process_single_range.sh

# 2. 배치 처리 (전체 파일)
bash 2_process_batch_ranges.sh

# 3. Master 파일 생성
bash 3_update_master.sh

# 4. 시각화
bash 4_visualize_seei.sh
```

---

## 📝 체크리스트

**실행 전 확인:**
- [ ] INPUT_FILE 경로 설정
- [ ] OUTPUT_DIR 디렉토리 존재 확인
- [ ] Config 파일 존재 확인
- [ ] Python 환경 활성화

**실행 후 확인:**
- [ ] CSV 파일 생성 확인
- [ ] JSON 파일 생성 확인
- [ ] 날짜가 올바른지 확인
- [ ] Total SEEI 값이 0이 아닌지 확인

---

## 🎓 참고

**SEEI 공식:**
```
SEEI = direction × neg_ratio × log(1 + comments)

direction = +1 (부정 비율 >= 50%)
           -1 (부정 비율 < 50%)
```

**키워드 필터링:**
- 키워드가 **하나라도** 있는 포스트만 집계
- 키워드 없는 포스트는 완전 제외
- 전체 통계도 키워드 있는 것만 포함

---

**마지막 업데이트:** 2025-12-10

# 3_update_master.sh - Master 파일 생성 가이드

## 📋 개요

Daily SEEI 파일들을 통합하여 시계열 Master 파일을 생성하는 스크립트입니다.

**기능:**
- Daily 파일 → 1개 Master 파일
- Raw SEEI 기반 
- 변화율 자동 계산 (전 range, MoM, YoY)
- CSV + JSON 두 가지 형식 생성

**출력:**
- `seei_master.csv` - 전체 데이터 (분석용)
- `seei_master.json` - UI 친화적 (웹/앱용)

---

## 🔧 설정

### 필수 경로

```bash
DAILY_DIR="/home/mindcastlib/data/seei/seei_daily"
MASTER_FILE="/home/mindcastlib/data/seei/seei_master/seei_master.csv"
```

**DAILY_DIR:**
- Step 2에서 생성된 Daily 파일 위치
- 약 105개의 CSV 파일 포함

**MASTER_FILE:**
- 통합 Master CSV 경로
- JSON은 자동으로 같은 위치에 생성

---

## 🚀 실행 방법

### 기본 실행

```bash
bash 3_update_master.sh
```

### 실행 전 준비사항

```bash
# 1. Daily 파일 존재 확인
ls /home/mindcastlib/data/seei/seei_daily/*.csv | wc -l
# 예상: 105개

# 2. 스크립트 실행 권한
chmod +x 3_update_master.sh

# 3. Python 환경 활성화 (필요시)
source /path/to/venv/bin/activate
```

---

## 📊 처리 과정

### 1단계: 초기화
```
- 출력 디렉토리 생성
- Daily 파일 카운트
- 기존 Master 파일 백업
```

### 2단계: Daily 파일 순차 로드
```python
# 각 seei_YYYYMMDD.csv 파일에서:
- 날짜 (date)
- 총합 SEEI (total_seei)
- 키워드 점수 10개 (kw_실업률, kw_경제활동인구, ...)
- 키워드 비율 10개 (kw_ratio_실업률, ...)
- 키워드 통계 30개 (posts, comments, neg_ratio × 10)
- 감정 분포 (emo_분노, emo_불안, ...)
- 전체 통계 (stat_total_posts, ...)
```

### 3단계: DataFrame 통합
```python
# 모든 Daily 데이터를 하나의 DataFrame으로
df_master = pd.concat([
    df_20200110,
    df_20200120,
    df_20200131,
    ...
])
```

### 4단계: 변화율 계산
```python
# 전 range 대비
df["prev_seei_delta"] = df["total_seei"].diff()
df["prev_seei_pct"] = df["total_seei"].pct_change() * 100

# 전월 대비 (3 ranges = 30일)
df["mom_seei_delta"] = df["total_seei"].diff(periods=3)
df["mom_seei_pct"] = df["total_seei"].pct_change(periods=3) * 100

# 전년 대비 (36 ranges = 1년)
df["yoy_seei_delta"] = df["total_seei"].diff(periods=36)
df["yoy_seei_pct"] = df["total_seei"].pct_change(periods=36) * 100
```

### 5단계: 방향 플래그
```python
# up, down, flat
df["prev_direction"] = df["prev_seei_delta"].apply(
    lambda x: "up" if x > 0 else "down" if x < 0 else "flat"
)
```

### 6단계: 파일 저장
```
- CSV: seei_master.csv
- JSON: seei_master.json
- Backup: seei_master.csv.backup
```

---

## 📁 출력 파일 구조

### Master CSV (`seei_master.csv`)

```csv
date,total_seei,prev_seei_delta,prev_seei_pct,prev_direction,mom_seei_delta,mom_seei_pct,mom_direction,yoy_seei_delta,yoy_seei_pct,yoy_direction,kw_실업률,kw_ratio_실업률,kw_posts_실업률,kw_comments_실업률,kw_negratio_실업률,kw_실업률_mom_pct,...
2020-01-10,15.23,,,flat,,,flat,,,flat,3.42,22.5,15,342,58.1,,...
2020-01-20,16.78,1.55,10.2,up,,,flat,,,flat,3.89,23.2,18,398,61.2,12.5,...
2020-01-31,14.52,-2.26,-13.5,down,,,flat,,,flat,2.95,20.3,12,287,52.3,-24.1,...
2020-02-10,15.87,1.35,9.3,up,-0.64,-4.2,down,,,flat,3.21,20.2,14,315,56.8,8.8,...
```

**주요 컬럼:**

| 컬럼 그룹 | 개수 | 설명 |
|----------|------|------|
| **기본 정보** | 11 | date, total_seei, 변화율×3, 방향×3 |
| **키워드 점수** | 10 | kw_{키워드} |
| **키워드 비율** | 10 | kw_ratio_{키워드} |
| **키워드 posts** | 10 | kw_posts_{키워드} |
| **키워드 comments** | 10 | kw_comments_{키워드} |
| **키워드 neg_ratio** | 10 | kw_negratio_{키워드} |
| **키워드 MoM** | 10 | kw_{키워드}_mom_pct |
| **감정 분포** | 12 | emo_{감정}, emo_ratio_{감정} |
| **전체 통계** | 4 | stat_total_posts, ... |
| **합계** | ~87 | |

### Master JSON (`seei_master.json`)

```json
[
  {
    "date": "2020-01-10",
    "seei": {
      "total": 15.23
    },
    "changes": {
      "prev": {
        "delta": null,
        "pct": null,
        "direction": "flat"
      },
      "mom": {
        "delta": null,
        "pct": null,
        "direction": "flat"
      },
      "yoy": {
        "delta": null,
        "pct": null,
        "direction": "flat"
      }
    },
    "keywords": [
      {
        "name": "실업률",
        "score": 3.42,
        "ratio": 22.5,
        "posts": 15,
        "comments": 342,
        "neg_ratio": 58.1,
        "mom_pct": null
      },
      {
        "name": "경제활동인구",
        "score": 1.68,
        "ratio": 11.0,
        "posts": 5,
        "comments": 120,
        "neg_ratio": 55.3,
        "mom_pct": null
      }
    ],
    "emotions": [
      {
        "name": "분노",
        "count": 245,
        "ratio": 18.5
      }
    ],
    "stats": {
      "posts_with_keyword": 87,
      "comments_with_keyword": 2134,
      "neg_ratio_overall": 54.2
    }
  },
  {
    "date": "2020-01-20",
    ...
  }
]
```

---

## 📈 실행 결과 예시

```
========================================
SEEI Master Update (v3 - Raw SEEI)
========================================
Daily: /home/mindcastlib/data/seei/seei_daily
Master: /home/mindcastlib/data/seei/seei_master/seei_master.csv

Found 105 daily files

📦 Backup created

============================================================
SEEI MASTER UPDATE (v3 FINAL)
============================================================

[1/105] seei_20200110.csv
[UPDATE] /home/mindcastlib/data/seei/seei_daily/seei_20200110.csv

[NEW] Creating master file
[OK] Master CSV updated → seei_master.csv

[2/105] seei_20200120.csv
[UPDATE] /home/mindcastlib/data/seei/seei_daily/seei_20200120.csv
[OK] Master CSV updated → seei_master.csv

...

[105/105] seei_20221231.csv
[UPDATE] /home/mindcastlib/data/seei/seei_daily/seei_20221231.csv
[OK] Master CSV updated → seei_master.csv

[OK] Master JSON saved → seei_master.json

[DONE] Batch update completed

✅ Done

Output:
  - CSV: /home/mindcastlib/data/seei/seei_master/seei_master.csv
  - JSON: /home/mindcastlib/data/seei/seei_master/seei_master.json
```

---

## 🎯 변화율 계산 상세

### 전 Range 대비 (Prev)

```python
# 이전 10일 대비 변화
2020-01-10: 15.23  → prev_delta = NaN (첫 데이터)
2020-01-20: 16.78  → prev_delta = +1.55 (↑ 10.2%)
2020-01-31: 14.52  → prev_delta = -2.26 (↓ 13.5%)
```

**해석:**
- `prev_direction = "up"`: SEEI 증가 (악화)
- `prev_direction = "down"`: SEEI 감소 (개선)

### 전월 대비 (MoM - Month over Month)

```python
# 3 ranges = 30일 전 대비
2020-01-10: 15.23  → mom_delta = NaN
2020-01-20: 16.78  → mom_delta = NaN
2020-01-31: 14.52  → mom_delta = NaN
2020-02-10: 15.87  → mom_delta = +0.64 (vs 2020-01-10)
2020-02-20: 17.23  → mom_delta = +0.45 (vs 2020-01-20)
```

**활용:**
- 계절성 파악
- 월별 추세 분석

### 전년 대비 (YoY - Year over Year)

```python
# 36 ranges = 1년(12개월) 전 대비
2020-01-10: 15.23  → yoy_delta = NaN
...
2021-01-10: 18.45  → yoy_delta = +3.22 (vs 2020-01-10)
2021-01-20: 19.12  → yoy_delta = +2.34 (vs 2020-01-20)
```

**활용:**
- 연간 성장률
- 장기 트렌드 분석

---

## ⚠️ 주의사항

### 1. Daily 파일 완전성

```bash
# ✅ 필수: 105개 파일 모두 존재해야 함
ls /home/mindcastlib/data/seei/seei_daily/*.csv | wc -l

# 누락 시 변화율 계산 오류 발생
```

### 2. 기존 Master 덮어쓰기

```bash
# ⚠️ 자동 백업되지만 수동 백업 권장
cp /home/mindcastlib/data/seei/seei_master/seei_master.csv \
   /home/mindcastlib/data/seei/seei_master/seei_master_$(date +%Y%m%d_%H%M%S).csv
```

### 3. 키워드 개수 고정

```python
# ⚠️ 항상 10개 키워드만 처리
MAIN_KEYWORDS = [
    "실업률", "경제활동인구", "비경제활동인구", "고용률",
    "소비자물가상승률", "가계신용", "GDP", "임금총액",
    "근로시간", "근로일수"
]
```

### 4. Infinity 값 처리

```python
# 0에서 양수 변화 시 Infinity 발생
# 자동으로 NaN 처리됨
df = df.replace([np.inf, -np.inf], np.nan)
```

---

## 🐛 트러블슈팅

### Q1: "No daily files found"

```bash
# 원인: Daily 파일 미생성
# 해결:
bash 2_process_batch_ranges.sh  # 먼저 실행
```

### Q2: 변화율이 모두 NaN

```bash
# 원인: Daily 파일이 1개뿐
# 해결: 최소 2개 이상의 Daily 파일 필요

# 확인
ls /home/mindcastlib/data/seei/seei_daily/*.csv | wc -l
```

### Q3: KeyError: 'kw_실업률'

```bash
# 원인: Daily 파일에 키워드 데이터 누락
# 해결: Daily 파일 재생성

bash 2_process_batch_ranges.sh
```

### Q4: JSON 생성 실패

```bash
# 원인: NaN 값 처리 오류
# 해결: safe_get_value() 함수가 제대로 동작하는지 확인

# 수동 재생성
python -c "
from update_seei_master import *
df = pd.read_csv('seei_master.csv', parse_dates=['date'])
save_master_json(df, 'seei_master.json')
"
```

---

## 📊 데이터 검증

### Master 파일 품질 확인

```bash
# 1. 레코드 수 확인
wc -l /home/mindcastlib/data/seei/seei_master/seei_master.csv
# 예상: 106줄 (헤더 + 105 rows)

# 2. 날짜 범위 확인
head -2 /home/mindcastlib/data/seei/seei_master/seei_master.csv
tail -1 /home/mindcastlib/data/seei/seei_master/seei_master.csv

# 3. NaN 비율 확인
python << 'EOF'
import pandas as pd
df = pd.read_csv('/home/mindcastlib/data/seei/seei_master/seei_master.csv')
print(df.isnull().sum().sum())  # 전체 NaN 개수
print(f"NaN ratio: {df.isnull().sum().sum() / df.size * 100:.2f}%")
EOF

# 4. 변화율 통계
python << 'EOF'
import pandas as pd
df = pd.read_csv('/home/mindcastlib/data/seei/seei_master/seei_master.csv')
print("=== 변화율 통계 ===")
print(f"Prev: {df['prev_seei_pct'].describe()}")
print(f"MoM: {df['mom_seei_pct'].describe()}")
print(f"YoY: {df['yoy_seei_pct'].describe()}")
EOF
```

### JSON 검증

```bash
# JSON 형식 확인
python -m json.tool /home/mindcastlib/data/seei/seei_master/seei_master.json > /dev/null
echo $?  # 0이면 정상

# 레코드 수 확인
python -c "import json; data=json.load(open('seei_master.json')); print(len(data))"
# 예상: 105
```

---

## 🔄 증분 업데이트

### 새로운 Daily 파일 추가 시

```bash
# 1. 새 Daily 파일 생성
bash 1_process_single_range.sh /path/to/new/infer.json

# 2. Master 업데이트 (자동으로 추가됨)
bash 3_update_master.sh

# 3. 중복 확인 (스킵 메시지 확인)
# [SKIP] Exists: 2020-01-10
```

---

## 📈 활용 예시

### Pandas로 분석

```python
import pandas as pd

# 로드
df = pd.read_csv('seei_master.csv', parse_dates=['date'])

# 월별 평균
monthly = df.set_index('date').resample('M')['total_seei'].mean()

# 연도별 트렌드
yearly = df.groupby(df['date'].dt.year)['total_seei'].agg(['mean', 'std'])

# 가장 높은/낮은 SEEI
print(df.nlargest(5, 'total_seei')[['date', 'total_seei']])
print(df.nsmallest(5, 'total_seei')[['date', 'total_seei']])
```

### JavaScript로 시각화

```javascript
// JSON 로드
fetch('seei_master.json')
  .then(res => res.json())
  .then(data => {
    const dates = data.map(d => d.date);
    const seei = data.map(d => d.seei.total);
    
    // Chart.js, Recharts 등으로 시각화
    drawLineChart(dates, seei);
  });
```

---

## 🔗 다음 단계

```bash
# 1. Master 파일 생성 완료 후
bash update_master.sh

# 2. 파일 검증
ls -lh /home/mindcastlib/data/seei/seei_master/

# 3. 시각화 실행
bash visualize_seei.sh
```

---

## 📝 체크리스트

**실행 전 확인:**
- [ ] Daily 파일 105개 생성 완료
- [ ] DAILY_DIR 경로 설정
- [ ] MASTER_FILE 경로 설정
- [ ] Python 환경 활성화

**실행 후 확인:**
- [ ] seei_master.csv 생성 (106줄)
- [ ] seei_master.json 생성 (105 records)
- [ ] seei_master.csv.backup 생성
- [ ] 변화율 컬럼 정상 (NaN 아님)
- [ ] 키워드 통계 포함 여부

---

## 🎓 참고

**변화율 기간:**
- Prev: 1 range = 10일
- MoM: 3 ranges = 30일 (대략 1개월)
- YoY: 36 ranges = 360일 (대략 1년)

**NaN 값이 정상인 경우:**
- 첫 range: prev_delta, mom_delta, yoy_delta 모두 NaN
- 첫 3 ranges: mom_delta NaN
- 첫 36 ranges: yoy_delta NaN

**키워드 순서 (고정):**
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

---

**마지막 업데이트:** 2025-12-10
**버전:** v3 (Raw SEEI)
**예상 소요 시간:** 10-30초
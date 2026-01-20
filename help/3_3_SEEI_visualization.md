# visualize_seei.sh - 시각화 및 통계 분석 가이드

## 📋 개요

Master 파일과 자살 데이터를 분석하여 다층적 시각화와 통계 검정을 수행하는 스크립트입니다.

**생성 결과:**
- **Range-level 시각화** (10일 단위)
- **Monthly-level 분석** (월별 집계)
- **통계 분석** (상관분석, Granger 인과관계)

**총 11개 파일 생성**

---

## 🔧 설정

### 필수 경로

```bash
VIS_SCRIPT="/home/mindcastlib/mindcastlib/scripts/visualize_seei.py"
MASTER_JSON="/home/mindcastlib/data/seei/seei_master/seei_master.json"
SUICIDE_CSV="/home/mindcastlib/data/base/base_data.csv"
OUT_DIR="/home/mindcastlib/data/seei/visualization"
```

**VIS_SCRIPT:**
- 시각화 Python 스크립트 경로

**MASTER_JSON:**
- Step 3에서 생성된 Master JSON
- UI 친화적 구조

**SUICIDE_CSV:**
- 월별 자살 사망자수 데이터
- 컬럼: `날짜`, `자살사망자수`

**OUT_DIR:**
- 시각화 결과 저장 위치
- `range/`, `monthly/` 하위 디렉토리 자동 생성

---

## 🚀 실행 방법

### 기본 실행

```bash
bash visualize_seei.sh
```

### 실행 전 준비사항

```bash
# 1. Master 파일 존재 확인
ls -lh /home/mindcastlib/data/seei/seei_master/seei_master.json

# 2. 자살 데이터 확인
head -5 /home/mindcastlib/data/base/base_data.csv

# 3. 필요 패키지 설치
pip install matplotlib seaborn scipy statsmodels --break-system-packages

# 4. 한글 폰트 설치 (Ubuntu)
sudo apt-get install fonts-nanum
```

---

## 📊 처리 과정

### 1단계: 데이터 로드

```python
# Master JSON → DataFrame (Range-level)
df_range = load_master_json(master_json)
# 105 rows (10일 단위)

# Monthly 집계
df_monthly = convert_monthly(df_range)
# 36 rows (월별)

# 자살 데이터 로드
df_suicide = pd.read_csv(suicide_csv)
# 컬럼: 날짜, 자살사망자수
```

### 2단계: Range-level 시각화

```
1. range_seei_trend.png          - SEEI 추이 (up/down 표시)
2. range_negative_ratio.png       - 부정 감정 비율
3. range_keyword_ratio.png        - 키워드 비율 (stacked)
4. keyword_small_multiples.png    - 키워드별 개별 그래프
5. emotion_small_multiples.png    - 감정별 개별 그래프
```

### 3단계: Monthly-level 시각화

```
1. monthly_seei_trend.png         - 월별 SEEI 추이
2. monthly_dual_axis.png          - SEEI vs 자살 (dual axis)
```

### 4단계: 통계 분석

```
1. scatter_correlation.png        - 산점도 + 회귀선
2. cross_correlation.png          - 교차상관 (lag 분석)
3. granger_pvalues.png            - Granger 인과관계 p-value
4. leading_analysis.json          - 통계 결과 (JSON)
```

---

## 📁 출력 파일 구조

```
/home/mindcastlib/data/seei/visualization/
├── range/
│   ├── range_seei_trend.png
│   ├── range_negative_ratio.png
│   ├── range_keyword_ratio.png
│   ├── keyword_small_multiples.png
│   └── emotion_small_multiples.png
└── monthly/
    ├── monthly_seei_trend.png
    ├── monthly_dual_axis.png
    ├── scatter_correlation.png
    ├── cross_correlation.png
    ├── granger_pvalues.png
    └── leading_analysis.json
```

---

## 📈 시각화 상세 설명

### Range-level (10일 단위)

#### 1. SEEI 추이 (`range_seei_trend.png`)

```
┌─────────────────────────────────────┐
│  Range-level SEEI Trend             │
│                                     │
│  20 ┤        ▲                      │
│     │       ╱ ╲     ▲               │
│  15 ┤──────╱───╲───╱─╲──▼──        │
│     │     ╱     ╲ ╱   ╲╱            │
│  10 ┤────╱───────▼─────╲────        │
│     │                                │
│     └────────────────────────────────│
│      2020  2021  2022               │
└─────────────────────────────────────┘
```

**요소:**
- 파란 선: SEEI 값
- ▲ (빨강): 증가 (up)
- ▼ (파랑): 감소 (down)

#### 2. 부정 감정 비율 (`range_negative_ratio.png`)

```
전체 부정 감정 비율 추이
- 50% 기준선 표시
- 시간에 따른 변화 확인
```

#### 3. 키워드 비율 (Stacked)

```
100% ┤ ╔═══실업률═══╗
     │ ║             ║
 75% ┤ ║  경제활동    ║
     │ ║             ║
 50% ┤ ║   가계신용   ║
     │ ║             ║
 25% ┤ ║    GDP      ║
     │ ║             ║
  0% ┤ ╚═════════════╝
     └──────────────────
```

**해석:** 시간에 따른 키워드 구성 변화

#### 4. Small Multiples (키워드)

```
┌────실업률────┐  ┌───경제활동인구─┐
│    ╱╲        │  │       ╱─╲      │
│   ╱  ╲       │  │      ╱   ╲     │
│  ╱    ╲      │  │     ╱     ╲    │
└──────────────┘  └────────────────┘

┌──고용률──────┐  ┌───가계신용─────┐
│      ╱───╲   │  │   ╱╲  ╱╲      │
│     ╱     ╲  │  │  ╱  ╲╱  ╲     │
│    ╱       ╲ │  │ ╱        ╲    │
└──────────────┘  └────────────────┘
```

**10개 키워드 개별 추이**

#### 5. Small Multiples (감정)

```
┌─────분노─────┐  ┌────불안────────┐
│    ╱╲        │  │       ╱─╲      │
└──────────────┘  └────────────────┘

┌─────슬픔─────┐  ┌────상처────────┐
│      ╱───╲   │  │   ╱╲  ╱╲      │
└──────────────┘  └────────────────┘

┌─────기쁨─────┐  ┌────당황────────┐
│    ╱╲        │  │       ╱─╲      │
└──────────────┘  └────────────────┘
```

**6개 감정 개별 추이**

---

### Monthly-level (월별)

#### 1. 월별 SEEI 추이 (`monthly_seei_trend.png`)

```
월별 집계 (Range → Monthly 변환)
- Sum: total_seei, posts, comments
- Weighted Avg: 비율, neg_ratio (댓글 수 가중)
```

#### 2. Dual Axis (`monthly_dual_axis.png`)

```
SEEI (좌축)            자살 사망자수 (우축)
  20 ┤              ● 1200
     │            ●     
  15 ┤          ●    ● 1000
     │        ●    ●
  10 ┤──────●────●──── 800
     │    ●    ●
   5 ┤  ●    ●         600
     └─────────────────────
      2020  2021  2022
```

**파란 선:** SEEI  
**빨간 선:** 자살 사망자수

**목적:** 시각적 상관관계 확인

---

### 통계 분석

#### 1. 산점도 (`scatter_correlation.png`)

```
자살 사망자수
    ┤
1200┤        ●
    │      ●   ●
1000┤    ●   ●
    │  ●   ●
 800┤●   ●          추세선: y = ax + b
    │  ●
 600┤●
    └────────────────────
     10   15   20  SEEI

r = 0.523, p = 0.001
```

**Pearson 상관계수:**
- r > 0.5: 중간 이상 상관
- p < 0.05: 통계적 유의

#### 2. 교차상관 (`cross_correlation.png`)

```
상관계수
  0.8┤
     │        ●
  0.6┤      ●   ●
     │    ●       ●
  0.4┤  ●           ●
     │●               ●
  0.2┤
     └─────────────────────
     -6  -3   0   3   6  Lag

음수 lag: SEEI가 선행
양수 lag: 자살이 선행
```

**최적 lag 찾기:**
- lag = -3 (최대 상관)
- SEEI가 3개월 선행

#### 3. Granger 인과관계 (`granger_pvalues.png`)

```
p-value
  0.10┤
      │
  0.05┤─ ─ ─ ─ ─ ─ ─ ─ ─  (유의수준)
      │    ●     ●
  0.03┤  ●   ●
      │
  0.01┤
      └──────────────────
       1   2   3   4  Lag

p < 0.05: 통계적 유의
```

**해석:**
- lag 1, 2, 3 유의 → SEEI가 자살을 선행 예측

#### 4. 통계 결과 JSON (`leading_analysis.json`)

```json
{
  "correlation": {
    "pearson_r": 0.523,
    "p_value": 0.001
  },
  "cross_correlation": {
    "best_lag": -3,
    "correlation": 0.645
  },
  "granger": {
    "1": 0.023,
    "2": 0.015,
    "3": 0.031,
    "4": 0.087
  }
}
```

---

## 📈 실행 결과 예시

```
============================================================
            SEEI Visualization & Statistical Analysis        
============================================================

[INFO] Creating output directory: /home/mindcastlib/data/seei/visualization
[INFO] Running visualization script...

Loading master JSON...
  - 105 records loaded

Converting to monthly...
  - 36 months aggregated

Loading suicide data...
  - 36 records loaded

Generating visualizations...

  [1/11] range_seei_trend.png
  [2/11] range_negative_ratio.png
  [3/11] range_keyword_ratio.png
  [4/11] keyword_small_multiples.png
  [5/11] emotion_small_multiples.png
  [6/11] monthly_seei_trend.png
  [7/11] monthly_dual_axis.png
  [8/11] scatter_correlation.png
  [9/11] cross_correlation.png
  [10/11] granger_pvalues.png
  [11/11] leading_analysis.json

✅ Visualization Completed!

------------------------------------------------------------
 ✅ SUCCESS: Visualization complete!
 📁 Output saved at: /home/mindcastlib/data/seei/visualization
------------------------------------------------------------
```

---

## 🎯 Monthly 집계 로직

### Sum 대상

```python
# 합계 계산
total_seei (월별 SEEI 합)
posts (월별 포스트 수 합)
comments (월별 댓글 수 합)
kw_실업률 (월별 키워드 점수 합)
```

### Weighted Average 대상

```python
# 댓글 수 가중 평균
neg_ratio_overall = Σ(neg_ratio × comments) / Σ(comments)
kw_ratio_실업률 = Σ(ratio × comments) / Σ(comments)
emo_분노 = Σ(ratio × comments) / Σ(comments)
```

**이유:** 댓글이 많은 날의 비율이 더 중요

---

## ⚠️ 주의사항

### 1. 한글 폰트

```python
# 한글 깨짐 시
plt.rcParams["font.family"] = "NanumGothic"

# 폰트 설치 확인
import matplotlib.pyplot as plt
print(plt.rcParams["font.family"])
```

### 2. 자살 데이터 형식

```csv
# ✅ 올바른 형식
날짜,자살사망자수
2020-01,1092
2020-02,1045
```

```csv
# ❌ 잘못된 형식
date,deaths
2020-01-10,123  # 월별이 아님
```

### 3. 통계 분석 최소 데이터

```python
# Granger 검정: 최소 20개 데이터 필요
if len(df_monthly) < 20:
    print("Not enough data for Granger test")
```

### 4. 메모리 사용

```bash
# matplotlib + seaborn: ~300-500MB
# 메모리 부족 시 폰트 캐시 삭제
rm -rf ~/.cache/matplotlib
```

---

## 🐛 트러블슈팅

### Q1: "Master JSON not found"

```bash
# 원인: Master 파일 미생성
# 해결:
bash 3_update_master.sh
```

### Q2: 한글 깨짐 (□□□ 표시)

```bash
# 해결 1: 나눔고딕 설치
sudo apt-get install fonts-nanum

# 해결 2: matplotlib 캐시 삭제
rm -rf ~/.cache/matplotlib

# 해결 3: 스크립트 수정
# visualize_seei.py에서:
plt.rcParams["font.family"] = "NanumGothic"
```

### Q3: "KeyError: '날짜'"

```bash
# 원인: 자살 데이터 컬럼명 불일치
# 해결: CSV 파일 확인

head -1 /home/mindcastlib/data/base/base_data.csv
# 컬럼명이 "날짜"인지 확인
```

### Q4: Granger 검정 실패

```python
# ERROR: Not enough observations
# 원인: 데이터 부족 (<20개)
# 해결: 더 많은 데이터 필요 또는 경고 무시
```

### Q5: 그래프가 생성되지 않음

```bash
# 원인: display 설정
# 해결: 백엔드 설정
export MPLBACKEND=Agg

# 또는 스크립트 시작 부분에 추가:
import matplotlib
matplotlib.use('Agg')
```

---

## 📊 통계 해석 가이드

### Pearson 상관계수 (r)

| 범위 | 해석 |
|------|------|
| 0.0 ~ 0.3 | 약한 상관 |
| 0.3 ~ 0.5 | 중간 상관 |
| 0.5 ~ 0.7 | 강한 상관 |
| 0.7 ~ 1.0 | 매우 강한 상관 |

### p-value

| 값 | 해석 |
|----|------|
| p < 0.001 | 매우 유의 (***) |
| p < 0.01 | 유의 (**) |
| p < 0.05 | 유의 (*) |
| p ≥ 0.05 | 유의하지 않음 |

### Cross-correlation lag

| Lag | 의미 |
|-----|------|
| -3 | SEEI가 3개월 선행 |
| 0 | 동시 변화 |
| +3 | 자살이 3개월 선행 |

### Granger 인과관계

```
p < 0.05: SEEI가 자살을 Granger-cause
→ SEEI가 유의한 선행지표
```

---


### 3. 대시보드 구축

```javascript
// React + Recharts
<LineChart data={seei_data}>
  <Line dataKey="total_seei" stroke="#8884d8" />
  <Line dataKey="suicide_deaths" stroke="#82ca9d" />
</LineChart>
```

---

## 📝 체크리스트

**실행 전 확인:**
- [ ] Master JSON 생성 완료
- [ ] 자살 데이터 준비 (월별)
- [ ] 한글 폰트 설치
- [ ] 필요 패키지 설치
- [ ] 출력 디렉토리 권한 확인

**실행 후 확인:**
- [ ] range/ 디렉토리 (5개 파일)
- [ ] monthly/ 디렉토리 (6개 파일)
- [ ] 한글 정상 표시
- [ ] 통계 결과 JSON 생성
- [ ] p-value < 0.05 확인

**논문 활용 시:**
- [ ] 그래프 해상도 300 dpi
- [ ] 통계 유의성 확인
- [ ] 선행지표 근거 확보
- [ ] 그래프 캡션 작성

---

**마지막 업데이트:** 2025-12-10
**예상 소요 시간:** 30-60초
**출력 파일 수:** 11개
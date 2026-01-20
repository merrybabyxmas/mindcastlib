#!/bin/bash

# ======================================================
# SEEI 통합 파이프라인
# ======================================================
# 1. 배치 처리 (2020-2022)
# 2. 마스터 파일 갱신
# 3. 요약 리포트
# ======================================================

set -e

# ======================================================
# 🔧 설정
# ======================================================
BASE_DIR="/home/mindcastlib/data/analysis_results2/2020"
DAILY_DIR="/home/mindcastlib/data/seei/seei_daily"
MASTER_FILE="/home/mindcastlib/data/seei/seei_master/seei_master.csv"

YEARS=("2020" "2021" "2022")
BASE_YEAR="2020"
BASE_DATE="2020-01-10"

# ======================================================
# 초기화
# ======================================================
mkdir -p ${DAILY_DIR}
mkdir -p $(dirname ${MASTER_FILE})

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║     SEEI Full Pipeline (2020-2022)                ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "Start: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

PIPELINE_START=$(date +%s)

# ======================================================
# STEP 1: 배치 처리
# ======================================================
echo "╔════════════════════════════════════════════════════╗"
echo "║  STEP 1: Batch Processing                         ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

STEP1_START=$(date +%s)
TOTAL=0
SUCCESS=0
FAILED=0

for YEAR in "${YEARS[@]}"; do
    YEAR_DIR="${BASE_DIR}/${YEAR}"
    
    echo "📅 ${YEAR}"
    
    if [ ! -d "${YEAR_DIR}" ]; then
        echo "   ⚠️  Not found"
        continue
    fi
    
    for MONTH_DIR in ${YEAR_DIR}/*; do
        [ ! -d "${MONTH_DIR}" ] && continue
        
        MONTH=$(basename ${MONTH_DIR})
        echo "   📆 ${MONTH}"
        
        for RANGE_DIR in ${MONTH_DIR}/*; do
            [ ! -d "${RANGE_DIR}" ] && continue
            
            json_files=(${RANGE_DIR}/*.json)
            [ ${#json_files[@]} -eq 0 ] || [ ! -f "${json_files[0]}" ] && continue
            
            for JSON_FILE in "${json_files[@]}"; do
                [ ! -f "${JSON_FILE}" ] && continue
                
                TOTAL=$((TOTAL + 1))
                
                if python compute_daily_seei.py \
                    --input "${JSON_FILE}" \
                    --output_dir "${DAILY_DIR}" > /dev/null 2>&1; then
                    SUCCESS=$((SUCCESS + 1))
                else
                    FAILED=$((FAILED + 1))
                fi
            done
        done
    done
done

STEP1_END=$(date +%s)
STEP1_TIME=$((STEP1_END - STEP1_START))

echo ""
echo "───────────────────────────────────────────────────"
echo "Total: ${TOTAL} | Success: ${SUCCESS} | Failed: ${FAILED}"
echo "Time: ${STEP1_TIME}s"
echo "───────────────────────────────────────────────────"
echo ""

[ ${SUCCESS} -eq 0 ] && echo "❌ No files processed" && exit 1

# ======================================================
# STEP 2: 마스터 갱신
# ======================================================
echo "╔════════════════════════════════════════════════════╗"
echo "║  STEP 2: Master Update                            ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

STEP2_START=$(date +%s)

DAILY_COUNT=$(find ${DAILY_DIR} -name "seei_*.csv" 2>/dev/null | wc -l)
echo "Daily files: ${DAILY_COUNT}"
echo ""

# 백업
if [ -f "${MASTER_FILE}" ]; then
    cp "${MASTER_FILE}" "${MASTER_FILE}.backup"
    echo "📦 Backup created"
    echo ""
fi

# 실행
python update_seei_master.py batch \
    --daily_dir "${DAILY_DIR}" \
    --master "${MASTER_FILE}" \
    --base_year "${BASE_YEAR}" \
    --base_date "${BASE_DATE}"

STEP2_END=$(date +%s)
STEP2_TIME=$((STEP2_END - STEP2_START))

echo ""
echo "───────────────────────────────────────────────────"
echo "Time: ${STEP2_TIME}s"
echo "───────────────────────────────────────────────────"
echo ""

# ======================================================
# STEP 3: 리포트
# ======================================================
echo "╔════════════════════════════════════════════════════╗"
echo "║  STEP 3: Summary Report                           ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

python << 'EOF'
import pandas as pd

try:
    df = pd.read_csv("/home/mindcastlib/seei_master/seei_master.csv", parse_dates=["date"])
    
    print("📊 Statistics")
    print("=" * 60)
    print(f"Records:  {len(df)}")
    print(f"Range:    {df['date'].min().strftime('%Y-%m-%d')} → {df['date'].max().strftime('%Y-%m-%d')}")
    print()
    
    print("📈 Latest")
    print("-" * 60)
    latest = df.iloc[-1]
    print(f"Date:     {latest['date'].strftime('%Y-%m-%d')}")
    print(f"SEEI:     {latest['total_seei']:.2f}")
    print(f"Index:    {latest['seei_index']:.1f}")
    print(f"Risk:     {latest['risk_level']}")
    
    if not pd.isna(latest['mom_index_change']):
        emoji = "📈" if latest['mom_index_change'] > 0 else "📉"
        print(f"MoM:      {emoji} {latest['mom_index_change']:+.1f}%")
    
    if not pd.isna(latest['yoy_index_change']):
        emoji = "📈" if latest['yoy_index_change'] > 0 else "📉"
        print(f"YoY:      {emoji} {latest['yoy_index_change']:+.1f}%")
    
    print()
    print("🎯 Risk Distribution")
    print("-" * 60)
    for level, count in df['risk_level'].value_counts().sort_index().items():
        pct = count / len(df) * 100
        print(f"{level:15s} {count:3d} ({pct:5.1f}%)")
    
except Exception as e:
    print(f"❌ Error: {e}")
EOF

# ======================================================
# 완료
# ======================================================
PIPELINE_END=$(date +%s)
TOTAL_TIME=$((PIPELINE_END - PIPELINE_START))
MINUTES=$((TOTAL_TIME / 60))
SECONDS=$((TOTAL_TIME % 60))

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║  Completed ✅                                      ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "Time: ${MINUTES}m ${SECONDS}s"
echo "Master: ${MASTER_FILE}"
echo ""
echo "End: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
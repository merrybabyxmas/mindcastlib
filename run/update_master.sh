#!/bin/bash

# ======================================================
# SEEI 마스터 파일 갱신 (v3 - Raw SEEI)
# ======================================================

set -e

# ======================================================
# 🔧 설정
# ======================================================
DAILY_DIR="/home/mindcastlib/data/seei/seei_daily"
MASTER_FILE="/home/mindcastlib/data/seei/seei_master/seei_master.csv"

# ======================================================
# 실행
# ======================================================
mkdir -p $(dirname ${MASTER_FILE})

echo "========================================"
echo "SEEI Master Update (v3 - Raw SEEI)"
echo "========================================"
echo "Daily: ${DAILY_DIR}"
echo "Master: ${MASTER_FILE}"
echo ""

# Daily 파일 카운트
DAILY_COUNT=$(find ${DAILY_DIR} -name "seei_*.csv" 2>/dev/null | wc -l)

if [ ${DAILY_COUNT} -eq 0 ]; then
    echo "❌ No daily files found"
    exit 1
fi

echo "Found ${DAILY_COUNT} daily files"
echo ""

# 백업
if [ -f "${MASTER_FILE}" ]; then
    cp "${MASTER_FILE}" "${MASTER_FILE}.backup"
    echo "📦 Backup created"
fi

# 배치 업데이트 (v3 - base_year, base_date 인자 제거)
python /home/mindcastlib/mindcastlib/scripts/update_seei_master.py batch \
    --daily_dir "${DAILY_DIR}" \
    --master "${MASTER_FILE}"

echo ""
echo "✅ Done"
echo ""
echo "Output:"
echo "  - CSV: ${MASTER_FILE}"
echo "  - JSON: ${MASTER_FILE/.csv/.json}"
#!/bin/bash

# ======================================================
# SEEI 시각화 (Custom Lag 지원)
# ======================================================

set -e

# ======================================================
# 🔧 설정
# ======================================================
MASTER_JSON="/home/mindcastlib/data/seei/seei_master/seei_master.json"
SUICIDE_CSV="/home/mindcastlib/data/base/base_data.csv"
OUTPUT_DIR="/home/mindcastlib/data/seei/visualization"

# Custom lag 값들 (쉼표 구분)
# 음수: SEEI 선행, 양수: 자살 선행, 0: 동시
CUSTOM_LAGS="0"

# ======================================================
# 실행
# ======================================================
echo "======================================"
echo "SEEI Visualization"
echo "======================================"
echo "Master JSON: ${MASTER_JSON}"
echo "Suicide CSV: ${SUICIDE_CSV}"
echo "Output: ${OUTPUT_DIR}"
echo "Custom Lags: ${CUSTOM_LAGS}"
echo ""

python3 /home/mindcastlib/mindcastlib/scripts/visualize_seei.py \
    --master_json "${MASTER_JSON}" \
    --suicide_csv "${SUICIDE_CSV}" \
    --output_dir "${OUTPUT_DIR}" \
    --lags "${CUSTOM_LAGS}"

echo ""
echo "✅ Done!"
echo ""
echo "Generated files:"
echo "  Range-level: ${OUTPUT_DIR}/range/"
echo "  Monthly-level: ${OUTPUT_DIR}/monthly/"
echo ""
echo "Custom lag files:"
ls -1 ${OUTPUT_DIR}/monthly/monthly_dual_axis_lag*.png 2>/dev/null | tail -10
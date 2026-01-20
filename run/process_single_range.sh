#!/bin/bash

# ======================================================
# 단일 Range SEEI 계산
# ======================================================
# 사용법: 
#   1. 아래 INPUT_FILE 경로 설정 후 실행: bash 1_process_single_range.sh
#   2. 또는 인수로 전달: bash 1_process_single_range.sh /path/to/file.json
# ======================================================

set -e

# ======================================================
# 🔧 설정 (여기만 수정)
# ======================================================
INPUT_FILE="/home/mindcastlib/data/analysis_results2/2020/01/11-20/infer_20251210_134354.json"
OUTPUT_DIR="/home/mindcastlib/data/seei/seei_daily"

# ======================================================
# 인수로 파일 경로가 주어지면 그것을 사용
# ======================================================
if [ $# -eq 1 ]; then
    INPUT_FILE="$1"
fi

# 파일 존재 확인
if [ ! -f "${INPUT_FILE}" ]; then
    echo "❌ File not found: ${INPUT_FILE}"
    echo ""
    echo "Please set INPUT_FILE in the script or provide as argument:"
    echo "  bash $0 /path/to/file.json"
    exit 1
fi

# ======================================================
# 실행
# ======================================================
mkdir -p ${OUTPUT_DIR}

echo "Processing: ${INPUT_FILE}"
echo "Output: ${OUTPUT_DIR}"
echo ""

python /home/mindcastlib/mindcastlib/scripts/compute_daily_seei.py \
    --input "${INPUT_FILE}" \
    --output_dir "${OUTPUT_DIR}"

echo ""
echo "✅ Done"
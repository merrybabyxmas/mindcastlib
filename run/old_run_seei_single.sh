#!/bin/bash
# ============================================================
# run_seei_single.sh
# 단일 JSON 파일 → SEEI 점수 계산
# ============================================================

echo "======================================"
echo " Run: preprocess_seei_single"
echo "======================================"

# Python 파일 경로
SCRIPT="/home/mindcastlib/mindcastlib/scripts/preprocess_seei_single.py"

# 입력 파일 (JSON)
INPUT_FILE="/home/mindcastlib/data/single_results/infer_20251208_162012.json"   # ex) /path/to/file.json

# 출력 디렉토리(고정)
OUTPUT_DIR="/home/mindcastlib/data/SEEI/single"
mkdir -p "$OUTPUT_DIR"

# 출력 파일
OUT_FILE="$OUTPUT_DIR/single_result.csv"

# 가상환경 활성화 (필요시)
# source /home/mindcastlib/venv/bin/activate

python "$SCRIPT" \
  --file "$INPUT_FILE" \
  --out "$OUT_FILE"

STATUS=$?

echo "--------------------------------------"
if [ $STATUS -eq 0 ]; then
    echo " ✅ SUCCESS: File processed"
    echo " 👉 Output: $OUT_FILE"
else
    echo " ❌ ERROR: Exit code $STATUS"
fi
echo "--------------------------------------"

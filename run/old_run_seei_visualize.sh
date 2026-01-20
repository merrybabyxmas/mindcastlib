#!/bin/bash
# ============================================================
# run_seei_visualize.sh
# SEEI 점수 CSV 파일 → 시각화 (HTML 파일)
# ============================================================

echo "======================================"
echo " 🚀 Run: seei_visualize"
echo "======================================"

# ------------------------------------------------------------
# 1. 사용자 설정 영역 (이 부분만 수정하면 됨)
# ------------------------------------------------------------
# Python 파일 경로 (고정)
SCRIPT="/home/mindcastlib/mindcastlib/scripts/seei_visualize.py"

# 입력 1: SEEI 계산 결과 CSV 파일
SEEI_RAW_FILE="/home/mindcastlib/data/SEEI/all/SEEI_raw.csv"

# 입력 2: 원본 경제 지표 데이터 CSV 파일
BASE_DATA_FILE="/home/mindcastlib/data/base/base_data.csv"

# 출력 디렉토리 (시각화 HTML 저장 폴더)
SAVE_DIR="/home/mindcastlib/data/SEEI/visualization"
# ------------------------------------------------------------

# 2. 출력 디렉토리 생성
mkdir -p "$SAVE_DIR"

echo "[INFO] SEEI CSV: $SEEI_RAW_FILE"
echo "[INFO] Base Data: $BASE_DATA_FILE"
echo "[INFO] Output Dir: $SAVE_DIR"

# 3. Python 스크립트 실행 (인수를 전달)
# 가상환경 활성화 (필요시 주석 해제)
# source /home/mindcastlib/venv/bin/activate

python "$SCRIPT" \
  --seei "$SEEI_RAW_FILE" \
  --base "$BASE_DATA_FILE" \
  --out "$SAVE_DIR"

STATUS=$?

# 4. 종료 메시지
echo "--------------------------------------"
if [ $STATUS -eq 0 ]; then
    echo " ✅ SUCCESS: Visualizations created"
    echo " 👉 Output directory: $SAVE_DIR"
else
    echo " ❌ ERROR: Exit code $STATUS"
fi
echo "--------------------------------------"
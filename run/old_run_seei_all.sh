#!/bin/bash
# ============================================================
# run_seei_all.sh
# 다수 연도의 분석 JSON 파일 → SEEI 점수 계산
# ============================================================

echo "======================================"
echo " 🚀 Run: preprocess_seei_all"
echo "======================================"

# ------------------------------------------------------------
# 1. 사용자 설정 영역 (이 부분만 수정하면 됨)
# ------------------------------------------------------------
# Python 파일 경로 (고정)
SCRIPT="/home/mindcastlib/mindcastlib/scripts/preprocess_seei_all.py"

# 입력 루트 디렉토리 (연도별 infer 파일들 위치)
# 예: /home/mindcastlib/data/analysis_results1/2020/01/...
BASE_ROOT="/home/mindcastlib/data/analysis_results"

# 출력 디렉토리 (결과 CSV 저장 폴더)
OUTPUT_DIR="/home/mindcastlib/data/SEEI/all"

# 처리할 연도 리스트 (공백으로 구분)
YEARS="2020 2021 2022 2023"
# ------------------------------------------------------------

# 2. 출력 디렉토리 생성
mkdir -p "$OUTPUT_DIR"

echo "[INFO] Input Root: $BASE_ROOT"
echo "[INFO] Output Dir: $OUTPUT_DIR"
echo "[INFO] Years to process: $YEARS"

# 3. Python 스크립트 실행 (인수를 전달)
# 가상환경 활성화 (필요시 주석 해제)
# source /home/mindcastlib/venv/bin/activate

python "$SCRIPT" \
  --root "$BASE_ROOT" \
  --out "$OUTPUT_DIR" \
  --years $YEARS

STATUS=$?

# 4. 종료 메시지
echo "--------------------------------------"
if [ $STATUS -eq 0 ]; then
    echo " ✅ SUCCESS: All files processed"
    echo " 👉 Output directory: $OUTPUT_DIR"
else
    echo " ❌ ERROR: Exit code $STATUS"
fi
echo "--------------------------------------"
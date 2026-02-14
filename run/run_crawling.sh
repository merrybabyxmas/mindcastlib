#!/bin/bash

echo "============================================"
echo " 🚀 Suicide Data Crawling Pipeline Start"
echo "============================================"

# ------------------------------------------------------------
# 1. 이 스크립트 기준으로 프로젝트 루트 자동 계산
# ------------------------------------------------------------
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")/.."     # run -> mindcastlib -> project root
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

CONFIG_PATH="$PROJECT_ROOT/mindcastlib/configs/crawling_config.yaml"

# ------------------------------------------------------------
# 2. 프로젝트 상위 루트로 이동
# ------------------------------------------------------------
cd "$PROJECT_ROOT" || exit
echo "[INFO] Working directory: $(pwd)"

# ------------------------------------------------------------
# 3. PYTHONPATH 설정
# ------------------------------------------------------------
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo "[INFO] PYTHONPATH : $PYTHONPATH"
echo "[INFO] CONFIG_PATH: $CONFIG_PATH"

# ------------------------------------------------------------
# 4. 실행
# ------------------------------------------------------------
echo "[INFO] Running crawling pipeline..."

python -m mindcastlib.pipeline.crawling_pipeline "$CONFIG_PATH"

# 5. 실패 시 직접 실행
if [ $? -ne 0 ]; then
    echo "[WARN] Module run failed. Retrying with direct script execution..."
    python mindcastlib/pipeline/crawling_pipeline.py "$CONFIG_PATH"
fi

STATUS=$?

# ------------------------------------------------------------
# 6. 결과 출력
# ------------------------------------------------------------
if [ $STATUS -eq 0 ]; then
    echo "[SUCCESS] Crawling pipeline completed successfully!"
else
    echo "[ERROR] Crawling pipeline failed with exit code $STATUS"
fi

echo "============================================"
echo " Suicide Data Crawling Pipeline Done"
echo "============================================"
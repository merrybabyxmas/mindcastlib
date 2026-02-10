#!/bin/bash

# ============================================================
# mindcastlib - Crawling Pipeline Runner
# 위치: /home/mindcastlib/mindcastlib/run/run_crawling_pipeline.sh
# ============================================================

echo "============================================"
echo " 🚀 Suicide Data Crawling Pipeline Start"
echo "============================================"

# ------------------------------------------------------------
# 1. 사용자 설정 영역 (config 경로)
# ------------------------------------------------------------
CONFIG_PATH="/home/mindcastlib/mindcastlib/configs/crawling_config.yaml"
# ------------------------------------------------------------

# 2. 프로젝트 루트로 이동
cd /home/mindcastlib || exit
echo "[INFO] Working directory: $(pwd)"

# 3. PYTHONPATH 설정
export PYTHONPATH=/home/mindcastlib:$PYTHONPATH

echo "[INFO] PYTHONPATH : $PYTHONPATH"
echo "[INFO] CONFIG_PATH: $CONFIG_PATH"

# 4. 실행 - python -m 방식 우선
echo "[INFO] Running crawling pipeline..."

python -m mindcastlib.pipeline.crawling_pipeline "$CONFIG_PATH"

# 5. 실패하면 .py 직접 실행
if [ $? -ne 0 ]; then
    echo "[WARN] Module run failed. Retrying with direct script execution..."
    python mindcastlib/pipeline/crawling_pipeline.py "$CONFIG_PATH"
fi

STATUS=$?

# 6. 실행 결과 처리
if [ $STATUS -eq 0 ]; then
    echo "[SUCCESS] Crawling pipeline completed successfully!"
else
    echo "[ERROR] Crawling pipeline failed with exit code $STATUS"
fi

echo "============================================"
echo " Suicide Data Crawling Pipeline Done" 
echo "============================================"
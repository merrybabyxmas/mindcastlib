#!/bin/bash

# ======================================================
# 다년도 배치 SEEI 계산 (2020-2022)
# ======================================================
# 모든 년도/월/range를 자동으로 순회하며 처리
# ======================================================

set -e

# ======================================================
# 🔧 설정 (여기만 수정)
# ======================================================
BASE_DIR="/home/mindcastlib/data/analysis_results2"
OUTPUT_DIR="/home/mindcastlib/data/seei/seei_daily"

# 처리할 년도 리스트
YEARS=("2020" "2021" "2022")

# ======================================================
# 초기화
# ======================================================
mkdir -p ${OUTPUT_DIR}

TOTAL_FILES=0
PROCESSED_FILES=0
FAILED_FILES=0

# ======================================================
# 메인 처리
# ======================================================
echo "========================================"
echo "Batch SEEI Processing (2020-2022)"
echo "========================================"
echo "Base: ${BASE_DIR}"
echo "Output: ${OUTPUT_DIR}"
echo ""

# 년도별 처리
for YEAR in "${YEARS[@]}"; do
    YEAR_DIR="${BASE_DIR}/${YEAR}"
    
    echo "📅 Year: ${YEAR}"
    
    if [ ! -d "${YEAR_DIR}" ]; then
        echo "   ⚠️  Directory not found"
        continue
    fi
    
    # 월별 처리
    for MONTH_DIR in ${YEAR_DIR}/*; do
        if [ ! -d "${MONTH_DIR}" ]; then
            continue
        fi
        
        MONTH=$(basename ${MONTH_DIR})
        echo "   📆 Month: ${MONTH}"
        
        # Range별 처리
        for RANGE_DIR in ${MONTH_DIR}/*; do
            if [ ! -d "${RANGE_DIR}" ]; then
                continue
            fi
            
            RANGE=$(basename ${RANGE_DIR})
            
            # JSON 파일 찾기
            json_files=(${RANGE_DIR}/*.json)
            
            if [ ${#json_files[@]} -eq 0 ] || [ ! -f "${json_files[0]}" ]; then
                continue
            fi
            
            # 각 JSON 파일 처리
            for JSON_FILE in "${json_files[@]}"; do
                if [ ! -f "${JSON_FILE}" ]; then
                    continue
                fi
                
                FILENAME=$(basename ${JSON_FILE})
                TOTAL_FILES=$((TOTAL_FILES + 1))
                
                echo "      📄 ${FILENAME}"
                
                if python /home/mindcastlib/mindcastlib/scripts/compute_daily_seei.py \
                    --input "${JSON_FILE}" \
                    --output_dir "${OUTPUT_DIR}"; then
                    
                    PROCESSED_FILES=$((PROCESSED_FILES + 1))
                    echo "         ✓"
                else
                    FAILED_FILES=$((FAILED_FILES + 1))
                    echo "         ✗ FAILED"
                    echo ""
                    echo "❌ First failure detected. Stopping for debugging."
                    echo "Failed file: ${JSON_FILE}"
                    exit 1
                fi
            done
        done
    done
done

# ======================================================
# 최종 요약
# ======================================================
echo ""
echo "========================================"
echo "Summary"
echo "========================================"
echo "Total:      ${TOTAL_FILES}"
echo "Success:    ${PROCESSED_FILES}"
echo "Failed:     ${FAILED_FILES}"
echo "========================================"
echo ""

OUTPUT_COUNT=$(find ${OUTPUT_DIR} -name "seei_*.csv" 2>/dev/null | wc -l)
echo "Generated: ${OUTPUT_COUNT} CSV files"
echo "Location: ${OUTPUT_DIR}"
echo ""
echo "✅ Done"
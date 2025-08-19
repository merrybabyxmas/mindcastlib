#!/bin/bash
# run_preprocess.sh

# 실행 경로를 변수로 지정
INPUT_DIR="/home/jeongseon38/MLLAB/mentalHealth/data/original_data"
OUTPUT_DIR="/home/jeongseon38/MLLAB/mentalHealth/data/preprocessed_data"

# 실행
python -m mindcastlib.pipeline.preprocess \
  --input_dir "$INPUT_DIR" \
  --output_dir "$OUTPUT_DIR" \
  --save \
  --monitoring

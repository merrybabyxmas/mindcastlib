# 정신건강 프로젝트 패키지

## 1. Analysis Pipeline
- **기능**: 뉴스 감정 분류, 토픽 분류, 요약
- **✅완료**
  1. 모듈별 target 설정 가능 (`title`, `comments`)
  2. 모듈별 model 설정 가능 (base model, fine-tuned model 등)
  3. config preset 제공 (customizing 가능)
  4. 날짜 조건 데이터 읽기 기능
- **추가 예정**
  1. modelConfig 프리셋 추가
  2. 실시간 모니터링 기능 (`self.monitoring = True`)
  3. 제목-댓글 관계 분석 기능

## 2. Train Pipeline
- **기능**: 감정 분류, 토픽 분류, 요약 모델 학습
- **추가 예정**
  1. 학습 방법 옵션 제공 (`lastlayerFT`, `LoRA`, `train-freeFT` 등)
  2. 학습 모니터링 기능 (TensorBoard 등)
  3. baseModel 성능 비교 기능

## 3. Debug Pipeline
- **기능**: DB 연동 및 성능 점검
- **추가 예정**
  1. 추론 시간 모니터링
  2. 저장 용량 모니터링
  3. config별 FILE I/O 및 GPU/CPU 사용량 비교

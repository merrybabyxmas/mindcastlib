# 🧠 정신건강 프로젝트 패키지

---

## 1. **Analysis Pipeline**  
> 기존 정신건강 분석 파이프라인 — 뉴스 감정 분류, 토픽 분류, 요약 수행

### ✅ 완료 사항
1. 모듈별 원하는 **Target** 설정 가능 (`title`, `comments`)
2. 모듈별 원하는 **Model** 설정 가능 (예: base model, fine-tuned model)
3. **Config Preset** 제공 (사용자 정의 Config 가능)
4. **날짜 조건**으로 데이터 읽기 기능 제공

### 🚧 진행 예정
- [ ] **ModelConfig 프리셋** 추가 (현재는 default model preset만 존재)
- [ ] **실시간 모니터링** 기능 추가 (`self.monitoring = True`)
- [ ] 추가 기능: *제목 - 댓글 간 관계 분석* 등

---

## 2. **Train Pipeline**  
> 뉴스 감정 분류, 토픽 분류, 요약 모델 학습 파이프라인

### 🚧 진행 예정
- [ ] 학습 방법 옵션 제공  
  *(예: `Literal["lastlayerFT", "LoRA", "train-freeFT"]`)*
- [ ] **학습 모니터링** 기능 추가 (예: TensorBoard)
- [ ] 추가 기능: *BaseModel과의 성능 비교 Pipeline*

---

## 3. **Debug Pipeline**  
> DB 연동 및 성능 검증을 위한 파이프라인

### 🚧 진행 예정
- [ ] **추론 시간** 모니터링
- [ ] **저장 용량** 모니터링
- [ ] Config별 **FILE I/O 시간 + Data & GPU/CPU 사용량** Grid 비교 기능

---

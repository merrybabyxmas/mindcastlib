# 정신건강 프로젝트 패키지

> 뉴스 데이터의 **감정 분류**, **토픽 분류**, **요약**을 위한 분석/학습/디버깅 파이프라인

## 설치

```bash
# (선택) 가상환경 권장
python -m venv venv39
source venv39/bin/activate   # Windows: venv39\Scripts\activate

# 의존성 설치
pip install -r /home/dongwoo38/mindcastlib/requirements.txt
```

---

## 1) Analysis Pipeline

- **기능**: 뉴스 감정 분류, 토픽 분류, 요약
- **완료 사항**
  1. 모듈별 `target` 설정 가능 (`title`, `comments`)
  2. 모듈별 `model` 설정 가능 (base model, fine-tuned model 등)
  3. `config` preset 제공 (customizing 가능)
  4. **날짜 조건** 데이터 읽기 기능
- **추가 예정**
  - [ ] `modelConfig` 프리셋 추가
  - [ ] 실시간 모니터링 (`self.monitoring = True`)
  - [ ] 제목–댓글 **관계 분석** 기능

---

## 2) Train Pipeline

- **기능**: 감정 분류, 토픽 분류, 요약 **모델 학습**
- **추가 예정**
  - [ ] 학습 방법 옵션 (`lastlayerFT`, `LoRA`, `train-freeFT` 등)
  - [ ] 학습 모니터링 (TensorBoard 등)
  - [ ] baseModel **성능 비교** 기능

---

## 3) Debug Pipeline

- **기능**: DB 연동 및 성능 점검
- **추가 예정**
  - [ ] **추론 시간** 모니터링
  - [ ] **저장 용량** 모니터링
  - [ ] `config`별 **FILE I/O 및 GPU/CPU** 사용량 비교

---

## 예제: Inference Pipeline 실행

```python
from mindcastlib.pipeline import AnalysisPipeLine
from mindcastlib.src import prepare_data_with_temporal_condition
from mindcastlib.configs import AnalysisConfig
import pprint

if __name__ == "__main__":
    # 1) 날짜 조건과 입력 데이터 경로 지정
    tc = ["2023-05-01", "2023-05-02"]
    data_dir = "/home/dongwoo38/data/example/ex.json"

    # 2) 날짜 조건에 맞는 데이터 준비
    data = prepare_data_with_temporal_condition(tc, data_dir=data_dir)

    # 3) 파이프라인 구성 (프리셋 사용 예시)
    pipeline = AnalysisPipeLine(
        analysis_config=AnalysisConfig.SENT_CMT_TOPIC_TTL(),
        realtime=False,
        monitoring=True,
        save=True,
        save_dir="./outputs"
    )

    # 4) 실행
    result = pipeline.run(data)

    # 5) 결과 출력/확인
    pprint.pprint(result)
```

### 프리셋 참고
- `AnalysisConfig.SENT_CMT_TOPIC_TTL()`:
  - 감정분석: `comments`
  - 토픽분류: `title`
  - (필요시) 분류기/요약 등 모듈 확장 가능

---

## 프로젝트 구조(예시)

```
mindcastlib/
├─ configs/
│  ├─ __init__.py
│  ├─ analysis_config.py
│  └─ llm_config.py            # (untracked → add/commit 필요)
├─ pipeline/
│  ├─ __init__.py
│  └─ train_pipeline.py         # (untracked)
├─ src/
│  ├─ __init__.py
│  └─ train_utils.py            # (untracked)
└─ requirements.txt
```

> `git status`에 **Untracked files**로 뜨는 항목은 아래처럼 추가하세요:
> ```bash
> git add configs/llm_config.py pipeline/train_pipeline.py src/train_utils.py
> git commit -m "Add llm_config, train_pipeline, train_utils"
> git push origin main
> ```

---

## 팁 & 트러블슈팅

- **requirements 설치 오류**: `pip install -r <path>/requirements.txt`처럼 **반드시 `-r` 옵션**을 사용하세요.
- **패키지 임포트**: `mindcastlib/src/__init__.py`가 있다면 `from mindcastlib.src import ...` 형태로 **깔끔한 임포트**가 가능합니다.
- **경로 이슈**: 절대경로 사용 시 시스템/사용자마다 경로가 다를 수 있으니, 가능하면 **상대경로** 또는 **환경변수**로 관리하세요.

# inference_pipeline.py
from __future__ import annotations
import os
import json
import time
from typing import List, Dict, Tuple, Iterable, Literal, Optional
from dataclasses import dataclass

import torch
from transformers import pipeline

# ====== 프로젝트 내 모듈 (경로에 맞게 조정하세요) ======
# model/analysis 설정은 이전 메시지의 구조를 가정
from mindcastlib.configs import BaseConfig, DefaultModuleConfig  # 프리셋/단위 모델 설정
from mindcastlib.configs import AnalysisConfig, AnalysisUnit  

from mindcastlib.src.data_utils import prepare_data_with_temporal_condition, extract_titles, extract_comments





Target = Literal["title", "comments"]
Task = Literal["sentiment", "topic", "summary"]




def iter_posts(data: Dict):
    """모든 post를 yield (day, post)"""
    for day in data.get("data", []):
        for post in day.get("posts", []):
            yield day, post


# ---------- HF 파이프라인 래퍼 ----------
@dataclass
class HFPipeSpec:
    task: str
    cfg: BaseConfig
    name: str  # 'sentiment' | 'topic' | 'summary'


class BatchCallable:
    """
    texts(list[str]) -> list[dict or str]
    - transformers.pipeline을 감싼 콜러블
    - 배치 처리 & 장치/길이 옵션 반영
    """
    def __init__(self, spec: HFPipeSpec):
        self.name = spec.name
        self.cfg = spec.cfg

        # device 매핑: cuda -> 0, cpu -> -1
        device_idx = 0 if (self.cfg.device.startswith("cuda") and torch.cuda.is_available()) else -1

        # task 결정
        task = spec.task  # "sentiment-analysis" | "text-classification" | "summarization" 등

        # pipeline 인스턴스
        self.pipe = pipeline(
            task,
            model=self.cfg.model_name,
            tokenizer=self.cfg.model_name,
            device=device_idx,
            truncation=self.cfg.truncation
        )

        # 파라미터
        self.batch_size = self.cfg.batch_size
        self.max_length = self.cfg.max_length
        self.return_all_scores = getattr(self.cfg, "return_all_scores", False)

        # 요약일 때 생성 길이 기본치(필요하면 cfg에 추가해 확장)
        self.gen_kwargs = dict(
            max_length=min(256, self.max_length),
            min_length=8,
            do_sample=False,
        )

    def __call__(self, texts: List[str]) -> List:
        if len(texts) == 0:
            return []
        out_all = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            if self.pipe.task == "summarization":
                # summarization: 문자열 출력 통일
                out = self.pipe(batch, **self.gen_kwargs)
                # [{"summary_text": "..."}] -> "..."
                out = [o.get("summary_text", "") if isinstance(o, dict) else o for o in out]
            else:
                # classification/sentiment
                out = self.pipe(
                    batch,
                    truncation=True,
                    return_all_scores=self.return_all_scores
                )
            out_all.extend(out)
        return out_all


# ---------- 작업 빌더 ----------
def build_task_callable(task: Task, cfg: BaseConfig) -> BatchCallable:
    if task == "sentiment":
        return BatchCallable(HFPipeSpec(task="sentiment-analysis", cfg=cfg, name="sentiment"))
    elif task == "topic":
        # 일반 다중/이진 분류는 text-classification로도 동작
        return BatchCallable(HFPipeSpec(task="text-classification", cfg=cfg, name="topic"))
    elif task == "summary":
        return BatchCallable(HFPipeSpec(task="summarization", cfg=cfg, name="summary"))
    else:
        raise ValueError(f"Unknown task: {task}")


# ---------- 파이프라인 본체 ----------
class InferencePipeLine:
    def __init__(
        self,
        model_names: Tuple[Optional[str], Optional[str], Optional[str]] | None = None,
        analysis_config: AnalysisConfig | None = None,
        realtime: bool = False,
        monitoring: bool = True,
        save: bool = True,
        save_dir: str | None = None,
        use_models: List[Task] = ["sentiment", "topic", "summary"],
        comments_summary_mode: Literal["per_comment", "per_post_concat"] = "per_post_concat",
    ):
        """
        - model_names: (sentiment, topic, summary) 순서의 모델 식별자 튜플.
                       None이면 analysis_config의 모델 사용. 일부만 override해도 됨.
        - analysis_config: AnalysisConfig 프리셋 인스턴스. 없으면 기본 프리셋 사용.
        - use_models: 실행할 작업의 부분집합.
        - comments_summary_mode:
             'per_comment'    -> 댓글별 요약
             'per_post_concat'-> 해당 post의 댓글을 합쳐 1회 요약 (권장: 토큰 효율)
        """
        self.realtime = realtime
        self.monitoring = monitoring
        self.save = save
        self.save_dir = save_dir or "./outputs"
        os.makedirs(self.save_dir, exist_ok=True)

        # 사용 작업 검증
        allowed = {"sentiment", "topic", "summary"}
        invalid = set(use_models) - allowed
        if invalid:
            raise ValueError(f"use_models contains invalid tasks: {invalid}")

        # 분석 프리셋 준비
        self.analysis: AnalysisConfig = analysis_config or AnalysisConfig.SENT_CMT_TOPIC_TTL()

        # 모델 이름 override
        if model_names:
            s_name, t_name, sm_name = model_names if len(model_names) == 3 else (None, None, None)
            if s_name:
                self.analysis.sentiment.module.model_name = s_name
            if t_name:
                self.analysis.topic.module.model_name = t_name
            # summary용 모델은 별도의 AnalysisUnit이 없을 수 있으니 sentiment/classifier 기반 중 하나 선택해서 사용하거나 기본값 사용
            # 여기서는 sentiment 모듈을 복사해 요약에 사용(모델명만 교체). 필요 시 별도 SummaryUnit 추가 가능.
            if sm_name:
                # 임시 summary Unit 구성(없으면 sentiment 모듈 사양을 복제)
                base = self.analysis.sentiment.module
                self.summary_module = BaseConfig(
                    model_name=sm_name,
                    finetuned=False,
                    device=base.device,
                    batch_size=base.batch_size,
                    truncation=base.truncation,
                    max_length=base.max_length,
                    return_all_scores=False,
                )
            else:
                self.summary_module = None
        else:
            self.summary_module = None

        # 코멘트 요약 모드
        self.comments_summary_mode = comments_summary_mode

        # 초기화/모델 로드
        self._init_config()
        self._load_models()

    # ----- 내부: 설정 검사/정리 -----
    def _init_config(self):
        # summary 모듈이 없고 use_models에 summary가 포함된 경우, 합리적인 기본값 설정
        if "summary" in self.use_models and self.summary_module is None:
            # 공개 한국어 요약 모델(토큰 불필요) 예: KoBART Summarization
            self.summary_module = BaseConfig(
                model_name="gogamza/kobart-summarization",
                finetuned=False,
                device="cuda" if torch.cuda.is_available() else "cpu",
                batch_size=8,
                truncation=True,
                max_length=256,
            )

        # 활성/타깃 체크: 비활성 유닛은 자동 스킵
        pass  # 필요시 추가 정책 반영

    # ----- 내부: HF 모델 로드 -----
    def _load_models(self):
        self.runners: Dict[Task, BatchCallable] = {}
        if "sentiment" in self.use_models and self.analysis.sentiment.active:
            self.runners["sentiment"] = build_task_callable("sentiment", self.analysis.sentiment.module)
        if "topic" in self.use_models and self.analysis.topic.active:
            self.runners["topic"] = build_task_callable("topic", self.analysis.topic.module)
        if "summary" in self.use_models:
            self.runners["summary"] = build_task_callable("summary", self.summary_module)

    # ----- 퍼블릭: 실행 -----
    def run(self, data: Dict) -> Dict:
        """
        입력 data: 
        {
          "data": [
            {"date": "...", "posts": [{"title": "...", "comments": ["c1","c2",...]}, ...]},
            ...
          ]
        }
        반환: 각 post에 _analyses 추가
        """
        t0 = time.time()

        # sentiment
        if "sentiment" in self.runners:
            self._apply_classification(data, task="sentiment", unit=self.analysis.sentiment)

        # topic
        if "topic" in self.runners:
            self._apply_classification(data, task="topic", unit=self.analysis.topic)

        # summary
        if "summary" in self.runners:
            self._apply_summarization(data, task="summary")

        if self.monitoring:
            n_posts = sum(len(day.get("posts", [])) for day in data.get("data", []))
            print(f"[Inference] done tasks={list(self.runners.keys())} posts={n_posts} time={time.time()-t0:.2f}s")

        if self.save:
            ts = time.strftime("%Y%m%d_%H%M%S")
            out_path = os.path.join(self.save_dir, f"infer_{ts}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            if self.monitoring:
                print(f"[Inference] saved to {out_path}")

        return data

    # ----- 내부: 적용기(분류 공통) -----
    def _apply_classification(self, data: Dict, task: Task, unit: AnalysisUnit):
        """
        sentiment/topic 공통 적용:
        - unit.target에 따라 title, comments 각각 처리
        - 결과를 per-post로 _analyses에 주입
        """
        runner = self.runners[task]
        for target in unit.target:
            if target == "title":
                # 전체 타이틀 모아 추론
                titles = extract_titles(data)
                preds = iter(runner(titles))
                for _, post in iter_posts(data):
                    t = post.get("title")
                    if t is None:
                        continue
                    self._attach(post, key=f"{task}_title", value=next(preds))
            elif target == "comments":
                # 전체 댓글을 평탄화해서 추론, 포스트별로 슬라이싱하여 주입
                all_comments: List[str] = []
                counts: List[int] = []
                for _, post in iter_posts(data):
                    cmt = post.get("comments", [])
                    counts.append(len(cmt))
                    all_comments.extend(cmt)
                if len(all_comments) == 0:
                    continue
                preds_all = iter(runner(all_comments))
                for _, post in iter_posts(data):
                    n = len(post.get("comments", []))
                    if n == 0:
                        self._attach(post, key=f"{task}_comments", value=[])
                        continue
                    per_post = [next(preds_all) for _ in range(n)]
                    self._attach(post, key=f"{task}_comments", value=per_post)
            else:
                raise ValueError(f"Unknown target: {target}")

    # ----- 내부: 적용기(요약) -----
    def _apply_summarization(self, data: Dict, task: Task):
        """
        summary 적용:
        - 타깃은 아래 정책으로 처리
          * title: 각 title 개별 요약
          * comments:
              - per_comment: 댓글 개별 요약
              - per_post_concat: 해당 post의 댓글을 '\n'로 합쳐 1회 요약
        - SummaryUnit이 별도로 없다면 sentiment/topic의 타깃을 참고하지 않고 두 타깃 모두 시도할 수 있음.
          여기선 title, comments 모두 처리.
        """
        runner = self.runners[task]

        # title 요약
        titles = extract_titles(data)
        if titles:
            sums = iter(runner(titles))
            for _, post in iter_posts(data):
                t = post.get("title")
                if t is None:
                    continue
                self._attach(post, key="summary_title", value=next(sums))

        # comments 요약
        if self.comments_summary_mode == "per_comment":
            all_comments: List[str] = []
            for _, post in iter_posts(data):
                all_comments.extend(post.get("comments", []))
            if all_comments:
                sums_all = iter(runner(all_comments))
                for _, post in iter_posts(data):
                    cmts = post.get("comments", [])
                    per_post = [next(sums_all) for _ in range(len(cmts))] if cmts else []
                    self._attach(post, key="summary_comments", value=per_post)
        else:
            # per_post_concat
            concat_texts: List[str] = []
            idx_posts: List[Dict] = []
            for _, post in iter_posts(data):
                cmts = post.get("comments", [])
                if len(cmts) == 0:
                    concat_texts.append("")  # placeholder
                else:
                    concat_texts.append("\n".join(cmts))
                idx_posts.append(post)
            if any(txt for txt in concat_texts):
                sums = iter(runner(concat_texts))
                for post, txt in zip(idx_posts, concat_texts):
                    if txt == "":
                        self._attach(post, key="summary_comments", value="")
                    else:
                        self._attach(post, key="summary_comments", value=next(sums))

    # ----- 내부: 결과 주입 -----
    @staticmethod
    def _attach(post: Dict, key: str, value):
        analyses = post.setdefault("_analyses", {})
        analyses[key] = value


# -------------- 사용 예시 --------------
if __name__ == "__main__":
    # (1) 프리셋 구성 예
    cfg = AnalysisConfig.SENT_CMT_TOPIC_TTL()

    # (2) 파이프라인 생성(모델 오버라이드 없음)
    pipe = InferencePipeLine(
        model_names=None,
        analysis_config=cfg,
        realtime=False,
        monitoring=True,
        save=True,
        save_dir="./outputs",
        use_models=["sentiment", "topic", "summary"],
        comments_summary_mode="per_post_concat",
    )

    # (3) 예제 데이터
    data = {
        "data": [
            {
                "date": "2023-05-01",
                "posts": [
                    {"title": "title1", "comments": ["c1", "c2", "c3"]},
                    {"title": "title2", "comments": ["c4", "c5", "c6"]},
                ],
            },
            {
                "date": "2023-05-02",
                "posts": [
                    {"title": "title3", "comments": ["c7", "c8"]},
                    {"title": "title4", "comments": ["c9", "c10", "c11", "c12"]},
                ],
            },
        ]
    }

    # (4) 실행
    out = pipe.run(data)
    print(json.dumps(out["data"][0]["posts"][0].get("_analyses", {}), ensure_ascii=False, indent=2))

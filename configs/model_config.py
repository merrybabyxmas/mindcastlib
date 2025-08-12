# model_config.py
from __future__ import annotations
import torch
from pydantic import BaseModel, Field, field_validator, ConfigDict


class BaseConfig(BaseModel):
    """
    개별 모델(HF pipeline/자체 모델) 설정 단위.
    - 모델 식별자 및 런타임 파라미터 보관
    - extra='allow'로 -> pipeline 특화 kwargs를 자유롭게 추가 가능
    """
    model_name: str
    finetuned: bool = False
    device: str = Field(default_factory=lambda: "cuda" if torch.cuda.is_available() else "cpu")

    # 추론 공통 파라미터(필요 시 자유롭게 확장)
    batch_size: int = 32
    truncation: bool = True
    max_length: int = 256
    return_all_scores: bool = False

    # 예: tokenizer/model kwargs 등 임의 확장 허용
    model_config = ConfigDict(extra="allow")

    @field_validator("batch_size")
    @classmethod
    def _check_batch_size(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("batch_size must be > 0")
        return v

    @field_validator("max_length")
    @classmethod
    def _check_max_length(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("max_length must be > 0")
        return v


class BaseModuleConfig(BaseModel):

    sentiment_model: BaseConfig
    topic_model: BaseConfig
    classifier_model: BaseConfig

    model_config = ConfigDict(extra="forbid")


class DefaultModuleConfig(BaseModuleConfig):
    """
    토큰 불필요 공개 모델 + 내부 기본값으로 채운 기본 프리셋
    """
    sentiment_model: BaseConfig = BaseConfig(
        model_name="hun3359/klue-bert-base-sentiment",
        finetuned=False,
        batch_size=32,
        truncation=True,
        max_length=256,
        return_all_scores=True,
    )
    topic_model: BaseConfig = BaseConfig(
        model_name="MC_TOPIC_LLFT_0812",   # 필요시 실제 토픽 모델 ID로 교체
        finetuned=True,
        batch_size=32,
        truncation=True,
        max_length=256,
        return_all_scores=False,
    )
    classifier_model: BaseConfig = BaseConfig(
        model_name="MC_SENT_LLFT_0812",    # 예: zero-shot/기본 분류기
        finetuned=False,
        batch_size=32,
        truncation=True,
        max_length=256,
        return_all_scores=False,
    )


class TrainedModuleConfig_V1(BaseModuleConfig):
    """
    직접 학습시킨 가중치로 구성한 프리셋 예시
    """
    sentiment_model: BaseConfig = BaseConfig(
        model_name="MC_SENT_LLFT_0812",    # 로컬 경로 가능: "/path/to/ckpt"
        finetuned=True,
        batch_size=32,
        truncation=True,
        max_length=256,
        return_all_scores=True,
    )
    topic_model: BaseConfig = BaseConfig(
        model_name="MC_TOPIC_LLFT_0812",
        finetuned=True,
        batch_size=32,
        truncation=True,
        max_length=256,
    )
    classifier_model: BaseConfig = BaseConfig(
        model_name="MC_SENT_LLFT_0812",
        finetuned=False,
        batch_size=32,
        truncation=True,
        max_length=256,
    )


if __name__ == "__main__":
    cfg = DefaultModuleConfig()
    print(cfg.model_dump_json(indent=2, exclude_none=True))

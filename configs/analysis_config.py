# analysis_config.py
from __future__ import annotations
from typing import List, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict

from .model_config import (
    BaseConfig,
    DefaultModuleConfig,
    TrainedModuleConfig_V1,
)

Target = Literal["title", "comments"]


class AnalysisUnit(BaseModel):
    active: bool = True
    target: List[Target] = Field(default_factory=lambda: ["title"])
    module: BaseConfig

    model_config = ConfigDict(extra="forbid")

    @field_validator("target")
    @classmethod
    def _validate_target(cls, v: List[Target]) -> List[Target]:
        if not v:
            raise ValueError("target must contain at least one of 'title' or 'comments'")
        # 중복 제거
        v = list(dict.fromkeys(v))
        return v


class AnalysisConfig(BaseModel):
    
    sentiment: AnalysisUnit
    topic: AnalysisUnit
    classifier: AnalysisUnit

    model_config = ConfigDict(extra="forbid")

    # -------- presets(Default)--------
    @classmethod
    def SENT_CMT_TOPIC_TTL(cls) -> "AnalysisConfig":
        mods = DefaultModuleConfig()
        return cls(
            sentiment=AnalysisUnit(active=True, target=["comments"], module=mods.sentiment_model),
            topic=AnalysisUnit(active=False, target=["title"], module=mods.topic_model),
            classifier=AnalysisUnit(active=False, target=["comments"], module=mods.classifier_model),
        )

    @classmethod
    def SENT_TTL_TOPIC_CMT(cls) -> "AnalysisConfig":
        mods = DefaultModuleConfig()
        return cls(
            sentiment=AnalysisUnit(active=True, target=["title"], module=mods.sentiment_model),
            topic=AnalysisUnit(active=True, target=["comments"], module=mods.topic_model),
            classifier=AnalysisUnit(active=True, target=["comments"], module=mods.classifier_model),
        )

    @classmethod
    def SENT_ALL_TOPIC_ALL(cls) -> "AnalysisConfig":
        mods = DefaultModuleConfig()
        both = ["title", "comments"]
        return cls(
            sentiment=AnalysisUnit(active=True, target=both, module=mods.sentiment_model),
            topic=AnalysisUnit(active=True, target=both, module=mods.topic_model),
            classifier=AnalysisUnit(active=False, target=both, module=mods.classifier_model),
        )
    # -------- TODO : presets(후에 finetuned model 프리셋도 추가 )--------


if __name__ == "__main__":
    cfg = AnalysisConfig.SENT_CMT_TOPIC_TTL()
    print(cfg.model_dump_json(indent=2, exclude_none=True))
    for name in cfg.model_fields:                  # 'sentiment', 'topic', 'classifier' 중 하나임.
        unit = getattr(cfg, name)                  # AnalysisUnit 인스턴스
        print(name, unit.active, unit.target)      # 값 출력
        if unit.active:
            print("yes")
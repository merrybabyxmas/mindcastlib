from __future__ import annotations
import os
import json
import time
from typing import List, Dict, Tuple, Literal, Optional 
from dataclasses import dataclass 
import logging
import pprint 

import torch
from transformers import pipeline

from mindcastlib.configs import BaseConfig, AnalysisConfig, AnalysisUnit
from mindcastlib.src import apply_func_to_title, apply_func_to_comments, extract_titles, extract_comments, prepare_data_with_temporal_condition



Target = Literal["title", "comments"]
Task = Literal["sentiment", "topic", "summary"]


@dataclass
class MCPipeSpec:
    task : Literal["sentiment", "topic", "summary"]
    target : Literal["title", "comments"]
    cfg : BaseConfig
    
    
class ModuleCallable:
    HF_TASK_MAPING : Dict[str, str] ={
        "sentiment": "text-classification",
        "topic": "text-classification",
        "summary": "summarization",
    }
    
    
    def __init__(self, spec : MCPipeSpec):
        self.task = spec.task
        self.target = spec.target
        self.cfg = spec.cfg
        
        device_index = 0 if torch.cuda.is_available() else -1

        # pipeline 정의
        self.pipe = pipeline(
            self.HF_TASK_MAPING[self.task],
            model=self.cfg.model_name,    
            device = device_index,    
        )
        
        
    def __call__(self, data: Dict) -> Dict:
        if len(data) == 0:
            return {}
        
        if self.target == "title":
            return apply_func_to_title(func = self.pipe, data = data)
        elif self.target == "comments":
            return apply_func_to_comments(func = self.pipe, data = data)
        
        return data
        
        
def build_task_callable(task: Task, target: Target, cfg: BaseConfig) -> ModuleCallable:
    return ModuleCallable(MCPipeSpec(task=task, target=target, cfg=cfg))
    
class AnalysisPipeLine:
    def __init__(
        self, 
        analysis_config : AnalysisConfig | None = None,
        realtime : bool = False,
        monitoring: bool = True,
        save: bool = True,
        save_dir: str | None = None,
    ):
        self.cfg = analysis_config
        self.realtime = realtime
        self.monitoring = monitoring
        self.save = save
        self.save_dir = save_dir or "./outputs"
        os.makedirs(self.save_dir, exist_ok=True)
        
        
        if self.cfg is None:
            logging.info("No config file detected. 기본 설정 파일로 대체 ")
            self.cfg = AnalysisConfig.SENT_CMT_TOPIC_TTL()
            
            
        self._load_models()
    
    def _load_models(self):
        self.runners: Dict[Task, ModuleCallable] = {}
        self.runners: Dict[str, ModuleCallable] = {}

        if self.cfg.sentiment.active:
            for tgt in self.cfg.sentiment.target:
                key = f"sentiment_{tgt}"
                self.runners[key] = build_task_callable(
                    task="sentiment", target=tgt, cfg=self.cfg.sentiment.module
                )
        else:
            logging.info("sentiment excluded!")

        if self.cfg.topic.active:
            for tgt in self.cfg.topic.target:
                key = f"topic_{tgt}"
                self.runners[key] = build_task_callable(
                    task="topic", target=tgt, cfg=self.cfg.topic.module
                )
        else:
            logging.info("topic excluded!")

        if self.cfg.classifier.active:
            for tgt in self.cfg.classifier.target:
                key = f"classifier_{tgt}"
                self.runners[key] = build_task_callable(
                    task="sentiment",  
                    target=tgt,
                    cfg=self.cfg.classifier.module,  
                )
        else:
            logging.info("classifier excluded!")
        


    def run(self, data:Dict) -> Dict:
        t0 = time.time()
        for key, runner in self.runners.items():
            if self.monitoring:
                logging.info(f"[RUN] executing runner: {key}")
            data = runner(data)
            
        if self.save:
            ts = time.strftime("%Y%m%d_%H%M%S")
            out_path = os.path.join(self.save_dir, f"infer_{ts}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            if self.monitoring:
                logging.info(f"[Inference] saved to {out_path}")

        if self.monitoring:
            logging.info(f"[RUN] done in {time.time() - t0:.2f}s")

        return data
    
    
    
if __name__ == "__main__":

    tc = ["2023-05-01", "2023-05-02"]
    data_dir = "/home/dongwoo38/data/example/ex.json"

    data = prepare_data_with_temporal_condition(tc, data_dir=data_dir)

    pipeline = AnalysisPipeLine(
        analysis_config=AnalysisConfig.SENT_CMT_TOPIC_TTL(),
        realtime=False,
        monitoring=True,
        save=True,
        save_dir="./outputs"
    )

    result = pipeline.run(data)

    pprint.pprint(result)


    

        
            
            
        
        
        



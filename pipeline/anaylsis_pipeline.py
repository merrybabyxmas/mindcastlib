from __future__ import annotations
import os
import json
import time
from typing import List, Dict, Tuple, Literal, Optional 
from dataclasses import dataclass 
import logging

import torch
from transformers import pipeline

from mindcastlib.configs import BaseConfig, AnalysisConfig, AnalysisUnit
from mindcastlib.src import apply_func_to_title, apply_func_to_comments, extract_titles, extract_comments



Target = Literal["title", "comments"]
Task = Literal["sentiment", "topic", "summary"]



@dataclass
class MCPipeSpec:
    task : Literal["sentiment", "topic", "summary"]
    target : Literal["title", "comments"]
    cfg : BaseConfig
    
    
class ModuleCallable:
    def __init__(self, spec : MCPipeSpec):
        self.task = spec.task
        self.target = spec.target
        self.cfg = spec.cfg
        
        # pipeline 정의
        self.pipe = pipeline(
            self.task,
            model=self.cfg.model_name,        
        )
        
        
    def __call__(self, data: Dict) -> Dict:
        if len(data.keys()) == 0:
            return {}
        
        if self.target == "title":
            return apply_func_to_title(func = self.pipe, data = data)
        elif self.target == "comments":
            return apply_func_to_comments(func = self.pipe, data = data)
        
        
def build_task_callable(task:Task, target:Target, cfg : BaseConfig) -> ModuleCallable:
    if task == "sentiment":
        if target == "title":
            return ModuleCallable(
                MCPipeSpec(task="sentiment", target="title", cfg = cfg )
            )
        elif target == "comments":
            return ModuleCallable(
                MCPipeSpec(task="sentiment", target="comments", cfg = cfg)
            )
    elif task == "topic":
        if target == "title":
            return ModuleCallable(
                MCPipeSpec(task="topic", target="title", cfg = cfg )
            )
        elif target == "comments":
            return ModuleCallable(
                MCPipeSpec(task="topic", target="comments", cfg = cfg)
            )
    elif task == "summary":
        if target == "title":
            return ModuleCallable(
                MCPipeSpec(task="summary", target="title", cfg = cfg )
            )
        elif target == "comments":
            return ModuleCallable(
                MCPipeSpec(task="summary", target="comments", cfg = cfg)
            )
    else:
        raise ValueError
    
    
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
        if self.cfg.sentiment.active:
            self.runners["sentiment"] = build_task_callable("sentiment", self.cfg.sentiment.module)
        else:
            logging.info("sentiment excluded!")
            
        if self.cfg.topic.active:
            self.runners["topic"] = build_task_callable("sentiment", self.cfg.sentiment.module)
        else:
            logging.info("topic excluded!")
            
        if self.cfg.classifier.active:
            self.runners["classifier"] = build_task_callable("sentiment", self.cfg.sentiment.module)
        else:
            logging.info("classifier excluded!")
        
    def run(self, data:Dict) -> Dict:
        pass
        
        



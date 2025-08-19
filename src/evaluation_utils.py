import torch 
from mindcastlib.src import LLMPipeLine
from typing import List, Dict, Tuple, Literal


DUMMY_LABEL = Literal["기쁨","슬픔","당황","화남"] #더미 레이블. 이거는 나중에 config에서 임포트 받도록


class EvaluationPipeLine:
    def __init__(self, cfg):
        self.cfg = cfg
    def __call__(self, pred: List[DUMMY_LABEL], true:List[DUMMY_LABEL]) -> None:
        # 둘을 비교 
        
        
        
        pass
        
        
        
        



        
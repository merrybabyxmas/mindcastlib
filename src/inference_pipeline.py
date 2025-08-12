import os 
import Pathlib

import torch
import torch.nn as nn 

from mindcastlib.configs.analysis_config import McBaseConfig, SENT_CMT_TOPIC_TTL_CONFIG
from data_utils import prepare_data

# 모델 로드 

sent_model_name = "MC_SENT_LLFT_0812"
topic_model_name = "MC_TOPIC_LLFT_0812"
classifier_model_name = "MC_CLASSIFIER_SBERT_0812"


cfg = SENT_CMT_TOPIC_TTL_CONFIG



# 파이프라인 정의
pipe = AnalysisPipeLine(
    model_name = (sent_model_name, topic_model_name, classifier_model_name),
    analysis_config = cfg,
    device = "cuda",
    realtime = False,
    monitoring = True,
    save = True, 
    save_dir = "./analysis_results"
)




# 데이터 준비 
timecondition = ["2021-01-01", "2021-03-03"]
data_dir = 'data/example'
data = prepare_data(timecondition, data_dir) # if realtime = True -> tc는 필요없음


# 추론 시작 
pipe(data) # 

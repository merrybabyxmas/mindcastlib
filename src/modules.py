from typing import List, Tuple, Dict

from mindcastlib.configs import SENT_TTL_TOPIC_CMT_CONFIG, AnalysisBaseConfig







sent_model_name = "beomi/KcELECTRA-base-v2022-finetuned-nsmc"
topic_model_name = ""
smry_model_name = ""



sent_model = MCmodel.load_model(
    task = "sentiment_analysis", 
    model_name = sent_model_name
)

topic_model = load_model(
    task = "topic_analysis", 
    model_name = topic_model_name
)


smry_model = load_model(
    task = "news_summarization",
    model_name = smry_model_name
)

cfg = AnalysisBaseConfig.SENT_CMT_TOPIC_TTL()


class InferencePipeLine():
    def __init__(self,
                 model_names : Tuple[str] | None,
                 analysis_config : AnalysisBaseConfig,
                 realtime = False,
                 monitoring = True,
                 save = True,
                 save_dir : str | None = None,
                 use_models = ["sentiment", "topic","summary"]):
        ### if !model_names -> analysis_config 대로 모델 로드 후 추론 진행 
        ### else : model_names에 있는 모델로 config 변경 후 추론 진행 
        self._init_config()
        self._load_models()
        self._
        
        
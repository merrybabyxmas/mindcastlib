from typing import List, Dict, Tuple, Literal, Optional

from mindcastlib.configs import LLMConfig
# transformers, huggingface,,,,
import torch 

class LLMPipeLine():
    def __init__(self, cfg:LLMConfig):
        pass
    def forward(self, data:List[str]) -> List[str]:
        
        # 
        pass 




if __name__ == "__main__":
    cfg_sent = LLMConfig().CLASSIFY_SENTIMENT()
    cfg_topic = LLMConfig().CLASSIFY_TOPIC()
    
    # 예시 출력 -> 여기의 config 활용해서 모델 만들기
    cfg_sent.llm_name = "gpt4o"
    cfg_topic.llm_name = "gpt-opensrc"
    
    print(cfg_sent.model_dump_json(indent=2, exclude_none=True))
    print(cfg_topic.model_dump_json(indent=2, exclude_none=True))
    

    
    ##### 1. 아래 try 문이 작동하도록 코드 짤 것! 
    ##### 2. 위의 llm_name을 바꿔도 잘 작동하도록 할 것 (llm name 은 현재 4개밖에 안댐. llm_config.py 확인할 것)
    ##### 3. List[str] -> List[str] 유지할 것 
    #####
    
    try:
        #예시 데이터 
        sent_data = ["나 슬퍼", "나 화나", "ㅋㅋ너가 뭔데", "든든한 치킨이 너무 먹고 싶다"] # List[str]
        
        # 감정 분류를 위한 LLM Model setting
        pipe = LLMPipeLine(cfg_sent)
        sent_result = pipe(sent_data)
        

        topic_data = ["우리나라 농구 개잘하네", "경제란 무엇일까", "재랑 재랑 연애한대ㄷㄷ"] # List[str]
        
        # 토픽 분류를 위한 LLM Model setting
        pipe = LLMPipeLine(cfg_topic)
        sent_result = pipe(topic_data)
        
    except (ValueError, NotImplementedError) as e:
        raise e
    
    else:
        print(f"나도 ㅁㄹ")
        
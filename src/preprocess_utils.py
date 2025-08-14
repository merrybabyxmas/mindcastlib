import os 
from pathlib import Path
import torch 
from mindcastlib.configs import PreProcessConfig
import pprint
from typing import List, Dict, Tuple
import logging

# ... 여기에 기존에 함수들 채워넣기 


def preprocess_raw_data(cfg:PreProcessConfig, 
                        input_dir: Path | str = None, 
                        save_dir:Path | str = None,
                        save = True,
                        monitoring = True) -> None:
    r"""
    save : 전처리한 데이터를 저장할 것인지 판단. 기본값은 저장하지만 저장공간 혹은 실시간이 필요할 때는 off도 구현 
    monitoring : 전처리 하는데에 소요된 시간 및 저장용량등을 tracking 
    """
    
    ### 1. input_dir에서 데이터를 불러와서
    ### 2. 전처리 후  
    ### 3. save 에 따라 저장 
    
    if save is False:
        logging.info("실시간 모드를 위해 save를 껐습니다.")
        
    if input_dir is None:
        logging.info("no raw data input directory detected! put input_dir")
    
    if save_dir is None and save is True:
        logging.info("No save dir detected. put save dir")





# 예시 실행 
# python -m mindcastlib.src.train_utils

if __name__ == "__main__":
    cfg = PreProcessConfig.DefaultConfig()
    pprint.pprint(cfg.model_dump_json())
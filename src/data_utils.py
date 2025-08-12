# from mindcastlib.configs import SENT_CMT_TOPIC_TTL_CONFIG
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from typing import List, Dict, Tuple, Callable, Any, Iterable
import json
import logging
import pprint

import torch




def prepare_data_with_temporal_condition(
    tc: List[str] | None,
    data : Dict | None = None,
    data_dir: str = None   
    ) -> Dict:
    """
    원하는 time condition의 데이터를 추출 
    
    """
    if tc is None:
        logging.info("Real time Mode : when TC is None")
        return {}  # TODO: 실시간 모드 구현
    else:
        if data is None and data_dir is not None:
            logging.info(f"Load data from {data_dir}")
            with open(data_dir, "r") as f:
                raw_data = json.load(f)
                return filter_data_with_temporal_condition(raw_data, tc)
        elif data is not None and data_dir is None:
            logging.info(f"use given data. not from data directory")
            return filter_data_with_temporal_condition(data, tc)
        elif data is not None and data_dir is not None:
            raise ValueError("데이터와 데이터디렉토리 둘 중 한개만 주어져야 합니다.")
        else:
            raise ValueError("데이터와 데이터 디렉토리 둘 중 최소 한개는 주어져야 합니다. ")
            



def filter_data_with_temporal_condition(data: Dict, tc:List[str]) -> Dict:
    r"데이터가 dict 형식으로 들어왔을 때, tc에 맞춰서  dict 반환"
    start_date, end_date = tc[0], tc[-1]
    return {
        "data": [
            entry for entry in data.get("data", [])
            if start_date <= entry.get("date", "") <= end_date
        ]
        }
            
            
def extract_titles(data: Dict) -> List[str]:
    titles: List[str] = []
    for day in data.get("data", []):
        for post in day.get("posts", []):
            t = post.get("title")
            if t is not None:
                titles.append(t)
    return titles

# 2) 모든 comments를 평탄화해서 리스트로 추출
def extract_comments(data: Dict) -> List[str]:
    comments: List[str] = []
    for day in data.get("data", []):
        for post in day.get("posts", []):
            for c in post.get("comments", []):
                if c is not None:
                    comments.append(c)
    return comments

                
def apply_func_to_title(
    func: Callable | None = None,
    func_name: str | None = None,
    data: Dict | None = None,
    **kwargs
) -> Dict:
    if func is None:
        raise ValueError("you should put Callable model e.g. Sentiment classification Model...")
    if data is None:
        raise ValueError("You should put data!")

    func_name = func_name if func_name is not None else func.__class__.__name__

    titles: List[str] = extract_titles(data)
    func_results_iter = iter(func(titles, **kwargs))

    for day in data.get("data", []):
        for post in day.get("posts", []):
            t = post.get("title")
            if t is not None:
                # 각 post에 결과를 저장
                res = next(func_results_iter)
                analyses = post.setdefault("analyses", {})
                analyses[func_name + "_title"] = res
    return data


def apply_func_to_comments(
    func: Callable | None = None,
    func_name: str | None = None,
    data: Dict | None = None,
    **kwargs
) -> Dict:
    if func is None:
        raise ValueError("you should put Callable model e.g. Sentiment classification Model...")
    if data is None:
        raise ValueError("You should put data!")

    func_name = func_name if func_name is not None else func.__class__.__name__

    # 전체 comment를 한 번에 추출/추론
    all_comments: List[str] = extract_comments(data)
    func_results_iter = iter(func(all_comments, **kwargs))

    for day in data.get("data", []):
        for post in day.get("posts", []):
            comments = post.get("comments", [])
            n = len(comments)
            if n == 0:
                continue
            # 해당 post의 댓글 개수만큼 결과를 떼서 저장
            per_post_results = [next(func_results_iter) for _ in range(n)]

            analyses = post.setdefault("analyses", {})
            analyses[func_name + "_comments"] = per_post_results

    return data
    
    





    
    
if __name__ == "__main__":
    # config import 테스트
    # config = SENT_CMT_TOPIC_TTL_CONFIG()
    # print(config.model_dump_json(indent = 2))
    
    
    # temporal conditon 테스트 
    tc = ["2023-05-01", "2023-05-02"]
    data_dir = "/home/dongwoo38/data/example/ex.json"
    res = prepare_data_with_temporal_condition(tc, data_dir=data_dir)
    # pprint.pprint(res)
    
    print(extract_titles(res))
    print(extract_comments(res))
    
    
    sent_func = HFSentimentFunc(
        model_name="hun3359/klue-bert-base-sentiment",
        device=0 if torch.cuda.is_available() else -1,
        batch_size=32,
        return_all_scores=False,  # True로 하면 모든 라벨 점수 반환
        max_length=256
    )

    # 3) 타이틀/댓글에 적용
    res = _apply_func_to_title(func=sent_func, data=res, func_name="hf_sent")
    res = _apply_func_to_comments(func=sent_func, data=res, func_name="hf_sent")
    pprint.pprint(res)

    
    
    
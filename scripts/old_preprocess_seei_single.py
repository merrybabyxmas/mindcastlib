# preprocess_seei_single.py
import os, json, math
import pandas as pd
from datetime import datetime, timedelta

# ======================================================
# 🔧 고정 경로 설정 (여기만 수정하면 됨)
# ======================================================


CONFIG = "/home/mindcastlib/mindcastlib/configs/suicide/suicide_keyword_ver2.json"

# ======================================================
# Load Config
# ======================================================
with open(CONFIG, "r") as f:
    CFG = json.load(f)

MAIN_TO_SUB = CFG["keywords"]
NEG_EMO = {"분노", "불안", "슬픔", "상처"}


def parse_dt(s):
    return datetime.strptime(s, "%Y-%m-%d")


# ======================================================
# Core SEEI 계산 함수
# ======================================================
def compute_SEEI_from_file(path):
    with open(path, "r") as f:
        data = json.load(f)["data"]

    # 🔥 news_date 기준 자동 window 설정
    all_dates = []
    for block in data:
        for post in block["posts"]:
            all_dates.append(parse_dt(post["news_date"]))

    if len(all_dates) == 0:
        raise ValueError("news_date 없음")

    base_date = min(all_dates)
    win_low = base_date - timedelta(days=3)
    win_high = base_date + timedelta(days=3)

    main_score = {k: 0 for k in MAIN_TO_SUB}
    sub_map = {k: {} for k in MAIN_TO_SUB}

    for block in data:
        for post in block["posts"]:

            t_date = parse_dt(post["news_date"])
            if not (win_low <= t_date <= win_high):
                continue

            analyses = post["analyses"]
            kw_mask = analyses["SuicideDetectionPipeLine_title"][0]["suicide_keyword_mask"]
            sub_mask = analyses["SuicideDetectionPipeLine_title"][0]["suicide_subtag_mask"]

            comments = analyses["SentimentClassificationPipeLine_comments"]
            n = len(comments)
            if n == 0:
                continue

            # 댓글 볼륨 score
            vol = math.log(1 + n)

            # 감정 방향성
            neg = sum(1 for c in comments if c[0]["label"] in NEG_EMO)
            dr = 1 if neg / n >= 0.5 else -1

            # main + subtag
            for mk, subs in MAIN_TO_SUB.items():

                hit = kw_mask.get(mk, False) or any(sub_mask.get(s, False) for s in subs)

                if hit:
                    main_score[mk] += dr * vol

                # 모든 subtag count 기록
                for s in subs:
                    if sub_mask.get(s, False):
                        sub_map[mk][s] = sub_map[mk].get(s, 0) + 1

    return main_score, sub_map


# ======================================================
# 실행 함수
# ======================================================
def run_single(input_path: str, output_path: str): # <-- 여기에 인수를 추가해야 합니다
    print(f"[INFO] Loading JSON → {input_path}")
    main_score, sub_map = compute_SEEI_from_file(input_path)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df = pd.DataFrame([{"file": os.path.basename(input_path), **main_score}])
    df.to_csv(output_path, index=False)

    print(f"[OK] Saved → {output_path}")


if __name__ == "__main__":
    import argparse
    
    # 🔥 커맨드 라인 인수를 처리하도록 수정
    parser = argparse.ArgumentParser(description="Compute SEEI score from a single analysis JSON file.")
    parser.add_argument(
        "--file", 
        type=str, 
        required=True, 
        help="Path to the input analysis JSON file (e.g., infer_*.json)"
    )
    parser.add_argument(
        "--out", 
        type=str, 
        required=True, 
        help="Path to the output CSV file (e.g., /path/to/result.csv)"
    )
    args = parser.parse_args()
    
    # 수정된 run_single 함수 호출
    run_single(input_path=args.file, output_path=args.out)
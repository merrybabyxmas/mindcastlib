import os, json, math
import pandas as pd
from datetime import datetime, timedelta
import argparse

# ======================================================
# 🔧 고정 경로 설정 (CONFIG만 남김)
# ======================================================
CONFIG = "/home/mindcastlib/mindcastlib/configs/suicide/suicide_keyword_ver2.json"
# ======================================================


# ----------------------------
# Config Load
# ----------------------------
with open(CONFIG, "r") as f:
    CFG = json.load(f)

MAIN_TO_SUB = CFG["keywords"]
NEG_EMO = {"분노", "불안", "슬픔", "상처"}


# ----------------------------
# Utility
# ----------------------------
def parse_dt(s):
    return datetime.strptime(s, "%Y-%m-%d")


# ----------------------------
# 개별 파일 SEEI 계산
# ----------------------------
def compute_SEEI_for_file(path, start_dt):

    with open(path, "r") as f:
        data = json.load(f)["data"]

    # 3-day window
    win_low = start_dt - timedelta(days=3)
    win_high = start_dt + timedelta(days=3)

    main_score = {k: 0 for k in MAIN_TO_SUB}

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

            # 볼륨 스코어
            vol = math.log(1 + n)

            # 감정 방향
            neg = sum(1 for c in comments if c[0]["label"] in NEG_EMO)
            dr = 1 if neg / n >= 0.5 else -1

            # main keyword 매칭
            for mk, subs in MAIN_TO_SUB.items():
                hit = kw_mask.get(mk, False) or any(sub_mask.get(s, False) for s in subs)
                if hit:
                    main_score[mk] += dr * vol

    return main_score


# ----------------------------
# 전체 연도 처리 함수 수정
# ----------------------------
def run_all(BASE_ROOT: str, OUTPUT_ROOT: str, YEARS: list[str]):

    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    seei_range_path = f"{OUTPUT_ROOT}/SEEI_range.csv"
    seei_month_path = f"{OUTPUT_ROOT}/SEEI_raw.csv"

    rows = []

    for yy in YEARS:
        YEAR_DIR = f"{BASE_ROOT}/{yy}"
        print(f"\n[PROCESS] Year → {yy}")

        if not os.path.exists(YEAR_DIR):
            print(f"[WARN] Directory not found: {YEAR_DIR}")
            continue

        for mm in sorted(os.listdir(YEAR_DIR)):
            MONTH_DIR = f"{YEAR_DIR}/{mm}"
            if not mm.isdigit() or not os.path.isdir(MONTH_DIR):
                continue

            print(f"   [Month] {yy}-{mm}")

            for rg in sorted(os.listdir(MONTH_DIR)):
                RANGE_DIR = f"{MONTH_DIR}/{rg}"
                if not os.path.isdir(RANGE_DIR):
                    continue

                json_files = [f for f in os.listdir(RANGE_DIR) if f.endswith(".json")]
                
                # 파일이 없는 경우 건너뜁니다.
                if not json_files: 
                    continue 

                # range start = ex: "01-10" → 01
                start_day = rg.split("-")[0]
                start_date = f"{yy}-{mm}-{start_day.zfill(2)}"

                # monthly accumulator
                acc = {mk: 0 for mk in MAIN_TO_SUB}

                for jf in json_files:
                    score = compute_SEEI_for_file(
                        f"{RANGE_DIR}/{jf}",
                        parse_dt(start_date)
                    )
                    for mk in score:
                        acc[mk] += score[mk]

                rows.append({
                    "year": int(yy),
                    "month": int(mm),
                    "range": rg,
                    **acc
                })

    # -----------------------------------------
    # Range 단위 저장
    # -----------------------------------------
    df_range = pd.DataFrame(rows)
    df_range = df_range.sort_values(["year", "month"])
    df_range.to_csv(seei_range_path, index=False)
    print(f"\n[OK] Saved → {seei_range_path}")

    # -----------------------------------------
    # Month 단위 Sum 저장
    # -----------------------------------------
    df_month = df_range.groupby(["year", "month"]).sum(numeric_only=True).reset_index()
    df_month.to_csv(seei_month_path, index=False)
    print(f"[OK] Saved → {seei_month_path}")


if __name__ == "__main__":
    
    # 커맨드 라인 인수를 처리하도록 수정
    parser = argparse.ArgumentParser(description="Compute SEEI score across multiple years/files.")
    parser.add_argument(
        "--root", 
        type=str, 
        required=True, 
        help="Base root directory containing year folders of analysis JSONs."
    )
    parser.add_argument(
        "--out", 
        type=str, 
        required=True, 
        help="Output directory to save the final SEEI CSV files."
    )
    parser.add_argument(
        "--years", 
        nargs='+',  # 여러 개의 인수를 리스트로 받음
        default=["2020", "2021", "2022"], 
        help="List of years to process (e.g., 2020 2021 2022)."
    )
    args = parser.parse_args()
    
    # 수정된 run_all 함수 호출
    run_all(BASE_ROOT=args.root, OUTPUT_ROOT=args.out, YEARS=args.years)
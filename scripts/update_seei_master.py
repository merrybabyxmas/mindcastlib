"""
SEEI Master File Updater (v3 FINAL)
=====================================
- Config JSON의 main keyword 10개만 사용
- Daily 파일에서 누락되는 값은 자동 0 처리
- master.csv + master.json 자동 생성
- 변화율(prev, MoM, YoY) 정상 계산
"""

import os
import json
import pandas as pd
import numpy as np
import argparse
from datetime import datetime


# ======================================================
# CONFIG PATH
# ======================================================
CONFIG = "/home/mindcastlib/mindcastlib/configs/suicide/suicide_keyword_final.json"


# ======================================================
# CONFIG 로드 (메인 키워드 목록)
# ======================================================
def load_main_keywords(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return list(cfg["keywords"].keys())


MAIN_KEYWORDS = load_main_keywords(CONFIG)


# ======================================================
# 일별 CSV 로드
# ======================================================
def load_daily_seei(filepath):
    df = pd.read_csv(filepath)

    date = df["date"].iloc[0]

    # 총합
    total = df[df["metric_type"] == "total"]["value"]
    total_seei = float(total.iloc[0]) if len(total) > 0 else 0.0

    # 키워드 점수 & 비율
    keyword_scores = {}
    keyword_ratios = {}

    score_rows = df[df["metric_type"] == "keyword_score"]
    for _, row in score_rows.iterrows():
        kw = row["metric_name"]
        keyword_scores[kw] = float(row["value"])
        keyword_ratios[kw] = float(row["ratio"]) if not pd.isna(row["ratio"]) else 0.0

    # 키워드 상세 통계
    keyword_stats = {}
    for kw in MAIN_KEYWORDS:
        v_posts = df[(df["metric_type"] == "keyword_posts") & (df["metric_name"] == kw)]
        v_comments = df[(df["metric_type"] == "keyword_comments") & (df["metric_name"] == kw)]
        v_neg = df[(df["metric_type"] == "keyword_neg_ratio") & (df["metric_name"] == kw)]

        keyword_stats[kw] = {
            "posts": float(v_posts["value"].iloc[0]) if len(v_posts) else 0,
            "comments": float(v_comments["value"].iloc[0]) if len(v_comments) else 0,
            "neg_ratio": float(v_neg["value"].iloc[0]) if len(v_neg) else 0.0
        }

    # 감정 분포
    emo_rows = df[df["metric_type"] == "emotion_dist"]
    emotion_dist = dict(zip(emo_rows["metric_name"], emo_rows["value"]))
    emotion_ratios = dict(zip(emo_rows["metric_name"], emo_rows["ratio"]))

    # 전체 통계
    stat_rows = df[df["metric_type"] == "stats"]
    stats = dict(zip(stat_rows["metric_name"], stat_rows["value"]))

    return {
        "date": date,
        "total_seei": total_seei,
        "keyword_scores": keyword_scores,
        "keyword_ratios": keyword_ratios,
        "keyword_stats": keyword_stats,
        "emotion_dist": emotion_dist,
        "emotion_ratios": emotion_ratios,
        "stats": stats
    }


# ======================================================
# Master JSON 생성기
# ======================================================
def build_master_json(df_master):
    records = []

    def safe_int(v):
        try:
            if v is None or (isinstance(v, float) and np.isnan(v)):
                return 0
            return int(v)
        except:
            return 0

    def safe_float(v):
        try:
            if v is None or (isinstance(v, float) and np.isnan(v)):
                return 0.0
            return float(v)
        except:
            return 0.0

    emotion_list = sorted({
        c.replace("emo_", "")
        for c in df_master.columns
        if c.startswith("emo_") and not c.startswith("emo_ratio_")
    })

    for _, row in df_master.iterrows():
        record = {
            "date": str(row["date"]),
            "seei": {
                "total": safe_float(row.get("total_seei"))
            },
            "changes": {
                "prev": {
                    "delta": safe_float(row.get("prev_seei_delta")),
                    "pct": safe_float(row.get("prev_seei_pct")),
                    "direction": row.get("prev_direction", "flat")
                },
                "mom": {
                    "delta": safe_float(row.get("mom_seei_delta")),
                    "pct": safe_float(row.get("mom_seei_pct")),
                    "direction": row.get("mom_direction", "flat")
                },
                    "yoy": {
                        "delta": safe_float(row.get("yoy_seei_delta")),
                        "pct": safe_float(row.get("yoy_seei_pct")),
                        "direction": row.get("yoy_direction", "flat")
                }
            },
            "keywords": [],
            "emotions": [],
            "stats": {
                "posts_with_keyword": safe_int(row.get("stat_total_posts")),
                "comments_with_keyword": safe_int(row.get("stat_total_comments")),
                "neg_ratio_overall": safe_float(row.get("stat_neg_ratio_overall"))
            }
        }

        # 키워드
        for kw in MAIN_KEYWORDS:
            record["keywords"].append({
                "name": kw,
                "score": safe_float(row.get(f"kw_{kw}")),
                "ratio": safe_float(row.get(f"kw_ratio_{kw}")),
                "posts": safe_int(row.get(f"kw_posts_{kw}")),
                "comments": safe_int(row.get(f"kw_comments_{kw}")),
                "neg_ratio": safe_float(row.get(f"kw_negratio_{kw}")),
                "mom_pct": safe_float(row.get(f"kw_{kw}_mom_pct"))
            })

        # 감정값 → safe_int 적용
        for emo in emotion_list:
            record["emotions"].append({
                "name": emo,
                "count": safe_int(row.get(f"emo_{emo}")),
                "ratio": safe_float(row.get(f"emo_ratio_{emo}"))
            })

        records.append(record)

    return records

def save_master_json(df_master, json_path):
    data = build_master_json(df_master)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Master JSON saved → {json_path}")


# ======================================================
# Master CSV 업데이트
# ======================================================
def update_master_file(new_daily_path, master_path):
    print(f"\n[UPDATE] {new_daily_path}")

    daily = load_daily_seei(new_daily_path)
    new_date = daily["date"]

    if os.path.exists(master_path):
        df = pd.read_csv(master_path, parse_dates=["date"])
        if new_date in df["date"].astype(str).values:
            print(f"[SKIP] Exists: {new_date}")
            return df
    else:
        print("[NEW] Creating master file")
        df = pd.DataFrame()

    # 신규 레코드 생성
    rec = {"date": new_date, "total_seei": daily["total_seei"]}

    for kw in MAIN_KEYWORDS:
        rec[f"kw_{kw}"] = daily["keyword_scores"].get(kw, 0.0)
        rec[f"kw_ratio_{kw}"] = daily["keyword_ratios"].get(kw, 0.0)

        rec[f"kw_posts_{kw}"] = daily["keyword_stats"][kw]["posts"]
        rec[f"kw_comments_{kw}"] = daily["keyword_stats"][kw]["comments"]
        rec[f"kw_negratio_{kw}"] = daily["keyword_stats"][kw]["neg_ratio"]

    # 감정
    for emo, cnt in daily["emotion_dist"].items():
        rec[f"emo_{emo}"] = cnt
        rec[f"emo_ratio_{emo}"] = daily["emotion_ratios"][emo]

    # 통계
    for k, v in daily["stats"].items():
        rec[f"stat_{k}"] = v

    df_new = pd.DataFrame([rec])
    df = pd.concat([df, df_new], ignore_index=True)

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # 변화율 계산
    df["prev_seei_delta"] = df["total_seei"].diff()
    df["prev_seei_pct"] = df["total_seei"].pct_change() * 100

    df["mom_seei_delta"] = df["total_seei"].diff(periods=3)
    df["mom_seei_pct"] = df["total_seei"].pct_change(periods=3) * 100

    df["yoy_seei_delta"] = df["total_seei"].diff(periods=36)
    df["yoy_seei_pct"] = df["total_seei"].pct_change(periods=36) * 100

    df = df.replace([np.inf, -np.inf], np.nan)

    df["prev_direction"] = df["prev_seei_delta"].apply(lambda x: "up" if x > 0 else "down" if x < 0 else "flat")
    df["mom_direction"] = df["mom_seei_delta"].apply(lambda x: "up" if x > 0 else "down" if x < 0 else "flat")
    df["yoy_direction"] = df["yoy_seei_delta"].apply(lambda x: "up" if x > 0 else "down" if x < 0 else "flat")

    for kw in MAIN_KEYWORDS:
        col = f"kw_{kw}"
        df[f"{col}_mom_pct"] = df[col].pct_change(periods=3) * 100
        df[f"{col}_mom_pct"] = df[f"{col}_mom_pct"].replace([np.inf, -np.inf], np.nan)

    # 저장
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df.to_csv(master_path, index=False, encoding="utf-8-sig")

    print(f"[OK] Master CSV updated → {master_path}")

    return df


# ======================================================
# Batch 처리
# ======================================================
def batch_update_master(daily_dir, master_path):
    print("=" * 60)
    print("SEEI MASTER UPDATE (v3 FINAL)")
    print("=" * 60)

    csv_files = sorted([f for f in os.listdir(daily_dir) if f.startswith("seei_") and f.endswith(".csv")])

    df_master = None
    for i, f in enumerate(csv_files, 1):
        print(f"[{i}/{len(csv_files)}] {f}")
        df_master = update_master_file(os.path.join(daily_dir, f), master_path)

    # JSON 저장
    json_out = master_path.replace(".csv", ".json")
    save_master_json(df_master, json_out)

    print("\n[DONE] Batch update completed")
    return df_master


# ======================================================
# MAIN
# ======================================================
def main():
    parser = argparse.ArgumentParser(description="SEEI Master Updater (v3 FINAL)")
    subparsers = parser.add_subparsers(dest="command")

    pb = subparsers.add_parser("batch")
    pb.add_argument("--daily_dir", required=True)
    pb.add_argument("--master", required=True)

    args = parser.parse_args()

    if args.command == "batch":
        batch_update_master(args.daily_dir, args.master)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

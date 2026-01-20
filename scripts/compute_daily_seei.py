"""
일별 SEEI 계산 및 파일 생성
================================
Input: 일별 감정 분석 JSON 파일
Output: seei_YYYYMMDD.csv (일별 상세 정보)

생성 정보:
1. 키워드별 지수
2. 총합 지수  
3. 키워드별 비율
4. 감정 분포
"""

import os
import json
import math
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter
import argparse


# ======================================================
# 설정
# ======================================================
CONFIG = "/home/mindcastlib/mindcastlib/configs/suicide/suicide_keyword_final.json"
NEG_EMO = {"분노", "불안", "슬픔", "상처"}


# ======================================================
# Config Load
# ======================================================
def load_config():
    with open(CONFIG, "r") as f:
        cfg = json.load(f)
    return cfg["keywords"]


# ======================================================
# 유틸리티
# ======================================================
def parse_dt(s):
    """날짜 파싱"""
    return datetime.strptime(s, "%Y-%m-%d")


def format_date_for_filename(dt):
    """날짜를 파일명 형식으로 변환: seei_YYYYMMDD"""
    return dt.strftime("seei_%Y%m%d")


# ======================================================
# 핵심: 일별 SEEI 계산
# ======================================================
def compute_daily_seei(json_path, main_to_sub):
    """
    일별 JSON 파일로부터 SEEI 계산
    ⚠️ 키워드가 있는 포스트만 집계!
    
    Returns:
    --------
    dict with keys:
        - date: 기준 날짜
        - keyword_scores: {keyword: score}
        - keyword_stats: {keyword: {posts, comments, neg_ratio}}
        - total_seei: 총합 지수
        - keyword_ratios: {keyword: 비율}
        - emotion_dist: {emotion: count}
        - emotion_ratios: {emotion: 비율}
        - stats: 전체 통계 (키워드 있는 것만)
    """
    
    with open(json_path, "r") as f:
        json_data = json.load(f)
    
    data = json_data["data"]
    
    # ===== 1. 날짜 추출 (JSON 최상위 date 필드) =====
    if len(data) == 0:
        raise ValueError(f"No data blocks found in {json_path}")
    
    date_str = data[0]["date"]
    base_date = datetime.strptime(date_str, "%Y-%m-%d")
    
    # ±3일 윈도우
    win_low = base_date - timedelta(days=3)
    win_high = base_date + timedelta(days=3)
    
    # ===== 2. 초기화 =====
    keyword_scores = {k: 0.0 for k in main_to_sub}
    keyword_stats = {
        k: {
            "posts": 0,
            "comments": 0,
            "neg_comments": 0,
            "neg_ratio": 0.0
        } 
        for k in main_to_sub
    }
    
    emotion_counter = Counter()
    
    # 전체 통계 (키워드 있는 것만)
    total_posts_with_keyword = 0
    total_comments_with_keyword = 0
    total_neg_comments_with_keyword = 0
    
    # ===== 3. 점수 계산 (키워드 있는 것만!) =====
    for block in data:
        for post in block["posts"]:
            t_date = parse_dt(post["news_date"])
            
            # 윈도우 체크
            if not (win_low <= t_date <= win_high):
                continue
            
            analyses = post["analyses"]
            kw_mask = analyses["SuicideDetectionPipeLine_title"][0]["suicide_keyword_mask"]
            sub_mask = analyses["SuicideDetectionPipeLine_title"][0]["suicide_subtag_mask"]
            comments = analyses["SentimentClassificationPipeLine_comments"]
            
            n = len(comments)
            if n == 0:
                continue
            
            # 댓글 볼륨
            vol = math.log(1 + n)
            
            # 부정 비율 계산
            neg_count = sum(1 for c in comments if c[0]["label"] in NEG_EMO)
            neg_ratio = neg_count / n
            
            # Direction: 부정 50% 이상이면 +1, 미만이면 -1
            direction = 1 if neg_ratio >= 0.5 else -1
            
            # 키워드 매칭 체크 (어떤 키워드들이 매칭되는지 확인)
            matched_keywords = []
            for main_kw, sub_kws in main_to_sub.items():
                hit = kw_mask.get(main_kw, False) or any(
                    sub_mask.get(s, False) for s in sub_kws
                )
                
                if hit:
                    matched_keywords.append(main_kw)
                    
                    # SEEI 공식: direction × neg_ratio × log(1 + comments)
                    score = direction * neg_ratio * vol
                    keyword_scores[main_kw] += score
                    
                    # 키워드별 통계
                    keyword_stats[main_kw]["posts"] += 1
                    keyword_stats[main_kw]["comments"] += n
                    keyword_stats[main_kw]["neg_comments"] += neg_count
            
            # 키워드가 하나라도 있는 포스트만 전체 통계에 포함 ⭐
            if matched_keywords:
                total_posts_with_keyword += 1
                total_comments_with_keyword += n
                total_neg_comments_with_keyword += neg_count
                
                # 감정 분포 카운트 (키워드 있는 포스트만!)
                for c in comments:
                    emotion = c[0]["label"]
                    emotion_counter[emotion] += 1
    
    # ===== 4. 키워드별 neg_ratio 계산 =====
    for kw, stats in keyword_stats.items():
        if stats["comments"] > 0:
            stats["neg_ratio"] = (stats["neg_comments"] / stats["comments"]) * 100
        else:
            stats["neg_ratio"] = 0.0
    
    # ===== 5. 총합 및 비율 계산 =====
    total_seei = sum(keyword_scores.values())
    
    # 키워드별 비율 (절댓값 기준)
    abs_sum = sum(abs(v) for v in keyword_scores.values())
    keyword_ratios = {
        k: (abs(v) / abs_sum * 100) if abs_sum > 0 else 0.0
        for k, v in keyword_scores.items()
    }
    
    # 감정별 비율
    total_emotions = sum(emotion_counter.values())
    emotion_ratios = {
        emo: (cnt / total_emotions * 100) if total_emotions > 0 else 0.0
        for emo, cnt in emotion_counter.items()
    }
    
    # ===== 6. 결과 반환 =====
    return {
        "date": base_date.strftime("%Y-%m-%d"),
        "keyword_scores": keyword_scores,
        "keyword_stats": keyword_stats,  # 추가! ⭐
        "total_seei": total_seei,
        "keyword_ratios": keyword_ratios,
        "emotion_dist": dict(emotion_counter),
        "emotion_ratios": emotion_ratios,
        "stats": {
            "total_posts": total_posts_with_keyword,  # 키워드 있는 것만!
            "total_comments": total_comments_with_keyword,  # 키워드 있는 것만!
            "total_neg_comments": total_neg_comments_with_keyword,  # 키워드 있는 것만!
            "neg_ratio_overall": (total_neg_comments_with_keyword / total_comments_with_keyword * 100) 
                                if total_comments_with_keyword > 0 else 0.0
        }
    }


# ======================================================
# CSV 파일 생성
# ======================================================
def save_daily_seei_csv(result, output_dir):
    """
    일별 SEEI 결과를 CSV로 저장
    
    파일명: seei_YYYYMMDD.csv
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    date_obj = datetime.strptime(result["date"], "%Y-%m-%d")
    filename = format_date_for_filename(date_obj) + ".csv"
    filepath = os.path.join(output_dir, filename)
    
    # ===== 데이터 구조화 =====
    rows = []
    
    # Row 1: 총합 정보
    row_total = {
        "metric_type": "total",
        "metric_name": "SEEI_TOTAL",
        "value": result["total_seei"],
        "ratio": 100.0,
        "date": result["date"]
    }
    rows.append(row_total)
    
    # Row 2~N: 키워드별 점수 및 비율
    for kw, score in result["keyword_scores"].items():
        row_kw = {
            "metric_type": "keyword_score",
            "metric_name": kw,
            "value": score,
            "ratio": result["keyword_ratios"][kw],
            "date": result["date"]
        }
        rows.append(row_kw)
    
    # 키워드별 상세 통계 추가 ⭐
    for kw, stats in result["keyword_stats"].items():
        # Posts
        rows.append({
            "metric_type": "keyword_posts",
            "metric_name": kw,
            "value": stats["posts"],
            "ratio": None,
            "date": result["date"]
        })
        # Comments
        rows.append({
            "metric_type": "keyword_comments",
            "metric_name": kw,
            "value": stats["comments"],
            "ratio": None,
            "date": result["date"]
        })
        # Neg Ratio
        rows.append({
            "metric_type": "keyword_neg_ratio",
            "metric_name": kw,
            "value": stats["neg_ratio"],
            "ratio": None,
            "date": result["date"]
        })
    
    # Row N+1~M: 감정별 분포
    for emo, count in result["emotion_dist"].items():
        row_emo = {
            "metric_type": "emotion_dist",
            "metric_name": emo,
            "value": count,
            "ratio": result["emotion_ratios"][emo],
            "date": result["date"]
        }
        rows.append(row_emo)
    
    # Row M+1: 통계 정보
    stats = result["stats"]
    for stat_name, stat_val in stats.items():
        row_stat = {
            "metric_type": "stats",
            "metric_name": stat_name,
            "value": stat_val,
            "ratio": None,
            "date": result["date"]
        }
        rows.append(row_stat)
    
    # ===== DataFrame 저장 =====
    df = pd.DataFrame(rows)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    
    return filepath


# ======================================================
# JSON 파일 생성 (UI/UX용) ⭐
# ======================================================
def save_daily_seei_json(result, output_dir):
    """
    일별 SEEI 결과를 JSON으로 저장 (프론트엔드 친화적)
    
    파일명: seei_YYYYMMDD.json
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    date_obj = datetime.strptime(result["date"], "%Y-%m-%d")
    filename = format_date_for_filename(date_obj) + ".json"
    filepath = os.path.join(output_dir, filename)
    
    # 구조화된 JSON 생성
    output = {
        "date": result["date"],
        "seei": {
            "total": result["total_seei"],
            "keywords": [
                {
                    "name": kw,
                    "score": result["keyword_scores"][kw],
                    "ratio": result["keyword_ratios"][kw],
                    "posts": result["keyword_stats"][kw]["posts"],
                    "comments": result["keyword_stats"][kw]["comments"],
                    "neg_ratio": result["keyword_stats"][kw]["neg_ratio"]
                }
                for kw in result["keyword_scores"].keys()
            ]
        },
        "emotions": {
            "distribution": [
                {
                    "name": emo,
                    "count": count,
                    "ratio": result["emotion_ratios"][emo]
                }
                for emo, count in result["emotion_dist"].items()
            ]
        },
        "stats": {
            "posts_with_keyword": result["stats"]["total_posts"],
            "comments_with_keyword": result["stats"]["total_comments"],
            "neg_comments": result["stats"]["total_neg_comments"],
            "neg_ratio_overall": result["stats"]["neg_ratio_overall"]
        }
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    return filepath


# ======================================================
# 통합 저장 (CSV + JSON)
# ======================================================
def save_daily_seei(result, output_dir):
    """
    일별 SEEI 결과를 CSV와 JSON 두 가지 형식으로 저장
    """
    
    csv_path = save_daily_seei_csv(result, output_dir)
    json_path = save_daily_seei_json(result, output_dir)
    
    stats = result["stats"]
    
    print(f"[OK] Daily SEEI saved")
    print(f"     Date: {result['date']}")
    print(f"     Total SEEI: {result['total_seei']:.2f}")
    print(f"     Posts (w/ keyword): {stats['total_posts']}")
    print(f"     Comments (w/ keyword): {stats['total_comments']}")
    print(f"     Neg Ratio: {stats['neg_ratio_overall']:.1f}%")
    print(f"     CSV: {csv_path}")
    print(f"     JSON: {json_path}")
    
    return csv_path, json_path


# ======================================================
# 실행
# ======================================================
def main():
    parser = argparse.ArgumentParser(
        description="일별 SEEI 계산 및 파일 생성"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="입력 JSON 파일 경로 (예: infer_20200101.json)"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="출력 디렉토리 (예: /path/to/daily_seei/)"
    )
    
    args = parser.parse_args()
    
    # Config 로드
    main_to_sub = load_config()
    
    # SEEI 계산
    print(f"\n[START] Computing daily SEEI")
    print(f"  Input: {args.input}")
    result = compute_daily_seei(args.input, main_to_sub)
    
    # 파일 저장
    save_daily_seei(result, args.output_dir)
    
    print(f"\n[DONE] Daily SEEI computation completed\n")


if __name__ == "__main__":
    main()
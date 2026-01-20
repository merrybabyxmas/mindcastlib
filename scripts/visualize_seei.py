import os
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats
from statsmodels.tsa.stattools import grangercausalitytests

plt.rcParams["font.family"] = "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False


# ======================================================================
# 1. MASTER JSON → RANGE-LEVEL DATAFRAME
# ======================================================================
def load_master_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []

    for entry in data:
        base = {
            "date": pd.to_datetime(entry["date"]),
            "total_seei": entry["seei"]["total"],
            "neg_ratio_overall": entry["stats"]["neg_ratio_overall"],
            "posts": entry["stats"]["posts_with_keyword"],
            "comments": entry["stats"]["comments_with_keyword"],
        }

        # Keywords
        for kw in entry["keywords"]:
            name = kw["name"]
            base[f"kw_{name}"] = kw["score"]
            base[f"kw_ratio_{name}"] = kw["ratio"]
            base[f"kw_posts_{name}"] = kw["posts"]
            base[f"kw_comments_{name}"] = kw["comments"]
            base[f"kw_neg_{name}"] = kw["neg_ratio"]

        # Emotions
        for emo in entry["emotions"]:
            base[f"emo_{emo['name']}"] = emo["ratio"]

        rows.append(base)

    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    return df


# ======================================================================
# 2. MONTHLY SUM/WEIGHTED AVERAGE CONVERSION
# ======================================================================
def convert_monthly(df):
    df["month"] = df["date"].dt.to_period("M")

    # sum 대상
    sum_cols = [c for c in df.columns if c.startswith("kw_") and "ratio" not in c and "neg" not in c]
    sum_cols += ["total_seei", "posts", "comments"]

    # weighted avg 대상
    ratio_cols = [c for c in df.columns if "ratio" in c or "neg_" in c or c.startswith("emo_")]

    # Sum
    monthly_sum = df.groupby("month")[sum_cols].sum()

    # Weighted average
    def wavg(group):
        w = group["comments"]
        out = {}
        for col in ratio_cols:
            if w.sum() == 0:
                out[col] = group[col].mean()
            else:
                out[col] = (group[col] * w).sum() / w.sum()
        return pd.Series(out)

    monthly_ratio = df.groupby("month").apply(wavg)

    monthly = pd.concat([monthly_sum, monthly_ratio], axis=1)
    monthly = monthly.reset_index()
    monthly["month"] = monthly["month"].dt.to_timestamp()

    return monthly


# ======================================================================
# 3. RANGE-LEVEL VISUALIZATION
# ======================================================================
def plot_range_level(df, outdir):
    os.makedirs(outdir, exist_ok=True)

    # 변화율 계산
    df["delta"] = df["total_seei"].diff()
    df["direction"] = df["delta"].apply(lambda x: "up" if x > 0 else ("down" if x < 0 else "flat"))

    # ---- (1) 변화율 ----
    plt.figure(figsize=(14, 6))
    plt.plot(df["date"], df["total_seei"], marker="o")
    for i, row in df.iterrows():
        if row["direction"] == "up":
            plt.scatter(row["date"], row["total_seei"], color="red", marker="^", s=80)
        elif row["direction"] == "down":
            plt.scatter(row["date"], row["total_seei"], color="blue", marker="v", s=80)
    plt.title("Range-level SEEI Trend")
    plt.grid(True)
    plt.savefig(f"{outdir}/range_seei_trend.png", dpi=300)
    plt.close()

    # ---- (2) Neg emotion ratio ----
    plt.figure(figsize=(14, 5))
    plt.plot(df["date"], df["neg_ratio_overall"], color="red")
    plt.title("Negative Emotion Ratio (Range-level)")
    plt.grid(True)
    plt.savefig(f"{outdir}/range_negative_ratio.png", dpi=300)
    plt.close()

    # ---- (3) Keyword ratios (stacked) ----
    kw_ratio_cols = [c for c in df.columns if c.startswith("kw_ratio_")]
    if kw_ratio_cols:
        plt.figure(figsize=(14, 6))
        plt.stackplot(df["date"], [df[c] for c in kw_ratio_cols], labels=kw_ratio_cols)
        plt.legend(loc="upper left", bbox_to_anchor=(1, 1))
        plt.title("Keyword Ratio Composition (Range-level)")
        plt.savefig(f"{outdir}/range_keyword_ratio.png", dpi=300)
        plt.close()


def plot_keyword_small_multiples(df, outdir):
    os.makedirs(outdir, exist_ok=True)

    kw_cols = [c for c in df.columns if c.startswith("kw_ratio_")]
    keywords = [c.replace("kw_ratio_", "") for c in kw_cols]

    rows, cols = 5, 2  # 10개 키워드 기준
    fig, axes = plt.subplots(rows, cols, figsize=(16, 20), sharex=True)
    axes = axes.flatten()

    for i, kw in enumerate(keywords):
        ax = axes[i]
        col = f"kw_ratio_{kw}"
        ax.plot(df["date"], df[col], linewidth=1.5)
        ax.set_title(kw, fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, max(df[col].max(), 1))

    for j in range(len(keywords), len(axes)):
        axes[j].axis("off")

    plt.tight_layout()
    plt.savefig(f"{outdir}/keyword_small_multiples.png", dpi=300)
    plt.close()


def plot_emotion_small_multiples(df, outdir):
    os.makedirs(outdir, exist_ok=True)

    emo_cols = [c for c in df.columns if c.startswith("emo_")]
    emotions = [c.replace("emo_", "") for c in emo_cols]

    rows, cols = 2, 3  # 6개 감정 기준
    fig, axes = plt.subplots(rows, cols, figsize=(16, 10), sharex=True)
    axes = axes.flatten()

    for i, emo in enumerate(emotions):
        ax = axes[i]
        col = f"emo_{emo}"
        ax.plot(df["date"], df[col], linewidth=1.5, color="purple")
        ax.set_title(emo, fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, max(df[col].max(), 1))

    for j in range(len(emotions), len(axes)):
        axes[j].axis("off")

    plt.tight_layout()
    plt.savefig(f"{outdir}/emotion_small_multiples.png", dpi=300)
    plt.close()


# ======================================================================
# 4. MONTHLY DUAL-AXIS (BASIC)
# ======================================================================
def plot_monthly_dual(df_m, df_su, outdir):
    os.makedirs(outdir, exist_ok=True)

    # CSV의 날짜 컬럼명은 "날짜"
    df = pd.merge(df_m, df_su, left_on="month", right_on="날짜", how="inner")

    plt.figure(figsize=(14, 6))
    ax1 = plt.gca()
    ax2 = ax1.twinx()

    ax1.plot(df["month"], df["total_seei"], color="blue", marker="o", label="SEEI")
    ax2.plot(df["month"], df["자살사망자수"], color="red", marker="s", label="Suicide")

    ax1.set_ylabel("SEEI", color="blue")
    ax2.set_ylabel("Suicide Deaths", color="red")
    plt.title("Monthly SEEI vs Suicide Deaths")

    plt.savefig(f"{outdir}/monthly_dual_axis.png", dpi=300)
    plt.close()


# ======================================================================
# 5. MONTHLY DUAL-AXIS WITH CUSTOM LAG (개선된 버전)
# ======================================================================
def plot_monthly_dual_with_lag(df_m, df_su, outdir, lag=0):
    """
    월별 SEEI vs 자살사망자수 Dual-Axis Plot (Custom Lag 지원)
    
    Parameters:
    -----------
    df_m : DataFrame
        월별 SEEI 데이터 (month, total_seei 포함)
    df_su : DataFrame
        월별 자살 데이터 (날짜, 자살사망자수 포함)
    outdir : str
        출력 디렉토리
    lag : int
        적용할 lag (음수: SEEI 선행, 양수: 자살 선행, 0: 동시)
        예: lag=-3 → SEEI가 3개월 선행
    
    Description:
    ------------
    같은 시간 범위(X축)에서 SEEI를 lag만큼 shift하여
    선행지표 관계를 명확하게 시각화합니다.
    
    lag < 0: SEEI를 미래로 shift → SEEI가 선행
    lag > 0: SEEI를 과거로 shift → 자살이 선행
    lag = 0: shift 없음 → 동시 비교
    """
    os.makedirs(outdir, exist_ok=True)

    # 병합
    df = pd.merge(df_m, df_su, left_on="month", right_on="날짜", how="inner")
    df = df.sort_values("month").reset_index(drop=True)

    # SEEI를 lag만큼 shift
    # lag < 0: SEEI를 미래로 shift (선행)
    # lag > 0: SEEI를 과거로 shift (후행)
    seei_shifted = df["total_seei"].shift(-lag)
    
    # 유효한 데이터만 (NaN 제거)
    valid_mask = seei_shifted.notna()
    dates = df["month"]

    # Dual-Axis Plot
    fig, ax1 = plt.subplots(figsize=(14, 7))
    ax2 = ax1.twinx()

    # SEEI (shifted) - 파란색
    ax1.plot(dates[valid_mask], seei_shifted[valid_mask], 
            color="#2E86AB", marker="o", markersize=6, linewidth=2.5,
            label=f"SEEI (shifted by {lag} months)", zorder=2)
    ax1.set_ylabel("SEEI (shifted)", color="#2E86AB", fontsize=12, fontweight="bold")
    ax1.tick_params(axis="y", labelcolor="#2E86AB")
    ax1.grid(True, alpha=0.3, zorder=1)

    # Suicide (original) - 빨간색
    ax2.plot(dates, df["자살사망자수"], 
            color="#E63946", marker="s", markersize=6, linewidth=2.5, alpha=0.7,
            label="Suicide Deaths (original)", zorder=2)
    ax2.set_ylabel("Suicide Deaths (original)", color="#E63946", fontsize=12, fontweight="bold")
    ax2.tick_params(axis="y", labelcolor="#E63946")

    # 제목 생성
    if lag < 0:
        title = f"SEEI Leading by {abs(lag)} months (Lag = {lag})"
        subtitle = "SEEI values are shifted forward to show leading relationship"
    elif lag > 0:
        title = f"Suicide Leading by {lag} months (Lag = {lag})"
        subtitle = "SEEI values are shifted backward"
    else:
        title = "No Lag Applied (Lag = 0)"
        subtitle = "Simultaneous comparison"

    ax1.set_title(f"{title}\n{subtitle}", fontsize=14, fontweight="bold", pad=20)
    ax1.set_xlabel("Date", fontsize=12, fontweight="bold")

    # X축 포맷
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # 범례
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=10)
    """
    # 상관계수 계산 (shifted 데이터 기준)
    if valid_mask.sum() > 2:
        corr, p_value = stats.pearsonr(seei_shifted[valid_mask], 
                                        df["자살사망자수"][valid_mask])

        # 통계 정보 텍스트 박스
        textstr = f"Correlation (with lag):\n"
        textstr += f"  r = {corr:.3f}\n"
        textstr += f"  p = {p_value:.4f}\n"
        textstr += f"  n = {valid_mask.sum()}"

        props = dict(boxstyle="round", facecolor="wheat", alpha=0.8)
        ax1.text(0.02, 0.98, textstr, transform=ax1.transAxes, fontsize=11,
                verticalalignment="top", bbox=props, fontfamily="monospace")
    else:
        corr, p_value = np.nan, np.nan
    """
    plt.tight_layout()

    # 파일명에 lag 포함
    filename = f"monthly_dual_axis_lag{lag:+d}.png"
    output_path = f"{outdir}/{filename}"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    if not np.isnan(corr):
        print(f"  [LAG {lag:+d}] Correlation: r={corr:.3f}, p={p_value:.4f} → {output_path}")
    else:
        print(f"  [LAG {lag:+d}] Insufficient data → {output_path}")

    return output_path


# ======================================================================
# 6. MONTHLY TREND
# ======================================================================
def plot_monthly_trend(df_m, outdir):
    os.makedirs(outdir, exist_ok=True)

    df = df_m.copy()
    df["delta"] = df["total_seei"].diff()
    df["direction"] = df["delta"].apply(lambda x: "up" if x > 0 else ("down" if x < 0 else "flat"))

    plt.figure(figsize=(14, 6))
    plt.plot(df["month"], df["total_seei"], marker="o", label="SEEI")

    for i, row in df.iterrows():
        if row["direction"] == "up":
            plt.scatter(row["month"], row["total_seei"], color="red", marker="^", s=90)
        elif row["direction"] == "down":
            plt.scatter(row["month"], row["total_seei"], color="blue", marker="v", s=90)

    plt.title("Monthly SEEI Trend (with Up/Down)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{outdir}/monthly_seei_trend.png", dpi=300)
    plt.close()


# ======================================================================
# 7. LEADING INDICATOR ANALYSIS
# ======================================================================
def analyze_leading(df_m, df_su, outdir):
    os.makedirs(outdir, exist_ok=True)

    df = pd.merge(df_m, df_su, left_on="month", right_on="날짜", how="inner")

    results = {}

    # ============ 1. Correlation ============
    r, p = stats.pearsonr(df["total_seei"], df["자살사망자수"])
    results["correlation"] = {"pearson_r": float(r), "p_value": float(p)}

    # ============ Scatter Plot ============
    plt.figure(figsize=(8, 6))
    plt.scatter(df["total_seei"], df["자살사망자수"], alpha=0.7)

    z = np.polyfit(df["total_seei"], df["자살사망자수"], 1)
    pfit = np.poly1d(z)
    plt.plot(df["total_seei"], pfit(df["total_seei"]), "r--")

    plt.title(f"Correlation Scatter Plot (r={r:.3f}, p={p:.4f})")
    plt.xlabel("SEEI")
    plt.ylabel("Suicide Deaths")
    plt.grid(True)
    plt.savefig(f"{outdir}/scatter_correlation.png", dpi=300)
    plt.close()

    # ============ 2. Cross-Correlation ============
    max_lag = 6
    lags = []
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            x = df["total_seei"][:lag]
            y = df["자살사망자수"][-lag:]
        elif lag > 0:
            x = df["total_seei"][lag:]
            y = df["자살사망자수"][:-lag]
        else:
            x = df["total_seei"]
            y = df["자살사망자수"]

        if len(x) > 2:
            corr = np.corrcoef(x, y)[0, 1]
            lags.append((int(lag), float(corr)))

    lag_df = pd.DataFrame(lags, columns=["lag", "correlation"])
    best_lag_row = lag_df.iloc[lag_df["correlation"].abs().idxmax()]

    results["cross_correlation"] = {
        "best_lag": int(best_lag_row["lag"]),
        "correlation": float(best_lag_row["correlation"]),
    }

    # ---- 그래프 ----
    plt.figure(figsize=(10, 5))
    plt.bar(lag_df["lag"], lag_df["correlation"], color="skyblue")
    plt.axvline(best_lag_row["lag"], color="red", linestyle="--")
    plt.title("Cross-Correlation (Lag Analysis)")
    plt.xlabel("Lag (months)")
    plt.ylabel("Correlation")
    plt.grid(True)
    plt.savefig(f"{outdir}/cross_correlation.png", dpi=300)
    plt.close()

    # ============ 3. Granger Causality ============
    try:
        gc = grangercausalitytests(
            df[["자살사망자수", "total_seei"]],
            maxlag=4,
            verbose=False
        )
        # numpy.int64 → int 변환
        pvals = {int(lag): float(gc[lag][0]["ssr_ftest"][1]) for lag in gc}
        results["granger"] = pvals

        # ---- 그래프 ----
        plt.figure(figsize=(8, 5))
        plt.bar(pvals.keys(), pvals.values(), color="orange")
        plt.axhline(0.05, color="red", linestyle="--", label="p=0.05")
        plt.title("Granger Causality p-values")
        plt.xlabel("Lag")
        plt.ylabel("p-value")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{outdir}/granger_pvalues.png", dpi=300)
        plt.close()

    except Exception as e:
        results["granger"] = f"ERROR: {str(e)}"

    # ============ Save JSON ============
    with open(f"{outdir}/leading_analysis.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return results


# ======================================================================
# 8. MAIN
# ======================================================================
def main():
    parser = argparse.ArgumentParser(description="SEEI 시각화 (Custom Lag 지원)")
    parser.add_argument("--master_json", required=True, help="SEEI Master JSON 파일")
    parser.add_argument("--suicide_csv", required=True, help="자살 사망자 CSV 파일")
    parser.add_argument("--output_dir", required=True, help="출력 디렉토리")
    parser.add_argument("--lags", type=str, default=None, 
                       help="Custom lag 값들 (쉼표 구분, 예: -6,-5,-4,-3,-2,-1,0,1,2,3)")
    
    args = parser.parse_args()

    print("="*70)
    print("SEEI Visualization with Custom Lag Support")
    print("="*70)
    print()

    # 데이터 로드
    print("Loading data...")
    df_range = load_master_json(args.master_json)
    df_month = convert_monthly(df_range)
    df_su = pd.read_csv(args.suicide_csv, parse_dates=["날짜"])
    print(f"  Range-level records: {len(df_range)}")
    print(f"  Monthly records: {len(df_month)}")
    print(f"  Suicide records: {len(df_su)}")
    print()

    # ---------------- RANGE LEVEL ----------------
    print("[1/3] Range-level visualizations...")
    plot_range_level(df_range, f"{args.output_dir}/range")
    plot_keyword_small_multiples(df_range, f"{args.output_dir}/range")
    plot_emotion_small_multiples(df_range, f"{args.output_dir}/range")
    print("  ✓ Range-level completed")
    print()

    # ---------------- MONTHLY LEVEL (BASIC) ----------------
    print("[2/3] Monthly-level visualizations...")
    plot_monthly_dual(df_month, df_su, f"{args.output_dir}/monthly")
    plot_monthly_trend(df_month, f"{args.output_dir}/monthly")
    analyze_leading(df_month, df_su, f"{args.output_dir}/monthly")
    print("  ✓ Monthly-level completed")
    print()

    # ---------------- CUSTOM LAG ----------------
    print("[3/3] Custom lag visualizations...")
    
    if args.lags:
        # 명령줄 인자로 받은 lag들
        lag_list = [int(x.strip()) for x in args.lags.split(",")]
        print(f"  Using custom lags: {lag_list}")
    else:
        # 기본값: -6 ~ +3
        lag_list = list(range(-6, 4))
        print(f"  Using default lags: {lag_list}")
    
    for lag in lag_list:
        plot_monthly_dual_with_lag(df_month, df_su, f"{args.output_dir}/monthly", lag=lag)
    
    print("  ✓ Custom lag completed")
    print()

    print("="*70)
    print("✅ All Visualizations Completed!")
    print(f"   Output directory: {args.output_dir}")
    print("="*70)

# ======================================================================
# 9. EXPORT MONTHLY DATA TO JSON
# ======================================================================
def export_monthly_json(df_m, df_su, outdir):
    """
    월별 SEEI와 자살 데이터를 JSON으로 내보내기
    """
    os.makedirs(outdir, exist_ok=True)
    
    # 병합
    df = pd.merge(df_m, df_su, left_on="month", right_on="날짜", how="inner")
    df = df.sort_values("month").reset_index(drop=True)
    
    # JSON 구조 생성
    monthly_data = {
        "metadata": {
            "description": "Monthly SEEI and Suicide Death Data",
            "period": {
                "start": df["month"].min().strftime("%Y-%m"),
                "end": df["month"].max().strftime("%Y-%m")
            },
            "total_months": len(df),
            "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "data": []
    }
    
    # 각 월 데이터 추가
    for _, row in df.iterrows():
        month_entry = {
            "date": row["month"].strftime("%Y-%m"),
            "seei": {
                "total": float(row["total_seei"]),
                "neg_ratio": float(row["neg_ratio_overall"]) if "neg_ratio_overall" in row else None
            },
            "suicide": {
                "deaths": int(row["자살사망자수"])
            },
            "stats": {
                "posts": int(row["posts"]) if "posts" in row else None,
                "comments": int(row["comments"]) if "comments" in row else None
            }
        }
        
        # Keywords 추가 (있는 경우)
        kw_cols = [c for c in df.columns if c.startswith("kw_") and not c.startswith("kw_ratio_") and not c.startswith("kw_posts_") and not c.startswith("kw_comments_") and not c.startswith("kw_neg_")]
        if kw_cols:
            month_entry["keywords"] = {}
            for col in kw_cols:
                kw_name = col.replace("kw_", "")
                month_entry["keywords"][kw_name] = {
                    "score": float(row[col]),
                    "ratio": float(row[f"kw_ratio_{kw_name}"]) if f"kw_ratio_{kw_name}" in row else None
                }
        
        # Emotions 추가 (있는 경우)
        emo_cols = [c for c in df.columns if c.startswith("emo_")]
        if emo_cols:
            month_entry["emotions"] = {}
            for col in emo_cols:
                emo_name = col.replace("emo_", "")
                month_entry["emotions"][emo_name] = float(row[col])
        
        monthly_data["data"].append(month_entry)
    
    # JSON 저장
    output_path = f"{outdir}/monthly_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(monthly_data, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ Monthly data exported to JSON: {output_path}")
    return output_path


# ======================================================================
# 10. EXPORT LAG ANALYSIS TO JSON
# ======================================================================
def export_lag_analysis_json(df_m, df_su, outdir, lag_list=None):
    """
    여러 lag에 대한 상관관계 데이터를 JSON으로 내보내기
    """
    os.makedirs(outdir, exist_ok=True)
    
    if lag_list is None:
        lag_list = list(range(-6, 4))
    
    # 병합
    df = pd.merge(df_m, df_su, left_on="month", right_on="날짜", how="inner")
    df = df.sort_values("month").reset_index(drop=True)
    
    # JSON 구조 생성
    lag_analysis = {
        "metadata": {
            "description": "SEEI vs Suicide Lag Analysis",
            "period": {
                "start": df["month"].min().strftime("%Y-%m"),
                "end": df["month"].max().strftime("%Y-%m")
            },
            "total_months": len(df),
            "lag_range": {
                "min": min(lag_list),
                "max": max(lag_list)
            },
            "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "lag_results": []
    }
    
    # 각 lag에 대해 계산
    for lag in lag_list:
        # SEEI shift
        seei_shifted = df["total_seei"].shift(-lag)
        valid_mask = seei_shifted.notna()
        
        if valid_mask.sum() > 2:
            # 상관계수 계산
            corr, p_value = stats.pearsonr(
                seei_shifted[valid_mask], 
                df["자살사망자수"][valid_mask]
            )
            
            # 데이터 포인트
            data_points = []
            for i in range(len(df)):
                if valid_mask.iloc[i]:
                    data_points.append({
                        "date": df["month"].iloc[i].strftime("%Y-%m"),
                        "seei_shifted": float(seei_shifted.iloc[i]),
                        "suicide": int(df["자살사망자수"].iloc[i])
                    })
            
            lag_entry = {
                "lag": int(lag),
                "interpretation": (
                    f"SEEI leads by {abs(lag)} months" if lag < 0 else
                    f"Suicide leads by {lag} months" if lag > 0 else
                    "No lag (simultaneous)"
                ),
                "correlation": {
                    "pearson_r": float(corr),
                    "p_value": float(p_value),
                    "significant": bool(p_value < 0.05),
                    "sample_size": int(valid_mask.sum())
                },
                "data_points": data_points
            }
        else:
            lag_entry = {
                "lag": int(lag),
                "error": "Insufficient data points",
                "correlation": None
            }
        
        lag_analysis["lag_results"].append(lag_entry)
    
    # 최적 lag 찾기
    valid_results = [r for r in lag_analysis["lag_results"] if r.get("correlation")]
    if valid_results:
        best = max(valid_results, key=lambda x: abs(x["correlation"]["pearson_r"]))
        lag_analysis["best_lag"] = {
            "lag": best["lag"],
            "interpretation": best["interpretation"],
            "correlation": best["correlation"]["pearson_r"],
            "p_value": best["correlation"]["p_value"]
        }
    
    # JSON 저장
    output_path = f"{outdir}/lag_analysis.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(lag_analysis, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ Lag analysis exported to JSON: {output_path}")
    return output_path


# ======================================================================
# 11. EXPORT KEYWORD TRENDS TO JSON
# ======================================================================
def export_keyword_trends_json(df_m, outdir):
    """
    월별 키워드 트렌드를 JSON으로 내보내기
    """
    os.makedirs(outdir, exist_ok=True)
    
    df = df_m.copy().sort_values("month").reset_index(drop=True)
    
    # 키워드 컬럼 찾기
    kw_ratio_cols = [c for c in df.columns if c.startswith("kw_ratio_")]
    keywords = [c.replace("kw_ratio_", "") for c in kw_ratio_cols]
    
    if not keywords:
        print("  ⚠️ No keyword data found")
        return None
    
    # JSON 구조 생성
    keyword_trends = {
        "metadata": {
            "description": "Monthly Keyword Trend Analysis",
            "period": {
                "start": df["month"].min().strftime("%Y-%m"),
                "end": df["month"].max().strftime("%Y-%m")
            },
            "total_months": len(df),
            "keywords": keywords,
            "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "trends": {}
    }
    
    # 각 키워드별 트렌드
    for kw in keywords:
        ratio_col = f"kw_ratio_{kw}"
        score_col = f"kw_{kw}"
        posts_col = f"kw_posts_{kw}"
        comments_col = f"kw_comments_{kw}"
        
        monthly_values = []
        for _, row in df.iterrows():
            entry = {
                "date": row["month"].strftime("%Y-%m"),
                "ratio": float(row[ratio_col]) if ratio_col in row else None,
                "score": float(row[score_col]) if score_col in row else None,
                "posts": int(row[posts_col]) if posts_col in row else None,
                "comments": int(row[comments_col]) if comments_col in row else None
            }
            monthly_values.append(entry)
        
        # 통계 계산
        ratios = [v["ratio"] for v in monthly_values if v["ratio"] is not None]
        keyword_trends["trends"][kw] = {
            "monthly_values": monthly_values,
            "statistics": {
                "mean": float(np.mean(ratios)) if ratios else None,
                "std": float(np.std(ratios)) if ratios else None,
                "min": float(np.min(ratios)) if ratios else None,
                "max": float(np.max(ratios)) if ratios else None
            }
        }
    
    # JSON 저장
    output_path = f"{outdir}/keyword_trends.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(keyword_trends, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ Keyword trends exported to JSON: {output_path}")
    return output_path


# ======================================================================
# 12. EXPORT EMOTION TRENDS TO JSON
# ======================================================================
def export_emotion_trends_json(df_m, outdir):
    """
    월별 감정 트렌드를 JSON으로 내보내기
    """
    os.makedirs(outdir, exist_ok=True)
    
    df = df_m.copy().sort_values("month").reset_index(drop=True)
    
    # 감정 컬럼 찾기
    emo_cols = [c for c in df.columns if c.startswith("emo_")]
    emotions = [c.replace("emo_", "") for c in emo_cols]
    
    if not emotions:
        print("  ⚠️ No emotion data found")
        return None
    
    # JSON 구조 생성
    emotion_trends = {
        "metadata": {
            "description": "Monthly Emotion Trend Analysis",
            "period": {
                "start": df["month"].min().strftime("%Y-%m"),
                "end": df["month"].max().strftime("%Y-%m")
            },
            "total_months": len(df),
            "emotions": emotions,
            "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "trends": {}
    }
    
    # 각 감정별 트렌드
    for emo in emotions:
        col = f"emo_{emo}"
        
        monthly_values = []
        for _, row in df.iterrows():
            entry = {
                "date": row["month"].strftime("%Y-%m"),
                "ratio": float(row[col])
            }
            monthly_values.append(entry)
        
        # 통계 계산
        ratios = [v["ratio"] for v in monthly_values]
        emotion_trends["trends"][emo] = {
            "monthly_values": monthly_values,
            "statistics": {
                "mean": float(np.mean(ratios)),
                "std": float(np.std(ratios)),
                "min": float(np.min(ratios)),
                "max": float(np.max(ratios))
            }
        }
    
    # JSON 저장
    output_path = f"{outdir}/emotion_trends.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(emotion_trends, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ Emotion trends exported to JSON: {output_path}")
    return output_path

if __name__ == "__main__":
    main()
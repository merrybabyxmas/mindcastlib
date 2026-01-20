# ==============================================
# seei_visualize.py
# SEEI 전체 시각화 자동 생성 (4종)
# ==============================================

import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import argparse # argparse 추가

# -------------------------------------------------
# 1) 데이터 로드 및 시각화 실행 (Main Runner)
# -------------------------------------------------

# 함수 정의: 인수로 세 개의 경로를 받습니다.
def run_visualization(seei_raw_path, base_data_path, save_dir):
    
    # 출력 디렉토리 생성
    os.makedirs(save_dir, exist_ok=True)
    
    # -------------------------------------------------
    # 1) 데이터 로드
    # -------------------------------------------------
    print(f"[INFO] Loading SEEI CSV: {seei_raw_path}")
    print(f"[INFO] Loading BASE DATA: {base_data_path}")
    
    try:
        # 인수로 받은 경로 사용
        se_df = pd.read_csv(seei_raw_path)
        orig = pd.read_csv(base_data_path)
    except FileNotFoundError as e:
        print(f"[ERROR] 파일 로드 실패: {e}")
        return

    # SEEI date 생성
    se_df["month"] = se_df["month"].astype(str).str.zfill(2)
    se_df["date"] = pd.to_datetime(se_df["year"].astype(str) + "-" + se_df["month"] + "-01")

    # 원본 경제지표 date
    orig["date"] = pd.to_datetime(orig["날짜"])

    # merge
    df = pd.merge(se_df, orig, on="date", how="inner").sort_values("date")

    # -------------------------------------------------
    # 2) 매핑 (SEEI → 원본 경제지표)
    # -------------------------------------------------
    mapping = {
        "실업률": "실업률(%)",
        "취업자": "취업자(천명)",
        "경제활동인구": "경제활동인구(천명)",
        "비경제활동인구": "비경제활동인구(천명)",
        "고용률": "고용률(%)",
        "소비자물가상승률": "소비자물가상승률(%)",
        "GDP": "GDP",
        "GNI": "GNI",
        "1인당_실질국민총소득": "1인당_실질국민총소득(원)",
        "임금총액": "임금총액",
        "근로시간": "근로시간",
        "근로일수": "근로일수",
        "고령인구비율": "고령인구비율",
        "총인구수": "총인구수",
        "평균연령": "평균연령",
        "중위연령": "중위연령",
        "0~14세 구성비": "0~14세 구성비",
        "15~64세 구성비": "15~64세 구성비",
    }

    # -------------------------------------------------
    # (1) SEEI vs 경제지표 Dual-Axis Plot
    # -------------------------------------------------
    def plot_dual_axis(seei_col, econ_col):
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df["date"], y=df[seei_col],
            mode="lines+markers",
            name=f"{seei_col} (SEEI)",
            yaxis="y1", line=dict(color="#D62728")
        ))

        fig.add_trace(go.Scatter(
            x=df["date"], y=df[econ_col],
            mode="lines+markers",
            name=f"{econ_col} (경제지표)",
            yaxis="y2", line=dict(color="#1F77B4")
        ))

        fig.update_layout(
            title=f"{seei_col} vs {econ_col} (Dual Axis)",
            xaxis=dict(title="날짜"),
            yaxis=dict(title=f"{seei_col} (SEEI)"),
            yaxis2=dict(title=econ_col, overlaying="y", side="right"),
            width=900, height=450,
        )

        # save_dir 사용
        save_path = f"{save_dir}/dualaxis_{seei_col}.html"
        fig.write_html(save_path)
        print(f"[SAVED] Dual Axis → {save_path}")

    # 전체 자동 생성
    for seei_col, econ_col in mapping.items():
        if seei_col in df.columns and econ_col in df.columns:
            plot_dual_axis(seei_col, econ_col)


    # -------------------------------------------------
    # (2) Pie Chart (월별 SEEI 구성비)
    # -------------------------------------------------

    def plot_pie(year, month, top_n=7):
        local_se_df = se_df.copy()
        row = local_se_df[(local_se_df["year"] == year) & (local_se_df["month"].astype(int) == month)]
        if len(row) == 0:
            return
        row = row.iloc[0]

        # 제외할 meta 컬럼
        exclude = {"year", "month", "date"}
        cols = [c for c in local_se_df.columns if c not in exclude]
        values = row[cols].values
        labels = cols

        # Top N
        order = values.argsort()[::-1]
        values = values[order][:top_n]
        labels = [labels[i] for i in order][:top_n]

        fig = go.Figure(go.Pie(
            labels=labels,
            values=values,
            hole=0.45
        ))

        fig.update_layout(
            title=f"{year}년 {month}월 SEEI 구성비",
            width=700, height=600
        )

        # save_dir 사용
        save_path = f"{save_dir}/pie_{year}_{month}.html"
        fig.write_html(save_path)
        print(f"[SAVED] Pie Chart → {save_path}")

    # 자동 생성 (전체 기간)
    for y in sorted(se_df["year"].unique()):
        for m in sorted(se_df[se_df["year"] == y]["month"].astype(int).unique()):
            plot_pie(y, m)


    # -------------------------------------------------
    # (3) Monthly SEEI Total Line Plot
    # -------------------------------------------------

    def plot_monthly_total():
        meta_cols = {"year", "month", "date"}
        value_cols = [c for c in se_df.columns if c not in meta_cols]

        se_df["SEEI_total"] = se_df[value_cols].sum(axis=1)

        fig = px.line(
            se_df,
            x="date",
            y="SEEI_total",
            markers=True,
            title="월별 SEEI Total 변화"
        )

        # save_dir 사용
        save_path = f"{save_dir}/monthly_total.html"
        fig.write_html(save_path)
        print(f"[SAVED] Monthly Total → {save_path}")

    plot_monthly_total()


    # -------------------------------------------------
    # (4) SEEI_total vs 자살자수 Dual Axis
    # -------------------------------------------------

    def plot_SEEI_suicide():
        # SEEI total
        meta_cols = {"year", "month", "date"}
        value_cols = [c for c in se_df.columns if c not in meta_cols]

        se_df["SEEI_total"] = se_df[value_cols].sum(axis=1)

        # 자살자수
        orig_month = orig.set_index("date").resample("MS").first().reset_index()
        merged = pd.merge(se_df, orig_month, on="date", how="inner")

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=merged["date"], y=merged["SEEI_total"],
            name="SEEI Total", yaxis="y1",
            mode="lines+markers", line=dict(color="red")
        ))

        fig.add_trace(go.Scatter(
            x=merged["date"], y=merged["자살사망자수"],
            name="자살자수", yaxis="y2",
            mode="lines+markers", line=dict(color="blue")
        ))

        fig.update_layout(
            title="SEEI Total vs 자살사망자수",
            yaxis=dict(title="SEEI Total"),
            yaxis2=dict(title="자살사망자수", overlaying="y", side="right"),
            width=900, height=450
        )

        # save_dir 사용
        save_path = f"{save_dir}/seei_vs_suicide.html"
        fig.write_html(save_path)
        print(f"[SAVED] SEEI vs Suicide → {save_path}")

    plot_SEEI_suicide()


    print("\n=====================================")
    print(" 🎉 ALL VISUALIZATIONS COMPLETED!")
    print("=====================================")


# -------------------------------------------------
# 메인 진입점
# -------------------------------------------------
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Generate SEEI visualizations.")
    parser.add_argument(
        "--seei", 
        type=str, 
        required=True, 
        help="Path to the input SEEI raw CSV file (SEEI_raw.csv)."
    )
    parser.add_argument(
        "--base", 
        type=str, 
        required=True, 
        help="Path to the base economic data CSV file (base_data.csv)."
    )
    parser.add_argument(
        "--out", 
        type=str, 
        required=True, 
        help="Output directory to save the visualization HTML files."
    )
    args = parser.parse_args()
    
    run_visualization(
        seei_raw_path=args.seei, 
        base_data_path=args.base, 
        save_dir=args.out
    )
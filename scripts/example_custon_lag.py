"""
Custom Lag 시각화 예제
======================
visualize_seei.py의 plot_with_custom_lag 함수 사용법
"""

import pandas as pd
from visualize_seei import plot_with_custom_lag

# ======================================================
# 데이터 로드
# ======================================================
seei_path = "/home/mindcastlib/data/seei/seei_master/seei_master.csv"
suicide_path = "/home/mindcastlib/data/base/base_data.csv"

# SEEI 데이터
df_seei = pd.read_csv(seei_path, parse_dates=['date'])
print(f"SEEI records: {len(df_seei)}")

# 자살 데이터 (월별)
df_suicide = pd.read_csv(suicide_path)
df_suicide['날짜'] = pd.to_datetime(df_suicide['날짜'], format='%Y-%m')
df_suicide = df_suicide.rename(columns={'날짜': 'date', '자살사망자수': 'suicide_deaths'})
df_suicide = df_suicide[['date', 'suicide_deaths']]
print(f"Suicide records: {len(df_suicide)}")

# ======================================================
# Custom Lag 시각화
# ======================================================
output_dir = "/home/mindcastlib/data/seei/visualization"

print("\n" + "="*60)
print("Testing Different Lag Values")
print("="*60)

# 예제 1: SEEI가 30일 선행 (lag = -3)
print("\n[Example 1] SEEI leading by 30 days (lag=-3)")
plot_with_custom_lag(df_seei, df_suicide, lag=-3, output_dir=output_dir)

# 예제 2: SEEI가 60일 선행 (lag = -6)
print("\n[Example 2] SEEI leading by 60 days (lag=-6)")
plot_with_custom_lag(df_seei, df_suicide, lag=-6, output_dir=output_dir)

# 예제 3: 동시 비교 (lag = 0)
print("\n[Example 3] Simultaneous comparison (lag=0)")
plot_with_custom_lag(df_seei, df_suicide, lag=0, output_dir=output_dir)

# 예제 4: 자살이 20일 선행 (lag = +2)
print("\n[Example 4] Suicide leading by 20 days (lag=+2)")
plot_with_custom_lag(df_seei, df_suicide, lag=2, output_dir=output_dir)

# 예제 5: 여러 lag를 한번에 테스트
print("\n[Example 5] Testing multiple lags at once")
test_lags = [-6, -5, -4, -3, -2, -1, 0, 1, 2, 3]

for lag in test_lags:
    plot_with_custom_lag(df_seei, df_suicide, lag=lag, output_dir=output_dir)

print("\n" + "="*60)
print("✅ All custom lag visualizations completed!")
print(f"   Check: {output_dir}/custom_lag_*.png")
print("="*60)

# ======================================================
# 상관계수 비교 (어떤 lag가 최적인지 확인)
# ======================================================
print("\nCorrelation comparison across different lags:")
print("-" * 60)

from scipy import stats

correlations = []

for lag in range(-10, 11):
    # 병합
    df_merged = pd.merge(df_seei[['date', 'total_seei']], 
                         df_suicide[['date', 'suicide_deaths']], 
                         on='date', how='inner')
    
    # shift
    seei_shifted = df_merged['total_seei'].shift(-lag)
    valid_mask = seei_shifted.notna()
    
    if valid_mask.sum() > 10:
        corr, p_val = stats.pearsonr(seei_shifted[valid_mask], 
                                     df_merged['suicide_deaths'][valid_mask])
        correlations.append({
            'lag': lag,
            'lag_days': lag * 10,
            'correlation': corr,
            'p_value': p_val,
            'n': valid_mask.sum()
        })

# DataFrame으로 변환
df_corr = pd.DataFrame(correlations)

# 상관계수 절대값 기준 정렬
df_corr['abs_corr'] = df_corr['correlation'].abs()
df_corr = df_corr.sort_values('abs_corr', ascending=False)

print("\nTop 5 lags by absolute correlation:")
print(df_corr.head(5)[['lag', 'lag_days', 'correlation', 'p_value']].to_string(index=False))

print("\nOptimal lag (highest absolute correlation):")
best = df_corr.iloc[0]
print(f"  Lag: {best['lag']} periods ({best['lag_days']} days)")
print(f"  Correlation: r = {best['correlation']:.3f}")
print(f"  P-value: p = {best['p_value']:.4f}")
print(f"  Interpretation: {'SEEI leads' if best['lag'] < 0 else 'Suicide leads' if best['lag'] > 0 else 'Simultaneous'}")
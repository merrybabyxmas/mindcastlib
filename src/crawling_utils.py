# crawling_utils.py
from __future__ import annotations

# =========================
# 표준 라이브러리
# =========================
import os
import json
import time
import re
import datetime as dt
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode

# =========================
# 서드파티
# =========================
import requests
import numpy as np
import pandas as pd

# =========================
# 전역 설정
# =========================
PROJECT_ROOT = Path(__file__).resolve().parents[1] # for 절대경로  
METADATA_PATH = PROJECT_ROOT / "data_suicide_crawling" / "metadata.json"
# ============================================================
# 📦 file_utils
# ============================================================
def ensure_parent_dir(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

# ============================================================
# 📦 metadata 관리
# ============================================================
def update_meta(meta_path: str, key: str, record: dict):
    p = Path(meta_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    if p.exists():
        meta = json.loads(p.read_text(encoding="utf-8"))
    else:
        meta = {}

    rec = dict(record)
    rec["collected_at"] = dt.datetime.now().isoformat(timespec="seconds")
    meta[key] = rec

    p.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

# ============================================================
# 📦 collectors.common
# ============================================================
def _set_query(url: str, **kwargs) -> str: # url의 쿼리 부분을 가져와서 쿼리를 바꾼 url을 return 합니다
    u = urlparse(url)
    q = parse_qs(u.query)
    for k, v in kwargs.items():
        q[k] = [str(v)]
    new_q = urlencode(q, doseq=True)
    return urlunparse((u.scheme, u.netloc, u.path, u.params, new_q, u.fragment))

# 
def _add_months(d: dt.date, months: int) -> dt.date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    return dt.date(y, m, 1)

def iter_ym_chunks_6m(start_ym: str, end_ym: str):
    """
    start_ym/end_ym: 'YYYYMM'
    데이터를 6개월 단위로 끊어서 가져옵니다.
    """
    s = dt.date(int(start_ym[:4]), int(start_ym[4:]), 1)
    e = dt.date(int(end_ym[:4]), int(end_ym[4:]), 1)

    cur = s
    while cur <= e:
        nxt = _add_months(cur, 6)         # 다음 청크 시작(6개월 뒤)
        chunk_end = _add_months(nxt, -1)  # 청크 끝 = 다음 시작의 전월
        if chunk_end > e:
            chunk_end = e

        yield f"{cur.year:04d}{cur.month:02d}", f"{chunk_end.year:04d}{chunk_end.month:02d}"
        cur = nxt

def make_latest_dated_path(base_path: str, date: str | None = None) -> str:

    if date is None:
        date = dt.date.today().strftime("%Y%m%d")

    p = Path(base_path)
    return str(p.with_name(f"{p.stem}_{date}{p.suffix}"))

def fetch_kosis_by_6m(openapi_url: str, start_ym: str, end_ym: str, fetch_to_df, sleep_s: float = 0.3) -> pd.DataFrame:
    frames = []
    for s, e in iter_ym_chunks_6m(start_ym, end_ym):
        url = _set_query(openapi_url, startPrdDe=s, endPrdDe=e)
        df = fetch_to_df(url)
        if df is None or df.empty:
            continue
        frames.append(df)
        time.sleep(sleep_s)  # 서버 과부하/타임아웃 완화

    if not frames:
        return pd.DataFrame()

    out = pd.concat(frames, ignore_index=True)

    # 중복 제거(기간 겹침/서버 중복 응답 대비)
    out = out.drop_duplicates()
    return out

def replace_latest_dated_file(base_path: str) -> str: # 갱신 당일의 날짜를 기존 파일명 뒤에 붙입니다
    """
    같은 디렉터리 내의 *_latest_*.csv 를 모두 삭제하고
    오늘 날짜의 *_latest_YYYYMMDD.csv 경로를 반환
    """
    p = Path(base_path)
    pattern = f"{p.stem}_*{p.suffix}"   

    # 기존 latest_날짜 파일 전부 삭제
    for f in p.parent.glob(pattern):
        f.unlink(missing_ok=True)

    # 새 파일 경로 생성
    return make_latest_dated_path(base_path)

def build_url_with_dynamic_period(issued_url: str, start_ym: str) -> str:
    """발급 URL을 템플릿으로 사용하되 start/end만 동적으로"""
    u = urlparse(issued_url)
    q = parse_qs(u.query)

    today = dt.date.today()
    end_ym = f"{today.year}{today.month:02d}"

    q["startPrdDe"] = [start_ym]
    q["endPrdDe"] = [end_ym]

    new_query = urlencode(q, doseq=True)
    return urlunparse((u.scheme, u.netloc, u.path, u.params, new_query, u.fragment))

def fetch_to_df(url: str) -> pd.DataFrame:
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    data = r.json()

    # ✅  정상적으로 데이터를 가져왔을 경우 list[dict]
    if isinstance(data, list):
        return pd.DataFrame(data)

    # ✅ 2) dict 케이스: 에러 or 래핑된 결과
    if isinstance(data, dict):
        # (A) KOSIS "데이터 없음"은 err=30 → 예외가 아니라 빈 DF로 처리합니다 -> fetch_6m을 위해서
        if str(data.get("err", "")).strip() == "30":
            return pd.DataFrame()

        # (B) 그 외 KOSIS 에러는 raise
        # - err / error / message 등이 있으면 에러로 간주
        err_keys = ["err", "errMsg", "error", "message"]
        if any(k in data for k in err_keys):
            raise ValueError(f"KOSIS API returned error dict: {data}")

        # (C) dict 안에 list가 들어있는 형태
        for key in ["data", "items", "rows", "list", "result", "RESULT"]:
            if key in data and isinstance(data[key], list):
                return pd.DataFrame(data[key])

        # (D) (디버깅용)
        return pd.DataFrame([data])

    raise ValueError(f"Unexpected JSON response type: {type(data)}")
# ============================================================
# 📦 parser.year_to_month
# ============================================================
def expand_year_to_months(df_year, year_col="date", value_cols=None):
    """
    연도 데이터 -> 월별 데이터 (값 단순 복제)
    """
    if value_cols is None:
        value_cols = [c for c in df_year.columns if c != year_col]


    rows = []
    for _, row in df_year.iterrows():
        y = row[year_col]

        # year 안전하게 추출
        if isinstance(y, pd.Timestamp):
            year = y.year
        else:
            year = int(str(y)[:4])  # "2020", "2020-01" 같은 것도 처리

        for m in range(1, 13):
            new_row = {"date": f"{year}-{m:02d}"}
            for col in value_cols:
                new_row[col] = row[col]
            rows.append(new_row)

    df_month = pd.DataFrame(rows)
    return df_month

# ============================================================
# 📦 parser.apply_denton
# ============================================================
def build_A(T, m=3):
    """
    제약행렬 A: 분기 -> 월 합계 보존
    """
    A = np.zeros((T, T * m))
    for i in range(T):
        A[i, i*m:(i+1)*m] = 1
    return A


def build_D(n):
    """
    1차 차분 행렬 D
    """
    D = np.zeros((n - 1, n))
    for i in range(n - 1):
        D[i, i] = -1
        D[i, i + 1] = 1
    return D

def quarter_label_to_months(q_label: str):
    # 분기 라벨 -> 월 라벨 
    year, q = q_label.split("-")
    q = int(q)

    if q not in [1, 2, 3, 4]:
        raise ValueError(f"Invalid quarter label: {q_label}")

    start_month = (q - 1) * 3 + 1  # 1,4,7,10

    months = []
    for m in range(start_month, start_month + 3):
        months.append(f"{year}-{m:02d}")

    return months


def apply_denton(y_quarterly, m=3):
    y = np.asarray(y_quarterly).reshape(-1) # 원래 쿼터 데이터
    T = len(y)
    n = T * m # 생성해야할 월 개수 

    A = build_A(T, m)
    D = build_D(n)
    DTD = D.T @ D

    zero = np.zeros((A.shape[0], A.shape[0]))
    # 라그랑주 승수법 적용 후 연립방정식 식 도출 
    KKT = np.block([
        [DTD, A.T],
        [A, zero]
    ]) # 좌변 정의 

    rhs = np.concatenate([np.zeros(n), y]) #우변 정의

    sol = np.linalg.solve(KKT, rhs) # 연립방정식 풀이 
    x_monthly = sol[:n]

    return x_monthly

def denton_with_dates(df_quarter, date_col="date", value_cols="value" ): 
    """
    df_quarter: 분기 데이터 (여러 지표 컬럼)
    date_col: 분기 라벨 컬럼
    value_cols: Denton 적용할 컬럼 리스트 (None이면 date_col 제외 전부)
    """
    df_quarter = df_quarter.sort_values(date_col).reset_index(drop=True)

    if value_cols is None:
        value_cols = [c for c in df_quarter.columns if c != date_col]

    # 분기 -> 월 인덱스 생성
    month_dates = []
    for q_label in df_quarter[date_col]:
        month_dates.extend(quarter_label_to_months(q_label))

    df_month = pd.DataFrame({"date": month_dates})

    # 컬럼별로 Denton 적용
    for col in value_cols:
        y = pd.to_numeric(df_quarter[col], errors="raise").values
        x_month = apply_denton(y)
        df_month[col] = x_month
    return df_month
    
# ============================================================
# 📦 collectors 구현부
# ============================================================

def cpi_run(cfg: dict):
     # 1) 수집
    url = build_url_with_dynamic_period(cfg["openapi_url"], cfg.get("start_ym", "196501"))
    raw = fetch_to_df(url)

    # 2) 전처리(collector에 포함)
    df = raw[["PRD_DE", "DT"]].copy()
    df.columns = df.columns.astype(str).str.strip()
    df = df.rename(columns={"PRD_DE": "date", "DT": "cpi"})

    df["cpi"] = pd.to_numeric(df["cpi"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], format="%Y%m").dt.strftime("%Y-%m")
    df = df.sort_values("date").reset_index(drop=True)
    
    # 3) 저장
    out_csv = PROJECT_ROOT / cfg["output_csv"]
    ensure_parent_dir(out_csv)
    # 1) 이전 latest_날짜 파일 제거 + 오늘 파일 경로 생성
    out_csv = replace_latest_dated_file(out_csv)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    # 4) metadata 기록
    key = cfg.get("metadata_key", "cpi")
    update_meta(METADATA_PATH, key, {
        "saved_file": out_csv,
        "source_url": url,
        "rows": int(df.shape[0]),
        "max_date": df["date"].max(),
    })

    print("✅ CPI 저장:", out_csv, "rows:", len(df), "max_date:", df["date"].max())


def consumer_price_change_index_run(cfg: dict):
    # 1) 수집
    url = build_url_with_dynamic_period(cfg["openapi_url"], cfg.get("start_ym",))
    raw = fetch_to_df(url)
    
    # 2) 전처리(collector에 포함)
    raw["C1_NM"] = raw["C1_NM"].astype(str).str.strip()
    raw = raw[raw["C1_NM"].eq("총지수")].copy()

    df = raw[["PRD_DE", "DT"]].copy()
    df.columns = df.columns.astype(str).str.strip()
    df = df.rename(columns={
    "PRD_DE": "date",
    "DT": "소비자물가등락률"
    })

    if df["date"].str.len().iloc[0] == 6:
        df["date"] = pd.to_datetime(df["date"], format="%Y%m").dt.strftime("%Y-%m")
    else:
        df["date"] = pd.to_datetime(df["date"], format="%Y").dt.strftime("%Y")

    df  = expand_year_to_months(df, year_col="date", value_cols = None) # 연간데이터를 복사해서 월별데이터로 변환 
    # 3) 저장
    out_csv = PROJECT_ROOT / cfg["output_csv"]
    ensure_parent_dir(out_csv)
    # 1) 이전 latest_날짜 파일 제거 + 오늘 파일 경로 생성
    out_csv = replace_latest_dated_file(out_csv)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    # 4) metadata 기록
    key = cfg.get("metadata_key", "consumer_price_change_index")
    update_meta(METADATA_PATH, key, {
        "saved_file": out_csv,
        "source_url": url,
        "rows": int(df.shape[0]),
        "max_date": df["date"].max(),
    })

    print("✅ Consumer_Price_Change_Index 저장:", out_csv, "rows:", len(df), "max_date:", df["date"].max())


def average_working_day_run(cfg: dict):
   
    url =cfg["openapi_url"] #지표누리 api는 항상 최신 값을 반환 
    df = fetch_to_df(url)
    df.columns = df.columns.astype(str).str.strip()
    
    date_col =  "시점"
    value_col =  "값"
    item_col = "항목이름"
    df = df[df[date_col].str.len() == 6].copy() # monthly 지표만 받아오게 됩니다

    df = df[[date_col,item_col,value_col]].copy()
    df = df[df[item_col].isin(["근로일수"])].copy()

    df[value_col] = pd.to_numeric(df[value_col],errors= "coerce")
    df[item_col] = df[item_col].astype(str).str.strip()
    df[date_col] = df[date_col].astype(str).str.strip()


    wide = df.pivot_table(
        index="시점",
        columns=item_col,
        values=value_col,
        aggfunc="first"
    ).sort_index()
    wide = wide.reset_index()
  
    wide = wide.rename(columns = {"시점":"date"})
    if wide["date"].str.len().iloc[0] == 6:
        wide["date"] = pd.to_datetime(wide["date"], format="%Y%m").dt.strftime("%Y-%m")
    else:
        wide["date"] = pd.to_datetime(wide["date"], format="%Y").dt.strftime("%Y")
        
    out_csv = PROJECT_ROOT / cfg["output_csv"]
    ensure_parent_dir(out_csv)
    # 1) 이전 latest_날짜 파일 제거 + 오늘 파일 경로 생성
    out_csv = replace_latest_dated_file(out_csv)
    wide.to_csv(out_csv, index=False, encoding="utf-8-sig")

    # 4) metadata 기록
    key = cfg.get("metadata_key", "average_working_day")
    update_meta(METADATA_PATH, key, {
        "saved_file": out_csv,
        "source_url": url,
        "rows": int(wide.shape[0]),
        "max_date": wide["date"].max(),
    })

    print("✅ Average_Working_Day 저장:", out_csv, "rows:", len(wide), "max_date:", wide["date"].max())
   

def aver_mid_age_run(cfg: dict):
    url = build_url_with_dynamic_period(cfg["openapi_url"], cfg.get("start_ym",))
    raw = fetch_to_df(url)
    

    # 전처리
    raw.columns = raw.columns.astype(str).str.strip()
    raw = raw[raw["C2_NM"] == "전국"].copy()

    date_col = "PRD_DE"
    item_col =  "ITM_NM"
    value_col = "DT"

    raw= raw[[date_col,item_col,value_col]].copy()
    
    raw = raw[raw[item_col].isin(["중위연령", "평균연령"])].copy()
    
    
    raw[value_col] = pd.to_numeric(raw[value_col],errors= "coerce")
    raw[item_col] = raw[item_col].astype(str).str.strip()
    raw[date_col] = raw[date_col].astype(str).str.strip()
    
    wide = raw.pivot_table(
        index=date_col,
        columns=item_col,
        values=value_col,
        aggfunc="first"
    ).sort_index()
    wide = wide.reset_index()
    wide = wide.rename(columns = {date_col : "date"})

    
    if wide["date"].str.len().iloc[0] == 6:
        wide["date"] = pd.to_datetime(wide["date"], format="%Y%m").dt.strftime("%Y-%m")
    else:
        wide["date"] = pd.to_datetime(wide["date"], format="%Y").dt.strftime("%Y")

    wide = expand_year_to_months(wide ,year_col="date",value_cols=None) # 연 데이터 복사해서 월별로 
    # 3) 저장
    out_csv = PROJECT_ROOT / cfg["output_csv"]
    ensure_parent_dir(out_csv)
    # 3-1) 이전 latest_날짜 파일 제거 + 오늘 파일 경로 생성
    out_csv = replace_latest_dated_file(out_csv)
    wide.to_csv(out_csv, index=False, encoding="utf-8-sig")

    # 3-2) metadata 기록
    key = cfg.get("metadata_key", "aver_mid_age")
    update_meta(METADATA_PATH, key, {
        "saved_file": out_csv,
        "source_url": url,
        "rows": int(wide.shape[0]),
        "max_date": wide["date"].max(),
    })

    print("✅ Aver_Mid_Age 저장:", out_csv, "rows:", len(wide), "max_date:", wide["date"].max())


def loan_run(cfg: dict):
    start_ym = cfg.get("start_ym", "200204")
    url = build_url_with_dynamic_period(cfg["openapi_url"], start_ym)
    df = fetch_to_df(url)
    df.columns = df.columns.astype(str).str.strip()

    date_col = "PRD_DE"
    value_col = "DT"
    item_col = "C1_NM"

    # 2) 전처리
    df = df[[date_col, item_col, value_col]].copy()

    wanted = ["가계신용", "가계대출", "판매신용"]
    df[item_col] = df[item_col].astype(str).str.strip()
    df = df[df[item_col].isin(wanted)].copy()

    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    df[date_col] = df[date_col].astype(str).str.strip()
    

    wide = (
        df.pivot_table(index=date_col, columns=item_col, values=value_col, aggfunc="first")
          .sort_index()
    )
    wide = wide[[c for c in wanted if c in wide.columns]].reset_index()
    wide = wide.rename(columns={date_col: "date"})
    wide["date"] = pd.to_datetime(wide["date"], format="%Y%m").dt.strftime("%Y-%m")
    wide = denton_with_dates(wide ,date_col="date",value_cols=None) ## denton 추가 
    # 3) 저장
    out_csv = PROJECT_ROOT / cfg["output_csv"]
    ensure_parent_dir(out_csv)
    # 1) 이전 latest_날짜 파일 제거 + 오늘 파일 경로 생성
    out_csv = replace_latest_dated_file(out_csv)
    wide.to_csv(out_csv, index=False, encoding="utf-8-sig")

    # 4) metadata 기록
    key = cfg.get("metadata_key", "loan")
    update_meta(METADATA_PATH, key, {
        "saved_file": out_csv,
        "source_url": url,
        "rows": int(wide.shape[0]),
        "max_date": wide["date"].max() if not wide.empty else None,
    })

    print("✅ Loan 저장:", out_csv, "rows:", len(wide), "max_date:", wide["date"].max() if not wide.empty else None)
    


def gdp_gni_run(cfg: dict):
    
    url = build_url_with_dynamic_period(cfg["openapi_url"], cfg.get("start_ym",))
    raw = fetch_to_df(url)
    
    
    # 전처리
    raw.columns = raw.columns.astype(str).str.strip()
   
    date_col = "PRD_DE"
    item_col =  "C1_NM"
    value_col = "DT"

    raw= raw[[date_col,item_col,value_col]].copy()
    raw = raw[raw[item_col].isin(["국내총생산(시장가격 GDP)", "국민총소득(GNI)"])].copy()
    
    raw[value_col] = pd.to_numeric(raw[value_col],errors= "coerce")
    raw[item_col] = raw[item_col].astype(str).str.strip()
    raw[date_col] = raw[date_col].astype(str).str.strip()


    wide = raw.pivot_table(
        index=date_col,
        columns=item_col,
        values=value_col,
        aggfunc="first"
    ).sort_index()
    wide = wide.reset_index()
    wide = wide.rename(columns = {date_col : "date"})

    
    if wide["date"].str.len().iloc[0] == 6:
        wide["date"] = pd.to_datetime(wide["date"], format="%Y%m").dt.strftime("%Y-%m")
    else:
        wide["date"] = pd.to_datetime(wide["date"], format="%Y").dt.strftime("%Y")
    
    wide = denton_with_dates(wide ,date_col="date",value_cols=None) ## denton 추가 
    # 3) 저장
    out_csv = PROJECT_ROOT / cfg["output_csv"]
    ensure_parent_dir(out_csv)
    # 3-1) 이전 latest_날짜 파일 제거 + 오늘 파일 경로 생성
    out_csv = replace_latest_dated_file(out_csv)
    wide.to_csv(out_csv, index=False, encoding="utf-8-sig")

    # 3-2) metadata 기록
    key = cfg.get("metadata_key", "gdp_gni")
    update_meta(METADATA_PATH, key, {
        "saved_file": out_csv,
        "source_url": url,
        "rows": int(wide.shape[0]),
        "max_date": wide["date"].max(),
    })

    print("✅ GDP_GNI 저장:", out_csv, "rows:", len(wide), "max_date:", wide["date"].max())


def normalize_item(name: str) -> str:
    s = str(name).strip()
    if "실업률" in s: return "실업률"
    if "고용률" in s: return "고용률"
    if "경제활동참가율" in s: return "경제활동참가율"
    return s

def labor_force_run(cfg: dict):
     # 1) 수집
    start_ym = cfg.get("start_ym",)
    url = build_url_with_dynamic_period(cfg["openapi_url"], start_ym)
    df = fetch_to_df(url)
    df.columns = df.columns.astype(str).str.strip()

    date_col = "PRD_DE"
    value_col = "DT"
    item_col = "ITM_NM"
    group_col = "C1_NM"
    if item_col not in df.columns:
        raise KeyError(f"ITM_NM 컬럼이 없습니다. columns={list(df.columns)}")
    if group_col not in df.columns:
        raise KeyError("‘계’를 담는 분류 컬럼(C1_NM 등)을 찾지 못했습니다.")
    
    # 3) 계만 필터
    df2 = df[df[group_col].astype(str).str.strip().eq("계")].copy()

    # 4) 필요한 항목만 필터 
    df2[item_col] = df2[item_col].astype(str).str.strip()
    pat = "경제활동인구|비경제활동인구|취업자|실업자|경제활동참가율|실업률|고용률"
    df2 = df2[df2[item_col].str.contains(pat, na=False)].copy()

    # 5) 타입 정리
    df2[value_col] = pd.to_numeric(df2[value_col], errors="coerce")
    df2[date_col] = df2[date_col].astype(str).str.strip()

    # 6) 날짜 정리
    if df2[date_col].str.len().iloc[0] == 6:
        df2["date"] = pd.to_datetime(df2[date_col], format="%Y%m", errors="coerce").dt.strftime("%Y-%m")
    else:
        df2["date"] = pd.to_datetime(df2[date_col], format="%Y", errors="coerce").dt.strftime("%Y")

    # 7) 피벗으로 행, 열 원하는 형식으로 정리
    wide = (
        df2.pivot_table(index="date", columns=item_col, values=value_col, aggfunc="first")
           .sort_index()
    )

    # 8) 항목명 정규화
    wide = wide.rename(columns=normalize_item)

    # 9) 컬럼 선택
    wanted_cols = ["경제활동인구", "비경제활동인구", "취업자", "실업자", "실업률", "고용률", "경제활동참가율"]
    final_cols = [c for c in wanted_cols if c in wide.columns]
    wide = wide[final_cols]

    wide = wide.reset_index()  # date를 컬럼으로

    # 10) 저장 (latest_날짜 파일 1개만 유지)
    base_path = PROJECT_ROOT / cfg["output_csv"] 
    ensure_parent_dir(base_path)
    out_csv = replace_latest_dated_file(base_path) # 기존 파일 없애고 새 파일로 대체한다 

    wide.to_csv(out_csv, index=False, encoding="utf-8-sig")

    # 11) metadata 기록
    key = cfg.get("metadata_key", "labor_force")
    update_meta(METADATA_PATH, key, {
        "saved_file": out_csv,
        "source_url": url,
        "rows": int(wide.shape[0]),
        "max_date": wide["date"].max() if not wide.empty else None,
    })

    print("✅ Labor_Force 저장:", out_csv, "rows:", len(wide), "max_date:", (wide["date"].max() if not wide.empty else None))
    return {
        "saved_to": out_csv,
        "rows": int(wide.shape[0]),
        "max_date": wide["date"].max() if not wide.empty else None,
    } 

def working_index_run(cfg: dict):
    start_ym = cfg.get("start_ym", "202001")
    end_ym = cfg.get("end_ym")  # 없으면 오늘 기준 YYYYMM
    if not end_ym:
        today = dt.date.today()
        end_ym = f"{today.year:04d}{today.month:02d}"

    
    raw = fetch_kosis_by_6m(
        openapi_url=cfg["openapi_url"],
        start_ym=start_ym,
        end_ym=end_ym,
        fetch_to_df=fetch_to_df,
        sleep_s=0.3
    ) # 40000셀 제한으로 인해 6개월 단위로 끊어서 데이터를 가져옵니다
    
    
    
    raw.columns = raw.columns.astype(str).str.strip()
    raw = raw[raw["C2_NM"] == "전규모(1인이상)"].copy() # 계 데이터만 불러옵니다 

    date_col = "PRD_DE"
    item_col= "ITM_NM"
    value_col = "DT"
    
    wanted = ["전체임금총액", "전체근로일수", "전체근로시간"]
    raw = raw[raw[item_col].isin(wanted)].copy()

    raw[value_col] = pd.to_numeric(raw[value_col], errors="coerce")
    raw[date_col] = raw[date_col].astype(str).str.strip()
    

    wide = (
        raw.pivot_table(index=date_col, columns=item_col, values=value_col, aggfunc="first")
          .sort_index()
    )
    wide = wide[[c for c in wanted if c in wide.columns]].reset_index()
    wide = wide.rename(columns={date_col: "date"})
    wide["date"] = pd.to_datetime(wide["date"], format="%Y%m").dt.strftime("%Y-%m")

    
    # 3) 저장
    out_csv = PROJECT_ROOT / cfg["output_csv"]
    ensure_parent_dir(out_csv)
    # 1) 이전 latest_날짜 파일 제거 +  파일 경로 생성
    out_csv = replace_latest_dated_file(out_csv)
    wide.to_csv(out_csv, index=False, encoding="utf-8-sig")

    # 4) metadata 기록
    key = cfg.get("metadata_key", "working_index")
    update_meta(METADATA_PATH, key, {
        "saved_file": out_csv,
        "source_url": cfg["openapi_url"],
        "rows": int(wide.shape[0]),
        "max_date": wide["date"].max() if not wide.empty else None,
    })

    print("✅ Working_Index 저장:", out_csv, "rows:", len(wide), "max_date:", wide["date"].max() if not wide.empty else None) 
    


def resident_population_run(cfg: dict):
    start_ym = str(cfg.get("start_ym", "200801")).strip()
    end_ym = cfg.get("end_ym")  # 없으면 오늘 기준 YYYYMM
    if not end_ym:
        today = dt.date.today()
        end_ym = f"{today.year:04d}{today.month:02d}"
    end_ym = str(end_ym).strip()

    # raw 로딩
    raw = fetch_kosis_by_6m(
        openapi_url=cfg["openapi_url"],
        start_ym=start_ym,
        end_ym=end_ym,
        fetch_to_df=fetch_to_df,
        sleep_s=0.3
    ) # 40000셀 제한으로 인해 6개월 단위로 끊어서 데이터를 가져옵니다
    
    
    # 전처리
    raw.columns = raw.columns.astype(str).str.strip()

    # 전국 데이터만
    #raw["C1_NM"] = raw["C1_NM"].astype(str).str.strip()
    #raw = raw[raw["C1_NM"] == "전국"].copy()

    # 필요한 컬럼 체크
    need = ["PRD_DE", "ITM_NM", "C2_NM", "DT"]
    miss = [c for c in need if c not in raw.columns]

    # 문자열 정리 + 값 숫자화
    for c in ["PRD_DE", "ITM_NM", "C2_NM"]:
        raw[c] = raw[c].astype(str).str.strip()
    raw["DT"] = pd.to_numeric(raw["DT"], errors="coerce")

    # 총인구수만 사용
    raw = raw[raw["ITM_NM"] == "총인구수"].copy()

    # 연령 '계' 제거(있으면)
    raw = raw[raw["C2_NM"] != "계"].copy()
    
    # 연령 파싱: "0세" -> 0, "100세 이상" -> 100
    def parse_age(s: str):
        s = str(s)
        m = re.search(r"(\d+)", s)
        return int(m.group(1)) if m else None

    raw["age"] = raw["C2_NM"].apply(parse_age)
    raw = raw.dropna(subset=["age"]).copy()
    raw["age"] = raw["age"].astype(int)
    
    # 월별(YYYYMM)로 연령대 합계 + 총인구(분모: 연령합)
    def agg(g: pd.DataFrame) -> pd.Series:
        return pd.Series({
            "총인구수": g["DT"].sum(),
            "pop_0_14": g.loc[g["age"].between(0, 14), "DT"].sum(),
            "pop_15_64": g.loc[g["age"].between(15, 64), "DT"].sum(),
            "pop_65p": g.loc[g["age"] >= 65, "DT"].sum(),
        })

    out = raw.groupby("PRD_DE").apply(agg).reset_index().sort_values("PRD_DE")

    # 구성비(%)
    out["0~14세 구성비"] = out["pop_0_14"] / out["총인구수"] * 100
    out["15~64세 구성비"] = out["pop_15_64"] / out["총인구수"] * 100
    out["고령인구비율"] = out["pop_65p"] / out["총인구수"] * 100
    
    out = out.drop(columns=["pop_0_14", "pop_15_64", "pop_65p"])

    # 날짜 포맷 정리 (YYYYMM -> YYYY-MM)
    out = out.rename(columns={"PRD_DE": "date"})
    out["date"] = pd.to_datetime(out["date"], format="%Y%m").dt.strftime("%Y-%m")

    out.reset_index()
    # 저장 

    out_csv = PROJECT_ROOT / cfg["output_csv"]
    ensure_parent_dir(out_csv)
    out_csv = replace_latest_dated_file(out_csv)
    out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    # 메타데이터 기록
    key = cfg.get("metadata_key", "resident_population")
    update_meta(METADATA_PATH, key, {
        "saved_file": out_csv,
        "source_url": cfg.get("openapi_url"),
        "rows": int(out.shape[0]),
        "max_date": out["date"].max() if not out.empty else None,
    })
    
    print("✅ Resident_Population 저장:", out_csv, "rows:", len(out), "max_date:", out["date"].max())
    


COLLECTOR_MAP = {
    "cpi": cpi_run,
    "consumer_price_change_index": consumer_price_change_index_run,
    "average_working_day": average_working_day_run,
    "aver_mid_age": aver_mid_age_run,
    "loan": loan_run,
    "gdp_gni": gdp_gni_run,
    "labor_force": labor_force_run,
    "working_index": working_index_run,
    "resident_population": resident_population_run,
}
# ============================================================
# 📦 concat_database
# ============================================================
def find_min_data(metadata_path = METADATA_PATH):
    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    max_dates =[]
    for k,v in meta.items():
        if "max_date" in v and v["max_date"]:
            max_dates.append(pd.to_datetime(v["max_date"],format="%Y-%m",errors="raise"))
    common_min_date = min(max_dates)
    #print("기준 월",common_min_date)
    return common_min_date 

def load_and_trim_monthly(csv_path, start_date, end_date, date_col="date"):
    df = pd.read_csv(csv_path)

    # 1) 날짜 → Timestamp (혼합 포맷 안전)
    df[date_col] = pd.to_datetime(df[date_col], format="mixed", errors="raise")

    start_date = pd.to_datetime(start_date, format="mixed")
    end_date = pd.to_datetime(end_date, format="mixed")

    # 2) 기간 필터링 (Timestamp끼리 비교)
    df = df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]

    # 3) 최종 포맷 통일 (문자열로 바꾸는 건 마지막에)
    df[date_col] = df[date_col].dt.strftime("%Y-%m")

    return df.sort_values(date_col).reset_index(drop=True)

def merge_all_monthly_from_metadata(metadata_path = METADATA_PATH, start_date="2020-01", date_col="date"):
    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    dfs = []
    common_min_date = find_min_data()
    for key, info in meta.items():
        if key == "suicide_base_data":
            continue
        csv_path = info["saved_file"]

        df = load_and_trim_monthly(
            csv_path=csv_path,
            start_date=start_date,
            end_date=common_min_date,
            date_col=date_col
        ) # start ~ end 기간으로 데이터를 다 자른다 
        dfs.append(df)

    # inner join: 공통 기간만 남김
    df_merged = dfs[0]
    for df in dfs[1:]:
        df_merged = df_merged.merge(df, on=date_col, how="inner")

    return df_merged.sort_values(date_col).reset_index(drop=True)

def concat_database_run(cfg: dict):
    start_date = cfg.get("start_date", "2020-01")

    # 템플릿은 문자열로 먼저 format
    output_csv_tpl = cfg["output_csv"].format(max_year="{max_year}")  # 안전장치 (이미 {max_year}가 있다면 그대로)
    metadata_key = cfg.get("metadata_key", "suicide_base_data")

    df = merge_all_monthly_from_metadata(start_date=start_date)

    max_year = pd.to_datetime(df["date"]).dt.year.max()

    # 🔥 파일명 동적 치환 (문자열 → Path)
    rel_path = cfg["output_csv"].format(max_year=max_year)
    out_csv = PROJECT_ROOT / rel_path

    # 3) 저장 (디렉터리 생성 → latest 날짜 파일로 교체)
    ensure_parent_dir(out_csv)
    out_csv = replace_latest_dated_file(out_csv)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    # 4) metadata 기록 (🔥 Timestamp → 문자열 변환)
    max_date_str = (
        pd.to_datetime(df["date"]).max().strftime("%Y-%m")
        if not df.empty else None
    )

    update_meta(METADATA_PATH, metadata_key, {
        "saved_file": out_csv,
        "rows": int(df.shape[0]),
        "max_date": max_date_str,     # JSON 직렬화 안전
        "start_date": start_date,     # 문자열  
    })

    print(
        "✅ Suicide_Base_Data 저장:",
        out_csv,
        "rows:", len(df),
        "max_date:", max_date_str,
    )
    """
    start_date = cfg.get("start_date", "2020-01")
    
    output_csv_tpl = PROJECT_ROOT / cfg["output_csv"]            # "../data/suicide_base_data_2020_{max_year}.csv"
    metadata_key = cfg.get("metadata_key", "suicide_base_data")

    df = merge_all_monthly_from_metadata(start_date=start_date)

    max_year = pd.to_datetime(df["date"]).dt.year.max()

    # 🔥 파일명 동적 치환
    out_csv = output_csv_tpl.format(max_year=max_year)

    # 3) 저장 (기존 collector 스타일 그대로)
    ensure_parent_dir(out_csv)
    out_csv = replace_latest_dated_file(out_csv)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    # 4) metadata 기록 (🔥 Timestamp → 문자열 변환)
    max_date_str = (
        pd.to_datetime(df["date"]).max().strftime("%Y-%m")
        if not df.empty else None
    )

    update_meta(METADATA_PATH, metadata_key, {
        "saved_file": out_csv,
        "rows": int(df.shape[0]),
        "max_date": max_date_str,     # ✅ JSON 직렬화 안전
        "start_date": start_date,     # 문자열  
    })

    print(
        "✅ Suicide_Base_Data 저장:",
        out_csv,
        "rows:", len(df),
        "max_date:", max_date_str,
    )
    """
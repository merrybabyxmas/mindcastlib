# crawling_pipeline.py
import sys
import yaml
import logging
from datetime import datetime
from pathlib import Path

import mindcastlib.src.crawling_utils as utils  # utils.py 한 파일 통합 버전

def log(level: str, msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] | {level:<5} | {msg}")

def run_collectors(collectors_cfg: dict):
    """
    collectors_cfg 예:
    {
        "cpi": {...},
        "loan": {...},
        ...
        "concat_database": {...}
    }
    collectors를 모두 실행합니다 
    """
    for name, cfg in collectors_cfg.items():
        if name == "concat_database":
            continue  # 마지막에 따로 실행

        if name not in utils.COLLECTOR_MAP:
            log("WARN", f"⚠️ 등록되지 않은 collector: {name} (skip)")
            continue

        try:
            log("INFO", f"▶️ Running collector: {name}")
            utils.COLLECTOR_MAP[name](cfg)
            log("INFO", f"✅ Done: {name}")
        except Exception as e:
            log("ERROR", f"❌ {name} 실패: {e}")
            raise


def run_concat_database(cfg: dict | None):
    if not cfg:
        log("INFO", "ℹ️ concat_database 설정이 없어 스킵합니다.")
        return

    try:
        log("INFO", "▶️ Running concat_database")
        utils.concat_database_run(cfg)
        log("INFO", "✅ Done: concat_database")
    except Exception as e:
        log("ERROR", f"❌ concat_database 실패: {e}")
        raise


def main():
    if len(sys.argv) < 2:
        log("ERROR", "❌ 사용법: python pipeline.py ../configs/crawling_config.yaml")
        sys.exit(1)

    config_path = Path(sys.argv[1])
    if not config_path.exists():
        log("ERROR", f"❌ config 파일이 존재하지 않습니다: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    collectors_cfg = config.get("collectors")
    if not collectors_cfg:
        raise ValueError("crawling_config.yaml 에 collectors 항목이 없습니다.")

    log("INFO", "🚀 Crawling pipeline started")

    # 1️⃣ 개별 collector 실행
    run_collectors(collectors_cfg)

    # 2️⃣ concat_database 실행
    run_concat_database(collectors_cfg.get("concat_database"))

    log("INFO", "🎉 Pipeline finished successfully")


if __name__ == "__main__":
    main()
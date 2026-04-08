from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from retrieval.index import DEFAULT_CACHE_DIR, DEFAULT_JOBS_DIR, DEFAULT_MODULES_CSV, MODEL_NAME, build_index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build retrieval artifacts for the chat app.")
    parser.add_argument("--cache-dir", default=str(DEFAULT_CACHE_DIR))
    parser.add_argument("--modules-csv", default=str(DEFAULT_MODULES_CSV))
    parser.add_argument("--jobs-dir", default=str(DEFAULT_JOBS_DIR))
    parser.add_argument("--model-name", default=MODEL_NAME)
    parser.add_argument("--force", action="store_true", help="Rebuild all artifacts from scratch.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_index(
        cache_dir=args.cache_dir,
        modules_csv=args.modules_csv,
        jobs_dir=args.jobs_dir,
        model_name=args.model_name,
        force=args.force,
    )
    print("Index ready:")
    for key, value in summary.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()

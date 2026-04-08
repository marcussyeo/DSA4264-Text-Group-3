from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from retrieval.index import DEFAULT_CACHE_DIR, MODEL_NAME
from retrieval.server import serve


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the retrieval API service.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--cache-dir", default=str(DEFAULT_CACHE_DIR))
    parser.add_argument("--model-name", default=MODEL_NAME)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    serve(
        host=args.host,
        port=args.port,
        cache_dir=args.cache_dir,
        model_name=args.model_name,
    )


if __name__ == "__main__":
    main()

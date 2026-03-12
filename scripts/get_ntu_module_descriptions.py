"""
Fetches course descriptions for each NTU module by scraping the NTUMods
website and appends a 'description' column to the existing module CSV.

Reads from:  data/ntu_mods_<date>.csv  (code, name, academic_units)
Writes to:   data/ntu_mods_with_description.csv

Uses a thread pool for parallel fetching. Writes are protected by a lock so
rows are never interleaved. Supports resuming: already-fetched codes in the
output file are skipped on re-run.

Usage:
    python scripts/get_ntu_module_descriptions.py \
        [--input   data/ntu_mods_2026-03-12.csv] \
        [--output  data/ntu_mods_with_description.csv] \
        [--workers 10]
"""

from __future__ import annotations

import argparse
import csv
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE_URL = "https://www.ntumods.org/mods/{code}?_rsc=aspwg"

DEFAULT_INPUT = "data/ntu_mods_2026-03-12.csv"
DEFAULT_OUTPUT = "data/ntu_mods_with_description.csv"
DEFAULT_WORKERS = 10

CSV_COLUMNS = ["code", "name", "academic_units", "description"]

REQUEST_DELAY = 0.5      # seconds each worker waits between its own requests
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF = 3.0      # seconds; multiplied by attempt number on each retry

# One shared session per thread avoids connection-pool contention.
_thread_local = threading.local()


def get_session() -> requests.Session:
    if not hasattr(_thread_local, "session"):
        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
        })
        _thread_local.session = session
    return _thread_local.session


def fetch_description(code: str) -> tuple[str, str]:
    """Return (code, description). description is empty string on failure."""
    url = BASE_URL.format(code=code)
    session = get_session()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(url, timeout=REQUEST_TIMEOUT)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                tqdm.write(f"Rate limited on {code}. Waiting {retry_after}s...")
                time.sleep(retry_after)
                continue

            if response.status_code == 404:
                return code, ""

            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            meta = soup.find("meta", attrs={"name": "description"})
            description = meta["content"].strip() if meta and meta.get("content") else ""
            time.sleep(REQUEST_DELAY)
            return code, description

        except requests.RequestException as exc:
            if attempt == MAX_RETRIES:
                tqdm.write(f"Failed to fetch {code} after {MAX_RETRIES} attempts: {exc}")
                return code, ""
            wait = RETRY_BACKOFF * attempt
            tqdm.write(f"Error fetching {code} (attempt {attempt}/{MAX_RETRIES}): {exc}. Retrying in {wait}s...")
            time.sleep(wait)

    return code, ""


def load_input(input_path: str) -> list[dict]:
    with open(input_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_seen_codes(output_path: str) -> set[str]:
    if not os.path.isfile(output_path):
        return set()
    with open(output_path, newline="", encoding="utf-8") as f:
        return {row["code"] for row in csv.DictReader(f)}


def main(input_path: str, output_path: str, workers: int) -> None:
    modules = load_input(input_path)
    print(f"Loaded {len(modules)} modules from '{input_path}'.")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    seen_codes = load_seen_codes(output_path)
    if seen_codes:
        print(f"Resuming — {len(seen_codes)} modules already saved in '{output_path}'.")

    # Build a lookup so workers can retrieve name/academic_units by code.
    module_by_code = {m["code"]: m for m in modules}
    pending = [m for m in modules if m["code"] not in seen_codes]
    print(f"{len(pending)} modules left to fetch ({workers} workers).")

    file_exists = os.path.isfile(output_path)
    csv_file = open(output_path, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
    write_lock = threading.Lock()

    if not file_exists:
        writer.writeheader()
        csv_file.flush()

    try:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(fetch_description, m["code"]): m["code"]
                for m in pending
            }
            with tqdm(total=len(futures), desc="Fetching descriptions") as pbar:
                for future in as_completed(futures):
                    code, description = future.result()
                    module = module_by_code[code]
                    with write_lock:
                        writer.writerow({
                            "code": code,
                            "name": module["name"],
                            "academic_units": module["academic_units"],
                            "description": description,
                        })
                        csv_file.flush()
                    pbar.update(1)
    finally:
        csv_file.close()

    total = len(seen_codes) + len(pending)
    print(f"Done. '{output_path}' now contains {total} modules.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch NTU module descriptions to CSV.")
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT,
        help=f"Input CSV file (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output CSV file (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Number of parallel workers (default: {DEFAULT_WORKERS})",
    )
    args = parser.parse_args()
    main(args.input, args.output, args.workers)

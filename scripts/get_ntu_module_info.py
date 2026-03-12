"""
Fetches NTU module information via the NTUMods API and outputs a CSV file
with one row per module. Writes incrementally after each page so no data is
lost if the script fails mid-run.

API reference: https://backend.ntumods.org/courses/
Usage:
    python scripts/get_ntu_module_info.py [--output data/ntu_mods_YYYY-MM-DD.csv]
"""

from __future__ import annotations

import argparse
import csv
import os
import time
from datetime import date

import requests
from tqdm import tqdm

BASE_URL = "https://backend.ntumods.org/courses/"
DEFAULT_OUTPUT = f"data/ntu_mods_{date.today().isoformat()}.csv"

CSV_COLUMNS = ["code", "name", "academic_units"]

REQUEST_DELAY = 0.5  # seconds between page requests to avoid rate limiting
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # seconds; doubled on each successive retry


def fetch_page(session: requests.Session, page: int) -> dict:
    params = {
        "page": page,
        "academic_units__gte": 0,
        "academic_units__lte": 8,
        "level__in": "",
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                print(f"\nRate limited. Waiting {retry_after}s before retrying...")
                time.sleep(retry_after)
                continue
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"Failed to fetch page {page} after {MAX_RETRIES} attempts: {exc}") from exc
            wait = RETRY_BACKOFF * attempt
            print(f"\nError on page {page} (attempt {attempt}/{MAX_RETRIES}): {exc}. Retrying in {wait}s...")
            time.sleep(wait)


def main(output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    file_exists = os.path.isfile(output_path)
    seen_codes: set[str] = set()

    # Resume support: read already-scraped codes so a re-run skips written rows.
    if file_exists:
        with open(output_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                seen_codes.add(row["code"])
        print(f"Resuming — {len(seen_codes)} modules already saved in '{output_path}'.")

    csv_file = open(output_path, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
    if not file_exists:
        writer.writeheader()
        csv_file.flush()

    session = requests.Session()
    session.headers.update({"Accept": "application/json"})

    # Discover total page count from the first response.
    print("Fetching page 1 to discover total pages...")
    first_page = fetch_page(session, page=1)
    total_pages: int = first_page["total_pages"]
    total_modules: int = first_page["count"]
    print(f"Found {total_modules} modules across {total_pages} pages.")

    new_rows = 0
    try:
        for page in tqdm(range(1, total_pages + 1), desc="Scraping pages"):
            if page == 1:
                data = first_page
            else:
                time.sleep(REQUEST_DELAY)
                data = fetch_page(session, page=page)

            for item in data.get("results", []):
                code = item.get("code", "")
                if code in seen_codes:
                    continue
                writer.writerow({
                    "code": code,
                    "name": item.get("name", ""),
                    "academic_units": item.get("academic_units", ""),
                })
                seen_codes.add(code)
                new_rows += 1

            csv_file.flush()

    finally:
        csv_file.close()

    print(f"Done. {new_rows} new modules written to '{output_path}' ({len(seen_codes)} total).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch NTU module info to CSV.")
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output CSV file path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()
    main(args.output)

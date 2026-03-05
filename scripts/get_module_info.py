"""
Fetches NUSMods module information via the NUSMods API v2 and outputs a
cleaned CSV file with one row per module.

API reference: https://api.nusmods.com/v2/
Usage:
    python scripts/get_module_info.py [--year 2024-2025] [--output data/modules.csv]
"""

from __future__ import annotations

import argparse
import csv
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from tqdm import tqdm

BASE_URL = "https://api.nusmods.com/v2"
DEFAULT_YEAR = "2024-2025"
DEFAULT_OUTPUT = "data/modules.csv"
MAX_WORKERS = 20

CSV_COLUMNS = [
    "moduleCode",
    "title",
    "acadYear",
    "faculty",
    "department",
    "moduleCredit",
    "description",
    "additionalInformation",
    "workload",
    "gradingBasisDescription",
    "preclusion",
    "prerequisite",
    "corequisite",
    "semestersOffered",
]


def fetch_module_list(year: str) -> list[dict]:
    url = f"{BASE_URL}/{year}/moduleList.json"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_module_detail(year: str, module_code: str) -> dict | None:
    url = f"{BASE_URL}/{year}/modules/{module_code}.json"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def flatten_module(detail: dict) -> dict:
    workload = detail.get("workload")
    if isinstance(workload, list):
        workload_str = "/".join(str(w) for w in workload)
    else:
        workload_str = str(workload) if workload is not None else ""

    semesters = [
        str(s["semester"])
        for s in detail.get("semesterData", [])
    ]

    return {
        "moduleCode": detail.get("moduleCode", ""),
        "title": detail.get("title", ""),
        "acadYear": detail.get("acadYear", ""),
        "faculty": detail.get("faculty", ""),
        "department": detail.get("department", ""),
        "moduleCredit": detail.get("moduleCredit", ""),
        "description": detail.get("description", "").strip(),
        "additionalInformation": detail.get("additionalInformation", "").strip(),
        "workload": workload_str,
        "gradingBasisDescription": detail.get("gradingBasisDescription", ""),
        "preclusion": detail.get("preclusion", ""),
        "prerequisite": detail.get("prerequisite", ""),
        "corequisite": detail.get("corequisite", ""),
        "semestersOffered": ",".join(semesters),
    }


def main(year: str, output_path: str) -> None:
    print(f"Fetching module list for {year}...")
    module_list = fetch_module_list(year)
    print(f"Found {len(module_list)} modules.")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    rows: list[dict] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(fetch_module_detail, year, m["moduleCode"]): m["moduleCode"]
            for m in module_list
        }
        for future in tqdm(as_completed(futures), total=len(futures), desc="Fetching modules"):
            detail = future.result()
            if detail:
                rows.append(flatten_module(detail))

    rows.sort(key=lambda r: r["moduleCode"])

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} modules to '{output_path}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch NUSMods module info to CSV.")
    parser.add_argument(
        "--year",
        default=DEFAULT_YEAR,
        help=f"Academic year in YYYY-YYYY format (default: {DEFAULT_YEAR})",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output CSV file path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()
    main(args.year, args.output)

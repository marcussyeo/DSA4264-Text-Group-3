from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup


def strip_html(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return ""
    soup = BeautifulSoup(text, "html.parser")
    clean = soup.get_text(separator=" ")
    return re.sub(r"\s+", " ", clean).strip()


def extract_level(code: str) -> int:
    digits = re.search(r"(\d)", str(code))
    return int(digits.group(1)) if digits else 9


def parse_job_file(path: Path) -> dict[str, object] | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except Exception:
        return None

    meta = raw.get("metadata", {}) or {}
    salary = raw.get("salary", {}) or {}
    salary_type = (salary.get("type") or {}).get("salaryType", "")

    skills_raw = raw.get("skills", []) or []
    skills_list = [item["skill"] for item in skills_raw if isinstance(item, dict) and item.get("skill")]

    categories_raw = raw.get("categories", []) or []
    categories_list = [
        item["category"] for item in categories_raw if isinstance(item, dict) and item.get("category")
    ]

    position_levels_raw = raw.get("positionLevels", []) or []
    position_levels = [
        item["position"] for item in position_levels_raw if isinstance(item, dict) and item.get("position")
    ]

    employment_types_raw = raw.get("employmentTypes", []) or []
    employment_types = [
        item["employmentType"]
        for item in employment_types_raw
        if isinstance(item, dict) and item.get("employmentType")
    ]

    return {
        "job_id": meta.get("jobPostId", path.stem),
        "title": raw.get("title", ""),
        "description_raw": raw.get("description", "") or "",
        "description_clean": strip_html(raw.get("description", "") or ""),
        "skills": skills_list,
        "skills_str": ", ".join(skills_list),
        "categories": categories_list,
        "categories_str": ", ".join(categories_list),
        "position_levels": position_levels,
        "employment_types": employment_types,
        "ssoc_code": raw.get("ssocCode", ""),
        "salary_min": salary.get("minimum"),
        "salary_max": salary.get("maximum"),
        "salary_type": salary_type,
        "company": (raw.get("postedCompany") or {}).get("name", ""),
        "posted_date": meta.get("newPostingDate", ""),
        "expiry_date": meta.get("expiryDate", ""),
        "job_url": meta.get("jobDetailsUrl", ""),
    }


def build_modules_dataframe(modules_csv: Path) -> pd.DataFrame:
    modules_raw = pd.read_csv(modules_csv)
    modules = modules_raw.copy()

    modules["description_clean"] = modules["description"].fillna("").apply(strip_html)
    modules["module_text"] = (
        modules["title"].fillna("").astype(str) + ". " + modules["description_clean"].astype(str)
    ).str.strip(". ")
    modules["level"] = modules["moduleCode"].apply(extract_level)
    modules["is_undergrad"] = modules["level"].between(1, 4)

    modules_clean = modules[
        modules["is_undergrad"] & modules["description_clean"].str.len().gt(20)
    ].copy()
    modules_clean["moduleCredit"] = pd.to_numeric(modules_clean["moduleCredit"], errors="coerce").fillna(0)
    modules_clean.sort_values("moduleCode", inplace=True)
    modules_clean.reset_index(drop=True, inplace=True)
    return modules_clean


def build_degree_profiles(modules_clean: pd.DataFrame, min_modules_per_degree: int, max_words: int) -> pd.DataFrame:
    def build_profile_text(group: pd.DataFrame) -> str:
        texts = group.sort_values("moduleCredit", ascending=False)["module_text"].tolist()
        result: list[str] = []
        word_count = 0

        for text in texts:
            words = text.split()
            if word_count + len(words) > max_words:
                remaining = max_words - word_count
                if remaining > 10:
                    result.append(" ".join(words[:remaining]))
                break
            result.append(text)
            word_count += len(words)

        return " ".join(result)

    filtered = modules_clean.groupby(["faculty", "department"]).filter(
        lambda group: len(group) >= min_modules_per_degree
    )

    degree_profiles = (
        filtered.groupby(["faculty", "department"], as_index=False)
        .apply(lambda group: pd.Series({"profile_text": build_profile_text(group)}))
        .reset_index(drop=True)
    )
    degree_profiles["word_count"] = degree_profiles["profile_text"].str.split().str.len()
    degree_profiles["degree_label"] = degree_profiles["department"]
    degree_profiles.reset_index(drop=True, inplace=True)
    return degree_profiles


def build_jobs_dataframe(jobs_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for path in sorted(jobs_dir.glob("*.json")):
        parsed = parse_job_file(path)
        if parsed is not None:
            rows.append(parsed)

    jobs = pd.DataFrame(rows)
    if jobs.empty:
        return jobs

    jobs["job_text"] = (jobs["title"].fillna("") + ". " + jobs["description_clean"].fillna("")).str.strip(". ")
    jobs = jobs[jobs["description_clean"].str.len().gt(30)].drop_duplicates("job_id").copy()
    jobs.sort_values("job_id", inplace=True)
    jobs.reset_index(drop=True, inplace=True)
    return jobs

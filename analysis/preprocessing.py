from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


LIST_COLUMNS = ["skills", "categories", "position_levels", "employment_types"]
SEMANTIC_DEDUP_SIM_THRESHOLD = 0.985
MAX_SEMANTIC_BLOCK_SIZE = 40


def strip_html(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return ""
    soup = BeautifulSoup(text, "html.parser")
    clean = soup.get_text(separator=" ")
    return re.sub(r"\s+", " ", clean).strip()


def extract_level(code: str) -> int:
    digits = re.search(r"(\d)", str(code))
    return int(digits.group(1)) if digits else 9


def listify_text_values(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, (list, tuple, set, np.ndarray, pd.Series)):
        return [str(item).strip() for item in value if pd.notna(item) and str(item).strip()]
    return []


def truncate_words(text: str, max_words: int) -> str:
    words = str(text or "").split()
    return " ".join(words[:max_words])


def build_structured_job_text(row: pd.Series, max_desc_words: int = 120) -> str:
    parts = [str(row.get("title", "") or "").strip()]
    categories = listify_text_values(row.get("categories", []))
    skills = listify_text_values(row.get("skills", []))
    if categories:
        parts.append(f"Categories: {', '.join(categories)}.")
    if skills:
        parts.append(f"Skills: {', '.join(skills)}.")
    description = truncate_words(row.get("description_clean", ""), max_desc_words)
    if description:
        parts.append(description)
    return " ".join(part for part in parts if part).strip()


def ensure_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set, np.ndarray)):
        return [item for item in value if pd.notna(item)]
    if pd.isna(value):
        return []
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return parsed
        except (SyntaxError, ValueError):
            pass
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def normalise_job_field(text: str) -> str:
    text = strip_html(str(text or "")).lower()
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def classify_role_scope(row: pd.Series) -> str:
    title = normalise_job_field(row.get("title", ""))
    company = normalise_job_field(row.get("company", ""))
    categories = normalise_job_field(" ".join(row.get("categories", []) or []))
    position_levels = normalise_job_field(" ".join(row.get("position_levels", []) or []))
    employment_types = normalise_job_field(" ".join(row.get("employment_types", []) or []))
    scope_text = " ".join([title, company, categories, position_levels, employment_types])

    if re.search(r"\b(intern(ship)?|industrial attachment|student assistant)\b", scope_text):
        return "exclude_internship"
    if re.search(r"\b(professor|postdoctoral?|research fellow|academic|dean|faculty)\b", scope_text):
        return "exclude_academia"
    if re.search(r"\b(tuition|tutor|teacher|lecturer|instructor)\b", scope_text):
        return "exclude_tuition_teaching"
    if re.search(r"\b(chief|director|vice president|president|head of|managing director|partner)\b", scope_text):
        return "exclude_very_senior"
    if "senior management" in position_levels:
        return "exclude_very_senior"
    return "in_scope"


def build_job_fingerprint(row: pd.Series) -> str:
    title_norm = normalise_job_field(row.get("title", ""))
    company_norm = normalise_job_field(row.get("company", "")) or normalise_job_field(row.get("ssoc_code", ""))
    desc_norm = normalise_job_field(row.get("description_clean", ""))
    payload = " || ".join([title_norm, company_norm, desc_norm])
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def cluster_semantic_duplicates(group: pd.DataFrame) -> pd.DataFrame:
    group = group.copy()
    n_rows = len(group)

    group["semantic_cluster_local_id"] = np.arange(n_rows)
    group["semantic_cluster_size"] = 1
    group["semantic_similarity_max"] = np.nan
    group["semantic_block_skipped"] = False

    if n_rows <= 1:
        return group
    if n_rows > MAX_SEMANTIC_BLOCK_SIZE:
        group["semantic_block_skipped"] = True
        return group

    cluster_text = (
        group["description_clean"].fillna("")
        + " Skills: "
        + group["skills_str"].fillna("")
        + " Categories: "
        + group["categories_str"].fillna("")
    ).map(normalise_job_field)

    if cluster_text.str.len().eq(0).all():
        group["semantic_block_skipped"] = True
        return group

    matrix = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1).fit_transform(cluster_text)
    sims = cosine_similarity(matrix)
    parent = list(range(n_rows))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for i in range(n_rows):
        for j in range(i + 1, n_rows):
            if sims[i, j] >= SEMANTIC_DEDUP_SIM_THRESHOLD:
                union(i, j)

    cluster_map: dict[int, int] = {}
    cluster_sizes: dict[int, int] = {}
    cluster_similarity: dict[int, float] = {}
    next_cluster_id = 0

    for i in range(n_rows):
        root = find(i)
        if root not in cluster_map:
            cluster_map[root] = next_cluster_id
            members = [member for member in range(n_rows) if find(member) == root]
            cluster_sizes[root] = len(members)
            if len(members) > 1:
                member_sims = sims[np.ix_(members, members)]
                upper = member_sims[np.triu_indices(len(members), k=1)]
                cluster_similarity[root] = float(upper.max()) if len(upper) else 1.0
            else:
                cluster_similarity[root] = np.nan
            next_cluster_id += 1

        group.iloc[i, group.columns.get_loc("semantic_cluster_local_id")] = cluster_map[root]
        group.iloc[i, group.columns.get_loc("semantic_cluster_size")] = cluster_sizes[root]
        group.iloc[i, group.columns.get_loc("semantic_similarity_max")] = cluster_similarity[root]

    return group


def parse_job_file(path: Path) -> dict | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        return None

    meta = payload.get("metadata", {})
    salary = payload.get("salary", {})
    salary_type = (salary.get("type") or {}).get("salaryType", "")

    skills_raw = payload.get("skills", []) or []
    skills_list = [item["skill"] for item in skills_raw if isinstance(item, dict) and item.get("skill")]

    categories_raw = payload.get("categories", []) or []
    categories_list = [item["category"] for item in categories_raw if isinstance(item, dict) and item.get("category")]

    position_raw = payload.get("positionLevels", []) or []
    position_levels = [item["position"] for item in position_raw if isinstance(item, dict) and item.get("position")]

    employment_raw = payload.get("employmentTypes", []) or []
    employment_types = [item["employmentType"] for item in employment_raw if isinstance(item, dict) and item.get("employmentType")]

    return {
        "job_id": meta.get("jobPostId", path.stem),
        "title": payload.get("title", ""),
        "description_raw": payload.get("description", "") or "",
        "skills": skills_list,
        "skills_str": ", ".join(skills_list),
        "categories": categories_list,
        "categories_str": ", ".join(categories_list),
        "position_levels": position_levels,
        "employment_types": employment_types,
        "ssoc_code": payload.get("ssocCode", ""),
        "salary_min": salary.get("minimum") or np.nan,
        "salary_max": salary.get("maximum") or np.nan,
        "salary_type": salary_type,
        "company": (payload.get("postedCompany") or {}).get("name", ""),
        "posted_date": meta.get("newPostingDate", ""),
        "expiry_date": meta.get("expiryDate", ""),
    }


def load_raw_jobs(jobs_dir: Path) -> tuple[pd.DataFrame, list[Path]]:
    job_files = sorted(jobs_dir.glob("*.json"))
    records = []
    for path in job_files:
        record = parse_job_file(path)
        if record:
            records.append(record)
    return pd.DataFrame(records), job_files


def clean_modules(modules_raw: pd.DataFrame) -> pd.DataFrame:
    modules = modules_raw.copy()
    modules["description_clean"] = modules["description"].apply(strip_html)
    modules["module_text"] = (modules["title"].fillna("") + ". " + modules["description_clean"]).str.strip(". ")
    modules["level"] = modules["moduleCode"].apply(extract_level)
    modules["is_undergrad"] = modules["level"].between(1, 4)
    return modules[modules["description_clean"].str.len() > 20].copy()


def build_module_profile(modules_df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "dtype": modules_df.dtypes.astype(str),
            "non_null_count": modules_df.notna().sum(),
            "missing_count": modules_df.isna().sum(),
            "missing_pct": (modules_df.isna().mean() * 100).round(2),
            "n_unique": modules_df.nunique(dropna=True),
        }
    ).sort_values(["missing_pct", "n_unique"], ascending=[False, False])


def build_jobs_summary(df: pd.DataFrame) -> pd.DataFrame:
    category_series = pd.Series([category for items in df["categories"] for category in items]) if len(df) else pd.Series(dtype=object)
    skill_series = pd.Series([skill for items in df["skills"] for skill in items]) if len(df) else pd.Series(dtype=object)
    return pd.DataFrame(
        {
            "metric": [
                "total_job_postings",
                "unique_job_titles",
                "unique_companies",
                "unique_categories",
                "total_skill_tags",
                "unique_skills",
                "median_skills_per_job",
                "jobs_without_tagged_skills",
            ],
            "value": [
                len(df),
                df["title"].nunique(),
                df["company"].nunique(),
                category_series.nunique(),
                int(df["skill_count"].sum()) if "skill_count" in df else 0,
                skill_series.nunique(),
                float(df["skill_count"].median()) if "skill_count" in df and len(df) else 0.0,
                int((df["skill_count"] == 0).sum()) if "skill_count" in df else 0,
            ],
        }
    )


def preprocess_jobs(jobs_raw: pd.DataFrame, max_desc_words: int = 120) -> dict[str, pd.DataFrame | dict]:
    jobs_candidates = jobs_raw.copy()
    jobs_candidates["description_clean"] = jobs_candidates["description_raw"].apply(strip_html)

    before = len(jobs_candidates)
    jobs_candidates = jobs_candidates[jobs_candidates["description_clean"].str.len() > 30].drop_duplicates("job_id").copy()

    for column in LIST_COLUMNS:
        if column in jobs_candidates.columns:
            jobs_candidates[column] = jobs_candidates[column].apply(ensure_list)

    jobs_candidates["job_text"] = jobs_candidates.apply(lambda row: build_structured_job_text(row, max_desc_words), axis=1)
    jobs_candidates["title_norm"] = jobs_candidates["title"].apply(normalise_job_field)
    jobs_candidates["company_norm"] = jobs_candidates["company"].apply(normalise_job_field)
    jobs_candidates["ssoc_norm"] = jobs_candidates["ssoc_code"].astype(str).apply(normalise_job_field)
    jobs_candidates["role_scope"] = jobs_candidates.apply(classify_role_scope, axis=1)
    jobs_candidates["is_target_role"] = jobs_candidates["role_scope"].eq("in_scope")
    jobs_candidates["job_fingerprint"] = jobs_candidates.apply(build_job_fingerprint, axis=1)
    jobs_candidates["posted_date_dt"] = pd.to_datetime(jobs_candidates["posted_date"], errors="coerce")

    salary_max_num = pd.to_numeric(jobs_candidates["salary_max"], errors="coerce")
    salary_min_num = pd.to_numeric(jobs_candidates["salary_min"], errors="coerce")
    jobs_candidates["salary_sort"] = salary_max_num.fillna(salary_min_num).fillna(-1)

    jobs_candidates = jobs_candidates.sort_values(
        ["job_fingerprint", "posted_date_dt", "salary_sort", "job_id"],
        ascending=[True, False, False, True],
    ).copy()

    jobs_candidates["duplicate_count"] = jobs_candidates.groupby("job_fingerprint")["job_id"].transform("size")
    jobs_candidates["duplicate_rank"] = jobs_candidates.groupby("job_fingerprint").cumcount() + 1
    jobs_candidates["is_near_duplicate"] = jobs_candidates["duplicate_count"].gt(1)
    jobs_candidates["canonical_job_id"] = jobs_candidates.groupby("job_fingerprint")["job_id"].transform("first")

    jobs_scope_audit = jobs_candidates.drop(columns=["posted_date_dt", "salary_sort"], errors="ignore").copy()
    jobs_excluded = jobs_scope_audit[~jobs_scope_audit["is_target_role"]].copy()
    jobs_exact_removed = jobs_scope_audit[jobs_scope_audit["is_target_role"] & jobs_scope_audit["duplicate_rank"].gt(1)].copy()

    jobs_for_semantic_cluster = jobs_scope_audit[jobs_scope_audit["is_target_role"] & jobs_scope_audit["duplicate_rank"].eq(1)].copy()
    jobs_for_semantic_cluster["semantic_block_key"] = jobs_for_semantic_cluster["title_norm"] + " || " + jobs_for_semantic_cluster["company_norm"].where(
        jobs_for_semantic_cluster["company_norm"].str.len() > 0,
        jobs_for_semantic_cluster["ssoc_norm"],
    )

    semantic_frames = [cluster_semantic_duplicates(group) for _, group in jobs_for_semantic_cluster.groupby("semantic_block_key", sort=False)]
    jobs_for_semantic_cluster = pd.concat(semantic_frames, ignore_index=True) if semantic_frames else jobs_for_semantic_cluster.copy()

    jobs_for_semantic_cluster["semantic_group_key"] = (
        jobs_for_semantic_cluster["semantic_block_key"]
        + " ## "
        + jobs_for_semantic_cluster["semantic_cluster_local_id"].astype(str)
    )
    jobs_for_semantic_cluster = jobs_for_semantic_cluster.sort_values(
        ["semantic_group_key", "posted_date", "job_id"],
        ascending=[True, False, True],
    ).copy()
    jobs_for_semantic_cluster["semantic_duplicate_count"] = jobs_for_semantic_cluster.groupby("semantic_group_key")["job_id"].transform("size")
    jobs_for_semantic_cluster["semantic_duplicate_rank"] = jobs_for_semantic_cluster.groupby("semantic_group_key").cumcount() + 1
    jobs_for_semantic_cluster["canonical_semantic_job_id"] = jobs_for_semantic_cluster.groupby("semantic_group_key")["job_id"].transform("first")
    jobs_for_semantic_cluster["is_semantic_near_duplicate"] = jobs_for_semantic_cluster["semantic_duplicate_count"].gt(1)

    semantic_columns = [
        "job_id",
        "semantic_block_key",
        "semantic_cluster_local_id",
        "semantic_group_key",
        "semantic_cluster_size",
        "semantic_similarity_max",
        "semantic_block_skipped",
        "semantic_duplicate_count",
        "semantic_duplicate_rank",
        "canonical_semantic_job_id",
        "is_semantic_near_duplicate",
    ]
    jobs_scope_audit = jobs_scope_audit.merge(
        jobs_for_semantic_cluster[semantic_columns],
        on="job_id",
        how="left",
        validate="one_to_one",
    )

    jobs_semantic_removed = jobs_for_semantic_cluster[jobs_for_semantic_cluster["semantic_duplicate_rank"].gt(1)].copy()
    jobs_clean = jobs_for_semantic_cluster[jobs_for_semantic_cluster["semantic_duplicate_rank"].eq(1)].copy()
    jobs_clean = jobs_clean.sort_values(["posted_date", "job_id"], ascending=[False, True]).reset_index(drop=True)

    summary = {
        "jobs_before_filtering": before,
        "jobs_after_description_filter": len(jobs_scope_audit),
        "jobs_excluded_out_of_scope": len(jobs_excluded),
        "jobs_exact_removed": len(jobs_exact_removed),
        "jobs_semantic_removed": len(jobs_semantic_removed),
        "jobs_final": len(jobs_clean),
    }

    return {
        "jobs_scope_audit": jobs_scope_audit,
        "jobs_clean": jobs_clean,
        "jobs_excluded": jobs_excluded,
        "jobs_exact_removed": jobs_exact_removed,
        "jobs_semantic_removed": jobs_semantic_removed,
        "summary": summary,
    }

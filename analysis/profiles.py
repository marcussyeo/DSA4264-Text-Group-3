from __future__ import annotations

import numpy as np
import pandas as pd


def build_module_text(row: pd.Series) -> str:
    parts = [f"{row['moduleCode']}. {row['description_clean']}"]
    if row.get("description_skills", ""):
        parts.append(f"Skills: {row['description_skills']}.")
    return " ".join(parts).strip()


def prepare_degree_modules(
    degree_map: pd.DataFrame,
    module_skills: pd.DataFrame,
    modules_clean: pd.DataFrame | None = None,
) -> pd.DataFrame:
    degree_map = degree_map.copy()
    module_skills = module_skills.copy()

    degree_map.columns = degree_map.columns.str.strip()
    module_skills.columns = module_skills.columns.str.strip()

    degree_map["moduleCode"] = degree_map["moduleCode"].astype(str).str.strip().str.upper()
    module_skills["moduleCode"] = module_skills["moduleCode"].astype(str).str.strip().str.upper()

    module_skill_cols = ["moduleCode", "title", "description_clean", "description_skills", "top_skills"]
    degree_modules = degree_map.merge(
        module_skills[module_skill_cols],
        on="moduleCode",
        how="left",
        validate="many_to_one",
    )

    if modules_clean is not None:
        fallback = modules_clean[["moduleCode", "title", "description_clean"]].copy()
        fallback["moduleCode"] = fallback["moduleCode"].astype(str).str.strip().str.upper()
        degree_modules = degree_modules.merge(
            fallback,
            on="moduleCode",
            how="left",
            suffixes=("", "_fallback"),
        )
        for column in ["title", "description_clean"]:
            fallback_column = f"{column}_fallback"
            degree_modules[column] = degree_modules[column].fillna(degree_modules[fallback_column])
            degree_modules = degree_modules.drop(columns=[fallback_column])

    for column in ["title", "description_clean", "description_skills", "top_skills"]:
        degree_modules[column] = degree_modules[column].fillna("").astype(str).str.strip()

    degree_modules["requirement_group"] = degree_modules["requirement_group"].astype(str).str.strip().str.lower()
    degree_modules["requirement_group_order"] = degree_modules["requirement_group"].map({"core": 0, "common": 1}).fillna(2)
    degree_modules["module_order"] = np.arange(len(degree_modules))
    degree_modules = degree_modules[degree_modules["description_clean"].str.len() > 0].copy()
    degree_modules["module_profile_text"] = degree_modules.apply(build_module_text, axis=1)
    return degree_modules


def build_profile_text(group: pd.DataFrame, max_words: int = 8000) -> str:
    group = group.sort_values(["requirement_group_order", "module_order"])
    result = []
    word_count = 0
    for text in group["module_profile_text"]:
        words = text.split()
        if word_count + len(words) > max_words:
            remaining = max_words - word_count
            if remaining > 10:
                result.append(" ".join(words[:remaining]))
            break
        result.append(text)
        word_count += len(words)
    return " ".join(result)


def build_degree_profiles(degree_modules: pd.DataFrame, max_words: int = 8000) -> pd.DataFrame:
    def summarise(group: pd.DataFrame) -> pd.Series:
        profile_text = build_profile_text(group, max_words=max_words)
        return pd.Series(
            {
                "profile_text": profile_text,
                "n_modules": len(group),
                "word_count": len(profile_text.split()),
            }
        )

    degree_profiles = (
        degree_modules.groupby(["degree_id", "degree_name"], as_index=False)
        .apply(summarise)
        .reset_index(drop=True)
    )
    degree_profiles["degree_label"] = degree_profiles["degree_name"]
    degree_profiles["degree_id"] = degree_profiles["degree_id"].astype(str)
    return degree_profiles


def build_degree_module_indices(degree_profiles: pd.DataFrame, degree_modules: pd.DataFrame) -> dict[str, np.ndarray]:
    degree_module_ids = degree_modules["degree_id"].astype(str).to_numpy()
    return {
        degree_id: np.flatnonzero(degree_module_ids == degree_id)
        for degree_id in degree_profiles["degree_id"].astype(str).tolist()
    }

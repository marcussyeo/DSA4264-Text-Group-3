from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd


def build_skill_vocab(jobs: pd.DataFrame) -> list[str]:
    all_skills = set()
    for skill_list in jobs["skills"]:
        if isinstance(skill_list, list):
            all_skills.update(str(skill).lower().strip() for skill in skill_list if skill)
    return sorted(all_skills, key=len, reverse=True)


def extract_skills_from_text(text: str, vocab: list[str]) -> set[str]:
    text_lower = str(text).lower()
    found = set()
    for skill in vocab:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found.add(skill)
    return found


def load_or_build_degree_skills(
    degree_profiles: pd.DataFrame,
    skill_vocab: list[str],
    cache_path,
) -> dict[str, set[str]]:
    expected_ids = set(degree_profiles["degree_id"].astype(str))
    if cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        if set(cached) == expected_ids:
            return {degree_id: set(skills) for degree_id, skills in cached.items()}

    degree_skills = {
        str(row["degree_id"]): extract_skills_from_text(row["profile_text"], skill_vocab)
        for _, row in degree_profiles.iterrows()
    }
    cache_path.write_text(
        json.dumps({degree_id: sorted(skills) for degree_id, skills in degree_skills.items()}, indent=2),
        encoding="utf-8",
    )
    return degree_skills


def job_skill_coverage(degree_skills: set[str], job_skills: set[str]) -> float:
    if not job_skills:
        return 0.0
    return len(degree_skills & job_skills) / len(job_skills)


def compute_skill_coverage_matrix(
    degree_profiles: pd.DataFrame,
    jobs: pd.DataFrame,
    degree_skills: dict[str, set[str]],
) -> np.ndarray:
    matrix = np.zeros((len(degree_profiles), len(jobs)), dtype=np.float32)
    job_skill_sets = [set(str(skill).lower().strip() for skill in skill_list if skill) for skill_list in jobs["skills"].tolist()]

    for degree_index, (_, degree_row) in enumerate(degree_profiles.iterrows()):
        skills = degree_skills.get(str(degree_row["degree_id"]), set())
        if not skills:
            continue
        for job_index, job_skills in enumerate(job_skill_sets):
            matrix[degree_index, job_index] = job_skill_coverage(skills, job_skills)
    return matrix


def build_hybrid_matrix(
    sim_matrix: np.ndarray,
    skill_coverage_matrix: np.ndarray,
    alpha: float = 0.7,
    beta: float = 0.3,
) -> np.ndarray:
    if sim_matrix.shape != skill_coverage_matrix.shape:
        raise ValueError("sim_matrix and skill_coverage_matrix must have matching shapes.")
    return (alpha * sim_matrix + beta * skill_coverage_matrix).astype(np.float32)

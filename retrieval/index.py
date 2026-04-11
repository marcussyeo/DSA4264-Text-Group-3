from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from .data import build_degree_profiles, build_jobs_dataframe, build_modules_dataframe

MODEL_NAME = "all-MiniLM-L6-v2"
MAX_WORDS_PER_PROFILE = 8000
MIN_MODULES_PER_DEGREE = 3
SKILL_SIGNAL_VERSION = "job_skill_coverage_v1"
DEFAULT_CACHE_DIR = Path("notebooks/cache")
DEFAULT_MODULES_CSV = Path("data/modules.csv")
DEFAULT_JOBS_DIR = Path("data/MyCareersFutureData")


@dataclass(slots=True)
class ArtifactPaths:
    cache_dir: Path
    model_name: str

    @property
    def model_slug(self) -> str:
        return self.model_name.replace("/", "_")

    @property
    def modules_meta(self) -> Path:
        return self.cache_dir / "modules_clean.parquet"

    @property
    def module_embeddings(self) -> Path:
        return self.cache_dir / f"module_embeddings_{self.model_slug}.npy"

    @property
    def degree_meta(self) -> Path:
        return self.cache_dir / "degree_profiles.parquet"

    @property
    def degree_embeddings(self) -> Path:
        return self.cache_dir / f"degree_embeddings_{self.model_slug}.npy"

    @property
    def jobs_meta(self) -> Path:
        return self.cache_dir / "jobs_clean.parquet"

    @property
    def job_embeddings(self) -> Path:
        return self.cache_dir / f"job_embeddings_{self.model_slug}.npy"

    @property
    def degree_skills(self) -> Path:
        return self.cache_dir / "degree_skills.json"

    @property
    def skill_overlap(self) -> Path:
        return self.cache_dir / f"skill_overlap_matrix_{SKILL_SIGNAL_VERSION}.npy"


def artifact_paths(cache_dir: Path | str = DEFAULT_CACHE_DIR, model_name: str = MODEL_NAME) -> ArtifactPaths:
    return ArtifactPaths(cache_dir=Path(cache_dir), model_name=model_name)


def _load_model(model_name: str) -> SentenceTransformer:
    print(f"Loading model: {model_name}")
    try:
        return SentenceTransformer(model_name, local_files_only=True)
    except Exception:
        return SentenceTransformer(model_name)


def _encode_texts(model: SentenceTransformer, texts: list[str], batch_size: int) -> np.ndarray:
    return model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
    ).astype(np.float32)


def _read_parquet_if_valid(path: Path, required_columns: list[str]) -> pd.DataFrame | None:
    if not path.exists():
        return None
    frame = pd.read_parquet(path)
    if all(column in frame.columns for column in required_columns):
        return frame
    return None


def _load_or_build_modules(paths: ArtifactPaths, modules_csv: Path, force: bool) -> pd.DataFrame:
    required = [
        "moduleCode",
        "title",
        "faculty",
        "department",
        "description_clean",
        "module_text",
        "moduleCredit",
    ]
    modules = None if force else _read_parquet_if_valid(paths.modules_meta, required)
    if modules is None:
        print("Preparing module metadata...")
        modules = build_modules_dataframe(modules_csv)
        modules.to_parquet(paths.modules_meta, index=False)
    return modules


def _load_or_build_degree_profiles(
    paths: ArtifactPaths,
    modules: pd.DataFrame,
    force: bool,
) -> pd.DataFrame:
    required = ["faculty", "department", "profile_text", "word_count", "degree_label"]
    degree_profiles = None if force else _read_parquet_if_valid(paths.degree_meta, required)
    if degree_profiles is None:
        print("Preparing degree profiles...")
        degree_profiles = build_degree_profiles(
            modules_clean=modules,
            min_modules_per_degree=MIN_MODULES_PER_DEGREE,
            max_words=MAX_WORDS_PER_PROFILE,
        )
        degree_profiles.to_parquet(paths.degree_meta, index=False)
    return degree_profiles


def _load_or_build_jobs(paths: ArtifactPaths, jobs_dir: Path, force: bool) -> pd.DataFrame:
    required = [
        "job_id",
        "title",
        "description_clean",
        "job_text",
        "company",
        "categories",
        "categories_str",
        "skills",
        "job_url",
    ]
    jobs = None if force else _read_parquet_if_valid(paths.jobs_meta, required)
    if jobs is None:
        print("Preparing job metadata...")
        jobs = build_jobs_dataframe(jobs_dir)
        jobs.to_parquet(paths.jobs_meta, index=False)
    return jobs


def _load_or_build_embeddings(
    model: SentenceTransformer,
    texts: list[str],
    output_path: Path,
    expected_rows: int,
    batch_size: int,
    force: bool,
) -> np.ndarray:
    if not force and output_path.exists():
        embeddings = np.load(output_path)
        if embeddings.shape[0] == expected_rows:
            return embeddings.astype(np.float32)

    embeddings = _encode_texts(model=model, texts=texts, batch_size=batch_size)
    np.save(output_path, embeddings)
    return embeddings


def _extract_degree_skills(
    degree_profiles: pd.DataFrame,
    jobs: pd.DataFrame,
    output_path: Path,
    force: bool,
) -> dict[str, set[str]]:
    if not force and output_path.exists():
        with output_path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        return {key: set(value) for key, value in raw.items()}

    all_skills = set()
    for skill_list in jobs["skills"]:
        if isinstance(skill_list, list):
            all_skills.update(skill.lower().strip() for skill in skill_list if skill)

    skill_vocab = sorted(all_skills, key=len, reverse=True)
    degree_skills: dict[str, set[str]] = {}

    import re

    def extract_skills(text: str) -> set[str]:
        text_lower = text.lower()
        found: set[str] = set()
        for skill in skill_vocab:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, text_lower):
                found.add(skill)
        return found

    for _, row in tqdm(
        degree_profiles.iterrows(),
        total=len(degree_profiles),
        desc="Degree skill extraction",
    ):
        degree_skills[row["degree_label"]] = extract_skills(row["profile_text"])

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump({key: sorted(value) for key, value in degree_skills.items()}, handle, indent=2)
    return degree_skills


def _load_or_build_skill_overlap(
    degree_profiles: pd.DataFrame,
    jobs: pd.DataFrame,
    degree_skills: dict[str, set[str]],
    output_path: Path,
    force: bool,
) -> np.ndarray:
    if not force and output_path.exists():
        overlap = np.load(output_path)
        if overlap.shape == (len(degree_profiles), len(jobs)):
            return overlap.astype(np.float32)

    def job_skill_coverage(degree_skills: set[str], job_skills: set[str]) -> float:
        if not job_skills:
            return 0.0
        return len(degree_skills & job_skills) / len(job_skills)

    job_skill_sets = [
        {skill.lower().strip() for skill in skills if skill}
        for skills in jobs["skills"].tolist()
    ]

    overlap = np.zeros((len(degree_profiles), len(jobs)), dtype=np.float32)
    for degree_pos, (_, row) in enumerate(
        tqdm(degree_profiles.iterrows(), total=len(degree_profiles), desc="Skill overlap")
    ):
        current_skills = degree_skills.get(row["degree_label"], set())
        if not current_skills:
            continue
        for job_pos, job_skills in enumerate(job_skill_sets):
            overlap[degree_pos, job_pos] = job_skill_coverage(current_skills, job_skills)

    np.save(output_path, overlap)
    return overlap


def build_index(
    cache_dir: Path | str = DEFAULT_CACHE_DIR,
    modules_csv: Path | str = DEFAULT_MODULES_CSV,
    jobs_dir: Path | str = DEFAULT_JOBS_DIR,
    model_name: str = MODEL_NAME,
    force: bool = False,
) -> dict[str, int]:
    paths = artifact_paths(cache_dir=cache_dir, model_name=model_name)
    paths.cache_dir.mkdir(parents=True, exist_ok=True)

    modules_csv = Path(modules_csv)
    jobs_dir = Path(jobs_dir)

    modules = _load_or_build_modules(paths=paths, modules_csv=modules_csv, force=force)
    degree_profiles = _load_or_build_degree_profiles(paths=paths, modules=modules, force=force)
    jobs = _load_or_build_jobs(paths=paths, jobs_dir=jobs_dir, force=force)

    model = _load_model(model_name)
    _load_or_build_embeddings(
        model=model,
        texts=modules["module_text"].tolist(),
        output_path=paths.module_embeddings,
        expected_rows=len(modules),
        batch_size=32,
        force=force,
    )
    _load_or_build_embeddings(
        model=model,
        texts=degree_profiles["profile_text"].tolist(),
        output_path=paths.degree_embeddings,
        expected_rows=len(degree_profiles),
        batch_size=16,
        force=force,
    )
    _load_or_build_embeddings(
        model=model,
        texts=jobs["job_text"].tolist(),
        output_path=paths.job_embeddings,
        expected_rows=len(jobs),
        batch_size=64,
        force=force,
    )

    degree_skills = _extract_degree_skills(
        degree_profiles=degree_profiles,
        jobs=jobs,
        output_path=paths.degree_skills,
        force=force,
    )
    _load_or_build_skill_overlap(
        degree_profiles=degree_profiles,
        jobs=jobs,
        degree_skills=degree_skills,
        output_path=paths.skill_overlap,
        force=force,
    )

    return {
        "modules": len(modules),
        "degrees": len(degree_profiles),
        "jobs": len(jobs),
    }

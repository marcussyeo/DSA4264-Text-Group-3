from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


def _find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists() or (candidate / "requirements.txt").exists():
            return candidate
    raise FileNotFoundError("Could not locate the repository root from the current working directory.")


def _slugify(value: str) -> str:
    return value.replace("/", "_").replace(" ", "_")


@dataclass(frozen=True)
class ProjectPaths:
    repo_root: Path
    data_dir: Path
    raw_dir: Path
    interim_dir: Path
    processed_dir: Path
    embeddings_dir: Path
    evaluation_dir: Path
    figures_dir: Path
    notebooks_dir: Path
    archive_dir: Path
    modules_csv: Path
    jobs_dir: Path
    degree_map_csv: Path
    module_skills_csv: Path

    def ensure_dirs(self) -> "ProjectPaths":
        for directory in [
            self.data_dir,
            self.raw_dir,
            self.interim_dir,
            self.processed_dir,
            self.embeddings_dir,
            self.evaluation_dir,
            self.figures_dir,
            self.notebooks_dir,
            self.archive_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)
        return self

    @property
    def jobs_raw_parquet(self) -> Path:
        return self.interim_dir / "jobs_raw.parquet"

    @property
    def modules_clean_parquet(self) -> Path:
        return self.interim_dir / "modules_clean.parquet"

    @property
    def jobs_scope_audit_parquet(self) -> Path:
        return self.interim_dir / "jobs_scope_audit.parquet"

    @property
    def jobs_clean_parquet(self) -> Path:
        return self.interim_dir / "jobs_clean.parquet"

    @property
    def module_profile_summary_csv(self) -> Path:
        return self.interim_dir / "eda_modules_profile.csv"

    @property
    def job_summary_csv(self) -> Path:
        return self.interim_dir / "eda_jobs_summary.csv"

    @property
    def degree_modules_parquet(self) -> Path:
        return self.processed_dir / "degree_modules.parquet"

    @property
    def degree_profiles_parquet(self) -> Path:
        return self.processed_dir / "degree_profiles.parquet"

    @property
    def degree_skills_json(self) -> Path:
        return self.processed_dir / "degree_skills.json"

    @property
    def cluster_summary_csv(self) -> Path:
        return self.processed_dir / "job_cluster_summary.csv"

    @property
    def jobs_with_clusters_parquet(self) -> Path:
        return self.processed_dir / "jobs_with_clusters.parquet"

    @property
    def degree_cluster_alignment_csv(self) -> Path:
        return self.processed_dir / "degree_cluster_alignment.csv"

    @property
    def degree_job_alignment_summary_csv(self) -> Path:
        return self.processed_dir / "degree_job_alignment_summary.csv"

    @property
    def golden_top10_csv(self) -> Path:
        return self.evaluation_dir / "golden_top10_jobs_per_degree.csv"

    @property
    def evaluation_metrics_csv(self) -> Path:
        return self.evaluation_dir / "method_metrics.csv"

    @property
    def coverage_report_json(self) -> Path:
        return self.evaluation_dir / "coverage_report.json"

    @property
    def similarity_distribution_png(self) -> Path:
        return self.figures_dir / "similarity_distributions.png"

    @property
    def degree_alignment_scores_png(self) -> Path:
        return self.figures_dir / "degree_alignment_scores.png"

    @property
    def alignment_heatmap_png(self) -> Path:
        return self.figures_dir / "alignment_heatmap.png"

    def degree_module_embeddings_npy(self, model_name: str = "all-MiniLM-L6-v2") -> Path:
        return self.embeddings_dir / f"degree_module_embeddings_{_slugify(model_name)}.npy"

    def degree_embeddings_npy(self, model_name: str = "all-MiniLM-L6-v2") -> Path:
        return self.embeddings_dir / f"degree_embeddings_{_slugify(model_name)}.npy"

    def job_embeddings_npy(self, model_name: str = "all-MiniLM-L6-v2") -> Path:
        return self.embeddings_dir / f"job_embeddings_{_slugify(model_name)}.npy"

    def similarity_matrix_npy(self, model_name: str = "all-MiniLM-L6-v2") -> Path:
        return self.embeddings_dir / f"similarity_matrix_{_slugify(model_name)}.npy"

    @property
    def skill_coverage_matrix_npy(self) -> Path:
        return self.embeddings_dir / "skill_coverage_matrix.npy"

    @property
    def hybrid_matrix_npy(self) -> Path:
        return self.embeddings_dir / "hybrid_matrix.npy"

    def cluster_labels_npy(self, n_clusters: int = 75) -> Path:
        return self.embeddings_dir / f"job_clusters_k{n_clusters}.npy"

    def degree_cluster_similarity_npy(self, n_clusters: int = 75) -> Path:
        return self.embeddings_dir / f"degree_cluster_similarity_k{n_clusters}.npy"


def build_paths(start: Path | None = None) -> ProjectPaths:
    repo_root = _find_repo_root(start)
    data_dir = repo_root / "data"
    return ProjectPaths(
        repo_root=repo_root,
        data_dir=data_dir,
        raw_dir=data_dir / "raw",
        interim_dir=data_dir / "interim",
        processed_dir=data_dir / "processed",
        embeddings_dir=data_dir / "embeddings",
        evaluation_dir=data_dir / "evaluation",
        figures_dir=data_dir / "figures",
        notebooks_dir=repo_root / "notebooks",
        archive_dir=repo_root / "notebooks" / "_archive",
        modules_csv=data_dir / "modules.csv",
        jobs_dir=data_dir / "MyCareersFutureData",
        degree_map_csv=data_dir / "degree_to_module_map.csv",
        module_skills_csv=data_dir / "nus_modules_skills_output.csv",
    ).ensure_dirs()


paths = build_paths()


def require_files(required_paths: Iterable[Path]) -> None:
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required input files:\n" + "\n".join(f"- {path}" for path in missing))


def write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

from .index import MODEL_NAME, _load_model, artifact_paths
from .types import (
    DegreeRecommendation,
    ExplorerResponse,
    JobRecommendation,
    MatchedEntity,
    ModuleRecommendation,
    SearchResponse,
)


def _canonicalize_degree_label(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value).strip().lower()
    return re.sub(r"[^a-z0-9 ]+", "", normalized)


def _normalize_module_code(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", value).upper()


def _truncate(value: str, limit: int = 220) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _coerce_list_column(frame: pd.DataFrame, column: str) -> None:
    if column not in frame.columns or frame.empty:
        return

    def parse(value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return []
        if isinstance(value, str):
            if not value.strip():
                return []
            try:
                parsed = ast.literal_eval(value)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed if str(item).strip()]
            except Exception:
                pass
            return [part.strip() for part in value.split(",") if part.strip()]
        return []

    frame[column] = frame[column].apply(parse)


def _normalize_vector(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm <= 0:
        return vector.astype(np.float32)
    return (vector / norm).astype(np.float32)


def _latest_matching_path(cache_dir: Path, pattern: str) -> Path | None:
    matches = list(cache_dir.glob(pattern))
    if not matches:
        return None
    return max(matches, key=lambda path: path.stat().st_mtime_ns)


def _first_existing(paths: list[Path | None]) -> Path | None:
    for path in paths:
        if path is not None and path.exists():
            return path
    return None


def _summarize_labels(labels: list[str], prefix: str) -> str:
    cleaned = [label for label in labels if label]
    if not cleaned:
        return prefix
    if len(cleaned) == 1:
        return f"{prefix}: {cleaned[0]}"
    if len(cleaned) == 2:
        return f"{prefix}: {cleaned[0]}, {cleaned[1]}"
    return f"{prefix}: {cleaned[0]}, {cleaned[1]} +{len(cleaned) - 2} more"


@dataclass(slots=True)
class SearchArtifacts:
    modules: pd.DataFrame
    module_embeddings: np.ndarray
    degree_profiles: pd.DataFrame
    degree_embeddings: np.ndarray
    degree_modules: pd.DataFrame | None
    jobs: pd.DataFrame
    job_embeddings: np.ndarray
    hybrid_scores: np.ndarray | None


@dataclass(slots=True)
class ResolvedArtifactPaths:
    modules_meta: Path
    module_embeddings: Path
    degree_meta: Path
    degree_embeddings: Path
    degree_modules_meta: Path | None
    jobs_meta: Path
    job_embeddings: Path
    hybrid_scores: Path | None


class SearchService:
    def __init__(self, cache_dir: Path | str = Path("notebooks/cache"), model_name: str = MODEL_NAME) -> None:
        self.cache_dir = Path(cache_dir)
        self.model_name = model_name
        self.paths = self._resolve_artifact_paths()
        self.artifacts = self._load_artifacts()

        self.module_code_to_pos = {
            _normalize_module_code(code): position
            for position, code in enumerate(self.artifacts.modules["moduleCode"])
        }
        self.degree_label_to_pos = {
            _canonicalize_degree_label(label): position
            for position, label in enumerate(self.artifacts.degree_profiles["degree_label"])
        }
        self.degree_key_to_pos = {
            str(key): position
            for position, key in enumerate(self.artifacts.degree_profiles["degree_key"])
        }

        self.degree_modules_by_key: dict[str, pd.DataFrame] = {}
        self.module_to_degree_rows: dict[str, list[dict[str, str]]] = {}

        if self.artifacts.degree_modules is not None:
            degree_modules = self.artifacts.degree_modules.copy()
            degree_modules["moduleCode"] = degree_modules["moduleCode"].astype(str).str.upper()
            degree_modules["degree_key"] = degree_modules["degree_key"].astype(str)
            for degree_key, frame in degree_modules.groupby("degree_key", sort=False):
                self.degree_modules_by_key[str(degree_key)] = frame.reset_index(drop=True)

            module_degree_rows = (
                degree_modules[["moduleCode", "degree_key", "degree_id", "degree_name"]]
                .drop_duplicates()
                .sort_values(["moduleCode", "degree_name"])
            )
            for module_code, frame in module_degree_rows.groupby("moduleCode", sort=False):
                self.module_to_degree_rows[str(module_code)] = frame.to_dict("records")

    def _resolve_artifact_paths(self) -> ResolvedArtifactPaths:
        generic = artifact_paths(cache_dir=self.cache_dir, model_name=self.model_name)

        modules_meta = _first_existing(
            [
                generic.modules_meta,
                self.cache_dir / "degree_modules.parquet",
            ]
        )
        module_embeddings = _first_existing(
            [
                generic.module_embeddings,
                _latest_matching_path(self.cache_dir, f"degree_module_embeddings_{generic.model_slug}_*.npy"),
                _latest_matching_path(self.cache_dir, "degree_module_embeddings_*.npy"),
            ]
        )
        degree_meta = _first_existing([generic.degree_meta])
        degree_embeddings = _first_existing(
            [
                generic.degree_embeddings,
                _latest_matching_path(self.cache_dir, f"degree_embeddings_{generic.model_slug}_*.npy"),
                _latest_matching_path(self.cache_dir, "degree_embeddings_*.npy"),
            ]
        )
        degree_modules_meta = _first_existing([self.cache_dir / "degree_modules.parquet"])
        jobs_meta = _first_existing(
            [
                generic.jobs_meta,
                _latest_matching_path(self.cache_dir, "jobs_clean_*.parquet"),
            ]
        )
        job_embeddings = _first_existing(
            [
                generic.job_embeddings,
                _latest_matching_path(self.cache_dir, f"job_embeddings_{generic.model_slug}_*.npy"),
                _latest_matching_path(self.cache_dir, "job_embeddings_*.npy"),
            ]
        )
        hybrid_scores = _first_existing(
            [
                _latest_matching_path(self.cache_dir, "hybrid_matrix_*.npy"),
                generic.skill_overlap,
                _latest_matching_path(self.cache_dir, "skill_coverage_matrix_*.npy"),
            ]
        )

        required = {
            "modules metadata": modules_meta,
            "module embeddings": module_embeddings,
            "degree metadata": degree_meta,
            "degree embeddings": degree_embeddings,
            "jobs metadata": jobs_meta,
            "job embeddings": job_embeddings,
        }
        missing = [name for name, path in required.items() if path is None]
        if missing:
            joined = ", ".join(missing)
            raise FileNotFoundError(
                f"Missing retrieval artifacts for {joined}. Run scripts/build_chat_index.py or refresh notebooks/cache."
            )

        return ResolvedArtifactPaths(
            modules_meta=modules_meta,
            module_embeddings=module_embeddings,
            degree_meta=degree_meta,
            degree_embeddings=degree_embeddings,
            degree_modules_meta=degree_modules_meta,
            jobs_meta=jobs_meta,
            job_embeddings=job_embeddings,
            hybrid_scores=hybrid_scores,
        )

    def _prepare_module_artifacts(
        self,
        raw_modules: pd.DataFrame,
        raw_embeddings: np.ndarray,
    ) -> tuple[pd.DataFrame, np.ndarray]:
        frame = raw_modules.reset_index(drop=True).copy()
        frame["moduleCode"] = frame["moduleCode"].fillna("").astype(str).str.upper()

        if raw_embeddings.shape[0] != len(frame):
            raise ValueError("Module embeddings do not match the module metadata row count.")

        if "degree_name" in frame.columns:
            context_column = "degree_name"
            context_prefix = "Appears in"
        else:
            context_column = "department"
            context_prefix = "Department"

        records: list[dict[str, object]] = []
        vectors: list[np.ndarray] = []

        for module_code, group in frame.groupby("moduleCode", sort=False):
            positions = group.index.to_numpy(dtype=int)
            mean_embedding = _normalize_vector(raw_embeddings[positions].mean(axis=0))
            title = next((str(value).strip() for value in group["title"] if str(value).strip()), str(module_code))
            description = next(
                (
                    str(value).strip()
                    for value in group.get("description_clean", pd.Series(dtype=object))
                    if str(value).strip()
                ),
                "",
            )
            context_labels = []
            if context_column in group.columns:
                seen: set[str] = set()
                for value in group[context_column].tolist():
                    label = str(value).strip()
                    if label and label not in seen:
                        context_labels.append(label)
                        seen.add(label)

            records.append(
                {
                    "moduleCode": str(module_code),
                    "title": title,
                    "description_clean": description,
                    "context_labels": context_labels,
                    "context_summary": _summarize_labels(context_labels, context_prefix),
                }
            )
            vectors.append(mean_embedding)

        return pd.DataFrame(records), np.vstack(vectors).astype(np.float32)

    def _load_artifacts(self) -> SearchArtifacts:
        modules_raw = pd.read_parquet(self.paths.modules_meta)
        degree_profiles = pd.read_parquet(self.paths.degree_meta).reset_index(drop=True)
        jobs = pd.read_parquet(self.paths.jobs_meta).reset_index(drop=True)

        if "degree_label" not in degree_profiles.columns:
            if "degree_name" in degree_profiles.columns:
                degree_profiles["degree_label"] = degree_profiles["degree_name"]
            elif "department" in degree_profiles.columns:
                degree_profiles["degree_label"] = degree_profiles["department"]
            else:
                degree_profiles["degree_label"] = "Unknown degree"

        if "degree_key" not in degree_profiles.columns:
            degree_profiles["degree_key"] = degree_profiles["degree_label"].apply(_canonicalize_degree_label)
        if "degree_id" not in degree_profiles.columns:
            degree_profiles["degree_id"] = degree_profiles["degree_key"]
        if "n_modules" not in degree_profiles.columns:
            degree_profiles["n_modules"] = 0

        _coerce_list_column(jobs, "categories")
        _coerce_list_column(jobs, "skills")

        module_embeddings_raw = np.load(self.paths.module_embeddings).astype(np.float32)
        modules, module_embeddings = self._prepare_module_artifacts(modules_raw, module_embeddings_raw)

        degree_modules = None
        if self.paths.degree_modules_meta is not None and self.paths.degree_modules_meta.exists():
            degree_modules = pd.read_parquet(self.paths.degree_modules_meta).reset_index(drop=True)

        degree_embeddings = np.load(self.paths.degree_embeddings).astype(np.float32)
        job_embeddings = np.load(self.paths.job_embeddings).astype(np.float32)

        hybrid_scores = None
        if self.paths.hybrid_scores is not None and self.paths.hybrid_scores.exists():
            candidate = np.load(self.paths.hybrid_scores).astype(np.float32)
            if candidate.shape == (len(degree_profiles), len(jobs)):
                hybrid_scores = candidate

        return SearchArtifacts(
            modules=modules,
            module_embeddings=module_embeddings,
            degree_profiles=degree_profiles,
            degree_embeddings=degree_embeddings,
            degree_modules=degree_modules,
            jobs=jobs,
            job_embeddings=job_embeddings,
            hybrid_scores=hybrid_scores,
        )

    @property
    def model(self) -> SentenceTransformer:
        model = getattr(self, "_model", None)
        if model is None:
            model = _load_model(self.model_name)
            self._model = model
        return model

    def _encode_query(self, query: str) -> np.ndarray:
        return self.model.encode(
            [query],
            normalize_embeddings=True,
        )[0].astype(np.float32)

    def _clamp_top_k(self, top_k: int) -> int:
        return max(1, min(int(top_k), 20))

    def _build_job_recommendations(
        self,
        scores: np.ndarray,
        reason_builder: Callable[[pd.Series], str],
        top_k: int,
    ) -> list[JobRecommendation]:
        top_idx = np.argsort(scores)[::-1][:top_k]
        results: list[JobRecommendation] = []
        for idx in top_idx:
            row = self.artifacts.jobs.iloc[int(idx)]
            categories = row["categories"] if isinstance(row["categories"], list) else []
            results.append(
                JobRecommendation(
                    jobId=str(row["job_id"]),
                    title=str(row["title"]),
                    company=str(row.get("company", "")),
                    categories=[str(item) for item in categories],
                    score=round(float(scores[idx]), 4),
                    reason=reason_builder(row),
                    descriptionSnippet=_truncate(str(row.get("description_clean", ""))),
                    url=(str(row.get("job_url", "")).strip() or None),
                )
            )
        return results

    def _build_module_recommendations(
        self,
        scores: np.ndarray,
        top_k: int,
        reason_builder: Callable[[pd.Series], str],
    ) -> list[ModuleRecommendation]:
        top_idx = np.argsort(scores)[::-1][:top_k]
        results: list[ModuleRecommendation] = []
        for idx in top_idx:
            row = self.artifacts.modules.iloc[int(idx)]
            results.append(
                ModuleRecommendation(
                    moduleCode=str(row["moduleCode"]),
                    title=str(row["title"]),
                    context=str(row.get("context_summary", "NUS course")),
                    score=round(float(scores[idx]), 4),
                    reason=reason_builder(row),
                    descriptionSnippet=_truncate(str(row.get("description_clean", ""))),
                )
            )
        return results

    def _build_degree_recommendations(
        self,
        scores: np.ndarray,
        top_k: int,
        reason_builder: Callable[[pd.Series], str],
    ) -> list[DegreeRecommendation]:
        top_idx = np.argsort(scores)[::-1][:top_k]
        results: list[DegreeRecommendation] = []
        for idx in top_idx:
            row = self.artifacts.degree_profiles.iloc[int(idx)]
            results.append(
                DegreeRecommendation(
                    degreeId=str(row.get("degree_id", row.get("degree_key", row.get("degree_label", "")))),
                    degreeLabel=str(row["degree_label"]),
                    score=round(float(scores[idx]), 4),
                    reason=reason_builder(row),
                    moduleCount=int(row.get("n_modules", 0) or 0),
                )
            )
        return results

    def _degree_suggestions(self, query: str, limit: int = 5) -> list[str]:
        labels = self.artifacts.degree_profiles["degree_label"].tolist()
        canonical_labels = {label: _canonicalize_degree_label(label) for label in labels}
        reverse = {value: key for key, value in canonical_labels.items()}
        matches = get_close_matches(_canonicalize_degree_label(query), list(reverse), n=limit, cutoff=0.55)
        return [reverse[match] for match in matches]

    def _module_suggestions(self, query: str, limit: int = 5) -> list[str]:
        normalized = _normalize_module_code(query)
        codes = self.artifacts.modules["moduleCode"].tolist()
        matches = get_close_matches(normalized, codes, n=limit, cutoff=0.55)
        return [str(match) for match in matches]

    def _representative_modules_for_degree(self, degree_key: str, top_k: int) -> list[ModuleRecommendation]:
        if degree_key not in self.degree_modules_by_key:
            return []

        frame = self.degree_modules_by_key[degree_key].copy()
        frame = frame.sort_values("module_order")
        frame = frame.drop_duplicates("moduleCode", keep="first").head(top_k)

        results: list[ModuleRecommendation] = []
        for _, row in frame.iterrows():
            requirement_group = str(row.get("requirement_group", "")).strip().lower()
            requirement_label = "Core course" if requirement_group == "core" else "Common course"
            degree_name = str(row.get("degree_name", "")).strip()
            results.append(
                ModuleRecommendation(
                    moduleCode=str(row["moduleCode"]),
                    title=str(row["title"]),
                    context=f"{requirement_label} in {degree_name}" if degree_name else requirement_label,
                    score=1.0,
                    reason=f"Representative course from the curated {degree_name or 'degree'} basket used in the notebook.",
                    descriptionSnippet=_truncate(str(row.get("description_clean", ""))),
                )
            )
        return results

    def _degrees_for_module(self, module_code: str, top_k: int) -> list[DegreeRecommendation]:
        rows = self.module_to_degree_rows.get(module_code.upper(), [])
        results: list[DegreeRecommendation] = []
        for row in rows[:top_k]:
            degree_pos = self.degree_key_to_pos.get(str(row["degree_key"]))
            module_count = 0
            if degree_pos is not None:
                degree_row = self.artifacts.degree_profiles.iloc[degree_pos]
                module_count = int(degree_row.get("n_modules", 0) or 0)

            results.append(
                DegreeRecommendation(
                    degreeId=str(row.get("degree_id", row["degree_key"])),
                    degreeLabel=str(row["degree_name"]),
                    reason=f"This course appears in the curated degree basket for {row['degree_name']}.",
                    moduleCount=module_count,
                )
            )
        return results

    def find_jobs(self, query: str, top_k: int = 8) -> SearchResponse:
        clean_query = query.strip()
        normalized_code = _normalize_module_code(clean_query)
        top_k = self._clamp_top_k(top_k)

        if normalized_code in self.module_code_to_pos:
            module_pos = self.module_code_to_pos[normalized_code]
            module_row = self.artifacts.modules.iloc[module_pos]
            scores = self.artifacts.module_embeddings[module_pos] @ self.artifacts.job_embeddings.T
            results = self._build_job_recommendations(
                scores=scores,
                top_k=top_k,
                reason_builder=lambda _: (
                    f"Matched to course {module_row['moduleCode']} ({module_row['title']}) using course-to-job semantic similarity."
                ),
            )
            return SearchResponse(
                mode="find_jobs",
                normalizedQuery=normalized_code,
                matchedEntity=MatchedEntity(
                    type="module",
                    value=str(module_row["moduleCode"]),
                    label=f"{module_row['moduleCode']} - {module_row['title']}",
                ),
                results=results,
            )

        canonical_degree = _canonicalize_degree_label(clean_query)
        if canonical_degree in self.degree_label_to_pos:
            degree_pos = self.degree_label_to_pos[canonical_degree]
            degree_row = self.artifacts.degree_profiles.iloc[degree_pos]
            if self.artifacts.hybrid_scores is not None:
                scores = self.artifacts.hybrid_scores[degree_pos]
                score_label = "cached degree-to-job alignment"
            else:
                scores = self.artifacts.degree_embeddings[degree_pos] @ self.artifacts.job_embeddings.T
                score_label = "degree-profile semantic similarity"

            results = self._build_job_recommendations(
                scores=scores,
                top_k=top_k,
                reason_builder=lambda _: (
                    f"Matched to degree proxy {degree_row['degree_label']} using {score_label} from the notebook pipeline."
                ),
            )
            return SearchResponse(
                mode="find_jobs",
                normalizedQuery=str(degree_row["degree_label"]),
                matchedEntity=MatchedEntity(
                    type="degree",
                    value=str(degree_row["degree_label"]),
                    label=str(degree_row["degree_label"]),
                ),
                results=results,
            )

        warnings: list[str] = ["I couldn't match that to a known NUS module code or degree label."]
        module_suggestions = self._module_suggestions(clean_query)
        degree_suggestions = self._degree_suggestions(clean_query)
        if module_suggestions:
            warnings.append(f"Closest module codes: {', '.join(module_suggestions)}")
        if degree_suggestions:
            warnings.append(f"Closest degree labels: {', '.join(degree_suggestions)}")

        return SearchResponse(
            mode="find_jobs",
            normalizedQuery=normalized_code or clean_query,
            warnings=warnings,
        )

    def find_modules(self, query: str, top_k: int = 8) -> SearchResponse:
        clean_query = re.sub(r"\s+", " ", query).strip()
        top_k = self._clamp_top_k(top_k)

        if len(clean_query) < 5:
            return SearchResponse(
                mode="find_modules",
                normalizedQuery=clean_query,
                warnings=["Please provide a job title or a longer job description so the course match is meaningful."],
            )

        query_embedding = self._encode_query(clean_query)
        scores = self.artifacts.module_embeddings @ query_embedding
        results = self._build_module_recommendations(
            scores=scores,
            top_k=top_k,
            reason_builder=lambda _: (
                "Semantically aligned to the supplied job text based on course descriptions and extracted course skills."
            ),
        )
        return SearchResponse(
            mode="find_modules",
            normalizedQuery=clean_query,
            matchedEntity=MatchedEntity(type="job_query", value=clean_query, label=_truncate(clean_query, 80)),
            results=results,
        )

    def explore(
        self,
        query: str,
        top_jobs: int = 3,
        top_modules: int = 3,
        top_degrees: int = 3,
    ) -> ExplorerResponse:
        clean_query = re.sub(r"\s+", " ", query).strip()
        if not clean_query:
            return ExplorerResponse(
                intent="job_query",
                normalizedQuery="",
                warnings=["Please enter a degree, module code, job title, or job description."],
            )

        top_jobs = self._clamp_top_k(top_jobs)
        top_modules = self._clamp_top_k(top_modules)
        top_degrees = self._clamp_top_k(top_degrees)

        normalized_code = _normalize_module_code(clean_query)
        if normalized_code in self.module_code_to_pos:
            jobs_response = self.find_jobs(clean_query, top_jobs)
            module_pos = self.module_code_to_pos[normalized_code]
            module_row = self.artifacts.modules.iloc[module_pos]
            module_card = ModuleRecommendation(
                moduleCode=str(module_row["moduleCode"]),
                title=str(module_row["title"]),
                context=str(module_row.get("context_summary", "NUS course")),
                score=1.0,
                reason="Exact course match from the curated NUS course basket.",
                descriptionSnippet=_truncate(str(module_row.get("description_clean", ""))),
            )
            return ExplorerResponse(
                intent="module_lookup",
                normalizedQuery=normalized_code,
                matchedEntity=jobs_response.matchedEntity,
                warnings=list(jobs_response.warnings),
                jobs=list(jobs_response.results),
                modules=[module_card],
                degrees=self._degrees_for_module(normalized_code, top_degrees),
            )

        canonical_degree = _canonicalize_degree_label(clean_query)
        if canonical_degree in self.degree_label_to_pos:
            jobs_response = self.find_jobs(clean_query, top_jobs)
            degree_pos = self.degree_label_to_pos[canonical_degree]
            degree_row = self.artifacts.degree_profiles.iloc[degree_pos]
            return ExplorerResponse(
                intent="degree_lookup",
                normalizedQuery=str(degree_row["degree_label"]),
                matchedEntity=jobs_response.matchedEntity,
                warnings=list(jobs_response.warnings),
                jobs=list(jobs_response.results),
                modules=self._representative_modules_for_degree(str(degree_row["degree_key"]), top_modules),
                degrees=[
                    DegreeRecommendation(
                        degreeId=str(degree_row.get("degree_id", degree_row.get("degree_key", degree_row["degree_label"]))),
                        degreeLabel=str(degree_row["degree_label"]),
                        reason="Exact degree match from the notebook's curated degree profiles.",
                        moduleCount=int(degree_row.get("n_modules", 0) or 0),
                    )
                ],
            )

        if len(clean_query) < 5:
            return ExplorerResponse(
                intent="job_query",
                normalizedQuery=clean_query,
                warnings=["Please provide a fuller role description, skills list, degree name, or module code."],
            )

        query_embedding = self._encode_query(clean_query)
        job_scores = self.artifacts.job_embeddings @ query_embedding
        module_scores = self.artifacts.module_embeddings @ query_embedding
        degree_scores = self.artifacts.degree_embeddings @ query_embedding

        return ExplorerResponse(
            intent="job_query",
            normalizedQuery=clean_query,
            matchedEntity=MatchedEntity(type="job_query", value=clean_query, label=_truncate(clean_query, 80)),
            jobs=self._build_job_recommendations(
                scores=job_scores,
                top_k=top_jobs,
                reason_builder=lambda _: (
                    "Semantically similar to your natural-language query within the filtered MyCareersFuture corpus."
                ),
            ),
            modules=self._build_module_recommendations(
                scores=module_scores,
                top_k=top_modules,
                reason_builder=lambda _: (
                    "Course content is semantically aligned to the role, skills, or job description you provided."
                ),
            ),
            degrees=self._build_degree_recommendations(
                scores=degree_scores,
                top_k=top_degrees,
                reason_builder=lambda _: (
                    "Degree profile is semantically aligned to the role or skill mix described in your query."
                ),
            ),
        )

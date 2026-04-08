from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

from .index import MODEL_NAME, _load_model, artifact_paths
from .types import JobRecommendation, MatchedEntity, ModuleRecommendation, SearchResponse


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
    sample = frame[column].iloc[0]
    if isinstance(sample, list):
        return
    if isinstance(sample, str):
        def parse(value: object) -> list[str]:
            if isinstance(value, list):
                return value
            if not isinstance(value, str) or not value.strip():
                return []
            try:
                parsed = ast.literal_eval(value)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except Exception:
                pass
            return [part.strip() for part in value.split(",") if part.strip()]

        frame[column] = frame[column].apply(parse)


@dataclass(slots=True)
class SearchArtifacts:
    modules: pd.DataFrame
    module_embeddings: np.ndarray
    degree_profiles: pd.DataFrame
    degree_embeddings: np.ndarray
    jobs: pd.DataFrame
    job_embeddings: np.ndarray
    skill_overlap: np.ndarray | None


class SearchService:
    def __init__(self, cache_dir: Path | str = Path("notebooks/cache"), model_name: str = MODEL_NAME) -> None:
        self.paths = artifact_paths(cache_dir=cache_dir, model_name=model_name)
        self.model_name = model_name
        self.artifacts = self._load_artifacts()

        self.module_code_to_pos = {
            _normalize_module_code(code): position
            for position, code in enumerate(self.artifacts.modules["moduleCode"])
        }
        self.degree_label_to_pos = {
            _canonicalize_degree_label(label): position
            for position, label in enumerate(self.artifacts.degree_profiles["degree_label"])
        }

    def _load_artifacts(self) -> SearchArtifacts:
        required_paths = [
            self.paths.modules_meta,
            self.paths.module_embeddings,
            self.paths.degree_meta,
            self.paths.degree_embeddings,
            self.paths.jobs_meta,
            self.paths.job_embeddings,
        ]
        missing = [str(path) for path in required_paths if not path.exists()]
        if missing:
            joined = ", ".join(missing)
            raise FileNotFoundError(
                f"Missing retrieval artifacts: {joined}. Run scripts/build_chat_index.py first."
            )

        modules = pd.read_parquet(self.paths.modules_meta)
        degree_profiles = pd.read_parquet(self.paths.degree_meta)
        jobs = pd.read_parquet(self.paths.jobs_meta)

        _coerce_list_column(jobs, "categories")
        _coerce_list_column(jobs, "skills")

        skill_overlap = None
        if self.paths.skill_overlap.exists():
            skill_overlap = np.load(self.paths.skill_overlap).astype(np.float32)

        return SearchArtifacts(
            modules=modules,
            module_embeddings=np.load(self.paths.module_embeddings).astype(np.float32),
            degree_profiles=degree_profiles,
            degree_embeddings=np.load(self.paths.degree_embeddings).astype(np.float32),
            jobs=jobs,
            job_embeddings=np.load(self.paths.job_embeddings).astype(np.float32),
            skill_overlap=skill_overlap,
        )

    @property
    def model(self) -> SentenceTransformer:
        model = getattr(self, "_model", None)
        if model is None:
            model = _load_model(self.model_name)
            self._model = model
        return model

    def _clamp_top_k(self, top_k: int) -> int:
        return max(1, min(int(top_k), 20))

    def _build_job_recommendations(
        self,
        scores: np.ndarray,
        reason_builder,
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
                    url=(str(row.get("job_url")) or None),
                )
            )
        return results

    def _build_module_recommendations(self, scores: np.ndarray, top_k: int) -> list[ModuleRecommendation]:
        top_idx = np.argsort(scores)[::-1][:top_k]
        results: list[ModuleRecommendation] = []
        for idx in top_idx:
            row = self.artifacts.modules.iloc[int(idx)]
            results.append(
                ModuleRecommendation(
                    moduleCode=str(row["moduleCode"]),
                    title=str(row["title"]),
                    department=str(row["department"]),
                    score=round(float(scores[idx]), 4),
                    reason="Similar to the supplied job text based on module title and description semantics.",
                    descriptionSnippet=_truncate(str(row["description_clean"])),
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
                    f"Matched to module {module_row['moduleCode']} ({module_row['title']}) using module-to-job cosine similarity."
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
            semantic_scores = self.artifacts.degree_embeddings[degree_pos] @ self.artifacts.job_embeddings.T
            if self.artifacts.skill_overlap is not None:
                hybrid_scores = 0.7 * semantic_scores + 0.3 * self.artifacts.skill_overlap[degree_pos]
                score_label = "hybrid degree-to-job alignment"
                scores = hybrid_scores
            else:
                score_label = "degree-profile cosine similarity"
                scores = semantic_scores

            results = self._build_job_recommendations(
                scores=scores,
                top_k=top_k,
                reason_builder=lambda _: (
                    f"Matched to degree proxy {degree_row['degree_label']} using {score_label}."
                ),
            )
            return SearchResponse(
                mode="find_jobs",
                normalizedQuery=degree_row["degree_label"],
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
                warnings=["Please provide a job title or a longer job description so the module match is meaningful."],
            )

        query_embedding = self.model.encode(
            [clean_query],
            normalize_embeddings=True,
        )[0].astype(np.float32)
        scores = self.artifacts.module_embeddings @ query_embedding
        results = self._build_module_recommendations(scores=scores, top_k=top_k)
        return SearchResponse(
            mode="find_modules",
            normalizedQuery=clean_query,
            matchedEntity=MatchedEntity(type="job_query", value=clean_query, label=_truncate(clean_query, 80)),
            results=results,
        )

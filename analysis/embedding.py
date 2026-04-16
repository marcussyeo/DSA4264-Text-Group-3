from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd


def aggregate_top_k_similarity(score_matrix: np.ndarray, top_k: int) -> np.ndarray:
    if score_matrix.ndim != 2:
        raise ValueError("score_matrix must be a 2D array.")
    if score_matrix.shape[0] == 0:
        return np.zeros(score_matrix.shape[1], dtype=np.float32)

    top_k = max(1, min(top_k, score_matrix.shape[0]))
    partition_index = score_matrix.shape[0] - top_k
    top_k_scores = np.partition(score_matrix, partition_index, axis=0)[partition_index:]
    return top_k_scores.mean(axis=0).astype(np.float32)


@lru_cache(maxsize=4)
def load_model(model_name: str):
    from sentence_transformers import SentenceTransformer

    try:
        return SentenceTransformer(model_name, local_files_only=True)
    except Exception:
        return SentenceTransformer(model_name)


def load_or_compute_embeddings(
    texts: list[str],
    output_path,
    model_name: str,
    batch_size: int,
) -> np.ndarray:
    if output_path.exists():
        cached = np.load(output_path)
        if cached.ndim == 2 and cached.shape[0] == len(texts):
            return cached

    model = load_model(model_name)
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    np.save(output_path, embeddings)
    return embeddings


def build_degree_embeddings(
    degree_profiles: pd.DataFrame,
    degree_module_indices: dict[str, np.ndarray],
    module_embeddings: np.ndarray,
) -> np.ndarray:
    degree_embeddings = np.zeros((len(degree_profiles), module_embeddings.shape[1]), dtype=np.float32)
    for index, degree_id in enumerate(degree_profiles["degree_id"].astype(str).tolist()):
        module_idx = degree_module_indices.get(degree_id, np.array([], dtype=int))
        if len(module_idx) == 0:
            continue
        centroid = module_embeddings[module_idx].mean(axis=0)
        norm = np.linalg.norm(centroid)
        degree_embeddings[index] = centroid / norm if norm > 0 else centroid
    return degree_embeddings


def compute_similarity_matrix(
    degree_profiles: pd.DataFrame,
    degree_module_indices: dict[str, np.ndarray],
    module_embeddings: np.ndarray,
    job_embeddings: np.ndarray,
    top_k: int,
) -> np.ndarray:
    if module_embeddings.shape[0] == 0 or job_embeddings.shape[0] == 0:
        return np.zeros((len(degree_profiles), len(job_embeddings)), dtype=np.float32)

    module_job_sim = module_embeddings @ job_embeddings.T
    sim_matrix = np.zeros((len(degree_profiles), len(job_embeddings)), dtype=np.float32)
    for degree_position, degree_id in enumerate(degree_profiles["degree_id"].astype(str).tolist()):
        module_idx = degree_module_indices.get(degree_id, np.array([], dtype=int))
        sim_matrix[degree_position] = aggregate_top_k_similarity(module_job_sim[module_idx], top_k)
    return sim_matrix


def top_k_jobs_for_degree(
    score_matrix: np.ndarray,
    degree_profiles: pd.DataFrame,
    jobs: pd.DataFrame,
    degree_id: str,
    score_column: str,
    k: int = 10,
) -> pd.DataFrame:
    matches = degree_profiles.index[degree_profiles["degree_id"].astype(str) == str(degree_id)]
    if len(matches) == 0:
        raise KeyError(f"Degree id {degree_id!r} was not found.")
    degree_idx = degree_profiles.index.get_loc(matches[0])
    scores = score_matrix[degree_idx]
    top_idx = np.argsort(scores)[::-1][:k]
    return pd.DataFrame(
        {
            "rank": range(1, len(top_idx) + 1),
            "job_id": jobs.iloc[top_idx]["job_id"].values,
            "job_title": jobs.iloc[top_idx]["title"].values,
            "company": jobs.iloc[top_idx]["company"].values,
            "categories": jobs.iloc[top_idx]["categories_str"].values,
            score_column: scores[top_idx].round(4),
        }
    )

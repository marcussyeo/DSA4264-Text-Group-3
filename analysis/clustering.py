from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from .embedding import aggregate_top_k_similarity


def load_or_compute_clusters(job_embeddings: np.ndarray, output_path, n_clusters: int = 75) -> np.ndarray:
    if output_path.exists():
        cached = np.load(output_path)
        if cached.shape[0] == len(job_embeddings):
            return cached

    model = MiniBatchKMeans(
        n_clusters=min(n_clusters, len(job_embeddings)),
        random_state=42,
        batch_size=2048,
        n_init=5,
        max_iter=300,
    )
    cluster_labels = model.fit_predict(job_embeddings)
    np.save(output_path, cluster_labels)
    return cluster_labels


def label_clusters(jobs: pd.DataFrame, cluster_labels: np.ndarray, n_clusters: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    jobs_with_clusters = jobs.copy()
    jobs_with_clusters["cluster_id"] = cluster_labels

    tfidf = TfidfVectorizer(max_features=20000, ngram_range=(1, 2), stop_words="english", min_df=2)
    tfidf.fit(jobs_with_clusters["description_clean"].tolist())
    feature_names = np.array(tfidf.get_feature_names_out())

    cluster_info = []
    for cluster_id in range(min(n_clusters, jobs_with_clusters["cluster_id"].nunique())):
        mask = jobs_with_clusters["cluster_id"] == cluster_id
        cluster_jobs = jobs_with_clusters[mask]
        if cluster_jobs.empty:
            continue

        vecs = tfidf.transform(cluster_jobs["description_clean"].tolist())
        mean_tfidf = np.asarray(vecs.mean(axis=0)).flatten()
        top_term_idx = mean_tfidf.argsort()[::-1][:8]
        top_terms = ", ".join(feature_names[top_term_idx])

        all_categories = [
            category
            for categories in cluster_jobs["categories"].tolist()
            for category in (categories if isinstance(categories, list) else [])
        ]
        top_category = pd.Series(all_categories).value_counts().index[0] if all_categories else "Unknown"

        title_words = pd.Series(" ".join(cluster_jobs["title"].tolist()).lower().split()).value_counts()
        common_titles = ", ".join(title_words.head(5).index.tolist())

        cluster_info.append(
            {
                "cluster_id": int(cluster_id),
                "n_jobs": int(mask.sum()),
                "top_category": top_category,
                "top_terms": top_terms,
                "common_titles": common_titles,
            }
        )

    cluster_df = pd.DataFrame(cluster_info).sort_values("n_jobs", ascending=False).reset_index(drop=True)
    return jobs_with_clusters, cluster_df


def compute_degree_cluster_similarity(
    degree_profiles: pd.DataFrame,
    degree_module_indices: dict[str, np.ndarray],
    module_embeddings: np.ndarray,
    job_embeddings: np.ndarray,
    cluster_labels: np.ndarray,
    top_k: int,
    n_clusters: int,
) -> np.ndarray:
    cluster_centroids = np.zeros((n_clusters, job_embeddings.shape[1]), dtype=np.float32)
    for cluster_id in range(n_clusters):
        mask = cluster_labels == cluster_id
        if mask.sum() == 0:
            continue
        centroid = job_embeddings[mask].mean(axis=0)
        norm = np.linalg.norm(centroid)
        cluster_centroids[cluster_id] = centroid / norm if norm > 0 else centroid

    module_cluster_sim = module_embeddings @ cluster_centroids.T
    degree_cluster_sim = np.zeros((len(degree_profiles), n_clusters), dtype=np.float32)

    for degree_index, degree_id in enumerate(degree_profiles["degree_id"].astype(str).tolist()):
        module_idx = degree_module_indices.get(degree_id, np.array([], dtype=int))
        degree_cluster_sim[degree_index] = aggregate_top_k_similarity(module_cluster_sim[module_idx], top_k)

    return degree_cluster_sim


def build_degree_cluster_alignment(
    degree_profiles: pd.DataFrame,
    degree_cluster_sim: np.ndarray,
    cluster_df: pd.DataFrame,
    top_n: int = 5,
) -> pd.DataFrame:
    cluster_label_map = dict(zip(cluster_df["cluster_id"], cluster_df["top_category"]))
    cluster_terms_map = dict(zip(cluster_df["cluster_id"], cluster_df["top_terms"]))
    rows = []

    for degree_position, degree_row in degree_profiles.reset_index(drop=True).iterrows():
        scores = degree_cluster_sim[degree_position]
        top_clusters = np.argsort(scores)[::-1][:top_n]
        for rank, cluster_id in enumerate(top_clusters, start=1):
            rows.append(
                {
                    "degree_id": degree_row["degree_id"],
                    "degree": degree_row["degree_name"],
                    "rank": rank,
                    "cluster_id": int(cluster_id),
                    "cluster_label": cluster_label_map.get(int(cluster_id), f"Cluster {cluster_id}"),
                    "cluster_terms": cluster_terms_map.get(int(cluster_id), ""),
                    "cluster_score": round(float(scores[cluster_id]), 4),
                }
            )

    return pd.DataFrame(rows)

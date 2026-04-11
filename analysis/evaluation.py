from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


def export_golden_topk(
    degree_profiles: pd.DataFrame,
    jobs: pd.DataFrame,
    sim_matrix: np.ndarray,
    skill_coverage_matrix: np.ndarray,
    hybrid_matrix: np.ndarray,
    output_path,
    top_k: int = 10,
    degree_cluster_sim: np.ndarray | None = None,
) -> pd.DataFrame:
    rows = []
    for degree_index, degree_row in degree_profiles.reset_index(drop=True).iterrows():
        scores = hybrid_matrix[degree_index]
        top_job_idx = np.argsort(scores)[::-1][:top_k]
        for rank, job_index in enumerate(top_job_idx, start=1):
            job_row = jobs.iloc[job_index]
            row = {
                "degree_id": degree_row["degree_id"],
                "degree_name": degree_row["degree_name"],
                "rank": rank,
                "job_id": job_row["job_id"],
                "job_title": job_row["title"],
                "company": job_row.get("company", ""),
                "job_categories": job_row.get("categories_str", ""),
                "job_description_snippet": str(job_row.get("description_clean", ""))[:600],
                "cosine_sim": round(float(sim_matrix[degree_index, job_index]), 4),
                "skill_coverage": round(float(skill_coverage_matrix[degree_index, job_index]), 4),
                "hybrid_score": round(float(hybrid_matrix[degree_index, job_index]), 4),
                "human_label": "",
                "annotator_notes": "",
            }
            if degree_cluster_sim is not None and "cluster_id" in jobs.columns:
                row["cluster_score"] = round(float(degree_cluster_sim[degree_index, int(job_row["cluster_id"])]), 4)
            rows.append(row)

    golden_df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    golden_df.to_csv(output_path, index=False)
    return golden_df


def precision_at_k(labels: list[int], k: int) -> float:
    top_k = labels[:k]
    if not top_k:
        return 0.0
    return sum(label >= 1 for label in top_k) / len(top_k)


def top_k_hit_rate(labels: list[int], k: int) -> int:
    return int(any(label == 2 for label in labels[:k]))


def ndcg_at_k(labels: list[int], k: int) -> float:
    labels = labels[:k]

    def dcg(values: list[int]) -> float:
        return sum((2**label - 1) / np.log2(index + 2) for index, label in enumerate(values))

    ideal = sorted(labels, reverse=True)
    ideal_dcg = dcg(ideal)
    return dcg(labels) / ideal_dcg if ideal_dcg > 0 else 0.0


def evaluate_ranked_scores(
    golden: pd.DataFrame,
    score_columns: list[str],
    metrics_path=None,
    k_precision: int = 5,
    k_hit: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_columns = [
        "degree_id",
        "degree_name",
        "method",
        f"Precision@{k_precision}",
        f"NDCG@{k_precision}",
        f"Top-{k_hit}_HitRate",
        "annotated_jobs",
    ]
    annotated = golden[golden["human_label"].apply(lambda value: str(value).strip()).isin(["0", "1", "2"])].copy()
    if annotated.empty:
        empty_metrics = pd.DataFrame(columns=metric_columns)
        empty_correlations = pd.DataFrame(columns=["method", "annotated_pairs", "degrees_evaluated", "spearman_rho", "p_value"])
        if metrics_path is not None:
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            empty_metrics.to_csv(metrics_path, index=False)
        return empty_metrics, empty_correlations

    annotated["human_label"] = annotated["human_label"].astype(int)
    metric_rows = []
    correlation_rows = []

    for score_column in score_columns:
        if score_column not in annotated.columns:
            continue

        per_degree_rows = []
        for degree_id, group in annotated.groupby("degree_id"):
            ranked = group.sort_values(score_column, ascending=False)
            labels = ranked["human_label"].tolist()
            per_degree_rows.append(
                {
                    "degree_id": degree_id,
                    "degree_name": ranked["degree_name"].iloc[0],
                    "method": score_column,
                    f"Precision@{k_precision}": precision_at_k(labels, k_precision),
                    f"NDCG@{k_precision}": ndcg_at_k(labels, k_precision),
                    f"Top-{k_hit}_HitRate": top_k_hit_rate(labels, k_hit),
                    "annotated_jobs": len(ranked),
                }
            )

        degree_metrics = pd.DataFrame(per_degree_rows)
        metric_rows.append(degree_metrics)

        rho, p_value = spearmanr(annotated[score_column], annotated["human_label"])
        correlation_rows.append(
            {
                "method": score_column,
                "annotated_pairs": len(annotated),
                "degrees_evaluated": annotated["degree_id"].nunique(),
                "spearman_rho": rho,
                "p_value": p_value,
            }
        )

    metrics_df = pd.concat(metric_rows, ignore_index=True) if metric_rows else pd.DataFrame()
    correlations_df = pd.DataFrame(correlation_rows)

    if metrics_path is not None:
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_df.to_csv(metrics_path, index=False)

    return metrics_df, correlations_df


def build_degree_job_summary(
    degree_profiles: pd.DataFrame,
    jobs: pd.DataFrame,
    hybrid_matrix: np.ndarray,
    output_path,
    sim_matrix: np.ndarray | None = None,
    skill_coverage_matrix: np.ndarray | None = None,
    top_n: int = 5,
) -> pd.DataFrame:
    rows = []
    for degree_index, degree_row in degree_profiles.reset_index(drop=True).iterrows():
        scores = hybrid_matrix[degree_index]
        top_idx = np.argsort(scores)[::-1][:top_n]
        for rank, job_index in enumerate(top_idx, start=1):
            job_row = jobs.iloc[job_index]
            row = {
                "degree_id": degree_row["degree_id"],
                "degree_name": degree_row["degree_name"],
                "rank": rank,
                "job_id": job_row["job_id"],
                "job_title": job_row["title"],
                "company": job_row.get("company", ""),
                "job_categories": job_row.get("categories_str", ""),
                "hybrid_score": round(float(hybrid_matrix[degree_index, job_index]), 4),
            }
            if sim_matrix is not None:
                row["cosine_sim"] = round(float(sim_matrix[degree_index, job_index]), 4)
            if skill_coverage_matrix is not None:
                row["skill_coverage"] = round(float(skill_coverage_matrix[degree_index, job_index]), 4)
            rows.append(row)

    summary_df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(output_path, index=False)
    return summary_df


def build_coverage_report(
    payload: dict,
    output_path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path

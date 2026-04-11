from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_similarity_distributions(sim_matrix: np.ndarray, degree_profiles: pd.DataFrame, output_path) -> None:
    max_sim_per_degree = sim_matrix.max(axis=1)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].hist(max_sim_per_degree, bins=30, color="steelblue", edgecolor="white")
    axes[0].set_title("Distribution of Max Cosine Similarity\n(best job match per degree)")
    axes[0].set_xlabel("Max Similarity Score")
    axes[0].set_ylabel("Number of Degrees")

    axes[1].hist(sim_matrix.max(axis=0), bins=40, color="darkorange", edgecolor="white")
    axes[1].set_title("Distribution of Max Cosine Similarity\n(best degree match per job)")
    axes[1].set_xlabel("Max Similarity Score")
    axes[1].set_ylabel("Number of Jobs")

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_alignment_heatmap(
    degree_cluster_sim: np.ndarray,
    degree_profiles: pd.DataFrame,
    cluster_df: pd.DataFrame,
    output_path,
    top_deg: int = 5,
    top_clusters: int = 20,
) -> None:
    top_deg = min(top_deg, len(degree_profiles))
    top_clusters = min(top_clusters, len(cluster_df))

    max_cluster_score = degree_cluster_sim.max(axis=1)
    top_deg_idx = np.argsort(max_cluster_score)[::-1][:top_deg]
    top_deg_labels = degree_profiles.iloc[top_deg_idx]["degree_id"].tolist()

    cluster_df_sorted = cluster_df.sort_values("n_jobs", ascending=False).reset_index(drop=True)
    top_cluster_ids = cluster_df_sorted.head(top_clusters)["cluster_id"].astype(int).tolist()
    top_cluster_labels = cluster_df_sorted.head(top_clusters)["top_category"].astype(str).tolist()

    heatmap_data = degree_cluster_sim[np.ix_(top_deg_idx, top_cluster_ids)]
    fig, ax = plt.subplots(figsize=(16, 6))
    image = ax.imshow(heatmap_data, aspect="auto", cmap="YlOrRd")
    plt.colorbar(image, ax=ax, label="Cosine Similarity")

    ax.set_xticks(range(top_clusters))
    ax.set_xticklabels(top_cluster_labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(top_deg))
    ax.set_yticklabels(top_deg_labels, fontsize=9)
    ax.set_title("Degree-Job Role Cluster Alignment Heatmap", fontsize=13)
    ax.set_xlabel("Job Role Cluster (by MCF Category)", fontsize=10)
    ax.set_ylabel("NUS Degree Programme", fontsize=10)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_degree_alignment_scores(hybrid_matrix: np.ndarray, degree_profiles: pd.DataFrame, output_path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    top1_scores = hybrid_matrix.max(axis=1)

    axes[0].hist(top1_scores, bins=min(10, len(top1_scores)), color="mediumseagreen", edgecolor="white")
    axes[0].axvline(top1_scores.mean(), color="red", linestyle="--", label=f"Mean={top1_scores.mean():.3f}")
    axes[0].set_title("Best Job Match Score per Degree\n(Hybrid Score)")
    axes[0].set_xlabel("Hybrid Alignment Score")
    axes[0].set_ylabel("Number of Degrees")
    axes[0].legend()

    degree_profiles_plot = degree_profiles.copy()
    degree_profiles_plot["max_hybrid_score"] = top1_scores
    top_aligned = degree_profiles_plot.nlargest(min(5, len(degree_profiles_plot)), "max_hybrid_score")[
        ["degree_name", "degree_id", "max_hybrid_score"]
    ]
    labels = [f"{name} ({degree_id})" for name, degree_id in zip(top_aligned["degree_name"], top_aligned["degree_id"])]

    axes[1].barh(labels, top_aligned["max_hybrid_score"], color="steelblue")
    axes[1].set_xlabel("Max Hybrid Alignment Score")
    axes[1].set_title("Top Degrees by Best Job Match")
    axes[1].invert_yaxis()

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

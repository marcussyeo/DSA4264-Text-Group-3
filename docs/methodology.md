# Methodology

## Design Principles

The framework is designed around three public-sector requirements: scale, explainability, and reproducibility. We therefore model curriculum-job alignment as a retrieval and ranking problem rather than a black-box prediction task.

## Data Preparation

We clean module descriptions and job ads, remove postings outside entry-to-mid-career scope, and deduplicate both exact reposts and semantic near-duplicates. The final retrieval corpus contains 17,096 in-scope job ads and 6,957 modules with usable descriptions.

## Degree Profile Construction

Alignment is estimated at the degree level because employers hire from programmes, not from individual modules. Each of the 15 NUS degree profiles aggregates 23-24 curated modules, combining core requirements with common curriculum so programmes are represented comparably. The selected degrees span computing, engineering, business, science, and humanities, which lets the evaluation cover both direct occupational pipelines and broader degrees.

## Alignment Methods

We compare five methods so the final choice is evidence-based rather than assumed.

| Method | Core idea | Why it matters |
| --- | --- | --- |
| Lexical TF-IDF | Matches degrees and jobs by term overlap | Transparent keyword baseline |
| Semantic cosine | Scores cosine similarity between `all-MiniLM-L6-v2` embeddings | Captures related meaning beyond exact wording |
| Skill coverage | Measures overlap between degree text and job skill tags | Highly interpretable explicit-skill signal |
| Hybrid semantic + skill | Combines semantic cosine and skill coverage with a 0.7 / 0.3 weighting | Balances semantic breadth with direct skill evidence |
| Cluster-routed semantic | Combines job-level semantic scores with degree-to-cluster priors from 75 job clusters using a 0.65 / 0.35 weighting | Improves robustness to firm-specific wording and supports scale |

## Evaluation Strategy

All methods are evaluated on the same gold file, `notebooks/evaluation/gold_degree_job_alignment.csv`. After matching the current 15 degree proxies, the benchmark contains 256,350 labelled degree-job pairs: 11,307 `Relevant`, 26,191 `Somewhat Relevant`, and 218,852 `Not Relevant`.

The primary metrics are `Balanced pairwise agreement` and `NDCG@5`. Balanced pairwise agreement tests whether each method orders `Relevant > Somewhat Relevant > Not Relevant` correctly within a degree, while `NDCG@5` rewards placing higher-relevance jobs near the top of the ranked list. We also report strict and relaxed `Precision@k` and `HitRate@k` at `k = 1, 3, 5`. Query-wise Spearman agreement is retained only as a secondary diagnostic because coarse `0/1/2` labels and large tied blocks make full-list correlation less informative for retrieval quality.

## Execution And Reproducibility

The notebook writes cleaned corpora, similarity matrices, cluster priors, and evaluation outputs to cached artifacts and `notebooks/evaluation/*.csv`, so the analysis can be rerun consistently. The same retrieval logic is reused in the `retrieval/` package, API layer, and frontend, which keeps the analytical benchmark and user-facing demo aligned.

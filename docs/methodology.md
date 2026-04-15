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

`all-MiniLM-L6-v2` was chosen because it offers a strong speed-quality trade-off for sentence retrieval. That matters here because the notebook compares every degree against a large job corpus and is intended to be rerun when the labour market refreshes; a larger encoder might improve marginal accuracy, but at higher inference cost and with weaker reproducibility on modest hardware.

The clustering layer uses `K = 75`, which sits in the notebook's intended 50-100 range and is a practical middle ground for a 17,096-job corpus. At this setting, clusters are large enough to form stable role families but not so large that engineering, finance, and communication roles collapse into overly broad groups. The resulting average cluster size is about 228 jobs, which is coarse enough for scalability but still specific enough to preserve occupational structure.

The weights are deliberately conservative rather than aggressively tuned. In the hybrid score, 0.7 / 0.3 keeps semantic similarity as the main signal and uses explicit skill overlap as a supporting adjustment, so generic keyword matches do not dominate. In the cluster-routed score, 0.65 / 0.35 lets the cluster prior stabilise role-family matching without overwhelming evidence from the individual job text.

## Evaluation Strategy

All methods are evaluated on the same gold file, `notebooks/evaluation/gold_degree_job_alignment.csv`. After matching the current 15 degree proxies, the benchmark contains 256,350 labelled degree-job pairs: 11,307 `Relevant`, 26,191 `Somewhat Relevant`, and 218,852 `Not Relevant`.

The final evaluation file stores resolved labels only, so the labelling workflow is only partially recoverable from the repo through the provenance-rich companion file `notebooks/evaluation/gold_degree_job_alignment_my.csv`. That file contains 616 labelled candidate pairs drawn from the union of method-specific high-ranking jobs plus 96 deliberately low-score contrast samples, which helps prevent the benchmark from containing only obvious positives. The three labels are `Relevant`, `Somewhat Relevant`, and `Not Relevant`. Its rationale field suggests that labels were assigned using evidence in job titles, categories, responsibilities, and skill overlap; 190 rows retain explicit evidence-count rationales, while 426 later edge cases carry proxy labels generated from a 15-nearest-neighbour rule over the existing gold signals. The repo does not preserve annotator identities or a formal adjudication log, so this benchmark should be read as a practical internal reference set rather than a fully adjudicated external gold standard.

The primary metrics are `Balanced pairwise agreement` and `NDCG@5`. Balanced pairwise agreement tests whether each method orders `Relevant > Somewhat Relevant > Not Relevant` correctly within a degree, while `NDCG@5` rewards placing higher-relevance jobs near the top of the ranked list. We also report strict and relaxed `Precision@k` and `HitRate@k` at `k = 1, 3, 5`. Query-wise Spearman agreement is retained only as a secondary diagnostic because coarse `0/1/2` labels and large tied blocks make full-list correlation less informative for retrieval quality.

## Execution And Reproducibility

The notebook writes cleaned corpora, similarity matrices, cluster priors, and evaluation outputs to cached artifacts and `notebooks/evaluation/*.csv`, so the analysis can be rerun consistently. The same retrieval logic is reused in the `retrieval/` package, API layer, and frontend, which keeps the analytical benchmark and user-facing demo aligned.

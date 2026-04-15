# Results

## Quantitative Comparison

The current benchmark evaluates 256,350 matched degree-job pairs across 15 degree proxies. It is deliberately difficult and strongly imbalanced, with 218,852 pairs labelled `Not Relevant`, 26,191 labelled `Somewhat Relevant`, and 11,307 labelled `Relevant`. In practical terms, this means a useful method must rank a very small number of relevant jobs ahead of a very large number of irrelevant ones.

Using the notebook's primary retrieval-aligned metric, hybrid semantic + skill is the strongest overall method. It achieves the highest `Balanced pairwise agreement` at 0.835 and the best `Precision@3` at 0.711, which means it is the most reliable at ordering relevant jobs above weaker matches while keeping top-ranked shortlists strong. Cluster-routed semantic is a very close second on pairwise agreement at 0.829, but it is the best method on `NDCG@5` at 0.797 and also leads on `Precision@1 = 0.800` and `Precision@5 = 0.747`. Semantic cosine remains clearly competitive, while lexical TF-IDF and especially skill coverage are materially weaker overall.

| Method | Balanced pairwise agreement | NDCG@5 | Precision@1 | Precision@3 | Precision@5 | Spearman |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Hybrid semantic + skill | 0.835 | 0.747 | 0.733 | 0.711 | 0.680 | 0.310 |
| Cluster-routed semantic | 0.829 | 0.797 | 0.800 | 0.689 | 0.747 | 0.308 |
| Semantic cosine | 0.824 | 0.755 | 0.800 | 0.644 | 0.693 | 0.297 |
| Lexical TF-IDF | 0.799 | 0.535 | 0.400 | 0.489 | 0.453 | 0.289 |
| Skill coverage | 0.704 | 0.348 | 0.333 | 0.244 | 0.280 | 0.213 |

No single method dominates every degree. By `Balanced pairwise agreement`, cluster-routed semantic is best for 7 degrees, hybrid for 4, semantic cosine for 2, and lexical TF-IDF for 2. This supports a portfolio view of evidence rather than a one-model rule. The evaluation therefore does not point to one universally optimal scoring method; instead, it shows that some degree families benefit more from clustering, others from explicit semantic-skill blending, and a few still from direct lexical overlap.

## Degree-Level Patterns

Programmes with clear occupational pipelines perform best. Hybrid reaches `Balanced pairwise agreement = 0.758` for Business Administration and `0.822` for Civil Engineering, while the strongest semantic-family methods achieve `NDCG@5 = 1.000` for both degrees. Cluster-routed semantic is strongest for Computer Science (`0.842`) and Electrical Engineering (`0.833`), which suggests that cluster priors help consolidate differently worded but substantively similar technical roles.

Some disciplines benefit more from direct vocabulary overlap or more specialised ranking behaviour. Communications and New Media is best served by lexical TF-IDF, which records `Balanced pairwise agreement = 0.868`, `NDCG@5 = 1.000`, and `Precision@3 = 1.000`. Architecture is more ambiguous: semantic cosine records the highest pairwise agreement at `0.873`, but `NDCG@5` remains modest, indicating overlap between core architecture roles and adjacent built-environment jobs. Data Science and Analytics is also notable: lexical TF-IDF has the highest pairwise agreement at `0.889`, but cluster-routed semantic achieves a stronger top-of-list profile on `NDCG@5 = 1.000`, which suggests different methods are capturing different aspects of relevance in that domain.

The weakest results remain in diffuse humanities labour markets. History and Southeast Asian Studies achieve best `NDCG@5` scores of only `0.170` and `0.161` respectively, and no method attains non-zero `Precision@3` for Southeast Asian Studies. Psychology is a useful edge case: cluster-routed semantic has the highest pairwise agreement at `0.926`, but its `Precision@3` is only `0.333`. This is precisely why the report prioritises pairwise agreement and `NDCG@5` together rather than relying on a single metric. One metric captures ordering quality across the whole degree-specific ranking, while the other captures how convincing the very top shortlist actually is.

## Interpretation And Recommendations

The evaluation supports a two-tier recommendation. Hybrid semantic + skill is the best primary method for overall benchmarking because it leads on the notebook's main agreement metric and remains straightforward to explain. Cluster-routed semantic is the strongest complementary method when the goal is to surface the best shortlists, since it leads on graded top-5 ranking, `Precision@1`, and `Precision@5`. Semantic cosine is a strong pure baseline and confirms that meaning-based matching carries most of the useful signal. Lexical TF-IDF still matters in selected domains, but it is not strong enough to be the main policy method. Skill coverage should be retained as an interpretable diagnostic rather than used as a standalone ranker.

In policy terms, the framework is most credible as a monitoring tool. Strong scores indicate clear curriculum-job pipelines, while weaker scores flag areas for qualitative review rather than automatic judgement. This is especially important for broad-based degrees, where low measured alignment may reflect diffuse labour-market pathways rather than a genuine curriculum problem.

## Limitations, Biases, And Ethical Considerations

The benchmark is large, but it still reflects one cleaned job corpus and one round of human labels. It is also strongly imbalanced toward negative pairs, which is realistic for retrieval but makes broad humanities and interdisciplinary degrees particularly difficult. Low measured alignment should therefore not be interpreted as low educational or social value, especially for programmes whose outcomes are not fully captured by short job ads. The framework should support expert review, not replace it.

# Results

## Quantitative Comparison

The updated benchmark evaluates 256,350 degree-job pairs across 15 degree proxies. It is highly imbalanced, with 85.4% `Not Relevant`, 10.2% `Somewhat Relevant`, and 4.4% `Relevant`, so strong performance requires ranking a small number of relevant jobs ahead of many negatives.

Using the notebook's primary retrieval-aligned metric, hybrid semantic + skill is the best overall method. It records the highest `Balanced pairwise agreement` at 0.835 and the strongest `Precision@3` at 0.711. Cluster-routed semantic is a close second on pairwise agreement at 0.829, but it is best on `NDCG@5` at 0.797 and also leads on `Precision@1 = 0.800`, `Precision@5 = 0.747`, and `RelaxedPrecision@5 = 0.880`. Semantic cosine remains competitive, while lexical TF-IDF and skill coverage are clearly weaker.

| Method | Balanced pairwise agreement | NDCG@5 | Precision@1 | Precision@3 | Precision@5 | Spearman |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Hybrid semantic + skill | 0.835 | 0.747 | 0.733 | 0.711 | 0.680 | 0.310 |
| Cluster-routed semantic | 0.829 | 0.797 | 0.800 | 0.689 | 0.747 | 0.308 |
| Semantic cosine | 0.824 | 0.755 | 0.800 | 0.644 | 0.693 | 0.297 |
| Lexical TF-IDF | 0.799 | 0.535 | 0.400 | 0.489 | 0.453 | 0.289 |
| Skill coverage | 0.704 | 0.338 | 0.267 | 0.222 | 0.267 | 0.213 |

No single method dominates every degree. By `Balanced pairwise agreement`, cluster-routed semantic is best for 7 degrees, hybrid for 4, semantic cosine for 2, and lexical TF-IDF for 2. This supports a portfolio view of evidence rather than a one-model rule.

## Degree-Level Patterns

Programmes with clear occupational pipelines perform best. Hybrid reaches `Balanced pairwise agreement = 0.758` for Business Administration and `0.822` for Civil Engineering, while the strongest semantic-family methods achieve `NDCG@5 = 1.000` for both degrees. Cluster-routed semantic is strongest for Computer Science (`0.842`) and Electrical Engineering (`0.833`), which suggests that cluster priors help consolidate differently worded but substantively similar technical roles.

Some disciplines benefit more from direct vocabulary overlap. Communications and New Media is best served by lexical TF-IDF, which records `Balanced pairwise agreement = 0.869`, `NDCG@5 = 1.000`, and `Precision@3 = 1.000`. Architecture is more ambiguous: agreement is high across methods, but the best `NDCG@5` is only `0.631`, indicating overlap between core architecture roles and adjacent built-environment jobs.

The weakest results remain in diffuse humanities labour markets. History and Southeast Asian Studies achieve best `NDCG@5` scores of only `0.170` and `0.161` respectively, and no method attains non-zero `Precision@3` for Southeast Asian Studies. Psychology is a useful edge case: hybrid reaches `Precision@3 = 1.000` and `NDCG@5 = 0.869`, but Spearman remains low at `0.111`, which is precisely why the report prioritises pairwise agreement and `NDCG@5` over full-list correlation.

## Worked Example

Civil Engineering shows why the strongest methods are plausible to a policy reader. The top-ranked jobs returned by the semantic-family methods include `Design Engineer/Senior Design Engineer`, `Civil & Structural Engineer / Assistant Civil & Structural Manager`, and `Project Engineer _Civil & Structural`. Their descriptions repeatedly mention drainage, temporary works, structural drawings, tender submissions, site coordination, and compliance with engineering codes. These are not just generic professional terms; they map directly onto the degree's emphasis on structures, infrastructure systems, construction methods, and project delivery.

The same example also shows what the evaluation is testing. It is not enough for a method to retrieve a vaguely technical role. The better methods place clearly civil-engineering roles near the top and keep obvious contrast cases such as nursing or hospitality postings much lower. This is why Civil Engineering achieves both high pairwise agreement and perfect `NDCG@5` for the strongest semantic-family methods: the ordering is not only relevant in aggregate, but substantively credible when individual job descriptions are read.

## Interpretation And Recommendations

The evaluation supports a two-tier recommendation. Hybrid semantic + skill is the best primary method for overall benchmarking because it leads on the main agreement metric and remains easy to explain. Cluster-routed semantic is the strongest complementary method when the goal is to surface the best shortlists, since it leads on graded top-5 ranking, `Precision@1`, and `Precision@5`. In policy terms, the framework is most credible as a monitoring tool: strong scores indicate clear curriculum-job pipelines, while weaker scores flag areas for qualitative review rather than automatic judgement.

## Limitations, Biases, And Ethical Considerations

The benchmark is large, but it still reflects one cleaned job corpus and one round of human labels. Low measured alignment should not be interpreted as low educational or social value, especially for broad degrees whose outcomes are not fully captured by short job ads. The framework should therefore support expert review, not replace it.

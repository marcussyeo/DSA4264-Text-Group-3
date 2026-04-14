# Results

## Quantitative Comparison

The evaluation benchmark covers 15 degree proxies and 256,350 matched degree-job pairs. It is deliberately demanding: every degree is assessed against a large pool of jobs, and the label distribution is highly imbalanced, with 85.4% of pairs marked `Not Relevant`, 10.2% marked `Somewhat Relevant`, and 4.4% marked `Relevant`. This makes both ranking quality and top-of-list precision important. A useful method must not only surface at least one good match, but also place genuinely relevant jobs ahead of a large number of irrelevant ones.

Cluster-routed semantic retrieval performs best on pooled ranking quality, achieving the highest global agreement with human judgement at 0.413. The hybrid semantic-plus-skill score is a very close second at 0.402 and achieves the best mean per-degree human-model agreement at 0.310, suggesting that it is the most balanced method across disciplines. Plain semantic cosine remains competitive at 0.389 global agreement, while lexical TF-IDF and skill coverage are materially weaker overall.

| Method | Global agreement | Mean human-model agreement | Precision@1 | Precision@5 | Relaxed Precision@5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cluster-routed semantic | 0.413 | 0.308 | 0.800 | 0.747 | 0.880 |
| Hybrid semantic + skill | 0.402 | 0.310 | 0.733 | 0.680 | 0.840 |
| Semantic cosine | 0.389 | 0.297 | 0.800 | 0.693 | 0.840 |
| Lexical TF-IDF | 0.363 | 0.289 | 0.400 | 0.453 | 0.720 |
| Skill coverage | 0.279 | 0.213 | 0.333 | 0.280 | 0.467 |

The strongest methods are therefore the ones that capture meaning rather than relying only on exact word overlap. Cluster-routed semantic achieves the highest `Precision@5`, while both cluster-routed and plain semantic reach `Precision@1 = 0.800`. This indicates that semantic information is especially valuable for putting the single best match near the top. The hybrid method remains especially attractive for practical use because it gives slightly lower top-end precision than cluster-routed semantic, but stronger average agreement across degrees and a clearer explanation structure through its semantic and skill components.

At the same time, no single method dominates every degree family. Cluster-routed semantic is the best by agreement for 7 degree proxies, hybrid semantic plus skill for 4, and lexical TF-IDF for 4. This variation is substantively meaningful. Technical and professionally structured programmes benefit from semantic structure and clustering, whereas some broader or language-heavy programmes still benefit from direct vocabulary overlap.

## Degree-Level Patterns

The clearest alignment appears in programmes with direct occupational pipelines. Business Administration records the strongest degree-level agreement, with the hybrid method reaching 0.551 and the top semantic-family methods all achieving perfect `Precision@5`. Civil Engineering shows a similar pattern, with hybrid again leading at 0.473 and the strongest methods retrieving highly relevant engineering roles consistently near the top. Computer Science and Electrical Engineering are also well served by cluster-routed semantic retrieval, which suggests that job clustering helps when employers describe closely related technical roles in varied ways.

The results are more mixed for broad, interdisciplinary, or humanities-oriented degrees. Communications and New Media is best served by lexical TF-IDF, which implies that shared vocabulary still carries strong signal in that domain. Architecture is an important edge case: hybrid has the best agreement at 0.424, but strict top-k precision remains modest, which is consistent with a labour market where adjacent built-environment roles overlap heavily with core architecture roles. History, Psychology, and Southeast Asian Studies are the most difficult cases overall. Their agreement scores are low across all methods, indicating that broad curricular content does not map as cleanly to current job-ad language as tightly regulated or strongly vocational degrees do.

| Degree proxy | Best method by agreement | What the result suggests |
| --- | --- | --- |
| Business Administration | Hybrid semantic + skill | Strong direct alignment and high consistency across top-ranked roles |
| Civil Engineering | Hybrid semantic + skill | Clear occupational pipeline with robust engineering matches |
| Computer Science | Cluster-routed semantic | Clustering helps consolidate closely related technical roles |
| Communications and New Media | Lexical TF-IDF | Shared vocabulary remains a strong signal in communication-heavy jobs |
| Architecture | Hybrid semantic + skill | Core and adjacent built-environment roles are both relevant |
| History / Southeast Asian Studies | No clearly strong method | Labour-market alignment is diffuse and harder to capture from job text alone |

## Interpretation And Recommendations

Three conclusions follow from these findings. First, curriculum-job alignment should be treated as a portfolio of evidence rather than a single model output. Cluster-routed semantic is the strongest overall ranking method, but hybrid semantic plus skill is more balanced across degrees and easier to explain to non-technical stakeholders. Second, the framework is most persuasive when used to identify patterns rather than to issue binary judgements. Strong scores for programmes such as Business Administration, Civil Engineering, and Computer Science provide evidence of clear labour-market fit, while weaker scores for broad-based programmes point to the need for more careful interpretation rather than immediate policy intervention. Third, exact skill overlap should be retained as a supporting diagnostic rather than used on its own, since skill coverage by itself consistently underperforms the richer text-based methods.

For policy use, the most credible recommendation is to use cluster-routed semantic retrieval as the primary offline benchmarking method, while retaining the hybrid score in stakeholder-facing applications because it is easier to interpret and only slightly less accurate overall. Reviewers should also inspect representative matched jobs alongside the numeric scores, especially for interdisciplinary degrees where alignment is diffuse. In practice, this framework is best positioned as an early warning and monitoring tool that can guide curriculum review, employer consultation, and deeper human investigation.

## Limitations, Biases, And Ethical Considerations

Several limitations remain important. The job corpus still reflects only one week of postings, so the results should be read as a market snapshot rather than a stable long-run equilibrium. The degree proxies are curated rather than exhaustive and therefore may miss specialised electives or informal learning pathways. The evaluation benchmark is also highly imbalanced toward `Not Relevant` pairs, which is realistic for large-scale ranking but makes broad agreement harder to achieve and means that weakly aligned degrees can appear especially difficult. Finally, the analysis still reflects the language and composition of MyCareersFuture postings rather than the entire labour market.

There are also ethical implications. Low measured alignment does not imply that a programme lacks value; some degrees serve civic, scientific, cultural, or foundational purposes that are not well represented in short-form job advertisements. The framework should therefore be used to support review, not to automate programme judgement. The current scope filters are another policy choice: excluding internships, academia, and very senior leadership roles makes the comparison more focused, but different policy questions may require different scope rules. Future work should extend the analysis over time, widen institutional coverage, and build a larger independently annotated benchmark.

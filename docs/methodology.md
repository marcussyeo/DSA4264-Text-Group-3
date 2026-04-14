# Methodology

## Design Principles

The methodology was built around three public-sector constraints. First, the system must scale to thousands of modules and tens of thousands of job ads. Second, the scoring logic must remain explainable enough for curriculum review. Third, the workflow must be reproducible so that results can be refreshed when labour-market conditions change. These constraints favour retrieval and ranking over black-box prediction.

At a high level, the pipeline cleans both corpora, constructs degree-level text profiles, embeds text into a shared semantic space, compares multiple ranking methods, and evaluates them against a labelled reference set. The notebook implementation is the analytical ground truth for the report, while the app and API expose a lightweight interface for interactive use.

## Data Preparation

The data was cleaned and preprocessed as detailed in the Data section.

## Degree Profile Construction

### Rationale

Employers do not hire based on whether a student took a specific course but rather on the degree programme as a whole. Therefore, our framework operates at the degree level and not the module level.

### Degree and Module Selection

We construct 15 degree profiles using a curated module lists. For each degree, the module basket consists of:

| Component | Count | Description |
|:---|:---:|:---|
| **Core modules** | 15 | Degree-specific required courses |
| **Common curriculum modules** | 8-9 | University-level requirements |
| **Total per degree** | 23-24 | Combined text from all modules |

**Note:** Not every degree has exactly 23 modules. The actual counts vary slightly depending on the specific programme structure (e.g., Accounting has 24 modules). However, we ensure that all degrees are represented almost equally by keeping the module count for each degree within a tight range (23-24 modules). This prevents any single degree from dominating similarity scores simply because it has more textual content.

The 15 degrees are chosen to represent the major undergraduate programmes in NUS across technical and non-technical domains, capturing the specturm of skills reflected in the EDA.<br>
- **Faculty of Science**: Data Science and Analytics (dsa), Data Science and Economics (dse) and Pharmacy (pharm)<br>
- **Faculty of Arts and Social Science**: Communications and New Media (cnm), History (hist), Psychology (psych) and Southeast Asian Studies (sea)<br>
- **NUS Business School**: Business Administration (biz) and Accountancy (acc)<br>
- **NUS Computing**: Computer Science (cs) and Business Analytics (bza)<br>
- **College of Desgin and Engineering**: Civil Engineering (ce), Chemical Engineering (chem_eng), Electrical Engineering (ee) and Architecture (archi)<br> 

## Alignment Methods

We compare five methods so that the final recommendation is justified against alternatives rather than chosen a priori.

| Method | Core idea | Why it matters |
| --- | --- | --- |
| Lexical TF-IDF | Matches degrees and jobs using surface-term overlap | Strong transparent baseline; reveals whether simple keyword matching is enough |
| Semantic cosine | Embeds curriculum and jobs with `all-MiniLM-L6-v2` and scores cosine similarity | Captures paraphrase and related concepts beyond exact keywords |
| Skill coverage | Measures overlap between degree text and structured job skill tags | Highly interpretable signal tied to employer-declared skills |
| Hybrid semantic + skill | Combines semantic cosine and skill coverage with a 0.7 / 0.3 weighting | Balances broad semantic meaning with explicit skill evidence |
| Cluster-routed semantic | Clusters jobs into 75 role groups, builds cluster priors, then combines them with job-level semantic similarity using a 0.65 / 0.35 weighting | Improves scalability and reduces sensitivity to firm-specific wording |

The semantic method uses the sentence-transformer model `all-MiniLM-L6-v2` with unit-normalised embeddings, so cosine similarity can be computed efficiently as a dot product. Embeddings and intermediate matrices are cached to disk as NumPy arrays and Parquet files, which keeps reruns fast and reproducible. The clustering layer uses MiniBatchKMeans on job embeddings to create 75 job-role clusters, then derives degree-to-cluster similarity from cluster centroids. This makes the analysis more stable when several employers describe the same role in slightly different ways.

The repository’s interactive search service uses the same general logic but in a streamlined form. Module-to-job and job-to-module lookups rely on semantic similarity, while degree-to-job lookups use the hybrid semantic-plus-skill score when the skill-overlap matrix is available. This is a deliberate execution choice: the hybrid score is slightly less accurate than the best cluster-routed method in offline evaluation, but it is easier to explain in an interactive interface because users can understand both components of the score.

## Evaluation Strategy

Evaluation is performed on the internal gold dataset stored in `notebooks/evaluation/gold_degree_job_alignment.csv`. The current benchmark contains 616 labelled degree-job pairs across 15 degree proxies. It combines top-ranked candidates from different methods with deliberately chosen low-score contrast samples, which makes it more credible than evaluating only on obvious positives. The label distribution is 476 Relevant, 52 Somewhat Relevant, and 88 Not Relevant.

We report precision-oriented ranking metrics at `k = 1, 3, 5` and a human-model agreement score. Strict precision counts only labels marked Relevant. Relaxed precision treats both Relevant and Somewhat Relevant as acceptable matches. This distinction matters in education-policy settings because many curriculum-job links are partial rather than binary. A role may be adjacent to a degree even if it is not the most direct destination.

## Execution And Reproducibility

The codebase is organised so that analysis, serving, and presentation remain separate. The notebook workflow generates cleaned corpora, embeddings, cluster assignments, evaluation tables, and figures. The `retrieval/` package exposes reusable search logic, `scripts/build_chat_index.py` builds cached artifacts, `scripts/run_retrieval_server.py` serves them over HTTP, and the Next.js frontend in `app/` and `components/` provides a deterministic chat-style interface. A unit test suite in `tests/test_retrieval.py` checks core behaviours such as module lookup, degree lookup, typo suggestions, and job-to-module retrieval.

This design improves execution quality in two ways. First, the analytical path remains transparent and auditable. Second, the user-facing demo can be inspected without rerunning the entire notebook. For public-sector deployment, this separation is valuable because it distinguishes the policy logic from the interface layer and makes future refreshes easier to govern.

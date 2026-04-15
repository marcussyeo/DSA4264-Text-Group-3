# Appendix

## Reproducibility Notes

The documentation site is written in Markdown and rendered with MkDocs Material through `mkdocs.yml`. The main implementation references are:

| Component                         | Purpose                                                |
| --------------------------------- | ------------------------------------------------------ |
| `notebooks/main.ipynb`            | End-to-end analysis, evaluation, and figure generation |
| `retrieval/data.py`               | Text cleaning and corpus construction utilities        |
| `retrieval/search.py`             | Deterministic retrieval logic for jobs and modules     |
| `scripts/build_chat_index.py`     | Offline artifact builder                               |
| `scripts/run_retrieval_server.py` | HTTP API for the demo app                              |
| `tests/test_retrieval.py`         | Basic regression tests for retrieval behaviour         |

To rebuild the documentation locally, install `requirements-docs.txt` and run `mkdocs serve`. To refresh the demo artifacts, run `.venv/bin/python scripts/build_chat_index.py`, then start the API with `.venv/bin/python scripts/run_retrieval_server.py` and the frontend with `npm run dev`.

---

## Notes On Interpretation

- The notebook analysis profiles 15 curated degree proxies, while the app is a lighter exploratory interface.
- Degree-to-job scores aggregate evidence from top-matching modules rather than from a single module.
- Offline results split by metric: hybrid leads balanced pairwise agreement, while cluster-routed semantic leads `NDCG@5` and several top-k precision metrics. The app still prioritises the hybrid score for degree lookups because it is easier to explain.

---

## Data Cleaning Pipelines

### NUSMods Cleaning Pipeline

**Step 1: Load raw module data**
- Read `modules.csv` into a dataframe.
- Retained module metadata such as `moduleCode`, `title`, `description`, `faculty`, and `department`.

**Step 2: Clean module text**
- Removed HTML tags from `description`.
- Normalised whitespace in both `description` and `title`.

**Step 3: Handle missing or weak descriptions**
- Marked descriptions with length `<= 20` characters as insufficient.
- Used the module title as a fallback description only if:
  - the cleaned title had at least 8 characters; and
  - the title did not match a project-like pattern such as `capstone`, `dissertation`, `final year project`, `internship`, `practicum`, `project`, `seminar`, or `thesis`.
- Recorded whether title fallback was used via `used_title_fallback`.

**Step 4: Construct module text**
- Combined cleaned title and cleaned description into a single `module_text` field.

**Step 5: Derive module level features**
- Extracted the first numeric digit from `moduleCode` to derive `level`.
- Marked modules as undergraduate if `level` was between 1 and 4.

**Step 6: Remove rows without usable semantic text**
- Kept only modules with either:
  - cleaned descriptions longer than 20 characters; or
  - an approved title fallback.

**Step 7: Prepare module text for degree profiles**
- Merged cleaned module text into the degree-to-module mapping.
- Retained only mapped modules with non-empty `description_clean`.
- Built `module_profile_text` as:
  - `moduleCode. description_clean`
  - plus `Skills: description_skills.` when extracted description skills were available.

**Step 8: Build degree-level profile text**
- Grouped modules by degree.
- Ordered modules by requirement group (`core` before `common`) and module order.
- Concatenated module texts into a single `profile_text` per degree.
- Capped each degree profile at `MAX_WORDS_PER_PROFILE = 8000` words.

**Output**
- `degree_modules`: cleaned module-level dataset used in profile construction
- `degree_profiles`: one aggregated text profile per degree

### MyCareersFuture Job Ads Cleaning Pipeline

**Step 1: Load and flatten raw job postings**
- Loaded job postings from JSON into tabular format.
- Extracted fields including `title`, `description_raw`, `skills`, `categories`, `position_levels`, `employment_types`, company information, salary, and posting date.

**Step 2: Clean job descriptions**
- Removed HTML tags from raw descriptions.
- Removed URLs.
- Split descriptions into sentence-like segments.
- Dropped boilerplate segments matching predefined patterns such as:
  - licence or registration references
  - “we regret that only shortlisted candidates”
  - “interested applicants”
  - “apply now”
  - “by submitting your resume”
  - “personal data”
  - “for quicker response”
- Recombined remaining segments into `description_clean`.

**Step 3: Remove low-information rows**
- Dropped rows where `description_clean` had length `<= 30` characters.
- Dropped duplicate `job_id` entries.

**Step 4: Standardise list-valued fields**
- Converted `skills`, `categories`, `position_levels`, and `employment_types` into Python lists.
- Parsed list-like strings where needed.

**Step 5: Clean skill tags**
- Normalised skills by lowercasing, stripping punctuation, and removing duplicates.
- Removed low-information skills using:
  - a generic skill stoplist (e.g. `team player`, `communication`, `leadership`)
  - a minimum length rule for short tokens unless whitelisted (e.g. `r`, `sql`, `nlp`)
  - a document-frequency threshold, removing overly common skills appearing in more than `8%` of job ads unless whitelisted
- Saved filtered skills as `skills_clean`.

**Step 6: Build structured job text**
- Constructed `job_text` from:
  - title
  - category labels
  - cleaned skill tags
  - the first `120` words of `description_clean`

**Step 7: Classify role scope**
- Marked each job as in-scope or excluded using title, company, categories, position levels, and employment types.
- Excluded:
  - internships and student assistant roles
  - academic roles
  - tuition/teaching roles
  - very senior roles such as chief, director, vice president, president, head of, managing director, partner, or jobs tagged as senior management

**Step 8: Remove exact repost duplicates**
- Built a `job_fingerprint` from normalised title, company or fallback SSOC code, and cleaned description.
- Sorted postings by fingerprint, posting date, salary, and job ID.
- Kept only the first row in each exact-duplicate group.

**Step 9: Remove semantic near-duplicates**
- Grouped remaining in-scope jobs by normalised title plus company (or SSOC fallback).
- Within each group, computed character n-gram TF-IDF similarity over description, skills, and categories.
- Marked jobs as semantic near-duplicates when cosine similarity was at least `0.985`.
- Skipped semantic clustering for groups larger than `40` rows.
- Kept only the first row in each semantic duplicate cluster.

**Step 10: Finalise filtered corpus**
- Sorted retained jobs by posting date and job ID.
- Used this final corpus for embeddings, retrieval, and evaluation.

**Output**
- `jobs`: final in-scope, deduplicated job corpus
- `jobs_scope_audit`: audit table covering scope and duplicate decisions
- `jobs_excluded`, `jobs_exact_removed`, `jobs_semantic_removed`: exclusion and deduplication audit subsets

---

## Gold Dataset Construction 

The evaluation dataset is stored as `gold_degree_job_alignment.csv`.

The raw file contains the following columns:
- `degree_id`
- `degree_name`
- `job_id`
- `job_title`
- `human_label`

The code maps the human labels into a three-level ordinal relevance scale:
- `Relevant` = 2
- `Somewhat Relevant` = 1
- `Not Relevant` = 0

### Gold Dataset Standardisation

Before evaluation, the gold dataset is standardised to ensure compatibility with the cached degree and job artefacts.

**Step 1: Resolve equivalent column names**
- If needed, `curriculum_id` is mapped to `degree_id`.
- If needed, `curriculum_title` is mapped to `degree_name`.

**Step 2: Standardise labels**
- If `human_relevance_score` is absent, it is derived from `human_label`.
- Only rows with valid scores in `{0, 1, 2}` are retained.
- Labels are normalised back into the canonical text labels:
  - `Relevant`
  - `Somewhat Relevant`
  - `Not Relevant`

**Step 3: Normalise identifiers**
- Trimmed whitespace in `degree_id`, `degree_name`, and `job_id`.

**Step 4: Fill missing metadata**
- If absent, the code merges in:
  - `job_title`
  - `job_categories`
  - `job_text`
  - `company`

**Step 5: Create query identifiers**
- If absent, `query_id` is set to `degree_id`.

---

## Degree Profile Construction

The final degree profiles are stored in a structured format (`degree_to_module_map.csv`), where:

- Each row corresponds to a module  
- Each module is associated with a specific degree  

### Role in Overall Framework

By explicitly designing degree profiles rather than relying on raw module groupings, we ensure that the analysis aligns more closely with how employers interpret educational qualifications.

To bridge this mismatch in granularity, we construct **degree profiles** as an intermediate representation. These profiles aggregate module-level information into a unified textual representation that approximates the knowledge and skills acquired within a degree programme.

### Design Rationale

The construction of degree profiles is guided by two key principles:

1. **Representativeness**  
   Each degree should capture the core competencies expected of graduates in that discipline.

2. **Comparability**  
   Degree profiles should be structured in a consistent manner to allow fair comparison across disciplines.

### Selection of Degrees

The 15 degrees are chosen to represent the major undergraduate programmes in NUS across technical and non-technical domains, capturing the spectrum of skills reflected in the EDA.<br>
- **Faculty of Science**: Data Science and Analytics (dsa), Data Science and Economics (dse) and Pharmacy (pharm)<br>
- **Faculty of Arts and Social Science**: Communications and New Media (cnm), History (hist), Psychology (psych) and Southeast Asian Studies (sea)<br>
- **NUS Business School**: Business Administration (biz) and Accountancy (acc)<br>
- **NUS Computing**: Computer Science (cs) and Business Analytics (bza)<br>
- **College of Desgin and Engineering**: Civil Engineering (ce), Chemical Engineering (chem_eng), Electrical Engineering (ee) and Architecture (archi)<br> 

### Module Selection Strategy

For each degree, a curated set of modules was selected to form the degree profile. The selection process is based on:

- **Core programme requirements**, which define the degree-specific required courses  
- **University-level requirements**, which capture necessary vourses all NUS grads have to take for a holistic learning (differs from faculty to faculty as each may have their own iteration of the course)  

These modules contribute to transferable skills such as:<br>
- Communication  
- Critical thinking  
- Interdisciplinary understanding  

### Handling of Module Count

Degree programmes vary in the number of modules required. However, embeddings used in this study are length-normalised, meaning that differences in text length do not disproportionately influence similarity scores.

As such, strict uniformity in module count is not required. Nevertheless, care was taken to ensure that each degree profile contains a comparable number of modules to maintain consistency in representation.

### Exclusion of Internship Modules

Internship modules were excluded from the degree profiles.

These modules were removed for the following reasons:

- They often lack standardised textual descriptions  
- Skills develop varies significantly across students  
- They introduce noise into the embedding process  

Excluding these modules improves the consistency and reliability of the degree representations.

### Assumptions

The construction of degree profiles relies on several assumptions:

- Module descriptions accurately reflect the skills and knowledge taught  
- Aggregated module descriptions approximate the overall learning outcomes of a degree  
- Selected modules are representative of the typical student experience  

These assumptions are necessary to operationalise degree-level analysis but may not fully capture individual variation in student pathways.

### Limitations

Despite its structured design, this approach has several limitations:

- **Subjectivity in module selection**: The curation process may introduce bias  
- **Lack of specialisation tracks**: Degree profiles do not capture individual student choices  
- **Implicit skill representation**: Some skills may not be explicitly mentioned in module descriptions  

These limitations suggest that results should be interpreted as approximations rather than precise measurements.


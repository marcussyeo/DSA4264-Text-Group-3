# Data

This section details the two primary datasets used in this project: the NUS Module Repository and the MyCareersFuture job postings. It covers the collection, cleaning, and exploratory analysis performed to assess data quality and inform subsequent modelling decisions.

## Data Collection and Cleaning

### NUSMods 

Course data was obtained from the NUSMods API which was then compiled into a CSV file (`modules.csv`) containing 7,015 rows and 14 columns. Key fields include:

| Field | Description |
|:---|:---|
| `moduleCode` | Unique course identifier (e.g., ABM5001) |
| `title` | Course title |
| `description` | Detailed course description |
| `faculty` | Offering faculty (e.g., Arts and Social Science, Computing) |
| `prerequisite` | Required prior modules |
| `moduleCredit` | Academic credit units |

**Cleaning Steps:**

1.  **Missing Description Handling**: Only 147 rows (2.1%) had missing descriptions. For 192 of these, the `title` was used as a descriptive fallback. Project-like modules (e.g., "Dissertation", "UROPS") with missing descriptions (93 rows) were excluded from the primary text analysis to prevent noise.
2.  **Feature Engineering**: A `level_band` feature was created by extracting the first digit of the `moduleCode` to distinguish undergraduate (1-4xxx) from postgraduate (5xxx+) courses.
3.  **Duplicate Check**: `moduleCode` is unique across all rows, confirming one row per module.

### MyCareersFuture Job Ads

The job dataset consisted of 22,720 JSON files from the MyCareersFuture portal. A custom Python loader was developed to flatten nested JSON structures into a tabular format.

**Key Extracted Fields:**

| Field | Description |
|:---|:---|
| `title` | Job title |
| `skills` | List of required skills (extracted from nested `skills` array) |
| `categories` | List of job categories (extracted from nested `categories` array) |
| `minimum_years_experience` | Minimum experience required |
| `salary_min` / `salary_max` | Monthly salary range |
| `posted_date` / `expiry_date` | Posting and application deadline dates |
| `position_levels` | Seniority level (e.g., Entry, Junior Executive, Manager) |

**Cleaning Steps:**

1.  **Structured Field Preservation**: Multi-label fields (`skills`, `categories`, `position_levels`, `employment_types`) were preserved as Python lists to maintain their inherent structure for analysis.
2.  **Feature Engineering**:
    - `salary_mid` = mean of `salary_min` and `salary_max`
    - `posting_window_days` = `expiry_date` - `posted_date`
    - `primary_category` = first element of `categories` list
    - `primary_position_level` = first element of `position_levels` list
3.  **Date Parsing**: All date fields were converted to datetime objects for temporal analysis.

---

## Exploratory Data Analysis (EDA)

 EDA was conducted to answer decision-oriented questions: Are the data of sufficient quality? What are the key characteristics of each dataset? What structural complexities must our model account for?

### NUSMods

#### Distribution by Faculty

The modules in NUSMods is not evenly distributed across faculties. `Arts and Social Science` alone contributes approximately 23.5% of all rows, followed by the `College of Design and Engineering` and `Science`.

**Figure 1: Distribution of Modules by Faculty**

![Module Distribution by Faculty](EDA_mod_dist_by_fac.png)
*Caption: Arts and Social Science, College of Design and Engineering, and Science are the largest contributors to the module catalogue, representing over half of all courses.*

**Key Finding:** This imbalance is useful context when interpreting any aggregate module-text statistics, as larger faculties will naturally dominate corpus-level analyses.

#### Description Length Quality

The median description length is 87 words, providing sufficient semantic content for downstream matching. However, the distribution shows a normal spread with a small number of outliers containing very long descriptions (over 250 words).

**Figure 2: Distribution of Description Length (Words)**

![Description Length Distribution](EDA_mod_desc_length.png)
*Caption: Most module descriptions contain between 60-100 words, providing sufficient context for skill extraction. The boxplot reveals a small number of outlier modules with exceptionally long descriptions.*

---

### MyCareersFuture Job Ads

#### Market Breadth and Top Skills

The dataset captures a broad and information-rich snapshot of Singapore's labor market. The most frequently occurring job title is `SUPERVISOR`, while the most common category is `Sales / Retail`. Critically, the most frequently tagged skill is `team player`, followed closely by `interpersonal skills` and `customer service`.

**Figure 3: Top Job Titles, Categories, and Tagged Skills**

![Top Job Market Features](EDA_job_skill_dist.png)
*Caption: The left panel shows the most common job titles (Supervisor, Quantity Surveyor). The middle panel confirms Sales/Retail and Engineering as dominant categories. The right panel reveals that soft skills like "team player" and "interpersonal skills" are the most frequently requested, alongside technical skills like "Microsoft Office."*

**Key Finding:** Skill tagging is dense rather than sparse. The median job carries 15 skill labels, providing a rich structured signal for matching. The prominence of soft skills highlights that employers value both technical and interpersonal competencies.

#### Category Co-occurrence

An analysis of category co-occurrence shows that jobs are rarely assigned a single category. For example, a Marketing job frequently also belongs to Sales / Retail or Events / Promotions. The co-occurrence matrix below quantifies these relationships.

**Figure 4: Category Co-occurrence Matrix**

![Category Co-occurrence](EDA_job.png)
*Caption: The matrix shows the frequency with which pairs of categories appear together in the same job posting. The strongest co-occurrence (Engineering and Building and Construction) appears 705 times, indicating that job functions are not mutually exclusive.*

#### Seniority and Experience

Critically for policy alignment, the job market leans heavily toward early-career roles of 0-3 years of experience.

**Figure 5: Job Position Level**

![Category Co-occurrence](EDA_job_seniority.png)
*Caption: Executive, Fresh/entry level, and Non-executive roles show the highest posting volumes, while median monthly salary increases predictably with seniority. This confirms the dataset's strong representation of entry-to-mid career positions.*

**Key Finding:** This distribution aligns directly with the profile of fresh university graduates, supporting the use of this corpus for undergraduate curriculum alignment.

---

### Insights for Modelling

The exploratory analysis revealed seven critical dataset characteristics that directly informed our modelling architecture. Each finding translated into specific implementation decisions in the alignment framework.

| Finding | Implication for Modelling | Implementation in Notebook |
|:---|:---|:---|
| Descriptions present for 97.9% of modules; median length 87 words | Text-based skill extraction is feasible; degree profiles can be constructed from module descriptions | Section 2: `MAX_WORDS_PER_PROFILE=8000` captures all content while bounding embedding computation |
| Faculty distribution is uneven (Arts and Social Science dominates 23.5% of modules) | - Using all faculty modules would bias toward larger faculties; degree-specific module baskets ensure fair comparison<br>- Embedding normalisation further mitigates length bias by projecting vectors onto a unit sphere | Section 2: Each degree uses prescribed module baskets (about 15 core + 8 common modules). Section 3: `model.encode(..., normalize_embeddings=True)` ensures all embeddings are length-normalised, making cosine similarity equivalent to dot product and preventing longer texts from dominating similarity scores |
| 75.7% of jobs require ≤3 years experience; entry-level roles dominate | Corpus aligns with undergraduate focus; exclude senior roles and internships to prevent skew | Section 1b: `classify_role_scope()` excludes internships and very senior positions (Chief, Director, VP) |
| Median job lists 15 structured skills; skill tagging is dense | Rich structured signal for matching; preserve list format and use Jaccard-based coverage scoring | Section 5: `job_skill_coverage()` uses Jaccard similarity; β=0.3 weight in hybrid alignment |
| Categories co-occur frequently (e.g., Engineering + Building & Construction appears 705 times) | Treat categories as a set, not a single label; use embedding-based clustering to capture functional similarity | Section 6: K=75 MiniBatchKMeans on job embeddings; cluster labeling reveals natural cross-category groupings |
| Soft skills ("team player", "interpersonal skills") are most frequent | Low discriminative power; filter generic skills to prevent false positives | Section 0 & 5: Generic skill stoplist + 8% document frequency threshold |
| Job descriptions contain recruiter boilerplate | Truncation and pattern-based filtering removes non-semantic content | Section 1b: `JOB_DESC_WORD_LIMIT=120` + pattern matching for common disclaimer text |


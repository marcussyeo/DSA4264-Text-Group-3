# Data

## Data Overview

### 1. NUSMods

Course data was retrieved from the NUSMods API and compiled into `modules.csv` (7,015 rows, 14 columns).

| Core Fields    | Description        |
| :------------- | :----------------- |
| `moduleCode`   | Unique identifier  |
| `title`        | Course title       |
| `description`  | Course description |
| `faculty`      | Offering faculty   |
| `prerequisite` | Required modules   |
| `moduleCredit` | Credit units       |

---

### 2. MyCareersFuture Job Ads

The dataset consists of 22,720 job postings, flattened from JSON into structured format.

| Core Fields                   | Description         |
| :---------------------------- | :------------------ |
| `title`                       | Job title           |
| `skills`                      | Required skills     |
| `categories`                  | Job categories      |
| `minimum_years_experience`    | Experience required |
| `salary_min` / `salary_max`   | Salary range        |
| `posted_date` / `expiry_date` | Posting dates       |
| `position_levels`             | Seniority level     |

---

## Exploratory Data Analysis (EDA)

EDA identifies structural properties that inform modelling choices and potential sources of bias.

---

## NUSMods

### Distribution by Faculty

![Module Distribution by Faculty](assets/EDA_mod_dist_by_fac.png)

_Figure 1: Module representation is uneven, with FASS, CDE, and Science dominating the corpus._

Implications for Framework:<br>
- Risk of representation bias in similarity matching
- Mitigation: - Construct degree-specific module baskets (≈15 core + 8 common modules)
- Use length-normalised embeddings for fair comparison

---

### Description Length

![Description Length Distribution](assets/EDA_mod_desc_length.png)

_Figure 2: Most descriptions fall within 60–100 words, with few long outliers (>250 words)._

Implications for Framework:<br>
- Descriptions provide sufficient semantic signal for embeddings.  
- Text length is bounded during profile construction to control computational cost.

---

## MyCareersFuture Job Ads

### Market Breadth and Skills

![Top Job Market Features](assets/EDA_job_skill_dist.png)

_Figure 3: Soft skills (e.g., teamwork, communication) dominate job postings._

Implications for Framework:<br>
- These skills are non-discriminative and introduce noise.  
- They are removed during preprocessing.

---

### Category Co-occurrence

![Category Co-occurrence](assets/EDA_job.png)

_Figure 4: Job categories frequently co-occur, reflecting overlapping roles._

Implications for Framework:<br>
- Categories are retained as structured features to enrich representations.

---

### Seniority and Experience

![Min Years Experience](assets/EDA_job_seniority.png)

_Figure 5: Entry-level roles dominate, though senior roles exist._

Implications for Framework:<br>
- Aligns with graduate outcomes
- Senior roles are excluded to maintain relevance

---

## Data Cleaning and Preprocessing

### NUSMods

1. **Standardise text**: Remove HTML and normalise whitespace

2. **Handle missing descriptions**: Use title as fallback if informative and exclude generic modules (e.g., internship, UROPS)

3. **Construct module text**: Combine cleaned title and description

4. **Filter by relevance**: Derive module level from code and retain undergraduate modules

5. **Remove low-quality entries**: Drop modules without sufficient text

---

### MyCareersFuture Job Ads

1. **Parse and structure data**: Convert JSON into structured format and preserve multi-label fields

2. **Clean text fields**: Remove HTML, URLs, and boilerplate, then filter low-information descriptions

3. **Clean skills**: Standardise text (lowercase), remove generic soft skills and retain meaningful technical terms

4. **Filter by scope**: Exclude internships, academic, and senior roles

5. **Deduplicate postings**: Remove exact and near-duplicates

6. **Construct job text**: Combine title, categories, skills and truncated description

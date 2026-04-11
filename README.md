# DSA4264 Text Group 3

## Case Topic

You are a team of data scientists in the
Ministry of Education, focusing on
higher education (universities)

Given the recent shifts in the global
economy and technological
developments, you have been tasked
to use a data-driven approach to
assess how well university courses
are preparing students today for
real-world jobs.

## Methodology

1. **Define scope** — Specify which degrees, graduate/seniority levels, and job types are in scope to make "alignment" operational. Output: written task definition.
2. **Ingest and QA data** — Parse modules and job ads, strip HTML, and track missingness, malformed rows, duplicates, and date coverage to support trustworthy coverage claims. Output: clean source tables and QA report.
3. **Filter and deduplicate jobs** — Remove or stratify out-of-scope roles and consolidate near-identical ads to stop noisy rankings. Output: curated job corpus.
4. **Construct auditable degree baskets** — Define core, common, and specialisation modules with explicit weights and provenance for defensible degree-level matching. Output: per-degree basket table.
5. **Build model-ready representations** — Create compact degree summaries and normalised skill sets that fit encoder limits to avoid truncation and improve interpretability. Output: degree texts/features and job texts/features.
6. **Score candidate matches** — Run semantic baseline, skill-only, and hybrid models, optionally with metadata features, to compare methods. Output: ranked degree-job pairs.
7. **Build a gold benchmark** — Sample pairs across degrees, score bands, baselines, and negatives, then label with multiple annotators for unbiased validation. Output: dev/test benchmark with inter-annotator agreement statistics.
8. **Evaluate and analyse** — Report strict and relaxed Precision@k, NDCG, hit rate, calibration/agreement, ablations, and error analysis to demonstrate validity. Output: model comparison tables and qualitative findings.
9. **Add reporting abstractions** — Only after validation, aggregate to role families or clusters and check their quality for MOE-friendly summaries. Output: validated role-level dashboards/tables.

## Dataset

1. Job ads from `MyCareersFuture` between **25 Jan 2026 and 31
   Jan 2026**
2. NUS module information from `NUSMods` API

## Prerequisites

- **Job ads data:** The MyCareersFuture dataset is large. Download it from [Google Drive](https://drive.google.com/file/d/1lmGbsgpxBRtl1tZTsasUbEEYy-STIqcA/view) and place it in the `data/` folder before running any analysis.
- **NUS modules data:** The `modules.csv` file (fetched from the NUSMods API) is already included in `data/`.

## Local Setup

This project uses Python 3.12+ with a virtual environment.

1. **Ensure Python 3.12+ is installed**:

   ```bash
   python3 --version
   ```

   If needed, install from [python.org](https://www.python.org/downloads/) or via `pyenv`.

2. **Clone the repository** (if you haven't already):

   ```bash
   git clone https://github.com/<org>/DSA4264-Text-Group-3.git
   cd DSA4264-Text-Group-3
   ```

3. **Create a virtual environment**:

   ```bash
   python3 -m venv .venv
   ```

4. **Activate the virtual environment**:
   - macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```

5. **Upgrade pip** (recommended):

   ```bash
   pip install --upgrade pip
   ```

6. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

7. Run your first cell in `nus.ipynb`

## Chat App

This repository now includes a browser-based chat interface that wraps the Python retrieval workflow.

### Architecture

- **Python retrieval backend** in `retrieval/`
- **Offline artifact builder** in `scripts/build_chat_index.py`
- **HTTP retrieval API** in `scripts/run_retrieval_server.py`
- **Next.js chat UI** in `app/`, `components/`, and `lib/`

### What the chat app does

- In `Find jobs` mode, enter a NUS module code like `CS1010` or a degree label like `Computer Science` to retrieve relevant job listings.
- In `Find modules` mode, enter a job title or paste a job description to retrieve relevant NUS modules.

### Setup

1. Install the existing Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Install the web app dependencies:

   ```bash
   npm install
   ```

3. Build the retrieval artifacts:

   ```bash
   .venv/bin/python scripts/build_chat_index.py
   ```

4. Start the retrieval API:

   ```bash
   .venv/bin/python scripts/run_retrieval_server.py
   ```

5. In a second terminal, start the Next.js app:

   ```bash
   npm run dev
   ```

6. Open [http://localhost:3000](http://localhost:3000)

### Environment variables

Create `.env.local` from `.env.example` if you want to point the web app at a non-default retrieval server URL.

## Scripts

See [`scripts/README.md`](scripts/README.md) for full documentation on all available scripts.

> **Note:** Scripts are available to scrape NTU module information (`get_ntu_module_info.py` and `get_ntu_module_descriptions.py`), but NTU data will **not** be included in our analysis due to time constraints.

## Contributed By

- TODO

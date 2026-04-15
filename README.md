## Objective

This project aims to develop a credible, scalable, and validated framework for assessing how well university curricula align with labour market needs. Rather than determining whether universities are performing “well” or “poorly,” the goal is to provide MOE with a systematic way to evaluate curriculum-job alignment at scale.

## Data

1. Job ads from `MyCareersFuture` between **25 Jan 2026 and 31 Jan 2026** (Restricted)
2. NUS module information from `NUSMods` API (Public)

## Prerequisites

**Job ads data:** The MyCareersFuture dataset is large and access-controlled. **Reach out to the project owners for a download link,** then unpack it under `data/` so job files are available at `data/MyCareersFutureData/*.json` before you run any analysis.

`notebooks/main.ipynb` reads those JSON job ads and the CSV inputs in the table below. For the job archive and for any CSV you cannot produce locally (degree map, skills extraction, gold evaluation set, and similar), **contact the project owners for download links**.

| Path                                                 | Role                                                     |
| ---------------------------------------------------- | -------------------------------------------------------- |
| `data/modules.csv`                                   | NUS module catalogue (see `get_module_info.py` above).   |
| `data/degree_to_module_map.csv`                      | Maps each degree programme to its constituent modules.   |
| `data/nus_modules_skills_output.csv`                 | Per-module skill signals used for skill-based alignment. |
| `notebooks/evaluation/gold_degree_job_alignment.csv` | Gold degree–job pairs and labels for evaluation.         |

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

7. **Run the analysis:** With the data laid out as in **Prerequisites**, open [`notebooks/main.ipynb`](notebooks/main.ipynb) and run the notebook from the first cell downward.

## Technical Report

The MkDocs report source lives in [`docs/`](docs/), with the main landing page at [`docs/index.md`](docs/index.md).

If you are editing the technical report, start from:

- [`docs/index.md`](docs/index.md)
- [`docs/project-overview.md`](docs/project-overview.md)
- [`docs/data.md`](docs/data.md)
- [`docs/methodology.md`](docs/methodology.md)
- [`docs/results.md`](docs/results.md)
- [`docs/appendix.md`](docs/appendix.md)

### Viewing the report locally

1. Install the documentation dependencies:

   ```bash
   pip install -r requirements-docs.txt
   ```

2. Serve the site with live-reload:

   ```bash
   mkdocs serve
   ```

3. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

## Chat App

This repository also includes a browser-based chat interface that wraps the Python retrieval workflow.

https://www.loom.com/share/02a35e4ad0c84dbbbc89aa46be5199af

### Architecture

- **Python retrieval backend** in `retrieval/`
- **Offline artifact builder** in `scripts/build_chat_index.py`
- **HTTP retrieval API** in `scripts/run_retrieval_server.py`
- **Next.js chat UI** in `app/`, `components/`, and `lib/`

### What the chat app does

- In `Find jobs` mode, enter a NUS module code like `CS1010` or a degree label like `Computer Science` to retrieve relevant job listings.
- In `Find modules` mode, enter a job title or paste a job description to retrieve relevant NUS modules.
- The chat route can optionally call an LLM to turn the retrieved evidence into a grounded natural-language explanation while still showing the raw evidence cards underneath.

### Setup

1. Install the existing Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure Node.js is installed.** The UI is a Next.js app; use a current [Node.js](https://nodejs.org/) LTS (20.x or newer is a safe choice). Check your toolchain:

   ```bash
   node --version
   npm --version
   ```

   If those commands are missing, install Node from the link above or via `nvm`, Homebrew, or your OS package manager.

3. Install the web app dependencies:

   ```bash
   npm install
   ```

4. Build the retrieval artifacts (optional if you ran the entire `notebooks/main.ipynb`):

   ```bash
   .venv/bin/python scripts/build_chat_index.py
   ```

   **Note:** This script reads and writes `notebooks/cache/`, the same directory populated by [`notebooks/main.ipynb`](notebooks/main.ipynb). It skips work when matching parquet, embedding, and JSON files are already present (omit `--force` unless you want a full rebuild), so a prior full notebook run usually avoids recomputing the expensive steps. Once the notebook and this script have produced a complete cache for your setup, you do not need to run the indexer again until you change source data, models, or cache paths.

5. Start the retrieval API (Backend):

   ```bash
   .venv/bin/python scripts/run_retrieval_server.py
   ```

6. In a second terminal, start the Next.js app (Frontend):

   ```bash
   npm run dev
   ```

7. Open [http://localhost:3000](http://localhost:3000)

### Environment variables (Used for Chat only)

Create `.env.local` from `.env.example` if you want to point the web app at a non-default retrieval server URL or enable the grounded LLM summary layer.

```bash
cp .env.example .env.local
```

For retrieval only:

```env
RETRIEVAL_API_BASE_URL=http://127.0.0.1:8000
```

To enable OpenAI-backed responses in `/app/api/chat`, add:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.4-mini-2026-03-17
OPENAI_REASONING_EFFORT=low
```

How the LLM layer works:

- The retrieval backend still determines which jobs, modules, and degrees are shown.
- The LLM only sees the retrieved evidence and is instructed to write a concise grounded explanation.
- If `OPENAI_API_KEY` is missing or the API call fails, the app falls back to a deterministic retrieval-only summary instead of breaking the chat flow.

## Scripts

See [`scripts/README.md`](scripts/README.md) for full documentation on all available scripts.

> **Note:** Scripts are available to scrape NTU module information (`get_ntu_module_info.py` and `get_ntu_module_descriptions.py`), but NTU data will **not** be included in our analysis due to time constraints.

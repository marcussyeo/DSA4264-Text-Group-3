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

- TODO

## Dataset

1. Job ads from `MyCareersFuture` between **25 Jan 2026 and 31
   Jan 2026**
2. NUS module information from `NUSMods` API
3. NTU module information from `NTUMods` API

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

7. Run your first cell in `main.ipynb`

## Scripts

### `scripts/get_module_info.py`

Fetches NUSMods module information from the [NUSMods API v2](https://api.nusmods.com/v2/) and outputs a cleaned CSV file with one row per module.

**Usage:**

```bash
python scripts/get_module_info.py [--year YEAR] [--output OUTPUT]
```

**Arguments:**

| Argument   | Default            | Description                                                            |
| ---------- | ------------------ | ---------------------------------------------------------------------- |
| `--year`   | `2024-2025`        | Academic year to fetch modules for, in `YYYY-YYYY` format              |
| `--output` | `data/modules.csv` | Path to the output CSV file (directory is created if it doesn't exist) |

**Examples:**

```bash
# Fetch 2024-2025 modules to the default output path
python scripts/get_module_info.py

# Fetch a different academic year
python scripts/get_module_info.py --year 2023-2024

# Specify a custom output path
python scripts/get_module_info.py --year 2024-2025 --output data/modules_2024.csv
```

**Output columns:**

| Column                    | Description                                                  |
| ------------------------- | ------------------------------------------------------------ |
| `moduleCode`              | Module code (e.g. `CS1101S`)                                 |
| `title`                   | Module title                                                 |
| `acadYear`                | Academic year (e.g. `2024/2025`)                             |
| `faculty`                 | Faculty offering the module                                  |
| `department`              | Department offering the module                               |
| `moduleCredit`            | Number of modular credits (MCs)                              |
| `description`             | Module description                                           |
| `additionalInformation`   | Additional notes from the module page                        |
| `workload`                | Expected weekly hours as `lecture/tutorial/lab/project/prep` |
| `gradingBasisDescription` | Grading scheme (e.g. `Graded`, `CS/CU`)                      |
| `preclusion`              | Modules that cannot be taken alongside this one              |
| `prerequisite`            | Prerequisites required before taking this module             |
| `corequisite`             | Modules that must be taken concurrently                      |
| `semestersOffered`        | Comma-separated semesters the module is offered (e.g. `1,2`) |

### `scripts/get_ntu_module_info.py`

Fetches all NTU modules from the [NTUMods API](https://backend.ntumods.org/courses/) and outputs a CSV file with one row per module. Pages through the paginated API and writes each page to disk immediately, so no data is lost if the script is interrupted.

**Usage:**

```bash
python scripts/get_ntu_module_info.py [--output OUTPUT]
```

**Arguments:**

| Argument   | Default                          | Description                                                            |
| ---------- | -------------------------------- | ---------------------------------------------------------------------- |
| `--output` | `data/ntu_mods_<today>.csv`      | Path to the output CSV file (directory is created if it doesn't exist) |

**Examples:**

```bash
# Fetch all NTU modules to the default date-stamped output path
python scripts/get_ntu_module_info.py

# Specify a custom output path
python scripts/get_ntu_module_info.py --output data/ntu_mods.csv
```

**Output columns:**

| Column           | Description                              |
| ---------------- | ---------------------------------------- |
| `code`           | Module code (e.g. `AAD08A`)              |
| `name`           | Module name                              |
| `academic_units` | Number of academic units (AUs)           |

**Notes:**
- If interrupted, re-running the script resumes from where it left off — already-saved module codes are skipped.
- A 0.5 s delay is inserted between page requests to avoid rate limiting. If a `429` response is received the script automatically waits for the `Retry-After` period before retrying.

---

### `scripts/get_ntu_module_descriptions.py`

Reads the CSV produced by `get_ntu_module_info.py`, fetches the full course description for each module from the [NTUMods website](https://www.ntumods.org), and writes a new CSV that includes a `description` column. Uses multiple parallel workers to speed up the process.

**Usage:**

```bash
python scripts/get_ntu_module_descriptions.py [--input INPUT] [--output OUTPUT] [--workers N]
```

**Arguments:**

| Argument    | Default                               | Description                                                             |
| ----------- | ------------------------------------- | ----------------------------------------------------------------------- |
| `--input`   | `data/ntu_mods_2026-03-12.csv`        | Path to the input CSV produced by `get_ntu_module_info.py`              |
| `--output`  | `data/ntu_mods_with_description.csv`  | Path to the output CSV file (directory is created if it doesn't exist)  |
| `--workers` | `10`                                  | Number of parallel worker threads                                       |

**Examples:**

```bash
# Fetch descriptions with default settings (10 workers)
python scripts/get_ntu_module_descriptions.py --input data/ntu_mods_2026-03-12.csv

# Use more workers for faster scraping (watch for 429s)
python scripts/get_ntu_module_descriptions.py --input data/ntu_mods_2026-03-12.csv --workers 20

# Use fewer workers if rate-limited
python scripts/get_ntu_module_descriptions.py --input data/ntu_mods_2026-03-12.csv --workers 5
```

**Output columns:**

| Column           | Description                              |
| ---------------- | ---------------------------------------- |
| `code`           | Module code (e.g. `AAD08A`)              |
| `name`           | Module name                              |
| `academic_units` | Number of academic units (AUs)           |
| `description`    | Full course description                  |

**Notes:**
- Run `get_ntu_module_info.py` first to generate the required input file.
- Each worker thread uses its own HTTP session. A 0.5 s delay is applied per worker between requests.
- If interrupted, re-running skips already-fetched module codes and resumes from where it left off.
- If a `429` response is received, the affected worker waits for the `Retry-After` period. Reduce `--workers` or increase `REQUEST_DELAY` (top of the script) if rate limiting is persistent.

---

## Contributed By

- TODO

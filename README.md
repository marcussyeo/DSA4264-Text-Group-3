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

## Contributed By

- TODO

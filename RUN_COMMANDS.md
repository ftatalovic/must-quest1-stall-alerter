# Stall Alerter: Run Commands

Quick-start reference for running MUST Quest 1 (Option C) locally. The tool uses **Python 3.9+** and only the Python standard library; no `pip install` is required.

> Run the commands from the **repository root** (the folder containing `stall_alerter.py`). The sample board contains 30 **synthetic** candidates.

## 1. Get the project

```bash
git clone https://github.com/ftatalovic/must-quest1-stall-alerter.git
cd must-quest1-stall-alerter
```

If the project is already on your computer, open a terminal in its root folder instead.

## 2. Check Python

**macOS / Linux**

```bash
python3 --version
```

**Windows PowerShell**

```powershell
py -3 --version
```

The examples below use `python3`. On Windows, replace `python3` with `py -3` (or `python` if that is your configured Python 3 command).

Every `python3` and `git` command in this file was run on a fresh clone of `main` on macOS with Python 3.9.6. The Windows commands were not run.

## 3. Run the tool: terminal report

**Reproduce the original Quest 1 example (7-day threshold):**

```bash
python3 stall_alerter.py data/hiring_board.csv --as-of 2026-11-16 --days 7
```

Expected on the supplied sample board: **30 candidates; 5 follow-ups, 3 data issues, 2 scheduled, 14 not stalled and 6 closed**.

**Use today's date and the default 7-day threshold** (the counts then depend on the day you run it):

```bash
python3 stall_alerter.py data/hiring_board.csv
```

**Change the stall threshold to 10 days:**

```bash
python3 stall_alerter.py data/hiring_board.csv --as-of 2026-11-16 --days 10
```

**See all command-line arguments:**

```bash
python3 stall_alerter.py --help
```

## 4. Generate a CSV report for Excel

The optional CSV export was added **after** the original four-hour Quest submission, with MUST's approval.

```bash
python3 stall_alerter.py data/hiring_board.csv --as-of 2026-11-16 --days 7 --output followup_2026-11-16.csv
```

The equivalent short option is `--out`:

```bash
python3 stall_alerter.py data/hiring_board.csv --as-of 2026-11-16 --days 7 --out followup_2026-11-16_alt.csv
```

The CSV contains **all 30 candidates in 12 columns**, sorted into status groups, with follow-ups prioritized. The original terminal report still appears.

**Important:** The output filename must **not already exist**. The tool does not overwrite existing files, does not modify the input board, and does not create directories. Choose a different filename for each run or deliberately remove an old report yourself.

**Opening in Excel:** If everything appears in one column, use **Data > From Text/CSV**, set encoding to **UTF-8** and the delimiter to **Comma**. The CSV contains user-controlled text; the spreadsheet-formula guard is a precaution, not a universal guarantee. Do not enable unexpected content or links.

## 5. Run the tests

**Acceptance checks (AC1 to AC11):**

```bash
python3 acceptance_test.py
```

**All unit tests (original + CSV export):**

```bash
python3 -m unittest discover -s tests -v
```

**Original unit tests only:**

```bash
python3 -m unittest tests.test_stall_alerter -v
```

**CSV export tests only:**

```bash
python3 -m unittest tests.test_csv_export -v
```

At the documented release, the suite contains **25 original unit tests, 32 CSV export tests and 11 acceptance checks**. All tests use local synthetic data.

## 6. Common problems

| Symptom | What to check |
| --- | --- |
| `python3: command not found` | Install Python 3.9+ or use the platform-specific command (`py -3` on Windows). |
| `can't open file 'stall_alerter.py'` | Run from the repository root, or supply the full path to the script. |
| `cannot read ...` | Check that the input CSV path exists and has the required columns. |
| `... already exists` when exporting | Use a new `--output` filename. Existing files are intentionally protected. |
| Dates reported as invalid | Source dates must use exact `YYYY-MM-DD` format. |
| Entire CSV is in one Excel column | Import as UTF-8 with **Comma** delimiter instead of double-clicking. |

## 7. Submission baseline vs. current version

- **Original Quest 1:** Git tag [`quest1-submission-baseline`](https://github.com/ftatalovic/must-quest1-stall-alerter/tree/quest1-submission-baseline), without CSV export.
- **Current `main`:** Adds the optional recruiter-friendly CSV export, additional tests and documentation.

For implementation details, see [`README.md`](README.md), [`evidence.md`](evidence.md) and [`docs/CSV_EXPORT_ARCHITECTURE.md`](docs/CSV_EXPORT_ARCHITECTURE.md).

**Safety:** The tool only reads the hiring board and never modifies it. It creates a report file only when `--output` (or `--out`) is given. It never sends messages and never makes hiring decisions. Human review is required before taking action.

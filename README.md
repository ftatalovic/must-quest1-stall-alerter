# Stall alerter

A small local tool for a recruiting team. It reads a hiring-board CSV file and lists the candidates who have not moved to a new stage for a set number of days (7 by default), longest wait first, with a suggested next step for each.

**What it does and does not do:**

- **The hiring board file is never modified.** The tool only reads it.
- **A new report file is created only when you ask for it** with `--output` (or `--out`). Without that option the tool writes nothing at all. It never overwrites an existing file.
- **It never sends a message and never makes a hiring decision.** A person reads the list and decides what to do.

Built for MUST Quest 1 (Option C). All data in this repository is synthetic: every name is invented.

## What you need

- Python 3.9 or newer. Nothing to install: only Python's built-in modules are used. Tested on Python 3.9.6, 3.12.14 and 3.13.15 (macOS).
- The hiring board saved as a CSV file (UTF-8) with these columns:

| Column | Example | Notes |
|---|---|---|
| `candidate_id` | C017 | Must be filled in and unique |
| `candidate_name` | Quin Mockford | |
| `role` | Backend Engineer | |
| `stage` | Interview | Applied, Screening, Interview, Offer (active) or Hired, Rejected, Withdrawn (closed) |
| `last_moved_date` | 2026-10-26 | Date of the last stage change, written `YYYY-MM-DD` |
| `next_step_date` | 2026-11-18 | Optional. Date of a booked next step, `YYYY-MM-DD` |
| `recruiter` | Tomo | Who owns the candidate |

## How to run it

From this folder:

```
python3 stall_alerter.py data/hiring_board.csv --as-of 2026-11-16
```

- `--as-of` is the date to count from. Leave it out to use today's date. Use `2026-11-16` to reproduce the planted answers in the sample data.
- `--days` changes the threshold, for example `--days 10`. Default: 7.

The tool never asks for a login and needs no internet. It creates no file unless `--output` (or `--out`) is given, and then exactly one new file (see "CSV report for Excel" below).

## Reading the output

```
Stall alerter | as of 2026-11-16 | threshold 7 days | 30 rows read
FOLLOW UP FIRST (5) - suggestions only, a person decides and sends
 1. C017  Quin Mockford  Interview  21 days  owner: Tomo
    Suggested: Chase interviewer feedback or book the next round, then update the candidate.
 ...
NEEDS A DATA FIX (3) - not judged by the tool
 C009  Ines Madeup  Screening  missing date
 ...
SUMMARY  stalled 5 | not stalled 14 | scheduled 2 | closed 6 | data issues 3 | total 30
Nothing was sent or changed. Input file was only read.
```

- **Follow up first**: who has waited too long, in priority order, with the owner and a suggested next step.
- **Needs a data fix**: rows the tool could not judge, with the reason. It does not guess. A person should correct these rows on the board.
- **Summary**: every row is counted once, so you can see nothing was skipped.

## CSV report for Excel (added after submission)

This option was added **after** the Quest was submitted, as a usability improvement approved by MUST. It was **not** part of the original four-hour build. The state of the repository before it is kept under the Git tag `quest1-submission-baseline`. Design and limits: `docs/CSV_EXPORT_ARCHITECTURE.md`. Results: `evidence.md` sections 12 and 13.

```
python3 stall_alerter.py data/hiring_board.csv --as-of 2026-11-16 --days 7 --output followup.csv
```

- `--output` and `--out` mean the same thing.
- The report on screen is exactly the same as without the option. One extra line confirms the file: `CSV report written: followup.csv (30 rows)`.
- The file has **one row for every candidate on the board**, so the row count matches the board. Use an Excel filter on the Status column to get the short list.
- **The file must not exist yet.** The tool never overwrites a file and never writes over the board. If the name is taken, it stops with an error (exit code 2); choose a new name or delete the old file first. It does not create folders.
- If the report cannot be written, the tool stops with an error and prints no report on screen.

Columns, in this order:

| Column | Meaning |
|---|---|
| Priority | 1, 2, 3... for candidates to follow up, empty for everyone else |
| Candidate ID, Candidate name, Role | As on the board |
| Hiring stage | The stage, or the text as typed if the tool does not know it |
| Days waiting | Calendar days since the last stage change. Empty for closed candidates and rows with bad data |
| Status | See below |
| Recruiter | Who owns the candidate |
| Next step date | As typed on the board, not corrected |
| Action / explanation | The suggested next step, or why the row has this status. Same text as on screen |
| As of, Threshold (days) | The reference date and threshold used for this report |

Status values, in the order the rows appear:

| Status | Meaning |
|---|---|
| Follow up first | Stalled. Rows are in priority order |
| Needs a data fix | The tool could not judge the row. Correct it on the board |
| Scheduled | A next step is booked for the reference date or later |
| Not stalled | Moved recently |
| Closed | Hired, Rejected or Withdrawn |

Good to know:

- **Excel shows everything in one column?** With some regional settings, double-clicking a comma-separated file does that. Use Data > From Text/CSV and choose comma as the separator.
- Excel may show the dates in your local style. The file itself keeps the text as typed on the board.
- A value that starts with `=`, `+`, `-` or `@` (or their full-width forms) gets a leading apostrophe (`'`), so that a spreadsheet does not run it as a formula. A real name such as `-Smith` therefore shows as `'-Smith`. The same apostrophe is added after a semicolon that is followed by one of these characters (`x;=1` becomes `x;'=1`), because a spreadsheet that separates on semicolons starts a new cell there.
- **This guard is a precaution, not a guarantee.** It was checked by reading the file back in tests, not in Excel itself. Treat a report made from a board you do not trust with care, and do not enable content or links a spreadsheet warns you about. Limits: `evidence.md` section 13.
- The file is UTF-8 with a byte order mark, so Excel reads accented names correctly.
- Not tested: opening the file in Excel itself, and Windows. See `evidence.md` sections 12 and 13.

## The rules

- **Stalled** means: the stage is active (Applied, Screening, Interview, Offer), the candidate has waited **at least** the threshold (exactly 7 days counts), and no next step is booked for the reference date or later.
- **Days waiting** = reference date minus `last_moved_date`, in calendar days (weekends and holidays count).
- **Closed** candidates (Hired, Rejected, Withdrawn) are never flagged.
- **Scheduled** candidates (a `next_step_date` on or after the reference date) are not flagged: the next step is already booked. If a booked date has **passed** with no stage change, the candidate is flagged and the suggestion says so.
- **Priority order**: most days waiting first. If equal, later stage first (Offer, Interview, Screening, Applied), because a late-stage candidate is the most costly to lose. If still equal, by `candidate_id`.
- **Needs a data fix** (listed, not judged): blank `candidate_id`; unknown or blank stage; missing date; a date not written exactly `YYYY-MM-DD` (for example `05/11/2026`, which could mean 5 November or 11 May); a date in the future; an unreadable `next_step_date`.
- **The tool stops with an error** (exit code 2, no report) if the file cannot be read as a hiring board: file not found, a required column missing, the same column name twice, a row with more or fewer fields than the header, or the same `candidate_id` twice. It also stops if `--days` is below 1 or `--as-of` is not a `YYYY-MM-DD` date.

## How to check that it works

```
python3 acceptance_test.py                      # acceptance test AC1-AC11, prints PASS/FAIL per line
python3 -m unittest discover -s tests -v        # 25 original unit tests plus 32 export tests
```

`acceptance_test.py` runs the tool on the sample board with the reference date 2026-11-16 and compares the result with `data/ground_truth.csv`, the planted answers written before the tool existed. Last result: **11/11 PASS**, 25/25 original unit tests (see `evidence.md`). The 32 export tests were added after submission with the CSV report: 32/32 (see `evidence.md` sections 12 and 13).

## Sample data and planted answers

- `data/hiring_board.csv`: 30 invented candidates.
- `data/ground_truth.csv`: the expected answer for every row, written by hand before any tool code existed.

At 2026-11-16 with a 7-day threshold, the expected follow-up list is **C017, C028, C004, C011, C023**. The board also contains boundary cases (6 days, exactly 7 days, a next step booked for the reference date itself), closed candidates with old dates, and 3 rows with bad data (C009, C014, C026).

Do not open and re-save the sample CSV in a spreadsheet: it may rewrite the dates and break the checks.

## Measured time saving (one comparison)

On the same 30-row board with the reference date 2026-11-18:

- Spreadsheet-assisted review (a helper formula column for days since last move, sorted, then reviewed by hand): **15 min 13 s**.
- Tool plus human review of its output: **4 min 37.84 s**.
- Reduction: **69.57%** (target: at least 50%).

This was one timed comparison on a small synthetic file, against a workflow that **already used a spreadsheet formula**. A fully manual review without formulas was not measured. It does not show average daily savings. Details and limits are in `evidence.md`.

## Limits

- Only stage changes count as movement. Emails or calls that are not on the board are not seen.
- Calendar days only: no business days or public holidays.
- One threshold for all stages.
- Dates must be `YYYY-MM-DD`. Other formats are reported as data fixes, not converted.
- The tool trusts the board: if `last_moved_date` is out of date, so is the list.
- One badly formed row (wrong number of fields) stops the whole run, so that nothing is silently misread.
- Tested only on the synthetic sample and on small test files, not on a real team's export.

## Files

| File | What it is |
|---|---|
| `stall_alerter.py` | The tool |
| `acceptance_test.py` | Acceptance test AC1-AC11 |
| `tests/test_stall_alerter.py` | Unit tests |
| `tests/test_csv_export.py` | Tests for the CSV report (added after submission) |
| `data/` | Synthetic board and planted answers |
| `data/expected_followup_2026-11-16.csv` | Expected CSV report for the sample board (added after submission) |
| `docs/CSV_EXPORT_ARCHITECTURE.md` | Approved design of the CSV report (added after submission) |
| `intent.md` | Problem, choice of tool, acceptance test as numbers (written before building) |
| `implementation_plan.md` | Approved build plan |
| `evidence.md` | Results, corrections, time measurement, limits |
| `Final directive.md` | How the AI tools were instructed, and where their output was checked or corrected |
| `CLAUDE.md`, `AGENTS.md` | Standing instructions for AI coding assistants |

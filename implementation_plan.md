# implementation_plan.md - Stall Alerter (for the implementing model, Claude Opus)

Read `TASK.md`, `CLAUDE.md`, `AGENTS.md` and `intent.md` first. `intent.md` holds the rules and acceptance numbers; this file says how to build to them. If this plan and `intent.md` disagree, stop and ask the candidate.

Hard limits: Python 3.9 standard library only (the machine has Python 3.9.6, so no `match`, no `X | Y` type syntax). No network, no installs, no writes to the input file, no em dashes in any file. Do not change the acceptance targets or the planted answers. If the detector and the ground truth disagree, report it to the candidate; never edit the ground truth to make a test pass.

## 1. Files to create

```
stall_alerter.py            single module, about 150 lines
acceptance_test.py          prints AC numbers, exit 0 if all pass, 1 otherwise
data/hiring_board.csv       30 synthetic rows
data/ground_truth.csv       expected answer for all 30 rows, hand-written
tests/test_stall_alerter.py unittest edge cases
README.md                   setup, run, verify, limits
Final directive.md          later, from section 9 plus the real session record
evidence.md                 later, from real measured output only
```

## 2. Build order (each step is a stop point for human review)

| Step | Work | Budget |
|---|---|---|
| 0 | With the candidate's OK: `git init`, commit the brief and planning files | 2 min |
| 1 | Create `data/hiring_board.csv` and `data/ground_truth.csv` from section 3. Candidate checks ground truth by hand and with the spreadsheet formula in section 8. Commit BEFORE any detector code so history shows the answers came first | 20 min |
| 2 | Write `tests/test_stall_alerter.py` and `acceptance_test.py` from sections 6 and 7 (they fail at this point) | 15 min |
| 3 | Write `stall_alerter.py` (sections 4 and 5) until tests pass | 30 min |
| 4 | Run everything, candidate reads the code and the output | 15 min |
| 5 | Timing measurement (section 8) | 20 min |
| 6 | `README.md`, `evidence.md`, `Final directive.md` | 40 min |
| 7 | Two Loom videos, recorded by the candidate | 40 min |

Planning is assumed to take the first hour in total. If time runs short, cut in this order: `--out` report file, README polish. Never cut tests, the ground-truth check, evidence, or the videos.

## 3. Dataset design

Columns, in this order:

`candidate_id, candidate_name, role, stage, last_moved_date, next_step_date, recruiter`

- IDs `C001` to `C030`, in ID order in the file. Names are invented and obviously fictional. No emails, phones or other personal fields.
- 3 recruiters (invented first names), 3 or 4 roles.
- Dates are `YYYY-MM-DD`. `next_step_date` is blank unless stated.
- Fixed reference date: `as_of = 2026-11-16`.

Special rows (exact values are fixed here):

| ID | Stage | last_moved_date | next_step_date | Days | Expected category | Rank |
|---|---|---|---|---|---|---|
| C017 | Interview | 2026-10-26 | | 21 | stalled | 1 |
| C028 | Offer | 2026-11-02 | | 14 | stalled | 2 |
| C004 | Screening | 2026-11-02 | | 14 | stalled | 3 |
| C011 | Interview | 2026-11-07 | 2026-11-12 (passed) | 9 | stalled | 4 |
| C023 | Applied | 2026-11-09 | | 7 | stalled | 5 |
| C002 | Screening | 2026-11-10 | | 6 | not_stalled (boundary) | |
| C019 | Offer | 2026-11-10 | | 6 | not_stalled (boundary) | |
| C006 | Interview | 2026-11-03 | 2026-11-18 | 13 | scheduled | |
| C020 | Offer | 2026-11-06 | 2026-11-16 (= as_of) | 10 | scheduled | |
| C003 | Hired | 2026-10-17 | | 30 | closed | |
| C008 | Rejected | 2026-10-02 | | 45 | closed | |
| C013 | Rejected | 2026-10-27 | | 20 | closed | |
| C016 | Withdrawn | 2026-11-01 | | 15 | closed | |
| C022 | Hired | 2026-11-09 | | 7 | closed | |
| C030 | Rejected | 2026-09-17 | | 60 | closed | |
| C009 | Screening | (blank) | | | data_issue: missing date | |
| C014 | Interview | 05/11/2026 | | | data_issue: invalid date | |
| C026 | Applied | 2026-11-20 | | | data_issue: future date | |

The other 12 rows (C001, C005, C007, C010, C012, C015, C018, C021, C024, C025, C027, C029): active stages, `last_moved_date` between 2026-11-11 and 2026-11-16 (0 to 5 days), at least one at 0 days, spread across all four active stages. Expected category `not_stalled`.

Totals: 5 stalled, 14 not_stalled, 2 scheduled, 6 closed, 3 data_issue = 30.

The planted order (C017, C028, C004, C011, C023) is deliberately neither file order nor reverse file order, so a missing sort cannot pass by luck.

`data/ground_truth.csv` columns: `candidate_id, expected_category, expected_rank, note`. One row per candidate, all 30. Type it from the table above. It must not be produced by running the detector.

## 4. Detection rules (apply in this order, first match wins)

Normalise first: strip whitespace on all fields; compare stage case-insensitively.

1. Stage is Hired, Rejected or Withdrawn: `closed`. Dates are not inspected.
2. Stage is not one of Applied, Screening, Interview, Offer: `data_issue` ("unknown stage").
3. `last_moved_date` blank: `data_issue` ("missing date").
4. `last_moved_date` not strict `YYYY-MM-DD` (use `datetime.date.fromisoformat` after a length-10 check, since 3.9 accepts only that form): `data_issue` ("invalid date").
5. `last_moved_date` after `as_of`: `data_issue` ("future date").
6. `next_step_date` non-blank and not a valid date: `data_issue` ("invalid next step date").
7. `next_step_date` >= `as_of`: `scheduled`.
8. `days = (as_of - last_moved_date).days`; `days >= threshold`: `stalled`. Otherwise `not_stalled`.

Priority sort key for stalled rows: `(-days, stage_rank, candidate_id)` with stage_rank Offer 0, Interview 1, Screening 2, Applied 3.

Suggested next step (fixed lookup, plain wording, always phrased as a suggestion):

- Applied: review the application and decide whether to screen or decline
- Screening: book or complete the screening call and tell the candidate where they stand
- Interview: chase interviewer feedback or book the next round, then update the candidate
- Offer: call the candidate about the pending offer and confirm the decision date
- If `next_step_date` is before `as_of`: prepend "Booked step on <date> has passed with no board update: confirm what happened."

Structural failures stop the run with exit code 2 and a clear message on stderr: file not found, a required column missing, duplicate `candidate_id`, `--days` below 1, unparseable `--as-of`. A file with a header and no rows is valid: prints zero flags, exit 0.

## 5. Architecture

One module, pure functions, I/O only at the edges:

```
load_rows(path) -> list[dict]            csv.DictReader, encoding utf-8-sig, read-only
classify(row, as_of, threshold) -> (category, days, reason)
prioritize(stalled) -> list              the sort key above
render(results, as_of, threshold) -> str plain text, no timestamps
main(argv) -> int                        argparse, prints, returns exit code
```

CLI:

```
python3 stall_alerter.py data/hiring_board.csv --as-of 2026-11-16 --days 7
```

`--as-of` defaults to today, `--days` defaults to 7. Optional `--out report.csv` writes the stalled list to a NEW file and refuses to overwrite the input path (first thing to cut if short on time).

Output sketch:

```
Stall alerter | as of 2026-11-16 | threshold 7 days | 30 rows read
FOLLOW UP FIRST (5) - suggestions only, a person decides and sends
 1. C017  <name>  Interview  21 days  owner: <recruiter>
    Suggested: chase interviewer feedback or book the next round ...
 ...
NEEDS A DATA FIX (3) - not judged by the tool
 C009  <name>  Screening  missing date
 ...
SUMMARY  stalled 5 | not stalled 14 | scheduled 2 | closed 6 | data issues 3 | total 30
Nothing was sent or changed. Input file was only read.
```

No imports beyond `argparse, csv, datetime, sys` (plus `hashlib` and `unittest` in tests). No wall-clock text in the output except the header's `as_of`, so runs are byte-identical.

## 6. Unit tests (`tests/test_stall_alerter.py`)

Use small in-memory rows, not the 30 row file, so they test rules independently of the dataset.

| # | Scenario | Expected |
|---|---|---|
| T1 | Active, exactly 7 days, threshold 7 | stalled |
| T2 | Active, 6 days | not_stalled |
| T3 | Active, 0 days | not_stalled |
| T4 | Each closed stage with a 100 day old date | closed, never stalled |
| T5 | Closed stage with a blank date | closed, not data_issue |
| T6 | Blank date, active | data_issue, missing date |
| T7 | `05/11/2026`, `2026-13-01`, `yesterday` | data_issue, invalid date |
| T8 | Date one day after as_of | data_issue, future date |
| T9 | Unknown stage `On Hold`, blank stage | data_issue, unknown stage |
| T10 | Stage ` offer ` with spaces and lower case, 8 days | stalled |
| T11 | Old date, next step = as_of; next step = as_of + 1 | scheduled |
| T12 | Old date, next step = as_of - 1 | stalled, action text mentions the passed step |
| T13 | Invalid next step date | data_issue |
| T14 | Sort: 10 days Applied vs 9 days Offer | 10 days first (days beat stage) |
| T15 | Sort: same days, Offer vs Applied; same days and stage, C002 vs C010 | Offer first; C002 first |
| T16 | Threshold 1 and threshold 30 on the same row | flips as expected |
| T17 | Missing required column; duplicate ID; `--days 0` | exit code 2 |
| T18 | Header-only file | exit 0, zero flags |
| T19 | File saved with a UTF-8 BOM | loads normally |
| T20 | Leap day: moved 2028-02-22, as_of 2028-02-29 | 7 days, stalled |

## 7. Acceptance script (`acceptance_test.py`)

Runs the tool on `data/hiring_board.csv` with `--as-of 2026-11-16`, compares with `data/ground_truth.csv`, and prints one PASS or FAIL line per criterion AC1 to AC10 from `intent.md` with the actual numbers (for example `AC2 recall 5/5 PASS`). Specific checks:

- AC2, AC3: set comparison of stalled IDs; print true positives, false positives, false negatives by ID.
- AC4: ordered list equality.
- AC5, AC6: per-row category equality for all 30 rows; counts sum to 30.
- AC7: rerun with thresholds 6 and 10 against the lists hard-coded from `intent.md` (`--days 6`: C017, C028, C004, C011, C023, C019, C002; `--days 10`: C017, C028, C004).
- AC9: render twice, compare strings.
- AC10: SHA-256 of the input before and after; scan `stall_alerter.py` source for `socket`, `smtplib`, `urllib`, `http`, `requests`, `subprocess`; confirm the input is opened without write mode.

Exit 0 only if every line is PASS. AC11 is `python3 -m unittest discover -s tests -v`. AC12 is a human measurement (section 8).

## 8. Independent check and timing (done by the candidate, not by the AI)

**Independent check of the ground truth (before detector code exists):** open `hiring_board.csv` in a spreadsheet, add a helper column `=DATE(2026,11,16) - E2` and filter to active stages with a value of 7 or more and no future next step. Confirm the result equals the 5 planted IDs. Note what the spreadsheet does with C009, C014 and C026 (this is evidence of the gap the tool fills). Record the outcome in `evidence.md`.

**Timing protocol:**

1. Manual pass: stopwatch on. Using the plain CSV in a spreadsheet with no helper formulas (assumed to be how the team works today), write down who to follow up, in order, with a next step for each. Stopwatch off. Record time, and misses and false flags against the ground truth.
2. Tool-assisted pass: stopwatch on. Run the command, read every flagged row and every data-issue row to the point of being ready to act. Stopwatch off.
3. Tool runtime alone: `time python3 stall_alerter.py ...` five times, report the median.
4. Saving = (manual - assisted) / manual. Report the real numbers even if under 50%.

Known bias to disclose: the person timing the manual pass already knows the planted answers, so the manual time is probably shorter than a real first look. If a second person can do the manual pass cold, prefer that and say so. One pass on 30 rows is a demonstration, not a productivity study. A minutes-per-day figure needs an assumption (for example one check per recruiter per day) and must be labelled as an estimate.

## 9. Planning record for `Final directive.md`

Facts so far (add to this as work proceeds; never fill gaps from imagination):

- Roles: candidate owns scope, approval, validation and submission. Claude Fable 5.2 did planning only (this file and `intent.md`). Claude Opus is intended for implementation. No code or data existed when the acceptance numbers were fixed.
- Planning directive given by the candidate (summary): read the three brief files; Option C only; act as architect, plan only; define acceptance numbers before building; design 30 synthetic rows with 5 planted stalls; deterministic rules; check existing solutions; standard library unless justified; define tests, false-positive checks and timing; name risks and human-control points; produce `intent.md` and this plan; stop for approval.
- Decisions made in planning: stalled means days >= threshold (exactly 7 counts); movement means stage change; closed stages excluded before dates are looked at; bad rows reported, not guessed; `next_step_date` suppression rule added (flagged for candidate approval); tie-break is later stage then ID; fixed `as_of` 2026-11-16; planted order scrambled against file order; ground truth hand-typed and checked by spreadsheet before code; no AI inside the tool.
- Assumptions (not verified with a customer): the board can be exported as CSV with one row per candidate; a stage-change date is available; calendar days are acceptable; the stage names listed are the team's stages; ISO dates.
- Not done in planning: no web research (existing-solution notes come from prior knowledge); nothing was run or tested.
- To be filled from the real record later: each prompt given to the implementing model, each point where the candidate checked output, each correction made (what was wrong, how it was found, what changed). If no corrections happen, say that plainly.
- The candidate must supply personally: the habit dropped for this Quest and what was done instead.

## 10. Risks and limits

| Risk | Handling |
|---|---|
| Ground truth and detector both written with AI help from the same rules, so a shared misunderstanding would pass | Candidate checks the 5 planted rows by hand and by spreadsheet before code exists; git history shows the order |
| Toy dataset makes results look better than real life | State it; list untested real-world cases (mixed date formats, renamed columns, re-opened candidates) |
| Stale board data: tool trusts `last_moved_date` | Out of the tool's control; say so in README |
| Date handling in spreadsheets may rewrite `05/11/2026` or ISO dates on save | Do not re-save the committed CSV from a spreadsheet; SHA-256 check in AC10 |
| Timing bias (see section 8) | Disclose; prefer a second person |
| Time overrun | Cut list in section 2; videos and evidence are protected |
| Suggested actions read as instructions | Wording says "Suggested"; footer states nothing was sent |

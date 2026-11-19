# CSV export architecture (`--output` / `--out`)

Status: **approved specification, not implemented yet.**
Written: 2026-11-19. Planning by Claude Fable 5.2, decisions approved by the candidate.
Baseline analysed: commit `12572eb98b52eacc701f34dc08d10004bf5fc160` (head of local `main` and of `origin/main` on 2026-11-19, confirmed with `git ls-remote`).

This document is self-contained. An implementer does not need the planning conversation. Read `CLAUDE.md` and `AGENTS.md` first; if they conflict with this file, ask the candidate.

## 0. Context and rules for the implementer

- The repository holds MUST Quest 1, Option C: a Python CLI (`stall_alerter.py`) that reads a synthetic hiring-board CSV, lists stalled candidates in priority order with a suggested next step, and reports rows with bad data. It never sends anything and never decides anything.
- The Quest was submitted before this feature existed. MUST approved a **post-submission usability improvement**: an optional CSV report that non-technical recruiters can open in Excel.
- This feature must never be described as part of the original four-hour submission.

Hard limits:

- Python 3.9 standard library only (the machine has Python 3.9.6: no `match`, no `X | Y` type syntax). No installs, no network, no GUI, no database.
- No new business rules. Classification, prioritization and terminal output stay exactly as they are.
- Do not modify: `acceptance_test.py`, `tests/test_stall_alerter.py`, `data/hiring_board.csv`, `data/ground_truth.csv`, `intent.md`, `implementation_plan.md`.
- Do not change acceptance targets or historical measurements. If a result disagrees with an expected value in this document, stop and report it to the candidate. Never edit an expected value to make a test pass.
- No em dashes or en dashes in any file.
- `TASK.md` is local only and must never be committed or pushed. The GitHub repository is public.
- No history rewriting: no amend, rebase, reset or force push.
- Work in phases (section 9) and stop for human verification after each phase.

## 1. Approved decisions

| # | Decision |
|---|---|
| 1 | Export **all** candidates, one row per input row, sorted by the existing priority order and then by status group. |
| 2 | Exactly 12 columns: Priority, Candidate ID, Candidate name, Role, Hiring stage, Days waiting, Status, Recruiter, Next step date, Action / explanation, As of, Threshold (days). |
| 3 | UTF-8 with BOM, comma-separated. |
| 4 | Both `--output` and `--out` are explicit, supported spellings of the same option. |
| 5 | Classification logic and terminal output are preserved byte for byte. |
| 6 | Protection against CSV formula injection and against accidental overwrites. |
| 7 | The pre-feature state is preserved as a separate Git baseline tag. Its identity with the exact MatchHire snapshot is **not verified** and must not be claimed. |

## 2. Current architecture and integration points

`stall_alerter.py` (212 lines, one file) is a linear pipeline:

```
main(argv)
  argparse: csv_path, --as-of, --days
  load_rows(path)        read-only, raises InputError on structural problems
  classify(row, as_of, threshold) -> (category, days, reason)   per row
  render(results, as_of, threshold) -> str                       terminal report
  sys.stdout.write(...)
```

Facts the implementation relies on:

- `main()` builds `results`: a list with one dict per input row, in input order. Each dict has the 7 input fields plus `category`, `days`, `reason` (`stall_alerter.py:203-207`). The export needs nothing else.
- `category` is one of `stalled`, `not_stalled`, `scheduled`, `closed`, `data_issue`.
- `days` is an `int` for `stalled`, `not_stalled` and `scheduled`, and `None` for `closed` and `data_issue`.
- `reason` is the suggested step for `stalled` rows and a short explanation for all other rows.
- `prioritize(items)` sorts stalled rows: most days first, then later stage first, then `candidate_id`.
- `stage_label(text)` returns the canonical stage name, or the stripped raw text for an unknown stage.
- `clean(text)` strips the value and replaces every non-printable character (tab, CR, LF, escape codes) with `?`.
- Current imports: `argparse`, `csv`, `datetime`, `sys`. Current exit codes: 0 (report printed), 2 (input or argument problem, message on stderr).

Integration with the existing acceptance script (which must not be edited):

- `acceptance_test.py:237-244` (AC10) already anticipates a writer. If the tool source contains a write-mode `open()`, AC10 copies the board to a temporary folder, runs the tool with `--out <that same copy>` and requires exit code 2 and an unchanged SHA-256. The explicit `--out` spelling (decision 4) satisfies this without relying on argparse abbreviation.
- AC10's forbidden import list is: `socket, smtplib, urllib, http, requests, subprocess, email, ftplib, imaplib, poplib, ssl, webbrowser, xmlrpc, asyncio, telnetlib`. The new imports `io` and `os` are not on it.
- AC11 discovers every test in `tests/` and requires at least 20 tests with 0 failures. New tests in that folder are picked up automatically and raise the count above 25.
- `implementation_plan.md:120` planned an optional `--out report.csv` and listed it as the first item to cut. This feature delivers that item, with a wider scope (all rows, not only the stalled list).

Existing statements that become outdated once the feature exists (handled in section 10, by adding notes, not by rewriting history):

- Module docstring in `stall_alerter.py`: "writes nothing".
- `README.md`: "does not create any files"; "25 unit tests".
- `evidence.md` section 11.1 ("no file opened for writing") and 11.3 ("`--out x.csv`: unrecognized argument"). These describe the baseline and remain true for the baseline tag.

## 3. Command line

```
python3 stall_alerter.py data/hiring_board.csv --as-of 2026-11-16 --days 7 --output followup.csv
python3 stall_alerter.py data/hiring_board.csv --as-of 2026-11-16 --days 7 --out followup.csv
```

- Declare one option with two spellings: `parser.add_argument("--output", "--out", dest="output", default=None, metavar="FILE", help=...)`.
- Only these two spellings are supported and tested. Shorter abbreviations are not part of the contract.
- Without the option, no new code path runs and no file is created.
- With the option, the terminal report on stdout is **identical** to a run without it. A one-line confirmation goes to **stderr**: `CSV report written: <path> (<n> rows)`.
- Exit codes are unchanged: 0 on success, 2 on any refusal or failure (input problem, argument problem, or export problem). No new exit code is introduced.

## 4. CSV format

### 4.1 File properties

| Property | Value |
|---|---|
| Encoding | UTF-8 with BOM (`encoding="utf-8-sig"`), so Excel reads non-ASCII names correctly |
| Separator | Comma |
| Line ending | CRLF (the `csv.writer` default), file opened with `newline=""` |
| Quoting | `csv.QUOTE_MINIMAL` (the default) |
| Header | One header row, exactly the 12 names below, in this order |
| Rows | One per input row. Row count equals the board's row count. |
| Determinism | No wall-clock time, no random values. Equal inputs and arguments give equal bytes. |

### 4.2 Columns

| # | Column | Source | Notes |
|---|---|---|---|
| 1 | Priority | Rank 1..n from `prioritize()` | Integer for `stalled` rows, empty for all others |
| 2 | Candidate ID | `candidate_id` | Text. Empty if blank on the board. |
| 3 | Candidate name | `candidate_name` | Text |
| 4 | Role | `role` | Text |
| 5 | Hiring stage | `stage_label(stage)` | Canonical name for known stages; the text as typed for unknown stages; empty if blank |
| 6 | Days waiting | `days` | Integer, or empty when `days` is `None` (closed, data issue) |
| 7 | Status | From `category` (table 4.3) | Fixed labels |
| 8 | Recruiter | `recruiter` | Text |
| 9 | Next step date | `next_step_date` as typed on the board | Text, not parsed again and not reformatted. Empty if blank. An unreadable value is shown as typed, so the recruiter can see what to fix. |
| 10 | Action / explanation | `reason` | Verbatim. One source of truth with the terminal report. |
| 11 | As of | Resolved reference date | `YYYY-MM-DD`, same value on every row |
| 12 | Threshold (days) | `--days` value | Integer, same value on every row |

"Text" means the value passes through `excel_safe()` (section 5.1). Columns 1, 6 and 12 are integers produced by the tool. Column 7 is a fixed label. Column 11 is a tool-formatted date.

### 4.3 Status labels and row order

Rows are written group by group in this order. The labels reuse the wording of the terminal report.

| Order | `category` | Status label | Order inside the group |
|---|---|---|---|
| 1 | `stalled` | Follow up first | `prioritize()` order; Priority 1..n |
| 2 | `data_issue` | Needs a data fix | Input file order |
| 3 | `scheduled` | Scheduled | Input file order |
| 4 | `not_stalled` | Not stalled | Input file order |
| 5 | `closed` | Closed | Input file order |

No new ordering rule is introduced: groups 2 to 5 keep the order of the board.

Why all rows: a list with only stalled rows and data issues hides scheduled candidates. That is open finding 1 in `evidence.md` section 11.4 (a mistyped `next_step_date` removes a candidate from view). With all rows and a Status column, the row count matches the board, the Scheduled rows show their days waiting and their booked date, and a recruiter gets the short list with one Excel filter.

### 4.4 Expected export for the sample board

Command: `--as-of 2026-11-16 --days 7`. Logical content (shown here with LF line endings and without the BOM):

```
Priority,Candidate ID,Candidate name,Role,Hiring stage,Days waiting,Status,Recruiter,Next step date,Action / explanation,As of,Threshold (days)
1,C017,Quin Mockford,Backend Engineer,Interview,21,Follow up first,Tomo,,"Chase interviewer feedback or book the next round, then update the candidate.",2026-11-16,7
2,C028,Bea Synthwell,Product Designer,Offer,14,Follow up first,Rina,,Call the candidate about the pending offer and confirm the decision date.,2026-11-16,7
3,C004,Dov Mockley,Backend Engineer,Screening,14,Follow up first,Rina,,Book or complete the screening call and tell the candidate where they stand.,2026-11-16,7
4,C011,Kaia Fictive,Backend Engineer,Interview,9,Follow up first,Tomo,2026-11-12,"Booked step on 2026-11-12 has passed with no board update: confirm what happened. Then: chase interviewer feedback or book the next round, then update the candidate.",2026-11-16,7
5,C023,Wren Exemplar,Data Analyst,Applied,7,Follow up first,Tomo,,Review the application and decide whether to screen or decline.,2026-11-16,7
,C009,Ines Madeup,Customer Success Lead,Screening,,Needs a data fix,Vesna,,missing date,2026-11-16,7
,C014,Nico Samplewood,Data Analyst,Interview,,Needs a data fix,Tomo,,invalid date '05/11/2026' (expected YYYY-MM-DD),2026-11-16,7
,C026,Zara Fakeworth,Customer Success Lead,Applied,,Needs a data fix,Tomo,,future date 2026-11-20 (after 2026-11-16),2026-11-16,7
,C006,Fynn Placeholder,Data Analyst,Interview,13,Scheduled,Vesna,2026-11-18,next step booked for 2026-11-18,2026-11-16,7
,C020,Tova Pretendo,Product Designer,Offer,10,Scheduled,Tomo,2026-11-16,next step booked for 2026-11-16,2026-11-16,7
,C001,Ada Sample,Backend Engineer,Applied,2,Not stalled,Rina,,moved recently,2026-11-16,7
,C002,Ben Fixture,Data Analyst,Screening,6,Not stalled,Tomo,,moved recently,2026-11-16,7
,C005,Elin Dummyson,Customer Success Lead,Screening,4,Not stalled,Tomo,,moved recently,2026-11-16,7
,C007,Gia Synthia,Product Designer,Interview,5,Not stalled,Rina,,moved recently,2026-11-16,7
,C010,Jori Exampleton,Data Analyst,Offer,3,Not stalled,Rina,,moved recently,2026-11-16,7
,C012,Lev Stubbs,Product Designer,Applied,0,Not stalled,Vesna,,moved recently,2026-11-16,7
,C015,Oona Fakeley,Backend Engineer,Screening,1,Not stalled,Vesna,,moved recently,2026-11-16,7
,C018,Rhea Dummett,Customer Success Lead,Interview,0,Not stalled,Vesna,,moved recently,2026-11-16,7
,C019,Sami Fixtura,Data Analyst,Offer,6,Not stalled,Rina,,moved recently,2026-11-16,7
,C021,Ugo Sampleby,Customer Success Lead,Applied,5,Not stalled,Vesna,,moved recently,2026-11-16,7
,C024,Xeni Notaperson,Backend Engineer,Offer,1,Not stalled,Vesna,,moved recently,2026-11-16,7
,C025,Yuri Madeleaf,Product Designer,Screening,3,Not stalled,Rina,,moved recently,2026-11-16,7
,C027,Abel Stubfield,Data Analyst,Interview,4,Not stalled,Vesna,,moved recently,2026-11-16,7
,C029,Cyd Mockerell,Backend Engineer,Applied,2,Not stalled,Tomo,,moved recently,2026-11-16,7
,C003,Cora Testwell,Product Designer,Hired,,Closed,Vesna,,closed stage,2026-11-16,7
,C008,Hugo Notreal,Backend Engineer,Rejected,,Closed,Tomo,,closed stage,2026-11-16,7
,C013,Mila Testova,Customer Success Lead,Rejected,,Closed,Rina,,closed stage,2026-11-16,7
,C016,Pim Demoson,Product Designer,Withdrawn,,Closed,Rina,,closed stage,2026-11-16,7
,C022,Vida Testoni,Backend Engineer,Hired,,Closed,Rina,,closed stage,2026-11-16,7
,C030,Dax Placeholt,Customer Success Lead,Rejected,,Closed,Vesna,,closed stage,2026-11-16,7
```

30 data rows: 5 + 3 + 2 + 14 + 6, the same counts as the terminal SUMMARY line.

**Provenance of this table (be honest about it in `evidence.md`):** it was computed on 2026-11-19 by a throwaway inline script that called the unmodified `load_rows`, `classify`, `prioritize` and `stage_label` at the baseline commit and applied the format of sections 4.2 and 4.3. It was printed to the terminal only; no file was written. It is therefore not independent of the tool's classification. Its categories and priority order agree with `data/ground_truth.csv` as far as the baseline acceptance test proves (AC2 to AC6). The candidate should review the table by eye before it is committed as the golden file.

## 5. Security and failure handling

### 5.1 Formula injection: `excel_safe(text)`

Spreadsheet programs run a cell as a formula when it starts with `=`, `+`, `-` or `@`, and in some cases a tab or carriage return.

```
excel_safe(text):
    value = clean(text)            # strips; tab, CR, LF and other control characters become "?"
    if value starts with one of  = + - @ :
        value = "'" + value
    return value
```

- Because `clean()` strips the value first, leading spaces cannot be used to hide a trigger character, and tab and CR cannot reach the first position.
- Apply it to every text column: Candidate ID, Candidate name, Role, Hiring stage, Recruiter, Next step date, Action / explanation. Apply it uniformly, even where the value is normally produced by the tool, because `reason` can contain text from the file (for example `unknown stage '...'`, which starts with a letter today, and the guard keeps that safe if the wording ever changes).
- Quoting and escaping of commas, quotes and line breaks is left to `csv.writer`.
- Accepted cost: a genuine value such as `-Smith` appears in Excel as `'-Smith`.

### 5.2 Output path rules

Run these checks immediately after argument validation and **before** the input is read:

| # | Condition | Result |
|---|---|---|
| 1 | Output path is an empty string | Exit 2: `error: --output needs a file name` |
| 2 | Output path exists and `os.path.samefile(output, csv_path)` is true | Exit 2: `error: refusing to write the report over the input file: <path>`. Covers relative versus absolute paths, symlinks, hard links and case-insensitive file systems. |
| 3 | `os.path.lexists(output)` is true (any existing file, folder or symlink, including a broken symlink) | Exit 2: `error: <path> already exists; choose a new name or delete it first` |

There is no `--force` flag. The tool never creates folders.

### 5.3 Writing

1. Classify all rows. Build the complete CSV text in memory (`io.StringIO(newline="")` with `csv.writer`).
2. Create the file with `open(output, "x", encoding="utf-8-sig", newline="")`. Mode `"x"` fails if the path exists, so the no-overwrite guarantee does not depend on the earlier check (no race window).
3. Write the text in one call and close the file.
4. If creation fails (`FileExistsError`, missing parent folder, permission denied, path is a directory, any other `OSError`): exit 2 with one clean line on stderr, no traceback.
5. If writing or closing fails after the file was created: remove the file the tool just created (best effort), then exit 2 with one line on stderr. Never remove a file the tool did not create in this run.
6. Only after a successful write: print the terminal report to stdout, then the confirmation line to stderr, and return 0.

Consequences:

- A failed export prints **no** terminal report (consistent with the existing rule "exit 2, no report") and leaves no report file.
- Input errors (exit 2 from `load_rows`) happen before any file is created.
- The only way to leave a partial file is a hard kill or power loss during the single write call. This is a stated limitation.

### 5.4 Other guarantees

| Requirement | How it is met |
|---|---|
| Input never overwritten | Rule 2 in 5.2, plus mode `"x"` |
| Original CSV unchanged | The input is still opened read-only by `load_rows`; test X7 checks the SHA-256 |
| No network, no external API | No new capability; imports stay within the standard library and outside AC10's forbidden list |
| No automatic email or hiring decision | Unchanged; the export is a file on the local disk |
| Predictable exit codes | 0 or 2 only |

## 6. Implementation steps

All changes are in `stall_alerter.py`. Expected size: about 60 to 70 added lines. Do not touch `classify`, `prioritize`, `render`, `load_rows`, `parse_iso_date`, `suggested_step`, `stage_label` or `clean`.

1. Add `import io` and `import os`.
2. Add module constants:
   - `EXPORT_HEADER`: the 12 column names of section 4.2, in order.
   - `EXPORT_STATUS`: an ordered sequence of `(category, label)` pairs from section 4.3.
3. Add `excel_safe(text)` as specified in 5.1.
4. Add `export_table(results, as_of, threshold)`: returns a list of lists, header first. For each category in `EXPORT_STATUS` order, take the matching rows (through `prioritize()` for `stalled`, input order otherwise) and build the 12 cells per section 4.2.
5. Add `csv_text(table)`: returns the CSV as one string using `csv.writer(io.StringIO(newline=""))`.
6. Add `check_output_path(output, csv_path)`: returns an error message or `None`, per section 5.2.
7. Add `write_new_file(path, text)`: per section 5.3, steps 2 to 5. Raises `OSError` on failure after cleaning up.
8. In `main()`:
   - Add the argparse option (section 3).
   - After the existing `--days` check: if `args.output is not None`, run `check_output_path`; on a message, print `error: ...` to stderr and return 2.
   - After `results` is built: if `args.output is not None`, build the text and call `write_new_file`; on `OSError`, print `error: cannot write <path>: <e>` to stderr and return 2.
   - Then the existing `sys.stdout.write(render(...))`, unchanged.
   - Then, if an export was written, the confirmation line on stderr.
9. Update the module docstring: add the `--output` usage line, and change "writes nothing" to say that it writes nothing unless `--output` is given, and then only one new file. Keep the exit code line accurate.

Print paths in error and confirmation messages through `clean()` so a hostile file name cannot inject terminal control characters.

## 7. Tests (defined before implementation)

### 7.1 Files

| File | Content | Status |
|---|---|---|
| `tests/test_csv_export.py` | New tests X1 to X15 | New, committed before the feature code, must fail at that point |
| `data/expected_followup_2026-11-16.csv` | The table from section 4.4, saved as plain UTF-8 with LF line endings and no BOM | New, committed together with the tests |
| `tests/test_stall_alerter.py`, `acceptance_test.py` | Existing | **Not modified** |

The golden file is compared as parsed rows (`csv.reader`), not as raw bytes, so Git or editor line-ending handling cannot break the test. Byte-level properties (BOM, CRLF) are asserted separately on the tool's actual output (X2).

Follow the conventions of the existing test file: `unittest`, temporary folders with cleanup, fixed `AS_OF = 2026-11-16`, synthetic names only, an in-process `run_main(argv)` helper that captures stdout, stderr and the exit code. Use a subprocess only where a real process is needed.

### 7.2 New tests

| # | Test | Pass condition |
|---|---|---|
| X1 | Golden export: sample board, `--as-of 2026-11-16 --days 7` | Parsed rows of the output equal the parsed rows of the golden file; exit 0 |
| X2 | File format | Output bytes start with the UTF-8 BOM (`EF BB BF`); every line ends with CRLF; header is exactly the 12 names in order; 31 lines; every row has 12 fields; every input `candidate_id` appears exactly once |
| X3 | Ordering | Priority column for the first 5 rows is 1..5 with IDs C017, C028, C004, C011, C023; Priority is empty on all other rows; Status groups appear in the order of section 4.3 with counts 5, 3, 2, 14, 6; groups 2 to 5 are in input file order |
| X4 | Values | Days waiting for the 5 stalled rows: 21, 14, 14, 9, 7. C011: Next step date `2026-11-12` and the explanation contains `2026-11-12` and `passed`. C006 and C020: Status `Scheduled`, Next step date `2026-11-18` and `2026-11-16`, Days waiting 13 and 10. C009, C014, C026: Status `Needs a data fix`, Days waiting empty, explanations contain `missing date`, `invalid date`, `future date`. Every row: As of `2026-11-16`, Threshold `7`. |
| X5 | No option: behaviour preserved | SHA-256 of stdout equals the three baselines in 8.1 for `--days 7`, `6`, `10`; stderr empty; the working folder contains no new file after the run |
| X6 | With option: terminal unchanged, both spellings | For `--output` and for `--out`: exit 0; stdout is byte-identical to the run without the option; stderr contains the confirmation line; the two spellings produce byte-identical files |
| X7 | Input unchanged | SHA-256 of the input file is equal before and after a successful export, and before and after each failing export in X8 to X10 and X13 |
| X8 | Input/output collision rejected | Output given as (a) the same path, (b) the same file by a different spelling (relative versus absolute), (c) a symlink to the input (skip where symlinks are unavailable); checked with `--output` and with `--out`: exit 2, message on stderr, nothing on stdout, input SHA-256 unchanged |
| X9 | Existing file not overwritten | Output path is an existing file with known content: exit 2, the file's bytes unchanged, nothing on stdout. Same for an existing directory and for a broken symlink. |
| X10 | Malformed input with the option | For each structural error (duplicate column, row with more fields, row with fewer fields, duplicate `candidate_id`, missing required column, invalid UTF-8 byte, input file not found): exit 2 and the output path does not exist afterwards |
| X11 | Formula injection | Board rows whose name, role, recruiter, candidate ID, stage or next step date is `=HYPERLINK("http://x","y")`, `+1+1`, `-2+3`, `@SUM(A1)`, a tab followed by `=1`, and spaces followed by `=1`. After parsing the output with `csv.reader`: no cell in any row starts with `=`, `+`, `-`, `@`, tab or CR; affected cells start with `'` followed by the original text; integer columns are unaffected |
| X12 | Hostile content | A name with a comma, a double quote, a line break and a terminal escape code: the output parses back to the correct number of rows with 12 fields each; no raw control character other than CR LF row endings is in the file |
| X13 | Failure paths leave nothing behind | (a) parent folder does not exist: exit 2, folder not created; (b) read-only folder (skip when running as root or where permissions do not apply): exit 2; (c) simulated write failure after creation (mock so the write raises `OSError`): exit 2 and the output path does not exist. In all cases: one message on stderr, no traceback, nothing on stdout. |
| X14 | Reproducible, threshold respected | Two exports with identical arguments are byte-identical. `--days 6`: 7 priority rows in the order C017, C028, C004, C011, C023, C019, C002. `--days 10`: 3 priority rows C017, C028, C004. Threshold column shows 6 and 10. Row count stays 30. |
| X15 | Header-only board | Exit 0; the export contains the header row only |

Edge cases to cover inside X4 or X11 with small in-memory boards: a blank `candidate_id` (Candidate ID empty, Status `Needs a data fix`), an unknown stage `On Hold` (Hiring stage shows `On Hold`), an unreadable `next_step_date` such as `next week` (shown as typed, Status `Needs a data fix`).

### 7.3 Proof that the tests test something

Record in `evidence.md`:

- Before the feature code exists, `tests/test_csv_export.py` fails (expected: every test that uses the option fails with an argparse error; X5 already passes because it describes the baseline).
- After implementation, the observed pass counts on each Python version actually run.

## 8. Regression baselines

### 8.1 Observed on 2026-11-19 at commit `12572eb`, Python 3.9.6, macOS

Terminal output, `python3 -B stall_alerter.py data/hiring_board.csv --as-of 2026-11-16 --days N | shasum -a 256`:

| `--days` | SHA-256 of stdout |
|---|---|
| 7 | `58c1769d00892cd6db3ab7670b486b91399de8ed46f14f31b3a4f891ae00da50` |
| 6 | `102e4859d2956659e82ce945c1fd7fa73bf5be8a160dafd98a59dfe9a351c30f` |
| 10 | `bc35b6d6b88eac05d8a1c61265daf6e728fa143d36be40285ab905e4e38cfd6f` |

File hashes (`shasum -a 256`):

| File | SHA-256 |
|---|---|
| `data/hiring_board.csv` | `fe3eb702a7bf5cdaf3ead92b6273dc2e844b0c5aad895d1eac48f4be61cf8d6a` |
| `acceptance_test.py` | `c15e6c032b664031d0eee32b6fa8608d1c93b2a202622dd1803fbba73715002c` |
| `tests/test_stall_alerter.py` | `e72db4fc696f2274761ac45ac05dee77c468fd85ef80b7b1508191341cfd1ba3` |
| `stall_alerter.py` (before the change) | `0222f2d77cb710950b633c83bfbffeab37031d79abe775c435343126f1f8416c` |

Not re-run during planning: `python3 acceptance_test.py` and the unit tests. The figures 11/11 and 25/25 come from `evidence.md`; re-run both before starting and record the observed result.

### 8.2 Regression checks after implementation

| Check | Expected |
|---|---|
| The three stdout hashes above, without the option | Identical |
| `git diff --exit-code quest1-submission-baseline -- acceptance_test.py tests/test_stall_alerter.py data/hiring_board.csv data/ground_truth.csv intent.md implementation_plan.md` | No difference |
| `python3 -m unittest tests.test_stall_alerter` | 25 tests, 0 failures |
| `python3 acceptance_test.py` | `RESULT: 11/11 PASS`. Two detail lines change by design: AC10 now reports `write-mode open() at lines [...]; --out onto input refused: True` and lists `io` and `os` among the imports; AC11 reports 25 plus the number of new tests. |
| `python3 -m unittest discover -s tests -v` | All tests pass |

## 9. Git workflow

Preconditions: the repository has a repo-local identity (`user.email` = the candidate's address). Show the exact author name and email before every commit. Do not use `gh` write commands in this repository. Push only named refs. Every push needs the candidate's explicit approval.

1. **Baseline tag.** Create an annotated tag on the pre-feature commit:

   ```
   git tag -a quest1-submission-baseline 12572eb98b52eacc701f34dc08d10004bf5fc160 \
     -m "Baseline before the post-submission CSV export. Head of main and origin/main on 2026-11-19. Not independently verified against the snapshot MatchHire received."
   git push origin quest1-submission-baseline
   ```

   The tag marks the repository state before this feature. Do not write anywhere that it is the verified MatchHire snapshot.

2. **Branch.** `git switch -c post-submission/csv-export`

3. **Commits, in this order** (the order is the evidence that tests came first):

   | Commit | Content | Phase |
   |---|---|---|
   | 1 | `docs/CSV_EXPORT_ARCHITECTURE.md` (this file) | Phase 0 |
   | 2 | `tests/test_csv_export.py` and `data/expected_followup_2026-11-16.csv`; tests fail | Phase 1 |
   | 3 | `stall_alerter.py`; all tests pass | Phase 2 |
   | 4 | `README.md`, `evidence.md`, `Final directive.md` additions | Phase 3 |

   Stop after each phase and show the observed test results and the commit ID.

4. **Publish.** Fast-forward `main` (`git switch main && git merge --ff-only post-submission/csv-export`), then `git push origin main`. Optionally tag the result `v1.1-csv-export`.

5. **Never:** amend, rebase, reset, force push, `git add -f TASK.md`, or `git add -A` without reading the file list. The untracked files `demonstration_run.md` and `report_2026-11-18.txt` are not part of this feature; leave them as they are unless the candidate says otherwise. Do not write demo exports into the repository folder, or delete them before committing.

## 10. Documentation updates (phase 3, additions only)

Rules: add, do not rewrite. Sections that describe the original submission keep their wording and numbers.

**README.md**

- New section "CSV report for Excel (added after submission)": states that it was added after the Quest was submitted, with MUST's approval, and that it was not part of the original four-hour build; shows the command; lists the 12 columns; explains the Status values; notes that the file must not already exist; notes that with some regional settings Excel opens a comma-separated file in one column, and that "Data > From Text/CSV" imports it correctly.
- Correct the sentence "does not create any files" to: it creates no file unless `--output` (or `--out`) is given, and then exactly one new file.
- Test count: "25 original unit tests plus N export tests". Keep "11/11".
- Files table: add the new test file, the golden file and this document.
- One line pointing to the tag `quest1-submission-baseline` as the state before this feature.

**evidence.md**

- New section 12 "Post-submission improvement: CSV export" only. Contents: what was added and why; that sections 1 to 11 describe the baseline tag and were not edited; observed results for X1 to X15 and for section 8.2, with the Python versions actually run; the provenance note for the golden table (section 4.4); which parts AI drafted and what the candidate checked; limits (section 11 of this document); explicit statement that no time-saving measurement was made for the export.
- Do not edit sections 1 to 11. In particular, section 11.1 to 11.3 results stay as recorded; section 12 states that they apply to the baseline and that the runtime trace was not repeated for the export path unless it actually is repeated.

**Final directive.md**

- One appended paragraph "Step 6. Post-submission improvement": the instruction pattern used (architecture first, tests and golden file committed before code, phase gates, baseline tag, no history rewriting).

**Not modified:** `intent.md`, `implementation_plan.md`, `CLAUDE.md`, `AGENTS.md`.

## 11. Risks, trade-offs and exclusions

| Risk or trade-off | Handling |
|---|---|
| Excel with semicolon regional settings opens a comma-separated file in one column on double-click (related to `evidence.md` 11.5) | Comma is the approved format. Documented in the README with the import route. |
| Excel reformats `Next step date` and `As of` to the local date style, and may reinterpret an ambiguous typed value such as `05/11/2026` in the Next step date column | Display only; the file itself keeps the text as typed. The Action / explanation column states the problem in words. Documented as a limit. |
| The apostrophe guard changes how a genuine value starting with `=`, `+`, `-` or `@` looks | Accepted cost of the protection. Documented. |
| A hard kill during the write can leave a partial file | Stated limit. The window is one in-memory write call. |
| The golden table was computed with the tool's own classification | Stated in section 4.4; the candidate reviews it before commit. |
| The baseline tag may not equal the exact MatchHire snapshot | The tag message says so; no document may claim otherwise. |
| Evidence section 11 (negative testing) describes the baseline, not the new write path | Stated in the new section 12; not silently reused. |
| More code paths in a tool whose main promise was "read-only" | The option is off by default; without it no new code runs (X5). |

Explicitly excluded: `.xlsx` output, a `--force` or overwrite flag, a `--delimiter` option, filter flags (for example "stalled only"), new statuses or business rules, fixes for open findings 2 to 4 of `evidence.md` 11.4, changes to error-message cleaning for existing messages, email or any sending, GUI or web interface, database, scheduling, and any time-saving claim for the export.

## 12. Ready gate for this feature

Before saying the feature is done, verify and record:

1. X1 to X15 pass, observed, with the command and Python version.
2. Section 8.2 regression checks pass, observed.
3. The six protected files are unchanged against the baseline tag.
4. No file other than those named in section 9 was added or changed.
5. README and evidence additions match tested behaviour and separate the baseline from the improvement.
6. Known limits (section 11) are disclosed.
7. The candidate has reviewed the diff and the golden table.

# evidence.md - Stall alerter (MUST Quest 1, Option C)

Every number here comes from a command that was run or a measurement the candidate reported. Anything not measured is labelled as such.

Repository: https://github.com/ftatalovic/must-quest1-stall-alerter (commit `a5aeb8f` for the tool and tests).

## 1. Acceptance test (fixed before building)

The targets were written in `intent.md` and committed (`45accf6`) before the sample data (`9d669ba`), the tests (`4769ef5`) and the tool (`5366e9f`). None of the targets, and none of the planted answers, were changed after results were seen. Git history shows each of those files was changed by exactly one commit, the one that added it.

Sample data: 30 synthetic candidates, 5 planted stalled cases, reference date 2026-11-16, threshold 7 days.

## 2. Results against the planted answers

Command: `python3 acceptance_test.py`. Run on Python 3.9.6, 3.12.14 and 3.13.15, and on a fresh clone from GitHub. Same result each time:

| # | Measure | Target | Result |
|---|---|---|---|
| AC1 | Dataset | 30 rows, 5 planted, ground truth 30/30 | 30 rows, 5 planted, 30/30. PASS |
| AC2 | Stalled candidates found | 5/5 | **5/5 = 100%** (C017, C028, C004, C011, C023). PASS |
| AC3 | False flags | 0 of 25 | **0 of 25**. PASS |
| AC4 | Priority order | C017, C028, C004, C011, C023 | Exact match. PASS |
| AC5 | Bad-data rows | 3/3 reported, none in the follow-up list | 3/3 (C009 missing date, C014 invalid date, C026 future date). PASS |
| AC6 | No row lost | 5 + 3 + 6 + 2 + 14 = 30 | 30/30 rows in the expected category. PASS |
| AC7 | Threshold can be changed | 7 flags at 6 days, 3 at 10 days | 7 and 3, in the expected order. PASS |
| AC8 | Every flag explained | 5/5 show days and a suggested step | 5/5; C011 also says its booked step (2026-11-12) has passed. PASS |
| AC9 | Repeatable | Two runs identical | Byte-identical (1332 bytes). PASS |
| AC10 | Person stays in control | 0 messages, input unchanged, no network | Input SHA-256 unchanged; imports only argparse, csv, datetime, sys; no file writing in the code. PASS |
| AC11 | Unit tests | 100% pass | **25/25**. PASS |
| AC12 | Time saved | at least 50% | **69.57%** in one comparison against a spreadsheet-assisted review (section 4). PASS against the target, with the limits below |

**Result: 11/11 automated checks PASS.** False flags: **0**. Missed stalled candidates: **0**.

## 3. Checks on the tests themselves

A test suite that passes on the first try could be too weak. These checks were run to rule that out:

- **Before the tool existed**, both test files were run and failed as expected: unit tests 0/20, acceptance 1/11 (only AC1, the data check, passed).
- **Test machinery check**: the acceptance script's report reader was fed a sample report, a report with two candidates swapped, and an unknown format. It read the first correctly, caught the swap, and refused the unknown format instead of passing.
- **Planted-bug check** on commit `5366e9f`: 11 single bugs were put into a throwaway copy of the tool, one at a time. The tests caught 10. The one that survived (removing a date-length check) made no difference on Python 3.9. See section 6 for why that check later turned out not to be enough.
- **Regression tests R1-R5** (added after the code review): all 5 fail on the old code `5366e9f` and pass on `a5aeb8f`, on Python 3.9 and 3.13.
- **Same output after the fix**: the report for the 30 sample candidates is byte-identical before and after the review fixes, at `--days` 6, 7 and 10.

## 4. Time saved (AC12)

Reported by the candidate. Both runs used the same 30-row synthetic board with **2026-11-18** as the reference date.

| Workflow | What the person did | Time |
|---|---|---|
| Spreadsheet-assisted (baseline) | Copied the CSV, opened it in Excel, added a formula in column H for days since the last stage move (reference date 2026-11-18), sorted by column H, then reviewed stages, booked next steps and priorities by hand | **15 min 13 s** (913.00 s) |
| Tool plus human review | Ran the tool, then a person reviewed its output | **4 min 37.84 s** (277.84 s) |
| Difference | | **635.16 s** (10 min 35.16 s) |
| Reduction | 635.16 / 913.00 | **69.57%** (target 50%) |

Tool running time alone, measured separately: 0.03 s in each of 5 runs (`/usr/bin/time -p`, 0.01 s resolution).

What the tool showed for the timed date (`--as-of 2026-11-18`): 10 to follow up (C017, C028, C004, C020, C011, C023, C019, C002, C007, C021), 3 data fixes, 1 scheduled, 6 closed, 10 not stalled. The list is longer than at 2026-11-16 because two more days have passed: C020's booked step on 2026-11-16 is now in the past, and C019, C002, C007 and C021 have reached 7 days. This is tool output. No hand-written ground truth exists for 2026-11-18.

**How to read this number:**

- It is **one comparison, not a productivity study**.
- The baseline **already used a spreadsheet formula**. It is a comparison against a spreadsheet-assisted review, not against fully manual work. A fully manual review without formulas was **not measured**. (The candidate's estimate is that it would take over 20 minutes. This is an estimate, not a measurement.)
- The two workflows were not exactly the same steps.
- The person timed had reviewed the sample data and its planted answers beforehand, which may have made either run faster.
- Whether the spreadsheet review reached the same list as the tool was not recorded.
- It does **not** show an average daily saving. Any per-day figure would need assumptions about board size and how often the team checks, and would be an estimate.
- The planted-answer tests (AC1-AC11) use 2026-11-16. The timing used 2026-11-18. They are separate measurements.

## 5. What was reused and what was built

| Existing option | Used? |
|---|---|
| Spreadsheet formulas (date difference, sort, filter) | **Reused as the baseline** in the timing comparison. A spreadsheet can compute days, but it does not report unreadable dates, check the file structure, or apply the booked-step and closed-stage rules without more manual work. |
| Python standard library (`csv`, `datetime`, `argparse`, `unittest`) | **Reused** for everything. Nothing to install. |
| pandas or other packages | Not used. They add an install step and give no benefit for a file this size. |
| Stale-candidate alerts in commercial hiring systems | Not used. The team works from a CSV file, and the brief rules out new systems and logins. |
| An AI model inside the tool | Not used. The rules are exact, so an AI would add cost, an API key to protect, and answers that could vary between runs. AI was used to plan, write and review the code instead. |

**The gap that was built:** one repeatable command that applies fixed rules, reports bad rows instead of hiding them, orders the list with a written tie-break rule, adds a suggested next step, and is proven by tests against planted answers.

Limit: this review of existing options came from working knowledge. No web search was done.

## 6. Independent code review (candidate) and corrections

An independent code review of commit `5366e9f` was carried out by the candidate. **Result: PASS WITH ISSUES**, with three findings. Each was reproduced before fixing and corrected in commit `a5aeb8f`:

| # | Finding | Reproduced | Fix | Test |
|---|---|---|---|---|
| 1 | Dates were not strictly `YYYY-MM-DD` on newer Python. | On Python 3.12 and 3.13, `2026-W47-3` (an ISO week date) was read as 2026-11-18 and the row was flagged as stalled. An earlier AI statement that the tests covered newer Python versions was wrong for this case. | The tool now checks the exact `YYYY-MM-DD` shape before reading any date. | R1, including a simulated lenient date reader so the check is proven on every Python version |
| 2 | Malformed CSV structure was accepted silently. | A duplicate `stage` column silently replaced the first one (C001 showed "Offer" instead of "Interview"). An extra field was dropped. A short row was flagged with a blank owner. | Duplicate column names, rows with too many fields and rows with too few now stop the run with a clear error and the line number. | R2, R3, R4 |
| 3 | A blank `candidate_id` was not handled. | A single blank ID would appear in the follow-up list. Two blank IDs gave a misleading "duplicate candidate_id" error. | A blank ID is now listed under "needs a data fix" as "missing candidate_id", never in the follow-up list. | R5 |

After the fixes: 25/25 unit tests and 11/11 acceptance checks on Python 3.9.6, 3.12.14 and 3.13.15.

## 7. Where AI helped and where it was corrected

AI (Claude) drafted the plan, the sample data, the ground truth, the tests, the tool and these documents. The full list of instructions and corrections is in `Final directive.md`. In short:

- **Corrected by the independent review (candidate)**: the three validation gaps in section 6.
- **Corrected by the candidate**:
  - The AI committed with the computer's global Git identity without showing which email it was. The commits were published under a different GitHub account. The candidate noticed, and the commits were rewritten with the right identity.
  - The candidate decided that the official Quest brief should not be published, and it was removed from the history before the first push.
  - The candidate clarified that the timing baseline was spreadsheet-assisted, not fully manual. This document reflects that.
- **Caught by the AI itself**: the GitHub repository already had a commit, so it was merged instead of force-pushed. One test-result report showed the exit code of a helper command instead of the test, so it was re-run.

## 8. What still fails or is not proven

- **Ground truth: what was checked and what was not.**
  - **Done:** before any tool code existed, a separate script recalculated the category of all 30 candidates from the board's dates at 2026-11-16 and compared it with the hand-written ground truth. Result: **30/30 match**. The priority order and the lists for `--days 6` and `--days 10` also matched. The script shares no code with the tool, but it was written by the same AI that wrote the ground truth, from the same rules. So a shared misunderstanding of the rules would still pass.
  - **Not done:** a separate human check of the planted answers in Excel at 2026-11-16, as the plan suggested. (The Excel review in section 4 used 2026-11-18 and was a timing run. Its list was not compared with the tool's.)
- **Small synthetic data only.** No real team export was tried. Untested real-world cases include renamed columns, mixed date formats, re-opened candidates and very large files.
- **Rules the tool does not cover**: only stage changes count as movement; calendar days only; one threshold for all stages; dates must be `YYYY-MM-DD`.
- **Strict file checks.** One badly formed row stops the whole report. This was chosen so nothing is misread, but it means one bad row blocks the list until it is fixed.
- **Documentation gap.** `intent.md` (written before building) does not list the rules added after the review: blank IDs as a data fix, and the new structural errors. The README describes the current behaviour.
- **Old commit still reachable.** One old commit with the wrong account attribution (`df75d99`) is no longer in the branch history, but GitHub still serves it to anyone who has its exact ID. Removing it completely needs GitHub Support or recreating the repository.
- **Time saving** is one comparison against a spreadsheet-assisted baseline (section 4).
- **Four findings from negative testing** are open and not fixed: a booked next step can hide a candidate, error messages are not cleaned, IDs are case-sensitive, and very old dates are accepted. Semicolon-separated files are rejected. Details in section 11.

## 9. The habit I unlearned

Previously, I tended to move into implementation as soon as I understood the problem, leaving some verification decisions for later.

For this Quest, I changed that approach. I defined measurable acceptance criteria and expected results before writing any application code. Besides my own independent review, I also required the AI-generated implementation to be reviewed by Codex, a different AI agent, and corrected the issues that were identified.

The main change was treating AI output as something to verify, not something to trust automatically.

## 10. Next improvement

Extend the synthetic dataset with more boundary cases, and have several different people do independent, timed checks on it, to replace the single comparison in section 4. The Quest limits data to synthetic or public data, so real candidate data is not the next step.

## 11. Negative Testing and Safety Verification

Sections 2 and 3 show the tool does what it should. This section records a second review, done by AI (Claude) at the candidate's request and accepted by the candidate, that looked for things the tool should **not** do.

**Scope of these results.** They describe what was observed in the runs listed below, on one machine. They do not guarantee the absence of all possible unsafe behaviour. Inputs, Python versions, operating systems and error paths that were not run are not covered.

**Conditions:** commit `28bc947` (tool code unchanged since `a5aeb8f`), Python 3.9.6 on macOS, bytecode writing switched off (`python3 -B`, `PYTHONDONTWRITEBYTECODE=1`). No code, test, dataset or acceptance target was changed, and no file was created. Negative tests were **not** repeated on Python 3.12 or 3.13.

### 11.1 Source check

Command: an inline `python3 -B` script that parsed `stall_alerter.py` with the `ast` module and listed every import, every function call name and every `open()` call.

| Observed | Result |
|---|---|
| Imports | `argparse`, `csv`, `datetime`, `sys` only |
| `open()` calls | One: `open(path, encoding="utf-8-sig", newline="")`, with no mode given, so read-only text |
| Calls to `eval`, `exec`, `compile`, `__import__`, or any `os`, `subprocess`, `socket` function | None in the list of call names |

### 11.2 Runtime trace

**Method:** Python's audit hooks (`sys.addaudithook`, PEP 578). The interpreter reports events such as opening a file, opening a socket, starting a process or importing a module. A hook recorded these events only while the tool's `main()` was running. The script was run inline, not saved as a file. Its core:

```python
WATCH = ("open", "socket.", "subprocess.", "os.system", "os.exec", "os.posix_spawn",
         "os.remove", "os.rename", "os.mkdir", "os.rmdir", "os.chmod", "os.truncate",
         "shutil.", "urllib.", "http.", "smtplib.", "ftplib.", "exec", "compile",
         "import", "ctypes.", "webbrowser.", "os.fork", "os.spawn", "pty.spawn",
         "os.putenv", "os.unsetenv")
def hook(ev, args):
    if armed[0] and ev.startswith(WATCH):
        events.append((ev, args[:3]))
sys.addaudithook(hook)
import stall_alerter
armed[0] = True
rc = stall_alerter.main(["data/hiring_board.csv", "--as-of", "2026-11-16", "--days", "7"])
armed[0] = False
```

Around it, the shell took `shasum -a 256 data/hiring_board.csv` and a checksum of `ls -laR` for the project folder (excluding `.git`), before and after.

**Traced run:** one run, the 30-row sample board, `--as-of 2026-11-16 --days 7`. Exit code 0, nothing on stderr, summary line `stalled 5 | not stalled 14 | scheduled 2 | closed 6 | data issues 3 | total 30`.

| Question | Observed in this run |
|---|---|
| Network activity | **None.** No `socket.*`, `urllib.*`, `http.*`, `smtplib.*` or `ftplib.*` event. The modules `socket`, `ssl`, `http`, `urllib`, `smtplib` and `subprocess` were not loaded in the interpreter at all. |
| Programs started | **None.** No `subprocess.*`, `os.system`, `os.exec*`, `os.posix_spawn`, `os.fork` or `os.spawn*` event. |
| Files deleted, renamed, created or changed | **None.** No `os.remove`, `os.rename`, `os.mkdir`, `os.rmdir`, `os.chmod`, `os.truncate` or `shutil.*` event. |
| Files opened | The input, `data/hiring_board.csv`, in mode `r`. The only other opens were Python's own cached standard-library modules, also in mode `r`. No file was opened for writing. |
| Input file | SHA-256 identical before and after (`fe3eb702a7bf5cda...`). |
| Project folder | Listing checksum (names, sizes, modification times) identical before and after. |

One thing to explain: the standard-library module `shutil` was loaded during the run. `argparse` loads it to read the terminal width. The tool does not import it, and none of its file operations were called (no `shutil.*` event).

**Limits of the trace.** One run on one input. Error paths (exit code 2) were not traced. Audit hooks only see events the Python interpreter reports; activity inside compiled extension code that reports no event would not be seen. The watch list is a list of event-name prefixes chosen by the reviewer, not every possible event.

### 11.3 Malformed-input and terminal-output checks

Each test board was sent on standard input, so no test file was written:

```
printf '<header>\n<rows>\n' | python3 -B stall_alerter.py /dev/stdin --as-of 2026-11-16
```

| Test input | What must not happen | Observed |
|---|---|---|
| Dates `20261101`, `2026-W44-1`, `2026-11-1`, `2026-11-01T00`, `2026-02-30`, `1/11/2026`, and a date typed with full-width digits | A guessed date leading to a flag | All 7 listed under "needs a data fix" as invalid date; 0 flagged |
| ` HIRED ` with a 2020 date, `Rejected` with a blank date, `Withdrawn` with unreadable dates | A closed candidate flagged or reported as a data problem | All 3 counted as closed; 0 flagged |
| Stages `On Hold` and `Rejected - no show` with 2020 dates | An unknown stage silently skipped or flagged | Both listed as unknown stage |
| A candidate name containing a terminal escape code and a line break followed by the text `FOLLOW UP FIRST (0)` | The file forging or wiping part of the report on screen | Escape and line break each replaced by `?`; the candidate stayed on one line (checked with `cat -v`) |
| A row with 4 fields instead of 7 | A partly read row | Exit 2: `line 4: fewer fields than the 7 header columns` |
| A row of commas only | A candidate with no ID in the follow-up list | The run stopped on the short row above, so this was not observed separately here; unit test R5 covers it |
| A byte that is not valid UTF-8 | A partly read file | Exit 2 with a decoding error, no report |
| `--days 0`, `--days -3`, `--days 7.5`, `--days 1e3` | A run with a meaningless threshold | Exit 2 each time |
| `--as-of 2026-11-31`, `--as-of 2026-W47-1` | A guessed reference date | Exit 2 each time |
| `--out x.csv` | A hidden way to write a file | Exit 2, unrecognized argument; no `x.csv` was created |
| `--days 99999999999999999999` | A crash | Exit 0, 0 flagged |

A NUL byte was only sent together with the invalid UTF-8 byte, and the run stopped on the UTF-8 error first. NUL handling on its own was not observed.

After these checks, `python3 -B acceptance_test.py` gave **11/11 PASS** with **25/25** unit tests, and `git status` showed no change to any tracked file.

A text search of all tracked files for email addresses and for the words api key, token, password and secret found no credential and no email address.

### 11.4 Findings

Four weaknesses were found. **None is fixed**: the code was left unchanged on purpose after this review. None of them sends anything, changes any file or contacts the network.

| # | Finding | How it was seen | Practical impact | Limit of this finding |
|---|---|---|---|---|
| 1 | **A booked next step can hide a candidate.** A row whose `next_step_date` is on or after the reference date is counted as "scheduled" and only appears in the summary total. It is not listed by name. | A candidate last moved on 2020-01-01 with `next_step_date` `9999-12-31` did not appear anywhere except `scheduled 1`. | Medium. A typing mistake in the next-step date, or a booking far in the future, removes a stalled candidate from the recruiter's view with no warning. The person cannot review what the tool does not show. | This follows the rule written in `intent.md`; it is a gap in the design, not a coding error. How often such dates occur in a real board is unknown. |
| 2 | **Error messages are not cleaned.** The main report replaces control characters, but two error messages print text from the file as it is. | A duplicate `candidate_id` and a duplicate column name, each containing a terminal escape code, were printed raw to stderr. | Low. A deliberately crafted file could change colours or move the cursor in the terminal while showing an error. It cannot run commands. | Seen in two messages (duplicate ID, duplicate column). Other error messages were not checked one by one. |
| 3 | **Candidate IDs are compared exactly.** `C001` and `c001` are treated as two different candidates. | Both were listed in the follow-up list. | Low. The same person could be listed twice if the board has inconsistent ID typing. Nobody is hidden. | Whether IDs differing only in case should count as duplicates is a decision for the team. |
| 4 | **No sanity limit on old dates.** | `last_moved_date` `0001-01-01` was accepted and listed first with 739935 days. | Low. An obvious typing mistake is ranked as the most urgent follow-up instead of being reported as a data problem. It is visible, not hidden. | No cut-off was defined in the acceptance criteria, so any limit would be a new rule. |

### 11.5 Semicolon-separated files

A file using semicolons between fields was rejected: exit 2, with a message listing all 7 required columns as missing. Spreadsheet programs save CSV with semicolons under many regional settings, so a real export from the team may be refused until it is saved with commas. Nothing is misread, which is the safe outcome, but the message does not say that the separator is the cause. The tool does not detect or accept semicolons.

## 12. Post-submission improvement: CSV export

**This section describes work done after the Quest was submitted. It is not part of the original four-hour build.** Sections 1 to 11 describe the repository as it was before this feature (Git tag `quest1-submission-baseline`, commit `12572eb`) and were not edited for it. The tag marks the state before the feature. Whether it is identical to the snapshot MatchHire received was **not verified**.

### 12.1 What was added and why

An optional CSV report: `--output FILE` (or `--out FILE`). It writes one row for every candidate on the board, with a Status column, so that a non-technical recruiter can open the result in Excel and filter it. It also makes scheduled candidates visible, which the terminal report does not list (open finding 1 in section 11.4). Without the option the tool behaves exactly as before. No business rule was added or changed. Specification: `docs/CSV_EXPORT_ARCHITECTURE.md`.

Work was done on the branch `post-submission/csv-export`, one commit per phase, on 2026-11-19:

| Commit | Content |
|---|---|
| `5868da4` | Specification only |
| `ddb30cb` | Export tests X1 to X15 and the expected report (golden file), before any feature code |
| `af75afa` | The feature in `stall_alerter.py` (96 lines inserted, 3 removed, docstring and blank lines included; the specification estimated 60 to 70 added lines) |
| the commit that adds this section | README, evidence and directive additions |

When this section was written, the branch and the tag existed only on the candidate's machine. Nothing had been merged or pushed.

### 12.2 Baseline, observed before any change

Python 3.9.6, macOS, commit `12572eb` (equal to `origin/main`, checked with `git ls-remote`):

- The three terminal-output hashes and the four file hashes in the specification (section 8.1) were recomputed and matched.
- `python3 -B -m unittest tests.test_stall_alerter`: 25 tests, OK.
- `python3 -B acceptance_test.py`: `RESULT: 11/11 PASS`.

### 12.3 The tests failed first

At commit `ddb30cb` (tests and golden file, no feature code), Python 3.9.6:

- `python3 -B -m unittest tests.test_csv_export`: 22 test methods, **21 failed**. The only one that passed was X5, as predicted: it describes the tool without the option.
- The 25 original unit tests: 25/25.
- `acceptance_test.py`: 10/11. AC11 failed, as it must while tests in `tests/` are failing.

Why the refusal tests check the wording of the message: before the feature exists, `argparse` already answers an unknown `--output` with exit code 2 and text on stderr. A test that only checked "exit 2, nothing on screen" would have passed before the feature existed and proven nothing. The tests therefore also require one clean error line with the expected reason.

### 12.4 Results after implementation

Commands: `python3 -B -m unittest tests.test_stall_alerter`, `python3 -B -m unittest tests.test_csv_export`, `python3 -B acceptance_test.py`, and the terminal-output hashes for `--days 7`, `6` and `10`. Commit `af75afa`, macOS.

| Python | Original unit tests | Export tests | Skipped | Acceptance | Three terminal-output hashes |
|---|---|---|---|---|---|
| 3.9.6 | 25/25 | 22/22 | 0 | 11/11 | Identical to the baseline |
| 3.12.14 | 25/25 | 22/22 | 0 | 11/11 | Identical to the baseline |
| 3.13.15 | 25/25 | 22/22 | 0 | 11/11 | Identical to the baseline |

Two acceptance detail lines changed by design, as the specification predicted: AC10 now reads `imports ['argparse', 'csv', 'datetime', 'io', 'os', 'sys'] | write-mode open() at lines [241]; --out onto input refused: True`, and AC11 reads `47/47 unit tests pass | failures 0 errors 0 skipped 0`.

Protected files: `git diff --exit-code quest1-submission-baseline -- acceptance_test.py tests/test_stall_alerter.py data/hiring_board.csv data/ground_truth.csv intent.md implementation_plan.md` returned exit code 0 (no difference).

The 15 planned tests are implemented as 22 test methods:

| # | What it proves | Result |
|---|---|---|
| X1 | The export for the sample board equals the golden file, row by row | Pass |
| X2 | UTF-8 with BOM, CRLF line ends, the 12 column names in order, 31 lines, 12 fields per row, every candidate exactly once | Pass |
| X3 | Priority 1 to 5 for C017, C028, C004, C011, C023; groups in the agreed order with 5, 3, 2, 14 and 6 rows; other groups in board order | Pass |
| X4 | Days, statuses, next step dates and explanations for the planted rows; blank ID, unknown stage `On Hold` and next step `next week` shown as specified | Pass (2 methods) |
| X5 | Without the option: the three baseline terminal hashes, empty stderr, no file created | Pass |
| X6 | With `--output` and with `--out`: terminal report byte-identical, confirmation line on stderr, both files byte-identical | Pass |
| X7 | Input SHA-256 unchanged after a successful export and after every refused or failed one in X8 to X10 and X13 | Pass |
| X8 | Report onto the board refused: same path, relative versus absolute spelling, symlink to the board; both spellings of the option | Pass (2 methods) |
| X9 | An existing file is not overwritten (bytes unchanged); an existing folder, a broken symlink and an empty name are refused | Pass (4 methods) |
| X10 | Seven kinds of unreadable board with the option: exit 2 and no report file left | Pass |
| X11 | 36 rows with formula-like text in each of 6 text fields: no cell starts with `=`, `+`, `-`, `@`, tab or CR; each affected cell is the original text behind an apostrophe | Pass |
| X12 | A name with a comma, a double quote, a line break and a terminal escape code: 12 fields per row, no control character in the file | Pass |
| X13 | Missing parent folder (not created), read-only folder, and a simulated write failure after the file was created (the new file is removed again): exit 2, one clean line, no traceback | Pass (3 methods) |
| X14 | Two exports with equal arguments are byte-identical; `--days 6` gives 7 priority rows, `--days 10` gives 3, in the expected order; 30 rows each | Pass |
| X15 | A board with only a header: exit 0, report with the header row only | Pass |

Also run by hand as real commands (Python 3.9.6), with the report written to a temporary folder outside the repository:

- `--output`: exit 0, terminal-output hash equal to the baseline, file starts with `EF BB BF`, content equal to the golden file after converting CRLF to LF.
- `--out` to a second name: byte-identical file.
- The same name again: exit 2, `... already exists; choose a new name or delete it first`.
- `--out data/hiring_board.csv` and `--out DATA/HIRING_BOARD.CSV` (same file on this case-insensitive disk): exit 2, `refusing to write the report over the input file`. Board SHA-256 unchanged (`fe3eb702a7bf5cda...`).

### 12.5 Safety checks for the new write path

Sections 11.1 to 11.3 apply to the baseline. Their statements "no file opened for writing" and "`--out x.csv`: unrecognized argument" are true for the baseline tag and are no longer true for the tool with this feature.

The runtime trace of section 11.2 (same audit-hook method and watch list) **was repeated** for the export path, once, on Python 3.9.6, with the report written to a temporary folder outside the repository:

| Run | Observed |
|---|---|
| Successful export of the sample board | Exit 0. Two files opened outside Python's own library: `data/hiring_board.csv` in mode `r` and the report in mode `x`. No network, process, delete, rename, mkdir or chmod event. `socket`, `ssl`, `http`, `urllib`, `smtplib` and `subprocess` were not loaded. |
| Second run onto the report that now existed | Exit 2 with the "already exists" message. No watched event at all: no file was opened, not even the board. |

Board SHA-256 and the project folder listing checksum were identical before and after. Limits: one run per case, one input, one Python version; the other limits listed in section 11.2 apply. The malformed-input checks of section 11.3 were not repeated by hand for the export path; X10 to X13 cover it in the automated tests only.

### 12.6 Where the expected report came from

`data/expected_followup_2026-11-16.csv` is the table in the specification (section 4.4), copied verbatim, saved as plain UTF-8 with LF line ends. That table was computed during planning by a throwaway script that called the tool's own `load_rows`, `classify`, `prioritize` and `stage_label` at the baseline commit. **It is therefore not independent of the tool's classification.** X1 shows that the export code reproduces it; it does not independently prove that the classification is right. That proof is still the ground truth and AC2 to AC6.

One extra check was made by the AI before committing the golden file: its Status and Priority columns were compared with `data/ground_truth.csv`, and its name, role, recruiter and next step date with `data/hiring_board.csv`. 0 mismatches in 30 rows. The Days waiting and Action / explanation columns have no independent source.

### 12.7 AI contribution and human checks

- **Drafted by AI (Claude Fable 5.2, in Claude Code):** the specification, the 22 tests, the feature code, the README and directive additions, and this section. The decisions in the specification (section 1) were approved by the candidate.
- **Run and observed by the AI:** every result in sections 12.2 to 12.6.
- **Candidate review: pending when this section was written.** The candidate had not yet reviewed the diff, the golden table by eye, or the report opened in Excel. Until that is done, this feature is AI-verified only.

Points where the implementation differs from, or adds to, the specification:

1. The specification asks to stop for human verification after each phase. On the candidate's instruction, all phases were run in one session, with one commit per phase so that the order (tests before code) is still visible in the history.
2. Refusal tests check the message wording (reason in section 12.3).
3. In X11, the candidate ID that starts with spaces is `   =2` instead of `   =1`, because two IDs that are equal after trimming would be rejected as a duplicate.
4. The write step also catches `ValueError` (for example a file name containing a null character), so that it ends with exit 2 and one line instead of a traceback.
5. The acceptance check AC11 fails if any test is skipped. The specification allows skips where symlinks or folder permissions are unavailable. On this machine nothing was skipped. On such a system `acceptance_test.py` would report AC11 as failed although nothing is wrong with the tool. Not changed, because `acceptance_test.py` must not be edited.
6. The `--help` description still ends with "Read-only.", and the README still opens with "It only reads." Both describe the default behaviour and the board. They were left as they are, because the specification allows only additions there.

### 12.8 Limits and what was not tested

- **Not opened in Excel, Numbers or LibreOffice.** The file format was checked by reading the bytes and parsing it back, not by opening it in a spreadsheet program.
- macOS only, Python 3.9.6, 3.12.14 and 3.13.15. Windows and Linux were not tested.
- With semicolon regional settings, Excel opens a comma-separated file in one column on double-click (related to section 11.5). The README describes the import route.
- Excel may reformat the date columns for display and may reinterpret an ambiguous typed value such as `05/11/2026`. The file keeps the text as typed, and the Action / explanation column states the problem in words.
- The apostrophe guard changes how a real value that starts with `=`, `+`, `-` or `@` looks.
- A hard kill or power loss during the single write call can leave a partial file. Not tested.
- The read-only folder test relies on normal file permissions; other failure causes (full disk, network drive) are covered only by the simulated write failure.
- Open findings 2 to 4 of section 11.4 are unchanged.
- **No time-saving measurement was made for the export.** The figures in section 4 are about the terminal report only.

## 13. Independent review of the CSV export and corrections

**Post-submission work, like section 12.** Section 12 is left as it was recorded before the review; where this section says something different, this section is the newer one (test counts, point 6 of section 12.7).

### 13.1 The review

- Verdict: **approve with changes**. The candidate passed the findings to the implementing AI session as a list of five priorities. The reviewer was described as "Fable's independent audit", done in a separate session.
- The implementing session saw the candidate's summary of the findings, **not the audit report itself**, and not the mitigation the audit proposed.
- All commits below are on the branch `post-submission/csv-export`. Nothing was merged or pushed, and no commit was rewritten.

| Commit | Content |
|---|---|
| `4d64270` | Regression tests S1 to S10, before the corrections |
| `819d797` | Corrections in `stall_alerter.py`, and the read-only wording in `README.md` |
| the commit that adds this section | This section, README notes, an amendment section in the architecture document, a note in `Final directive.md` |

### 13.2 Findings and corrections

| # | Finding | Confirmed? | Correction |
|---|---|---|---|
| 1 | **Formula injection with semicolon separators.** A value such as `x;=1+1;` was written unchanged. Spreadsheet software set to semicolon separators would split it and get a cell that starts with `=1+1`. | **Yes**, reproduced by test S1 on the unchanged code. The first failing cell was `=1+1,Person 009,Test Role,...`. | An apostrophe is now put after every semicolon that is followed by a formula character: `x;'=1+1;`. See 13.3. |
| 2 | **Full-width formula characters** (`＝ ＋ － ＠`) were not guarded. Found while checking the fix against the OWASP list, not part of the candidate's summary. | **Yes**, test S4 failed. Whether Excel really runs them was not verified; OWASP lists them as a risk in some locales. | Treated like `=`, `+`, `-`, `@`, at the start of a cell and after a semicolon. |
| 3 | **Contradictory "read-only" statements** in `--help` and at the top of `README.md`, while the tool can now create a report file. | **Yes**, test S10 failed. | Both now say three separate things: the input board is never modified; a new report is created only when asked for; nothing is sent and no hiring decision is made. The last line of the terminal report was not touched (the terminal output must stay byte-identical) and is still true: nothing was sent or changed, and the input was only read. |
| 4 | **Ctrl-C during the write leaves a file behind.** Only `OSError` triggered the cleanup. | **Yes**, test S8 failed: the file stayed. | Cleanup now runs for any exception, including `KeyboardInterrupt`, and the exception is always re-raised. See 13.4. |
| 5 | **AI attribution**: all commit trailers of the export say Claude Fable 5.2, while the implementation was expected to be by Opus. | **The trailers are consistent with what can be checked; no error was found.** See 13.6. | Clarification added here and in `Final directive.md`. No commit was changed. |
| 6 | **Missing test coverage**: hostile Action / explanation values, `stage_label()` variations, failed `close()`, hard links to the input, delimiter and quoting cases. | Coverage gaps, not defects: the tests for these (S2, S3, S6, S7, S9) passed on the unchanged code. | Tests added. |

### 13.3 The formula guard: what was decided and why

References, read on 2026-11-19: the OWASP "CSV Injection" page and OWASP ASVS 5.0 requirement 1.2.10 (level 3).

- OWASP lists as dangerous first characters: `=`, `+`, `-`, `@`, tab, carriage return, line feed, and the full-width forms `＝ ＋ － ＠`. It also warns that checking only the start of a value is not enough, because **separators and quotes can start a new cell in the middle of a value**. That is this finding.
- ASVS 1.2.10 asks for RFC 4180 escaping and for a single quote before `=`, `+`, `-`, `@`, tab and the null character at the start of a field.

How the tool now meets this:

| Risk | Handling | Checked by |
|---|---|---|
| `= + - @` at the start of a cell | Apostrophe in front (unchanged) | X11, S3, S5 |
| Full-width `＝ ＋ － ＠` at the start | Apostrophe in front (new) | S4, S5 |
| Tab, CR, LF and any other control or invisible character (for example a zero-width space) | Never reach a cell: replaced by `?` before the guard (unchanged) | X12, S4, S5 |
| Null character | Python 3.12 and 3.13: replaced by `?` (run by hand, the cell became `?=1+1`). Python 3.9: the board is rejected with `error: cannot read`, no report | Run by hand, not an automated test |
| Leading spaces of any kind hiding a formula character | Stripped first, then guarded (unchanged) | X11, S4 |
| Comma, double quote inside a value | Quoted and doubled by Python's `csv` module, RFC 4180 style (unchanged) | X12, S2 |
| A semicolon followed by a formula character, also with spaces or a double quote in between | Apostrophe right after the semicolon (new) | S1, S5 |
| The same, in a value typed into the stage or a date column and repeated in Action / explanation | Same guard; Action / explanation and Hiring stage go through it like every other text cell | S1, S5 |

S1 puts 12 hostile values into each of the 7 columns a user can type into (84 rows) and reads the report back three ways: as a comma-separated file, split on every semicolon, and parsed as a semicolon-separated CSV. No cell may start with a formula character in any of the three, even after leading spaces and double quotes are removed.

Alternatives that were considered and not used:

- **Putting every field in double quotes.** This is the first step of OWASP's general recipe, but it does not close this hole. Read with semicolons, the quote that opens the field is not at the start of the semicolon-cell, so the text after the `;` is still a new cell. This is reasoning about how such a reader works; it was not tried in Excel.
- **A first line `sep=,`.** Excel-specific, changes the approved format (the header would no longer be the first line) and can interfere with how Excel detects UTF-8.
- **Replacing semicolons** with another character. Changes what the recruiter typed in every value with a semicolon, not only in hostile ones.
- **A tab in front of the value** (OWASP's option for Excel). It leaves a control character in the data, against this tool's rule that every cell is one printable line.

The chosen guard changes only values where a semicolon is followed by a formula character. `Smith; Jones`, `a;b` and `x;y=1` are written exactly as typed (S2).

### 13.4 Cleanup on interruption: was catching everything safe?

The correction catches `BaseException` in the one function that writes the file. Checked before adopting it:

- The exception is **always re-raised**. Ctrl-C still stops the program, with Python's usual traceback. It is not turned into exit code 2 and not hidden (S8 requires the interrupt to arrive at the caller).
- The file is removed only after the tool itself created it in this run (`open` in mode `x` succeeded). An existing file can never be removed by this path.
- If the interrupt arrives after the text was fully written but before the function returns, the complete file is removed as well. That is consistent: interrupted means no report.
- Not covered: an interrupt in the instant between creating the file and starting the write, a second Ctrl-C during the cleanup itself, and a hard kill or power loss. In these cases an empty or partial file can remain. S7 and S8 simulate the failures; no real Ctrl-C was sent to a running process.

### 13.5 Test results

**Before the corrections** (commit `4d64270`, export code unchanged from `af75afa`, Python 3.9.6): 10 new tests, **5 failed**.

| Test | What it checks | Before | After |
|---|---|---|---|
| S1 | No formula cell when the file is read with semicolons; 84 hostile rows | **Fail** | Pass |
| S2 | Harmless semicolons and quotes are kept as typed | Pass | Pass |
| S3 | A cell ending in `;` next to a guarded cell | Pass | Pass |
| S4 | Full-width characters; spaces and invisible characters in front | **Fail** | Pass |
| S5 | Hostile Action / explanation values: line break, escape code, formula text | **Fail** | Pass |
| S6 | `stage_label()` with upper and lower case, spaces, non-breaking spaces, unknown and blank stages | Pass | Pass |
| S7 | `close()` fails: exit 2, new file removed | Pass | Pass |
| S8 | Ctrl-C during the write: interrupt passed on, new file removed | **Fail** | Pass |
| S9 | Report onto a hard link of the board: refused, board unchanged | Pass | Pass |
| S10 | `--help` does not say "Read-only" and states the three points | **Fail** | Pass |

**After the corrections** (commit `819d797`, macOS):

| Python | Original unit tests | Export tests (X and S) | Skipped | Acceptance | Three terminal-output hashes |
|---|---|---|---|---|---|
| 3.9.6 | 25/25 | 32/32 | 0 | 11/11 | Identical to the baseline |
| 3.12.14 | 25/25 | 32/32 | 0 | 11/11 | Identical to the baseline |
| 3.13.15 | 25/25 | 32/32 | 0 | 11/11 | Identical to the baseline |

- AC10 now lists the imports `argparse, csv, datetime, io, os, re, sys` and reports `write-mode open() at lines [250]; --out onto input refused: True`. AC11 reports `57/57 unit tests pass | failures 0 errors 0 skipped 0`.
- The six protected files show no difference against `quest1-submission-baseline` (`git diff --exit-code`, exit 0).
- `data/hiring_board.csv` SHA-256 before and after all runs: `fe3eb702a7bf5cdaf3ead92b6273dc2e844b0c5aad895d1eac48f4be61cf8d6a`.
- The report for the sample board is **byte-identical** to the one made before the corrections (`cmp`), and still equals the golden file (X1). The corrections change nothing for a board without semicolons or full-width characters.
- Run by hand with a hostile row (`x;=1+1;` as name, `=2+2` as role, `On;-Hold` as stage), the report line was: `,C001,x;'=1+1;,'=2+2,On;'-Hold,,Needs a data fix,Tester,,unknown stage 'On;'-Hold',2026-11-16,7`.

### 13.6 AI attribution: what can be verified

Checked with `git log` (the `Co-Authored-By` trailer of every commit):

| Commits | When | Trailer |
|---|---|---|
| `7c2a87a` | 2026-11-18 18:14 | None (created by GitHub) |
| `45accf6` to `28bc947` (7 commits: instructions, data, tests, tool, review fixes, first documents) | 2026-11-18 18:19 to 19:54 | Claude Opus 5.5 |
| `541132d` to `12572eb` (4 commits: evidence section 11 and three wording changes) | 2026-11-18 20:19 to 21:53 | Claude Fable 5.2 |
| All commits of the CSV report, `5868da4` onwards | 2026-11-19 | Claude Fable 5.2 |

- The trailer text is supplied by the Claude Code session that makes the commit. The session that implemented the CSV report and these corrections reports its model as Claude Fable 5.2 (model ID `claude-fable-5-2`), which matches its trailers and what section 12.7 and `Final directive.md` Step 6 say.
- **This is the tool's own report about itself. It cannot be proven from the repository**, and nothing outside the session was available to confirm it.
- Nothing in the repository says that Opus implemented the CSV report. "Fable plans, Opus implements" is how `implementation_plan.md` and section 1 of `Final directive.md` describe the **original Quest**, and the trailers of the original build agree with that. That table was not updated when the model changed on the evening of 2026-11-18: evidence section 11 (commit `541132d`) carries a Fable trailer.
- Conclusion: the existing attribution of the CSV report is **consistent with everything that could be checked, and otherwise unverified**. No historical commit was changed.
- Consequence for the review: if the audit session was also Claude Fable 5.2, the review was independent as a session (it did not write the code) but **not independent as a model**. The candidate's own review is still the only human check.

### 13.7 Remaining risks and limits

- **Manual verification in Excel by the candidate: PENDING.** No report produced by this tool has been opened in Excel, Numbers or LibreOffice by anyone. The candidate has not yet reviewed or approved this feature or these corrections.
- **No claim of general Excel safety.** The guard is checked by reading the file back in Python, under assumptions about how spreadsheet programs split and trim cells. Real programs, versions and regional settings may behave differently.
- OWASP states that the apostrophe approach is not reliable in Excel after a file is saved and reopened. Not tested here.
- Only comma and semicolon separators are considered. A person who imports the file with another separator chosen by hand (for example space, colon or pipe) is not protected by the semicolon rule.
- Whether Excel runs full-width characters as formulas was not verified; they are guarded as a precaution.
- Text that only looks dangerous once a person edits the cell (for example removing the apostrophe) is outside what a file can prevent.
- The apostrophe is visible and changes how a real value such as `-Smith` or `a;-b` looks.
- Interruption: see the "not covered" cases in 13.4.
- The null-character case differs by Python version (13.3) and has no automated test.
- macOS only, Python 3.9.6, 3.12.14 and 3.13.15. On a system where symlinks, hard links or folder permissions are unavailable, the tests that need them are skipped, and AC11 then reports a failure (section 12.7, point 5).
- The runtime trace of section 12.5 was not repeated after the corrections.
- Still no time-saving measurement for the export.

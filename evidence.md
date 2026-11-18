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

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

## 6. Independent code review and corrections

An independent code review of commit `5366e9f` was reported by the candidate. **Result: PASS WITH ISSUES**, with three findings. Each was reproduced before fixing and corrected in commit `a5aeb8f`:

| # | Finding | Reproduced | Fix | Test |
|---|---|---|---|---|
| 1 | Dates were not strictly `YYYY-MM-DD` on newer Python. | On Python 3.12 and 3.13, `2026-W47-3` (an ISO week date) was read as 2026-11-18 and the row was flagged as stalled. An earlier AI statement that the tests covered newer Python versions was wrong for this case. | The tool now checks the exact `YYYY-MM-DD` shape before reading any date. | R1, including a simulated lenient date reader so the check is proven on every Python version |
| 2 | Malformed CSV structure was accepted silently. | A duplicate `stage` column silently replaced the first one (C001 showed "Offer" instead of "Interview"). An extra field was dropped. A short row was flagged with a blank owner. | Duplicate column names, rows with too many fields and rows with too few now stop the run with a clear error and the line number. | R2, R3, R4 |
| 3 | A blank `candidate_id` was not handled. | A single blank ID would appear in the follow-up list. Two blank IDs gave a misleading "duplicate candidate_id" error. | A blank ID is now listed under "needs a data fix" as "missing candidate_id", never in the follow-up list. | R5 |

After the fixes: 25/25 unit tests and 11/11 acceptance checks on Python 3.9.6, 3.12.14 and 3.13.15.

## 7. Where AI helped and where it was corrected

AI (Claude) drafted the plan, the sample data, the ground truth, the tests, the tool and these documents. The full list of instructions and corrections is in `Final directive.md`. In short:

- **Corrected by the independent review**: the three validation gaps in section 6.
- **Corrected by the candidate**:
  - The AI committed with the computer's global Git identity without showing which email it was. The commits were published under a different GitHub account. The candidate noticed, and the commits were rewritten with the right identity.
  - The candidate decided that the official Quest brief should not be published, and it was removed from the history before the first push.
  - The candidate clarified that the timing baseline was spreadsheet-assisted, not fully manual. This document reflects that.
- **Caught by the AI itself**: the GitHub repository already had a commit, so it was merged instead of force-pushed. One test-result report showed the exit code of a helper command instead of the test, so it was re-run.

## 8. What still fails or is not proven

- **Independent check of the ground truth not recorded.** The plan asked for a spreadsheet check of the planted answers at 2026-11-16 before any code was written. No result of that check is recorded in this repository. The ground truth was cross-checked by an AI-written script, which is not independent: the same AI wrote the data, the answers and the tool from the same rules, so a shared misunderstanding would pass every test here.
- **Small synthetic data only.** No real team export was tried. Untested real-world cases include renamed columns, mixed date formats, re-opened candidates and very large files.
- **Rules the tool does not cover**: only stage changes count as movement; calendar days only; one threshold for all stages; dates must be `YYYY-MM-DD`.
- **Strict file checks.** One badly formed row stops the whole report. This was chosen so nothing is misread, but it means one bad row blocks the list until it is fixed.
- **Documentation gap.** `intent.md` (written before building) does not list the rules added after the review: blank IDs as a data fix, and the new structural errors. The README describes the current behaviour.
- **Old commit still reachable.** One old commit with the wrong account attribution (`df75d99`) is no longer in the branch history, but GitHub still serves it to anyone who has its exact ID. Removing it completely needs GitHub Support or recreating the repository.
- **Time saving** is one comparison against a spreadsheet-assisted baseline (section 4).

## 9. The habit I unlearned

*To be written by the candidate:* one habit from the old way of working that was dropped for this Quest, and what was done instead.

## 10. Next improvement

*Proposed by the AI; the candidate to confirm or replace:* run the tool on a real (anonymised) export from the team's board, and time a few daily checks by different team members, including a fully manual review, to replace the single comparison above.

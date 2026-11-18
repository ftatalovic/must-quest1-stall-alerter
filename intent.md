# intent.md - MUST Quest 1, Option C: Stall Alerter

Status: written BEFORE any code or data exists. Targets below are pre-build targets, not results. They must not be relaxed after seeing results. Drafted with AI assistance (Claude), to be reviewed and approved by the candidate before implementation starts.

## 1. The team's problem, in plain words

A recruiting team of three keeps its hiring board in a file. Every day someone scrolls through it to spot candidates who have gone quiet: nobody moved them to the next stage and nobody followed up. Doing this by eye is slow and easy to get wrong. A candidate sitting at "Offer" for two weeks can be missed while the team is busy, and a good candidate who hears nothing gives up and leaves. The company pays twice: for the hours spent checking, and for the candidates lost.

The team will only accept a tool that:

1. runs on their own file (a CSV export of the board),
2. saves time that is actually measured,
3. gets its answers right (finds the stalled people, does not cry wolf),
4. leaves every decision and every message to a person.

## 2. The tool and why this one

**Stall alerter:** one local command that reads the hiring-board CSV and prints three things:

1. **Who to follow up first:** stalled candidates, longest wait first, each with the number of days waiting and a suggested next step.
2. **Rows the tool could not judge:** missing or invalid dates, unknown stages. These are shown to the human with a reason, never silently skipped and never guessed.
3. **A count summary** so the reader can see every row was accounted for.

Why Option C: the right answer for each row is a matter of dates and stages, so it can be decided by fixed rules and checked exactly against planted answers. No AI model runs inside the tool, which means every result is reproducible by anyone, offline, with no API key and no cost. That fits a 4 hour budget and removes the two critical-defect risks (unreproducible numbers, exposed keys) by design.

The tool only reads and prints. It sends nothing, updates nothing, and decides nothing.

## 3. Rules (fixed before building)

**Movement** means a stage change. The CSV column `last_moved_date` holds the date the candidate last changed stage.

| Term | Definition |
|---|---|
| Reference date (`as_of`) | Fixed at **2026-11-16** for all tests. Defaults to today in daily use. |
| Days waiting | `as_of` minus `last_moved_date`, in calendar days |
| Threshold | **7 days** by default, configurable with `--days` |
| Stalled | Active stage AND days waiting **>= threshold** AND no next step scheduled for `as_of` or later |
| Active stages | Applied, Screening, Interview, Offer |
| Closed stages (never flagged) | Hired, Rejected, Withdrawn |
| Scheduled (not flagged) | `next_step_date` is on or after `as_of`: the next step is already booked |
| Data issue (reported separately) | Unknown or blank stage; missing, non-ISO or future `last_moved_date`; unreadable `next_step_date` |

Boundary: exactly 7 days waiting IS stalled; 6 days is NOT.

**Priority order:** (1) most days waiting first; (2) tie: later stage first (Offer, Interview, Screening, Applied), because losing a late-stage candidate costs the most; (3) tie: `candidate_id` ascending.

**Suggested next step** comes from a fixed lookup by stage (for example Offer: "Call the candidate about the pending offer and confirm the decision date"). If a booked step date has passed with no stage change, the text says so. These are suggestions for a human to act on.

## 4. Acceptance test, as numbers

Sample data: 30 synthetic candidates, 5 planted stalled cases, 25 traps and normal rows. The expected answer for all 30 rows is written by hand in a separate ground-truth file BEFORE the detector exists, and cross-checked with a spreadsheet formula, not with the tool.

| # | Measure | Target | How it is checked |
|---|---|---|---|
| AC1 | Dataset | 30 rows; 5 planted stalled; ground truth covers 30/30 rows | Inspect the two CSV files |
| AC2 | Stalled candidates found (recall) | 5/5 = 100% | Tool output IDs vs planted IDs |
| AC3 | False flags | 0 of 25 non-stalled rows | Same comparison |
| AC4 | Priority order | Exact match: C017, C028, C004, C011, C023 | Compare ordered lists |
| AC5 | Data issues | 3/3 reported with a reason; 0 of them in the stalled list | Compare to ground truth |
| AC6 | No row lost | Categories add up: 5 stalled + 3 data issues + 6 closed + 2 scheduled + 14 not stalled = 30 | Summary counts |
| AC7 | Threshold is configurable | `--days 6` gives exactly 7 flags (adds C019 then C002); `--days 10` gives exactly 3 (C017, C028, C004) | Run with both values |
| AC8 | Every flag is explained | 5/5 flags show days waiting and a suggested next step | Inspect output |
| AC9 | Repeatable | Two runs with the same inputs give byte-identical output | Compare outputs |
| AC10 | Human control | 0 messages sent, 0 changes to the input file (same SHA-256 before and after), 0 network modules imported, works offline | Automated checks plus code inspection |
| AC11 | Edge-case tests | 100% of the listed unit tests pass | `python3 -m unittest` |
| AC12 | Time saved | At least 50% less time than a manual pass on the same file | Stopwatch: one manual pass, one tool-assisted review. Actual times reported even if the target is missed |

Recall is 5/5 only if AC2 holds at the default threshold with `as_of` 2026-11-16. A reviewer can repeat every check from AC1 to AC11 with one command.

On AC12: the manual time is one person, one pass, on a 30 row toy file. It will be reported as exactly that. Any "minutes per day" figure will be labelled as an extrapolation with its assumptions, not as a measured fact.

## 5. What already exists (checked before building)

Source: the candidate's and the AI's working knowledge. No web research was run in this session; that is stated as a limitation.

| Existing option | Verdict |
|---|---|
| Spreadsheet formula (date difference, FILTER, SORT, conditional formatting) | Can do the core flagging. **Reused** as the independent check of the ground truth and as the realistic manual baseline. Weak on bad data (a text date silently fails), on repeatability, and on tests. |
| Built-in stale-candidate alerts in commercial hiring systems | Exist in several products, but the customer works from a CSV file and the brief rules out new logins and systems. Not used. |
| Python standard library (`csv`, `datetime`, `argparse`, `unittest`) | **Reused** for everything. Nothing to install. |
| pandas | Would work, but adds an install step for a 30 row file and no benefit. Not used. |
| AI API inside the tool | Not needed: the rules are exact. It would add cost, a key to protect, and non-repeatable answers. Not used. AI is used to plan, write and review the code instead. |

**The gap we build:** one repeatable command that applies the rules above, reports bad rows instead of hiding them, orders the list with a documented tie-break, attaches a next step, and is proven by tests against planted answers.

## 6. Left out to fit 4 hours

- Any user interface beyond one command and its printed output
- Sending emails or messages, drafting message text, calendar or board updates
- Connecting to a live hiring system, logins, scheduling the tool to run daily
- Business days and public holidays (calendar days only)
- Different thresholds per stage
- Full activity history (emails, calls): "movement" is stage change only
- Date formats other than `YYYY-MM-DD` (others are reported as data issues, not guessed)
- Options A and B

## 7. What stays with a person

- Whether a flagged candidate really needs a follow-up, and what to say
- Sending any message and updating the board
- Fixing the rows listed as data issues
- Choosing the threshold and the list of active and closed stages
- Checking the AI-written code, the ground truth and every number in `evidence.md`

## 8. Decision to confirm at approval

The `next_step_date` rule (do not flag a candidate whose next step is already booked) is an addition beyond the brief's minimum. It is included because flagging someone with an interview booked for tomorrow is the most likely false alarm in real use. If the candidate prefers the bare minimum, it must be removed now, before the data is created, not after results are seen.

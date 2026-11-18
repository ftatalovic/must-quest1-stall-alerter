# Final directive - Stall alerter (MUST Quest 1, Option C)

This file records how the AI tools were instructed, so another person can repeat the process, and where their output was checked or corrected. It is based on the actual session record. Nothing here is reconstructed from memory beyond what that record shows.

## 1. Who did what

| Who | Role |
|---|---|
| Candidate (human) | Chose Option C, approved the plan, made every decision about scope, publishing and Git, reported the independent code review, ran the timing measurement, owns the submission |
| Claude Fable 5.2 | Planning only: `intent.md` and `implementation_plan.md` (no code, no data) |
| Claude Opus 5.5, in Claude Code | Implementation: sample data, ground truth, tests, tool, Git and GitHub steps, these documents |
| Independent code reviewer | Reviewed commit `5366e9f`. Result: PASS WITH ISSUES, three findings |
| Standing instructions | `CLAUDE.md` and `AGENTS.md`: inspect before coding, define success as numbers first, no invented results, no unapproved external actions, the human owns every decision |

## 2. The directive, step by step (reusable)

Give these to an AI coding assistant in order. **Stop after each step** and have a person check the result before giving the next one.

**Step 0. Plan (no code).** "Read the brief, `CLAUDE.md` and `AGENTS.md`. Option C only. Act as architect and plan only. Define the acceptance test as numbers before anything is built. Design 30 synthetic rows with 5 planted stalled candidates and boundary cases. Use fixed rules with a fixed reference date. Check what already exists. Use the standard library unless there is a reason not to. Define the tests, the false-flag checks and the timing method. Name the risks and the points where a person must decide. Write `intent.md` and `implementation_plan.md`, then stop for approval."

**Step 1. Data and answers first.** "The plan is approved. Decisions: [list them]. Phase 1 only. Set up Git. Create the 30-row board exactly as planned. Write the ground truth separately from any detector. Check the category counts and the priority order. Include the boundary cases and bad-data rows. Commit the acceptance criteria, data and ground truth **before** any detector code. Show the expected results and the commit ID. Do not write the detector. Do not change the acceptance criteria. Do not overwrite the planning documents. Do not invent results. Stop."

**Step 2. Publish safely, then write the tests.** "Connect the existing repository to [GitHub URL]. Check the status, branch and remotes first. Keep the existing history. Do not force push or create a new repository. Do not push secrets or temporary files. Verify the commits and files on GitHub. Then write the unit tests and the acceptance script from the plan. They must fail while no detector exists."

**Step 3. Build to the tests.** "Write the tool according to the plan. Run the unit tests and the acceptance test and report the actual results and failures. Do not change the ground truth or the acceptance targets."

**Step 4. Independent review.** Have someone (or a separate tool) who did not write the code review it. Then: "Make these minimal fixes: [findings]. Add a regression test for each. Keep the behaviour for the 30 sample rows unchanged. Do not change the acceptance criteria or the data. Run everything, commit, push and report the actual results."

**Step 5. Measure and document.** The person times the old way and the new way on the same file. Then: "Write `README.md`, `evidence.md` and `Final directive.md` from the actual measurements. Describe the review findings, the corrections, the regression tests and the remaining limits in plain words for a non-technical team. Do not invent verification results."

**Guardrails worth stating up front** (each one was learned the hard way in this Quest, see section 3):

- "Before the first commit, show me the exact Git name and email that will be used, and which GitHub account will push."
- "Before pushing, tell me whether the repository is public and list every file that will be published."
- "Run the tests on every Python version we claim to support, not just the default one."
- "Report the exit code of the test command itself, not of a command it was piped into."

## 3. Where AI output was checked or corrected

| # | What happened | Found by | Correction | Commit |
|---|---|---|---|---|
| 1 | The AI committed with the computer's global Git identity. It checked that an email was set but did not show which one, and that email belonged to a different GitHub account. Two commits were published on GitHub under that account. | Candidate | The identity was set for this repository only (name Filip Tatalovic, account `ftatalovic`). The commits were rewritten with the same content and order, then one approved `--force-with-lease` push. GitHub's commit list was checked: every commit is attributed to `ftatalovic`. The old commit `df75d99` can still be opened by its exact ID (see `evidence.md` section 8). | `45accf6`, `9d669ba`, `4769ef5` |
| 2 | The GitHub repository is public, and the official brief (`TASK.md`) would have been published. | AI flagged it before the first push; candidate decided | The repository stays public and `TASK.md` stays local only. It is in `.gitignore` and was removed from all history before the first push. Verified: no published commit contains it. | `45accf6` onward |
| 3 | GitHub had created its own first commit, so a plain push would be rejected. | AI | Built on top of GitHub's commit instead of force pushing. | `7c2a87a` kept |
| 4 | The AI said its date test covered newer Python versions. On Python 3.12 and 3.13, `2026-W47-3` was still read as a valid date and flagged. | Independent review | Exact `YYYY-MM-DD` shape check before reading a date; regression test R1. The tests are now run on 3.9, 3.12 and 3.13. | `a5aeb8f` |
| 5 | Duplicate column names and rows with too many or too few fields were accepted silently. | Independent review | They now stop the run with a clear error and the line number; tests R2-R4. | `a5aeb8f` |
| 6 | A blank `candidate_id` could appear in the follow-up list. | Independent review | It is now listed as a data fix; test R5. | `a5aeb8f` |
| 7 | One test report showed the exit code of a helper command, not of the test. | AI | Re-run without the pipe to get the real exit code (0). | none |
| 8 | The timing baseline was spreadsheet-assisted, not fully manual. | Candidate clarification | The documents describe it as a comparison against a spreadsheet-assisted review. The candidate's estimate for a fully manual review is labelled as not measured. | this commit |

## 4. Checks run on the AI's own work

- **Ground truth**: cross-checked against the board's dates and the targets in `intent.md` by a separate AI-written script. All checks passed. This is **not** an independent check, because the same AI wrote both. The planned spreadsheet check by a person is not recorded (see `evidence.md` section 8).
- **Order of work**: Git history shows the targets, data and ground truth (`45accf6`, `9d669ba`) and the failing tests (`4769ef5`) were committed before the tool (`5366e9f`).
- **Tests failed first**: unit tests 0/20 and acceptance 1/11 before the tool existed.
- **Planted-bug check**: 10 of 11 deliberately planted bugs were caught by the tests.
- **Regression tests**: all fail on the old code and pass on the fixed code.
- **Fresh clone from GitHub**: unit tests and acceptance pass (exit 0).

## 5. What stays with a person

- Deciding whether a flagged candidate really needs a follow-up, and what to say.
- Sending any message and updating the board.
- Fixing the rows listed under "needs a data fix".
- Choosing the threshold and the stage names.
- Checking the AI's code, the ground truth and every number in `evidence.md` before submitting.

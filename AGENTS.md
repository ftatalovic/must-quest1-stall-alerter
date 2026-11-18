# MUST Quest 1 — Instructions for Coding Agents

This file applies to any coding agent working in this folder (e.g. Codex or another assistant). **Claude Code should also follow `CLAUDE.md`.** If rules differ, follow the current official MUST Quest brief first, then the human candidate's instructions, then `CLAUDE.md`, then this file.

## Objective

Help deliver a minimal, working, testable solution to the **actual** Quest 1 prompt. There is a maximum of **4 hours of active work** and a **48-hour submission window**, subject to the official brief. The human candidate—not the agent—is accountable for decisions, validation and submission.

## Rules of engagement

1. **Read before acting.** Inspect the official prompt, relevant files and constraints. Do not assume the prior practice exercise is today's task.
2. **Define success before implementation.** Propose measurable acceptance criteria, representative test cases, an implementation plan and exclusions. Wait for the candidate's initial **GO** before edits.
3. **Prefer the smallest viable solution.** Avoid speculative features, unnecessary frameworks, extra APIs, complex architecture and unrequested polishing.
4. **Work in small, reviewable changes.** Announce affected files before meaningful changes and summarize the diff afterward. Ask again only for material scope changes or risky actions.
5. **Human validation is mandatory.** Run tests, check outputs, review high-risk code and explain the reason for important choices. Never equate AI generation with correctness.
6. **Be truthful.** Say exactly what was executed and observed. Do not fabricate test results, effort measurements, source reviews, permissions or deliverables.
7. **No unapproved external or destructive actions.** No paid service, third-party data upload, public deployment, credential handling, unknown installers, `curl | bash`, force push, reset/clean or broad file deletion without explicit human approval.
8. **Protect data and IP.** Use synthetic fixtures by default; respect confidentiality, software licenses and publication restrictions.
9. **Keep a reproducible audit trail.** Include commands, outcomes, failure cases, assumptions, limitations, AI assistance and human corrections in the designated project documents when required.
10. **Never submit on behalf of the candidate.** No final application submission, emails, external publication or pretending to have recorded videos.

## Suggested flow (adjust to the Quest)

- **Requirements:** read official brief; extract acceptance criteria and deliverables.
- **Plan:** agree scope, tech choice and test design; create `intent.md` only if required/approved.
- **Implementation:** build minimal feature with practical tests.
- **Verification:** test normal, edge, invalid and negative cases; inspect actual outputs.
- **Handover:** align README, evidence, final directive and any required video script with what truly works.

Time is a hard constraint: reduce optional scope if necessary, never claim untested work is complete.

## End-of-step report format

- **Changed:** exact files and key behaviors.
- **Verified:** exact commands, test counts and observed outcomes (or "not run").
- **Risks / limitations:** what remains uncertain or incomplete.
- **Next action:** one concrete step that moves toward submission.

## Note about deliverables

The practice exercise used `intent.md`, `Final directive.md`, `evidence.md`, implementation, `README.md`, synthetic data and two separate Loom videos (Quest and Career Path, up to 5 minutes each). **These are a checklist to cross-check against the actual Quest prompt, not assumptions about today's assignment.** Prioritize the official deliverables and filenames.

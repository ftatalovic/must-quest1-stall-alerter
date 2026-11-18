"""Stall alerter: lists hiring-board candidates who have not moved for N days.

Reads a hiring-board CSV, finds active candidates whose stage has not changed for
at least --days calendar days (default 7) with no next step booked, and prints who
to follow up first with a suggested next step. Rows it cannot judge are listed
separately with a reason. It only reads the input file: it sends nothing, writes
nothing and decides nothing. A person reviews every line.

Usage:
    python3 stall_alerter.py data/hiring_board.csv --as-of 2026-11-16 --days 7

Exit codes: 0 report printed, 2 input or argument problem (message on stderr).
Rules: intent.md section 3 and implementation_plan.md section 4.
"""
import argparse
import csv
import datetime
import sys

REQUIRED_COLUMNS = ("candidate_id", "candidate_name", "role", "stage",
                    "last_moved_date", "next_step_date", "recruiter")
ACTIVE_STAGES = {"applied": "Applied", "screening": "Screening",
                 "interview": "Interview", "offer": "Offer"}
CLOSED_STAGES = {"hired": "Hired", "rejected": "Rejected", "withdrawn": "Withdrawn"}
# Tie-break when days are equal: a later stage is more costly to lose.
STAGE_RANK = {"Offer": 0, "Interview": 1, "Screening": 2, "Applied": 3}
NEXT_STEP = {
    "Applied": "Review the application and decide whether to screen or decline.",
    "Screening": "Book or complete the screening call and tell the candidate where they stand.",
    "Interview": "Chase interviewer feedback or book the next round, then update the candidate.",
    "Offer": "Call the candidate about the pending offer and confirm the decision date.",
}


class InputError(Exception):
    """The file cannot be processed as a hiring board (structural problem)."""


def parse_iso_date(value):
    """Return a date for strict YYYY-MM-DD text, else None. Never guesses other formats."""
    # Check the shape first: Python 3.11+ fromisoformat also accepts other ISO
    # forms such as 20261109 and the week date 2026-W47-3.
    digits = value[:4] + value[5:7] + value[8:]
    if (len(value) != 10 or value[4] != "-" or value[7] != "-"
            or not all(ch in "0123456789" for ch in digits)):
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


def field(row, name):
    return (row.get(name) or "").strip()


def load_rows(path):
    """Read the CSV (read-only). Raises InputError on a malformed structure:
    duplicate or missing columns, rows with more or fewer fields than the
    header, or duplicate candidate IDs."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = [h.strip() for h in (reader.fieldnames or [])]
        duplicates = sorted({h for h in header if header.count(h) > 1})
        if duplicates:
            raise InputError(f"duplicate column name(s): {', '.join(duplicates)}")
        missing = [c for c in REQUIRED_COLUMNS if c not in header]
        if missing:
            raise InputError(f"missing required column(s): {', '.join(missing)}")
        reader.fieldnames = header
        rows = []
        for row in reader:
            if None in row:  # DictReader puts surplus fields under the key None
                raise InputError(f"line {reader.line_num}: more fields than the "
                                 f"{len(header)} header columns")
            if None in row.values():  # DictReader fills absent fields with None
                raise InputError(f"line {reader.line_num}: fewer fields than the "
                                 f"{len(header)} header columns")
            rows.append(row)
    seen = set()
    for row in rows:
        cid = field(row, "candidate_id")
        if cid and cid in seen:  # blank IDs are reported per row by classify()
            raise InputError(f"duplicate candidate_id: {cid or '(blank)'}")
        seen.add(cid)
    return rows


def suggested_step(stage, next_step):
    text = NEXT_STEP[stage]
    if next_step is not None:  # a booked step exists and is before as_of
        text = (f"Booked step on {next_step.isoformat()} has passed with no board update: "
                f"confirm what happened. Then: {text[0].lower()}{text[1:]}")
    return text


def classify(row, as_of, threshold):
    """Return (category, days, reason). Rules are applied in order; first match wins."""
    if not field(row, "candidate_id"):  # cannot be followed up without an ID
        return "data_issue", None, "missing candidate_id"
    stage_key = field(row, "stage").lower()
    if stage_key in CLOSED_STAGES:
        return "closed", None, "closed stage"
    stage = ACTIVE_STAGES.get(stage_key)
    if stage is None:
        return "data_issue", None, f"unknown stage '{field(row, 'stage')}'"
    moved_text = field(row, "last_moved_date")
    if not moved_text:
        return "data_issue", None, "missing date"
    moved = parse_iso_date(moved_text)
    if moved is None:
        return "data_issue", None, f"invalid date '{moved_text}' (expected YYYY-MM-DD)"
    if moved > as_of:
        return "data_issue", None, f"future date {moved_text} (after {as_of.isoformat()})"
    next_text = field(row, "next_step_date")
    next_step = None
    if next_text:
        next_step = parse_iso_date(next_text)
        if next_step is None:
            return "data_issue", None, f"invalid next step date '{next_text}' (expected YYYY-MM-DD)"
    days = (as_of - moved).days
    if next_step is not None and next_step >= as_of:
        return "scheduled", days, f"next step booked for {next_text}"
    if days >= threshold:
        return "stalled", days, suggested_step(stage, next_step)
    return "not_stalled", days, "moved recently"


def stage_label(stage_text):
    key = stage_text.strip().lower()
    return ACTIVE_STAGES.get(key) or CLOSED_STAGES.get(key) or stage_text.strip()


def prioritize(items):
    """Most days first; tie: later stage first; tie: candidate_id ascending."""
    return sorted(items, key=lambda i: (-i["days"],
                                        STAGE_RANK.get(stage_label(i["stage"]), len(STAGE_RANK)),
                                        i["candidate_id"].strip()))


def clean(text):
    """Make a CSV value safe to print on one terminal line."""
    return "".join(ch if ch.isprintable() else "?" for ch in (text or "").strip())


def render(results, as_of, threshold):
    """Plain-text report. Contains no wall-clock time, so equal inputs give equal output."""
    by_cat = {}
    for r in results:
        by_cat.setdefault(r["category"], []).append(r)
    stalled = prioritize(by_cat.get("stalled", []))
    issues = by_cat.get("data_issue", [])
    out = [f"Stall alerter | as of {as_of.isoformat()} | threshold {threshold} days | "
           f"{len(results)} rows read",
           f"FOLLOW UP FIRST ({len(stalled)}) - suggestions only, a person decides and sends"]
    for rank, r in enumerate(stalled, 1):
        unit = "day" if r["days"] == 1 else "days"
        out.append(f"{rank:>2}. {clean(r['candidate_id'])}  {clean(r['candidate_name'])}  "
                   f"{stage_label(r['stage'])}  {r['days']} {unit}  owner: {clean(r['recruiter'])}")
        out.append(f"    Suggested: {r['reason']}")
    if not stalled:
        out.append("    (none)")
    out.append(f"NEEDS A DATA FIX ({len(issues)}) - not judged by the tool")
    for r in issues:
        out.append(f" {clean(r['candidate_id']) or '(blank id)'}  {clean(r['candidate_name'])}  "
                   f"{clean(r['stage']) or '(blank stage)'}  {clean(r['reason'])}")
    if not issues:
        out.append("    (none)")
    n = {c: len(by_cat.get(c, [])) for c in
         ("stalled", "not_stalled", "scheduled", "closed", "data_issue")}
    out.append(f"SUMMARY  stalled {n['stalled']} | not stalled {n['not_stalled']} | "
               f"scheduled {n['scheduled']} | closed {n['closed']} | "
               f"data issues {n['data_issue']} | total {len(results)}")
    out.append("Nothing was sent or changed. Input file was only read.")
    return "\n".join(out) + "\n"


def as_of_arg(text):
    value = parse_iso_date(text.strip())
    if value is None:
        raise argparse.ArgumentTypeError(f"'{text}' is not a YYYY-MM-DD date")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="List hiring-board candidates who have not moved for N days. Read-only.")
    parser.add_argument("csv_path", help="hiring board CSV export")
    parser.add_argument("--as-of", type=as_of_arg, default=None,
                        help="reference date YYYY-MM-DD (default: today)")
    parser.add_argument("--days", type=int, default=7,
                        help="stall threshold in calendar days (default: 7)")
    args = parser.parse_args(argv)
    if args.days < 1:
        print(f"error: --days must be 1 or more, got {args.days}", file=sys.stderr)
        return 2
    as_of = args.as_of or datetime.date.today()
    try:
        rows = load_rows(args.csv_path)
    except (OSError, InputError, csv.Error, UnicodeDecodeError) as e:
        print(f"error: cannot read {args.csv_path}: {e}", file=sys.stderr)
        return 2
    results = []
    for row in rows:
        category, days, reason = classify(row, as_of, args.days)
        results.append(dict(row, category=category, days=days, reason=reason))
    sys.stdout.write(render(results, as_of, args.days))
    return 0


if __name__ == "__main__":
    sys.exit(main())

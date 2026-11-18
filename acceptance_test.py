"""Acceptance test for the stall alerter: AC1-AC11 from intent.md section 4.

Written BEFORE stall_alerter.py exists. Runs the real command on
data/hiring_board.csv with the fixed reference date, compares the printed report
with data/ground_truth.csv, and prints one PASS/FAIL line per criterion with the
actual numbers. Exit 0 only if every line is PASS. AC12 (time saved) is a human
stopwatch measurement and is not automated here.

Usage (repo root):  python3 acceptance_test.py
"""
import ast
import csv
import datetime
import hashlib
import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(ROOT, "data", "hiring_board.csv")
GROUND_TRUTH = os.path.join(ROOT, "data", "ground_truth.csv")
TOOL = os.path.join(ROOT, "stall_alerter.py")
AS_OF = "2026-11-16"

# Targets copied from intent.md / implementation_plan.md BEFORE any detector code.
# Do not edit these to make results pass.
EXPECTED_ORDER = {
    7: ["C017", "C028", "C004", "C011", "C023"],
    6: ["C017", "C028", "C004", "C011", "C023", "C019", "C002"],
    10: ["C017", "C028", "C004"],
}
EXPECTED_DAYS = {"C017": 21, "C028": 14, "C004": 14, "C011": 9, "C023": 7}
EXPECTED_COUNTS = {"stalled": 5, "not_stalled": 14, "scheduled": 2, "closed": 6, "data_issue": 3}
EXPECTED_ISSUES = {"C009": "missing date", "C014": "invalid date", "C026": "future date"}
# Plan section 7 list, plus other stdlib modules that can send or open things.
FORBIDDEN_MODULES = {"socket", "smtplib", "urllib", "http", "requests", "subprocess",
                     "email", "ftplib", "imaplib", "poplib", "ssl", "webbrowser",
                     "xmlrpc", "asyncio", "telnetlib"}

# Report format from implementation_plan.md section 5 (output sketch).
RE_FLAG = re.compile(r"^\s*(\d+)\.\s+(C\d{3})\b(.*)$")
RE_ISSUE = re.compile(r"^\s+(C\d{3})\b(.*)$")
RE_SUMMARY = re.compile(r"SUMMARY\s+stalled (\d+) \| not stalled (\d+) \| scheduled (\d+) \| "
                        r"closed (\d+) \| data issues (\d+) \| total (\d+)")
SECTION_FLAGS, SECTION_ISSUES = "FOLLOW UP FIRST", "NEEDS A DATA FIX"


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def run_tool(board=BOARD, *extra):
    """Run the CLI exactly as a user would. Returns (exit_code, stdout_bytes, stderr_text)."""
    if not os.path.exists(TOOL):
        raise RuntimeError("stall_alerter.py not found")
    p = subprocess.run([sys.executable, TOOL, board, "--as-of", AS_OF] + list(extra),
                       cwd=ROOT, capture_output=True, timeout=60)
    return p.returncode, p.stdout, p.stderr.decode("utf-8", "replace")


def parse_report(stdout):
    """Split the printed report into flagged entries, data-issue entries and summary counts."""
    lines = stdout.decode("utf-8").splitlines()
    try:
        i_flags = next(i for i, l in enumerate(lines) if l.startswith(SECTION_FLAGS))
        i_issues = next(i for i, l in enumerate(lines) if l.startswith(SECTION_ISSUES))
        i_summary = next(i for i, l in enumerate(lines) if l.startswith("SUMMARY"))
    except StopIteration:
        raise RuntimeError("report sections not found; output does not match the plan format")
    flags = []
    for i in range(i_flags + 1, i_issues):
        m = RE_FLAG.match(lines[i])
        if m:
            nxt = next((l for l in lines[i + 1:i_issues] if l.strip()), "")
            flags.append({"rank": int(m.group(1)), "id": m.group(2), "line": lines[i],
                          "next_line": nxt.strip()})
    issues = {}
    for i in range(i_issues + 1, i_summary):
        m = RE_ISSUE.match(lines[i])
        if m:
            issues[m.group(1)] = m.group(2)
    m = RE_SUMMARY.search(lines[i_summary])
    if not m:
        raise RuntimeError("summary line does not match the plan format")
    keys = ["stalled", "not_stalled", "scheduled", "closed", "data_issue", "total"]
    return flags, issues, dict(zip(keys, map(int, m.groups())))


def import_tool():
    if not os.path.exists(TOOL):
        raise RuntimeError("stall_alerter.py not found")
    spec = importlib.util.spec_from_file_location("stall_alerter", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def source_audit():
    """Return (imported top-level modules, write-mode open() calls) found in the tool source."""
    with open(TOOL, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    imported, write_opens = set(), []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if name == "__import__" or name == "import_module":
                imported.add("<dynamic import>")
            if name == "open":
                mode = node.args[1] if len(node.args) > 1 else next(
                    (k.value for k in node.keywords if k.arg == "mode"), None)
                if mode is not None and not (isinstance(mode, ast.Constant) and
                                             not set(str(mode.value)) & set("wax+")):
                    write_opens.append(node.lineno)
    return imported, write_opens


# --------------------------------------------------------------------------- checks
# Each returns (ok: bool, detail: str).

def ac1():
    board, gt = read_csv(BOARD), read_csv(GROUND_TRUTH)
    b_ids, g_ids = [r["candidate_id"] for r in board], [r["candidate_id"] for r in gt]
    ranked = [r["candidate_id"] for r in sorted((r for r in gt if r["expected_rank"]),
                                                key=lambda r: int(r["expected_rank"]))]
    planted = sum(r["expected_category"] == "stalled" for r in gt)
    ok = (len(board) == 30 and b_ids == g_ids and planted == 5 and ranked == EXPECTED_ORDER[7])
    return ok, (f"{len(board)} board rows, ground truth covers {len(set(g_ids) & set(b_ids))}/30, "
                f"{planted} planted stalled, ranked {ranked}")


def gt_sets():
    gt = read_csv(GROUND_TRUTH)
    stalled = {r["candidate_id"] for r in gt if r["expected_category"] == "stalled"}
    return gt, stalled


def ac2():
    _, stalled = gt_sets()
    flagged = {f["id"] for f in parse_report(run_tool()[1])[0]}
    tp, fn = sorted(flagged & stalled), sorted(stalled - flagged)
    return len(tp) == 5 and not fn, f"recall {len(tp)}/5 = {len(tp) * 20}% | found {tp} | missed {fn}"


def ac3():
    gt, stalled = gt_sets()
    flagged = {f["id"] for f in parse_report(run_tool()[1])[0]}
    fp = sorted(flagged - stalled)
    return not fp, f"false flags {len(fp)} of {len(gt) - len(stalled)} non-stalled rows {fp}"


def ac4():
    gt = read_csv(GROUND_TRUTH)
    expected = [r["candidate_id"] for r in sorted((r for r in gt if r["expected_rank"]),
                                                  key=lambda r: int(r["expected_rank"]))]
    flags = parse_report(run_tool()[1])[0]
    got = [f["id"] for f in flags]
    ranks_ok = [f["rank"] for f in flags] == list(range(1, len(flags) + 1))
    return got == expected and ranks_ok, f"expected {expected} | got {got}"


def ac5():
    flags, issues, _ = parse_report(run_tool()[1])
    flagged = {f["id"] for f in flags}
    reported = sorted(c for c, why in EXPECTED_ISSUES.items() if c in issues and why in issues[c])
    leaked = sorted(set(EXPECTED_ISSUES) & flagged)
    extra = sorted(set(issues) - set(EXPECTED_ISSUES))
    ok = len(reported) == 3 and not leaked and not extra
    return ok, (f"{len(reported)}/3 reported with the expected reason {reported} | "
                f"in stalled list {leaked} | unexpected issue rows {extra}")


def ac6():
    mod = import_tool()
    as_of = datetime.date.fromisoformat(AS_OF)
    gt = {r["candidate_id"]: r["expected_category"] for r in read_csv(GROUND_TRUTH)}
    rows = mod.load_rows(BOARD)
    got = {r["candidate_id"]: mod.classify(r, as_of, 7)[0] for r in rows}
    wrong = sorted(f"{c}: expected {gt[c]} got {got.get(c)}" for c in gt if got.get(c) != gt[c])
    summary = parse_report(run_tool()[1])[2]
    counts_ok = all(summary[k] == v for k, v in EXPECTED_COUNTS.items()) and summary["total"] == 30
    parts = sum(summary[k] for k in EXPECTED_COUNTS)
    ok = not wrong and counts_ok and parts == 30
    return ok, (f"per-row {30 - len(wrong)}/30 correct {wrong} | summary {summary} | "
                f"parts sum to {parts}")


def ac7():
    details, ok = [], True
    for days in (6, 10):
        got = [f["id"] for f in parse_report(run_tool(BOARD, "--days", str(days))[1])[0]]
        ok &= got == EXPECTED_ORDER[days]
        details.append(f"--days {days}: {len(got)} flags {got}")
    return ok, " | ".join(details)


def ac8():
    flags = parse_report(run_tool()[1])[0]
    good = []
    for f in flags:
        days_ok = f["id"] in EXPECTED_DAYS and re.search(rf"\b{EXPECTED_DAYS[f['id']]} days\b", f["line"])
        step_ok = f["next_line"].startswith("Suggested:")
        if days_ok and step_ok:
            good.append(f["id"])
    c011 = next((f for f in flags if f["id"] == "C011"), None)
    passed_ok = bool(c011) and "2026-11-12" in c011["next_line"]
    ok = len(good) == 5 and len(flags) == 5 and passed_ok
    return ok, (f"{len(good)}/{len(flags)} flags show correct days and a Suggested step | "
                f"C011 mentions its passed step 2026-11-12: {passed_ok}")


def ac9():
    a, b = run_tool()[1], run_tool()[1]
    return a == b and len(a) > 0, f"two runs byte-identical: {a == b} ({len(a)} bytes)"


def ac10(sha_before):
    imported, write_opens = source_audit()
    bad = sorted(imported & FORBIDDEN_MODULES | ({"<dynamic import>"} & imported))
    guard = "no write-mode open() in source"
    guard_ok = True
    if write_opens:  # e.g. an --out report: prove it refuses to overwrite the input file
        with tempfile.TemporaryDirectory() as tmp:
            copy = os.path.join(tmp, "board.csv")
            shutil.copyfile(BOARD, copy)
            before = sha256(copy)
            code = run_tool(copy, "--out", copy)[0]
            guard_ok = code == 2 and sha256(copy) == before
        guard = f"write-mode open() at lines {write_opens}; --out onto input refused: {guard_ok}"
    sha_after = sha256(BOARD)
    ok = not bad and guard_ok and sha_after == sha_before
    return ok, (f"input SHA-256 unchanged: {sha_after == sha_before} | forbidden imports {bad} | "
                f"imports {sorted(imported)} | {guard}")


def ac11():
    # same discovery as: python3 -m unittest discover -s tests
    suite = unittest.defaultTestLoader.discover(os.path.join(ROOT, "tests"))
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    bad = len(result.failures) + len(result.errors)
    passed = result.testsRun - bad - len(result.skipped)
    ok = result.testsRun >= 20 and bad == 0 and not result.skipped
    return ok, (f"{passed}/{result.testsRun} unit tests pass | failures {len(result.failures)} "
                f"errors {len(result.errors)} skipped {len(result.skipped)}")


def main():
    sha_before = sha256(BOARD)
    checks = [("AC1 dataset", ac1), ("AC2 recall", ac2), ("AC3 false flags", ac3),
              ("AC4 priority order", ac4), ("AC5 data issues", ac5), ("AC6 no row lost", ac6),
              ("AC7 threshold configurable", ac7), ("AC8 every flag explained", ac8),
              ("AC9 repeatable", ac9), ("AC10 human control", lambda: ac10(sha_before)),
              ("AC11 unit tests", ac11)]
    print(f"Acceptance test | as_of {AS_OF} | input {os.path.relpath(BOARD, ROOT)} "
          f"| SHA-256 {sha_before[:16]}...")
    passed = 0
    for name, fn in checks:
        try:
            ok, detail = fn()
        except Exception as e:  # report, never crash: a missing tool is a FAIL, not a traceback
            ok, detail = False, f"error: {e}"
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
    print("----  AC12 time saved: human stopwatch measurement (implementation_plan.md section 8), "
          "not automated")
    print(f"RESULT: {passed}/{len(checks)} PASS")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())

"""Unit tests T1-T20 for the stall alerter (implementation_plan.md section 6).

Written BEFORE stall_alerter.py exists. They use small in-memory rows, not the
30-row dataset, so they test the rules independently of the planted answers.

Interface these tests expect (implementation_plan.md section 5):
    classify(row, as_of, threshold) -> (category, days, reason)
        category: "stalled" | "not_stalled" | "scheduled" | "closed" | "data_issue"
        days:     int calendar days waiting, or None when not judged from a date
        reason:   for data_issue, names the problem ("missing date", "invalid date",
                  "future date", "unknown stage", "invalid next step date");
                  for stalled, the suggested next step text
    prioritize(items) -> new list sorted by (-days, later stage first, candidate_id);
        each item is a dict with at least candidate_id, stage, days
    load_rows(path) -> list of dicts, one per CSV row
    main(argv) -> int exit code (0 ok, 2 structural failure); prints the report

Run from the repo root:  python3 -m unittest discover -s tests -v
"""
import contextlib
import datetime
import io
import os
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    import stall_alerter as sa
except ImportError:  # expected until the detector is written
    sa = None

AS_OF = datetime.date(2026, 11, 16)
HEADER = "candidate_id,candidate_name,role,stage,last_moved_date,next_step_date,recruiter"


def day(offset):
    """ISO date string `offset` days relative to AS_OF (negative = in the past)."""
    return (AS_OF + datetime.timedelta(days=offset)).isoformat()


def row(stage="Interview", last_moved=None, next_step="", cid="C001"):
    return {
        "candidate_id": cid,
        "candidate_name": "Test Person",
        "role": "Test Role",
        "stage": stage,
        "last_moved_date": day(-7) if last_moved is None else last_moved,
        "next_step_date": next_step,
        "recruiter": "Tester",
    }


def run_main(argv):
    """Call main(argv); return (exit_code, stdout, stderr). argparse exits count as codes."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = sa.main(argv)
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), err.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        if sa is None:
            self.fail("stall_alerter.py not found (detector not written yet)")

    def assertCategory(self, r, expected, threshold=7, as_of=AS_OF):
        category, days, reason = sa.classify(r, as_of, threshold)
        self.assertEqual(category, expected, f"row={r} reason={reason!r}")
        return category, days, reason

    def write_csv(self, text, encoding="utf-8"):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = os.path.join(tmp.name, "board.csv")
        with open(path, "w", encoding=encoding, newline="") as f:
            f.write(text)
        return path


class TestClassify(Base):
    def test_t01_exactly_threshold_is_stalled(self):
        _, days, _ = self.assertCategory(row(last_moved=day(-7)), "stalled")
        self.assertEqual(days, 7)

    def test_t02_one_day_under_threshold_not_stalled(self):
        _, days, _ = self.assertCategory(row(last_moved=day(-6)), "not_stalled")
        self.assertEqual(days, 6)

    def test_t03_zero_days_not_stalled(self):
        _, days, _ = self.assertCategory(row(last_moved=day(0)), "not_stalled")
        self.assertEqual(days, 0)

    def test_t04_closed_stages_never_stalled(self):
        for stage in ("Hired", "Rejected", "Withdrawn"):
            with self.subTest(stage=stage):
                self.assertCategory(row(stage=stage, last_moved=day(-100)), "closed")

    def test_t05_closed_stage_with_blank_date_is_closed(self):
        self.assertCategory(row(stage="Rejected", last_moved=""), "closed")

    def test_t06_blank_date_is_data_issue(self):
        _, _, reason = self.assertCategory(row(last_moved=""), "data_issue")
        self.assertIn("missing date", reason)

    def test_t07_invalid_date_formats_are_data_issue(self):
        # "20261109" is extra: Python 3.11+ fromisoformat accepts it, so the
        # length-10 check from the plan must reject it on any version.
        for bad in ("05/11/2026", "2026-13-01", "yesterday", "20261109"):
            with self.subTest(value=bad):
                _, _, reason = self.assertCategory(row(last_moved=bad), "data_issue")
                self.assertIn("invalid date", reason)

    def test_t08_future_date_is_data_issue(self):
        _, _, reason = self.assertCategory(row(last_moved=day(1)), "data_issue")
        self.assertIn("future date", reason)

    def test_t09_unknown_or_blank_stage_is_data_issue(self):
        for stage in ("On Hold", ""):
            with self.subTest(stage=stage):
                _, _, reason = self.assertCategory(row(stage=stage), "data_issue")
                self.assertIn("unknown stage", reason)

    def test_t10_stage_whitespace_and_case_normalised(self):
        self.assertCategory(row(stage=" offer ", last_moved=day(-8)), "stalled")

    def test_t11_next_step_today_or_later_is_scheduled(self):
        for nxt in (day(0), day(1)):
            with self.subTest(next_step=nxt):
                self.assertCategory(row(last_moved=day(-30), next_step=nxt), "scheduled")

    def test_t12_passed_next_step_is_stalled_and_mentioned(self):
        passed = day(-1)
        _, _, reason = self.assertCategory(row(last_moved=day(-30), next_step=passed), "stalled")
        self.assertIn(passed, reason)
        self.assertIn("passed", reason)

    def test_t13_invalid_next_step_date_is_data_issue(self):
        for bad in ("next week", "16/11/2026"):
            with self.subTest(value=bad):
                _, _, reason = self.assertCategory(row(last_moved=day(-30), next_step=bad), "data_issue")
                self.assertIn("invalid next step date", reason)

    def test_t16_threshold_is_respected(self):
        r = row(last_moved=day(-10))
        self.assertCategory(r, "stalled", threshold=1)
        self.assertCategory(r, "stalled", threshold=10)
        self.assertCategory(r, "not_stalled", threshold=11)
        self.assertCategory(r, "not_stalled", threshold=30)

    def test_t20_leap_day(self):
        _, days, _ = self.assertCategory(
            row(last_moved="2028-02-22"), "stalled", as_of=datetime.date(2028, 2, 29))
        self.assertEqual(days, 7)


class TestPrioritize(Base):
    def ids(self, items):
        return [i["candidate_id"] for i in sa.prioritize(items)]

    def test_t14_days_beat_stage(self):
        items = [{"candidate_id": "C001", "stage": "Offer", "days": 9},
                 {"candidate_id": "C002", "stage": "Applied", "days": 10}]
        self.assertEqual(self.ids(items), ["C002", "C001"])

    def test_t15_tie_breaks_later_stage_then_id(self):
        same_days = [{"candidate_id": "C001", "stage": "Applied", "days": 9},
                     {"candidate_id": "C002", "stage": "Offer", "days": 9}]
        self.assertEqual(self.ids(same_days), ["C002", "C001"])
        same_stage = [{"candidate_id": "C010", "stage": "Interview", "days": 9},
                      {"candidate_id": "C002", "stage": "Interview", "days": 9}]
        self.assertEqual(self.ids(same_stage), ["C002", "C010"])


class TestMainAndLoading(Base):
    def test_t17_structural_failures_exit_2(self):
        good = HEADER + "\nC001,A,R,Interview,2026-11-01,,X\n"
        as_of = ["--as-of", AS_OF.isoformat()]
        cases = {
            "missing column": [self.write_csv(good.replace(",stage", ",phase"))] + as_of,
            "duplicate id": [self.write_csv(good + "C001,B,R,Offer,2026-11-02,,X\n")] + as_of,
            "days zero": [self.write_csv(good), "--days", "0"] + as_of,
            "bad as-of": [self.write_csv(good), "--as-of", "16/11/2026"],
            "file not found": [os.path.join(tempfile.gettempdir(), "no_such_board_x9.csv")] + as_of,
        }
        for name, argv in cases.items():
            with self.subTest(case=name):
                code, _, err = run_main(argv)
                self.assertEqual(code, 2)
                self.assertTrue(err.strip(), "expected a message on stderr")

    def test_t18_header_only_file_is_valid(self):
        code, out, _ = run_main([self.write_csv(HEADER + "\n"), "--as-of", AS_OF.isoformat()])
        self.assertEqual(code, 0)
        self.assertIn("FOLLOW UP FIRST (0)", out)

    def test_t19_utf8_bom_loads_normally(self):
        path = self.write_csv(HEADER + "\nC001,A,R,Interview,2026-11-01,,X\n", encoding="utf-8-sig")
        rows = sa.load_rows(path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["candidate_id"], "C001")
        code, _, _ = run_main([path, "--as-of", AS_OF.isoformat()])
        self.assertEqual(code, 0)


class TestReviewRegressions(Base):
    """R1-R5: issues found in the independent code review of commit 5366e9f."""

    def test_r1_only_strict_yyyy_mm_dd_dates_accepted(self):
        # Python 3.11+ fromisoformat reads both of these as valid dates.
        for bad in ("2026-W47-3", "20261109"):
            with self.subTest(last_moved=bad):
                _, _, reason = self.assertCategory(row(last_moved=bad), "data_issue")
                self.assertIn("invalid date", reason)
            with self.subTest(next_step=bad):
                _, _, reason = self.assertCategory(row(last_moved=day(-30), next_step=bad), "data_issue")
                self.assertIn("invalid next step date", reason)
        # Simulate a fully permissive parser so the format guard is proven on any
        # Python version, including 3.9 where fromisoformat already rejects these.
        permissive = types.SimpleNamespace(date=types.SimpleNamespace(
            fromisoformat=lambda s: datetime.date(2026, 11, 9)))
        with mock.patch.object(sa, "datetime", permissive):
            for bad in ("2026-W47-3", "20261109", "2026/11/09", "2026-11-0x"):
                with self.subTest(permissive_parser=bad):
                    self.assertIsNone(sa.parse_iso_date(bad))
            self.assertEqual(sa.parse_iso_date("2026-11-09"), datetime.date(2026, 11, 9))

    def assertStructuralError(self, text, expected_message):
        code, out, err = run_main([self.write_csv(text), "--as-of", AS_OF.isoformat()])
        self.assertEqual(code, 2)
        self.assertIn(expected_message, err)
        self.assertEqual(out, "", "no report may be printed for a malformed file")

    def test_r2_duplicate_column_names_rejected(self):
        self.assertStructuralError(HEADER + ",stage\nC001,A,R,Interview,2026-11-01,,X,Offer\n",
                                   "duplicate column name(s): stage")

    def test_r3_row_with_more_fields_than_header_rejected(self):
        self.assertStructuralError(HEADER + "\nC001,A,R,Interview,2026-11-01,,X,EXTRA\n",
                                   "line 2: more fields")

    def test_r4_row_with_fewer_fields_than_header_rejected(self):
        self.assertStructuralError(HEADER + "\nC001,A,R,Interview,2026-11-01,,X\nC002,B,R,Offer,2026-11-01\n",
                                   "line 3: fewer fields")

    def test_r5_blank_candidate_id_is_data_issue_not_follow_up(self):
        for cid in ("", "   "):
            with self.subTest(candidate_id=repr(cid)):
                _, _, reason = self.assertCategory(row(cid=cid, last_moved=day(-30)), "data_issue")
                self.assertIn("missing candidate_id", reason)
        text = (HEADER + "\n,A,R,Interview,2026-10-01,,X\n  ,B,R,Offer,2026-10-02,,X\n"
                "C003,C,R,Offer,2026-10-03,,X\n")
        code, out, _ = run_main([self.write_csv(text), "--as-of", AS_OF.isoformat()])
        self.assertEqual(code, 0, "two blank IDs must not be reported as duplicates")
        self.assertIn("FOLLOW UP FIRST (1)", out)
        self.assertIn(" 1. C003", out)
        self.assertIn("NEEDS A DATA FIX (2)", out)
        self.assertEqual(out.count("(blank id)"), 2)


if __name__ == "__main__":
    unittest.main()

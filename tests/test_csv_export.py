"""Tests X1-X15 for the optional CSV export (--output / --out).

POST-SUBMISSION IMPROVEMENT. These tests are not part of the original Quest 1
submission. The specification is docs/CSV_EXPORT_ARCHITECTURE.md, section 7.

Written BEFORE the export code exists. At that point every test that uses the
option must fail (argparse does not know it yet) and X5 must pass, because X5
describes the behaviour of the tool without the option.

Tests that expect a refusal (exit code 2) also check the wording of the message
or that stderr is one clean line. Without that, argparse's own "unrecognized
arguments" exit 2 would make them pass before the feature exists.

Run from the repo root:  python3 -m unittest discover -s tests -v
"""
import contextlib
import csv
import datetime
import hashlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import stall_alerter as sa  # noqa: E402

BOARD = os.path.join(ROOT, "data", "hiring_board.csv")
GOLDEN = os.path.join(ROOT, "data", "expected_followup_2026-11-16.csv")
AS_OF = datetime.date(2026, 11, 16)
AS_OF_ARGS = ["--as-of", AS_OF.isoformat()]
OPTIONS = ("--output", "--out")

INPUT_HEADER = ["candidate_id", "candidate_name", "role", "stage",
                "last_moved_date", "next_step_date", "recruiter"]
EXPORT_HEADER = ["Priority", "Candidate ID", "Candidate name", "Role", "Hiring stage",
                 "Days waiting", "Status", "Recruiter", "Next step date",
                 "Action / explanation", "As of", "Threshold (days)"]
(PRIORITY, CID, NAME, ROLE, STAGE, DAYS, STATUS, RECRUITER, NEXT_STEP, ACTION, AS_OF_COL,
 THRESHOLD) = range(12)
STATUS_ORDER = ["Follow up first", "Needs a data fix", "Scheduled", "Not stalled", "Closed"]

# Observed on 2026-11-19 at the baseline commit 12572eb (architecture section 8.1).
# Do not edit these to make a test pass.
BASELINE_STDOUT_SHA256 = {
    7: "58c1769d00892cd6db3ab7670b486b91399de8ed46f14f31b3a4f891ae00da50",
    6: "102e4859d2956659e82ce945c1fd7fa73bf5be8a160dafd98a59dfe9a351c30f",
    10: "bc35b6d6b88eac05d8a1c61265daf6e728fa143d36be40285ab905e4e38cfd6f",
}
EXPECTED_ORDER = {
    7: ["C017", "C028", "C004", "C011", "C023"],
    6: ["C017", "C028", "C004", "C011", "C023", "C019", "C002"],
    10: ["C017", "C028", "C004"],
}
FORMULA_TRIGGERS = ("=", "+", "-", "@", "\t", "\r")


def run_main(argv):
    """Call main(argv); return (exit_code, stdout, stderr). argparse exits count as codes."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = sa.main(argv)
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), err.getvalue()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def read_export(path):
    """Parse a report the way a spreadsheet import would: UTF-8, BOM tolerated."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f))


def board_row(cid, name="Test Person", role="Test Role", stage="Interview",
              moved="2026-11-01", next_step="", recruiter="Tester"):
    return [cid, name, role, stage, moved, next_step, recruiter]


class Base(unittest.TestCase):
    def tmp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        return folder.name

    def chdir(self, folder):
        previous = os.getcwd()
        os.chdir(folder)
        self.addCleanup(os.chdir, previous)

    def write_board(self, rows, header=INPUT_HEADER):
        path = os.path.join(self.tmp(), "board.csv")
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(header)
            writer.writerows(rows)
        return path

    def write_raw_board(self, data):
        path = os.path.join(self.tmp(), "board.csv")
        with open(path, "wb") as f:
            f.write(data)
        return path

    def copy_of_sample_board(self):
        path = os.path.join(self.tmp(), "board.csv")
        shutil.copyfile(BOARD, path)
        return path

    def export(self, board, *extra, option="--output", out=None):
        """Run the tool with the export option. Returns (code, stdout, stderr, out_path)."""
        if out is None:
            out = os.path.join(self.tmp(), "followup.csv")
        code, stdout, stderr = run_main([board] + AS_OF_ARGS + list(extra) + [option, out])
        return code, stdout, stderr, out

    def symlink_or_skip(self, target, link):
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError, AttributeError):
            self.skipTest("symlinks are not available here")

    @contextlib.contextmanager
    def assertUnchanged(self, path):
        """X7: the file has the same SHA-256 before and after the block."""
        before = sha256_bytes(read_bytes(path))
        yield
        self.assertEqual(sha256_bytes(read_bytes(path)), before, f"{path} was modified")

    def assertRefused(self, result, fragment):
        """Exit 2, nothing on stdout, exactly one clean line on stderr with the reason."""
        code, stdout, stderr = result[0], result[1], result[2]
        self.assertEqual(code, 2, stderr)
        self.assertEqual(stdout, "", "no report may be printed when the run is refused")
        self.assertNotIn("Traceback", stderr)
        lines = stderr.splitlines()
        self.assertEqual(len(lines), 1, f"expected one message line on stderr, got: {stderr!r}")
        self.assertTrue(lines[0].startswith("error: "), stderr)
        self.assertIn(fragment, lines[0])


class TestExportContent(Base):
    def setUp(self):
        self.code, self.stdout, self.stderr, self.out = self.export(BOARD, "--days", "7")
        self.assertEqual(self.code, 0, self.stderr)
        self.rows = read_export(self.out)

    def test_x01_golden_export_matches(self):
        with open(GOLDEN, encoding="utf-8-sig", newline="") as f:
            golden = list(csv.reader(f))
        self.assertEqual(len(golden), 31)
        self.assertEqual(self.rows, golden)

    def test_x02_file_format(self):
        data = read_bytes(self.out)
        self.assertEqual(data[:3], b"\xef\xbb\xbf", "file must start with the UTF-8 BOM")
        self.assertTrue(data.endswith(b"\r\n"))
        self.assertEqual(data.count(b"\r\n"), 31, "31 lines, each ending with CRLF")
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""), "a line ends with LF only")
        self.assertNotIn(b"\r", data.replace(b"\r\n", b""), "a line ends with CR only")
        self.assertEqual(self.rows[0], EXPORT_HEADER)
        self.assertEqual(len(self.rows), 31)
        self.assertEqual({len(r) for r in self.rows}, {12})
        with open(BOARD, encoding="utf-8-sig", newline="") as f:
            board_ids = [r["candidate_id"] for r in csv.DictReader(f)]
        self.assertEqual(len(board_ids), 30)
        self.assertEqual(sorted(r[CID] for r in self.rows[1:]), sorted(board_ids))

    def test_x03_ordering(self):
        body = self.rows[1:]
        self.assertEqual([r[PRIORITY] for r in body[:5]], ["1", "2", "3", "4", "5"])
        self.assertEqual([r[CID] for r in body[:5]], EXPECTED_ORDER[7])
        self.assertEqual({r[PRIORITY] for r in body[5:]}, {""})
        expected_statuses = (["Follow up first"] * 5 + ["Needs a data fix"] * 3 +
                             ["Scheduled"] * 2 + ["Not stalled"] * 14 + ["Closed"] * 6)
        self.assertEqual([r[STATUS] for r in body], expected_statuses)
        with open(BOARD, encoding="utf-8-sig", newline="") as f:
            position = {r["candidate_id"]: i for i, r in enumerate(csv.DictReader(f))}
        for status in STATUS_ORDER[1:]:
            with self.subTest(status=status):
                places = [position[r[CID]] for r in body if r[STATUS] == status]
                self.assertEqual(places, sorted(places), "group is not in input file order")

    def test_x04_values(self):
        body = self.rows[1:]
        by_id = {r[CID]: r for r in body}
        self.assertEqual([r[DAYS] for r in body[:5]], ["21", "14", "14", "9", "7"])
        self.assertEqual(by_id["C011"][NEXT_STEP], "2026-11-12")
        self.assertIn("2026-11-12", by_id["C011"][ACTION])
        self.assertIn("passed", by_id["C011"][ACTION])
        for cid, next_step, days in (("C006", "2026-11-18", "13"), ("C020", "2026-11-16", "10")):
            with self.subTest(candidate=cid):
                self.assertEqual(by_id[cid][STATUS], "Scheduled")
                self.assertEqual(by_id[cid][NEXT_STEP], next_step)
                self.assertEqual(by_id[cid][DAYS], days)
        for cid, why in (("C009", "missing date"), ("C014", "invalid date"),
                         ("C026", "future date")):
            with self.subTest(candidate=cid):
                self.assertEqual(by_id[cid][STATUS], "Needs a data fix")
                self.assertEqual(by_id[cid][DAYS], "")
                self.assertIn(why, by_id[cid][ACTION])
        self.assertEqual({r[AS_OF_COL] for r in body}, {"2026-11-16"})
        self.assertEqual({r[THRESHOLD] for r in body}, {"7"})

    def test_x07_input_unchanged_by_successful_export(self):
        board = self.copy_of_sample_board()
        with self.assertUnchanged(board):
            code, _, stderr, out = self.export(board)
        self.assertEqual(code, 0, stderr)
        self.assertTrue(os.path.isfile(out))


class TestExportEdgeRows(Base):
    def test_x04_edge_rows_blank_id_unknown_stage_unreadable_next_step(self):
        board = self.write_board([
            board_row("", name="No Id Person"),
            board_row("C002", name="Hold Person", stage="On Hold"),
            board_row("C003", name="Next Week Person", next_step="next week"),
        ])
        code, _, stderr, out = self.export(board)
        self.assertEqual(code, 0, stderr)
        rows = read_export(out)
        self.assertEqual(len(rows), 4)
        by_name = {r[NAME]: r for r in rows[1:]}
        self.assertEqual({r[STATUS] for r in rows[1:]}, {"Needs a data fix"})
        self.assertEqual(by_name["No Id Person"][CID], "")
        self.assertIn("missing candidate_id", by_name["No Id Person"][ACTION])
        self.assertEqual(by_name["Hold Person"][STAGE], "On Hold")
        self.assertEqual(by_name["Next Week Person"][NEXT_STEP], "next week")
        self.assertEqual(by_name["Next Week Person"][DAYS], "")

    def test_x15_header_only_board(self):
        board = self.write_board([])
        code, stdout, stderr, out = self.export(board)
        self.assertEqual(code, 0, stderr)
        self.assertEqual(read_export(out), [EXPORT_HEADER])
        self.assertIn("FOLLOW UP FIRST (0)", stdout)
        self.assertIn("(0 rows)", stderr)


class TestTerminalBehaviourPreserved(Base):
    def test_x05_without_option_output_is_the_baseline_and_no_file_is_created(self):
        folder = self.tmp()
        self.chdir(folder)
        for days, expected in BASELINE_STDOUT_SHA256.items():
            with self.subTest(days=days):
                code, stdout, stderr = run_main([BOARD] + AS_OF_ARGS + ["--days", str(days)])
                self.assertEqual(code, 0)
                self.assertEqual(sha256_bytes(stdout.encode("utf-8")), expected)
                self.assertEqual(stderr, "")
                self.assertEqual(os.listdir(folder), [], "a run without the option created a file")

    def test_x06_with_option_terminal_unchanged_for_both_spellings(self):
        _, plain_stdout, _ = run_main([BOARD] + AS_OF_ARGS)
        files = []
        for option in OPTIONS:
            with self.subTest(option=option):
                code, stdout, stderr, out = self.export(BOARD, option=option)
                self.assertEqual(code, 0, stderr)
                self.assertEqual(stdout, plain_stdout)
                self.assertEqual(stderr, f"CSV report written: {out} (30 rows)\n")
                files.append(read_bytes(out))
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0], files[1], "--output and --out wrote different files")

    def test_x14_reproducible_and_threshold_respected(self):
        first = read_bytes(self.export(BOARD, "--days", "7")[3])
        second = read_bytes(self.export(BOARD, "--days", "7")[3])
        self.assertEqual(first, second, "two exports with equal arguments differ")
        for days in (6, 10):
            with self.subTest(days=days):
                code, _, stderr, out = self.export(BOARD, "--days", str(days))
                self.assertEqual(code, 0, stderr)
                body = read_export(out)[1:]
                self.assertEqual(len(body), 30)
                ranked = [r for r in body if r[PRIORITY]]
                self.assertEqual([r[CID] for r in ranked], EXPECTED_ORDER[days])
                self.assertEqual([r[PRIORITY] for r in ranked],
                                 [str(n) for n in range(1, len(ranked) + 1)])
                self.assertEqual(body[:len(ranked)], ranked, "priority rows are not first")
                self.assertEqual({r[THRESHOLD] for r in body}, {str(days)})


class TestOutputPathRefusals(Base):
    def test_x08_output_onto_the_input_is_refused(self):
        for option in OPTIONS:
            board = self.copy_of_sample_board()
            with self.subTest(option=option, case="same path"):
                with self.assertUnchanged(board):
                    result = self.export(board, option=option, out=board)
                self.assertRefused(result, "refusing to write the report over the input file")
            with self.subTest(option=option, case="relative input, absolute output"):
                self.chdir(os.path.dirname(board))
                with self.assertUnchanged(board):
                    result = self.export("board.csv", option=option, out=board)
                self.assertRefused(result, "refusing to write the report over the input file")
            with self.subTest(option=option, case="absolute input, relative output"):
                with self.assertUnchanged(board):
                    result = self.export(board, option=option, out="board.csv")
                self.assertRefused(result, "refusing to write the report over the input file")

    def test_x08c_output_symlink_to_the_input_is_refused(self):
        board = self.copy_of_sample_board()
        link = os.path.join(os.path.dirname(board), "link.csv")
        self.symlink_or_skip(board, link)
        for option in OPTIONS:
            with self.subTest(option=option):
                with self.assertUnchanged(board):
                    result = self.export(board, option=option, out=link)
                self.assertRefused(result, "refusing to write the report over the input file")
                self.assertTrue(os.path.islink(link))

    def test_x09_existing_file_is_not_overwritten(self):
        board = self.copy_of_sample_board()
        existing = os.path.join(self.tmp(), "report.csv")
        with open(existing, "wb") as f:
            f.write(b"keep me\n")
        with self.assertUnchanged(board):
            result = self.export(board, out=existing)
        self.assertRefused(result, "already exists")
        self.assertEqual(read_bytes(existing), b"keep me\n")

    def test_x09b_existing_directory_is_refused(self):
        board = self.copy_of_sample_board()
        folder = os.path.join(self.tmp(), "report.csv")
        os.mkdir(folder)
        with self.assertUnchanged(board):
            result = self.export(board, out=folder)
        self.assertRefused(result, "already exists")
        self.assertTrue(os.path.isdir(folder))
        self.assertEqual(os.listdir(folder), [])

    def test_x09c_broken_symlink_is_refused(self):
        board = self.copy_of_sample_board()
        folder = self.tmp()
        target = os.path.join(folder, "not_there.csv")
        link = os.path.join(folder, "report.csv")
        self.symlink_or_skip(target, link)
        with self.assertUnchanged(board):
            result = self.export(board, out=link)
        self.assertRefused(result, "already exists")
        self.assertTrue(os.path.islink(link))
        self.assertFalse(os.path.exists(target), "the tool wrote through a broken symlink")

    def test_x09d_empty_output_name_is_refused(self):
        board = self.copy_of_sample_board()
        folder = self.tmp()
        self.chdir(folder)
        for option in OPTIONS:
            with self.subTest(option=option):
                with self.assertUnchanged(board):
                    result = self.export(board, option=option, out="")
                self.assertRefused(result, "--output needs a file name")
                self.assertEqual(os.listdir(folder), [])


class TestFailuresLeaveNothingBehind(Base):
    def test_x10_malformed_input_creates_no_report(self):
        good = "candidate_id,candidate_name,role,stage,last_moved_date,next_step_date,recruiter\n" \
               "C001,A,R,Interview,2026-11-01,,X\n"
        cases = {
            "duplicate column": good.replace("recruiter\n", "recruiter,stage\n")
                                    .replace(",X\n", ",X,Offer\n").encode(),
            "row with more fields": good.replace(",X\n", ",X,EXTRA\n").encode(),
            "row with fewer fields": (good + "C002,B,R,Offer,2026-11-01\n").encode(),
            "duplicate candidate_id": (good + "C001,B,R,Offer,2026-11-02,,X\n").encode(),
            "missing required column": good.replace(",stage,", ",phase,").encode(),
            "invalid UTF-8 byte": good.encode().replace(b",A,", b",\xff,"),
        }
        for name, data in cases.items():
            with self.subTest(case=name):
                board = self.write_raw_board(data)
                with self.assertUnchanged(board):
                    result = self.export(board)
                self.assertRefused(result, "cannot read")
                self.assertFalse(os.path.lexists(result[3]), "a report file was left behind")
        with self.subTest(case="input file not found"):
            missing = os.path.join(self.tmp(), "no_such_board.csv")
            result = self.export(missing)
            self.assertRefused(result, "cannot read")
            self.assertFalse(os.path.lexists(result[3]))
            self.assertFalse(os.path.lexists(missing))

    def test_x13a_missing_parent_folder(self):
        board = self.copy_of_sample_board()
        parent = os.path.join(self.tmp(), "missing_folder")
        with self.assertUnchanged(board):
            result = self.export(board, out=os.path.join(parent, "report.csv"))
        self.assertRefused(result, "cannot write")
        self.assertFalse(os.path.lexists(parent), "the tool created a folder")

    def test_x13b_read_only_folder(self):
        if os.name == "nt" or not hasattr(os, "geteuid") or os.geteuid() == 0:
            self.skipTest("folder permissions do not stop this user")
        board = self.copy_of_sample_board()
        folder = os.path.join(self.tmp(), "read_only")
        os.mkdir(folder)
        os.chmod(folder, 0o555)
        self.addCleanup(os.chmod, folder, 0o755)
        if os.access(folder, os.W_OK):
            self.skipTest("folder permissions do not stop this user")
        with self.assertUnchanged(board):
            result = self.export(board, out=os.path.join(folder, "report.csv"))
        self.assertRefused(result, "cannot write")
        self.assertEqual(os.listdir(folder), [])

    def test_x13c_write_failure_after_creation_removes_the_new_file(self):
        board = self.copy_of_sample_board()
        real_open = open
        created = []

        class FailingFile:
            def __init__(self, handle):
                self.handle = handle

            def write(self, text):
                raise OSError(28, "No space left on device")

            def close(self):
                self.handle.close()

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                self.handle.close()
                return False

        def fake_open(file, mode="r", *args, **kwargs):
            if "x" in mode:  # the report file: really create it, then fail on write
                handle = real_open(file, mode, *args, **kwargs)
                created.append(file)
                return FailingFile(handle)
            return real_open(file, mode, *args, **kwargs)

        out = os.path.join(self.tmp(), "report.csv")
        with mock.patch.object(sa, "open", fake_open, create=True):
            with self.assertUnchanged(board):
                result = self.export(board, out=out)
        self.assertRefused(result, "cannot write")
        self.assertEqual(created, [out], "the report file was never created, so nothing was proven")
        self.assertFalse(os.path.lexists(out), "a partial report file was left behind")


class TestHostileContent(Base):
    def test_x11_formula_injection_is_neutralised(self):
        payloads = ['=HYPERLINK("http://x","y")', "+1+1", "-2+3", "@SUM(A1)", "\t=1", "   =1"]
        fields = {"candidate_id": CID, "candidate_name": NAME, "role": ROLE, "stage": STAGE,
                  "next_step_date": NEXT_STEP, "recruiter": RECRUITER}
        rows, expected = [], []
        for field in fields:
            for payload in payloads:
                n = len(rows) + 1
                marker_id, marker_name = f"C{n:03d}", f"Person {n:03d}"
                value = payload
                if field == "candidate_id" and payload == "   =1":
                    value = "   =2"  # IDs must stay unique once surrounding spaces are stripped
                row = dict(zip(INPUT_HEADER, board_row(marker_id, name=marker_name)))
                row[field] = value
                rows.append([row[h] for h in INPUT_HEADER])
                find_by = (NAME, marker_name) if field == "candidate_id" else (CID, marker_id)
                expected.append((field, value, find_by))
        code, _, stderr, out = self.export(self.write_board(rows))
        self.assertEqual(code, 0, stderr)
        parsed = read_export(out)
        self.assertEqual(len(parsed), len(rows) + 1)
        self.assertEqual({len(r) for r in parsed}, {12})
        for r in parsed:
            for cell in r:
                self.assertFalse(cell.startswith(FORMULA_TRIGGERS),
                                 f"cell can run as a formula: {cell!r}")
        for field, value, (column, marker) in expected:
            with self.subTest(field=field, value=value):
                matches = [r for r in parsed[1:] if r[column] == marker]
                self.assertEqual(len(matches), 1)
                self.assertEqual(matches[0][fields[field]], "'" + value.strip())
        for r in parsed[1:]:
            self.assertRegex(r[PRIORITY], r"^\d*$")
            self.assertRegex(r[DAYS], r"^\d*$")
            self.assertEqual(r[THRESHOLD], "7")
            self.assertEqual(r[AS_OF_COL], "2026-11-16")

    def test_x12_commas_quotes_line_breaks_and_escape_codes(self):
        hostile = 'Eve "Quote", Comma\nSecond line\x1b[31mRED'
        board = self.write_board([
            board_row("C001", name=hostile),
            board_row("C002", name="Plain Person", stage="Hired"),
            board_row("C003", name="Other Person", moved="2026-11-15"),
        ])
        code, _, stderr, out = self.export(board)
        self.assertEqual(code, 0, stderr)
        parsed = read_export(out)
        self.assertEqual(len(parsed), 4)
        self.assertEqual({len(r) for r in parsed}, {12})
        by_id = {r[CID]: r for r in parsed[1:]}
        self.assertEqual(by_id["C001"][NAME], 'Eve "Quote", Comma?Second line?[31mRED')
        text = read_bytes(out).decode("utf-8-sig")
        self.assertEqual(text.count("\r\n"), 4, "a line break inside a cell reached the file")
        leftovers = [ch for ch in text.replace("\r\n", "") if not ch.isprintable()]
        self.assertEqual(leftovers, [], "raw control characters in the report")



# ---------------------------------------------------------------------------
# S1-S10: regression tests added after the independent review of the export
# (verdict: approve with changes). Written before the corrections. References:
# OWASP "CSV Injection" and OWASP ASVS 5.0 requirement 1.2.10.

# OWASP list: = + - @, tab, carriage return, line feed, and the full-width forms.
ALL_TRIGGERS = ("=", "+", "-", "@", "\t", "\r", "\n", "＝", "＋", "－", "＠")
USER_FIELDS = ("candidate_id", "candidate_name", "role", "stage", "last_moved_date",
               "next_step_date", "recruiter")


def cells_if_split_on_semicolon(path):
    """Every cell a spreadsheet would see if it split this file on semicolons.

    Two readings are combined, because programs differ in how they treat quotes:
    a plain split on ';', and a CSV parse with ';' as the delimiter. Leading
    spaces and double quotes are dropped from each cell before it is judged, so
    the check does not depend on how a program trims or unquotes a cell.
    """
    text = read_bytes(path).decode("utf-8-sig")
    cells = []
    for line in text.split("\r\n"):
        cells.extend(line.split(";"))
    for row in csv.reader(io.StringIO(text, newline=""), delimiter=";"):
        cells.extend(row)
    return [cell.lstrip(' " 　') for cell in cells]


class TestReviewHardening(Base):
    def hostile_board(self, payloads):
        """One row per (user-controlled field, payload). Returns (path, [(field, payload, id)])."""
        rows, placed = [], []
        for field in USER_FIELDS:
            for payload in payloads:
                n = len(rows) + 1
                row = dict(zip(INPUT_HEADER, board_row(f"C{n:03d}", name=f"Person {n:03d}")))
                row[field] = payload
                rows.append([row[h] for h in INPUT_HEADER])
                placed.append((field, payload, f"Person {n:03d}" if field == "candidate_id"
                               else f"C{n:03d}"))
        return self.write_board(rows), placed

    def assertNoFormulaCells(self, out):
        parsed = read_export(out)
        self.assertEqual({len(r) for r in parsed}, {12})
        for r in parsed:
            for cell in r:
                self.assertFalse(cell.startswith(ALL_TRIGGERS),
                                 f"comma-separated reading: cell can run as a formula: {cell!r}")
        for cell in cells_if_split_on_semicolon(out):
            self.assertFalse(cell.startswith(ALL_TRIGGERS),
                             f"semicolon-separated reading: cell can run as a formula: {cell!r}")
        return parsed

    def test_s01_semicolon_separator_cannot_start_a_formula(self):
        payloads = ["x;=1+1;", "x;+1+1", "x;-2+3", "x;@SUM(A1)", "x; =1+1", 'x;"=1+1',
                    "a,b;=1+1", "x;;=1+1", ";=1+1", "x;＝1+1", 'x;" =1+1', "x;=1;=2"]
        board, placed = self.hostile_board(payloads)
        code, _, stderr, out = self.export(board)
        self.assertEqual(code, 0, stderr)
        parsed = self.assertNoFormulaCells(out)
        self.assertEqual(len(parsed), len(placed) + 1, "a row was lost or split")
        # The text typed in stage and in both date columns is repeated in the
        # Action / explanation column: prove it arrived there and was checked.
        wording = {"stage": "unknown stage", "last_moved_date": "invalid date",
                   "next_step_date": "invalid next step date"}
        by_id = {r[CID]: r for r in parsed[1:]}
        for field, payload, marker in placed:
            if field in wording:
                with self.subTest(field=field, payload=payload):
                    action = by_id[marker][ACTION]
                    self.assertIn(wording[field], action)
                    self.assertIn("x" if payload.startswith("x") else payload[:1], action)
                    for part in action.split(";")[1:]:
                        self.assertFalse(part.lstrip(' "').startswith(ALL_TRIGGERS), action)

    def test_s02_harmless_semicolons_and_quotes_are_kept_as_typed(self):
        values = ["Smith; Jones", "a;b", "x;1", "x;", ";", '"', 'a"b', ",", 'a,"b";c',
                  "O'Neil", "x;y=1", "x; y-1"]
        rows = [board_row(f"C{n:03d}", name=v) for n, v in enumerate(values, 1)]
        code, _, stderr, out = self.export(self.write_board(rows))
        self.assertEqual(code, 0, stderr)
        parsed = self.assertNoFormulaCells(out)
        by_id = {r[CID]: r for r in parsed[1:]}
        for n, value in enumerate(values, 1):
            with self.subTest(value=value):
                self.assertEqual(by_id[f"C{n:03d}"][NAME], value)

    def test_s03_cell_ending_with_semicolon_before_a_guarded_cell(self):
        board = self.write_board([board_row("C001", name="x;", role="=1+1", recruiter="-1")])
        code, _, stderr, out = self.export(board)
        self.assertEqual(code, 0, stderr)
        parsed = self.assertNoFormulaCells(out)
        self.assertEqual(parsed[1][NAME], "x;")
        self.assertEqual(parsed[1][ROLE], "'=1+1")
        self.assertEqual(parsed[1][RECRUITER], "'-1")

    def test_s04_full_width_and_invisible_leading_characters(self):
        guarded = ["＝1+1", "＋1+1", "－2+3", "＠SUM(A1)"]
        trimmed = [" =1+1", "　=1+1", " \t =1+1"]      # spaces of any kind are stripped
        replaced = ["​=1+1", "﻿=1+1", "\x1b=1+1"]     # invisible characters become "?"
        values = guarded + trimmed + replaced
        rows = [board_row(f"C{n:03d}", name=v) for n, v in enumerate(values, 1)]
        code, _, stderr, out = self.export(self.write_board(rows))
        self.assertEqual(code, 0, stderr)
        parsed = self.assertNoFormulaCells(out)
        names = [r[NAME] for r in sorted(parsed[1:], key=lambda r: r[CID])]
        self.assertEqual(names[:4], ["'" + v for v in guarded])
        self.assertEqual(names[4:7], ["'=1+1"] * 3)
        self.assertEqual(names[7:], ["?=1+1"] * 3)

    def test_s05_hostile_action_explanation_values(self):
        # (a) A line break and an escape code typed into a date reach the explanation.
        board = self.write_board([
            board_row("C001", moved="x\n=1+1"),
            board_row("C002", next_step="y\x1b[2J\r\n@SUM(A1)"),
            board_row("C003", stage="z\t-1+1"),
        ])
        code, _, stderr, out = self.export(board)
        self.assertEqual(code, 0, stderr)
        parsed = self.assertNoFormulaCells(out)
        self.assertEqual(len(parsed), 4, "a line break in a cell split a row")
        text = read_bytes(out).decode("utf-8-sig")
        self.assertEqual([ch for ch in text.replace("\r\n", "") if not ch.isprintable()], [])
        by_id = {r[CID]: r for r in parsed[1:]}
        self.assertIn("invalid date", by_id["C001"][ACTION])
        self.assertIn("invalid next step date", by_id["C002"][ACTION])
        self.assertIn("unknown stage", by_id["C003"][ACTION])
        # (b) Today every explanation starts with the tool's own words. If that wording
        # ever changes, the explanation must still be guarded like any other text cell.
        for reason, expected in (("=1+1", "'=1+1"), ("  @SUM(A1)", "'@SUM(A1)"),
                                 ("why;=1+1", None), ("＝1", "'＝1")):
            with self.subTest(reason=reason):
                result = dict(zip(INPUT_HEADER, board_row("C001")),
                              category="data_issue", days=None, reason=reason)
                cell = sa.export_table([result], AS_OF, 7)[1][ACTION]
                self.assertFalse(cell.startswith(ALL_TRIGGERS), cell)
                if expected is not None:
                    self.assertEqual(cell, expected)
                for part in cell.split(";")[1:]:
                    self.assertFalse(part.lstrip(' "').startswith(ALL_TRIGGERS), cell)

    def test_s06_stage_label_case_and_whitespace(self):
        cases = [(" OFFER ", "Offer", "Follow up first"), ("hIrEd", "Hired", "Closed"),
                 (" Interview ", "Interview", "Follow up first"),
                 ("screening", "Screening", "Follow up first"),
                 ("WITHDRAWN  ", "Withdrawn", "Closed"),
                 ("  On Hold  ", "On Hold", "Needs a data fix"),
                 ("ON HOLD", "ON HOLD", "Needs a data fix"),
                 ("", "", "Needs a data fix")]
        for typed, label, _ in cases:
            with self.subTest(stage_label=typed):
                self.assertEqual(sa.stage_label(typed), label)
        rows = [board_row(f"C{n:03d}", stage=c[0], moved="2026-10-01")
                for n, c in enumerate(cases, 1)]
        code, _, stderr, out = self.export(self.write_board(rows))
        self.assertEqual(code, 0, stderr)
        by_id = {r[CID]: r for r in read_export(out)[1:]}
        for n, (typed, label, status) in enumerate(cases, 1):
            with self.subTest(exported_stage=typed):
                self.assertEqual(by_id[f"C{n:03d}"][STAGE], label)
                self.assertEqual(by_id[f"C{n:03d}"][STATUS], status)

    def failing_open(self, write_error=None, close_error=None):
        """Patch for the tool's open(): the report file is really created, then its
        write() or close() raises. Returns (patch, list of created paths)."""
        real_open, created = open, []

        class Wrapped:
            def __init__(self, handle):
                self.handle = handle

            def write(self, text):
                if write_error is not None:
                    raise write_error
                return self.handle.write(text)

            def close(self):
                self.handle.close()
                if close_error is not None:
                    raise close_error

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                self.close()
                return False

        def fake_open(file, mode="r", *args, **kwargs):
            handle = real_open(file, mode, *args, **kwargs)
            if "x" in mode:
                created.append(file)
                return Wrapped(handle)
            return handle

        return mock.patch.object(sa, "open", fake_open, create=True), created

    def test_s07_failed_close_removes_the_new_file(self):
        board = self.copy_of_sample_board()
        out = os.path.join(self.tmp(), "report.csv")
        patch, created = self.failing_open(close_error=OSError(5, "Input/output error"))
        with patch, self.assertUnchanged(board):
            result = self.export(board, out=out)
        self.assertRefused(result, "cannot write")
        self.assertEqual(created, [out])
        self.assertFalse(os.path.lexists(out), "a report that failed to close was left behind")

    def test_s08_keyboard_interrupt_during_write_removes_the_new_file(self):
        board = self.copy_of_sample_board()
        out = os.path.join(self.tmp(), "report.csv")
        patch, created = self.failing_open(write_error=KeyboardInterrupt())
        with patch, self.assertUnchanged(board):
            with self.assertRaises(KeyboardInterrupt):  # the interrupt must not be swallowed
                self.export(board, out=out)
        self.assertEqual(created, [out])
        self.assertFalse(os.path.lexists(out), "an interrupted report was left behind")

    def test_s09_hard_link_to_the_input_is_refused(self):
        board = self.copy_of_sample_board()
        link = os.path.join(os.path.dirname(board), "hard_link.csv")
        try:
            os.link(board, link)
        except (OSError, NotImplementedError, AttributeError):
            self.skipTest("hard links are not available here")
        for option in OPTIONS:
            with self.subTest(option=option):
                with self.assertUnchanged(board), self.assertUnchanged(link):
                    result = self.export(board, option=option, out=link)
                self.assertRefused(result, "refusing to write the report over the input file")

    def test_s10_help_text_does_not_claim_read_only(self):
        code, stdout, _ = run_main(["--help"])
        self.assertEqual(code, 0)
        help_text = " ".join(stdout.split())
        self.assertNotIn("Read-only", help_text)
        self.assertIn("never modified", help_text)       # the input board
        self.assertIn("only when", help_text)            # a report only on request
        self.assertIn("no hiring decision", help_text)   # nothing sent, nothing decided


if __name__ == "__main__":
    unittest.main()

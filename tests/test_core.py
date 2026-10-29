import datetime as dt
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from preprint_tracker.cli import main
from preprint_tracker.core import PreprintLog, parse_arxiv_version

FEED = "<feed><entry><id>http://arxiv.org/abs/2401.01234v3</id><title>x</title></entry></feed>"


class LogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "p.json")
        self.log = PreprintLog(self.path, today=dt.date(2026, 1, 10))

    def tearDown(self):
        self.tmp.cleanup()

    def test_versions_and_status(self):
        self.log.add("soil", "Drought and soil microbes", "arXiv", "2401.01234", "2026-01-02")
        self.assertEqual(self.log.new_version("soil", "added second field season"), 2)
        self.log.set_status("soil", "submitted", "Soil Biology Journal")
        again = PreprintLog(self.path, today=dt.date(2026, 6, 1))
        self.assertEqual(again.data["soil"]["status"], "submitted")
        self.assertEqual(again.days_in_status("soil"), 142)
        self.assertEqual(again.needs_attention()[0][0], "soil")

    def test_rules(self):
        self.log.add("a", "A")
        with self.assertRaises(ValueError):
            self.log.add("a", "A again")
        with self.assertRaises(ValueError):
            self.log.new_version("a", " ")
        with self.assertRaises(ValueError):
            self.log.set_status("a", "lost")
        with self.assertRaises(ValueError):
            self.log.set_status("a", "published", doi="")
        self.log.set_status("a", "published", "J", doi="10.1000/xyz")
        self.assertEqual(self.log.data["a"]["published_doi"], "10.1000/xyz")
        with self.assertRaises(KeyError):
            self.log.new_version("zzz", "x")

    def test_remote_check_and_changelog(self):
        self.assertEqual(parse_arxiv_version(FEED), 3)
        self.assertIsNone(parse_arxiv_version("<feed></feed>"))
        self.log.add("p", "Paper", "arXiv", "2401.01234")
        self.assertEqual(self.log.check_remote("p", fetch=lambda i: FEED), (3, 1))
        self.log.add("b", "Bio", "bioRxiv", "10.1101/x")
        with self.assertRaises(ValueError):
            self.log.check_remote("b", fetch=lambda i: FEED)
        self.log.set_status("p", "accepted", "J Good")
        md = self.log.changelog("p")
        self.assertIn("- **v1** (2026-01-10): initial version", md)
        self.assertIn("accepted at J Good", md)

    def test_cli(self):
        with redirect_stdout(io.StringIO()) as buf, redirect_stderr(io.StringIO()):
            main(["--file", self.path, "add", "x", "Title", "--id", "2401.01234"])
            main(["--file", self.path, "version", "x", "fixed typo in eq. 3"])
            self.assertEqual(main(["--file", self.path, "check", "x"], fetch=lambda i: FEED), 1)
        self.assertIn("x is now v2", buf.getvalue())
        self.assertIn("log is behind", buf.getvalue())


if __name__ == "__main__":
    unittest.main()

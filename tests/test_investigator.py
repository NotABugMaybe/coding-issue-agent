import tempfile
import unittest
from pathlib import Path
from issue_agent.search import investigate
from issue_agent.report import render_report
from issue_agent.provider import ReadOnlyTools
from issue_agent.parsing import extract_terms

class InvestigationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / "src").mkdir()
        (self.repo / "src" / "cart.py").write_text("def calculate_total(price):\n    return price\n", encoding="utf-8")
        (self.repo / "src" / "unrelated.py").write_text("def other(): pass\n", encoding="utf-8")
        (self.repo / ".hidden.py").write_text("calculate_total", encoding="utf-8")
        (self.repo / "node_modules").mkdir()
        (self.repo / "node_modules" / "cart.py").write_text("calculate_total", encoding="utf-8")

    def tearDown(self): self.tmp.cleanup()

    def test_ranking_and_line_evidence(self):
        terms, candidates = investigate(self.repo, "calculate_total returns incorrect price")
        self.assertTrue(terms)
        self.assertEqual(candidates[0].path, "src/cart.py")
        self.assertEqual(candidates[0].evidence[0].line, 1)

    def test_path_safety_and_bounded_tools(self):
        tools = ReadOnlyTools(self.repo, max_calls=2)
        with self.assertRaises(ValueError): tools.read_range("../outside.py", 1, 1)
        tools.search("calculate_total")
        with self.assertRaises(ValueError): tools.list_files()

    def test_malformed_issue_terms(self):
        self.assertEqual(extract_terms("!!!"), [])
        self.assertEqual(investigate(self.repo, "!!!")[1], [])

    def test_report_has_evidence_and_cautious_sections(self):
        terms, candidates = investigate(self.repo, "calculate_total returns incorrect price")
        report = render_report(self.repo, "Cart total bug", terms, candidates)
        self.assertIn("src/cart.py:1", report)
        self.assertIn("Uncertainties", report)
        self.assertIn("Proposed regression test", report)

if __name__ == "__main__": unittest.main()

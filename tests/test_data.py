import json
import sqlite3
import unittest

from helpers import DB, HELDOUT, OFFICIAL, QUESTIONS, ROOT

from sql4business.model import BASELINE_TEMPLATE


class DataTests(unittest.TestCase):
    def test_official_set_is_unchanged_from_deliverable_1(self):
        questions = OFFICIAL["questions"]
        self.assertEqual(len(questions), 15)
        self.assertEqual(sum(q["type"] == "combinada" for q in questions), 5)
        conn = sqlite3.connect(DB)
        for question in questions:
            recomputed = [[list(row) for row in conn.execute(sql).fetchall()] for sql in question["gold_sql"]]
            self.assertEqual(recomputed, question["gold_result"], question["id"])

    def test_heldout_paraphrases_share_the_gold_of_their_source(self):
        heldout = HELDOUT["questions"]
        self.assertEqual(len(heldout), 12)
        self.assertEqual(len({q["id"] for q in heldout}), 12)
        for question in heldout:
            source = QUESTIONS[question["source_id"]]
            self.assertEqual(question["gold_result"], source["gold_result"])
            self.assertEqual(question.get("combine"), source.get("combine"))
            self.assertNotEqual(question["question"], source["question"])

    def test_baseline_prompt_is_the_deliverable_1_prompt(self):
        notebook = json.loads((ROOT / "notebooks" / "baseline_eval.ipynb").read_text(encoding="utf-8"))
        source = "".join("".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code")
        start = source.index('PROMPT_TEMPLATE = """') + len('PROMPT_TEMPLATE = """')
        self.assertEqual(source[start : source.index('"""', start)], BASELINE_TEMPLATE)


if __name__ == "__main__":
    unittest.main()

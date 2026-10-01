import unittest

from helpers import DB, QUESTIONS

from sql4business.composition import compose_results
from sql4business.sql_tools import connect_read_only


class CompositionTests(unittest.TestCase):
    def setUp(self):
        self.conn = connect_read_only(DB)

    def tearDown(self):
        self.conn.close()

    def compose(self, operation, *result_sets):
        return compose_results(operation, list(result_sets), conn=self.conn).value

    def test_growth_and_share_take_the_single_number_of_each_step(self):
        growth = self.compose("growth_pct", [("Q1", 100)], [("Q2", 125)])
        self.assertAlmostEqual(growth["growth_pct"], 25.0)
        self.assertEqual(growth["direction"], "increase")
        share = self.compose("share_pct", [(200,)], [(50,)])
        self.assertAlmostEqual(share["share_pct"], 25.0)

    def test_malformed_steps_raise_value_error_so_the_plan_is_repaired(self):
        cases = [
            ("growth_pct", [(1,), (2,)], [(3,)]),          # two rows
            ("growth_pct", [(3, 100)], [(8, 125)]),        # two numbers
            ("share_pct", [(50,)], [(200,)]),              # part larger than total
            ("compare_equal", [(100,)], [(200,)]),         # no name
            ("filter_then_rank", [(6,)], [(1, 99)]),       # no ranked product passes the filter
            ("growth_pct", [(1,)]),                        # one step
        ]
        for operation, *sets in cases:
            with self.assertRaises(ValueError, msg=(operation, sets)):
                self.compose(operation, *sets)

    def test_compare_equal_prefers_product_names_over_other_labels(self):
        value = self.compose("compare_equal", [("2026-Q1", "Notebook 14 pulgadas", 10)], [(20, "Set de Ollas")])
        self.assertEqual(value, {"first": "Notebook 14 pulgadas", "second": "Set de Ollas", "changed": True})

    def test_filter_then_rank_accepts_ids_names_and_unordered_rankings(self):
        filtered = [(6,), (7,), (8,), (9,)]
        by_revenue = self.conn.execute(
            "SELECT p.product_id, p.name, SUM(s.amount) FROM sales s JOIN products p USING(product_id) "
            "GROUP BY p.product_id ORDER BY SUM(s.amount) DESC"
        ).fetchall()
        rankings = {
            "ids with revenue": [(pid, total) for pid, _, total in by_revenue],
            "ids only": [(pid,) for pid, _, _ in by_revenue],
            "name then id, ordered by SQL": [(name, pid) for pid, name, _ in by_revenue],
            "unordered names with revenue": sorted((name, total) for _, name, total in by_revenue),
        }
        for label, ranking in rankings.items():
            self.assertEqual(self.compose("filter_then_rank", filtered, ranking), {"winner": "Zapatillas Urbanas"}, label)

    def test_gold_answers_compose(self):
        self.assertAlmostEqual(self.compose("growth_pct", *QUESTIONS["q09"]["gold_result"])["growth_pct"], 60.1256899, places=5)
        self.assertEqual(self.compose("filter_then_rank", *QUESTIONS["q14"]["gold_result"]), {"winner": "Zapatillas Urbanas"})
        self.assertFalse(self.compose("compare_equal", *QUESTIONS["q10"]["gold_result"])["changed"])


if __name__ == "__main__":
    unittest.main()

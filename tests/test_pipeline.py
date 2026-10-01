import unittest

from helpers import DB, ScriptedGenerator, plan, report

from sql4business.pipeline import AssistantFailure, BusinessAssistant, expand_step_references, validate_plan
from sql4business.sql_tools import connect_read_only, execute_read_only

Q1 = "SELECT SUM(amount) FROM sales WHERE sale_date BETWEEN '2026-03-01' AND '2026-05-31'"
Q2 = "SELECT SUM(amount) FROM sales WHERE sale_date BETWEEN '2026-06-01' AND '2026-08-31'"


class PlanTests(unittest.TestCase):
    def test_plan_contract(self):
        self.assertEqual(len(validate_plan({"steps": [{"sql": "SELECT 1"}, {"sql": "SELECT 2"}], "composition": {"operation": "direct"}})["steps"]), 2)
        for bad in (
            {"steps": [{"sql": Q1}], "composition": {"operation": "growth_pct"}},
            {"steps": [{"sql": Q1}], "composition": {"operation": "average"}},
            {"steps": [], "composition": {"operation": "direct"}},
            {"steps": [{"purpose": "no sql"}], "composition": {"operation": "direct"}},
        ):
            with self.assertRaises(ValueError, msg=bad):
                validate_plan(bad)

    def test_later_steps_can_read_earlier_steps(self):
        steps = [
            {"id": "step_1", "sql": "SELECT product_id FROM inventory WHERE stock < reorder_point"},
            {"id": "step_2", "sql": "SELECT p.product_id, SUM(s.amount) AS total FROM products p JOIN sales s ON p.product_id = s.product_id "
                                     "WHERE p.product_id IN (SELECT product_id FROM step_1) GROUP BY p.product_id ORDER BY total DESC LIMIT 1"},
            {"id": "top", "sql": "WITH t AS (SELECT * FROM step_2) SELECT name FROM products JOIN t USING (product_id)"},
        ]
        conn = connect_read_only(DB)
        try:
            rows = [execute_read_only(conn, sql).rows for sql in expand_step_references(steps)]
        finally:
            conn.close()
        self.assertEqual(rows[1], [(8, 6198450)])
        self.assertEqual(rows[2], [("Zapatillas Urbanas",)])


class AssistantTests(unittest.TestCase):
    def test_combined_question_end_to_end(self):
        generator = ScriptedGenerator(plan(Q1, Q2, operation="growth_pct"), report("Las ventas aumentaron un 60.13%."))
        result = BusinessAssistant(DB, generator).answer("¿Cuánto crecieron las ventas?")
        self.assertAlmostEqual(result.composed.value["growth_pct"], 60.1256899, places=5)
        self.assertEqual(result.report_source, "model")
        self.assertTrue(result.fidelity.faithful, result.fidelity.issues)
        self.assertNotIn("operation hint", generator.prompts[0].lower())

    def test_model_chooses_the_operation_without_a_keyword_veto(self):
        question = "¿Cuánto crecieron, en porcentaje, las ventas de junio a agosto respecto de marzo a mayo?"
        generator = ScriptedGenerator(plan(Q1, Q2, operation="growth_pct"), report("Crecieron un 60.13%."))
        self.assertEqual(BusinessAssistant(DB, generator).answer(question).composed.operation, "growth_pct")

    def test_failed_plan_is_repaired_with_the_error(self):
        generator = ScriptedGenerator(
            plan(Q1, operation="growth_pct"),
            plan(Q1, Q2, operation="growth_pct"),
            report("Las ventas aumentaron un 60.13%."),
        )
        result = BusinessAssistant(DB, generator).answer("¿Cuánto crecieron las ventas?")
        self.assertEqual(len(result.attempts), 2)
        self.assertIn("requires exactly two steps", generator.prompts[1])

    def test_plain_text_reports_are_checked_and_empty_ones_fall_back(self):
        ropa = plan("SELECT COUNT(*) FROM products WHERE category = 'Ropa'")
        for raw, source, faithful in (
            ("La categoría Ropa tiene 2 productos.", "model", True),
            ('```\n"Ropa tiene 3 productos."\n```', "model", False),
            (report("Ropa tiene 2 productos."), "model", True),
            ("   ", "fallback", False),
        ):
            result = BusinessAssistant(DB, ScriptedGenerator(ropa, raw)).answer("¿Cuántos productos tiene Ropa?")
            self.assertEqual((result.report_source, result.fidelity.faithful), (source, faithful), raw)

    def test_failure_keeps_every_attempt(self):
        bad = plan("SELECT SUM(quantity) FROM sales WHERE products.category = 'Alimentos'")
        with self.assertRaises(AssistantFailure) as context:
            BusinessAssistant(DB, ScriptedGenerator(bad, bad, bad)).answer("¿Cuántas unidades de Alimentos?")
        self.assertEqual(len(context.exception.attempts), 3)
        self.assertIn("no such column", context.exception.attempts[-1]["error"])


if __name__ == "__main__":
    unittest.main()

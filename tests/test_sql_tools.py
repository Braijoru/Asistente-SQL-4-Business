import sqlite3
import unittest

from helpers import DB

from sql4business.sql_tools import (
    SQLExecutionError,
    SQLValidationError,
    connect_read_only,
    execute_baseline,
    execute_read_only,
    grounded_schema,
    validate_read_only,
)


class ValidationTests(unittest.TestCase):
    def test_write_statements_are_rejected(self):
        for sql in ("DELETE FROM sales", "REPLACE INTO products VALUES (1, 'a', 'b', 1)", "SELECT 1; DROP TABLE sales"):
            with self.assertRaises(SQLValidationError, msg=sql):
                validate_read_only(sql)

    def test_quoted_text_and_replace_function_are_allowed(self):
        for sql in (
            "SELECT REPLACE(name, ' ', '_') FROM products",
            "SELECT name FROM products WHERE name <> 'Update; now'",
            "```sql\nWITH t AS (SELECT 1 AS x) SELECT x FROM t;\n```",
        ):
            self.assertTrue(validate_read_only(sql).upper().startswith(("SELECT", "WITH")), sql)

    def test_quarter_format_is_rejected_with_a_hint(self):
        with self.assertRaisesRegex(SQLValidationError, "%Q"):
            validate_read_only("SELECT strftime('%Q', sale_date) FROM sales")


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.conn = connect_read_only(DB)

    def tearDown(self):
        self.conn.close()

    def test_connection_is_read_only(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.conn.execute("DELETE FROM sales")

    def test_invented_years_are_rejected_but_wider_ranges_are_not(self):
        with self.assertRaisesRegex(SQLExecutionError, "2023"):
            execute_read_only(self.conn, "SELECT SUM(amount) FROM sales WHERE sale_date >= '2023-07-01'")
        total = execute_read_only(self.conn, "SELECT SUM(amount) FROM sales WHERE sale_date >= '2026-01-01'")
        self.assertEqual(total.rows, [(126807450,)])

    def test_baseline_execution_follows_deliverable_1(self):
        output = "```sql\nSELECT COUNT(*) FROM products; WITH x AS (SELECT 1) SELECT * FROM x; SELECT nope FROM products\n```"
        executions = execute_baseline(self.conn, output)
        self.assertEqual([e.rows for e in executions], [[(10,)], []])
        self.assertIsNone(executions[0].error)
        self.assertIn("no such column", executions[1].error)


class SchemaTests(unittest.TestCase):
    def test_grounded_schema_lists_tables_exact_values_and_dates(self):
        schema = grounded_schema(DB)
        for text in ("CREATE TABLE inventory", "CREATE TABLE products", "CREATE TABLE sales",
                     "'Electronica'", "'Zapatillas Urbanas'", "2026-03-01 to 2026-08-31", "Joins:"):
            self.assertIn(text, schema)


if __name__ == "__main__":
    unittest.main()

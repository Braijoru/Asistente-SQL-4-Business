"""Deterministic composition of SQL results for combined questions.

Every shape problem raises ValueError, so the assistant's retry loop can ask
the planner for a corrected plan instead of silently returning a wrong value.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Any


SUPPORTED_OPERATIONS = ("direct", "growth_pct", "share_pct", "compare_equal", "filter_then_rank")
TWO_STEP_OPERATIONS = SUPPORTED_OPERATIONS[1:]


@dataclass
class ComposedAnswer:
    operation: str
    value: Any
    details: dict[str, Any] = field(default_factory=dict)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _single_number(rows: list[tuple[Any, ...]], role: str) -> float:
    if len(rows) != 1:
        raise ValueError(f"The {role} step must return exactly one row; it returned {len(rows)}.")
    numbers = [value for value in rows[0] if _is_number(value)]
    if len(numbers) != 1:
        raise ValueError(f"The {role} step must return exactly one number; it returned {rows[0]!r}.")
    return float(numbers[0])


class _Products:
    """Resolve product ids, product names and category labels from the database."""

    def __init__(self, conn: sqlite3.Connection):
        rows = conn.execute("SELECT product_id, name, category FROM products").fetchall()
        self.name_by_id = {int(product_id): name for product_id, name, _ in rows}
        self.id_by_name = {name: int(product_id) for product_id, name, _ in rows}
        self.labels = set(self.id_by_name) | {category for _, _, category in rows}

    def resolve(self, value: Any) -> int | None:
        if isinstance(value, str):
            return self.id_by_name.get(value)
        if _is_number(value) and float(value).is_integer() and int(value) in self.name_by_id:
            return int(value)
        return None

    def entity_column(self, rows: list[tuple[Any, ...]]) -> int | None:
        """Index of the first column that identifies a product in every row."""

        width = min(len(row) for row in rows)
        def identifies(i: int, text: bool) -> bool:
            return all(isinstance(r[i], str) == text and self.resolve(r[i]) is not None for r in rows)
        candidates = [i for i in range(width) if identifies(i, True)] or [
            i for i in range(width) if identifies(i, False)
        ]
        return candidates[0] if candidates else None


def _top_label(rows: list[tuple[Any, ...]], role: str, products: _Products | None) -> str:
    """First known product/category name in the first row, else its first text value."""

    if not rows:
        raise ValueError(f"The {role} step returned no rows.")
    labels = [value for value in rows[0] if isinstance(value, str)]
    if products is not None:
        labels = [value for value in labels if value in products.labels] or labels
    if not labels:
        raise ValueError(f"The {role} step must return a name; it returned {rows[0]!r}.")
    return labels[0]


def _filter_then_rank(result_sets: list[list[tuple[Any, ...]]], conn: sqlite3.Connection) -> ComposedAnswer:
    products = _Products(conn)
    filtered_rows, ranking_rows = result_sets
    if not filtered_rows:
        raise ValueError("The filter step returned no rows.")
    if not ranking_rows:
        raise ValueError("The ranking step returned no rows.")

    filter_column = products.entity_column(filtered_rows)
    if filter_column is None:
        raise ValueError("The filter step must return product ids or names.")
    filtered_ids = {products.resolve(row[filter_column]) for row in filtered_rows}

    entity = products.entity_column(ranking_rows)
    if entity is None:
        raise ValueError("The ranking step must return product ids or names.")
    width = min(len(row) for row in ranking_rows)
    metric_columns = [
        i for i in range(width)
        if i != entity
        and products.entity_column([(row[i],) for row in ranking_rows]) is None
        and all(_is_number(row[i]) for row in ranking_rows)
    ]
    ordered = list(ranking_rows)
    if metric_columns:
        # Sort by the metric so an unordered ranking query still yields the maximum.
        ordered.sort(key=lambda row: row[metric_columns[-1]], reverse=True)
    ranked_ids = [products.resolve(row[entity]) for row in ordered]
    winner_id = next((pid for pid in ranked_ids if pid in filtered_ids), None)
    if winner_id is None:
        raise ValueError("No ranked product satisfies the filter; rank all candidate products.")
    return ComposedAnswer(
        "filter_then_rank",
        {"winner": products.name_by_id[winner_id]},
        {
            "filtered": sorted(products.name_by_id[pid] for pid in filtered_ids),
            "ranked": [products.name_by_id[pid] for pid in ranked_ids],
        },
    )


def compose_results(
    operation: str,
    result_sets: list[list[tuple[Any, ...]]],
    conn: sqlite3.Connection | None = None,
) -> ComposedAnswer:
    """Apply a named operation to executed results; the model never calculates."""

    if operation not in SUPPORTED_OPERATIONS:
        raise ValueError(f"Unsupported composition operation: {operation}")
    if not result_sets:
        raise ValueError("At least one SQL result is required.")
    result_sets = [[tuple(row) for row in rows] for rows in result_sets]

    if operation == "direct":
        rows = result_sets[-1]
        value = rows[0][0] if len(rows) == 1 and len(rows[0]) == 1 else [list(row) for row in rows]
        return ComposedAnswer(operation, value)

    if len(result_sets) != 2:
        raise ValueError(f"Operation {operation} requires exactly two steps.")
    first, second = result_sets

    if operation == "growth_pct":
        previous = _single_number(first, "earlier value")
        current = _single_number(second, "later value")
        if previous == 0:
            raise ValueError("Cannot calculate growth from a zero earlier value.")
        growth = (current - previous) / previous * 100
        return ComposedAnswer(
            operation,
            {
                "previous": previous,
                "current": current,
                "growth_pct": growth,
                "direction": "increase" if growth >= 0 else "decrease",
            },
        )

    if operation == "share_pct":
        total = _single_number(first, "total")
        part = _single_number(second, "part")
        if total == 0:
            raise ValueError("Cannot calculate a share of a zero total.")
        if part > total:
            raise ValueError("The part is larger than the total; return the total in the first step.")
        return ComposedAnswer(operation, {"total": total, "subset": part, "share_pct": part / total * 100})

    if operation == "compare_equal":
        products = _Products(conn) if conn is not None else None
        left = _top_label(first, "first group", products)
        right = _top_label(second, "second group", products)
        return ComposedAnswer(operation, {"first": left, "second": right, "changed": left != right})

    if conn is None:
        raise ValueError("filter_then_rank needs a database connection to resolve products.")
    return _filter_then_rank(result_sets, conn)

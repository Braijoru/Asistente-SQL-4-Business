"""Structured assistant: plan, execute read-only SQL, compose deterministically, report."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .composition import SUPPORTED_OPERATIONS, TWO_STEP_OPERATIONS, ComposedAnswer, compose_results
from .fidelity import FidelityCheck, check_report
from .model import TextGenerator, parse_json_object, plan_prompt, report_prompt
from .sql_tools import (
    QueryExecution,
    SQLExecutionError,
    connect_read_only,
    execute_read_only,
    grounded_schema,
    rows_to_json,
    strip_fences,
    strip_literals,
)


IDENTIFIER = re.compile(r"^[A-Za-z_]\w*$")
LEADING_WITH = re.compile(r"^\s*WITH(\s+RECURSIVE)?\s+", re.IGNORECASE)
# Errors caused by the model's plan; they trigger a repair attempt.
PLAN_ERRORS = (ValueError, TypeError, KeyError, IndexError, SQLExecutionError)


@dataclass
class AssistantResult:
    question: str
    plan: dict[str, Any]
    executions: list[QueryExecution]
    composed: ComposedAnswer
    report: str
    report_source: str
    raw_report: str
    fidelity: FidelityCheck
    attempts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "plan": self.plan,
            "executions": [{"sql": e.sql, "rows": rows_to_json(e.rows)} for e in self.executions],
            "composed": {"operation": self.composed.operation, "value": self.composed.value, "details": self.composed.details},
            "report_text": self.report,
            "report_source": self.report_source,
            "raw_report": self.raw_report,
            "report_faithful": self.fidelity.faithful,
            "report_issues": self.fidelity.issues,
            "attempts": self.attempts,
        }


class AssistantFailure(RuntimeError):
    """Every attempt produced an invalid or failing plan."""

    def __init__(self, question: str, attempts: list[dict[str, Any]]):
        self.question = question
        self.attempts = attempts
        super().__init__(f"The assistant failed after {len(attempts)} attempts: {attempts[-1]['error']}")


def validate_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Return the plan in canonical form or raise ValueError with the reason."""

    steps = plan.get("steps")
    composition = plan.get("composition")
    if not isinstance(steps, list) or not steps:
        raise ValueError("The plan must contain at least one step.")
    if not isinstance(composition, dict):
        raise ValueError("The plan must contain a composition object.")
    operation = composition.get("operation")
    if operation not in SUPPORTED_OPERATIONS:
        raise ValueError(f"Unsupported composition operation: {operation!r}.")
    canonical = []
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict) or not isinstance(step.get("sql"), str) or not step["sql"].strip():
            raise ValueError(f"Step {index} must contain SQL text.")
        canonical.append(
            {"id": str(step.get("id") or f"step_{index}"), "purpose": str(step.get("purpose", "")), "sql": step["sql"]}
        )
    if operation in TWO_STEP_OPERATIONS and len(canonical) != 2:
        raise ValueError(f"Operation {operation} requires exactly two steps; the plan has {len(canonical)}.")
    return {"steps": canonical, "operation": operation}


def expand_step_references(steps: list[dict[str, Any]]) -> list[str]:
    """Make each step self-contained by defining the earlier steps it reads as CTEs.

    Steps run on one read-only connection that cannot store results, so
    ``FROM step_1`` in step 2 becomes ``WITH step_1 AS (<step 1 SQL>) ...``.
    """

    expanded: list[str] = []
    for index, step in enumerate(steps):
        sql = strip_fences(step["sql"]).rstrip(";").strip()
        bare = strip_literals(sql)
        tokens = {token.lower() for token in re.findall(r"[A-Za-z_]\w*", bare)}
        definitions = []
        for earlier in range(index):
            names = {f"step_{earlier + 1}", steps[earlier]["id"]}
            for name in sorted(n for n in names if IDENTIFIER.match(n) and n.lower() in tokens):
                if re.search(rf"\b{re.escape(name)}\s+AS\s*\(", bare, re.IGNORECASE):
                    continue  # The step defines this name itself.
                definitions.append(f"{name} AS ({expanded[earlier]})")
        if definitions:
            prefix = LEADING_WITH.match(sql)
            if prefix:
                sql = f"{prefix.group(0)}{', '.join(definitions)}, {sql[prefix.end():]}"
            else:
                sql = f"WITH {', '.join(definitions)} {sql}"
        expanded.append(sql)
    return expanded


def summarize(composed: ComposedAnswer) -> str:
    return "Verified result: " + json.dumps(composed.value, ensure_ascii=False, sort_keys=True)


class BusinessAssistant:
    """Plan, execute, compose and report, with a bounded number of repairs."""

    def __init__(self, db_path: str | Path, generator: TextGenerator, max_retries: int = 2):
        self.db_path = Path(db_path)
        self.generator = generator
        self.max_retries = max(0, max_retries)
        self.schema = grounded_schema(self.db_path)

    def answer(self, question: str) -> AssistantResult:
        attempts: list[dict[str, Any]] = []
        error: str | None = None
        for _ in range(self.max_retries + 1):
            raw_plan = self.generator.generate(plan_prompt(self.schema, question, error))
            try:
                plan = validate_plan(parse_json_object(raw_plan))
                executions, composed = self._execute(plan)
            except PLAN_ERRORS as exc:
                error = f"{exc} Previous plan: {raw_plan[:1500]}"
                attempts.append({"raw_plan": raw_plan, "error": str(exc)})
                continue
            attempts.append({"raw_plan": raw_plan, "error": None})
            report, source, raw_report = self._report(question, plan, executions, composed)
            if source == "model":
                steps = [
                    {"purpose": step["purpose"], "sql": execution.sql, "rows": rows_to_json(execution.rows)}
                    for step, execution in zip(plan["steps"], executions)
                ]
                evidence = question + "\n" + json.dumps(steps, ensure_ascii=False)
                fidelity = check_report(report, composed.value, evidence)
            else:
                fidelity = FidelityCheck(False, ["The reporter returned no text; the deterministic summary is shown."])
            return AssistantResult(question, plan, executions, composed, report, source, raw_report, fidelity, attempts)
        raise AssistantFailure(question, attempts)

    def _execute(self, plan: dict[str, Any]) -> tuple[list[QueryExecution], ComposedAnswer]:
        conn = connect_read_only(self.db_path)
        try:
            executions = [execute_read_only(conn, sql) for sql in expand_step_references(plan["steps"])]
            for step, execution in zip(plan["steps"], executions):
                if not execution.rows:
                    raise SQLExecutionError(f"{step['id']} returned no rows; check labels, joins and dates.")
                if any(value is None for row in execution.rows for value in row):
                    raise SQLExecutionError(f"{step['id']} returned NULL; check labels, joins and dates.")
            composed = compose_results(plan["operation"], [e.rows for e in executions], conn=conn)
            return executions, composed
        finally:
            conn.close()

    def _report(
        self, question: str, plan: dict[str, Any], executions: list[QueryExecution], composed: ComposedAnswer
    ) -> tuple[str, str, str]:
        steps = [
            {"id": step["id"], "purpose": step["purpose"], "rows": rows_to_json(execution.rows)}
            for step, execution in zip(plan["steps"], executions)
        ]
        raw = self.generator.generate(report_prompt(question, composed.value, steps))
        text = strip_fences(raw).strip().strip('"').strip()
        if text.startswith("{"):  # Tolerate the JSON shape used by earlier prompts.
            try:
                text = str(parse_json_object(text).get("answer", "")).strip()
            except ValueError:
                pass
        if text:
            return text, "model", raw
        return summarize(composed), "fallback", raw


def save_trace(result: AssistantResult, path: str | Path) -> None:
    Path(path).write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

#!/usr/bin/env python3
"""Answer one business question with the baseline and the structured solution.

Shows both systems on the same input (the demonstration the video requires)
and saves the solution trace. Needs a GPU for the model.

    python scripts/run_question.py --id q09-p
    python scripts/run_question.py "¿Cuál fue el ingreso total de julio de 2026?"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sql4business.model import BASELINE_MAX_NEW_TOKENS, MODEL_ID, HuggingFaceGenerator, baseline_prompt  # noqa: E402
from sql4business.pipeline import AssistantFailure, BusinessAssistant, save_trace  # noqa: E402
from sql4business.sql_tools import connect_read_only, execute_baseline  # noqa: E402


def load(name: str) -> dict:
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("question", nargs="?", help="question text")
    parser.add_argument("--id", help="id of a question in data/questions.json or data/paraphrases.json")
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--db", default=ROOT / "data" / "business.db", type=Path)
    parser.add_argument("--trace", default=ROOT / "results" / "trace.json", type=Path)
    args = parser.parse_args()

    official = load("questions.json")
    if args.id:
        dataset = official["questions"] + load("paraphrases.json")["questions"]
        question = next(q["question"] for q in dataset if q["id"] == args.id)
    elif args.question:
        question = args.question
    else:
        parser.error("give a question or --id")
    print("QUESTION:", question)

    generator = HuggingFaceGenerator(args.model)

    print("\n=== Baseline: Deliverable 1 direct prompt ===")
    raw = generator.generate(baseline_prompt(official["schema"], question), BASELINE_MAX_NEW_TOKENS)
    conn = connect_read_only(args.db)
    try:
        executions = execute_baseline(conn, raw)
    finally:
        conn.close()
    for execution in executions or [None]:
        if execution is None:
            print("no SELECT statement in the output:", raw)
            continue
        print("SQL: ", execution.sql)
        print("rows:", execution.error or execution.rows[:10])

    print("\n=== Structured solution ===")
    try:
        result = BusinessAssistant(args.db, generator).answer(question)
    except AssistantFailure as failure:
        print(failure)
        for number, attempt in enumerate(failure.attempts, start=1):
            print(f"attempt {number}: {attempt['error']}")
        return
    for number, attempt in enumerate(result.attempts[:-1], start=1):
        print(f"attempt {number} repaired: {attempt['error']}")
    for step, execution in zip(result.plan["steps"], result.executions):
        print(f"{step['id']}: {step['purpose']}\n  SQL:  {execution.sql}\n  rows: {execution.rows[:10]}")
    print("composition:", result.composed.operation, "->", result.composed.value)
    print("report:", result.report)
    print("report faithful:", result.fidelity.faithful, result.fidelity.issues or "")
    save_trace(result, args.trace)
    print("trace:", args.trace)


if __name__ == "__main__":
    main()

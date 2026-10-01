#!/usr/bin/env python3
"""Evaluate the baseline, the grounded direct prompt and the structured solution.

Runs the official 15 questions and the 12 held-out paraphrases with the same
criteria for every system, writes the full traces and a summary, and can emit
the LaTeX results table used by docs/deliverable2.tex. Needs a GPU for the model.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sql4business.evaluation import SYSTEMS, environment, evaluate, latex_table, load_questions  # noqa: E402
from sql4business.model import MODEL_ID, GenerationSettings, HuggingFaceGenerator  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--db", default=ROOT / "data" / "business.db", type=Path)
    parser.add_argument("--questions", default=ROOT / "data" / "questions.json", type=Path)
    parser.add_argument("--heldout", default=ROOT / "data" / "paraphrases.json", type=Path)
    parser.add_argument("--systems", default=",".join(SYSTEMS), help="comma-separated subset of " + ",".join(SYSTEMS))
    parser.add_argument("--limit", type=int, default=0, help="questions per set, for a smoke test")
    parser.add_argument("--output", default=ROOT / "results" / "deliverable2_v3.json", type=Path)
    parser.add_argument("--tex", type=Path, help="also write the LaTeX results table here")
    args = parser.parse_args()

    official = load_questions(args.questions)
    question_sets = {
        "official": official["questions"],
        "heldout": load_questions(args.heldout)["questions"],
    }
    if args.limit:
        question_sets = {name: questions[: args.limit] for name, questions in question_sets.items()}

    started = time.perf_counter()
    generator = HuggingFaceGenerator(args.model, GenerationSettings())
    results = evaluate(
        generator,
        args.db,
        question_sets,
        baseline_schema=official["schema"],
        systems=[name.strip() for name in args.systems.split(",") if name.strip()],
    )
    meta = {**environment(generator), "settings": vars(generator.settings)}
    meta["seconds"] = round(time.perf_counter() - started, 1)
    results = {"meta": meta, **results}
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"\nSaved {len(results['records'])} records to {args.output}")
    for set_name, systems in results["summary"].items():
        for system, metrics in systems.items():
            cells = "  ".join(
                f"{metric}: " + " ".join(f"{group[:4]}={k}/{n}" for group, (k, n) in counts.items())
                for metric, counts in metrics.items()
            )
            print(f"{set_name:8} {system:9} {cells}")
    if "solution" in results["records"][0]:
        print("\nStructured solution without a correct and faithful answer:")
        for record in results["records"]:
            solution = record["solution"]
            if not solution["e2e"]:
                reason = solution.get("error") or "; ".join(solution.get("report_issues", [])) or "wrong answer"
                print(f"- {record['set']}/{record['id']}: {reason[:200]}")
    if args.tex:
        args.tex.write_text(latex_table(results["summary"]), encoding="utf-8")
        print(f"\nWrote {args.tex}")


if __name__ == "__main__":
    main()

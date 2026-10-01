import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DB = ROOT / "data" / "business.db"
OFFICIAL = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))
HELDOUT = json.loads((ROOT / "data" / "paraphrases.json").read_text(encoding="utf-8"))
QUESTIONS = {q["id"]: q for q in OFFICIAL["questions"] + HELDOUT["questions"]}


class ScriptedGenerator:
    """Returns canned model outputs in order, recording the prompts it received."""

    def __init__(self, *outputs):
        self.outputs = list(outputs)
        self.prompts = []

    def generate(self, prompt, max_new_tokens=None):
        self.prompts.append(prompt)
        return self.outputs.pop(0)


def plan(*sqls, operation="direct"):
    steps = [{"id": f"step_{i}", "purpose": f"step {i}", "sql": sql} for i, sql in enumerate(sqls, start=1)]
    return json.dumps({"steps": steps, "composition": {"operation": operation}})


def report(text):
    return json.dumps({"answer": text}, ensure_ascii=False)

"""Model wrapper and prompts for the baseline and the structured assistant."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol


MODEL_ID = "Qwen/Qwen2.5-Coder-3B-Instruct"

# Direct-prompting baseline, verbatim from notebooks/baseline_eval.ipynb (Deliverable 1).
BASELINE_TEMPLATE = """Eres un asistente que traduce preguntas de negocio a SQL.

Esquema de la base de datos:
{schema}

Pregunta: {question}

Responde unicamente con la o las consultas SQL necesarias para responder la
pregunta, separadas por punto y coma. No expliques nada, no uses markdown."""
BASELINE_MAX_NEW_TOKENS = 300


class TextGenerator(Protocol):
    def generate(self, prompt: str, max_new_tokens: int | None = None) -> str:
        """Return one deterministic completion."""


@dataclass
class GenerationSettings:
    max_new_tokens: int = 384
    load_in_4bit: bool = True


class HuggingFaceGenerator:
    """Greedy generation with 4-bit NF4 quantization, as declared in Deliverable 1."""

    def __init__(self, model_id: str = MODEL_ID, settings: GenerationSettings | None = None):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.model_id = model_id
        self.settings = settings or GenerationSettings()
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        kwargs: dict[str, Any] = {"device_map": "auto"}
        if self.settings.load_in_4bit and torch.cuda.is_available():
            from transformers import BitsAndBytesConfig

            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
            )
        self.model = AutoModelForCausalLM.from_pretrained(model_id, **kwargs)

    def generate(self, prompt: str, max_new_tokens: int | None = None) -> str:
        messages = [{"role": "user", "content": prompt}]
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
        ).to(self.model.device)
        output = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens or self.settings.max_new_tokens,
            do_sample=False,
        )
        generated = output[0][inputs["input_ids"].shape[1] :]
        return self.tokenizer.decode(generated, skip_special_tokens=True).strip()


def baseline_prompt(schema: str, question: str) -> str:
    return BASELINE_TEMPLATE.format(schema=schema, question=question)


def plan_prompt(schema: str, question: str, previous_error: str | None = None) -> str:
    retry = ""
    if previous_error:
        retry = (
            "\nYour previous plan failed. Fix the cause and return a complete new plan.\n"
            f"Error: {previous_error}\n"
        )
    return f"""You are the planning component of a business analytics assistant over a SQLite database.
The user is a manager who does not know SQL. Turn the question into a short executable plan.

Database:
{schema}

Question:
{question}
{retry}
Return exactly one JSON object and nothing else:
{{"steps": [{{"id": "step_1", "purpose": "short description", "sql": "one SQLite SELECT"}}],
  "composition": {{"operation": "direct"}}}}

Choose the operation; code computes it, so never calculate percentages yourself:
- direct: the answer is the result of the last step. Prefer a single step.
- growth_pct: exactly two steps, each returning one number: the earlier or reference value first,
  the later value second. Code computes (second - first) / first * 100.
- share_pct: exactly two steps, each returning one number: the total first, the part second.
  Code computes part / total * 100.
- compare_equal: exactly two steps, each returning the top name of one group or period, in the
  order the question mentions them. Code checks whether both names are the same.
- filter_then_rank: exactly two steps: the first returns the ids of the products that satisfy the
  condition; the second ranks products by the requested metric in descending order. Code returns
  the best-ranked product that satisfies the condition.

SQL rules: one SELECT or WITH query per step, SQLite syntax, only the tables, columns and exact
text values listed above, explicit date ranges inside the available dates. When a filter or a
name comes from another table, join it through product_id. A later step may read an earlier
step's rows as a table with that step's id (for example FROM step_1). Select only the columns
the answer needs.
"""


def report_prompt(question: str, answer: Any, steps: list[dict[str, Any]]) -> str:
    evidence = "\n".join(
        f"- {step['id']}: {step['purpose']} -> {json.dumps(step['rows'][:5], ensure_ascii=False)}"
        for step in steps
    )
    encoded = json.dumps(answer, ensure_ascii=False)
    return f"""You are the reporting component of a business analytics assistant.

Question: {question}

Verified answer computed by code:
{encoded}

SQL steps that produced it:
{evidence}

Write one or two sentences for a non-technical manager, in the same language as the question.
Use only the numbers and names of the verified answer and the steps. Copy each number exactly
as it appears above (for example 97658120 or 59.08), without adding separators, and do not add
other figures. For a percentage change, state whether it is an increase or a decrease.
Describe periods and groups as the steps define them.
Return only the sentences, without JSON, markdown or quotes.
"""


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object, tolerating a markdown fence around it."""

    cleaned = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise ValueError("The model did not return a JSON object.") from None
        try:
            value = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise ValueError(f"The model returned invalid JSON: {exc}") from None
    if not isinstance(value, dict):
        raise ValueError("The model JSON must be an object.")
    return value

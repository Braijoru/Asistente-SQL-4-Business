"""
Define el set de evaluacion (15 preguntas de negocio) y calcula el
resultado de referencia ejecutando el SQL correcto contra business.db.
Genera questions.json, listo para que el notebook de evaluacion lo
use como ground truth.

Genera tambien paraphrases.json: 12 preguntas con la misma intencion
y el mismo SQL de referencia que una pregunta oficial, pero redactadas
de otra forma. Es el conjunto de evaluacion externo (held-out): se
escribio durante la auditoria del Deliverable 2 y no se usa para
disenar el sistema.

Uso:
    python build_questions.py
"""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "business.db"
OUT_PATH = Path(__file__).parent / "questions.json"
HELDOUT_PATH = Path(__file__).parent / "paraphrases.json"

SCHEMA = """
CREATE TABLE products (product_id INTEGER PRIMARY KEY, name TEXT, category TEXT, price INTEGER);
CREATE TABLE sales (sale_id INTEGER PRIMARY KEY, product_id INTEGER, sale_date TEXT, quantity INTEGER, amount INTEGER);
CREATE TABLE inventory (product_id INTEGER PRIMARY KEY, stock INTEGER, reorder_point INTEGER);
""".strip()

# Cada pregunta trae su(s) consulta(s) SQL de referencia. "puntual"
# se resuelve con una sola consulta, "combinada" requiere ejecutar
# mas de una y razonar sobre los resultados (p.ej. calcular un
# porcentaje de crecimiento a partir de dos consultas).
QUESTIONS = [
    {
        "id": "q01",
        "type": "puntual",
        "question": "Cuantas unidades del Notebook 14 pulgadas se vendieron en junio de 2026?",
        "gold_sql": [
            "SELECT SUM(s.quantity) FROM sales s JOIN products p ON s.product_id = p.product_id "
            "WHERE p.name = 'Notebook 14 pulgadas' AND s.sale_date BETWEEN '2026-06-01' AND '2026-06-30'"
        ],
    },
    {
        "id": "q02",
        "type": "puntual",
        "question": "Cual es el ingreso total generado por la categoria Electronica en todo el semestre?",
        "gold_sql": [
            "SELECT SUM(s.amount) FROM sales s JOIN products p ON s.product_id = p.product_id "
            "WHERE p.category = 'Electronica'"
        ],
    },
    {
        "id": "q03",
        "type": "puntual",
        "question": "Que producto tuvo el mayor ingreso total acumulado en el semestre?",
        "gold_sql": [
            "SELECT p.name FROM sales s JOIN products p ON s.product_id = p.product_id "
            "GROUP BY p.product_id ORDER BY SUM(s.amount) DESC LIMIT 1"
        ],
    },
    {
        "id": "q04",
        "type": "puntual",
        "question": "Cuantas unidades en total se vendieron en la categoria Alimentos durante agosto de 2026?",
        "gold_sql": [
            "SELECT SUM(s.quantity) FROM sales s JOIN products p ON s.product_id = p.product_id "
            "WHERE p.category = 'Alimentos' AND s.sale_date BETWEEN '2026-08-01' AND '2026-08-31'"
        ],
    },
    {
        "id": "q05",
        "type": "puntual",
        "question": "Cual es el precio del producto Set de Ollas?",
        "gold_sql": ["SELECT price FROM products WHERE name = 'Set de Ollas'"],
    },
    {
        "id": "q06",
        "type": "puntual",
        "question": "Que productos tienen stock por debajo de su punto de reorden?",
        "gold_sql": [
            "SELECT p.name FROM inventory i JOIN products p ON i.product_id = p.product_id "
            "WHERE i.stock < i.reorder_point"
        ],
    },
    {
        "id": "q07",
        "type": "puntual",
        "question": "Cuantas ventas distintas se registraron para la Polera Basica en todo el semestre?",
        "gold_sql": [
            "SELECT COUNT(*) FROM sales s JOIN products p ON s.product_id = p.product_id "
            "WHERE p.name = 'Polera Basica'"
        ],
    },
    {
        "id": "q08",
        "type": "puntual",
        "question": "Cual es el ingreso promedio por venta en la categoria Hogar?",
        "gold_sql": [
            "SELECT AVG(s.amount) FROM sales s JOIN products p ON s.product_id = p.product_id "
            "WHERE p.category = 'Hogar'"
        ],
    },
    {
        "id": "q09",
        "type": "combinada",
        "question": "Cual fue el crecimiento porcentual de ventas totales entre el primer trimestre (marzo a mayo) y el segundo trimestre (junio a agosto) del semestre?",
        "gold_sql": [
            "SELECT SUM(amount) FROM sales WHERE sale_date BETWEEN '2026-03-01' AND '2026-05-31'",
            "SELECT SUM(amount) FROM sales WHERE sale_date BETWEEN '2026-06-01' AND '2026-08-31'",
        ],
        "combine": "growth_pct",
    },
    {
        "id": "q10",
        "type": "combinada",
        "question": "Cual fue el producto top en ingresos de cada trimestre del semestre, y cambio el lider entre el primer y el segundo trimestre?",
        "gold_sql": [
            "SELECT p.name FROM sales s JOIN products p ON s.product_id = p.product_id "
            "WHERE s.sale_date BETWEEN '2026-03-01' AND '2026-05-31' "
            "GROUP BY p.product_id ORDER BY SUM(s.amount) DESC LIMIT 1",
            "SELECT p.name FROM sales s JOIN products p ON s.product_id = p.product_id "
            "WHERE s.sale_date BETWEEN '2026-06-01' AND '2026-08-31' "
            "GROUP BY p.product_id ORDER BY SUM(s.amount) DESC LIMIT 1",
        ],
        "combine": "compare_equal",
    },
    {
        "id": "q11",
        "type": "combinada",
        "question": "Cuantas unidades totales se vendieron en el semestre y cuantas de esas corresponden a la categoria Electronica?",
        "gold_sql": [
            "SELECT SUM(quantity) FROM sales",
            "SELECT SUM(s.quantity) FROM sales s JOIN products p ON s.product_id = p.product_id "
            "WHERE p.category = 'Electronica'",
        ],
        "combine": "share_pct",
        # La pregunta pide los dos conteos, no el porcentaje.
        "answer_fields": ["total", "subset"],
    },
    {
        "id": "q12",
        "type": "combinada",
        "question": "El ingreso de agosto de 2026 fue mayor o menor que el de marzo de 2026, y en que porcentaje?",
        "gold_sql": [
            "SELECT SUM(amount) FROM sales WHERE sale_date BETWEEN '2026-03-01' AND '2026-03-31'",
            "SELECT SUM(amount) FROM sales WHERE sale_date BETWEEN '2026-08-01' AND '2026-08-31'",
        ],
        "combine": "growth_pct",
    },
    {
        "id": "q13",
        "type": "puntual",
        "question": "Cuantos productos distintos tiene la categoria Ropa?",
        "gold_sql": ["SELECT COUNT(*) FROM products WHERE category = 'Ropa'"],
    },
    {
        "id": "q14",
        "type": "combinada",
        "question": "De los productos con stock bajo el punto de reorden, cual es el que mas ingreso genero en el semestre?",
        "gold_sql": [
            "SELECT p.product_id FROM inventory i JOIN products p ON i.product_id = p.product_id "
            "WHERE i.stock < i.reorder_point",
            "SELECT p.name FROM sales s JOIN products p ON s.product_id = p.product_id "
            "GROUP BY p.product_id ORDER BY SUM(s.amount) DESC",
        ],
        "combine": "filter_then_rank",
    },
    {
        "id": "q15",
        "type": "puntual",
        "question": "Cual es el ingreso total de la tienda en todo el semestre?",
        "gold_sql": ["SELECT SUM(amount) FROM sales"],
    },
]


# Parafrasis: (id, pregunta oficial de origen, texto). Heredan el SQL de
# referencia, el tipo y la operacion de la pregunta de origen.
PARAPHRASES = [
    ("q09-p", "q09", "¿Cuánto crecieron, en porcentaje, las ventas de junio a agosto respecto de marzo a mayo?"),
    ("q10-p", "q10", "¿Qué producto generó más ingresos entre marzo y mayo, y cuál entre junio y agosto? ¿Es el mismo?"),
    ("q11-p", "q11", "¿Qué porcentaje de las unidades vendidas en el semestre corresponde a la categoría Electronica?"),
    ("q12-p", "q12", "¿Cuánto varió el ingreso entre marzo de 2026 y agosto de 2026, en términos porcentuales?"),
    ("q14-p", "q14", "Entre los productos que están bajo su punto de reorden, ¿cuál vendió más en pesos durante el semestre?"),
    ("q12-en", "q12", "Was August 2026 revenue higher or lower than March 2026 revenue, and by what percent?"),
    ("q14-en", "q14", "Among products whose stock is below the reorder point, which one generated the most revenue in the semester?"),
    ("q02-p", "q02", "¿Cuánto facturó en total la categoría Electronica entre marzo y agosto de 2026?"),
    ("q04-p", "q04", "¿Cuántas unidades de productos de la categoría Alimentos se vendieron en agosto de 2026?"),
    ("q07-p", "q07", "¿Cuántas transacciones de venta tuvo la Polera Basica durante todo el periodo?"),
    ("q08-p", "q08", "¿Cuál es el monto promedio de cada venta de productos de la categoría Hogar?"),
    ("q15-p", "q15", "¿Cuánto vendió la tienda en total, en pesos, entre marzo y agosto de 2026?"),
]


def run_scalar(cur, sql):
    cur.execute(sql)
    rows = cur.fetchall()
    return rows


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    out = []
    for q in QUESTIONS:
        gold_results = [run_scalar(cur, s) for s in q["gold_sql"]]
        entry = dict(q)
        entry["gold_result"] = gold_results
        out.append(entry)

    OUT_PATH.write_text(
        json.dumps(
            {"schema": SCHEMA, "questions": out}, ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )
    print(f"questions.json generado con {len(out)} preguntas.")
    for e in out:
        print(f"  {e['id']} [{e['type']}] -> {e['gold_result']}")

    by_id = {q["id"]: q for q in out}
    heldout = []
    for pid, source, text in PARAPHRASES:
        entry = {k: v for k, v in by_id[source].items() if k not in ("id", "question", "answer_fields")}
        entry = {"id": pid, "source_id": source, "question": text, **entry}
        entry["gold_result"] = [run_scalar(cur, s) for s in entry["gold_sql"]]
        heldout.append(entry)
    HELDOUT_PATH.write_text(
        json.dumps({"questions": heldout}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    conn.close()
    print(f"paraphrases.json generado con {len(heldout)} preguntas.")


if __name__ == "__main__":
    main()

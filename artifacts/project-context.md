# Contexto canonico del proyecto

## Identidad

- Proyecto: SQL4Business, asistente de consultas de negocio.
- Curso: Generative Artificial Intelligence (580694), Universidad de
  Concepcion.
- Equipo: Aredhel Jimenez, Bryan Riquelme, Guido Salazar y Vicente Sonez.
- Repositorio: `Asistente-SQL-4-Business`.
- Objetivo de investigacion: responder preguntas de negocio ejecutando el SQL
  necesario y redactar un resumen ejecutivo cuyas cifras sean fieles a los
  resultados ejecutados.

## Tarea que no se debe simplificar

La tarea incluye dos casos:

1. Preguntas puntuales, resolubles con una consulta.
2. Preguntas combinadas, que requieren planificar y ejecutar varias consultas,
   relacionar sus resultados y realizar una operacion como crecimiento,
   participacion, comparacion o filtrado seguido de ranking.

Una salida correcta requiere consultas necesarias y suficientes, resultados
correctos y un reporte final sin cifras inventadas ni inconsistentes con la
base de datos. Deliverable 2 debe continuar con esta misma definicion, no
convertir el problema en solo text-to-SQL de una consulta.

## Estado al terminar Deliverable 1

- Base SQLite sintetica reproducible en `data/business.db`.
- Datos generados con semilla fija `42`.
- Periodo: 1 de marzo a 31 de agosto de 2026.
- Tablas: `products`, `sales` e `inventory`.
- Set de evaluacion: 15 preguntas con SQL y resultados de referencia en
  `data/questions.json`.
- Distribucion: 10 preguntas puntuales y 5 combinadas.
- Notebook baseline: `notebooks/baseline_eval.ipynb`.
- La evaluacion usa cuantizacion de 4 bits, generacion determinista y una GPU
  T4 de Colab declarada en Deliverable 1.

## Esquema de datos

```sql
CREATE TABLE products (
  product_id INTEGER PRIMARY KEY,
  name TEXT,
  category TEXT,
  price INTEGER
);

CREATE TABLE sales (
  sale_id INTEGER PRIMARY KEY,
  product_id INTEGER,
  sale_date TEXT,
  quantity INTEGER,
  amount INTEGER
);

CREATE TABLE inventory (
  product_id INTEGER PRIMARY KEY,
  stock INTEGER,
  reorder_point INTEGER
);
```

Hay 10 productos en cuatro categorias: Electronica, Hogar, Ropa y Alimentos.
Las ventas tienen fechas ISO, cantidad y monto entero. La segunda parte del
periodo tiene un sesgo de mayor volumen para producir crecimiento observable.

## Preguntas de referencia

Tipos de composicion presentes en `questions.json`:

- `growth_pct`: comparar dos totales y calcular `(nuevo - anterior) /
  anterior * 100`.
- `compare_equal`: comparar lideres entre dos periodos.
- `share_pct`: calcular la participacion de un subconjunto sobre el total.
- `filter_then_rank`: filtrar por inventario y luego seleccionar el mayor
  ingreso.

Las cinco preguntas combinadas son `q09`, `q10`, `q11`, `q12` y `q14`. La
pregunta `q14` es especialmente importante porque exige combinar la condicion
de stock bajo con el ranking de ingresos; el resultado correcto es
`Zapatillas Urbanas`.

## Baseline medido

Fuente: `results/baseline_comparison.csv` y
`results/baseline_results.json`.

| Modelo | Global | Puntual | Combinada |
|---|---:|---:|---:|
| Qwen/Qwen2.5-Coder-7B-Instruct | 33.3% | 50% | 0% |
| Qwen/Qwen2.5-Coder-3B-Instruct | 46.7% | 70% | 0% |
| meta-llama/Llama-3.1-8B-Instruct | 46.7% | 70% | 0% |

El baseline entrega directamente una o mas consultas SQL a partir del esquema
y la pregunta. El notebook extrae sentencias `SELECT`, las ejecuta en SQLite
y compara los resultados con el ground truth. Los errores observados incluyen
fechas inventadas, categorias en ingles, sintaxis de otros motores SQL,
seleccion incorrecta de columnas y tratar una pregunta combinada como una sola
consulta no composicional.

## Modelo elegido

Deliverable 1 propuso tres candidatos:

- Qwen2.5-Coder-7B-Instruct: mejor exactitud publicada entre los candidatos
  pequenos, pero mayor costo; 33.3% en el baseline propio.
- Qwen2.5-Coder-3B-Instruct: menor tamano y misma familia; empata el mejor
  resultado propio (46.7%).
- Llama-3.1-8B-Instruct: mayor soporte de comunidad, pero requiere acceso
  gated y tambien obtiene 46.7%.

Decision de Deliverable 2: `Qwen/Qwen2.5-Coder-3B-Instruct` (revision
`488639f`), por economia de parametros y empate en el mejor resultado propio.

## Direccion tecnica recomendada

La primera solucion debe atacar el fallo observado, no solo cambiar el nombre
del modelo. La intervencion recomendada es una descomposicion controlada:

1. El modelo clasifica la pregunta y propone un plan de pasos SQL.
2. Cada paso se ejecuta contra SQLite con validacion de errores.
3. Un compositor determinista calcula operaciones entre resultados cuando la
   pregunta lo requiere.
4. El reporte se genera a partir de resultados estructurados y se valida que
   cada cifra citada exista en esos resultados.

La implementacion concreta puede usar prompts estructurados, formato JSON,
ejecucion de herramientas y composicion determinista. No se debe afirmar que
una tecnica mejora el baseline hasta medirla sobre el mismo set.

## Restricciones de evidencia

- El sistema debe correr end-to-end sobre el hardware declarado en Deliverable
  1, no ser un mockup ni usar respuestas hardcodeadas.
- Baseline y solucion deben recibir las mismas entradas y evaluarse con el
  mismo criterio.
- Debe existir al menos un caso de fallo real de la solucion, con explicacion
  causal.
- La evidencia debe distinguir hechos medidos, decisiones del equipo e
  hipotesis aun no verificadas.
- No usar datos sinteticos nuevos o un subconjunto mas facil sin declararlo.

## Decisiones de Deliverable 2 (version v3, despues de la auditoria)

- Modelo: `Qwen/Qwen2.5-Coder-3B-Instruct`, NF4 4-bit, computo bf16,
  decodificacion greedy, Colab T4.
- Intervencion: esquema enriquecido (valores exactos, rango de fechas, joins),
  plan JSON con la operacion elegida por el modelo (sin reglas especificas de
  las preguntas), SQLite de solo lectura con referencias entre pasos, hasta dos
  reparaciones, composicion determinista, reporte en el idioma de la pregunta y
  verificacion de fidelidad de cada cifra.
- Conjuntos: las 15 preguntas oficiales (set de desarrollo, in-sample) y 12
  parafrasis externas en `data/paraphrases.json` (no se usan para disenar).
- Sistemas comparados: baseline de D1 (prompt literal), alternativa (mismo
  prompt con esquema enriquecido) y solucion estructurada.
- Metricas: `sql` (criterio de D1), `answer` (respuesta final, comun a todos),
  `report` y `e2e` (solo solucion); por tipo y global, mas tiempo por pregunta.
- Reintentos: maximo dos despues del primer intento.
- Interfaz: notebook de Colab que clona el repositorio; scripts
  `scripts/evaluate.py` y `scripts/run_question.py`.
- Idioma: documento tecnico en ingles; reportes en el idioma de la pregunta.
- Presentacion: PDF tecnico LaTeX de una pagina con la tabla generada desde
  `results/deliverable2_v3.json`; el video se publica fuera del repositorio.

Historial de corridas: `results/deliverable2_v1.json` (17-09, version
auditada), `results/deliverable2_v2.json` (24-09, primera corrida corregida) y
`results/deliverable2_v3.json` (24-09, reportero en texto plano; version
final). Ver `artifacts/auditoria-deliverable-2.md`.

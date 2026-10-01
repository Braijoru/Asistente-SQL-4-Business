# Auditoría del Deliverable 2 — SQL4Business

> **Estado (24-09-2026):** los hallazgos de este informe se corrigieron en la rama
> `d2-correcciones`: v2, commit `2d99f37`, y v3, commit `d0c33b6`, que es la versión final.
> La tabla de la sección 0 indica dónde quedó cada corrección. Las secciones 1 a 7
> describen la versión auditada (v1, commit `dbd29b1`), así que sus rutas y números de
> línea corresponden a ese commit.

## 0. Estado de las correcciones (v2 y v3)

| Hallazgo | Corrección aplicada en v2 |
|---|---|
| C1 PDF desactualizado | La tabla del PDF la genera `scripts/evaluate.py --tex` desde `results/deliverable2_v2.json`; el PDF se recompila desde el `.tex` (1 página) |
| C2 Ajuste al set no declarado | Se eliminaron el clasificador por palabras clave, su veto y los alias específicos de preguntas. El planificador elige la operación con definiciones genéricas. Las 12 paráfrasis quedaron como set externo (`data/paraphrases.json`), evaluado con los mismos criterios. Las 15 preguntas oficiales se declaran como set de desarrollo (in-sample) |
| A1 Baseline distinta a D1 | La baseline vuelve a ser el prompt de D1 literal (un test lo compara con el notebook de D1) |
| A2 Criterio asimétrico | Métrica de respuesta final común a todos los sistemas (`evaluation.answer_correct`); `answer_fields` en q11; el criterio SQL es el de D1 (conjuntos de filas exactos) |
| A3 Regresiones | Se reportan por pregunta en `results/deliverable2_v2.json` y en el PDF |
| A4 Validador de fidelidad | Nuevo `fidelity.py`: toda cifra debe salir de la respuesta verificada o de la evidencia, controla dirección y "cambió", y cuenta el respaldo como fallo. El reporte va en el idioma de la pregunta |
| A5 Reproducibilidad | El notebook clona el repo en `REF` (sin ZIP); versiones fijadas; un solo script de evaluación; los resultados registran commit, versiones y GPU; el PDF cita el fork |
| M1 Fallo sin causa | Los pasos pueden leer pasos anteriores (se expanden como CTE), que era la causa de q14 y q10 en v1. Se guardan todos los intentos en la traza, y el caso de fallo del PDF se analiza con esas trazas |
| M2 Composición | Valida la forma de cada resultado, resuelve productos por id o nombre y no reordena por columnas id |
| M3 Validador SQL | Ignora literales, permite `REPLACE()`, rechaza solo años sin datos; conexión SQLite `mode=ro` |
| M4 Documento técnico | Se agregaron equipo, URLs, configuración del modelo, estrategia alternativa, costo, límites y diagrama TikZ |
| M5 README | Reescrito: reproducción, métricas, resultados, límites e historial |
| B1–B5 | Se eliminó código muerto, se borraron el ZIP, el notebook duplicado y los scripts redundantes, se ignoran `*.exe`, y hay 31 tests por módulo |

**Re-medición en Colab T4:**

- La primera corrida del código corregido (v2, `results/deliverable2_v2.json`) mostró que
  el reportero escribía reportes correctos en texto plano que se descartaban por no ser
  JSON (5 de 27).
- En v3 solo cambió ese formato. El SQL y las respuestas son idénticos a v2 en las 27
  preguntas.

Resultados v3 (`results/deliverable2_v3.json`, respuesta correcta y reporte fiel):

| Conjunto | Baseline D1 | Solución, respuesta | Solución, respuesta + reporte fiel |
|---|---|---|---|
| Oficial (15) | 8/15 | 11/15 | 10/15 |
| Paráfrasis (12) | 5/12 | 10/12 | 10/12 |
| Combinadas parafraseadas (7) | 2/7 | 5/7 | 5/7 (en v1: 0/7 con el criterio SQL) |

Los fallos que quedan tienen causa identificada en el README y el PDF (q09 es el caso
principal) y no se corrigieron con reglas específicas de las preguntas.

---

- **Fecha de la auditoría:** 23-09-2026 (entrega: 30-09-2026, 23:59).
- **Objeto auditado:** commit `dbd29b1` ("Deliverable 2", 17-09-2026 03:44) del fork
  `VicenteSonez/Asistente-SQL-4-Business`, más los notebooks de Colab guardados en el
  Drive de Vicente (solo lectura).
- **Referencia normativa:** enunciado `docs/Deliverable 2.pdf` (requisitos y rúbrica de
  6 criterios × 10 puntos) y lo comprometido en el Deliverable 1.
- **Evidencia:** `artifacts/auditoria/colab_rerun_2026-09-23.txt` (salida de la
  re-ejecución en Colab). Las verificaciones offline de la auditoría quedaron como tests en
  `tests/`, y las paráfrasis en `data/paraphrases.json`.

---

## 1. Veredicto

**El sistema es real, corre de extremo a extremo en una T4 y las cifras publicadas son
auténticas. Pero el entregable no está listo para enviarse tal cual:** hay un PDF con
cifras equivocadas, una mejora que depende de reglas escritas para las 15 preguntas del
set y varias desviaciones respecto del Deliverable 1 que no están declaradas.

Lo que **sí queda certificado**:

| Verificación | Resultado |
|---|---|
| La corrida que generó `results/deliverable2_comparison.json` existió | ✅ Notebook en Drive, 17-09 03:29–03:38 (hora Chile), GPU T4; su salida (progreso por pregunta, errores y resumen) coincide con el JSON |
| Las banderas del JSON salen del código versionado | ✅ Re-ejecutando el SQL guardado con el código del commit: 0 discrepancias |
| Re-ejecución independiente en Colab T4 (23-09) desde `dbd29b1` | ✅ Idéntica en 15/15 preguntas: mismas salidas de la baseline, planes, reportes, errores y banderas (6/10, 0/5 · 9/10, 3/5 · 8/10, 2/5) |
| Datos reproducibles | ✅ `business.db` y `questions.json` se regeneran idénticos; los 15 resultados gold son correctos |
| Tests y sintaxis | ✅ 8/8 tests (Python 3.8 y 3.12); 13 archivos compilan |
| Modelo más pequeño de los tres candidatos | ✅ Qwen2.5-Coder-3B-Instruct |

Lo que **impide certificarlo como "bien"** (detalle en §4):

1. **C1** — `docs/deliverable2.pdf` muestra la solución con 20 % / 20 % / 20 % y falla en q01:
   es de una iteración anterior. El `.tex` dice 90 % / 60 % / 80 %.
2. **C2** — La mejora en preguntas combinadas depende de un clasificador por palabras clave
   calcado de la redacción exacta de las 5 preguntas del set: clasifica bien 15/15 del set
   pero 1/7 paráfrasis combinadas. Re-ejecutado en Colab con esas paráfrasis, la solución
   acierta **0/7 combinadas** (igual que la baseline). No está declarado.
3. **A1** — La baseline cambió respecto de D1 (46,7 % → 40 %) sin declararlo; el propio PDF
   cita 46,7 % en el texto y 40 % en la tabla.
4. **A2/A3** — El criterio marca como incorrecta una respuesta correcta de la baseline
   (q14), así que "0 % en combinadas" está sobrestimado; hay 2 regresiones (q04, q14) no
   reportadas.
5. **A4** — El validador de fidelidad acepta un reporte engañoso (q09), rechaza dos fieles
   (q11, q13) y cuenta como fiel un reporte de respaldo que el modelo no generó (q03).
6. **A5** — El ZIP versionado es anterior al código y hace fallar el notebook; el
   repositorio citado en D1 (upstream `aredhel-jmze`) no contiene el Deliverable 2.

---

## 2. Qué se verificó y cómo

| # | Verificación | Método | Resultado |
|---|---|---|---|
| 1 | Datos | `build_db.py` y `build_questions.py` re-ejecutados en una carpeta aparte; comparación tabla por tabla | Idénticos (549 ventas, 10 productos, 10 inventarios); gold recalculado = gold guardado |
| 2 | Tests | `unittest` con Python 3.8.10 y 3.12.5 | 8/8 OK |
| 3 | Replay de trazas | Re-ejecutar cada SQL de `deliverable2_comparison.json` y recalcular `execution_correct`, `answer_correct`, `report_fidelity` con el código del commit | 0 discrepancias en 15 preguntas |
| 4 | Pipeline completo con salidas grabadas | `BusinessAssistant.answer` alimentado con los planes y reportes grabados (modo `AUDIT_FAKE=1` de `audit_colab.py`) | Reproduce 6/10, 0/5, 9/10, 3/5, 8/10, 2/5 |
| 5 | Baseline D1 vs D2 | Salidas de D1 re-puntuadas con el criterio D2 y viceversa | El criterio no explica la diferencia; el prompt sí |
| 6 | Generalización del clasificador | `infer_operation` sobre paráfrasis con la misma intención | 1/7 combinadas |
| 7 | Validador de fidelidad | 7 reportes sintéticos fieles/infieles | 7/7 mal clasificados |
| 8 | Casos borde | Composición y validador SQL con entradas plausibles | 3 modos de falla en composición, 3 falsos positivos del validador SQL |
| 9 | PDF | `pdfinfo`, `pdftotext` y compilación del `.tex` con MiKTeX | PDF versionado ≠ `.tex`; el `.tex` compila a 1 página |
| 10 | Trazabilidad de la corrida | Lectura (sin ejecutar ni modificar) de los 3 notebooks `deliverable2_demo.ipynb` del Drive | Corrida final identificada; 2 iteraciones previas |
| 11 | Re-ejecución independiente | Colab T4, commit `dbd29b1`, mismos parámetros que el notebook (partes A–D, §3.2) | A idéntica 15/15; B reproduce D1 (15/15 salidas idénticas); C: 0/7 combinadas parafraseadas; D: 9–11/15 sin descomposición |

Sin GPU: la 2 con `python -m unittest discover -s tests`; la 3 y de la 5 a la 8 con:

```
python artifacts/auditoria/verificaciones_offline.py
```

La 1 requiere copiar `data/build_db.py` y `data/build_questions.py` a otra carpeta antes de
ejecutarlos, porque sobrescriben los archivos junto a los que están.

---

## 3. Cifras: declaradas vs. verificadas

### 3.1 Conjunto oficial (15 preguntas: 10 puntuales, 5 combinadas)

| Sistema | Puntual | Combinada | Global | Estado |
|---|---|---|---|---|
| Baseline D1 (prompt en español, 300 tokens) | 7/10 (70 %) | 0/5 | 7/15 (46,7 %) | Medido en D1 |
| Baseline D2 (prompt nuevo en inglés, 384 tokens) | 6/10 (60 %) | 0/5 | 6/15 (40 %) | ✅ verificado |
| Solución, criterio SQL | 9/10 (90 %) | 3/5 (60 %) | 12/15 (80 %) | ✅ verificado |
| Solución, extremo a extremo (SQL + respuesta + validador) | 8/10 (80 %) | 2/5 (40 %) | 10/15 (66,7 %) | ✅ verificado (pero ver A4) |
| Baseline D2, **respuesta final** (no reportado) | 6/10 | **1/5** (q14) | 7/15 | Calculado en esta auditoría |
| Solución, **respuesta final** (`answer_correct`) | 9/10 | 3/5 | 12/15 | Del JSON |

Lectura honesta de la mejora con el mismo criterio para ambos sistemas:

- **SQL:** 6/15 → 12/15 (y 7/15 → 12/15 si se compara contra la baseline de D1).
- **Respuesta final en combinadas:** 1/5 → 3/5 (q09, q11, q12). q14 pasa de acierto de la
  baseline a fallo de la solución.
- **Tiempo:** la solución tarda ~3,3× más por pregunta (18,0 s de media en las 12 resueltas
  vs 5,5 s de la baseline en T4, según el JSON); no aparece en el PDF.

### 3.2 Re-ejecución independiente en Colab (23-09-2026)

**Configuración.** Runtime T4 de Colab (cuaderno de prueba, sin guardar nada en Drive),
commit `dbd29b1` clonado desde GitHub y los mismos parámetros del notebook: NF4 de 4 bits,
cómputo bf16, decodificación greedy, `max_new_tokens=384` y 2 reintentos. Versiones:
Python 3.13.15, torch 2.11.0+cu130, transformers 5.17.0, bitsandbytes 0.50.2; snapshot del
modelo `488639f1ff808d1d3d0ba301aef8c11461451ec5`. Memoria GPU máxima: 2,4 GB. Duración
total: 21 min. Registro completo en `artifacts/auditoria/colab_rerun_2026-09-23.txt`.

| Parte | Sistema | Puntual | Combinada | Global |
|---|---|---|---|---|
| A · réplica exacta del notebook | Baseline D2 | 6/10 | 0/5 | 6/15 |
| A | Solución, criterio SQL | 9/10 | 3/5 | 12/15 |
| A | Solución, extremo a extremo | 8/10 | 2/5 | 10/15 |
| B · prompt de D1 | Baseline D1 | 7/10 | 0/5 | 7/15 |
| D · ablación | Prompt directo + esquema enriquecido, sin descomposición (criterio D2) | 10/10 | 1/5 | 11/15 |
| D | Ídem con el criterio estricto de D1 | 9/10 | 0/5 | 9/15 |
| C · 12 paráfrasis (mismo gold) | Baseline D2 | 3/5 | 0/7 | 3/12 |
| C | Solución, SQL y extremo a extremo | 5/5 | 0/7 | 5/12 |

**Lectura.**

- **A es idéntica a la corrida del 17-09 en 15/15 preguntas:** mismas salidas crudas de la
  baseline, planes, reportes, mensajes de error y banderas. Las cifras publicadas se
  reproducen en el hardware declarado.
- **B reproduce D1 carácter por carácter** (15/15 salidas idénticas, 7/15). La caída de la
  baseline a 40 % en D2 se debe solo al cambio de prompt.
- **D muestra de dónde viene la mejora en puntuales.** Basta agregar al prompt directo el
  esquema enriquecido de la solución (valores exactos de categorías y productos, y rango de
  fechas) para llegar a 9–10/10 puntuales, igual o mejor que la solución (9/10). La
  descomposición es lo que suma en combinadas: 3/5 frente a 0–1/5. Esta es justamente la
  "estrategia alternativa evaluada" que falta en el PDF. Ojo: q03 y q12 de la ablación
  solo pasan por la tolerancia a columnas extra del criterio de D2; con el criterio de D1
  no pasarían. Esa tolerancia no cambia el 12/15 de la solución, que es igual con ambos
  criterios.
- **C confirma C2.** En puntuales parafraseadas la solución generaliza: 5/5 frente a 3/5 de
  la baseline. En combinadas parafraseadas **ningún sistema acierta ninguna (0/7)**:
  - En q09-p y q12-p el modelo propuso el plan correcto en los 3 intentos y el clasificador
    lo vetó ("The question requires direct, but the plan uses growth_pct").
  - En q14-p el clasificador forzó `direct` y la solución dio la respuesta correcta en una
    sola consulta (`Zapatillas Urbanas`), pero el criterio la marca incorrecta (A2). La
    baseline también responde bien q14-p y q14-en en una consulta: a nivel de respuesta
    final, 2/7 para la baseline y 1/7 para la solución.
  - En q12-en el sistema entregó al usuario "August 2026 revenue was higher than March 2026
    revenue by 34.7%": la cifra es inventada (la real es 59,08 %). El validador la marcó como
    no fiel, pero el texto igual se muestra.
  - q14-en conserva las palabras clave, el clasificador acierta y la solución falla igual
    que en q14.
- **El ejemplo del README** ("percentage growth in total sales between the first and second
  quarter") responde +207,28 %: compara marzo contra abril–junio y el reporte es el volcado
  de respaldo. Con la definición de trimestre del proyecto (q09) la respuesta es +60,13 %.

---

## 4. Hallazgos

Severidad: **Crítico** = puede anular un criterio de la rúbrica o invalida lo entregado;
**Alto** = resta puntos con alta probabilidad; **Medio** = debilidad visible para quien
revise; **Bajo** = higiene.

### C1 · Crítico — El PDF versionado no corresponde al `.tex` ni a los resultados

- **Qué pasa.** `docs/deliverable2.pdf` dice "Structured solution 20.0% 20.0% 20.0%",
  "Failure case: q01: the solution failed its correctness checks" y "The Measured results
  from the committed Colab execution.". El `.tex` dice 90 % / 60 % / 80 %, agrega la línea de
  extremo a extremo y el fallo q04.
- **Por qué ocurrió.** El PDF se compiló el 17-09 a las 02:55, antes de la corrida final
  (03:29). La última celda del notebook final descargó `docs/deliverable2.pdf` desde el ZIP
  subido, sin recompilarlo (la celda 7 solo actualiza el `.tex`).
- **Impacto.** El PDF es lo que se evalúa. Con esas cifras la solución aparece peor que la
  baseline en puntuales, y el PDF contradice el JSON del repositorio (trazabilidad).
- **Corrección.** Recompilar después de aplicar los cambios de contenido de este informe
  (el `.tex` actual compila a 1 página con MiKTeX). Corregir el desborde de 30 pt en el
  párrafo "Reproduction" (rutas en `\texttt` que no se cortan; usar `\path{}` o partir la
  línea).

### C2 · Crítico — Ajuste al conjunto de evaluación no declarado

- **Qué pasa.** La operación de composición no la decide el modelo sino
  `infer_operation` (`src/sql4business/pipeline.py:228`), con reglas copiadas de la
  redacción de cada pregunta combinada:

  | Regla | Pregunta de la que sale |
  |---|---|
  | `"stock"` + `"ingreso"` → `filter_then_rank` | q14 |
  | `"lider"`, `"cada trimestre"`, `"producto top"` → `compare_equal` | q10 |
  | `"crecimiento porcentual"` → `growth_pct` | q09 |
  | `"en que porcentaje"` → `growth_pct` | q12 |
  | `"cuantas unidades totales"` + `"cuantas de esas"` → `share_pct` | q11 |

  `_validate_plan` rechaza cualquier plan cuya operación difiera de la del clasificador
  (`pipeline.py:114`) y toda pregunta recibe una etiqueta (por defecto `direct`), así que
  **una pregunta combinada redactada de otra forma no puede componerse**, aunque el modelo
  proponga la operación correcta.
- **Otras reglas derivadas de fallos observados en el set:** en el prompt del planificador
  (`src/sql4business/model.py:114-124`): `AVG(sales.amount)` para el "ingreso promedio por
  venta" (el error de la baseline en q08), `strftime('%Q')` (error de q10), "total units
  first" (q11) y la estructura de `filter_then_rank` que replica el SQL gold de q14; en
  `sql_tools.py:78` el nombre de CTE `quarterly_sales`; en `sql_tools.py:193` los alias
  `"notebook"` y `"ollas"` (productos de q01 y q05).
- **Historia.** Hubo al menos tres iteraciones en Colab sobre las mismas 15 preguntas
  (ZIPs `deliverable2-date-fix`, `evaluation-corrections`, `evaluation-final-v3`); una
  corrida intermedia dio 20 % (la que quedó en el PDF). Varios fallos observados se
  corrigieron con reglas específicas: el fallo de q01 en la prueba de humo ("A direct
  operation must contain one step") derivó en la normalización de pasos, y los errores de
  la baseline (`%Q`, `AVG/SUM`, fechas 2023) aparecen como reglas del prompt.
- **Evidencia de fragilidad.** El clasificador acierta 15/15 en el set y 1/7 en paráfrasis
  combinadas con la misma intención (`artifacts/auditoria/paraphrases.json`); la única que
  acierta es la que conserva las palabras `stock` y `revenue`. En la re-ejecución la
  solución acertó 0/7 de esas combinadas; en dos de ellas el modelo había propuesto el plan
  correcto y el clasificador lo vetó, y en otra el sistema reportó un porcentaje inventado
  (§3.2).
- **Impacto.** Rúbrica, *Continuidad*: una demostración que resuelve en silencio un
  problema más fácil que el especificado recibe cero en ese criterio. *Evidencia de
  mejora*: el 80 % es una estimación dentro de la muestra (in-sample), no de
  generalización.
- **Corrección.**
  1. Declararlo en el PDF y el README: el clasificador y varias reglas del prompt se
     escribieron mirando las 15 preguntas; los resultados son in-sample.
  2. Reportar además el set de paráfrasis (mismo gold, redacción distinta) con el mismo
     criterio para baseline y solución (§3.2).
  3. Técnicamente: usar el clasificador como sugerencia y no como veto (aceptar la
     operación del modelo si es válida), o reemplazarlo por una llamada de clasificación al
     propio modelo, y ampliar el vocabulario (porcentaje, variación, participación, share,
     growth, reposición…).

### A1 · Alto — La baseline cambió respecto del Deliverable 1 sin declararlo

- **Qué pasa.** La baseline de D2 usa un prompt nuevo en inglés (`model.py:61`) y 384
  tokens; D1 usó un prompt en español y 300 tokens. Resultado: 7/15 (46,7 %) en D1 contra
  6/15 (40 %) en D2. Cambian q03 (✗→✓), q07 (✓→✗) y q15 (✓→✗): la instrucción nueva "use …
  the dates … present in the question" llevó al modelo a inventar rangos de 2023 en
  preguntas sin fecha (q07, q15).
- **No es el criterio:** las salidas de D1 re-puntuadas con el criterio de D2 siguen en
  7/15, y las de D2 con el criterio de D1 siguen en 6/15.
- **Inconsistencia visible.** El PDF justifica el modelo con "matches the best local
  baseline accuracy (46.7%)" y dos párrafos después muestra 40,0 % para el mismo modelo.
- **Corrección.** Declarar el cambio en una frase, o mejor, reportar ambas baselines y
  comparar la solución contra la más fuerte (la de D1). La mejora se mantiene: 7/15 → 12/15.
  Re-ejecutado el 23-09 en T4, el prompt de D1 reproduce las 15 salidas de D1 carácter por
  carácter.

### A2 · Alto — El criterio penaliza respuestas correctas en una sola consulta, y solo a la baseline

- **Qué pasa.** En combinadas, "correcto" exige reproducir cada conjunto intermedio del
  gold (`evaluation.py:58`). En q14 la baseline respondió con una sola consulta correcta,
  que devuelve `('Zapatillas Urbanas', 6198450)`, y quedó como incorrecta porque no
  reproduce el ranking completo de los 10 productos. Lo mismo ocurrió en D1 con Qwen-3B y
  Qwen-7B. La solución se evalúa además por respuesta final (`answer_correct`); la baseline
  no.
- **Impacto.** "0 % en combinadas" (D1 y D2) está sobrestimado: a nivel de respuesta final
  la baseline logra 1/5. La comparación usa el mismo criterio SQL para ambos, pero reportar
  la métrica de respuesta solo para la solución favorece a la solución.
- **Además:** el gold de q11 es `share_pct`, pero la pregunta pide dos conteos, no un
  porcentaje (esto provoca un falso negativo en A4).
- **Corrección.** Mantener el criterio de D1 por continuidad, pero agregar la métrica de
  respuesta final para ambos sistemas y explicar que el criterio SQL mide la
  descomposición, no solo la respuesta.

### A3 · Alto — Regresiones no reportadas

- **q04** (puntual): la baseline acierta con una subconsulta sobre `category`; la solución
  falla los 3 intentos con `no such column: products.category`.
- **q14** (combinada): la baseline da la respuesta final correcta; la solución falla los 3
  intentos ("requires exactly two steps").
- El skill de evaluación del propio repo pide "reportar también cualquier regresión en
  las preguntas puntuales". El PDF no menciona ninguna.
- **Corrección.** Una línea en el PDF: "Regressions: q04 and q14", con su causa (M1).

### A4 · Alto — El validador de fidelidad no mide fidelidad

- **Qué pasa.** `_validate_report` (`pipeline.py:178`) solo comprueba que el valor clave
  aparezca como subcadena. No revisa otras cifras, ni la dirección del cambio, ni la
  afirmación "cambió el líder"; no acepta números en palabras ni redondeos. El campo
  `claims` se pide y nunca se valida. Si el modelo rompe el formato, el reporte se
  reemplaza por un volcado `Verified result: {...}` (`pipeline.py:172`) que pasa la
  validación automáticamente.
- **En la corrida real:**
  - q09 pasa con "Ventas aumentaron un 60.13% entre marzo y agosto", pero la comparación es
    trimestre marzo–mayo vs junio–agosto (el 59,08 % "de marzo a agosto" es q12). Es
    engañoso.
  - q11 falla con "En total se vendieron 1655 unidades … de las cuales 488 corresponden a
    Electrónica", que es exactamente lo que se preguntó, porque no incluye 29,49 %.
  - q13 falla con "La categoría Ropa tiene dos productos distintos" (correcto, en palabras).
  - q03 cuenta como fiel, pero su "reporte" es el volcado de respaldo: el reportero falló.
- **Pruebas sintéticas:** 7/7 mal clasificadas (acepta dirección invertida, cifras
  inventadas y "2" dentro de "2026"; rechaza redondeos a 1 decimal y números en palabras).
- **Adjudicación manual** de los 12 reportes: 10 fieles (q01, q02, q05, q06, q07, q08, q11,
  q12, q13, q15), 1 engañoso (q09), 1 sin reporte del modelo (q03). El total de extremo a
  extremo sigue siendo 10/15, pero cambian las preguntas que pasan.
- **Idioma:** 9 de 12 reportes están en español, aunque el prompt exige inglés
  (`model.py:132`) y el PDF promete "verified English report".
- **Corrección.** Extraer todas las cifras del reporte y verificar cada una contra los
  valores de la respuesta (con tolerancia de redondeo); verificar palabras de dirección
  (`growth_pct`) y la afirmación de cambio (`compare_equal`); contar el respaldo como fallo
  del reporte (mostrando igual la respuesta verificada); pedir cifras en dígitos; declarar
  la adjudicación manual en el PDF.

### A5 · Alto — Reproducibilidad del repositorio

1. **ZIP obsoleto.** `Asistente-SQL-4-Business.zip` (01:42) es anterior al código: no trae
   `_validate_date_literals`, `infer_operation` ni la normalización de pasos. La celda 3 del
   notebook tiene `assert` sobre esas funciones: **con ese ZIP el notebook falla**. La
   corrida real usó `…-evaluation-final-v3.zip`, que no está en el repositorio.
2. **Instrucciones.** El README dice "upload or clone this repository", pero el notebook
   solo acepta subir un ZIP (`files.upload()`) y no explica cómo generarlo. También lo
   presenta como "Colab/VS Code demonstration", pero depende de `google.colab`.
3. **Dos caminos no equivalentes.** `scripts/evaluate_baseline_solution.py` (la alternativa
   del README y del PDF) usa `max_new_tokens=512` por defecto; el notebook usa 384.
4. **Versiones sin fijar.** `requirements.txt` no fija `torch` ni versiones exactas; la
   decodificación greedy solo es reproducible con las mismas versiones. Hoy la
   reproducción es exacta (§3.2), pero conviene fijar las versiones de esa corrida
   (torch 2.11.0, transformers 5.17.0, bitsandbytes 0.50.2) para que lo siga siendo.
5. **Evidencia fuera del repo.** El notebook ejecutado con salidas solo existe en el Drive;
   `docs/deliverable2_demo.ipynb` es un duplicado sin salidas.
6. **Enlace del repositorio.** El PDF de D1 enlaza `aredhel-jmze/Asistente-SQL-4-Business`,
   cuyo `main` sigue en `03d3fe2` (01-09) sin el Deliverable 2 y sin PR abierto. El D2 solo
   está en el fork `VicenteSonez/…`.

- **Corrección.** Cambiar la primera celda por `git clone` del repositorio en un tag
  (`d2-final`) y dejar la subida de ZIP como alternativa; borrar el ZIP obsoleto; fijar las
  versiones de la corrida; guardar el notebook ejecutado con salidas; fusionar el fork en
  el upstream (PR) o citar explícitamente el fork en PDF y README.

### M1 · Medio — El caso de fallo describe el síntoma, no la causa

- El texto del PDF se genera por coincidencia de cadenas (`scripts/update_deliverable2_tex.py:38-45`):
  "the generated SQL referenced a column unavailable in the selected table". La rúbrica
  pide explicar *por qué* falla.
- **Análisis causal propuesto (q04):** el modelo filtra por `products.category` sin hacer
  `JOIN` con `products`. La regla del prompt "Use products.category for category filters"
  (`model.py:118`) empuja a usar el nombre calificado sin enseñar el join; el reintento solo
  devuelve el mensaje de error y, con decodificación greedy, el modelo cambia la redacción
  pero no el error: en la re-ejecución los 3 intentos dieron 2 planes distintos, ambos con
  `products.category` sin `JOIN`. La baseline resolvió q04 con una subconsulta, así que el
  fallo lo introduce la solución.
- **q14, el caso más ilustrativo:** el primer plan era casi correcto (2 pasos), pero el
  paso 2 filtraba con `WHERE p.product_id IN (SELECT product_id FROM step_1)`. El validador
  lo rechaza porque cada paso corre en una conexión nueva, y ante ese error el modelo
  "reparó" el plan eliminando el paso 2, lo que produce "requires exactly two steps" en los
  intentos 2 y 3. La reparación empeora el plan. Materializar los resultados de cada paso
  como tablas temporales, o sugerir en el error "inline the subquery", probablemente
  resolvería q14.
- **q10:** el intento 1 usa `strftime('%Q')` (rechazado); los intentos 2 y 3 agrupan por mes
  llamándolo "quarter" y el paso 2 consulta `FROM step_1`.
- **Reintentos:** en ambas corridas ninguna de las 12 respuestas exitosas usó un reintento,
  y las 3 fallidas agotaron los 3 intentos: el componente "bounded repair" no rescató
  ninguna pregunta.
- **Corrección.** Tres o cuatro líneas con este análisis en el PDF. Mejoras posibles:
  plantilla de `JOIN` en la pista, reparación dirigida (si aparece `no such column:
  products.X`, sugerir el join) y muestreo con temperatura en los reintentos.

### M2 · Medio — Fallos silenciosos en la composición

- `composition.py:102`: si el paso de ranking devuelve solo ids, `row[1]` lanza
  `IndexError`, que no captura el bucle de reintentos (`pipeline.py:89`): la pregunta se
  aborta sin reintentar.
- `composition.py:100`: "ordenar por la última columna numérica" reordena por
  `product_id` si la consulta devuelve `(name, product_id)` → ganador `Cafe Molido 500g`
  en vez de `Zapatillas Urbanas`.
- `compare_equal` (`composition.py:61`) toma la primera columna de la primera fila: si el
  modelo devuelve `(revenue, name)`, compara montos.
- No se activaron en la corrida medida, pero son modos de falla sin error visible.
- **Corrección.** Validar la forma de cada resultado según la operación y lanzar
  `ValueError` si no calza (así aplica el reintento); no reordenar por columnas id.

### M3 · Medio — Falsos positivos del validador SQL

- `FORBIDDEN_SQL` (`sql_tools.py:13`) rechaza la función `REPLACE()` y palabras reservadas
  dentro de literales (`WHERE name <> 'Update'`).
- `_validate_date_literals` (`sql_tools.py:111`) rechaza filtros válidos más amplios que los
  datos (`sale_date >= '2026-01-01'` devuelve el total correcto y se rechaza).
- También se aplica a la baseline. Verificado: en esta corrida no cambió su puntaje (todas
  las consultas rechazadas usaban fechas de 2023 realmente erróneas), pero conviene
  declararlo.
- **Corrección.** Quitar literales antes de buscar palabras reservadas, permitir `REPLACE(`
  como función y rechazar fechas solo si el filtro excluye todos los datos.

### M4 · Medio — Documento técnico incompleto

Casi la mitad de la página está vacía y faltan elementos que la rúbrica o el curso piden:

- Equipo, URL del repositorio y URL del video.
- "Model and version": falta la configuración (NF4 4-bit, cómputo bf16, greedy,
  `max_new_tokens=384`) y las versiones de librerías.
- "Alternative strategies evaluated": solo menciona la baseline. Se pueden agregar la
  baseline de D1 (7/15) y la ablación "prompt directo + esquema enriquecido" (9–11/15,
  §3.2), que además explica qué parte de la intervención produce cada mejora.
- Costo: ~3,3× más tiempo por pregunta.
- Límites: hoy son genéricos; agregar C2, A4 y el análisis de M1.
- El "diagrama" es una caja de texto con flechas; un diagrama TikZ cabe en el espacio libre.
- Detalles: "Puntual/Combinada" en un documento en inglés; "Concepcion" sin tilde.

### M5 · Medio — README

- El checklist sigue en el estado de D1. El README anunciaba "Fine-tuning QLoRA sobre el
  modelo principal (próximo entregable)" y el PDF de D1 describe el plan de fine-tuning con
  bases de BIRD; D2 no lo hace. No es obligatorio, pero hay que declarar el cambio de plan
  (rúbrica de continuidad).
- Faltan: enlace al video y qué comando corresponde a cada parte, versión de Python, tiempo
  esperado (≈7,3 min la comparación de 15 preguntas en T4) y cómo armar el ZIP (o
  reemplazarlo por `git clone`, ver A5).
- El ejemplo de una sola pregunta del README ("percentage growth in total sales between
  the first and second quarter") es ambiguo: el sistema compara marzo contra abril–junio,
  responde +207,28 % y el reporte es el volcado de respaldo (§3.2). Conviene usar una
  pregunta con los meses explícitos, o una de las paráfrasis.

### Bajos

- **B1.** Código muerto o no validado: `answer_claim_values` (`composition.py:131`),
  `report_fields`, `claims` y `question_type` del plan (q14 dice "puntual" con
  `filter_then_rank`).
- **B2.** Duplicados y confusión: `docs/deliverable2_demo.ipynb` duplica el notebook;
  "Deliverable 2.pdf" (enunciado) vs "deliverable2.pdf" (entrega); el ZIP incluye
  `__pycache__` de Python 3.14.
- **B3.** Archivos sin versionar que **no** deben subirse: `docs/Claude Setup.exe`
  (instalador de 7 MB) y `docs/MER.png` (diagrama ER de un sistema de arriendo de
  vehículos, ajeno al proyecto).
- **B4.** `update_deliverable2_tex.py` divide por cero si un grupo queda vacío y elige como
  caso de fallo el primero que encuentra.
- **B5.** Los tests no cubren el validador de fidelidad, el clasificador de intención ni
  los casos borde de composición.

### Lo que está bien

- Elección de modelo coherente con la evidencia y con el criterio de economía.
- Arquitectura clara: plan JSON → SQL de solo lectura (`PRAGMA query_only`) → composición
  determinista → reporte; la aritmética sale del modelo.
- Trazas completas por pregunta, sin sustituir resultados gold tras un fallo; los fallos
  quedan registrados.
- Datos sintéticos reproducibles con semilla y gold verificable.

---

## 5. Riesgo por criterio de la rúbrica

| Criterio (10 pts c/u) | Estado actual | Riesgo | Acción |
|---|---|---|---|
| Continuidad con D1 | Misma tarea y mismo criterio SQL; baseline cambiada, reglas in-sample y abandono del QLoRA sin declarar | **Alto** | Declarar C2, A1 y M5 |
| Ejecución demostrada | Corre en T4 (verificado); el video no está enlazado; la demo del notebook usa q09, que la solución acierta | Medio | Video con una entrada no favorable (una paráfrasis o q04), con la baseline visible en la misma entrada y trazable al commit |
| Evidencia de mejora | 15 preguntas y mismo criterio SQL; mejora real y reproducible, pero in-sample (0/7 en combinadas parafraseadas); métrica de respuesta solo para la solución | Medio-alto | Agregar paráfrasis, ablación y métrica de respuesta para ambos sistemas |
| Lectura de límites | Fallo real (q04), sin causa | Medio-alto | Análisis causal (M1) y regresiones (A3) |
| Economía de modelo | 3B, el menor | Bajo | Ninguna (se acredita si se cumplen los demás) |
| Repositorio y reproducibilidad | ZIP obsoleto rompe el notebook; upstream sin D2; PDF obsoleto | **Alto** | A5 y C1 |

---

## 6. Plan de corrección priorizado (antes del 30-09)

1. **Enlace oficial del repo (15 min).** Abrir PR del fork al upstream o decidir citar el
   fork; crear el tag `d2-final` al terminar.
2. **Reproducibilidad (30–45 min).** Primera celda con `git clone` del tag; borrar el ZIP
   obsoleto y `docs/deliverable2_demo.ipynb`; fijar versiones; no subir
   `docs/Claude Setup.exe` ni `docs/MER.png`.
3. **Declaraciones en PDF y README (1–2 h).** Cambio de baseline (A1), reglas in-sample
   (C2), regresiones (A3), métrica de respuesta para ambos sistemas (A2), análisis causal
   del fallo (M1), costo, equipo, URLs y configuración del modelo (M4).
4. **Evidencia adicional (ya disponible).** Tablas de §3.2: baseline de D1, ablación y
   paráfrasis, con el análisis causal de q14 (M1). Si se corrige el código, volver a correr
   las paráfrasis con `artifacts/auditoria/audit_colab.py` y reportar ambos resultados.
5. **Código (opcional, 2–3 h).** C2 (clasificador como sugerencia), A4 (validador),
   M2/M3 y tests. **Si se cambia código, repetir la corrida completa en T4** y regenerar
   JSON y PDF, conservando la corrida actual como v1.
6. **PDF (15 min).** Recompilar, verificar 1 página y sin desbordes; subir el notebook
   ejecutado con salidas.
7. **Video.** Grabar después del punto 6, con una entrada no elegida para favorecer a la
   solución y la baseline visible en la misma entrada.

---

## 7. Cómo reproducir esta auditoría

- Los scripts de la auditoría ya no existen como archivos aparte. Sus verificaciones se
  incorporaron al repositorio:
  - las pruebas del validador, la composición y el SQL son tests en `tests/`;
  - la re-puntuación de la baseline de v1 con la métrica de respuesta está en
    `tests/test_evaluation.py`;
  - la evaluación con baseline de D1, alternativa y paráfrasis la hace
    `scripts/evaluate.py`.
- La re-ejecución de v1 del 23-09 (código del commit `dbd29b1`) quedó registrada en
  `artifacts/auditoria/colab_rerun_2026-09-23.txt`, y los resultados originales de v1 en
  `results/deliverable2_v1.json`.

## Anexo A — Resultados por pregunta (corrida versionada)

| ID | Tipo | Baseline D1 | Baseline D2 | Solución SQL | Respuesta | Validador | Adjudicación manual del reporte | Intentos / error |
|---|---|---|---|---|---|---|---|---|
| q01 | P | ✓ | ✓ | ✓ | ✓ | ✓ | fiel (EN) | 1 |
| q02 | P | ✗ | ✗ (2023, "Electronics") | ✓ | ✓ | ✓ | fiel (ES) | 1 |
| q03 | P | ✗ | ✓ | ✓ | ✓ | ✓ | **sin reporte del modelo** | 1 |
| q04 | P | ✓ | ✓ | ✗ | — | — | — | 3 / `no such column: products.category` |
| q05 | P | ✓ | ✓ | ✓ | ✓ | ✓ | fiel (ES) | 1 |
| q06 | P | ✓ | ✓ | ✓ | ✓ | ✓ | fiel (ES) | 1 |
| q07 | P | ✓ | ✗ (2023) | ✓ | ✓ | ✓ | fiel (EN) | 1 |
| q08 | P | ✗ | ✗ (AVG/SUM) | ✓ | ✓ | ✓ | fiel (ES) | 1 |
| q09 | C | ✗ | ✗ (2023) | ✓ | ✓ | ✓ | **engañoso** ("marzo y agosto") | 1 |
| q10 | C | ✗ | ✗ (`%Q`) | ✗ | — | — | — | 3 / referencia entre pasos |
| q11 | C | ✗ | ✗ (2023, "Electronics") | ✓ | ✓ | ✗ | **fiel** (falso negativo) | 1 |
| q12 | C | ✗ | ✗ | ✓ | ✓ | ✓ | fiel (ES) | 1 |
| q13 | P | ✓ | ✓ | ✓ | ✓ | ✗ | **fiel** ("dos"; falso negativo) | 1 |
| q14 | C | ✗* | ✗* | ✗ | — | — | — | 3 / plan de 1 paso (tras rechazarse `FROM step_1` en el intento 1) |
| q15 | P | ✓ | ✗ (2023) | ✓ | ✓ | ✓ | fiel (ES) | 1 |

\* La consulta de la baseline devuelve la respuesta final correcta (`Zapatillas Urbanas`),
pero no reproduce los conjuntos intermedios del gold.

## Anexo B — Línea de tiempo del 17-09-2026 (hora Chile)

| Hora | Evento | Fuente |
|---|---|---|
| 01:42 | Se arma el ZIP que quedó versionado (código anterior) | Fechas internas del ZIP |
| 02:05 | Corrida con `…deliverable2-date-fix.zip`: prueba con q01 falla ("A direct operation must contain one step") | Notebook en Drive |
| 02:55 | Se compila el PDF con solución 20/20/20 y fallo q01 (el que quedó versionado) | Metadatos del PDF |
| 03:04 | Corrida con `…evaluation-corrections.zip`: se detiene en el `assert` de la celda 3 | Notebook en Drive |
| 03:29–03:38 | **Corrida final** con `…evaluation-final-v3.zip` en T4: 60/90/80 y 0/60/40 | Notebook en Drive |
| 03:38 | Descarga de JSON, `.tex`, PDF (el del ZIP, sin recompilar) y notebook | Notebook en Drive |
| 03:41 | Última edición del `.tex` | Fecha del archivo |
| 03:44 | Commit `dbd29b1` | Git |

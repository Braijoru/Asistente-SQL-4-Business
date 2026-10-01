# Artefactos de trabajo

Esta carpeta concentra el contexto y las skills de trabajo para desarrollar el
Deliverable 2 de SQL4Business. No reemplaza al codigo fuente ni a los datos;
los documentos apuntan a las fuentes existentes del repositorio.

## Contenido

- `project-context.md`: contexto canonico del proyecto, estado actual, datos,
  baseline y decisiones vigentes de Deliverable 2.
- `deliverable-2-brief.md`: lectura verificada de `docs/enunciado-deliverable2.pdf`,
  organizada por pagina y requisito.
- `skills/deliverable-2-implementation.md`: skill para disenar e implementar
  la primera solucion end-to-end.
- `skills/evaluation.md`: skill para comparar baseline y solucion con el mismo
  criterio y conjunto de entradas.
- `skills/reproducible-demo.md`: skill para preparar el documento tecnico, el
  video y la reproduccion desde el repositorio.
- `auditoria-deliverable-2.md`: auditoria de la version v1 del Deliverable 2
  (commit `dbd29b1`) y estado de las correcciones aplicadas en v2.
- `auditoria/colab_rerun_2026-09-23.txt`: registro de la re-ejecucion
  independiente de v1 en Colab T4 usada como evidencia en la auditoria.

## Fuentes revisadas

- `README.md`
- `docs/deliverable1.tex`
- `docs/enunciado-deliverable2.pdf`
- `data/build_db.py`
- `data/build_questions.py`
- `data/questions.json`
- `notebooks/baseline_eval.ipynb`
- `results/baseline_comparison.csv`
- `results/baseline_results.json`

## Regla de uso

Antes de cambiar la arquitectura o afirmar un resultado, consultar primero
`project-context.md` y `deliverable-2-brief.md`. Si una decision cambia, debe
actualizarse el contexto y quedar separada de los hechos ya medidos.

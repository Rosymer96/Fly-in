# CLAUDE.md — Reglas de evaluación de Fly-in

Fuente: fly-in.subject.pdf v1.6. "p." = página del PDF (no la impresa).

## Código
- Python 3.10 o superior (p.6, III.1).
- Cumplir flake8 sin errores (p.6, III.1; p.9, V).
- Type hints en parámetros, retornos y variables, con `typing` (p.6).
- Docstrings PEP 257 (estilo Google o NumPy) en funciones y clases:
  propósito, parámetros y retorno (p.6).
- Gestionar excepciones con try-except; un crash en la revisión = no funcional (p.6).
- Usar context managers para ficheros y recursos; sin fugas (p.6).
- Comentarios del código en inglés (regla del usuario, no del subject).
- Variables, funciones, clases, docstrings y comentarios: SIEMPRE en inglés;
  si no, suspenso (regla del usuario, no del subject).

## Mypy y flake8
- `make lint` ejecuta: `flake8 .` y
  `mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs` (p.7).
- `make lint-strict`: `flake8 .` y `mypy . --strict` (p.7). El subject lo marca
  opcional, pero el usuario lo exige siempre. Si es imposible pasarlo,
  preguntar al usuario y decidir caso por caso (nunca silenciarlo solo).
- Todas las funciones deben pasar mypy sin errores (p.6).

## Restricciones
- Prohibida cualquier librería de grafos (networkx, graphlib, etc.) (p.9).
- Proyecto completamente typesafe y completamente orientado a objetos;
  hay que demostrarlo en la peer review (p.9).
- Decisión propia: toda la lógica (parser, simulación, pathfinding, visual) en
  clases, sin funciones sueltas. Solo un punto de entrada mínimo que crea un
  objeto y lo ejecuta. Sin estado: `@staticmethod` o `@classmethod`.
- Pathfinding propio: el subject pide implementarlo (p.23).

## Mapa y parser (p.10-11, p.14)
- Primera línea: `nb_drones: <entero positivo>`; cualquier nº de drones.
- Un solo `start_hub` y un `end_hub`; coordenadas enteras; nombres únicos sin guiones ni espacios.
- Conexiones solo entre zonas ya definidas; sin duplicados (a-b == b-a).
- Zonas válidas: normal, blocked, restricted, priority; otra = error de parseo.
- `max_drones` y `max_link_capacity`: enteros positivos (por defecto 1).
- `max_drones` se ignora en start y end (no es error).
- Decisión propia (no del subject): rechazar metadata desconocida y conexiones a-a.
- Metadatos sintácticamente válidos; tags en cualquier orden; `#` = comentario.
- Cualquier otro error: parar y dar mensaje claro con línea y causa.
- Colores: una palabra cualquiera, sin lista fija.

## Simulación (p.12-16)
- Costes: normal 1, priority 1 (preferida), restricted 2, blocked prohibida.
- Zona: 1 dron por defecto o `max_drones`; start y end sin límite.
- Hacia zona restricted: el dron debe llegar en el turno siguiente; no espera en la conexión.
- Quien sale libera capacidad en ese mismo turno.
- Respetar capacidad de zonas y de conexiones en todo momento.
- Debe gestionar: reparto entre rutas, esperas, conflictos y deadlocks.
- Salida: una línea por turno, movimientos separados por espacio,
  `D<ID>-<zona>` o `D<ID>-<conexión>` si siguen en vuelo.
- Los drones quietos se omiten; los entregados dejan de listarse.
- Termina cuando todos llegan al end.
- Feedback visual obligatorio: terminal con colores y/o interfaz gráfica (p.12).

## Rendimiento (p.18)
- Easy < 10 turnos, Medium 10-30, Hard < 60 (esperado).
- Objetivos por mapa: ver tabla p.18 (ej. Ultimate challenge ≤ 45).
- Challenger (45 turnos) y rendimiento exacto son bonus; el bonus solo se
  revisa si todo lo obligatorio está cumplido (p.22).

## Entregables
- Todos los ficheros en la raíz del repo (p.23).
- Debe incluir: parser, motor de simulación, pathfinding, sistema visual y salida con el formato indicado (p.23).
- Makefile con reglas: `install`, `run`, `debug` (pdb), `clean`
  (`__pycache__`, `.mypy_cache`), `lint`; `lint-strict` opcional (p.6-7).
- Ejecución prevista (decisión del usuario): `python3 fly_in.py <map.txt>` (fichero principal: fly_in.py; clase principal: `Simulator` en simulator.py);
  el nombre del mapa varía. `make run` debe pasar el mapa como argumento.
- `.gitignore` que excluya artefactos de Python (p.7).
- Tests (pytest/unittest) recomendados; no se entregan ni puntúan (p.7).
- README.md en inglés, en la raíz (p.21):
  - Línea 1 en cursiva: *This project has been created as part of the 42 curriculum by <login>.*
  - Secciones: Description, Instructions, Resources (incluye uso de IA: tareas y partes).
  - Algoritmo e implementación detallados; visualización documentada;
    ejemplo de entrada y salida.

## Suspender el proyecto (riesgos)
- Código no en inglés (variables, funciones, comentarios), según el usuario.
- Crash por excepción no controlada en la revisión = no funcional (p.6).
- No poder explicar el código generado con IA = suspenso (p.5).
- Pueden pedir explicar, escribir o modificar código en la evaluación (p.23-24).
- Los mapas de evaluación pueden diferir de los del subject (p.23).
- Solo se evalúa lo que esté en el repositorio (p.23).

## Forma de trabajar
1. Antes de tocar un archivo, explícame qué vas a cambiar y por qué, y espera mi aprobación.
2. Haz cambios pequeños, uno cada vez. No regeneres archivos completos.
3. No escribas la solución completa. Guíame, dame pistas o muéstrame un ejemplo pequeño.
4. Explícame en español el razonamiento de cada cambio, porque tengo que entender y explicar mi código en la evaluación.
5. Antes de proponer un cambio, comprueba que cumple las reglas de este archivo (mypy, flake8, comentarios en inglés, etc.).

## Eficiencia
- Lee el PDF una sola vez, en este paso. No lo vuelvas a leer salvo que yo lo pida; usa este archivo.
- Trabaja solo con los archivos y líneas que yo indique con @. No explores el resto del repo sin preguntarme.
- Respuestas concisas: muéstrame solo lo que cambia (diff), no archivos completos ni código que no se modifica.
- Antes de ejecutar comandos largos o de leer varios archivos, dime el plan en 3 líneas y espera mi aprobación.

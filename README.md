# Parcialito BD — práctica de SQL

App local para practicar el parcialito de Base de Datos con la base `universidad` de la cátedra.
Tiene 113 ejercicios al estilo del **TP1** y de la **Clase Semana 10**, y los corrige en el momento contra tu MySQL.

## Cómo abrirla

Hacé **doble clic en `iniciar.command`** (o ejecutá `./iniciar.command` en la Terminal).
Se abre el navegador en http://127.0.0.1:5050. Dejá la ventana de la Terminal abierta mientras practicás y cerrala con Ctrl+C.

La primera vez el script prepara Python e importa `BD-Universidad.sql` en bases propias de la app.
Ya está todo configurado en esta Mac.

> La app usa un usuario de MySQL propio (`parcialito`) que solo puede tocar las bases `parcialito_*`.
> Tu base `universidad` de Workbench **no se toca**.

## Qué tiene

| Sección | Para qué sirve |
|---|---|
| **Inicio** | Plan de estudio en orden, avance y cuenta regresiva al parcialito. |
| **Ejercicios** | 113 ejercicios. Entran en el parcialito: básicas, JOINs, GROUP BY, problemáticas de dominio, subconsultas y vistas. Aparte, como práctica extra: DML y DDL. |
| **Simulacro** | Ejercicios al azar con reloj, sin pistas ni corrección hasta entregar. Al final te da la nota y la solución de cada uno. |
| **Consola SQL** | Para escribir cualquier consulta, como en Workbench. Por defecto los cambios se deshacen. «Restaurar base» vuelve todo a los datos originales. |
| **Esquema (DER)** | Diagrama interactivo: columnas, valores de los ENUM, relaciones y datos de ejemplo. |
| **Machete** | Método para encarar los ejercicios, patrones (ausencia/presencia, HAVING, promedio de conteos, vistas…), valores ENUM y errores típicos. Cada ejemplo se puede probar. |
| **Mi progreso** | Qué secciones dominás y cuáles conviene repasar. |

## Cómo corrige

- **SELECT y vistas:** compara tu resultado con el de la solución oficial. No importan los alias, el orden de las columnas ni que agregues columnas de más. Te dice si faltan o sobran filas, si hay repetidas (falta DISTINCT) o si el orden está mal.
- **Casos borde:** en los ejercicios de «los que no tienen…» también prueba tu consulta con datos extra. Por ejemplo, docentes sin comisiones o aulas sin uso, que en la base original no existen. Así una consulta mal hecha que da 0 filas no pasa por casualidad.
- **Enunciados ambiguos:** acepta todas las interpretaciones razonables, por ejemplo «actualmente» = estado distinto de `'Baja'`.
- **DML:** se ejecuta en una transacción que se deshace al terminar. Se compara el estado final de los datos y se muestra qué filas cambiaron.
- **DDL:** se ejecuta sobre una copia temporal de la estructura. Revisa la estructura resultante y prueba que las restricciones funcionen (CHECK, UNIQUE, FK).
- **Errores de MySQL:** se explican en castellano. Si escribiste mal una columna, te sugiere la correcta.

Atajos del editor: `⌘↵` ejecutar · `⌘⇧↵` corregir · `Ctrl+Espacio` autocompletar · `⌘/` comentar.

## Estructura

```
iniciar.command        lanzador
app/server.py          servidor web (Flask) + API
app/grader.py          motor de ejecución y corrección
app/errores.py         explicaciones de errores de MySQL
app/setup_db.py        importa el dump y crea la base de práctica
app/ejercicios/*.py    banco de ejercicios (uno por sección) y casos borde
app/validar.py         verifica todo el banco contra la base: python -m app.validar
app/static/            frontend (Vue 3 + CodeMirror, sin necesidad de internet)
docs/                  guía para escribir ejercicios nuevos
```

Bases que crea en tu MySQL:
- `parcialito_uni`: copia intacta del dump.
- `parcialito_sandbox`: donde corren tus consultas.
- `parcialito_app`: tu progreso.

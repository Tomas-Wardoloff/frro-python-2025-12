# Q-Sec — Estado del refactor

> Documento de trabajo para el equipo. Última actualización: 2026-08-25.
> Rama `TPI`, seis commits. **Todavía sin pushear.**

---

## ⚠️ Leé esto primero

**Antes de este refactor, correr `pytest tests/` borraba `qsec.db`**, y los tests
igual daban verde. Lo verifiqué con el código original en una copia limpia del
repo: 29 tests en verde y la base sin tablas al terminar. A cualquiera que haya
corrido la suite localmente se le borró la base sin ningún aviso.

**Causa:** `app.py` creaba la aplicación como objeto global y llamaba a
`db.create_all()` a nivel de módulo, con lo que el engine de SQLAlchemy quedaba
ligado a `qsec.db` apenas se importaba. Las fixtures cambiaban la URI a
`:memory:` *después* de ese import, cuando ya no tenía efecto, y el
`db.drop_all()` del teardown caía sobre el archivo real.

**Ya está arreglado** y hay tres capas de protección: la app se construye con una
factory, la configuración de test fuerza la base en memoria, y un test falla si
algún archivo de test vuelve a importar la instancia global.

---

## Qué tenés que hacer

### 1. Correr la migración (obligatorio)

```bash
cd TPI
python scripts/migrar_esquema.py
```

Agrega las columnas nuevas sin tocar los datos. Es idempotente: correrla dos
veces no hace nada la segunda. Sin esto la app falla con `no such column`.

### 2. Instalar dependencias

```bash
pip install -r requirements-dev.txt   # desarrollo: incluye Qiskit y pytest
pip install -r requirements.txt       # producción: sin Qiskit
```

### 3. Levantar y probar

```bash
python app.py         # http://localhost:5000
pytest tests/ -v      # 177 tests
```

`run.py` ya no existe: era un segundo entrypoint que duplicaba el de `app.py`.

---

## Estado: las seis fases están hechas

| # | Fase | Commit |
|---|---|---|
| 0 | Correctitud | `8d515e4` |
| 1 | Motor dual analítico + Qiskit | `e78fd34` |
| 2 | Ruido de canal y estrategias de Eve | `26608f3` |
| 3 | Traza real, animación y detalle | `9c81764` |
| 4 | One-time-pad, gráficos y gestión de sesiones | `3778b8c` |
| 5-6 | Factory, deploy, CI y tests de reglas de negocio | `d58c9bb` |

**177 tests en verde**, flake8 limpio sin silenciar `F821` ni `C901`.

---

## Los bugs que aparecieron

### El simulador reventaba con la longitud mínima

El cálculo del QBER usaba `min(len(clave)//4, 20)` como tamaño de muestra, que da
cero cuando la clave cribada tiene menos de 4 bits, y después dividía por ese
cero. Reproducido: **6 de cada 30 corridas con `key_length=10`**, que es justo el
mínimo que acepta el formulario.

### La animación mostraba bits inventados

`bb84_animation.html` generaba los bits de Alice, Bob y Eve con `Math.random()`
en el browser. El backend los calculaba, pero `simulate_bb84()` nunca los
devolvía. Los fotones "interceptados" del SVG eran un 60% arbitrario, sin
relación con lo que Eve realmente tocaba. Hoy quedan cero usos de `Math.random()`.

### El registro habría fallado en producción

`password_hash` era `String(128)` y el hash scrypt de Werkzeug ocupa ~162
caracteres. SQLite ignora la longitud declarada; Postgres y MySQL la validan.

### Cualquiera podía leer las claves de cualquiera

`get_session_by_id()` no filtraba por usuario. Al implementar `/simulation/<id>`
eso habría dejado ver las claves ajenas cambiando el ID en la URL. Ahora la
propiedad se valida en la capa de datos y en la de negocio, y la ruta responde
404 para no revelar siquiera que la sesión existe.

### El motor de Qiskit no era reproducible

Aceptaba una semilla, pero Aer tiene su propio generador que nunca se sembraba:
dos corridas con la misma semilla daban resultados distintos. Era la causa de un
test que fallaba una de cada diez corridas de la suite.

### Un cuerpo JSON vacío devolvía 500

`request.get_json()` levanta excepción y el `except` genérico la convertía en
error de servidor. Ahora responde 400.

### Otras

`get_user_info()` leía `user.created_at`, un campo inexistente. `datetime.utcnow`
está deprecada desde Python 3.12. Las estadísticas traían todas las filas a
memoria para contarlas. `ASECRET_KEY` en el `.env.example` dejaba a quien lo
copiara con la clave de desarrollo.

---

## Lo que se agregó

### Motor dual, validado contra la teoría

`business/bb84/` separa la lógica del protocolo de la física del canal. Hay dos
motores con la misma interfaz: uno analítico (forma cerrada) y uno de circuitos
con Qiskit. `tests/test_engines.py` contrasta ambos contra el QBER teórico en
cinco escenarios y verifica que coincidan entre sí.

Medido sobre 12.032 bits cribados por escenario, ambos coinciden con la teoría
dentro de **1,7 desviaciones estándar**.

Sirve para la ponencia y también para el deploy: con Qiskit opcional el proyecto
baja de los ~365 MB que no entran en ninguna plataforma gratuita.

### Ruido de canal y estrategias de Eve

El simulador ahora acepta ruido (0–50%) y una fracción interceptada configurable,
con el QBER previsto calculándose en vivo. El QBER esperado es
`ruido + 0.25·p`, y eso permite mostrar la frontera donde el enlace se vuelve
inutilizable **aunque no haya nadie espiando**: el protocolo descarta la clave
igual, porque no puede distinguir una causa de la otra. Esa indistinguibilidad es
la garantía de BB84 y también su límite práctico.

### El protocolo se ve de verdad

La traza se persiste (tabla aparte, recortada a 256 qubits) y alimenta tanto la
animación como `/simulation/<id>`, que antes era un stub que flasheaba "en
desarrollo". El detalle muestra el embudo de qubits enviados → cribados → clave
final y la tabla bit a bit con la base de cada medición.

### Cifrado one-time-pad

Tras una corrida segura se puede cifrar un mensaje con la clave generada, y se
ve a Bob recuperando el original y a Eve obteniendo ruido. Cierra el relato de
por qué sirve BB84.

### Gráficos y gestión de sesiones

Chart.js en el dashboard (histograma de QBER y evolución temporal), más borrar,
paginar y exportar a JSON.

---

## Deploy

**GitHub Pages no puede hostear esto**: sirve archivos estáticos y no tiene
runtime de Python. Los pasos están en [DEPLOY.md](../DEPLOY.md); en resumen, la
app va a Render o Vercel con `SECRET_KEY` propia y un Postgres gestionado, y
Pages queda para una landing del congreso.

El CI tiene un job que instala **sólo** las dependencias de producción y verifica
que la app levante y simule sin Qiskit.

---

## Referencia rápida

```bash
cd TPI

python scripts/migrar_esquema.py        # migrar esquema (idempotente)
python app.py                           # levantar
pytest tests/ -v                        # 177 tests
pytest tests/test_business_rules.py -v  # reglas de negocio
pytest tests/test_engines.py -v         # validación cruzada de motores
```

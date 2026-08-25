# Q-Sec — Estado del refactor

> Documento de trabajo para el equipo. Última actualización: 2026-08-24.
> Rama `TPI`. **Los commits todavía no están pusheados.**

---

## ⚠️ Leé esto primero: puede que hayas perdido tu base local

**Correr `pytest tests/` borraba `qsec.db`**, y los tests igual daban verde.

Lo verifiqué con el código original en una copia limpia del repo: 29 tests en
verde y la base sin tablas al terminar. O sea que a cualquiera que haya corrido
la suite localmente se le borró la base sin ningún aviso.

**Causa:** `app.py` ejecuta `db.create_all()` a nivel de módulo, lo que liga el
engine de SQLAlchemy a `qsec.db` en el momento del import. Las fixtures seteaban
`SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'` *después* de ese import, cuando
Flask-SQLAlchemy ya tiene el engine cacheado y el cambio no tiene efecto. El
`db.drop_all()` del teardown terminaba cayendo sobre el archivo real.

**Estado:** arreglado. `tests/conftest.py` ahora fija `DATABASE_URL` antes de
importar la app y además *verifica* que la URI sea en memoria antes de crear o
borrar nada. Si tu base quedó vacía no hay nada que recuperar, pero se recrea
sola al levantar la app.

---

## Qué tenés que hacer

### 1. Correr la migración (obligatorio)

En cualquier máquina donde ya exista un `qsec.db`:

```bash
cd TPI
python scripts/migrar_esquema.py
```

Agrega la columna nueva sin tocar los datos. Es idempotente: correrla dos veces
no hace nada la segunda. Sin esto, la app falla con `no such column: user.created_at`.

Hace falta porque `db.create_all()` crea tablas que faltan pero **no** agrega
columnas a tablas que ya existen.

### 2. Levantar la app

```bash
cd TPI
python app.py
```

`run.py` ya no existe: era un segundo entrypoint que duplicaba el de `app.py`.

### 3. Correr los tests

```bash
cd TPI
pytest tests/ -v
```

Ahora es seguro: no tocan ningún archivo real.

---

## Lo que ya está hecho

Dos commits en `TPI`, verificados y sin pushear:

| Commit | Descripción |
|---|---|
| `8d515e4` | fix: correcciones de correctitud en capa de datos, negocio y tests |
| `e78fd34` | feat: motor dual de simulación BB84 (analítico + Qiskit) con traza real |

### Fase 0 — Correctitud

**El simulador reventaba con la longitud de clave mínima.**
El cálculo del QBER usaba `min(len(clave)//4, 20)` como tamaño de muestra, que
da cero cuando la clave cribada tiene menos de 4 bits, y después dividía por ese
cero. Reproducido: **6 de cada 30 corridas con `key_length=10`**, que es justo el
mínimo que acepta el formulario. El usuario veía *"Error en la simulación:
division by zero"*. Ahora la muestra tiene al menos un bit y, si no alcanzan las
bases coincidentes, la corrida aborta con un mensaje útil. Cubierto por tests de
regresión.

**`password_hash` era demasiado corto — bloqueante para el deploy.**
Estaba declarado `String(128)`, pero el hash scrypt de Werkzeug ocupa ~162
caracteres. SQLite ignora la longitud declarada y por eso funcionaba; Postgres y
MySQL la validan, así que el registro de usuarios habría fallado en producción.
Corregido a 255.

**`get_user_info()` estaba rota.** Leía `user.created_at`, un campo que no
existía en el modelo. No explotaba sólo porque nadie la llamaba. Se agregó la
columna y se contempla que las cuentas previas la tengan vacía.

**Otras correcciones:**

- `datetime.utcnow` (deprecada en Python 3.12+, y devolvía datetimes naive)
  reemplazada por un helper `utc_now()` timezone-aware.
- Migración al estilo SQLAlchemy 2.0: `db.session.get()` y `db.select()` en lugar
  del Query API legacy.
- `get_user_statistics()` traía **todas** las filas del usuario a memoria sólo
  para contarlas; ahora cuenta en SQL.
- Eliminado el handler `beforeunload` de la animación, que asignaba
  `location.href` durante la descarga de la página (donde no navega a ningún
  lado) e interfería con la navegación.
- Corregido `ASECRET_KEY` → `SECRET_KEY` en `.env.example`: quien copiara el
  archivo se quedaba en silencio con la clave de desarrollo hardcodeada.
- `pytest.ini` define `pythonpath`, lo que saca los `sys.path.insert` que había
  en cada archivo de test.
- Eliminado `run.py`.

### Fase 1 — Motor dual

`bb84_simulation.py` pasó a ser el paquete `business/bb84/`, que separa la
lógica del protocolo de la resolución física del canal.

```
business/bb84/
├── protocol.py              # cribado, QBER, decisión de seguridad
├── result.py                # BB84Result: la traza completa
└── engines/
    ├── analytic.py          # forma cerrada, sin dependencias pesadas
    └── qiskit_engine.py     # circuitos cuánticos reales
```

**Por qué dos motores.** BB84 es *prepare-and-measure* de un qubit: el resultado
de cada medición tiene forma cerrada y no hace falta simular el circuito para
obtenerlo. Pero tirar Qiskit sería perder el argumento de "simulación cuántica
real". Entonces están los dos, y `tests/test_engines.py` los contrasta contra el
QBER teórico en cinco escenarios (canal ideal, espía total, espía parcial, canal
ruidoso, ruido con espía). **Coinciden dentro del 3%.**

Eso nos da dos cosas: el argumento para la ponencia ("validamos el modelo
analítico contra un simulador cuántico") y la posibilidad de deployar, porque con
Qiskit como dependencia opcional el proyecto baja de los ~365 MB actuales
(Qiskit 27 MB + Aer 7 MB + SciPy 98 MB) y entra en los límites de las
plataformas gratuitas.

**La animación mostraba bits inventados.** `bb84_animation.html` generaba los
bits de Alice, Bob y Eve con `Math.random()` en el browser. El backend sí los
calculaba, pero `simulate_bb84()` nunca los devolvía y el controller los leía
como listas vacías. Ahora la simulación devuelve un `BB84Result` con la traza
completa (bits y bases de Alice, Bob y Eve, índices cribados y muestreados) y la
API la expone. **Falta conectar la animación** — es la Fase 3.

**Mejoras en el motor de Qiskit:** los circuitos se ejecutan en lote en vez de
uno por bit, el backend se obtiene una sola vez en lugar de una por qubit
interceptado, y se migró de `QasmSimulator` (deprecado) a `AerSimulator`.

**Parámetros nuevos:** `simulate_bb84()` ya acepta `noise_rate`, `eve_strategy`,
`eve_fraction` y `seed`. La interfaz todavía no los expone (Fase 2).

### Verificado

| Métrica | Resultado |
|---|---|
| Tests | 52 en verde |
| flake8 | 0 errores, incluso sin silenciar `F821` |
| Acuerdo entre motores | dentro del 3% en los 5 escenarios |
| Base de desarrollo | 2 usuarios / 43 simulaciones, intactos |
| Server | levanta y responde 200 en `/`, `/login`, `/register` |

---

## Lo que viene

Las fases están numeradas porque hay dependencias reales entre ellas.

### Fase 2 — Ruido de canal y estrategias de Eve

El motor ya lo soporta; falta exponerlo en `SimulationForm`, en la ruta
`/simulator` y en el template.

Hoy Eve es un booleano y sin ruido el QBER es 0% o ~25%, así que el umbral del
11% nunca se pone interesante. Con `noise_rate` y una fracción interceptada
configurable, el QBER esperado pasa a ser `ruido + 0.25·p`, y se puede mostrar en
vivo la frontera donde el enlace se vuelve inutilizable por ruido aunque no haya
nadie espiando. Eso es una **regla de negocio nueva y no trivial**: el protocolo
descarta la clave sin poder distinguir si el error lo causó un espía o el canal,
y esa indistinguibilidad es justamente la garantía de BB84 y también su límite
práctico.

### Fase 3 — Mostrar el protocolo de verdad

1. Persistir la traza en una tabla aparte (1:1 con la sesión, carga diferida,
   truncada a ~256 bits) e incorporar Flask-Migrate, porque hoy no hay
   migraciones de verdad.
2. Reescribir la animación para que consuma la traza real en lugar de
   `Math.random()`. Los fotones interceptados en el SVG pasarían a corresponderse
   con los qubits que Eve realmente tocó, en vez de un 60% arbitrario.
3. Implementar `/simulation/<id>`, que hoy es un stub que flashea "en
   desarrollo": tabla bit a bit, desglose del QBER y clave final.
   **Con chequeo de propiedad** — hoy `get_session_by_id()` no filtra por
   usuario, así que sin eso cualquiera leería las claves de cualquiera cambiando
   el ID en la URL.

### Fase 4 — Features de producto

- **Cifrado one-time-pad**: tras una corrida segura, el usuario escribe un
  mensaje, se cifra con XOR contra la clave generada, y se muestra el intento de
  descifrado de Eve con su clave parcial (basura). Cierra el relato de *por qué*
  sirve BB84.
- **Gráficos** en el dashboard: histograma de QBER, línea temporal de seguras vs.
  comprometidas, QBER contra ruido.
- **Gestión de sesiones**: borrar (con chequeo de propiedad), paginar el
  historial (hoy tope duro de 50) y exportar a JSON/CSV.

### Fase 5 — Deploy y CI

**GitHub Pages no puede hostear esto.** Sirve archivos estáticos y no tiene
runtime de Python: una app Flask no corre ahí. Lo que sí conviene:

- La app va a **Render** (free tier) con `gunicorn` y `Procfile`, apuntando a un
  Postgres gratis (el disco del free tier es efímero y la base se borraría en
  cada deploy).
- **Vercel** es viable *sólo gracias a la Fase 1*: sus funciones serverless
  tienen un límite de 250 MB y el `site-packages` actual pesa 365 MB.
- **GitHub Pages sí sirve para el congreso**: una landing estática con el
  abstract, los diagramas, las capturas y el link a la demo en vivo.

En el CI, `flake8` corre con `--ignore=...,F821`. **`F821` es "nombre no
definido"**, o sea que estamos silenciando una clase de bug real — exactamente la
familia del `user.created_at` que arreglamos. Ya verifiqué que el código pasa sin
ese ignore, así que sacarlo no rompe nada.

### Fase 6 — Tests de reglas de negocio

Hoy **ningún test importa `auth_controller` ni `simulation_controller`**. Lo que
había testeaba SQLAlchemy y el módulo `random` de Python, con asserts como
`assert LoginForm is not None`. El enunciado pide explícitamente *"Test que
evalúe que se cumplan las reglas de negocio en los Métodos de la Clase de
Negocio"*.

Falta: reglas de registro (usuario < 3 caracteres, password < 6, duplicado) y de
simulación (límites 10–1000, decisión de umbral, ruido vs. espía, precondiciones
del one-time-pad). Más el refactor a *application factory*, que es lo que permite
fixtures limpias.

---

## Referencia rápida

```bash
cd TPI

python scripts/migrar_esquema.py   # migrar el esquema (idempotente)
python app.py                      # levantar la app
pytest tests/ -v                   # correr los tests
pytest tests/test_engines.py -v    # sólo la validación de motores
```

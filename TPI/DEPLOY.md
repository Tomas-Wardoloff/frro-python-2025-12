# Deploy de Q-Sec

## GitHub Pages no sirve para esta aplicación

GitHub Pages sirve **archivos estáticos**: no tiene runtime de Python, así que
una app Flask con base de datos no puede correr ahí. Lo que sí conviene es
publicar en Pages una página estática del congreso (abstract, diagramas,
capturas, el paper) con un enlace a la demo en vivo.

## Render (recomendado)

Es la opción más simple para Flask.

1. Crear un **Web Service** apuntando al repositorio.
2. Configurar:
   - **Root Directory**: `TPI`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: se toma del `Procfile`
3. Variables de entorno:

   | Variable | Valor |
   |---|---|
   | `SECRET_KEY` | una cadena aleatoria larga (ver abajo) |
   | `FLASK_ENV` | `production` |
   | `DATABASE_URL` | la URL del Postgres (ver abajo) |

Para generar la `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Sin `SECRET_KEY` la app no arranca**, y es a propósito: con la clave de
desarrollo cualquiera podría falsificar cookies de sesión.

### Sobre la base de datos

El disco del free tier de Render es **efímero**: un SQLite ahí se borra en cada
deploy. Conviene un Postgres gratis de [Neon](https://neon.tech) o
[Supabase](https://supabase.com) y pasar su URL en `DATABASE_URL`.

La app normaliza sola el esquema `postgres://` que entregan varios proveedores
y que SQLAlchemy 2.0 rechaza (ver `config.normalizar_url`).

## Vercel

Viable, pero **sólo** porque el motor analítico permite prescindir de Qiskit:
las funciones serverless de Vercel tienen un límite de 250 MB y el entorno
completo con Qiskit y SciPy pesa unos 365 MB. Con `requirements.txt` (sin
Qiskit) entra.

Vercel además tiene el sistema de archivos en sólo lectura, así que ahí el
Postgres no es opcional.

## Por qué Qiskit no está en `requirements.txt`

Qiskit con SciPy pesa ~130 MB y no entra en varios free tiers. El motor
analítico resuelve el mismo canal y produce los mismos resultados: la
equivalencia está verificada en `tests/test_engines.py`, que contrasta ambos
motores contra el QBER teórico en cinco escenarios.

En producción la app usa el motor analítico. Para desarrollo, con
`requirements-dev.txt` se instala Qiskit y la interfaz ofrece los dos motores.

El CI tiene un job (`deploy-check`) que instala **sólo** las dependencias de
producción y verifica que la app levante y simule sin Qiskit.

## Checklist antes de publicar

- [ ] `SECRET_KEY` propia definida por entorno
- [ ] `FLASK_ENV=production`
- [ ] `DATABASE_URL` apuntando a una base persistente
- [ ] Migración aplicada: `python scripts/migrar_esquema.py`
- [ ] La suite en verde: `pytest tests/`

#!/usr/bin/env bash
# Corre la suite completa contra un PostgreSQL real en Docker.
#
# La suite normal usa SQLite, que es mas permisivo: no valida longitudes de
# VARCHAR y -sin el pragma que activa datos/__init__.py- tampoco las claves
# foraneas. Correrla contra Postgres detecta lo que solo fallaria en produccion.
#
# Uso:  ./scripts/test_postgres.sh
set -euo pipefail

CONTENEDOR=qsec-pg-test
PUERTO=55432
cd "$(dirname "$0")/.."

limpiar() {
  docker rm -f "$CONTENEDOR" >/dev/null 2>&1 || true
  [ -f tests/conftest.py.bak ] && mv tests/conftest.py.bak tests/conftest.py
}
trap limpiar EXIT

echo "▸ Levantando PostgreSQL 16..."
docker rm -f "$CONTENEDOR" >/dev/null 2>&1 || true
docker run -d --name "$CONTENEDOR" \
  -e POSTGRES_PASSWORD=qsec -e POSTGRES_USER=qsec -e POSTGRES_DB=qsec_test \
  -p "$PUERTO":5432 postgres:16-alpine >/dev/null

for _ in $(seq 1 40); do
  docker exec "$CONTENEDOR" pg_isready -U qsec -d qsec_test >/dev/null 2>&1 && break
  sleep 1
done
echo "  listo"

echo "▸ Corriendo la suite contra Postgres..."
cp tests/conftest.py tests/conftest.py.bak
cp tests/postgres/conftest_postgres.py tests/conftest.py
python -m pytest tests/ -q || { echo "FALLARON tests contra Postgres"; exit 1; }

echo "▸ Todo en verde contra PostgreSQL"

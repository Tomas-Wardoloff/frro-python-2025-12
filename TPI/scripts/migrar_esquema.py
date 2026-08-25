"""
Migración de esquema idempotente para SQLite.

``db.create_all()`` crea tablas que faltan pero **no** agrega columnas nuevas a
tablas que ya existen, así que agregar un campo a un modelo deja la base de
desarrollo desincronizada y las consultas fallan con "no such column".

Este script agrega las columnas faltantes sin tocar los datos existentes.
Es idempotente: correrlo dos veces no hace nada la segunda vez.

Uso:
    python scripts/migrar_esquema.py [ruta_a_la_base]
"""
import os
import sqlite3
import sys

# (tabla, columna, definición SQL). Las columnas nuevas tienen que ser
# nullable o traer DEFAULT, porque las filas que ya existen las van a recibir
# vacías.
COLUMNAS = [
    ('user', 'created_at', 'DATETIME'),
    # Parametros del canal y del ataque (las corridas viejas quedan en NULL,
    # y to_dict() las reporta con sus valores por defecto)
    ('simulation_session', 'noise_rate', 'FLOAT'),
    ('simulation_session', 'eve_strategy', 'VARCHAR(30)'),
    ('simulation_session', 'eve_fraction', 'FLOAT'),
    ('simulation_session', 'engine', 'VARCHAR(20)'),
    ('simulation_session', 'sifted_length', 'INTEGER'),
    ('simulation_session', 'final_length', 'INTEGER'),
]

# Las tablas nuevas (simulation_trace) las crea db.create_all() al levantar la
# app, porque create_all si crea tablas faltantes; lo que no hace es agregar
# columnas a tablas que ya existen, que es de lo que se ocupa este script.


def columnas_existentes(con, tabla):
    return {fila[1] for fila in con.execute(f'PRAGMA table_info("{tabla}")')}


def tabla_existe(con, tabla):
    fila = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabla,)
    ).fetchone()
    return fila is not None


def migrar(db_path):
    if not os.path.exists(db_path):
        print(f'No existe {db_path}; nada que migrar (se creará con create_all).')
        return 0

    aplicadas = 0
    with sqlite3.connect(db_path) as con:
        for tabla, columna, tipo in COLUMNAS:
            if not tabla_existe(con, tabla):
                print(f'- tabla "{tabla}" todavía no existe, se omite')
                continue
            if columna in columnas_existentes(con, tabla):
                print(f'- {tabla}.{columna} ya existe')
                continue
            con.execute(f'ALTER TABLE "{tabla}" ADD COLUMN "{columna}" {tipo}')
            print(f'+ agregada {tabla}.{columna} ({tipo})')
            aplicadas += 1

    print(f'\nListo: {aplicadas} columna(s) agregada(s).')
    return aplicadas


if __name__ == '__main__':
    if len(sys.argv) > 1:
        ruta = sys.argv[1]
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ruta = os.path.join(base_dir, 'qsec.db')
    migrar(ruta)

import sqlite3
import os

db_path = 'qsec.db'
print(f"Verificando base de datos en: {os.path.abspath(db_path)}")
print(f"¿Existe? {os.path.exists(db_path)}\n")

if not os.path.exists(db_path):
    print("❌ La base de datos no existe!")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== ESQUEMA DE LA BASE DE DATOS ===\n")

# Listar todas las tablas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"Tablas encontradas: {[t[0] for t in tables]}\n")

# Ver esquema de cada tabla
for table in tables:
    table_name = table[0]
    print(f"\nTabla '{table_name}':")
    cursor.execute(f'PRAGMA table_info({table_name})')
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"  - {row[1]} ({row[2]})")
    else:
        print("  (sin columnas)")

conn.close()

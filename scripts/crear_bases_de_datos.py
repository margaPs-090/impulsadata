"""
crear_bases_de_datos.py
Crea las 10 tablas de ImpulsaData en los tres motores (MySQL, PostgreSQL y MariaDB)
a partir del fichero impulsaData.sql (el diagrama Entidad-Relación).

Requisitos:  pip install mysql-connector-python psycopg2-binary
Uso:         python crear_bases_de_datos.py
"""
from pathlib import Path

import mysql.connector
import psycopg2

SQL_FILE = Path(__file__).parent / "impulsaData.sql"

# Orden inverso al de creación, para poder borrar respetando las claves foráneas
TABLAS = [
    "candidaturas", "curso_competencia", "cursos", "oferta_competencia",
    "ofertas_empleo", "empresas", "usuario_competencia", "competencias",
    "usuarios", "municipios",
]

CONEXIONES = {
    "MySQL":      {"motor": "mysql",    "host": "localhost", "port": 3306,
                   "database": "impulsadata", "user": "impulsa", "password": "impulsa1234"},
    "PostgreSQL": {"motor": "postgres", "host": "localhost", "port": 5432,
                   "database": "impulsadata", "user": "impulsa", "password": "impulsa1234"},
    "MariaDB":    {"motor": "mysql",    "host": "localhost", "port": 3307,
                   "database": "impulsadata", "user": "impulsa", "password": "impulsa1234"},
}


def leer_sentencias():
    """Lee el .sql y lo separa en sentencias CREATE TABLE."""
    texto = SQL_FILE.read_text(encoding="utf-8")
    return [s.strip() for s in texto.split(";") if s.strip()]


def adaptar_postgres(sentencia):
    """PostgreSQL no tiene AUTO_INCREMENT: se sustituye por SERIAL."""
    return sentencia.replace("INT AUTO_INCREMENT PRIMARY KEY", "SERIAL PRIMARY KEY")


def conectar(cfg):
    datos = {k: v for k, v in cfg.items() if k != "motor"}
    if cfg["motor"] == "postgres":
        return psycopg2.connect(dbname=datos.pop("database"), **datos)
    return mysql.connector.connect(**datos)


def crear_esquema(nombre, cfg, sentencias):
    es_postgres = cfg["motor"] == "postgres"
    conn = conectar(cfg)
    cur = conn.cursor()

    # 1) Borrar tablas anteriores (así el script se puede ejecutar varias veces)
    if not es_postgres:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    for tabla in TABLAS:
        cur.execute(f"DROP TABLE IF EXISTS {tabla}" + (" CASCADE" if es_postgres else ""))
    if not es_postgres:
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")

    # 2) Crear las tablas del diagrama ER
    for sentencia in sentencias:
        cur.execute(adaptar_postgres(sentencia) if es_postgres else sentencia)
    conn.commit()

    # 3) Comprobar cuántas tablas hay
    if es_postgres:
        cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
    else:
        cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE()")
    total = cur.fetchone()[0]
    print(f"[OK] {nombre}: {total} tablas creadas")
    cur.close()
    conn.close()


if __name__ == "__main__":
    sentencias = leer_sentencias()
    for nombre, cfg in CONEXIONES.items():
        try:
            crear_esquema(nombre, cfg, sentencias)
        except Exception as e:
            print(f"[ERROR] {nombre}: {e}")

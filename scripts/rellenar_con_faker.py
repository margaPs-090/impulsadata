"""
rellenar_con_faker.py
Rellena con datos falsos (Faker) las tablas de ImpulsaData en los tres motores:
MySQL, PostgreSQL y MariaDB. Los datos se generan una vez (con semilla fija)
y se insertan idénticos en las tres bases de datos.

Providers / comandos de Faker utilizados (10 distintos):
 1.  fake.name()                 -> nombre y apellidos de los usuarios
 2.  fake.unique.email()         -> email único de cada usuario
 3.  fake.phone_number()         -> teléfonos de usuarios y empresas
 4.  fake.date_between()         -> fechas de registro, publicación y candidatura
 5.  fake.city()                 -> nombre de los municipios
 6.  fake.administrative_unit()  -> provincia de cada municipio
 7.  fake.company()              -> nombre de las empresas
 8.  fake.unique.cif()           -> CIF único de cada empresa
 9.  fake.company_email()        -> email de contacto de las empresas
 10. fake.job()                  -> título de las ofertas de empleo
 11. fake.paragraph()            -> descripción de ofertas y cursos
 12. fake.pydecimal()            -> salario de las ofertas
 13. fake.random_int()           -> horas y plazas de los cursos
 14. fake.random_element()       -> estados y niveles

Requisitos:  pip install faker mysql-connector-python psycopg2-binary
Uso:         python rellenar_con_faker.py   (antes: python crear_bases_de_datos.py)
"""
import random
from collections import OrderedDict

from faker import Faker

from crear_bases_de_datos import CONEXIONES, TABLAS, conectar

SEMILLA = 42
N_MUNICIPIOS = 30
N_USUARIOS = 300
N_EMPRESAS = 60
N_OFERTAS = 150
N_CURSOS = 24
N_CANDIDATURAS = 600

COMPETENCIAS = [
    ("Python", "Programación"), ("Java", "Programación"), ("SQL", "Programación"),
    ("JavaScript", "Programación"), ("Excel avanzado", "Ofimática"),
    ("Word y documentos", "Ofimática"), ("Análisis de datos", "Digital"),
    ("Marketing digital", "Digital"), ("Redes sociales", "Digital"),
    ("Diseño gráfico", "Digital"), ("Inglés", "Idiomas"), ("Francés", "Idiomas"),
    ("Alemán", "Idiomas"), ("Atención al cliente", "Habilidades"),
    ("Trabajo en equipo", "Habilidades"), ("Liderazgo", "Habilidades"),
    ("Comunicación", "Habilidades"), ("Contabilidad", "Administración"),
    ("Gestión de almacén", "Logística"), ("Conducción de carretillas", "Logística"),
    ("Soldadura", "Industria"), ("Electricidad", "Industria"),
    ("Cocina", "Hostelería"), ("Camarero/a de sala", "Hostelería"),
    ("Cuidado de personas mayores", "Sociosanitario"), ("Primeros auxilios", "Sociosanitario"),
    ("Prevención de riesgos laborales", "Seguridad"), ("Carpintería", "Industria"),
]
NIVELES = ["básico", "intermedio", "avanzado"]


def generar_datos():
    """Devuelve un diccionario {tabla: [filas]} con las filas en el orden de las columnas."""
    fake = Faker("es_ES")
    Faker.seed(SEMILLA)
    random.seed(SEMILLA)
    d = {}

    d["municipios"] = [
        (i, fake.city(), fake.administrative_unit()) for i in range(1, N_MUNICIPIOS + 1)
    ]
    d["competencias"] = [(i, n, c) for i, (n, c) in enumerate(COMPETENCIAS, start=1)]
    n_comp = len(COMPETENCIAS)

    d["usuarios"] = [
        (i, fake.name(), fake.unique.email(), fake.phone_number()[:20],
         fake.date_between("-2y", "today"), random.randint(1, N_MUNICIPIOS))
        for i in range(1, N_USUARIOS + 1)
    ]

    d["usuario_competencia"], k = [], 1
    for u in range(1, N_USUARIOS + 1):
        for c in random.sample(range(1, n_comp + 1), random.randint(2, 5)):
            d["usuario_competencia"].append((k, u, c, fake.random_element(NIVELES)))
            k += 1

    d["empresas"] = [
        (i, fake.company(), fake.unique.cif(), fake.company_email(),
         fake.phone_number()[:20], random.randint(1, N_MUNICIPIOS))
        for i in range(1, N_EMPRESAS + 1)
    ]

    estados_oferta = OrderedDict([("abierta", 0.6), ("cerrada", 0.3), ("en revisión", 0.1)])
    d["ofertas_empleo"] = [
        (i, fake.job()[:150], fake.paragraph(nb_sentences=3),
         fake.pydecimal(left_digits=5, right_digits=2, positive=True,
                        min_value=14000, max_value=55000),
         fake.date_between("-1y", "today"), fake.random_element(estados_oferta),
         random.randint(1, N_EMPRESAS))
        for i in range(1, N_OFERTAS + 1)
    ]

    d["oferta_competencia"], k = [], 1
    for o in range(1, N_OFERTAS + 1):
        for c in random.sample(range(1, n_comp + 1), random.randint(2, 4)):
            d["oferta_competencia"].append((k, o, c))
            k += 1

    d["cursos"] = []
    for i in range(1, N_CURSOS + 1):
        nombre = f"Curso de {COMPETENCIAS[(i - 1) % n_comp][0]}"
        d["cursos"].append((i, nombre, fake.paragraph(nb_sentences=3),
                            fake.random_int(20, 300), fake.random_int(10, 40)))

    d["curso_competencia"], k = [], 1
    for cu in range(1, N_CURSOS + 1):
        principal = (cu - 1) % n_comp + 1          # la competencia que da nombre al curso
        extra = random.sample(range(1, n_comp + 1), random.randint(0, 2))
        for c in dict.fromkeys([principal] + extra):
            d["curso_competencia"].append((k, cu, c))
            k += 1

    fechas_oferta = {f[0]: f[4] for f in d["ofertas_empleo"]}
    estados_cand = OrderedDict([("enviada", 0.35), ("en proceso", 0.25), ("entrevista", 0.15),
                                ("contratado", 0.1), ("rechazada", 0.15)])
    pares = set()
    while len(pares) < N_CANDIDATURAS:
        pares.add((random.randint(1, N_USUARIOS), random.randint(1, N_OFERTAS)))
    d["candidaturas"] = [
        (i, fake.date_between(fechas_oferta[o], "today"), fake.random_element(estados_cand), u, o)
        for i, (u, o) in enumerate(sorted(pares), start=1)
    ]
    return d


COLUMNAS = {
    "municipios": "id_municipio, nombre, provincia",
    "competencias": "id_competencia, nombre, categoria",
    "usuarios": "id_usuario, nombre, email, telefono, fecha_registro, id_municipio",
    "usuario_competencia": "id_usuario_competencia, id_usuario, id_competencia, nivel",
    "empresas": "id_empresa, nombre, cif, email, telefono, id_municipio",
    "ofertas_empleo": "id_oferta, titulo, descripcion, salario, fecha_publicacion, estado, id_empresa",
    "oferta_competencia": "id_oferta_competencia, id_oferta, id_competencia",
    "cursos": "id_curso, nombre, descripcion, horas, plazas",
    "curso_competencia": "id_curso_competencia, id_curso, id_competencia",
    "candidaturas": "id_candidatura, fecha_candidatura, estado, id_usuario, id_oferta",
}
ORDEN_INSERCION = list(reversed(TABLAS))   # padres antes que hijos


def rellenar(nombre, cfg, datos):
    es_postgres = cfg["motor"] == "postgres"
    conn = conectar(cfg)
    cur = conn.cursor()

    for tabla in TABLAS:                       # vaciar (hijos antes que padres)
        cur.execute(f"DELETE FROM {tabla}")

    for tabla in ORDEN_INSERCION:
        cols = COLUMNAS[tabla]
        marcas = ", ".join(["%s"] * len(cols.split(",")))
        cur.executemany(f"INSERT INTO {tabla} ({cols}) VALUES ({marcas})", datos[tabla])
        if es_postgres:                        # ajustar el SERIAL tras insertar ids explícitos
            pk = cols.split(",")[0]
            cur.execute(f"SELECT setval(pg_get_serial_sequence('{tabla}', '{pk}'), "
                        f"(SELECT MAX({pk}) FROM {tabla}))")
    conn.commit()
    cur.close()
    conn.close()
    resumen = ", ".join(f"{t}={len(datos[t])}" for t in ORDEN_INSERCION)
    print(f"[OK] {nombre}: {resumen}")


if __name__ == "__main__":
    datos = generar_datos()
    for nombre, cfg in CONEXIONES.items():
        try:
            rellenar(nombre, cfg, datos)
        except Exception as e:
            print(f"[ERROR] {nombre}: {e}")

import pandas as pd
from sqlalchemy import create_engine
import json
import os

# --- CONFIGURACIÓN DE RUTAS ---
# Esto asegura que los JSON se guarden en la carpeta principal, no dentro de 'scripts'
RUTA_BASE = os.path.join(os.path.dirname(__file__), '..')

def guardar_json(datos, nombre_archivo):
    """Función auxiliar para guardar los datos en formato JSON en la raíz"""
    ruta_completa = os.path.join(RUTA_BASE, nombre_archivo)
    with open(ruta_completa, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
    print(f"✅ Archivo generado: {nombre_archivo}")

def generar_json_mysql():
    print("\n--- Iniciando extracción de MySQL ---")
    try:
        # Conexión MySQL
        engine = create_engine('mysql+pymysql://impulsa:impulsa1234@localhost:3306/impulsadata')
        
        # CONSULTA 1: Top competencias más demandadas en ofertas activas
        query = """
        SELECT 
            c.nombre AS competencia,
            c.categoria AS categoria,
            COUNT(oc.id_oferta) AS total_ofertas_activas
        FROM competencias c
        JOIN oferta_competencia oc ON c.id_competencia = oc.id_competencia
        JOIN ofertas_empleo o ON oc.id_oferta = o.id_oferta
        WHERE o.estado = 'Activa'
        GROUP BY c.id_competencia, c.nombre, c.categoria
        ORDER BY total_ofertas_activas DESC
        LIMIT 15;
        """
        
        df = pd.read_sql(query, engine)
        guardar_json(df.to_dict(orient='records'), 'mysql_demanda_competencias.json')
        
    except Exception as e:
        print(f"❌ Error en MySQL: {e}")

def generar_json_postgres():
    print("\n--- Iniciando extracción de PostgreSQL ---")
    try:
        # Conexión PostgreSQL
        engine = create_engine('postgresql://impulsa:impulsa1234@localhost:5432/impulsadata')
        
        # CONSULTA 2: Tasa de éxito de candidaturas por municipio
        query = """
        SELECT 
            m.nombre AS municipio,
            m.provincia,
            COUNT(ca.id_candidatura) AS total_candidaturas,
            SUM(CASE WHEN ca.estado = 'Contratado' THEN 1 ELSE 0 END) AS total_contratados
        FROM municipios m
        JOIN usuarios u ON m.id_municipio = u.id_municipio
        JOIN candidaturas ca ON u.id_usuario = ca.id_usuario
        GROUP BY m.id_municipio, m.nombre, m.provincia
        HAVING COUNT(ca.id_candidatura) > 0
        ORDER BY total_contratados DESC, total_candidaturas DESC
        LIMIT 20;
        """
        
        df = pd.read_sql(query, engine)
        guardar_json(df.to_dict(orient='records'), 'postgres_exito_municipios.json')
        
    except Exception as e:
        print(f"❌ Error en PostgreSQL: {e}")

def generar_json_mariadb():
    print("\n--- Iniciando extracción de MariaDB ---")
    try:
        # Conexión MariaDB
        engine = create_engine('mariadb+mariadbconnector://impulsa:impulsa1234@localhost:3307/impulsadata')
        
        # CONSULTA 3: Cursos con mayor demanda en el mercado laboral
        query = """
        SELECT 
            cu.nombre AS curso,
            cu.horas AS duracion_horas,
            COUNT(DISTINCT c.id_competencia) AS num_competencias_ensenadas,
            COUNT(DISTINCT oc.id_oferta) AS ofertas_que_requieren_esas_competencias
        FROM cursos cu
        JOIN curso_competencia cc ON cu.id_curso = cc.id_curso
        JOIN competencias c ON cc.id_competencia = c.id_competencia
        LEFT JOIN oferta_competencia oc ON c.id_competencia = oc.id_competencia
        GROUP BY cu.id_curso, cu.nombre, cu.horas
        ORDER BY ofertas_que_requieren_esas_competencias DESC
        LIMIT 10;
        """
        
        df = pd.read_sql(query, engine)
        guardar_json(df.to_dict(orient='records'), 'mariadb_cursos_demandados.json')
        
    except Exception as e:
        print(f"❌ Error en MariaDB: {e}")

if __name__ == "__main__":
    print("🚀 INICIANDO GENERACIÓN DE ARCHIVOS JSON ANALÍTICOS 🚀")
    
    # Ejecutamos las tres funciones
    generar_json_mysql()
    generar_json_postgres()
    generar_json_mariadb()
    
    print("\n🎉 ¡Proceso finalizado! Revisa la carpeta principal de tu proyecto.")
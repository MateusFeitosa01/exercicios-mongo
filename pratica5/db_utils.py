import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "openf1_data")
SQLITE_DB_NAME = "analysis_reports.db"


# ==========================================
# CONEXÕES E OPERAÇÕES MONGODB (NoSQL)
# ==========================================

def get_mongo_client():
    """Retorna o cliente de conexão com o MongoDB."""
    return MongoClient(MONGODB_URI)


def get_available_years():
    """Busca os anos disponíveis na coleção de sessões."""
    client = get_mongo_client()
    db = client[MONGODB_DB_NAME]
    years = db.sessions.distinct("year")
    client.close()
    return sorted(years, reverse=True)


def get_sessions_by_year(year):
    """Retorna as sessões disponíveis para um determinado ano."""
    client = get_mongo_client()
    db = client[MONGODB_DB_NAME]
    sessions = list(db.sessions.find({"year": year}, {"_id": 0, "session_key": 1, "location": 1, "country_name": 1, "session_name": 1, "circuit_short_name": 1}))
    client.close()
    return sessions


def get_drivers_by_session(session_key):
    """Busca a lista de pilotos únicos em uma determinada sessão."""
    client = get_mongo_client()
    db = client[MONGODB_DB_NAME]
    
    # Busca acrônimos/números dos pilotos nas voltas da sessão
    pipeline = [
        {"$match": {"session_key": session_key}},
        {"$group": {"_id": "$driver_number", "driver_acronym": {"$first": "$driver_acronym"}}}
    ]
    results = list(db.laps.aggregate(pipeline))
    client.close()
    
    drivers = []
    for r in results:
        label = r["driver_acronym"] if r.get("driver_acronym") else str(r["_id"])
        drivers.append({"driver_number": r["_id"], "label": label})
        
    return sorted(drivers, key=lambda x: x["label"])


def get_laps_data(session_key, driver_numbers):
    """Obtém os dados brutos de voltas para a sessão e pilotos selecionados."""
    client = get_mongo_client()
    db = client[MONGODB_DB_NAME]
    
    query = {
        "session_key": session_key,
        "driver_number": {"$in": driver_numbers}
    }
    
    laps = list(db.laps.find(query, {"_id": 0}))
    client.close()
    
    if laps:
        return pd.DataFrame(laps)
    return pd.DataFrame()


# ==========================================
# CONEXÕES E OPERAÇÕES SQLITE (Relacional)
# ==========================================

def init_sqlite_db():
    """Inicializa o banco de dados SQLite e cria a tabela de relatórios se não existir."""
    conn = sqlite3.connect(SQLITE_DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS race_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT,
            driver_name TEXT,
            fastest_lap REAL,
            average_lap_time REAL,
            total_laps INTEGER,
            consistency_std_dev REAL,
            analysis_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def save_analysis_report(reports_list):
    """Salva uma lista de dicionários com métricas agregadas na tabela race_analysis."""
    conn = sqlite3.connect(SQLITE_DB_NAME)
    cursor = conn.cursor()
    
    for item in reports_list:
        cursor.execute("""
            INSERT INTO race_analysis 
            (session_name, driver_name, fastest_lap, average_lap_time, total_laps, consistency_std_dev, analysis_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
        """, (
            item["session_name"],
            item["driver_name"],
            item["fastest_lap"],
            item["average_lap_time"],
            item["total_laps"],
            item["consistency_std_dev"]
        ))
        
    conn.commit()
    conn.close()


def get_analysis_history():
    """Lê todo o histórico de análises gravadas no SQLite."""
    conn = sqlite3.connect(SQLITE_DB_NAME)
    query = "SELECT id, session_name, driver_name, fastest_lap, average_lap_time, total_laps, consistency_std_dev, analysis_timestamp FROM race_analysis ORDER BY id DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
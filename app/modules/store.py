import duckdb
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "./data/alerts.duckdb")

def get_connection():
    return duckdb.connect(DB_PATH)

def init_db():
    con = get_connection()
    con.execute("""
        CREATE TABLE IF NOT EXISTS alerts(
            id             VARCHAR PRIMARY KEY,
            timestamp      TIMESTAMP,
            agent_name     VARCHAR,
            agent_ip       VARCHAR,
            rule_id        VARCHAR,
            rule_description VARCHAR,
            rule_level      INTEGER,
            rule_groups     VARCHAR,
            location        VARCHAR,
            full_log        VARCHAR,
            anomaly_score   FLOAT DEFAULT 0.0,
            is_anomaly      BOOLEAN DEFAULT FALSE,
            ingested_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP     
        )
    """)
    con.close()
    print(f"Database initiated at {DB_PATH}")


def insert_alert(alert: dict):
    con = get_connection()
    con.execute("""
        INSERT INTO alerts (
                id, timestamp, agent_name, agent_ip,
                rule_id, rule_description, rule_level,
                rule_groups, location, full_log
                ) VALUES (?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT (id) DO NOTHING
    """, [
        alert.get("id"),
        alert.get("timestamp"),
        alert.get("agent_name"),
        alert.get("agent_ip"),
        alert.get("rule_id"),
        alert.get("rule_description"),
        alert.get("rule_level"),
        alert.get("rule_groups"),
        alert.get("location"),
        alert.get("full_log"),

    ])
    con.close()

def get_alerts(limit:int = 100, anomaly_only: bool = False) -> pd.DataFrame:
    con = get_connection()
    query = "SELECT * FROM alerts"
    if anomaly_only:
        query += " WHERE is_anomaly = TRUE"
    query +=f" ORDER BY anomaly_score DESC LIMIT {limit}"
    df = con.execute(query).df()
    con.close()
    return df

def update_anomaly_scores(df: pd.DataFrame):
    con = get_connection()
    for _, row in df.iterrows():
        con.execute("""
            UPDATE alerts
            SET anomaly_score = ?, is_anomaly = ?
            WHERE id = ?
        """, [row["anomaly_score"], row["is_anomaly"], row["id"]])
    con.close()

def get_status() -> dict:
    con = get_connection()
    total = con.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    anomalies = con.execute("SELECT COUNT(*) FROM alerts WHERE is_anomaly = TRUE").fetchone()[0]
    avg_score = con.execute("SELECT AVG(anomaly_score) FROM alerts").fetchone()[0]
    con.close()
    return {
        "total_alerts": total,
        "total_anomalies": anomalies,
        "average_anomaly_score": round(avg_score or 0.0, 4)
    }   



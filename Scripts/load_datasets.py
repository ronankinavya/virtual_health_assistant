# Scripts/load_datasets.py
import csv, yaml, os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------
# CONNECT TO DATABASE
# ---------------------------------
conn = mysql.connector.connect(
    host=os.environ["DB_HOST"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASS"],
    database=os.environ["DB_NAME"],
    port=int(os.environ.get("DB_PORT", 3306))
)
cur = conn.cursor()

# ---------------------------------
# FILE PATHS
# ---------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "symptoms_data.csv")
YAML_PATH = os.path.join(BASE_DIR, "data", "triage_rules.yaml")

print("Loading data from:", CSV_PATH)

# ---------------------------------
# 1. LOAD symptoms_data.csv
# ---------------------------------
with open(CSV_PATH, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    
    for idx, row in enumerate(reader, start=1):
        symptom = (row.get("symptom") or "").strip().lower()
        disease = (row.get("disease") or "").strip()
        severity = (row.get("severity_level") or row.get("severity") or "").strip()
        danger = int(row.get("danger_flag") or 0)
        description = (row.get("description") or "").strip()
        precautions = (row.get("precautions") or "").strip()
        duration_rules = (row.get("duration_rules") or "").strip()
        risk_level = (row.get("risk_level") or "").strip()

        cur.execute("""
            INSERT INTO symptoms_data 
            (id, symptom, disease, severity_level, danger_flag, description, precautions, duration_rules, risk_level)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            idx,  # auto-generated ID
            symptom, disease, severity, danger,
            description, precautions, duration_rules, risk_level
        ))

print("CSV data inserted.")

# ---------------------------------
# 2. LOAD triage_rules.yaml
# ---------------------------------
with open(YAML_PATH, "r", encoding="utf-8") as f:
    rules = yaml.safe_load(f)

danger_list = rules.get("danger", []) or rules.get("emergency", [])

for idx, item in enumerate(danger_list, start=10000):  # large IDs to avoid collision
    cur.execute("""
        INSERT INTO symptoms_data
        (id, symptom, disease, severity_level, danger_flag, description, precautions, duration_rules, risk_level)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        idx,
        item.lower(),
        "Emergency condition",
        "severe",
        1,
        "Immediate medical attention required.",
        "Go to the nearest hospital, call emergency services.",
        "0 hours",
        "critical"
    ))

print("YAML emergency rules inserted.")

# ---------------------------------
# COMMIT AND CLOSE
# ---------------------------------
conn.commit()
cur.close()
conn.close()

print("✅ Data loading complete.")

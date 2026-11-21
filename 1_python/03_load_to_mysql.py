"""
STEP 2B-EASY (Python -> MySQL) - Load the cleaned CSVs into MySQL without any server settings.

Run AFTER you have run 2_mysql/01_schema.sql (the empty tables must exist).
    python 03_load_to_mysql.py
It asks for your MySQL password. (Or set env vars MYSQL_USER / MYSQL_PASSWORD / MYSQL_HOST / MYSQL_PORT.)
"""
import os
from getpass import getpass
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

CLEAN = Path(__file__).resolve().parent.parent / "data" / "clean"

user = os.getenv("MYSQL_USER") or input("MySQL user [root]: ") or "root"
pwd = os.getenv("MYSQL_PASSWORD") or getpass("MySQL password: ")
host = os.getenv("MYSQL_HOST", "localhost")
port = int(os.getenv("MYSQL_PORT", "3306"))

engine = create_engine(URL.create("mysql+pymysql", username=user, password=pwd, host=host, port=port,
                                  database="bank_retention"))

def load(table, df):
    df.to_sql(table, engine, if_exists="append", index=False, chunksize=5000)
    print(f"  loaded {len(df):>6,} rows into {table}")

with engine.begin() as con:                       # wipe tables first so the script can be re-run safely
    con.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    for t in ["monthly_activity", "complaints", "customer_scores", "customers"]:
        con.execute(text(f"DELETE FROM {t}"))
    con.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

print("Loading...")
cust = pd.read_csv(CLEAN / "customers_clean.csv")
cust["churn_date"] = cust["churn_date"].where(cust["churn_date"].notna(), None)     # blank -> NULL
cust["exit_reason"] = cust["exit_reason"].where(cust["exit_reason"].notna(), None)
load("customers", cust)
load("monthly_activity", pd.read_csv(CLEAN / "monthly_activity.csv"))
load("complaints", pd.read_csv(CLEAN / "complaints.csv"))

scored = pd.read_csv(CLEAN / "customer_scored.csv")
cols = ["customer_id", "tenure_years", "txn_avg_first3", "txn_avg_last3", "avg_app_logins", "upi_share",
        "txn_change_pct", "complaints", "unresolved_complaints", "churn_probability", "est_annual_revenue",
        "value_3yr", "revenue_at_risk", "value_segment", "risk_band", "recommended_action", "risk_decile"]
load("customer_scores", scored[cols])
print("Done. Now open 2_mysql/03_data_quality_checks.sql")

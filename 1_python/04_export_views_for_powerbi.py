"""
STEP 4-OPTIONAL (Python) - Export the MySQL views to CSV for Power BI.

Use this ONLY if Power BI cannot connect to MySQL directly (it needs the 'MySQL Connector/NET' driver).
Run AFTER 2_mysql/05_views_and_procedure.sql.   python 04_export_views_for_powerbi.py
Creates  data/powerbi_csv/v_customer_360.csv, v_monthly_activity.csv, v_complaints.csv
"""
import os
from getpass import getpass
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

OUT = Path(__file__).resolve().parent.parent / "data" / "powerbi_csv"; OUT.mkdir(parents=True, exist_ok=True)
user = os.getenv("MYSQL_USER") or input("MySQL user [root]: ") or "root"
pwd = os.getenv("MYSQL_PASSWORD") or getpass("MySQL password: ")
engine = create_engine(URL.create("mysql+pymysql", username=user, password=pwd,
                                  host=os.getenv("MYSQL_HOST", "localhost"), port=int(os.getenv("MYSQL_PORT", "3306")),
                                  database="bank_retention"))
for view in ["v_customer_360", "v_monthly_activity", "v_complaints"]:
    df = pd.read_sql(f"SELECT * FROM {view}", engine)
    df.to_csv(OUT / f"{view}.csv", index=False)
    print(f"{view}: {len(df):,} rows -> {OUT / (view + '.csv')}")

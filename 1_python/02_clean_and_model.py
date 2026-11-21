"""
STEP 1B (Python) - Clean -> Engineer features -> Predict churn -> Put a Rupee value on it.

Run:  python 02_clean_and_model.py          (after 01_generate_data.py)

Reads : ../data/raw/*.csv
Writes: ../data/clean/customers_clean.csv
        ../data/clean/customer_scored.csv      <- the MAIN table used by MySQL, Excel, Power BI
        ../data/clean/monthly_activity.csv, complaints.csv (copied, ready for MySQL)
        ../1_python/charts/*.png               <- screenshots for your portfolio / README
        ../5_resume/resume_bullets.md          <- bullets auto-filled with YOUR real numbers
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, roc_curve, precision_score, recall_score

ROOT = Path(__file__).resolve().parent.parent
RAW, CLEAN = ROOT / "data" / "raw", ROOT / "data" / "clean"
CHARTS = Path(__file__).resolve().parent / "charts"
CLEAN.mkdir(parents=True, exist_ok=True); CHARTS.mkdir(exist_ok=True)
log = []                                   # we collect a "cleaning report" as we go

def note(msg):
    print(msg); log.append(msg)

# =====================================================================
# PART 1 - CLEANING   (one problem at a time, always print what you fixed)
# =====================================================================
cust = pd.read_csv(RAW / "customers_raw.csv")
act = pd.read_csv(RAW / "monthly_activity.csv")
comp = pd.read_csv(RAW / "complaints.csv")
note(f"Raw customers rows: {len(cust):,}")

# 1. duplicates
dups = cust.duplicated().sum()
cust = cust.drop_duplicates().reset_index(drop=True)
note(f"[1] Removed {dups} duplicate rows -> {len(cust):,} rows left")

# 2. gender spelling:  'M', 'male', ' Female', 'FEMALE'  ->  'Male' / 'Female'
cust["gender"] = (cust["gender"].str.strip().str.lower()
                  .map({"m": "Male", "male": "Male", "f": "Female", "female": "Female"}))
note(f"[2] Standardised gender -> {cust['gender'].value_counts().to_dict()}")

# 3. city: remove spaces and fix CAPITALS
cust["city"] = cust["city"].str.strip().str.title()
note(f"[3] Cleaned city names -> {cust['city'].nunique()} unique cities")

# 4. impossible ages -> blank -> fill with median age
bad_age = ~cust["age"].between(18, 90)
cust.loc[bad_age, "age"] = np.nan
cust["age"] = cust["age"].fillna(cust["age"].median())
note(f"[4] Fixed {bad_age.sum()} impossible ages (0, -5, 150, 999) with the median age")

# 5. missing values -> fill with the median of similar customers (same account type)
miss_cs, miss_inc = cust["credit_score"].isna().sum(), cust["annual_income"].isna().sum()
cust["credit_score"] = cust["credit_score"].fillna(cust.groupby("account_type")["credit_score"].transform("median"))
cust["annual_income"] = cust["annual_income"].fillna(cust.groupby("account_type")["annual_income"].transform("median"))
note(f"[5] Filled {miss_cs} missing credit scores and {miss_inc} missing incomes (median by account type)")

for c in ["age", "credit_score", "annual_income"]:      # whole numbers only (so MySQL loads them cleanly)
    cust[c] = cust[c].round().astype(int)
cust["join_date"] = pd.to_datetime(cust["join_date"])
cust["tenure_years"] = ((pd.Timestamp("2026-06-30") - cust["join_date"]).dt.days / 365.25).round(1)
assert cust["customer_id"].is_unique, "customer_id must be unique after cleaning!"

# =====================================================================
# PART 2 - FEATURE ENGINEERING  (turn raw tables into 'signals' about each customer)
# =====================================================================
act["month"] = pd.to_datetime(act["month"])
first3 = act[act["month"] < "2026-04-01"].groupby("customer_id")["txn_count"].mean().rename("txn_avg_first3")
last3 = act[act["month"] >= "2026-04-01"].groupby("customer_id")["txn_count"].mean().rename("txn_avg_last3")
logins = act.groupby("customer_id")["app_logins"].mean().rename("avg_app_logins")
upi = (act.groupby("customer_id")["upi_txn_count"].sum() / act.groupby("customer_id")["txn_count"].sum().clip(lower=1)).rename("upi_share")
feat = pd.concat([first3, last3, logins, upi], axis=1).reset_index()
feat["txn_change_pct"] = ((feat["txn_avg_last3"] - feat["txn_avg_first3"]) / feat["txn_avg_first3"].clip(lower=1)).round(3)

comp_f = comp.groupby("customer_id").agg(complaints=("complaint_id", "count"),
                                        unresolved_complaints=("is_resolved", lambda s: (s == 0).sum())).reset_index()
df = cust.merge(feat, on="customer_id", how="left").merge(comp_f, on="customer_id", how="left")
df[["complaints", "unresolved_complaints"]] = df[["complaints", "unresolved_complaints"]].fillna(0).astype(int)
note(f"[6] Built behaviour features: txn trend, app logins, UPI share, complaints -> {df.shape[1]} columns")

# =====================================================================
# PART 3 - CHURN MODEL
# Rule: use ONLY information from Jan-Jun. 'exit_reason' and 'churn_date' are
# known only AFTER churn, so we never feed them to the model (data leakage!).
# =====================================================================
X = pd.get_dummies(df[["age", "tenure_years", "annual_income", "credit_score", "avg_monthly_balance",
                       "products_held", "has_credit_card", "has_loan", "loan_amount", "uses_mobile_app",
                       "txn_avg_first3", "txn_avg_last3", "txn_change_pct", "avg_app_logins", "upi_share",
                       "complaints", "unresolved_complaints", "account_type", "city_tier"]],
                   columns=["account_type", "city_tier"], drop_first=True).astype(float)
y = df["churned_next_90d"]

cv = StratifiedKFold(5, shuffle=True, random_state=42)
models = {
    "Logistic Regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),
    "Random Forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=25, random_state=42, n_jobs=-1),
}
oof, auc = {}, {}
for name, m in models.items():
    # out-of-fold = every customer is scored by a model that NEVER saw that customer
    oof[name] = cross_val_predict(m, X, y, cv=cv, method="predict_proba")[:, 1]
    auc[name] = roc_auc_score(y, oof[name])
    note(f"[7] {name:<20} ROC-AUC = {auc[name]:.3f}")
best = max(auc, key=auc.get)
df["churn_probability"] = oof[best].round(4)
note(f"[8] Best model: {best}. Its probabilities are used for every customer.")

# at a simple cut-off (top-20% riskiest) how good are we?
cut = df["churn_probability"].quantile(0.80)
pred = (df["churn_probability"] >= cut).astype(int)
prec, rec = precision_score(y, pred), recall_score(y, pred)
note(f"[9] Flagging the riskiest 20% catches {rec:.0%} of all churners (precision {prec:.0%}; base rate {y.mean():.1%})")

# =====================================================================
# PART 4 - BUSINESS LAYER  (this is what makes the project different)
# =====================================================================
# Assumptions (also shown in Excel). Change them if you like - just state them in your README.
df["est_annual_revenue"] = (0.03 * df["avg_monthly_balance"]        # 3% spread on deposits
                            + 0.035 * df["loan_amount"]             # 3.5% spread on loans
                            + 1500 * df["has_credit_card"]          # card fees + interchange
                            + 300 * df["products_held"]).round(0)   # service fees per product
PV_FACTOR = round(sum(1 / 1.10 ** t for t in (1, 2, 3)), 3)         # 3 years discounted at 10% = 2.487
df["value_3yr"] = (df["est_annual_revenue"] * PV_FACTOR).round(0)
df["revenue_at_risk"] = (df["churn_probability"] * df["value_3yr"]).round(0)

# value segment: Premium = top 20% by revenue, Core = next 50%, Emerging = bottom 30%
q80, q30 = df["est_annual_revenue"].quantile(.80), df["est_annual_revenue"].quantile(.30)
df["value_segment"] = np.select([df["est_annual_revenue"] >= q80, df["est_annual_revenue"] >= q30],
                                ["Premium", "Core"], default="Emerging")
# risk band
df["risk_band"] = np.select([df["churn_probability"] >= 0.25, df["churn_probability"] >= 0.12],
                            ["High", "Medium"], default="Low")

# THE RETENTION PRIORITY MATRIX: value x risk -> what should the bank DO?
action = {
    ("Premium", "High"): "RM Personal Call", ("Premium", "Medium"): "Proactive Check-in",
    ("Core", "High"): "Fee Waiver + Cashback Offer", ("Core", "Medium"): "Targeted App Nudge",
    ("Emerging", "High"): "Automated SMS / App Nudge",
}
df["recommended_action"] = [action.get((v, r), "Monitor Only") for v, r in zip(df["value_segment"], df["risk_band"])]
df["risk_decile"] = pd.qcut(df["churn_probability"].rank(method="first"), 10, labels=range(1, 11)).astype(int)

# ---- numbers for the story ----
total_rev, total_rar = df["est_annual_revenue"].sum(), df["revenue_at_risk"].sum()
hi = df[df["risk_band"] == "High"]
top_cut = df["revenue_at_risk"].quantile(.80)
pareto = df.loc[df["revenue_at_risk"] >= top_cut, "revenue_at_risk"].sum() / total_rar
note(f"[10] 3-year value at risk = Rs {total_rar/1e7:,.2f} crore | High-risk customers = {len(hi):,} ({len(hi)/len(df):.0%})")
note(f"[11] Top 20% of customers (by value at risk) hold {pareto:.0%} of all value at risk -> focus the budget there")

# calibration check (predicted vs actual churn by decile) - proves probabilities are trustworthy
calib = df.groupby("risk_decile").agg(predicted=("churn_probability", "mean"), actual=("churned_next_90d", "mean")).round(3)
print("\nCalibration by risk decile:\n", calib)

# =====================================================================
# PART 5 - SAVE FILES
# =====================================================================
df["join_date"] = df["join_date"].dt.strftime("%Y-%m-%d")
df["churn_date"] = df["churn_date"].fillna("")
df["exit_reason"] = df["exit_reason"].fillna("")
df.to_csv(CLEAN / "customer_scored.csv", index=False)
df[["customer_id", "age", "gender", "city", "city_tier", "account_type", "join_date", "annual_income",
    "credit_score", "avg_monthly_balance", "products_held", "has_credit_card", "has_loan", "loan_amount",
    "uses_mobile_app", "churned_next_90d", "churn_date", "exit_reason"]].to_csv(CLEAN / "customers_clean.csv", index=False)
act["month"] = act["month"].dt.strftime("%Y-%m-%d")
act.to_csv(CLEAN / "monthly_activity.csv", index=False)
comp["days_to_resolve"] = comp["days_to_resolve"].astype("Int64")   # whole days, blank when unresolved
comp.to_csv(CLEAN / "complaints.csv", index=False)
pd.Series(log).to_csv(CLEAN / "cleaning_log.txt", index=False, header=False)

# ---- charts ----
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(6, 4.2))
for name, p in oof.items():
    fpr, tpr, _ = roc_curve(y, p); ax.plot(fpr, tpr, label=f"{name} (AUC {auc[name]:.2f})")
ax.plot([0, 1], [0, 1], "--", color="grey"); ax.set(xlabel="False positive rate", ylabel="True positive rate", title="Churn model - ROC curve")
ax.legend(); fig.tight_layout(); fig.savefig(CHARTS / "roc_curve.png", dpi=150); plt.close(fig)

if best == "Random Forest":
    imp = pd.Series(models[best].fit(X, y).feature_importances_, index=X.columns)
else:
    lr = models[best].fit(X, y); imp = pd.Series(np.abs(lr[-1].coef_[0]), index=X.columns)
imp = imp.sort_values().tail(10)
fig, ax = plt.subplots(figsize=(6.5, 4.2)); imp.plot.barh(ax=ax, color="#1f6f8b")
ax.set(title="Top 10 churn drivers"); fig.tight_layout(); fig.savefig(CHARTS / "churn_drivers.png", dpi=150); plt.close(fig)

fig, ax = plt.subplots(figsize=(6.5, 4.2))
d = calib.reset_index(); ax.plot(d["risk_decile"], d["predicted"], marker="o", label="Predicted")
ax.plot(d["risk_decile"], d["actual"], marker="s", label="Actual"); ax.set(xlabel="Risk decile (10 = riskiest)", ylabel="Churn rate", title="Are the probabilities trustworthy?")
ax.legend(); fig.tight_layout(); fig.savefig(CHARTS / "calibration.png", dpi=150); plt.close(fig)

seg = df.pivot_table(index="value_segment", columns="risk_band", values="revenue_at_risk", aggfunc="sum").reindex(["Premium", "Core", "Emerging"])
seg = seg[[c for c in ["High", "Medium", "Low"] if c in seg.columns]] / 1e5
fig, ax = plt.subplots(figsize=(6.5, 4.2)); seg.plot.bar(stacked=True, ax=ax, color=["#c0392b", "#e6a23c", "#95a5a6"][:seg.shape[1]], rot=0)
ax.set(title="3-year value at risk (Rs lakh)", xlabel="", ylabel="Rs lakh"); fig.tight_layout(); fig.savefig(CHARTS / "value_at_risk_matrix.png", dpi=150); plt.close(fig)

# ---- resume bullets filled with YOUR numbers ----
bullets = f"""# Resume bullets (auto-filled from your own run)

**Project title:** Bank Retention Command Center - Churn Prediction, Revenue-at-Risk & Intervention ROI
**Tools:** Python (pandas, scikit-learn), MySQL, Excel, Power BI | **Data:** synthetic 10,000-customer retail-bank dataset

- Cleaned and merged 3 relational tables ({len(cust):,} customers, {len(act):,} monthly activity rows, {len(comp):,} complaints) in Python; fixed duplicates, inconsistent labels, impossible values and missing data.
- Built a churn model ({best}, out-of-fold ROC-AUC {auc[best]:.2f}) that flags the riskiest 20% of customers and catches {rec:.0%} of all churners, using leakage-safe time windows.
- Converted churn probability into Rs {total_rar/1e7:,.2f} crore of 3-year customer value at risk and a Value x Risk retention matrix; the top 20% of customers hold {pareto:.0%} of the exposure.
- Wrote MySQL queries using CTEs, window functions, views and aggregations to analyse customer churn patterns.
- Built an Excel retention ROI simulator using budget, cost-per-action and save-rate assumptions.
- Created a one-page Power BI dashboard with customer KPIs, churn analysis, risk segmentation and retention action insights.
"""

resume_dir = ROOT / "5_resume"
resume_dir.mkdir(parents=True, exist_ok=True)
(resume_dir / "resume_bullets.md").write_text(bullets, encoding="utf-8")

print("\nDONE. Files written to data/clean, charts in 1_python/charts, bullets in 5_resume/resume_bullets.md")


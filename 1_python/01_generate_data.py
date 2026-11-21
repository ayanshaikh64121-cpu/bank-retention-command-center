import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)          # fixed seed -> same data every run
N = 10_000
OUT = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

# ---------- 1. customer profile ----------
cities = {  # city: (tier, weight)
    "Mumbai": ("Metro", .13), "Delhi": ("Metro", .13), "Bengaluru": ("Metro", .12),
    "Hyderabad": ("Metro", .11), "Chennai": ("Metro", .08), "Kolkata": ("Metro", .07),
    "Pune": ("Tier-2", .09), "Ahmedabad": ("Tier-2", .08), "Jaipur": ("Tier-2", .06),
    "Lucknow": ("Tier-2", .05), "Indore": ("Tier-2", .04), "Patna": ("Tier-2", .04),
}
city_names = list(cities)
weights = np.array([v[1] for v in cities.values()])
city = rng.choice(city_names, N, p=weights / weights.sum())

age = np.clip(rng.normal(38, 11, N), 18, 80).round().astype(int)
gender = rng.choice(["Male", "Female"], N, p=[.55, .45])
account_type = rng.choice(["Savings", "Salary", "Current"], N, p=[.55, .30, .15])
join_date = pd.to_datetime("2026-06-30") - pd.to_timedelta(rng.integers(30, 365 * 11, N), unit="D")
tenure_years = ((pd.Timestamp("2026-06-30") - join_date).days / 365.25).round(1)

income = np.clip(rng.lognormal(13.3, .55, N), 150_000, 8_000_000).round(-3)          # Rs per year
credit_score = np.clip(rng.normal(715, 70, N), 300, 900).round().astype(int)
avg_balance = np.clip(income * rng.uniform(.02, .9, N) * rng.lognormal(0, .5, N), 500, 6_000_000).round(0)
products = rng.choice([1, 2, 3, 4], N, p=[.38, .34, .20, .08])
has_credit_card = (rng.random(N) < .30 + .12 * (products - 1)).astype(int)
has_loan = (rng.random(N) < .12 + .08 * (products - 1)).astype(int)
loan_amount = np.where(has_loan == 1, (income * rng.uniform(.5, 3, N)).round(-3), 0)
app_user = (rng.random(N) < np.clip(.85 - (age - 18) * .008, .25, .9)).astype(int)

# ---------- 2. complaints ----------
n_comp = 3_000
comp_cust = rng.choice(N, n_comp)
comp_date = pd.to_datetime("2026-01-01") + pd.to_timedelta(rng.integers(0, 181, n_comp), unit="D")
comp_cat = rng.choice(["Hidden Charges", "ATM / Card Issue", "Net Banking Issue", "Loan Service", "Branch Service"],
                      n_comp, p=[.28, .24, .22, .12, .14])
resolved = rng.random(n_comp) < .72
resolve_days = np.where(resolved, rng.integers(1, 15, n_comp), np.nan)
complaints = pd.DataFrame({
    "complaint_id": [f"CMP{i:05d}" for i in range(1, n_comp + 1)],
    "customer_id": [f"C{c + 1:05d}" for c in comp_cust],
    "complaint_date": comp_date.date, "category": comp_cat,
    "is_resolved": resolved.astype(int), "days_to_resolve": resolve_days,
})
unresolved_cnt = np.bincount(comp_cust[~resolved], minlength=N)
complaint_cnt = np.bincount(comp_cust, minlength=N)

# ---------- 3. hidden "churn risk" -> real churn (Jul-Sep) ----------
z = (-2.2
     + 0.03 * np.abs(age - 45)                    # very young / older customers leave a bit more
     + 0.8 * (products == 1)                      # single-product customers leave more
     - 0.5 * (products >= 3)
     - 0.7 * (account_type == "Salary")           # salary accounts are sticky
     + 0.5 * (app_user == 0)
     + 0.55 * unresolved_cnt + 0.15 * complaint_cnt
     - 0.25 * np.log1p(tenure_years)
     - 0.0000002 * avg_balance
     + 0.35 * (credit_score < 620)
     + 0.3 * (city == "Delhi")
     + rng.normal(0, .5, N))
p_churn = 1 / (1 + np.exp(-z))
churned = (rng.random(N) < p_churn).astype(int)

exit_reasons = np.array(["Better interest elsewhere", "High charges", "Poor service", "Moved city",
                         "Switched to digital-only bank", "Loan refinanced elsewhere"])
exit_reason = np.where(churned == 1, rng.choice(exit_reasons, N), "")
churn_dt = pd.to_datetime("2026-07-01") + pd.to_timedelta(rng.integers(0, 92, N), unit="D")
churn_date = np.where(churned == 1, churn_dt.strftime("%Y-%m-%d"), "")

# ---------- 4. monthly activity (Jan-Jun): churners slowly disengage ----------
base_txn = np.clip(rng.lognormal(2.6, .5, N) * (1 + .4 * app_user), 1, 200)
base_amt = np.clip(avg_balance * rng.uniform(.15, .5, N), 500, None)
cust_ids = [f"C{i + 1:05d}" for i in range(N)]
# Real life is messy: only ~75% of churners slowly fade (others leave suddenly),
# and ~6% of loyal customers also go quiet for a while (false alarms).
fades = np.where(churned == 1, rng.random(N) < .75, rng.random(N) < .06)
rows = []
for m, month in enumerate(pd.date_range("2026-01-01", periods=6, freq="MS")):
    decay = np.where(fades, 1 - 0.09 * m * rng.uniform(.3, 1.7, N), 1.0)   # 'fading' customers disengage each month
    decay = np.clip(decay * rng.uniform(.8, 1.2, N), .05, 1.3)
    txn = rng.poisson(base_txn * decay * rng.uniform(.85, 1.15, N))
    amt = (base_amt * decay * rng.uniform(.7, 1.3, N)).round(0)
    upi = (txn * np.clip(rng.normal(.6 + .2 * app_user, .1, N), 0, 1)).round().astype(int)
    login = rng.poisson(np.where(app_user == 1, 14, 1) * decay)
    rows.append(pd.DataFrame({"customer_id": cust_ids, "month": month.date(), "txn_count": txn,
                              "txn_amount": amt, "upi_txn_count": upi, "app_logins": login}))
activity = pd.concat(rows, ignore_index=True)

# ---------- 5. assemble customers + make it MESSY ----------
cust = pd.DataFrame({
    "customer_id": cust_ids, "age": age, "gender": gender, "city": city,
    "city_tier": [cities[c][0] for c in city], "account_type": account_type,
    "join_date": join_date.date, "annual_income": income, "credit_score": credit_score.astype(float),
    "avg_monthly_balance": avg_balance, "products_held": products, "has_credit_card": has_credit_card,
    "has_loan": has_loan, "loan_amount": loan_amount, "uses_mobile_app": app_user,
    "churned_next_90d": churned, "churn_date": churn_date, "exit_reason": exit_reason,
})
# mess 1: inconsistent gender spelling
idx = rng.choice(N, 600, replace=False)
cust.loc[idx, "gender"] = rng.choice(["M", "F", "male", "FEMALE", " Female"], 600)
# mess 2: city with spaces / wrong case
idx = rng.choice(N, 500, replace=False)
cust.loc[idx, "city"] = cust.loc[idx, "city"].str.upper() + " "
# mess 3: missing values
cust.loc[rng.choice(N, 300, replace=False), "credit_score"] = np.nan
cust.loc[rng.choice(N, 250, replace=False), "annual_income"] = np.nan
# mess 4: impossible ages
cust.loc[rng.choice(N, 12, replace=False), "age"] = rng.choice([0, 150, 999, -5], 12)
# mess 5: duplicate rows
cust = pd.concat([cust, cust.sample(80, random_state=1)], ignore_index=True)

cust.to_csv(OUT / "customers_raw.csv", index=False)
activity.to_csv(OUT / "monthly_activity.csv", index=False)
complaints.to_csv(OUT / "complaints.csv", index=False)
print(f"customers_raw.csv   : {len(cust):,} rows (includes 80 duplicates)")
print(f"monthly_activity.csv: {len(activity):,} rows")
print(f"complaints.csv      : {len(complaints):,} rows")
print(f"overall churn rate  : {churned.mean():.1%}")

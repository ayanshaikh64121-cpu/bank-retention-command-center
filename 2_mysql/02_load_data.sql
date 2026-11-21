-- =====================================================================
-- STEP 2B (MySQL) - Load the CSV files into the tables
-- ---------------------------------------------------------------------
-- TWO WAYS. Pick ONE:
--   EASY WAY  : run   python 1_python/03_load_to_mysql.py   (no setup, recommended for beginners)
--   SQL WAY   : use the LOAD DATA commands below.
--               Needs:  (a) connection setting  OPT_LOCAL_INFILE=1
--                       (b) once:  SET GLOBAL local_infile = 1;   (run as root)
--               CHANGE the path below to where YOUR project folder is.
--               Use forward slashes even on Windows, e.g. 'C:/Users/Ayan/bank-retention-project/data/clean/...'
-- =====================================================================
USE bank_retention;
SET GLOBAL local_infile = 1;

SET FOREIGN_KEY_CHECKS = 0;

LOAD DATA LOCAL INFILE 'C:/PATH/TO/bank-retention-project/data/clean/customers_clean.csv'
INTO TABLE customers
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(customer_id, age, gender, city, city_tier, account_type, join_date, annual_income, credit_score,
 avg_monthly_balance, products_held, has_credit_card, has_loan, loan_amount, uses_mobile_app,
 churned_next_90d, @churn_date, @exit_reason)
SET churn_date = NULLIF(TRIM(@churn_date), ''),
    exit_reason = NULLIF(TRIM(REPLACE(@exit_reason, '\r', '')), '');

LOAD DATA LOCAL INFILE 'C:/PATH/TO/bank-retention-project/data/clean/monthly_activity.csv'
INTO TABLE monthly_activity
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(customer_id, month, txn_count, txn_amount, upi_txn_count, app_logins);

LOAD DATA LOCAL INFILE 'C:/PATH/TO/bank-retention-project/data/clean/complaints.csv'
INTO TABLE complaints
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(complaint_id, customer_id, complaint_date, category, is_resolved, @days)
SET days_to_resolve = NULLIF(TRIM(REPLACE(@days, '\r', '')), '');

-- customer_scored.csv has 34 columns, we only keep the ones our table needs
LOAD DATA LOCAL INFILE 'C:/PATH/TO/bank-retention-project/data/clean/customer_scored.csv'
INTO TABLE customer_scores
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(customer_id, @age, @gender, @city, @city_tier, @account_type, @join_date, @income, @credit, @balance,
 @products, @cc, @loan, @loan_amt, @app, @churned, @churn_date, @exit_reason,
 tenure_years, txn_avg_first3, txn_avg_last3, avg_app_logins, upi_share, txn_change_pct,
 complaints, unresolved_complaints, churn_probability, est_annual_revenue, value_3yr,
 revenue_at_risk, value_segment, risk_band, recommended_action, risk_decile);

SET FOREIGN_KEY_CHECKS = 1;

-- Quick check: expect 10000 / 60000 / 3000 / 10000
SELECT 'customers' AS tbl, COUNT(*) AS rows_loaded FROM customers
UNION ALL SELECT 'monthly_activity', COUNT(*) FROM monthly_activity
UNION ALL SELECT 'complaints', COUNT(*) FROM complaints
UNION ALL SELECT 'customer_scores', COUNT(*) FROM customer_scores;

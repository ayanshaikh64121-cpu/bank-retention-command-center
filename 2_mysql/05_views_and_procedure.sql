-- =====================================================================
-- STEP 2E (MySQL) - Views for Power BI + a reusable stored procedure
-- A VIEW is a saved query that behaves like a table. Power BI connects to these views,
-- so all the business logic lives in ONE place (SQL), not scattered in the dashboard.
-- =====================================================================
USE bank_retention;

-- 1) The customer 360 table: one row per customer, everything Power BI needs
CREATE OR REPLACE VIEW v_customer_360 AS
SELECT c.customer_id, c.age,
       CASE WHEN c.age < 26 THEN '18-25' WHEN c.age < 36 THEN '26-35' WHEN c.age < 46 THEN '36-45'
            WHEN c.age < 61 THEN '46-60' ELSE '60+' END                       AS age_band,
       c.gender, c.city, c.city_tier, c.account_type, c.join_date, YEAR(c.join_date) AS join_year,
       CASE WHEN s.tenure_years < 2 THEN '0-2 yrs' WHEN s.tenure_years < 5 THEN '2-5 yrs'
            WHEN s.tenure_years < 8 THEN '5-8 yrs' ELSE '8+ yrs' END          AS tenure_band,
       c.annual_income, c.credit_score, c.avg_monthly_balance, c.products_held,
       c.has_credit_card, c.has_loan, c.loan_amount, c.uses_mobile_app,
       c.churned_next_90d, c.exit_reason,
       s.txn_avg_first3, s.txn_avg_last3, s.txn_change_pct, s.avg_app_logins, s.upi_share,
       s.complaints, s.unresolved_complaints,
       s.churn_probability, s.est_annual_revenue, s.value_3yr, s.revenue_at_risk,
       s.value_segment, s.risk_band, s.recommended_action, s.risk_decile
FROM customers c
JOIN customer_scores s ON s.customer_id = c.customer_id;

-- 2) Monthly activity enriched with segment info (for trend charts)
CREATE OR REPLACE VIEW v_monthly_activity AS
SELECT a.customer_id, a.month, a.txn_count, a.txn_amount, a.upi_txn_count, a.app_logins,
       c.churned_next_90d, s.value_segment, s.risk_band
FROM monthly_activity a
JOIN customers c ON c.customer_id = a.customer_id
JOIN customer_scores s ON s.customer_id = a.customer_id;

-- 3) Complaints enriched (for the service-quality page)
CREATE OR REPLACE VIEW v_complaints AS
SELECT cp.complaint_id, cp.customer_id, cp.complaint_date, cp.category, cp.is_resolved,
       cp.days_to_resolve, c.churned_next_90d, s.value_segment
FROM complaints cp
JOIN customers c ON c.customer_id = cp.customer_id
JOIN customer_scores s ON s.customer_id = cp.customer_id;

-- 4) Action-level summary (feeds the Excel ROI model and a Power BI table)
CREATE OR REPLACE VIEW v_action_summary AS
SELECT recommended_action,
       COUNT(*)                          AS customers,
       ROUND(AVG(churn_probability), 3)  AS avg_churn_probability,
       SUM(revenue_at_risk)              AS value_at_risk,
       ROUND(AVG(value_3yr), 0)          AS avg_3yr_value
FROM customer_scores
GROUP BY recommended_action;

-- 5) Stored procedure: "give me the top N customers to call in a city"
DROP PROCEDURE IF EXISTS sp_watchlist;
DELIMITER //
CREATE PROCEDURE sp_watchlist(IN p_city VARCHAR(30), IN p_limit INT)
BEGIN
    SELECT customer_id, value_segment, risk_band, ROUND(churn_probability, 2) AS churn_prob,
           revenue_at_risk, recommended_action
    FROM v_customer_360
    WHERE city = p_city
    ORDER BY revenue_at_risk DESC
    LIMIT p_limit;
END //
DELIMITER ;

-- Try it:
-- CALL sp_watchlist('Hyderabad', 10);
SELECT * FROM v_action_summary ORDER BY value_at_risk DESC;

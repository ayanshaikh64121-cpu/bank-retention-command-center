-- =====================================================================
-- STEP 2D (MySQL) - Business analysis (needs MySQL 8.0+ for CTEs and window functions)
-- 15 questions a retention manager would really ask. Each one = a screenshot + one insight line.
-- =====================================================================
USE bank_retention;

-- ---------------------------------------------------------------------
-- Q1. Headline numbers
-- ---------------------------------------------------------------------
SELECT COUNT(*)                                             AS customers,
       SUM(c.churned_next_90d)                              AS churners,
       ROUND(100 * AVG(c.churned_next_90d), 1)              AS churn_rate_pct,
       ROUND(SUM(s.est_annual_revenue) / 1e7, 2)            AS annual_revenue_crore,
       ROUND(SUM(s.revenue_at_risk) / 1e7, 2)               AS value_at_risk_3yr_crore
FROM customers c JOIN customer_scores s USING (customer_id);

-- ---------------------------------------------------------------------
-- Q2. Which account type / city tier leaks the most?
-- ---------------------------------------------------------------------
SELECT account_type, city_tier,
       COUNT(*) AS customers,
       ROUND(100 * AVG(churned_next_90d), 1) AS churn_rate_pct
FROM customers
GROUP BY account_type, city_tier
ORDER BY churn_rate_pct DESC;

-- ---------------------------------------------------------------------
-- Q3. Do new customers leave faster? (tenure bands with CASE)
-- ---------------------------------------------------------------------
SELECT CASE WHEN tenure_years < 2  THEN '1) Under 2 yrs'
            WHEN tenure_years < 5  THEN '2) 2-5 yrs'
            WHEN tenure_years < 8  THEN '3) 5-8 yrs'
            ELSE                        '4) 8+ yrs' END AS tenure_band,
       COUNT(*) AS customers,
       ROUND(100 * AVG(c.churned_next_90d), 1) AS churn_rate_pct
FROM customers c JOIN customer_scores s USING (customer_id)
GROUP BY tenure_band
ORDER BY tenure_band;

-- ---------------------------------------------------------------------
-- Q4. Product depth x digital usage ("sticky" customers hold more products and use the app)
-- ---------------------------------------------------------------------
SELECT products_held,
       ROUND(100 * AVG(CASE WHEN uses_mobile_app = 1 THEN churned_next_90d END), 1) AS churn_pct_app_users,
       ROUND(100 * AVG(CASE WHEN uses_mobile_app = 0 THEN churned_next_90d END), 1) AS churn_pct_non_app_users,
       COUNT(*) AS customers
FROM customers
GROUP BY products_held
ORDER BY products_held;

-- ---------------------------------------------------------------------
-- Q5. Do UNRESOLVED complaints push people out?
-- ---------------------------------------------------------------------
SELECT CASE WHEN unresolved_complaints = 0 THEN '0 unresolved'
            WHEN unresolved_complaints = 1 THEN '1 unresolved'
            ELSE '2+ unresolved' END AS complaint_status,
       COUNT(*) AS customers,
       ROUND(100 * AVG(c.churned_next_90d), 1) AS churn_rate_pct
FROM customers c JOIN customer_scores s USING (customer_id)
GROUP BY complaint_status
ORDER BY complaint_status;

-- ---------------------------------------------------------------------
-- Q6. Which complaint CATEGORY is the most dangerous? (and how slow is the fix?)
-- ---------------------------------------------------------------------
SELECT cp.category,
       COUNT(DISTINCT cp.customer_id)                         AS customers_complained,
       ROUND(100 * AVG(cu.churned_next_90d), 1)               AS churn_rate_pct,
       ROUND(AVG(cp.days_to_resolve), 1)                      AS avg_days_to_resolve,
       ROUND(100 * AVG(1 - cp.is_resolved), 1)                AS pct_still_unresolved
FROM complaints cp JOIN customers cu USING (customer_id)
GROUP BY cp.category
ORDER BY churn_rate_pct DESC;

-- ---------------------------------------------------------------------
-- Q7. EARLY WARNING: activity decline (CTE). Last-3-month vs first-3-month transactions.
-- ---------------------------------------------------------------------
WITH half_year AS (
    SELECT customer_id,
           AVG(CASE WHEN month <  '2026-04-01' THEN txn_count END) AS first3,
           AVG(CASE WHEN month >= '2026-04-01' THEN txn_count END) AS last3
    FROM monthly_activity
    GROUP BY customer_id
), banded AS (
    SELECT customer_id,
           CASE WHEN last3 >= first3 * 0.9  THEN '1) Stable / growing'
                WHEN last3 >= first3 * 0.6  THEN '2) Mild decline (10-40%)'
                ELSE                             '3) Sharp decline (>40%)' END AS activity_trend
    FROM half_year
)
SELECT b.activity_trend,
       COUNT(*) AS customers,
       ROUND(100 * AVG(c.churned_next_90d), 1) AS churn_rate_pct
FROM banded b JOIN customers c USING (customer_id)
GROUP BY b.activity_trend
ORDER BY b.activity_trend;

-- ---------------------------------------------------------------------
-- Q8. Month-by-month activity: churners vs stayers, with month-on-month change (LAG)
-- ---------------------------------------------------------------------
WITH monthly AS (
    SELECT a.month, c.churned_next_90d, AVG(a.txn_count) AS avg_txn
    FROM monthly_activity a JOIN customers c USING (customer_id)
    GROUP BY a.month, c.churned_next_90d
)
SELECT month,
       CASE churned_next_90d WHEN 1 THEN 'Churned later' ELSE 'Stayed' END AS group_name,
       ROUND(avg_txn, 2) AS avg_txn,
       ROUND(100 * (avg_txn / LAG(avg_txn) OVER (PARTITION BY churned_next_90d ORDER BY month) - 1), 1) AS mom_change_pct
FROM monthly
ORDER BY group_name, month;

-- ---------------------------------------------------------------------
-- Q9. City league table (RANK) - where is the most money at risk?
-- ---------------------------------------------------------------------
SELECT c.city,
       COUNT(*) AS customers,
       ROUND(100 * AVG(c.churned_next_90d), 1) AS churn_rate_pct,
       ROUND(SUM(s.revenue_at_risk) / 1e5, 1)   AS value_at_risk_lakh,
       RANK() OVER (ORDER BY SUM(s.revenue_at_risk) DESC) AS rank_by_value_at_risk
FROM customers c JOIN customer_scores s USING (customer_id)
GROUP BY c.city
ORDER BY rank_by_value_at_risk;

-- ---------------------------------------------------------------------
-- Q10. WATCH-LIST: top 3 customers to save in every city (ROW_NUMBER inside a CTE)
-- ---------------------------------------------------------------------
WITH ranked AS (
    SELECT c.city, c.customer_id, s.value_segment, s.recommended_action,
           ROUND(s.churn_probability, 2) AS churn_prob, s.revenue_at_risk,
           ROW_NUMBER() OVER (PARTITION BY c.city ORDER BY s.revenue_at_risk DESC) AS rn
    FROM customers c JOIN customer_scores s USING (customer_id)      -- all customers, as seen on 30-Jun-2026
)
SELECT city, rn AS city_rank, customer_id, value_segment, churn_prob, revenue_at_risk, recommended_action
FROM ranked WHERE rn <= 3
ORDER BY city, rn;

-- ---------------------------------------------------------------------
-- Q11. PARETO: how concentrated is the risk? (NTILE + SUM OVER)
-- ---------------------------------------------------------------------
WITH quintiles AS (
    SELECT customer_id, revenue_at_risk,
           NTILE(5) OVER (ORDER BY revenue_at_risk DESC) AS quintile      -- 1 = biggest exposures
    FROM customer_scores
)
SELECT quintile,
       COUNT(*) AS customers,
       SUM(revenue_at_risk) AS value_at_risk,
       ROUND(100 * SUM(revenue_at_risk) / SUM(SUM(revenue_at_risk)) OVER (), 1) AS pct_of_total,
       ROUND(100 * SUM(SUM(revenue_at_risk)) OVER (ORDER BY quintile) / SUM(SUM(revenue_at_risk)) OVER (), 1) AS cumulative_pct
FROM quintiles
GROUP BY quintile
ORDER BY quintile;

-- ---------------------------------------------------------------------
-- Q12. THE RETENTION PRIORITY MATRIX (value segment x risk band) - conditional aggregation
-- ---------------------------------------------------------------------
SELECT value_segment,
       SUM(risk_band = 'High')   AS high_risk_customers,
       SUM(risk_band = 'Medium') AS medium_risk_customers,
       SUM(risk_band = 'Low')    AS low_risk_customers,
       ROUND(SUM(CASE WHEN risk_band = 'High' THEN revenue_at_risk END) / 1e5, 1) AS high_risk_value_lakh
FROM customer_scores
GROUP BY value_segment
ORDER BY FIELD(value_segment, 'Premium', 'Core', 'Emerging');

-- ---------------------------------------------------------------------
-- Q13. Cohorts: churn by the year the customer joined
-- ---------------------------------------------------------------------
SELECT YEAR(join_date) AS join_year,
       COUNT(*) AS customers,
       ROUND(100 * AVG(churned_next_90d), 1) AS churn_rate_pct,
       ROUND(AVG(avg_monthly_balance), 0)    AS avg_balance
FROM customers
GROUP BY YEAR(join_date)
ORDER BY join_year;

-- ---------------------------------------------------------------------
-- Q14. WHY do customers leave? Share of exit reasons inside each value segment
-- ---------------------------------------------------------------------
SELECT s.value_segment, c.exit_reason,
       COUNT(*) AS churners,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY s.value_segment), 1) AS pct_within_segment
FROM customers c JOIN customer_scores s USING (customer_id)
WHERE c.churned_next_90d = 1
GROUP BY s.value_segment, c.exit_reason
ORDER BY FIELD(s.value_segment, 'Premium', 'Core', 'Emerging'), churners DESC;

-- ---------------------------------------------------------------------
-- Q15. MODEL REALITY CHECK: do predicted probabilities match what really happened?
-- ---------------------------------------------------------------------
SELECT s.risk_decile,
       COUNT(*) AS customers,
       ROUND(100 * AVG(s.churn_probability), 1) AS predicted_churn_pct,
       ROUND(100 * AVG(c.churned_next_90d), 1)  AS actual_churn_pct
FROM customer_scores s JOIN customers c USING (customer_id)
GROUP BY s.risk_decile
ORDER BY s.risk_decile;

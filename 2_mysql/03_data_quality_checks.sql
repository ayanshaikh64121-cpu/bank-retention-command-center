-- =====================================================================
-- STEP 2C (MySQL) - Data quality checks ("trust, but verify")
-- Every query below should return the EXPECTED result written in the comment.
-- Screenshot this for your portfolio: it shows you validate data before analysing it.
-- =====================================================================
USE bank_retention;

-- 1. Row counts            EXPECT: 10000 | 60000 | 3000 | 10000
SELECT 'customers' AS tbl, COUNT(*) AS n FROM customers
UNION ALL SELECT 'monthly_activity', COUNT(*) FROM monthly_activity
UNION ALL SELECT 'complaints', COUNT(*) FROM complaints
UNION ALL SELECT 'customer_scores', COUNT(*) FROM customer_scores;

-- 2. Every customer has exactly 6 months of activity      EXPECT: 0 rows
SELECT customer_id, COUNT(*) AS months
FROM monthly_activity GROUP BY customer_id HAVING COUNT(*) <> 6;

-- 3. Orphan check: complaints whose customer does not exist     EXPECT: 0
SELECT COUNT(*) AS orphan_complaints
FROM complaints c LEFT JOIN customers cu ON cu.customer_id = c.customer_id
WHERE cu.customer_id IS NULL;

-- 4. Customers with no score       EXPECT: 0
SELECT COUNT(*) AS customers_without_score
FROM customers c LEFT JOIN customer_scores s ON s.customer_id = c.customer_id
WHERE s.customer_id IS NULL;

-- 5. Range checks           EXPECT: all zeros
SELECT SUM(age NOT BETWEEN 18 AND 90)                AS bad_age,
       SUM(credit_score NOT BETWEEN 300 AND 900)     AS bad_credit_score,
       SUM(avg_monthly_balance < 0)                  AS negative_balance,
       SUM(gender NOT IN ('Male','Female'))          AS bad_gender
FROM customers;

-- 6. Probabilities must be between 0 and 1          EXPECT: 0
SELECT COUNT(*) AS bad_probability FROM customer_scores
WHERE churn_probability NOT BETWEEN 0 AND 1;

-- 7. Churn date only exists for churners            EXPECT: 0
SELECT COUNT(*) AS inconsistent_churn_dates FROM customers
WHERE (churned_next_90d = 0 AND churn_date IS NOT NULL)
   OR (churned_next_90d = 1 AND churn_date IS NULL);

-- 8. Customer value logic: revenue_at_risk = probability x 3-year value (small rounding allowed)   EXPECT: 0
SELECT COUNT(*) AS wrong_value_at_risk FROM customer_scores
WHERE ABS(revenue_at_risk - churn_probability * value_3yr) > 1;

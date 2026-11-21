# Interview Q&A - Bank Retention Command Center

## The 60-second story
"Banks lose customers quietly, and retention budgets are limited. I built a project that doesn't just predict who will leave - it puts a Rupee value on each customer, recommends an action, and simulates whether the campaign pays off. I cleaned three tables in Python, built a churn model using only Jan-Jun data to predict Jul-Sep exits, answered 15 business questions in MySQL, built an ROI simulator in Excel, and delivered a four-page Power BI dashboard. The headline: about 70% of the money at risk sits with 20% of customers, so a small, targeted budget protects most of the value."

## Likely questions
**Why synthetic data?** Real bank data is confidential. Generating it let me control the time windows (no leakage) and plant realistic data-quality problems to show cleaning skills. I say this openly in the README.

**What is data leakage and how did you avoid it?** Using information from the future to predict the past. Features come only from Jan-Jun; the label is Jul-Sep. I excluded exit_reason and churn_date because they only exist after a customer leaves.

**Why out-of-fold predictions?** So every customer is scored by a model that never saw them; otherwise probabilities look better than they are.

**Why Logistic Regression / Random Forest and how did you choose?** I compared both on ROC-AUC (both about 0.83). I checked calibration by decile because the Rupee-at-risk numbers need trustworthy probabilities, not just a good ranking.

**What does AUC 0.83 mean in business terms?** Flagging the riskiest 20% of customers catches about 64% of those who actually leave, against 20% by random selection.

**How did you define value at risk?** Revenue per customer (3% spread on balance, 3.5% on loans, card fees, per-product fees) x 3-year discount factor at 10% x churn probability. The assumptions are listed and editable.

**How did you decide who to contact?** Rank by net benefit per rupee (probability x save rate x value - cost) and fund top-down until the budget is used. It is a greedy approach, not a perfect optimisation.

**What if your save rates are wrong?** I stress-tested in Excel: I halved every save rate and checked whether the campaign still pays back. (State your own result.)

**Which SQL concepts did you use?** CTEs, window functions (LAG, RANK, ROW_NUMBER, NTILE, SUM OVER PARTITION), conditional aggregation, views, a stored procedure, and data-quality checks.

**Why both Excel and Power BI?** Excel for the what-if business case that finance teams trust; Power BI for interactive exploration by managers. I rebuilt the same logic in both to cross-check results.

**What would you do next?** Run an A/B test of retention offers to measure real save rates, add transaction-level data, and track model drift monthly.

**What was the hardest part?** (Be honest - e.g. making the probabilities calibrated, or getting the DAX TOPN what-if to match Excel.)

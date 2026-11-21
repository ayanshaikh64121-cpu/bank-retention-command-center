# Resume bullets (auto-filled from your own run)

**Project title:** Bank Retention Command Center - Churn Prediction, Revenue-at-Risk & Intervention ROI
**Tools:** Python (pandas, scikit-learn), MySQL, Excel, Power BI | **Data:** synthetic 10,000-customer retail-bank dataset

- Cleaned and merged 3 relational tables (10,000 customers, 60,000 monthly activity rows, 3,000 complaints) in Python; fixed duplicates, inconsistent labels, impossible values and missing data.
- - Built a Random Forest churn prediction model (out-of-fold ROC-AUC 0.83) using pre-churn customer and behavioural features, excluding post-churn information; identified the riskiest 20% of customers, capturing 64% of churners at 44% precision.
- Converted churn probability into Rs 6.56 crore of 3-year customer value at risk and a Value x Risk retention matrix; the top 20% of customers hold 70% of the exposure.
- Wrote MySQL queries using CTEs, window functions, views and aggregations to analyse customer churn patterns.
- Built an Excel retention ROI simulator using budget, cost-per-action and save-rate assumptions.
- Created a one-page Power BI dashboard with customer KPIs, churn analysis, risk segmentation and retention action insights.

\# Bank Retention Command Center



\*\*Who is likely to leave a bank, what are they worth, what should we offer them, and does the offer pay off?\*\*



An end-to-end Data Analytics and Business Analysis project using \*\*Python, MySQL, Excel, and Power BI\*\* to identify customers at risk of churn, estimate their financial value, and prioritize retention actions.



> \*\*Data note:\*\* This project uses synthetic data generated to resemble an Indian retail banking environment. It contains 10,000 customers, 60,000 monthly activity records, and 3,000 complaints. Retention costs and save rates in the ROI model are stated assumptions, not real banking results.



\## Why this project is different



| Typical churn project | This project |

|---|---|

| Predicts who may churn | Predicts churn and estimates Rupee value at risk |

| Focuses on one model metric | Evaluates model performance using ROC-AUC and risk concentration |

| Stops at prediction | Converts customer value and churn risk into recommended retention actions |

| No financial business case | Includes an Excel ROI simulator to evaluate retention budgets |

| Uses one tool | Combines Python, MySQL, Excel, and Power BI |



\## Key findings



\- \*\*10,000 customers\*\* analyzed after data cleaning.

\- \*\*13.8% churn rate\*\*, representing 1,380 customers.

\- Approximately \*\*₹6.56 crore\*\* in estimated three-year customer value at risk.

\- The top 20% of customers by value at risk account for approximately \*\*70% of total value at risk\*\*.

\- Random Forest model achieved approximately \*\*0.833 ROC-AUC\*\*.

\- The riskiest 20% of customers contain approximately \*\*64% of all churners\*\*.



These findings are based on the synthetic dataset and the project's modeling assumptions.



\## Project workflow



```text

Synthetic Data Generation

&#x20;         |

&#x20;         v

Python: Cleaning, Feature Engineering and Churn Modeling

&#x20;         |

&#x20;         v

MySQL: Data Storage, Quality Checks and Business Analysis

&#x20;         |

&#x20;         v

Excel: Retention ROI Simulator

&#x20;         |

&#x20;         v

Power BI: Interactive One-Page Dashboard

```



\## Repository structure



```text

bank-retention-project/

│

├── 1\_python/

│   ├── 01\_generate\_data.py

│   ├── 02\_clean\_and\_model.py

│   ├── 03\_load\_to\_mysql.py

│   ├── 04\_export\_views\_for\_powerbi.py

│   ├── requirements.txt

│   └── charts/

│

├── 2\_mysql/

│   ├── 01\_schema.sql

│   ├── 02\_load\_data.sql

│   ├── 03\_data\_quality\_checks.sql

│   ├── 04\_analysis\_queries.sql

│   └── 05\_views\_and\_procedure.sql

│

├── 3\_excel/

│   └── Retention\_ROI\_Simulator.xlsx

│

├── 4\_powerbi/

│   └── Banking\_Retention\_Dashboard.pbix

│

├── data/

│   ├── raw/

│   ├── clean/

│   └── powerbi\_csv/

│

├── README.md

├── STEP\_BY\_STEP\_GUIDE.md

└── .gitignore

```



\## Tools and technologies



\- \*\*Python:\*\* Pandas, NumPy, Scikit-learn, Matplotlib

\- \*\*SQL:\*\* MySQL, joins, CTEs, window functions, views, stored procedures

\- \*\*Excel:\*\* Formulas, budget allocation, ROI calculations, sensitivity analysis

\- \*\*Power BI:\*\* Data modeling, DAX measures, KPI cards, and business charts



\## How to run



For detailed setup instructions, refer to `STEP\_BY\_STEP\_GUIDE.md`.



The general execution order is:



1\. Install the Python dependencies from `1\_python/requirements.txt`.

2\. Generate the synthetic data using `01\_generate\_data.py`.

3\. Clean the data and build the churn model using `02\_clean\_and\_model.py`.

4\. Create the MySQL database and tables using `01\_schema.sql`.

5\. Load the cleaned data using `03\_load\_to\_mysql.py`.

6\. Run the data quality checks, analysis queries, and views scripts.

7\. Open `3\_excel/Retention\_ROI\_Simulator.xlsx` to explore the retention ROI model.

8\. Open `4\_powerbi/Banking\_Retention\_Dashboard.pbix` to explore the dashboard.

![Power BI Dashboard Preview](powerbi/dashboard_preview.png)



\*\*Note:\*\* `02\_load\_data.sql` is an alternative SQL-based loading method. The project data was loaded using the Python MySQL loader.



\## Project limitations



\- The dataset is synthetic. Real-world customer behavior may differ.

\- Retention costs and save rates are assumptions, not experimentally measured outcomes.

\- Revenue and customer value are estimates based on simplified assumptions, not actual bank financial statements.

\- The churn model identifies statistical patterns and does not establish causation.

\- A controlled A/B test would be needed to measure the actual effectiveness of retention offers.



\## Project objective



The objective is to demonstrate an end-to-end analytical workflow that moves beyond predicting customer churn and connects customer risk to financial value, actionable retention strategies, and business decision-making.


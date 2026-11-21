# \# Step-by-Step Guide: Bank Retention Command Center

# 

# This guide explains how to set up and run the Bank Retention Command Center project.

# 

# The project uses synthetic banking data. No real customer information is used.

# 

# \## 1. Project Requirements

# 

# Install the following software:

# 

# \- Python

# \- MySQL Server

# \- MySQL Workbench

# \- Microsoft Excel

# \- Microsoft Power BI Desktop

# 

# You also need a working internet connection to install the Python libraries.

# 

# \## 2. Python: Data Generation and Cleaning

# 

# \### Step 1: Install Python dependencies

# 

# Open a terminal in the project directory and execute:

# 

# ```bash

# cd 1\_python

# pip install -r requirements.txt

# ```

# 

# \### Step 2: Generate synthetic data

# 

# Run:

# 

# ```bash

# python 01\_generate\_data.py

# ```

# 

# This generates synthetic banking data, including customer information, monthly activity, and complaints.

# 

# The generated files are saved in the project's data directory.

# 

# \### Step 3: Clean and prepare the data

# 

# Run:

# 

# ```bash

# python 02\_clean\_and\_model.py

# ```

# 

# This script performs:

# 

# \- Duplicate removal and data cleaning

# \- Missing-value treatment

# \- Feature engineering

# \- Churn prediction using Logistic Regression and Random Forest

# \- Model evaluation

# \- Customer risk segmentation

# \- Customer value and revenue-at-risk estimation

# \- Generation of analytical charts

# 

# The cleaned datasets and model outputs are saved for downstream analysis.

# 

# \## 3. MySQL: Database Setup and Analysis

# 

# \### Step 1: Create the database and tables

# 

# Open MySQL Workbench and execute:

# 

# ```text

# 2\_mysql/01\_schema.sql

# ```

# 

# \*\*Warning:\*\* This script contains `DROP DATABASE IF EXISTS bank\_retention`. It deletes an existing database with that name before recreating it. Back up any existing data before running it.

# 

# \### Step 2: Load the cleaned data

# 

# The project uses a Python script to load the cleaned CSV files into MySQL.

# 

# Return to the terminal and execute:

# 

# ```bash

# python 03\_load\_to\_mysql.py

# ```

# 

# The script connects to MySQL and loads the cleaned datasets.

# 

# It requests the MySQL credentials when required. Alternatively, the connection settings can be supplied through environment variables:

# 

# \- MYSQL\_USER

# \- MYSQL\_PASSWORD

# \- MYSQL\_HOST

# \- MYSQL\_PORT

# 

# The target database is `bank\_retention`.

# 

# \*\*Alternative:\*\* `2\_mysql/02\_load\_data.sql` provides an SQL-based loading method. It requires updating the placeholder CSV file paths and configuring MySQL local file loading. It is not required when using the Python loader.

# 

# \### Step 3: Run data quality checks

# 

# In MySQL Workbench, execute:

# 

# ```text

# 2\_mysql/03\_data\_quality\_checks.sql

# ```

# 

# These queries check record counts, missing values, data ranges, relationships, and other data-quality conditions.

# 

# \### Step 4: Run business analysis queries

# 

# Execute:

# 

# ```text

# 2\_mysql/04\_analysis\_queries.sql

# ```

# 

# This file contains business-focused SQL analysis using joins, aggregations, CTEs, and window functions.

# 

# \### Step 5: Create views and stored procedure

# 

# Execute:

# 

# ```text

# 2\_mysql/05\_views\_and\_procedure.sql

# ```

# 

# This creates analytical views and a stored procedure for retrieving high-value customers at risk of churn.

# 

# Example:

# 

# ```sql

# CALL sp\_watchlist('Hyderabad', 10);

# ```

# 

# \## 4. Excel: Retention ROI Simulator

# 

# Open:

# 

# ```text

# 3\_excel/Retention\_ROI\_Simulator.xlsx

# ```

# 

# The workbook contains five sheets:

# 

# 1\. README

# 2\. Summary

# 3\. Assumptions

# 4\. Targeting

# 5\. Data\_All

# 

# Explore the budget assumptions, customer targeting, expected customers saved, estimated value saved, and return on investment.

# 

# The ROI results depend on the assumptions entered in the workbook. They should not be interpreted as guaranteed financial outcomes.

# 

# \## 5. Power BI: Retention Dashboard

# 

# Open:

# 

# ```text

# 4\_powerbi/Banking\_Retention\_Dashboard.pbix

# ```

# 

# The dashboard presents the project's customer retention analysis through KPI cards and business charts.

# 

# It includes metrics such as:

# 

# \- Total customers

# \- Churned customers

# \- Churn rate

# \- Total value at risk

# \- Expected customers saved

# \- Expected value saved

# 

# It also visualizes churn patterns across customer locations, value segments, and risk categories, along with recommended retention actions.

# 

# \## 6. Important Notes

# 

# \- The dataset is synthetic and intended for analytical demonstration.

# \- Python scripts should be executed in the intended order.

# \- The MySQL database must be created before loading data.

# \- The Python loader requires a running MySQL server and valid connection credentials.

# \- The SQL-based loader is optional when the Python loader is used.

# \- The Excel ROI simulator uses stated assumptions.

# \- The Power BI dashboard is provided as a completed PBIX file.

# 

# \## 7. Project Execution Order

# 

# ```text

# 1\. Install Python dependencies

# &#x20;         |

# &#x20;         v

# 2\. Generate synthetic data

# &#x20;         |

# &#x20;         v

# 3\. Clean data and build churn models

# &#x20;         |

# &#x20;         v

# 4\. Create MySQL database and tables

# &#x20;         |

# &#x20;         v

# 5\. Load cleaned data into MySQL

# &#x20;         |

# &#x20;         v

# 6\. Run data quality checks

# &#x20;         |

# &#x20;         v

# 7\. Execute business analysis queries

# &#x20;         |

# &#x20;         v

# 8\. Create SQL views and stored procedure

# &#x20;         |

# &#x20;         v

# 9\. Explore Excel ROI simulator

# &#x20;         |

# &#x20;         v

# 10\. Open Power BI dashboard

# ```

# 




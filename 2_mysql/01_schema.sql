-- =====================================================================
-- STEP 2A (MySQL) - Build the database
-- Run this whole file once in MySQL Workbench (lightning-bolt icon).
-- Analogy: the database is a building, each table is a room with labelled shelves.
-- =====================================================================
DROP DATABASE IF EXISTS bank_retention;
CREATE DATABASE bank_retention CHARACTER SET utf8mb4;
USE bank_retention;

-- 1) One row per customer (cleaned in Python)
CREATE TABLE customers (
    customer_id          VARCHAR(10)   NOT NULL,
    age                  TINYINT UNSIGNED NOT NULL,
    gender               VARCHAR(10)   NOT NULL,
    city                 VARCHAR(30)   NOT NULL,
    city_tier            VARCHAR(10)   NOT NULL,
    account_type         VARCHAR(10)   NOT NULL,
    join_date            DATE          NOT NULL,
    annual_income        DECIMAL(12,0) NOT NULL,
    credit_score         SMALLINT UNSIGNED NOT NULL,
    avg_monthly_balance  DECIMAL(12,0) NOT NULL,
    products_held        TINYINT UNSIGNED NOT NULL,
    has_credit_card      TINYINT(1)    NOT NULL,
    has_loan             TINYINT(1)    NOT NULL,
    loan_amount          DECIMAL(12,0) NOT NULL,
    uses_mobile_app      TINYINT(1)    NOT NULL,
    churned_next_90d     TINYINT(1)    NOT NULL,   -- 1 = closed account Jul-Sep 2026
    churn_date           DATE          NULL,
    exit_reason          VARCHAR(50)   NULL,
    PRIMARY KEY (customer_id),
    INDEX idx_city (city),
    INDEX idx_churn (churned_next_90d)
) ENGINE=InnoDB;

-- 2) Six months of activity per customer (Jan-Jun 2026)
CREATE TABLE monthly_activity (
    customer_id    VARCHAR(10)   NOT NULL,
    month          DATE          NOT NULL,
    txn_count      INT UNSIGNED  NOT NULL,
    txn_amount     DECIMAL(12,0) NOT NULL,
    upi_txn_count  INT UNSIGNED  NOT NULL,
    app_logins     INT UNSIGNED  NOT NULL,
    PRIMARY KEY (customer_id, month),
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
) ENGINE=InnoDB;

-- 3) Complaints raised by customers
CREATE TABLE complaints (
    complaint_id    VARCHAR(10) NOT NULL,
    customer_id     VARCHAR(10) NOT NULL,
    complaint_date  DATE        NOT NULL,
    category        VARCHAR(30) NOT NULL,
    is_resolved     TINYINT(1)  NOT NULL,
    days_to_resolve SMALLINT UNSIGNED NULL,
    PRIMARY KEY (complaint_id),
    INDEX idx_cust (customer_id),
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
) ENGINE=InnoDB;

-- 4) Model output from Python: churn probability + business value per customer
CREATE TABLE customer_scores (
    customer_id           VARCHAR(10)   NOT NULL,
    tenure_years          DECIMAL(4,1)  NOT NULL,
    txn_avg_first3        DECIMAL(10,2) NULL,
    txn_avg_last3         DECIMAL(10,2) NULL,
    avg_app_logins        DECIMAL(10,2) NULL,
    upi_share             DECIMAL(6,4)  NULL,
    txn_change_pct        DECIMAL(8,3)  NULL,
    complaints            SMALLINT UNSIGNED NOT NULL,
    unresolved_complaints SMALLINT UNSIGNED NOT NULL,
    churn_probability     DECIMAL(6,4)  NOT NULL,
    est_annual_revenue    DECIMAL(12,0) NOT NULL,
    value_3yr             DECIMAL(12,0) NOT NULL,
    revenue_at_risk       DECIMAL(12,0) NOT NULL,
    value_segment         VARCHAR(10)   NOT NULL,   -- Premium / Core / Emerging
    risk_band             VARCHAR(10)   NOT NULL,   -- High / Medium / Low
    recommended_action    VARCHAR(40)   NOT NULL,
    risk_decile           TINYINT UNSIGNED NOT NULL,
    PRIMARY KEY (customer_id),
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
) ENGINE=InnoDB;

SHOW TABLES;

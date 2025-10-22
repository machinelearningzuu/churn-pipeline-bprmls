# Analytics & Dashboards - Visualizing Your ML Insights

**Learn how to turn ML predictions into actionable business insights**

Welcome! 👋 This guide will teach you how to build beautiful, interactive dashboards that business teams actually want to use. We'll take raw ML predictions and transform them into charts, tables, and visualizations that drive decision-making.

---

## What You'll Learn

By the end of this guide, you'll be able to:
- Store ML predictions in a database (AWS RDS PostgreSQL)
- Create SQL views for analytics
- Connect AWS QuickSight to your database
- Build interactive dashboards
- Share insights with business stakeholders
- Understand why this matters for real ML projects

**Time to Complete**: 3-4 hours (including hands-on practice)

---

## Prerequisites

Before starting, make sure you have:
- [x] AWS account with admin access
- [x] Kafka streaming system running (from Guide 01)
- [x] Basic SQL knowledge (SELECT, WHERE, GROUP BY)
- [x] Understanding of what business intelligence means

---

## Table of Contents

1. [Why Do We Need Analytics?](#why-do-we-need-analytics)
2. [Understanding the Analytics Architecture](#understanding-the-analytics-architecture)
3. [Setting Up AWS RDS PostgreSQL](#setting-up-aws-rds-postgresql)
4. [Creating the Database Schema](#creating-the-database-schema)
5. [Building SQL Views for Business Intelligence](#building-sql-views-for-business-intelligence)
6. [Setting Up AWS QuickSight](#setting-up-aws-quicksight)
7. [Creating Your First Dataset](#creating-your-first-dataset)
8. [Building Visualizations](#building-visualizations)
9. [Creating the Complete Dashboard](#creating-the-complete-dashboard)
10. [Sharing with Stakeholders](#sharing-with-stakeholders)
11. [Troubleshooting](#troubleshooting)

---

## Why Do We Need Analytics?

Let's start with a story...

### The Problem

You've built an amazing ML model that predicts customer churn with 80% accuracy. It processes thousands of predictions per day through Kafka. Your CTO is impressed!

But then your VP of Marketing asks:

> "Great! So which customers should my team contact first?"

You realize: **The predictions are stored somewhere, but nobody can access them!**

The marketing team needs to:
- See which customers are high-risk
- Identify patterns (which regions have high churn?)
- Track trends (is churn increasing or decreasing?)
- Make data-driven decisions

**They can't write SQL queries.** They need dashboards!

### The Solution: Business Intelligence (BI)

```
ML Predictions → Database → SQL Views → Beautiful Dashboards → Business Decisions
```

**Business Intelligence** transforms raw data into actionable insights that anyone can understand.

---

## Understanding the Analytics Architecture

Here's how everything connects:

```
┌─────────────────────────────────────┐
│ Kafka Predictions Topic             │
│ (Real-time predictions)             │
└───────────────┬─────────────────────┘
                │
                ↓ Analytics Service consumes
┌─────────────────────────────────────┐
│ AWS RDS PostgreSQL                  │
│ ┌─────────────────────────────────┐ │
│ │ Table: churn_predictions        │ │
│ │ (Raw prediction records)        │ │
│ └────────────┬────────────────────┘ │
│              │                        │
│              ↓ SQL Views aggregate   │
│ ┌─────────────────────────────────┐ │
│ │ View: v_realtime_dashboard      │ │
│ │ View: v_geography_churn         │ │
│ │ View: v_top_risk_customers      │ │
│ └────────────┬────────────────────┘ │
└──────────────┼──────────────────────┘
               │
               ↓ QuickSight imports
┌──────────────────────────────────────┐
│ AWS QuickSight                       │
│ ┌──────────────────────────────────┐ │
│ │ Interactive Dashboards            │ │
│ │ • Churn Rate KPI                 │ │
│ │ • Geographic Analysis            │ │
│ │ • Risk Customer List             │ │
│ │ • Trend Charts                   │ │
│ └──────────────────────────────────┘ │
└──────────────┼───────────────────────┘
               │
               ↓ Business teams access
┌──────────────────────────────────────┐
│ Marketing, Sales, Executives         │
│ Make data-driven decisions           │
└──────────────────────────────────────┘
```

### The Three-Layer Architecture

#### Layer 1: Storage (PostgreSQL Table)

**Purpose**: Store every prediction

```sql
churn_predictions table:
- Every prediction is a row
- Includes customer details
- Timestamp of when prediction was made
```

**Example rows:**
```
customer_id | prediction | probability | geography | predicted_at
15634602   | 0          | 0.13        | France    | 2025-10-21 10:15:30
15634603   | 1          | 0.87        | Germany   | 2025-10-21 10:15:31
15634604   | 0          | 0.24        | Spain     | 2025-10-21 10:15:32
```

#### Layer 2: Aggregation (SQL Views)

**Purpose**: Pre-calculate analytics

```sql
v_realtime_dashboard view:
- Hourly churn rate
- Total predictions count
- Average risk scores
- Already calculated, fast to query!
```

**Example results:**
```
hour              | total_predictions | churn_rate
2025-10-21 10:00 | 1500             | 23.5%
2025-10-21 11:00 | 1620             | 24.2%
2025-10-21 12:00 | 1580             | 22.8%
```

#### Layer 3: Visualization (QuickSight)

**Purpose**: Make it beautiful and interactive

- Line charts showing trends
- KPIs showing current metrics
- Tables listing high-risk customers
- Filters to drill down into data

---

## Setting Up AWS RDS PostgreSQL

AWS RDS (Relational Database Service) is a managed database that AWS maintains for you.

### Why RDS Instead of Local PostgreSQL?

| Local PostgreSQL | AWS RDS |
|------------------|---------|
| You manage backups | AWS handles backups |
| You manage upgrades | AWS handles upgrades |
| You monitor disk space | AWS auto-scales storage |
| Single point of failure | High availability option |
| Need VPN for remote access | Built-in security |

**For production**: Always use RDS (or similar managed service)

### Creating Your RDS Instance

**Step 1**: Go to AWS Console

1. Log into AWS Console
2. Search for "RDS" in the search bar
3. Click on "RDS"

**Step 2**: Create Database

1. Click **"Create database"** button

2. **Choose Database Creation Method:**
   - Select: **Standard create** (more control)

3. **Engine Options:**
   - Engine type: **PostgreSQL**
   - Version: **PostgreSQL 14.x** or newer (recommended)

4. **Templates:**
   - For learning: **Free tier** (limited to db.t3.micro)
   - For production: **Production** (better performance)

5. **Settings:**
   ```
   DB instance identifier: churn-pipeline-db
   Master username: zuucrew
   Master password: [Create a strong password!]
   Confirm password: [Same password]
   ```

   **💡 Tip**: Save this password! You'll need it later.

6. **DB Instance Class:**
   - For learning: `db.t3.micro` (free tier eligible)
   - For production: `db.t3.medium` or larger

7. **Storage:**
   - Storage type: **General Purpose SSD (gp3)**
   - Allocated storage: **20 GB** (enough for millions of predictions)
   - Storage autoscaling: **Enable** (grows automatically if needed)
   - Maximum storage threshold: **100 GB**

8. **Connectivity:**
   - Virtual Private Cloud (VPC): **Default VPC**
   - Public access: **Yes** (so QuickSight can access)
   - VPC security group: **Create new**
   - New VPC security group name: `churn-pipeline-db-sg`
   - Availability Zone: **No preference**

9. **Database Authentication:**
   - Database authentication options: **Password authentication**

10. **Additional Configuration:**
    - Initial database name: **analytics**
    - DB parameter group: **default.postgres14**
    - Backup retention period: **7 days**
    - Enable encryption: **Yes** (good security practice)

11. **Click "Create database"**

**Wait 5-10 minutes...** AWS is provisioning your database!

### Configuring Security Group

Your database is now created but locked down. Let's allow access.

**Step 1**: Find Your Security Group

1. Go to RDS → Databases → Click on `churn-pipeline-db`
2. Under "Connectivity & security" section
3. Click on the security group link (looks like `sg-xxxxxxxxx`)

**Step 2**: Add Inbound Rules

1. Click **"Edit inbound rules"**
2. Click **"Add rule"**

**Rule 1: Your Computer**
```
Type: PostgreSQL
Protocol: TCP
Port: 5432
Source: My IP
Description: My laptop access
```

**Rule 2: QuickSight (Important!)**

QuickSight needs special IPs to access your database. These vary by region:

**For us-east-1 (N. Virginia):**
```
52.210.255.224/27
54.246.232.224/27
```

**For ap-south-1 (Mumbai):**
```
52.66.193.64/27
52.66.193.96/27
```

Add each as a separate rule:
```
Type: PostgreSQL
Protocol: TCP
Port: 5432
Source: Custom → 52.66.193.64/27
Description: QuickSight access 1
```

3. Click **"Save rules"**

### Getting Your Database Endpoint

1. Go to RDS → Databases → `churn-pipeline-db`
2. Under "Connectivity & security"
3. Copy **Endpoint** (looks like: `churn-pipeline-db.xxxxxx.ap-south-1.rds.amazonaws.com`)

**Save this!** You'll use it everywhere.

### Testing the Connection

```bash
# Install psql if you don't have it
# Mac: brew install postgresql
# Ubuntu: sudo apt-get install postgresql-client

# Test connection
psql -h churn-pipeline-db.xxxxxx.ap-south-1.rds.amazonaws.com \
     -U zuucrew \
     -d analytics

# Enter your password when prompted

# Should see:
analytics=>

# Try a query
SELECT version();

# Exit
\q
```

If this works, your RDS is ready! ✅

### Setting Up Environment Variables

Create/update your `.env` file:

```bash
# AWS RDS Configuration
RDS_HOST=churn-pipeline-db.xxxxxx.ap-south-1.rds.amazonaws.com
RDS_PORT=5432
RDS_DB_NAME=analytics
RDS_USERNAME=zuucrew
RDS_PASSWORD=your_secure_password
```

**Important**: Never commit `.env` to Git! It should be in `.gitignore`.

---

## Creating the Database Schema

Now let's create the table where predictions will be stored.

### Understanding the Schema

Think of a database table like an Excel spreadsheet:
- **Columns** = Fields (customer_id, prediction, probability)
- **Rows** = Records (one prediction per row)
- **Indexes** = Quick lookup (like a book index)

### The Main Table: churn_predictions

**Purpose**: Store every single prediction

```sql
CREATE TABLE IF NOT EXISTS churn_predictions (
    -- Primary key (auto-incrementing ID)
    id SERIAL PRIMARY KEY,
    
    -- Prediction information
    customer_id VARCHAR(50) NOT NULL,
    prediction INTEGER NOT NULL,     -- 0 = won't churn, 1 = will churn
    probability FLOAT NOT NULL,      -- 0.0 to 1.0 (churn probability)
    risk_score FLOAT NOT NULL,       -- Same as probability
    predicted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(50),       -- Which model made this prediction
    
    -- Customer attributes (for segmentation)
    geography VARCHAR(50),
    gender VARCHAR(10),
    age INTEGER,
    tenure INTEGER,
    balance FLOAT,
    num_of_products INTEGER,
    has_cr_card INTEGER,
    is_active_member INTEGER,
    estimated_salary FLOAT,
    
    -- Metadata
    event_id VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Let's break this down:**

**id**: Auto-generated number (1, 2, 3, ...)
- Primary key (uniquely identifies each row)
- SERIAL = automatically increments

**customer_id**: The customer this prediction is for
- VARCHAR(50) = text up to 50 characters
- NOT NULL = must have a value

**prediction**: The actual prediction (0 or 1)
- 0 = Customer will stay
- 1 = Customer will churn

**probability**: How confident the model is (0.0 to 1.0)
- 0.13 = 13% chance of churn (low risk)
- 0.87 = 87% chance of churn (high risk!)

**predicted_at**: When this prediction was made
- TIMESTAMP = date and time
- DEFAULT CURRENT_TIMESTAMP = uses current time if not specified

### Creating Indexes for Speed

**Indexes make queries faster** (like a book index - instead of reading every page, you jump to the right one)

**We create 5 indexes to speed up common queries:**

1. **By timestamp** (`idx_predictions_timestamp`) - Fast date-range queries (e.g., "show predictions from last 7 days")
2. **By customer ID** (`idx_predictions_customer`) - Fast customer lookup (e.g., "find all predictions for customer 15634602")
3. **By risk score** (`idx_predictions_risk`) - Fast high-risk queries (e.g., "show all customers with risk > 0.7")
4. **By geography** (`idx_predictions_geography`) - Fast regional queries (e.g., "show all predictions from France")
5. **By date only** (`idx_predictions_date`) - Fast daily analysis (e.g., "show predictions grouped by day")

**The performance difference:**
- **Without index**: PostgreSQL scans ALL rows (5 seconds with 1 million rows)
- **With index**: PostgreSQL jumps directly to the right rows (0.01 seconds with 1 million rows)

That's a **500x speedup!** This is crucial when business teams are waiting for dashboards to load.

### Running the Schema Script

**Option 1: Using psql (Command Line)**

```bash
# Connect to database
psql -h $RDS_HOST -U $RDS_USERNAME -d $RDS_DB_NAME

# Run the SQL
\i sql/create_analytics_tables.sql

# Or paste the SQL directly
CREATE TABLE IF NOT EXISTS churn_predictions (
    ...
);

# Verify table exists
\dt

# Check table structure
\d churn_predictions

# Exit
\q
```

**Option 2: Using a SQL File**

Create `sql/create_analytics_tables.sql` with the schema above, then:

```bash
PGPASSWORD=$RDS_PASSWORD psql \
  -h $RDS_HOST \
  -U $RDS_USERNAME \
  -d $RDS_DB_NAME \
  -f sql/create_analytics_tables.sql
```

### Verifying the Setup

```sql
-- Check if table exists
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Should show: churn_predictions

-- Check table structure
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'churn_predictions';

-- Insert a test record
INSERT INTO churn_predictions (
    customer_id, prediction, probability, risk_score,
    geography, age, balance
) VALUES (
    'TEST123', 1, 0.85, 0.85,
    'France', 42, 50000.0
);

-- Query it back
SELECT * FROM churn_predictions WHERE customer_id = 'TEST123';

-- Delete test record
DELETE FROM churn_predictions WHERE customer_id = 'TEST123';
```

If all this works, your database is ready! ✅

---

## Building SQL Views for Business Intelligence

Raw predictions are great, but business teams need aggregated insights. That's where **SQL Views** come in!

### What is a SQL View?

Think of a view as a **saved query** that acts like a virtual table:

```sql
-- Regular query (you run it every time)
SELECT geography, COUNT(*) as total
FROM churn_predictions
GROUP BY geography;

-- View (saved query, run it anytime)
CREATE VIEW v_geography_stats AS
SELECT geography, COUNT(*) as total
FROM churn_predictions
GROUP BY geography;

-- Use the view
SELECT * FROM v_geography_stats;
```

**Benefits:**
- ✅ Write complex query once
- ✅ Reuse it easily
- ✅ Hide complexity from users
- ✅ Always shows fresh data (not a cache!)

### View 1: Real-Time Dashboard (Last 24 Hours)

**Business Question**: "How is our system performing right now?"

**What this view does:**

This view aggregates predictions by hour for the last 24 hours, calculating:

1. **Hour** - Rounds timestamps to the hour (10:37:25 becomes 10:00:00) so all predictions in that hour are grouped together
2. **Total Predictions** - Counts how many predictions were made in each hour
3. **Churn Count** - Counts how many customers were predicted to churn (where prediction = 1)
4. **Churn Rate %** - Calculates percentage (churn_count ÷ total_predictions × 100)
5. **Average Risk Score** - Average probability across all predictions in that hour
6. **High Risk Count** - Count of customers with risk score ≥ 0.7
7. **Latest Prediction Time** - Most recent prediction timestamp

**Key SQL concepts used:**
- `DATE_TRUNC('hour', timestamp)` - Groups data by hour
- `COUNT(*)` - Counts total rows
- `SUM(prediction)` - Since prediction is 0 or 1, sum gives us the count of 1s (churns)
- `WHERE predicted_at >= NOW() - INTERVAL '24 hours'` - Filters to last 24 hours only

**Example output:**

| Hour | Total Predictions | Churn Count | Churn Rate | Avg Risk | High Risk Count |
|------|-------------------|-------------|------------|----------|-----------------|
| 12:00 PM | 1580 | 360 | 22.78% | 0.234 | 45 |
| 11:00 AM | 1620 | 392 | 24.20% | 0.256 | 52 |
| 10:00 AM | 1500 | 352 | 23.47% | 0.241 | 38 |

**Business insight**: "Our churn rate spiked at 11 AM! Let's investigate."

### View 2: Geography Analysis (Last 30 Days)

**Business Question**: "Which regions have the highest churn?"

**What this view does:**

This view groups predictions by geography (France, Germany, Spain) for the last 30 days, calculating:

1. **Geography** - The country/region
2. **Total Customers** - How many predictions for this region
3. **Churn Count** - How many predicted to churn
4. **Churn Rate %** - Percentage of customers predicted to churn in this region
5. **Average Risk Score** - Average churn probability for this region
6. **Average Age** - Demographic profile
7. **Average Balance** - Financial profile
8. **Average Tenure** - How long customers stay

Results are ordered by churn rate (highest first) so you immediately see problem regions.

**Example output:**

| Geography | Total Customers | Churn Count | Churn Rate | Avg Risk | Avg Age | Avg Balance |
|-----------|----------------|-------------|------------|----------|---------|-------------|
| Germany   | 45,000 | 12,500 | 27.78% | 0.289 | 41.2 | $76,543 |
| France    | 50,000 | 11,500 | 23.00% | 0.247 | 39.5 | $62,346 |
| Spain     | 35,000 | 7,000 | 20.00% | 0.218 | 38.1 | $54,322 |

**Business insight**: "Germany has highest churn! We need to improve service there."

### View 3: Top High-Risk Customers (Last 7 Days)

**Business Question**: "Which customers should we contact immediately?"

**What this view does:**

This view identifies the top 100 highest-risk customers from the last 7 days:

1. **Groups by customer ID** - If a customer has multiple predictions in 7 days, we take the highest risk score
2. **Filters to high-risk only** - Only includes customers with risk ≥ 0.7 (70% chance of churning)
3. **Gets their details** - Customer ID, max risk score, last prediction time, geography, age, balance, tenure, etc.
4. **Sorts by risk** - Highest risk first (so you see the most urgent cases)
5. **Limits to top 100** - Marketing teams can't call thousands of people - focus on the most at-risk

**Why group by customer?**

A customer might appear in our data multiple times over 7 days. For example:
- Monday: Customer 15634602 has risk score 0.75
- Thursday: Same customer now has risk score 0.82
- Sunday: Same customer now has risk score 0.87

We want to show each customer ONCE with their HIGHEST risk score (0.87 in this example).

**Example output:**

| Customer ID | Max Risk | Last Prediction | Geography | Age | Balance | Tenure |
|-------------|----------|-----------------|-----------|-----|---------|--------|
| 15634602 | 0.87 (87%) | 2025-10-21 12:30 | Germany | 42 | $0 | 2 |
| 15634603 | 0.85 (85%) | 2025-10-21 11:15 | France | 38 | $125,000 | 1 |
| 15634604 | 0.83 (83%) | 2025-10-21 10:45 | Spain | 45 | $0 | 3 |

**Business action**: "Marketing team, call these 100 customers TODAY!"

### Creating All Views

```bash
# Connect to database
psql -h $RDS_HOST -U $RDS_USERNAME -d $RDS_DB_NAME

# Create views (paste the SQL above)
# Or use a SQL file
\i sql/create_analytics_views.sql

# Verify views exist
\dv

# Should show:
# v_realtime_dashboard
# v_geography_churn
# v_top_risk_customers

# Test each view
SELECT * FROM v_realtime_dashboard LIMIT 5;
SELECT * FROM v_geography_churn;
SELECT * FROM v_top_risk_customers LIMIT 10;
```

---

## Setting Up AWS QuickSight

AWS QuickSight is Amazon's Business Intelligence (BI) tool. Think of it as "Tableau, but cheaper and integrated with AWS."

### Step 1: Sign Up for QuickSight

1. **Go to AWS Console** → Search for "QuickSight"
2. **Click "Sign up for QuickSight"**
3. **Choose Edition:**
   - **Standard**: $9/user/month (good for learning)
   - **Enterprise**: $18/user/month (more features)
   
   Choose **Standard** for this course

4. **QuickSight Account Setup:**
   ```
   QuickSight account name: churn-analytics
   Notification email: your.email@example.com
   ```

5. **Choose Region**: Same as your RDS (e.g., ap-south-1)

6. **Click "Finish"**

**Wait 2-3 minutes...** AWS is setting up your QuickSight account.

### Step 2: Grant QuickSight Access to RDS

QuickSight needs permission to access your RDS database.

1. **In QuickSight, click the user icon (top right)**
2. **Click "Manage QuickSight"**
3. **Click "Security & permissions"**
4. **Under "QuickSight access to AWS services", click "Add or remove"**
5. **Check these boxes:**
   - ✅ Amazon RDS
   - ✅ Amazon S3 (in case you need it later)
6. **For RDS, select your instance**: `churn-pipeline-db`
7. **Click "Update"**

### Step 3: Verify Network Access

Remember those QuickSight IPs we added to the RDS security group earlier? Let's verify:

1. **Go to RDS** → Databases → `churn-pipeline-db`
2. **Click on the security group**
3. **Check inbound rules** include QuickSight IPs:
   - For ap-south-1: `52.66.193.64/27` and `52.66.193.96/27`
   - For us-east-1: Different IPs (check AWS docs)

If not there, add them now!

---

## Creating Your First Dataset

A **dataset** in QuickSight is a connection to your data source (our RDS views).

### Step 1: Create New Dataset

1. **In QuickSight, click "Datasets" (left sidebar)**
2. **Click "New dataset"**
3. **Choose "PostgreSQL"**

### Step 2: Configure Data Source

Fill in the connection details:

```
Data source name: RDS Analytics
Database server: churn-pipeline-db.xxxxxx.ap-south-1.rds.amazonaws.com
Port: 5432
Database name: analytics
Username: zuucrew
Password: [your RDS password]
```

**Click "Validate connection"**

✅ Should show: "Connection validated successfully"

❌ If fails: Check security group IPs, RDS endpoint, password

**Click "Create data source"**

### Step 3: Choose Table/View

You'll see a list of tables and views:
```
Tables:
  churn_predictions

Views:
  v_realtime_dashboard
  v_geography_churn
  v_top_risk_customers
```

**For your first dataset:**
1. **Select**: `v_realtime_dashboard`
2. **Click "Select"**

### Step 4: Import Method

QuickSight offers two options:

**Option 1: SPICE (Recommended)**
- **SPICE** = Super-fast, Parallel, In-memory Calculation Engine
- Imports data into QuickSight's memory
- ✅ Blazing fast (queries in milliseconds)
- ✅ No load on your database
- ❌ Need to refresh to get new data
- Free tier: 10 GB

**Option 2: Direct Query**
- Queries database directly each time
- ✅ Always fresh data
- ❌ Slower (waits for database)
- ❌ Puts load on database

**Choose**: Import to SPICE (click "Import to SPICE")

### Step 5: Edit Dataset (Optional)

**Click "Edit/Preview data"** to customize:

1. **Rename fields** (make them business-friendly):
   ```
   hour → Hour
   total_predictions → Total Predictions
   churn_rate → Churn Rate (%)
   ```

2. **Change data types** if needed:
   - `hour` → Date/Time
   - `churn_rate` → Decimal (2 decimals)
   - `avg_risk_score` → Decimal (3 decimals)

3. **Add calculated fields** (we'll do this later)

**Click "Save & publish"**

Give it a name: `Realtime Dashboard Data`

**Click "Publish"**

Your first dataset is ready! 🎉

### Creating More Datasets

Repeat the process for other views:

**Dataset 2: Geography Analysis**
- Source: `v_geography_churn`
- Name: `Geography Analysis Data`
- Import to SPICE

**Dataset 3: High-Risk Customers**
- Source: `v_top_risk_customers`
- Name: `High Risk Customers Data`
- Import to SPICE

---

## Building Visualizations

Now the fun part - creating charts and graphs!

### Understanding SPICE Refresh

**Important**: SPICE data is a snapshot. To get fresh data:

1. **Manual refresh**: Datasets → (your dataset) → Refresh now
2. **Schedule refresh**: Datasets → (your dataset) → Schedule refresh
   - Example: Refresh every hour

For this tutorial, manually refresh when needed.

### Visualization 1: Churn Rate KPI

**What is a KPI?** Key Performance Indicator - a big number that shows important metrics.

**Steps:**

1. **Click "Analyses" (left sidebar)**
2. **Click "New analysis"**
3. **Choose dataset**: `Realtime Dashboard Data`
4. **Click "Create analysis"**

5. **Add KPI visual:**
   - Click "+ Add" → "Add visual"
   - Click "Visual types" → Choose "KPI"

6. **Configure KPI:**
   - Drag `churn_rate` to **Value**
   - Drag `hour` to **Trend group**
   - The KPI shows the latest churn rate with a trend arrow

7. **Format the KPI:**
   - Click the visual → Click "..." menu → "Format visual"
   - **Number format**: 
     - Type: Percentage
     - Decimal places: 2
   - **Comparison**:
     - Progress bar: ON
     - Target value: 20 (target churn rate)

8. **Add conditional formatting:**
   - Click "Format visual" → "Data colors"
   - Rules:
     - If `churn_rate < 15`: Green
     - If `churn_rate >= 15 AND < 20`: Yellow
     - If `churn_rate >= 20`: Red

9. **Title**: Click title → Type "Current Churn Rate"

Your first visual is done! 📊

### Visualization 2: Hourly Prediction Volume (Line Chart)

**Purpose**: Show how many predictions are being made over time

**Steps:**

1. **Add new visual**: "+ Add" → "Add visual"
2. **Choose "Line chart"**

3. **Configure:**
   - X-axis: `hour`
   - Value: `total_predictions`

4. **Format:**
   - Click "Format visual"
   - Data labels: ON
   - Grid lines: ON
   - Legend: Bottom

5. **Title**: "Hourly Prediction Volume (Last 24 Hours)"

### Visualization 3: Geographic Distribution (Pie Chart)

**Purpose**: Show customer distribution across regions

**Steps:**

1. **Click "+ Add" → "Add visual"**
2. **⚠️ Switch dataset**: Click dataset name (top) → Choose "Geography Analysis Data"
3. **Choose "Pie chart"**

4. **Configure:**
   - Group/Color: `geography`
   - Value: `total_customers`

5. **Format:**
   - Data labels: ON
   - Show percentage: ON
   - Legend: Right side

6. **Title**: "Customer Distribution by Geography"

### Visualization 4: Churn Rate by Geography (Bar Chart)

**Purpose**: Compare churn rates across regions

**Steps:**

1. **Add new visual** (using Geography Analysis Data dataset)
2. **Choose "Horizontal bar chart"**

3. **Configure:**
   - Y-axis: `geography`
   - Value: `churn_rate`

4. **Sort:**
   - Click visual → "..." menu → "Sort"
   - Sort by: `churn_rate` Descending

5. **Conditional formatting:**
   - Format visual → Data colors
   - Rules:
     - If `churn_rate < 18`: Green
     - If `churn_rate >= 18 AND < 22`: Yellow
     - If `churn_rate >= 22`: Red

6. **Title**: "Churn Rate by Region"

### Visualization 5: High-Risk Customers Table

**Purpose**: List customers who need immediate attention

**Steps:**

1. **Add new visual** → Switch to "High Risk Customers Data" dataset
2. **Choose "Table"**

3. **Add fields** (drag to "Group by"):
   - `customer_id`
   - `max_risk_score`
   - `geography`
   - `age`
   - `balance`
   - `tenure`

4. **Sort**: Click `max_risk_score` header → Descending

5. **Format `max_risk_score`:**
   - Click field → Format
   - Show as percentage
   - Conditional formatting:
     - ≥ 0.9: Dark red background
     - ≥ 0.8: Orange background
     - ≥ 0.7: Yellow background

6. **Limit rows**: Visual menu "..." → Limit rows → 20

7. **Title**: "Top 20 High-Risk Customers"

---

## Creating the Complete Dashboard

Now let's arrange all visuals into a beautiful dashboard!

### Step 1: Save Your Analysis

1. **Click "Save" (top right)**
2. **Name**: "Churn Prediction Analytics"
3. **Click "Save"**

### Step 2: Arrange the Layout

Drag and resize visuals to create this layout:

```
┌─────────────────────────────────────────────────────┐
│ 📊 CHURN PREDICTION ANALYTICS DASHBOARD             │
├─────────────┬──────────────┬────────────────────────┤
│ Churn KPI   │ Total Preds  │ High Risk Count        │
│  23.5% ↑    │   12,450     │     1,234              │
├─────────────┴──────────────┴────────────────────────┤
│ Hourly Prediction Volume (Line Chart)               │
│ ────────────────────────────────────                 │
├─────────────────────────┬───────────────────────────┤
│ Customer Distribution   │ Churn Rate by Geography   │
│ (Pie Chart)             │ (Bar Chart)               │
│                         │                           │
├─────────────────────────┴───────────────────────────┤
│ Top 20 High-Risk Customers (Table)                  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Tips:**
- Drag visuals by clicking the title bar
- Resize by dragging corners
- Use gridlines (View → Show grid) to align perfectly

### Step 3: Add Filters

Make your dashboard interactive!

1. **Click "+ Add" → "Filter"**

**Filter 1: Date Range**
- Field: `hour` (from Realtime Dashboard Data)
- Control type: Date range picker
- Default: Last 7 days
- Position: Top of dashboard

**Filter 2: Geography**
- Field: `geography` (from Geography Analysis Data)
- Control type: Dropdown
- Default: All
- Position: Top right

**Filter 3: Risk Level**
- Add a calculated field first:
  ```
  ifelse(
    {max_risk_score} >= 0.9, 'Extreme Risk',
    ifelse(
      {max_risk_score} >= 0.8, 'High Risk',
      ifelse({max_risk_score} >= 0.7, 'Moderate Risk', 'Low Risk')
    )
  )
  ```
  Name: `risk_level`
- Field: `risk_level`
- Control type: Multi-select
- Default: All

### Step 4: Add Dashboard Title

1. **Click "+ Add" → "Text box"**
2. **Type**: "🎯 Customer Churn Analytics - Real-Time Dashboard"
3. **Format**: Font size 24, Bold, Center aligned
4. **Position**: Very top of dashboard

### Step 5: Add Description

Add another text box below the title:
```
Last updated: {Now()}
Data source: AWS RDS PostgreSQL
Update frequency: Hourly
Contact: analytics-team@yourcompany.com
```

### Step 6: Publish Dashboard

1. **Click "Share" (top right)**
2. **Click "Publish dashboard"**
3. **Dashboard name**: "Churn Prediction Analytics"
4. **Click "Publish dashboard"**

Congratulations! Your dashboard is live! 🎉

---

## Sharing with Stakeholders

### Step 1: Add Users

1. **Click user icon (top right) → "Manage QuickSight"**
2. **Click "Manage users"**
3. **Click "Invite users"**
4. **Enter email addresses** (one per line):
   ```
   marketing-vp@yourcompany.com
   sales-director@yourcompany.com
   ceo@yourcompany.com
   ```
5. **Choose role**:
   - **Reader**: Can view dashboards (most users)
   - **Author**: Can create dashboards (data team)
   - **Admin**: Can manage users (you)

6. **Click "Invite"**

They'll receive an email with login link!

### Step 2: Share Dashboard

1. **Go to Dashboards** → Your dashboard
2. **Click "Share" (top right)**
3. **Click "Share dashboard"**
4. **Choose users** from dropdown
5. **Set permissions**:
   - ✅ View dashboard
   - ⚠️ Save as (allows them to create copies)
6. **Click "Share"**

### Step 3: Schedule Email Reports

Send dashboard screenshots automatically:

1. **Dashboard → "..." menu → "Schedule email report"**
2. **Configure:**
   - Frequency: Daily at 9 AM
   - Recipients: marketing-vp@yourcompany.com, sales-director@yourcompany.com
   - Subject: "Daily Churn Analytics Report"
   - Include: Snapshot of dashboard

3. **Click "Schedule"**

Now they get daily reports in their inbox! 📧

---

## Troubleshooting

### Issue 1: QuickSight Can't Connect to RDS

**Symptom:**
```
Connection failed: Connection timed out
```

**Solutions:**

1. **Check RDS security group:**
   ```bash
   # Verify QuickSight IPs are added
   aws ec2 describe-security-groups --group-ids sg-xxxxxxxx
   ```

2. **Verify RDS is publicly accessible:**
   - RDS → Your instance → Connectivity
   - "Public accessibility" should be "Yes"

3. **Check RDS endpoint is correct:**
   - RDS → Your instance → Copy endpoint
   - Make sure no typos in QuickSight connection

4. **Test connection manually:**
   ```bash
   psql -h $RDS_HOST -U $RDS_USERNAME -d $RDS_DB_NAME
   ```
   If this works but QuickSight doesn't, it's a security group issue.

### Issue 2: No Data in Dashboard

**Symptom:** Dashboard shows "No data available"

**Solutions:**

1. **Check if predictions are being written:**
   ```sql
   -- Connect to RDS
   SELECT COUNT(*) FROM churn_predictions;
   -- Should show > 0
   ```

2. **Check if views return data:**
   ```sql
   SELECT * FROM v_realtime_dashboard LIMIT 5;
   SELECT * FROM v_geography_churn;
   ```

3. **Refresh SPICE dataset:**
   - QuickSight → Datasets → Your dataset → Refresh now

4. **Check date filters:**
   - Views filter by date (last 24 hours, last 7 days)
   - Make sure you have recent data

### Issue 3: SPICE Refresh Fails

**Symptom:**
```
SPICE refresh failed: Insufficient permissions
```

**Solutions:**

1. **Grant QuickSight RDS access:**
   - QuickSight → Manage QuickSight → Security & permissions
   - Add Amazon RDS permissions

2. **Check RDS password hasn't changed:**
   - Datasets → Your dataset → Edit data source → Update password

3. **Check SPICE capacity:**
   - Manage QuickSight → SPICE capacity
   - Free tier: 10 GB (usually enough)
   - If full, delete unused datasets

### Issue 4: Visuals Not Showing

**Symptom:** Empty boxes where charts should be

**Solutions:**

1. **Check field mappings:**
   - Click visual → Make sure fields are in correct sections
   - Example: Line chart needs X-axis AND Value

2. **Check filters:**
   - Filters might be hiding all data
   - Remove filters temporarily

3. **Check data types:**
   - Dates should be Date type, not String
   - Numbers should be Number type, not String
   - Edit dataset → Change data types

### Issue 5: Slow Dashboard Performance

**Symptoms:** Dashboard takes > 10 seconds to load

**Solutions:**

1. **Use SPICE instead of Direct Query:**
   - Datasets → Edit → Import to SPICE

2. **Reduce data volume in views:**
   ```sql
   -- Instead of all data
   WHERE predicted_at >= NOW() - INTERVAL '7 days'
   
   -- Use shorter time window
   WHERE predicted_at >= NOW() - INTERVAL '24 hours'
   ```

3. **Add aggregations in SQL views:**
   - Pre-calculate in views instead of in QuickSight
   - Views are faster than QuickSight calculations

4. **Limit rows in tables:**
   - Visual menu → Limit rows → 100

---

## Key Takeaways

Congratulations! You now understand:

✅ **Why analytics matter**: Transform predictions into business value  
✅ **AWS RDS**: Managed PostgreSQL database in the cloud  
✅ **Database schema**: Tables for storage, indexes for speed  
✅ **SQL views**: Pre-calculated aggregations for fast queries  
✅ **AWS QuickSight**: Business intelligence and dashboards  
✅ **SPICE**: Fast in-memory analytics engine  
✅ **Visualizations**: KPIs, charts, tables for insights  
✅ **Sharing**: Collaborative dashboards for business teams  

### Real-World Skills

You can now:
- Design database schemas for ML systems
- Write complex SQL queries with aggregations
- Create interactive business dashboards
- Share data insights with non-technical stakeholders
- Troubleshoot data pipeline issues
- Understand the full ML deployment stack

### The Complete Picture

You've now learned the entire production ML system:

```
Data → Kafka → ML Model → Predictions → Database → Dashboard → Business Decisions
  ↑       ↑        ↑           ↑            ↑          ↑            ↑
Guide 1  Guide 1  Guide 2   Guide 1      Guide 3    Guide 3      Guide 3
```

### Next Steps

1. **Practice**: Create more visualizations, experiment with filters
2. **Customize**: Add your own metrics and KPIs
3. **Automate**: Set up scheduled refreshes and email reports
4. **Present**: Show your dashboard to peers, get feedback
5. **Expand**: Add more data sources (customer feedback, sales data)

---

## Additional Resources

### AWS Documentation
- [AWS RDS PostgreSQL Guide](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
- [AWS QuickSight User Guide](https://docs.aws.amazon.com/quicksight/latest/user/welcome.html)
- [QuickSight Visual Types](https://docs.aws.amazon.com/quicksight/latest/user/working-with-visuals.html)

### SQL Learning
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com/)
- [SQL Window Functions](https://mode.com/sql-tutorial/sql-window-functions/)
- [SQL Optimization Tips](https://www.postgresql.org/docs/current/performance-tips.html)

### BI Best Practices
- Search: "Dashboard design best practices"
- Search: "Data visualization principles"
- Book: "Storytelling with Data" by Cole Nussbaumer Knaflic

---

**Last Updated**: October 21, 2025  
**Maintained by**: Production ML Systems Course Team  
**Questions?** Check the troubleshooting section or ask your instructor!

Happy Analyzing! 📊


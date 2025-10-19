# 📊 AWS QuickSight Dashboard Implementation Guide

Complete guide to building real-time churn prediction dashboards with AWS QuickSight.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [QuickSight Setup](#quicksight-setup)
4. [Connect to RDS](#connect-to-rds)
5. [Create Datasets](#create-datasets)
6. [Build Visualizations](#build-visualizations)
7. [Create Dashboard](#create-dashboard)
8. [Schedule Refresh](#schedule-refresh)
9. [Share Dashboard](#share-dashboard)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

AWS QuickSight is a serverless Business Intelligence (BI) service that lets you create interactive dashboards from your data.

### What We'll Build

**Churn Analytics Dashboard** with:
- 📊 Real-time churn rate metrics
- 🌍 Geographic analysis
- 🚨 High-risk customer alerts
- 📈 Trend analysis over time
- 🎯 Model performance metrics
- 👥 Customer segmentation

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Flow                                 │
│                                                              │
│  Kafka Consumer → RDS PostgreSQL → QuickSight → Dashboard   │
│  (Predictions)    (Storage)        (Analytics)   (Visual)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Prerequisites

### 1. AWS Account Requirements

- ✅ Active AWS account
- ✅ IAM user with QuickSight permissions
- ✅ RDS PostgreSQL instance running
- ✅ Analytics tables populated (from Kafka consumer)

### 2. RDS Database Setup

**Tables Required**:
- `churn_predictions` - All predictions
- `churn_metrics_hourly` - Hourly aggregates
- `churn_metrics_daily` - Daily aggregates
- `high_risk_customers` - High-risk alerts

**Views Required**:
- `v_realtime_dashboard` - Last 24 hours
- `v_geography_churn` - Geographic analysis
- `v_churn_trends` - Trend analysis
- `v_model_performance` - Model metrics

> These are already created by `sql/create_analytics_tables.sql`

### 3. Network Configuration

**Security Group Settings**:
```bash
# Your RDS security group must allow:
- Port: 5432 (PostgreSQL)
- Source: QuickSight IP ranges for your region
```

### 4. Cost Considerations

**QuickSight Pricing**:
- **Author**: $18/month (can create dashboards)
- **Reader**: $0.30/session (view-only, max $5/month)
- **Enterprise**: $18/author + $0.30/reader

> Start with Standard Edition for learning

---

## 🚀 QuickSight Setup

### Step 1: Sign Up for QuickSight

1. **Go to AWS Console** → Search "QuickSight"
   
2. **Click "Sign up for QuickSight"**

3. **Choose Edition**:
   - Select **"Standard Edition"** (for learning)
   - Or **"Enterprise Edition"** (for production with advanced features)

4. **Set Account Name**:
   ```
   Account Name: churn-analytics-dashboard
   Notification Email: your-email@example.com
   ```

5. **Choose Authentication**:
   - Select **"Use IAM federated identities & QuickSight-managed users"**

6. **Grant Permissions**:
   - ✅ Enable access to **Amazon S3** (select your bucket)
   - ✅ Enable access to **Amazon Athena** (optional)
   - ✅ Enable access to **Amazon RDS** (select your region)

7. **Click "Finish"** and wait for setup (~2 minutes)

### Step 2: Configure QuickSight Network

1. **Go to QuickSight Console** → Click your profile icon (top right)

2. **Select "Manage QuickSight"**

3. **Go to "Security & permissions"** → **"QuickSight access to AWS services"**

4. **Enable RDS Access**:
   - Click **"Add or remove"**
   - Select your RDS region
   - Check your RDS instance
   - Click **"Update"**

### Step 3: Get QuickSight IP Ranges

1. **Go to** → https://docs.aws.amazon.com/quicksight/latest/user/regions.html

2. **Find your region's IP ranges** (example for `ap-south-1`):
   ```
   52.66.193.64/27
   13.232.67.32/27
   ```

3. **Add to RDS Security Group**:
   ```bash
   # AWS Console → RDS → Your DB → Security Group → Edit Inbound Rules
   
   Type: PostgreSQL
   Protocol: TCP
   Port Range: 5432
   Source: 52.66.193.64/27
   Description: QuickSight ap-south-1
   
   # Add another rule for the second IP range
   Type: PostgreSQL
   Protocol: TCP
   Port Range: 5432
   Source: 13.232.67.32/27
   Description: QuickSight ap-south-1
   ```

---

## 🔗 Connect to RDS

### Step 1: Create Data Source

1. **Go to QuickSight Console** → Click **"Datasets"** (left menu)

2. **Click "New dataset"**

3. **Choose "RDS"** as data source

4. **Configure Connection**:
   ```
   Data source name: churn-analytics-rds
   
   Database engine: PostgreSQL
   
   Instance ID: [Select your RDS instance from dropdown]
   (Or manually enter connection details)
   
   Database name: analytics
   
   Username: [Your RDS username]
   Password: [Your RDS password]
   ```

5. **Click "Validate connection"**
   - ✅ Should show "Successfully validated"
   - ❌ If fails, check security group and credentials

6. **Click "Create data source"**

### Step 2: Test Connection

1. **After creating data source**, you'll see schema selector

2. **Select Schema**: `public`

3. **You should see your tables**:
   - `churn_predictions`
   - `churn_metrics_hourly`
   - `churn_metrics_daily`
   - `high_risk_customers`
   - Views: `v_realtime_dashboard`, `v_geography_churn`, etc.

---

## 📊 Create Datasets

Datasets are QuickSight's way of preparing data for visualization.

---

### ⚠️ HOW TO ADD % SYMBOL (TESTED & WORKING!)

**Problem**: `churn_rate` is stored as 26.04, but you want it to display as "26.04%"

**✅ SOLUTION - Use This Calculated Field:**

```sql
concat(toString({churn_rate}), '%')
```

**Steps:**
1. Click **"Add calculated field"**
2. **Field name**: `churn_rate_pct`
3. **Formula**: `concat(toString({churn_rate}), '%')`
4. Click **"Save"**
5. Use `churn_rate_pct` in your visuals instead of `churn_rate`

**Result**: 26.04 → displays as **"26.04%"** ✅

---

**Alternative (simpler but no % symbol):**
- Just use `{churn_rate}` directly → shows "26.04"
- Everyone knows it's a percentage anyway

---

**❌ WHAT DOESN'T WORK:**
- `{churn_rate} %` → Syntax error
- Using "Percentage" data type → Shows "2604%" (multiplies by 100)
- Format options (gear icon) → Doesn't exist in dataset editor

---

### Dataset 1: Real-Time Dashboard

**Purpose**: Last 24 hours of predictions

1. **Click "New dataset"** → Select your RDS data source

2. **Choose Table**: `v_realtime_dashboard`

3. **Choose Import Method**:
   - **SPICE** (recommended): Fast, in-memory, refreshed on schedule
   - **Direct Query**: Real-time but slower

4. **Select "Import to SPICE for quicker analytics"**

5. **Click "Edit/Preview data"** (to configure)

6. **Configure Fields** (optional - just make sure types are correct):
   ```
   hour            → Date/Time field
   total_predictions → Integer
   churn_count     → Integer
   churn_rate      → Decimal/Number
   avg_risk_score  → Decimal/Number (0-1 range)
   high_risk_count → Integer
   latest_prediction → Date/Time
   ```

7. **Add Calculated Fields** (click "Add calculated field" button):

   **a) Churn Rate with % Symbol**:
   ```sql
   concat(toString({churn_rate}), '%')
   ```
   - **Field name**: `churn_rate_pct`
   - **What it does**: Adds % symbol (26.04 → "26.04%")
   
   **b) Retention Rate with % Symbol**:
   ```sql
   concat(toString(100 - {churn_rate}), '%')
   ```
   - **Field name**: `retention_rate_pct`
   - **What it does**: Calculates retention (100 - 26.04 = "73.96%")
   
   **c) Avg Risk Score with % Symbol**:
   ```sql
   concat(toString({avg_risk_score} * 100), '%')
   ```
   - **Field name**: `avg_risk_score_pct`
   - **What it does**: Converts 0.647 → "64.7%"

   **d) Hour of Day (0-23)**:
   ```sql
   extract('HH', {hour})
   ```
   - **Field name**: `hour_of_day`
   - **What it does**: Extracts hour (0-23) for hourly charts
   
   **e) Time Period**:
   ```sql
   ifelse(
     extract('HH', {hour}) < 6, 'Night (12am-6am)',
     ifelse(
       extract('HH', {hour}) < 12, 'Morning (6am-12pm)',
       ifelse(
         extract('HH', {hour}) < 18, 'Afternoon (12pm-6pm)',
         'Evening (6pm-12am)'
       )
     )
   )
   ```
   - **Field name**: `time_period`
   - **What it does**: Groups hours into time periods
   
   **f) Predictions per Minute**:
   ```sql
   {total_predictions} / 60
   ```
   - **Field name**: `predictions_per_minute`
   - **What it does**: Calculates throughput rate

8. **Click "Save & publish"**
   - Name: `Realtime Dashboard Data`

### Dataset 2: Geographic Analysis

1. **Create new dataset** → RDS source → `v_geography_churn`

2. **Edit/Preview data**

3. **Configure Fields**:
   ```
   geography       → Text (Dimension)
   total_customers → Integer
   churn_count     → Integer
   churn_rate      → Decimal/Number
   avg_age         → Number
   avg_balance     → Currency
   ```

4. **Add Calculated Fields** (click "Add calculated field"):

   **a) Churn Rate with % Symbol**:
   ```sql
   concat(toString({churn_rate}), '%')
   ```
   - **Field name**: `churn_rate_pct`
   - **What it does**: Adds % symbol (22.5 → "22.5%")

   **b) Customer Share %**:
   ```sql
  {total_customers} / sum({total_customers})
   ```
   - **Field name**: `customer_share_pct`
   - **Format**: Percentage, 1 decimal
   - **What it does**: Shows what % of total customers are in each geography
   
   **c) Churn Risk Level**:
   ```sql
   ifelse(
     {churn_rate} >= 25, 'High',
     ifelse({churn_rate} >= 20, 'Medium', 'Low')
   )
   ```
   - **Field name**: `risk_level`
   - **What it does**: Creates High/Medium/Low labels for color coding
   
   **d) Retained Customer Value**:
   ```sql
   {avg_balance} * (1 - {churn_rate}/100)
   ```
   - **Field name**: `retained_value`
   - **What it does**: Estimates value after churn (e.g., $100K * 76.5% = $76,500)
   
   **e) Revenue at Risk**:
   ```sql
   {avg_balance} * {total_customers} * ({churn_rate}/100)
   ```
   - **Field name**: `revenue_at_risk`
   - **What it does**: Total potential revenue loss from churn

5. **Save & publish**: `Geography Analysis Data`

### Dataset 3: High-Risk Customers

1. **Create new dataset** → RDS source → `v_top_risk_customers`

2. **Edit fields**:
   ```
   customer_id     → Text
   max_risk_score  → Decimal (0-1)
   last_prediction → Date/Time
   geography       → Text
   gender          → Text
   age             → Integer
   balance         → Decimal
   tenure          → Integer
   ```

3. **Add Calculated Fields**:

   **a) Risk Level Category**:
   ```sql
   ifelse(
      {max_risk_score} >= 0.9, 'Extreme Risk',
      ifelse(
      {max_risk_score} >= 0.8, 'High Risk',
      ifelse({max_risk_score} >= 0.7, 'Moderate Risk', 'Low Risk')
      )
   )
   ```
   - **Field name**: `risk_level`
   - **Format**: Text
   - **What it does**: Categorizes customers (Extreme/High/Moderate/Low)
   
   **b) Age Group**:
   ```sql
   ifelse(
     {age} < 30, '18-29',
     ifelse(
       {age} < 50, '30-49',
       ifelse({age} < 65, '50-64', '65+')
     )
   )
   ```
   - **Field name**: `age_group`
   - **Format**: Text
   - **What it does**: Groups customers by age brackets
   
   **c) Balance Category**:
   ```sql
   ifelse(
     {balance} < 50000, 'Low (<50K)',
     ifelse(
       {balance} < 100000, 'Medium (50K-100K)',
       'High (>100K)'
     )
   )
   ```
   - **Field name**: `balance_category`
   - **Format**: Text
   - **What it does**: Segments by account balance
   
   **d) Customer Priority Score**:
   ```sql
   ({max_risk_score} * 0.6) + ({balance}/200000 * 0.4)
   ```
   - **Field name**: `priority_score`
   - **Format**: Number, 2 decimals
   - **What it does**: Weighted score (60% risk + 40% balance value)

4. **Save & publish**: `High Risk Customers Data`

### Dataset 4: Churn Trends

1. **Create new dataset** → RDS source → `v_churn_trends`

2. **Edit fields**:
   ```
   date            → Date
   predictions     → Integer
   churns          → Integer
   churn_rate      → Decimal → %
   avg_risk        → Decimal
   ```

3. **Add Calculated Fields**:

   **a) 7-Day Moving Average**:
   ```sql
   windowAvg({churn_rate}, [{date} ASC], 7, 0)
   ```
   - **Field name**: `churn_rate_ma7`
   - **Format**: Number, 2 decimals, suffix "%"
   - **What it does**: Smooths out daily fluctuations with 7-day rolling average
   
   **b) Day-over-Day Change**:
   ```sql
   {churn_rate} - lag({churn_rate}, [{date} ASC], 1)
   ```
   - **Field name**: `churn_rate_dod`
   - **Format**: Number, 2 decimals, suffix "pp" (percentage points)
   - **What it does**: Shows daily change (e.g., +2.3pp means increased by 2.3%)
   
   **c) Week Number**:
   ```sql
   extract('WK', {date})
   ```
   - **Field name**: `week_number`
   - **Format**: Number, 0 decimals
   - **What it does**: Groups data by week (1-52) for weekly analysis
   
   **d) Month Name**:
   ```sql
   formatDate({date}, 'MMM yyyy')
   ```
   - **Field name**: `month_name`
   - **Format**: Text
   - **What it does**: Displays as "Jan 2024" for monthly trends
   
   **e) Is Increasing Trend**:
   ```sql
   ifelse(
     {churn_rate} > lag({churn_rate}, [{date} ASC], 1),
     '📈 Increasing',
     '📉 Decreasing'
   )
   ```
   - **Field name**: `trend_indicator`
   - **Format**: Text
   - **What it does**: Shows trend direction with emojis

4. **Save & publish**: `Churn Trends Data`

---

## 📈 Build Visualizations

Now let's create visualizations for each dataset using the exact field names.

### 📋 Available Fields by Dataset

**Dataset 1: Realtime Dashboard Data**
- Base fields: `hour`, `total_predictions`, `churn_count`, `churn_rate`, `avg_risk_score`, `high_risk_count`, `latest_prediction`
- Calculated fields: `churn_rate_pct`, `retention_rate_pct`, `avg_risk_score_pct`, `hour_of_day`, `time_period`, `predictions_per_minute`

**Dataset 2: Geography Analysis Data**
- Base fields: `geography`, `total_customers`, `churn_count`, `churn_rate`, `avg_risk_score`, `avg_age`, `avg_balance`
- Calculated fields: `churn_rate_pct`, `retention_rate_pct`, `customer_share_pct`, `risk_level`, `retained_value`, `revenue_at_risk`

**Dataset 3: High Risk Customers Data**
- Base fields: `customer_id`, `max_risk_score`, `last_prediction`, `geography`, `gender`, `age`, `balance`, `tenure`
- Calculated fields: `risk_level`, `age_group`, `balance_category`, `priority_score`

**Dataset 4: Churn Trends Data**
- Base fields: `date`, `hour`, `predictions`, `churns`, `churn_rate`, `avg_risk`
- Calculated fields: `churn_rate_ma7`, `churn_rate_dod`, `week_number`, `month_name`, `trend_indicator`

---





### Visualization 1: Churn Rate KPI

**Dataset**: `Realtime Dashboard Data`

1. **Create Analysis** → **New analysis** → Select `Realtime Dashboard Data`

2. **Add Visual** → Choose **KPI**

3. **Drag Fields**:
   - **Value**: Drag `churn_rate` to the "Value" field well
   - **Trend Group**: Leave empty (or drag `hour` if you want hourly trend)

4. **Configure Value**:
   - Click dropdown on `churn_rate` in Value field well
   - **Aggregate**: Max or Average (since data is already aggregated by hour)
   - **Show as**: Number
   
5. **Add Conditional Formatting**:
   - Click on the visual → Format visual (paintbrush icon)
   - Go to "Conditional formatting"
   - Click "+" to add rules:
     - **Rule 1**: If `churn_rate` < 15 → Green color
     - **Rule 2**: If `churn_rate` >= 15 and < 20 → Yellow color  
     - **Rule 3**: If `churn_rate` >= 20 → Red color

6. **Title**: Click "..." → Edit title → "Current Churn Rate (%)"

7. **Optional - Add Comparison**:
   - In visual settings, enable "Comparison"
   - Compare to: Previous value (compares current hour to previous hour)
   - Or skip comparison if not needed

   **Fields Used**: `churn_rate` (displayed with conditional colors)

### Visualization 2: Prediction Volume Over Time

**Dataset**: `Realtime Dashboard Data`

1. **Add Visual** → Choose **Line Chart**

2. **Configure**:
   ```
   X-axis: hour (Date/Time field)
   Value: total_predictions
   Aggregation: Sum
   
   Optional - Add second line:
   Value: predictions_per_minute (calculated field)
   Aggregation: Average
   ```

3. **Title**: "Hourly Prediction Volume (Last 24 Hours)"

   **Fields Used**: `hour`, `total_predictions`, `predictions_per_minute` (optional)

### Visualization 3: Geographic Distribution

**Dataset**: `Geography Analysis Data`

1. **Add Visual** → Choose **Pie Chart** or **Donut Chart**

2. **Configure**:
   ```
   Group by: geography
   Value: total_customers
   Aggregation: Sum
   
   Optional - Show calculated %:
   Add: customer_share_pct (calculated field)
   ```

3. **Title**: "Customer Distribution by Geography"

   **Fields Used**: `geography`, `total_customers`, `customer_share_pct`

### Visualization 4: Churn Rate by Geography

**Dataset**: `Geography Analysis Data`

1. **Add Visual** → Choose **Bar Chart** (Horizontal)

2. **Configure**:
   ```
   Y-axis: geography
   Value: churn_rate_pct (calculated field with %)
   Aggregation: Max or First (it's already aggregated from the view)
   
   Sort: Descending by churn_rate
   
   Color: risk_level (calculated field - High/Medium/Low)
   
   Conditional Formatting (based on churn_rate):
   - Green: < 18
   - Yellow: 18-22
   - Red: > 22
   ```

3. **Title**: "Churn Rate by Region"

   **Fields Used**: `geography`, `churn_rate_pct`, `churn_rate`, `risk_level`

### Visualization 5: High-Risk Customers Table

**Dataset**: `High Risk Customers Data`

1. **Add Visual** → Choose **Table**

2. **Configure Columns**:
   ```
   - customer_id
   - max_risk_score (shows as 0.85)
   - risk_level (calculated field: Extreme/High/Moderate/Low)
   - geography
   - gender
   - age_group (calculated field: 18-29, 30-49, etc.)
   - age (actual age number)
   - balance_category (calculated field: Low/Medium/High)
   - balance (actual balance in $)
   - tenure (years with bank)
   - last_prediction (timestamp)
   - priority_score (calculated field - weighted score)
   ```

3. **Sort**: By `priority_score` or `max_risk_score` descending

4. **Conditional Formatting** (based on max_risk_score):
   ```
   - Dark Red: >= 0.9
   - Orange: >= 0.8 and < 0.9
   - Yellow: >= 0.7 and < 0.8
   ```

5. **Limit**: Top 20-50 rows

6. **Title**: "Top High-Risk Customers"

   **Fields Used**: `customer_id`, `max_risk_score`, `risk_level`, `geography`, `gender`, `age`, `age_group`, `balance`, `balance_category`, `tenure`, `last_prediction`, `priority_score`

### Visualization 6: Churn Trend with Moving Average

**Dataset**: `Churn Trends Data`

1. **Add Visual** → Choose **Combo Chart** (Line + Line)

2. **Configure**:
   ```
   X-axis: date
   
   Lines:
   - Line 1: churn_rate (Actual daily rate)
     Aggregation: Average
     Color: Red
   
   - Line 2: churn_rate_ma7 (7-day moving average calculated field)
     Aggregation: Average
     Color: Blue (make it dashed in formatting options)
   
   Optional - Add day-over-day change:
   - Line 3: churn_rate_dod (change from previous day)
     Show on secondary Y-axis
   ```

3. **Add Trend Indicator**:
   - Use `trend_indicator` field (📈 Increasing / 📉 Decreasing)
   - Display as tooltip or legend

4. **Title**: "Churn Rate Trend (Last 90 Days)"

   **Fields Used**: `date`, `churn_rate`, `churn_rate_ma7`, `churn_rate_dod`, `trend_indicator`

### Visualization 7: Risk Score Distribution

**Dataset**: `High Risk Customers Data`

1. **Add Visual** → Choose **Histogram** or **Bar Chart**

2. **Configure**:
   ```
   X-axis: risk_level (calculated field: Extreme/High/Moderate/Low)
   Value: customer_id
   Aggregation: Count
   
   Alternative - Use actual scores:
   X-axis: max_risk_score (group into bins 0.7-0.8, 0.8-0.9, 0.9-1.0)
   Value: customer_id
   Aggregation: Count
   
   Color by: risk_level or age_group
   ```

3. **Title**: "Risk Score Distribution"

   **Fields Used**: `max_risk_score`, `risk_level`, `customer_id`, `age_group` (optional)

### Visualization 8: Age vs Balance Scatter

**Dataset**: `High Risk Customers Data`

1. **Add Visual** → Choose **Scatter Plot**

2. **Configure**:
   ```
   X-axis: age
   Y-axis: balance
   Size: max_risk_score (larger bubble = higher risk)
   Color: geography or risk_level
   
   Group by: customer_id (each point is a customer)
   
   Tooltip - Show on hover:
   - customer_id
   - max_risk_score
   - risk_level
   - age_group
   - balance_category
   - priority_score
   ```

3. **Format**:
   - Show trend line (optional)
   - Add quadrant lines at median age and balance

4. **Title**: "High-Risk Customers: Age vs Balance Analysis"

   **Fields Used**: `age`, `balance`, `max_risk_score`, `geography`, `risk_level`, `customer_id`, `age_group`, `balance_category`, `priority_score`

---

## 🎨 Create Dashboard

### Step 1: Organize Visuals

**Layout Recommendation**:

```
┌────────────────────────────────────────────────────────────┐
│  CHURN ANALYTICS DASHBOARD                                  │
├──────────────┬──────────────┬──────────────┬───────────────┤
│  Churn KPI   │ Predictions  │  High Risk   │  Avg Risk     │
│  (23.5%)     │  (2,450)     │  (245)       │  (0.45)       │
├──────────────┴──────────────┴──────────────┴───────────────┤
│  Hourly Prediction Volume (Line Chart)                      │
│                                                              │
├──────────────────────────┬──────────────────────────────────┤
│  Customer Distribution   │  Churn Rate by Geography         │
│  (Pie Chart)             │  (Bar Chart)                     │
│                          │                                  │
├──────────────────────────┴──────────────────────────────────┤
│  Churn Trend Over Time (30 Days) - Line Chart               │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Top 20 High-Risk Customers (Table)                          │
│                                                              │
├──────────────────────────┬──────────────────────────────────┤
│  Risk Score Distribution │  Age vs Balance Scatter          │
│  (Histogram)             │  (Scatter Plot)                  │
└──────────────────────────┴──────────────────────────────────┘
```

### Step 2: Publish Dashboard

1. **Click "Share"** (top right) → **"Publish dashboard"**

2. **Dashboard Settings**:
   ```
   Dashboard name: Churn Prediction Analytics
   
   Description: Real-time customer churn prediction analytics 
                with model performance monitoring
   
   Permissions:
   - Add users/groups who can view
   ```

3. **Click "Publish dashboard"**

### Step 3: Add Filters

1. **Click "Filter"** (left panel) → **"Add filter"**

2. **Add Date Range Filter**:
   ```
   Field: hour (or date)
   Filter type: Time range
   Default: Last 7 days
   ```

3. **Add Geography Filter**:
   ```
   Field: geography
   Filter type: Multi-select dropdown
   Default: All
   ```

4. **Apply to All Visuals**: Check "Apply to all visuals"

### Step 4: Add Parameters (Advanced)

**Create Threshold Parameter**:

1. **Click "Parameters"** → **"Create parameter"**

2. **Configure**:
   ```
   Name: churn_threshold
   Data type: Decimal
   Default value: 0.20 (20%)
   Display as: Slider (0.10 - 0.40)
   ```

3. **Create Calculated Field Using Parameter**:
   ```sql
   -- Field name: is_above_threshold
   -- Note: churn_rate is 23.5 (percentage), parameter is 0.20 (decimal)
   -- So multiply parameter by 100 to compare: 23.5 > (0.20 * 100) = 23.5 > 20
   ifelse({churn_rate} > ${churn_threshold} * 100, 'Above Threshold', 'Below Threshold')
   ```
   - This field changes dynamically when user adjusts the slider
   - Example: If threshold = 0.20 (20%), then 23.5% churn is "Above Threshold"
   
4. **Use in Conditional Formatting**:
   ```sql
   -- For color rules on visuals
   ifelse({churn_rate} > ${churn_threshold} * 100, '#FF0000', '#00FF00')
   ```
   - Red if above threshold, Green if below
   - Dynamically updates when slider changes

---

## 🔄 Schedule Refresh

Keep your dashboard up-to-date with scheduled refreshes.

### Step 1: Configure SPICE Refresh

1. **Go to Datasets** → Select your dataset

2. **Click "Schedule refresh"**

3. **Add Schedule**:
   ```
   Refresh type: Full refresh
   
   Frequency: Hourly
   Starting: 00:00
   Time zone: Your timezone
   
   Or for daily:
   Frequency: Daily
   Time: 06:00 AM
   ```

4. **Click "Save"**

### Recommended Refresh Schedules

| Dataset | Refresh Frequency | Reason |
|---------|------------------|---------|
| Realtime Dashboard | Every 1 hour | Keep metrics current |
| Geography Analysis | Every 6 hours | Less frequent changes |
| High-Risk Customers | Every 2 hours | Important for alerts |
| Churn Trends | Daily | Historical data |

### Step 2: Enable Email Alerts

1. **Go to Dashboard** → **Click "Share"** → **"Manage subscriptions"**

2. **Create Email Report**:
   ```
   Subject: Daily Churn Analytics Report
   Recipients: team@company.com
   Schedule: Daily at 8:00 AM
   Format: PDF
   ```

---

## 👥 Share Dashboard

### Option 1: Share with AWS Users

1. **Click "Share"** → **"Share dashboard"**

2. **Add Users**:
   ```
   Enter AWS account email addresses
   
   Permissions:
   - Viewer: Can only view
   - Co-owner: Can edit
   ```

3. **Click "Share"**

### Option 2: Embed in Website (Enterprise Only)

1. **Go to Dashboard** → **"Share"** → **"Embed"**

2. **Get Embed Code**:
   ```html
   <iframe 
     width="100%" 
     height="700px" 
     src="https://quicksight.aws.amazon.com/embed/..."
   </iframe>
   ```

3. **Configure Domain Whitelist**:
   - **Manage QuickSight** → **"Domains & embedding"**
   - Add your website domain

### Option 3: Public Dashboard (Not Recommended)

QuickSight doesn't support truly public dashboards. Options:
- Share via cognito identity pool
- Use AWS Amplify for authentication
- Create read-only IAM users

---

## 🎯 Best Practices

### 1. Performance Optimization

**Use SPICE Efficiently**:
```sql
-- Instead of:
SELECT * FROM churn_predictions

-- Use filtered views:
SELECT * FROM churn_predictions 
WHERE predicted_at >= NOW() - INTERVAL '30 days'
```

**Aggregate Data**:
- Use `churn_metrics_hourly` instead of raw `churn_predictions`
- Pre-aggregate in database views
- Limit dataset size to what you need

### 2. Dashboard Design

**Keep It Simple**:
- Max 8-10 visuals per dashboard
- Use consistent colors (Red = bad, Green = good)
- Add clear titles and descriptions
- Use filters for drill-down

**Visual Hierarchy**:
- Most important KPIs at top
- Trends in middle
- Detailed tables at bottom

### 3. Security

**Data Access**:
- Use row-level security (RLS) for multi-tenant
- Separate dashboards for different teams
- Audit access logs regularly

**Example RLS**:
```sql
-- In QuickSight dataset settings
-- Add rule: geography = ${username_geography}
```

### 4. Monitoring

**Track Dashboard Usage**:
- QuickSight → "Usage metrics"
- See who views dashboards
- Identify unused visuals

### 5. Cost Optimization

**Reduce SPICE Usage**:
- Only import necessary columns
- Use incremental refresh where possible
- Archive old data

**Reader Licensing**:
- Use session-based pricing ($0.30/session)
- Max $5/reader/month
- Good for occasional viewers

---

## 🐛 Troubleshooting

### Issue 1: Cannot Connect to RDS

**Symptoms**:
```
Error: Could not connect to database
Connection timeout
```

**Solutions**:

1. **Check Security Group**:
   ```bash
   # RDS Security Group must allow QuickSight IP ranges
   aws ec2 describe-security-groups --group-ids sg-xxxxx
   ```

2. **Verify RDS is Public** (if needed):
   ```bash
   # RDS → Modify → Publicly accessible: Yes
   ```

3. **Test Connection**:
   ```bash
   psql "host=$RDS_HOST port=5432 dbname=analytics user=admin"
   ```

### Issue 2: SPICE Refresh Fails

**Symptoms**:
```
Error: SPICE capacity exceeded
Error: Dataset refresh failed
```

**Solutions**:

1. **Check SPICE Capacity**:
   - QuickSight → Manage QuickSight → SPICE capacity
   - Free tier: 1GB, Standard: 10GB/user

2. **Reduce Dataset Size**:
   ```sql
   -- Add date filter to view
   WHERE predicted_at >= CURRENT_DATE - INTERVAL '30 days'
   ```

3. **Purchase More SPICE**:
   - $0.25/GB/month (if needed)

### Issue 3: Visuals Show No Data

**Symptoms**:
- Charts are empty
- "No data to display"

**Solutions**:

1. **Check Data in RDS**:
   ```sql
   SELECT COUNT(*) FROM churn_predictions;
   SELECT * FROM v_realtime_dashboard LIMIT 10;
   ```

2. **Refresh Dataset**:
   - Datasets → Select dataset → Refresh now

3. **Check Filters**:
   - Remove all filters
   - Check date ranges

### Issue 4: Slow Dashboard Loading

**Symptoms**:
- Dashboard takes > 10 seconds to load
- Timeout errors

**Solutions**:

1. **Use SPICE Instead of Direct Query**

2. **Optimize SQL Views**:
   ```sql
   -- Add indexes
   CREATE INDEX idx_predictions_date 
   ON churn_predictions(predicted_at);
   
   CREATE INDEX idx_predictions_geography 
   ON churn_predictions(geography);
   ```

3. **Limit Data Range**:
   - Show last 30 days by default
   - Use filters for historical data

### Issue 5: Colors Not Showing Correctly

**Symptoms**:
- Conditional formatting not working
- Wrong colors applied

**Solutions**:

1. **Check Field Types**:
   - Percentage fields must be decimal/float
   - Not text

2. **Reconfigure Conditional Formatting**:
   ```
   Click visual → Format visual → Conditional formatting
   Clear and re-add rules
   ```

---

## 📊 Sample SQL Queries for Custom Views

### View 1: Executive Summary

```sql
CREATE OR REPLACE VIEW v_executive_summary AS
SELECT 
    COUNT(*) as total_predictions_today,
    SUM(CASE WHEN prediction = 1 THEN 1 ELSE 0 END) as churns_today,
    ROUND(AVG(CASE WHEN prediction = 1 THEN 1.0 ELSE 0.0 END) * 100, 2) as churn_rate_pct,
    COUNT(CASE WHEN risk_score >= 0.7 THEN 1 END) as high_risk_count,
    ROUND(AVG(probability), 3) as avg_confidence
FROM churn_predictions
WHERE predicted_at >= CURRENT_DATE;
```

### View 2: Hourly Performance

```sql
CREATE OR REPLACE VIEW v_hourly_performance AS
SELECT 
    DATE_TRUNC('hour', predicted_at) as hour,
    COUNT(*) as predictions,
    AVG(CASE WHEN prediction = 1 THEN 1.0 ELSE 0.0 END) * 100 as churn_rate,
    AVG(probability) as avg_confidence,
    AVG(risk_score) as avg_risk
FROM churn_predictions
WHERE predicted_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', predicted_at)
ORDER BY hour DESC;
```

### View 3: Customer Segments

```sql
CREATE OR REPLACE VIEW v_customer_segments AS
SELECT 
    CASE 
        WHEN age < 30 THEN 'Young'
        WHEN age BETWEEN 30 AND 50 THEN 'Middle-aged'
        ELSE 'Senior'
    END as age_group,
    CASE 
        WHEN balance < 50000 THEN 'Low Balance'
        WHEN balance BETWEEN 50000 AND 150000 THEN 'Medium Balance'
        ELSE 'High Balance'
    END as balance_group,
    geography,
    COUNT(*) as customer_count,
    AVG(CASE WHEN prediction = 1 THEN 1.0 ELSE 0.0 END) * 100 as churn_rate,
    AVG(risk_score) as avg_risk_score
FROM churn_predictions
WHERE predicted_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY age_group, balance_group, geography
ORDER BY churn_rate DESC;
```

---

## 📚 Additional Resources

### Project Documentation
- 📖 **[Calculated Fields Reference](QUICKSIGHT_CALCULATED_FIELDS.md)** - Complete SQL reference for all calculated fields
- 📊 70+ ready-to-use calculated field formulas
- 🎨 Conditional formatting examples and color codes
- 🔍 Window functions and aggregations guide

### Official Documentation
- [AWS QuickSight User Guide](https://docs.aws.amazon.com/quicksight/)
- [QuickSight Pricing](https://aws.amazon.com/quicksight/pricing/)
- [QuickSight Best Practices](https://docs.aws.amazon.com/quicksight/latest/user/best-practices.html)

### Video Tutorials
- [QuickSight Getting Started](https://www.youtube.com/watch?v=gcwLG3E_EqU)
- [Building Dashboards](https://www.youtube.com/watch?v=3BWdT_hP5YU)

### Community
- [AWS QuickSight Forum](https://repost.aws/tags/TA9T4MwaDwT5GTQ_JJUXpX0g/aws-quicksight)
- [Stack Overflow - quicksight tag](https://stackoverflow.com/questions/tagged/amazon-quicksight)

---

## ✅ Checklist

### Setup Checklist
- [ ] QuickSight account created
- [ ] RDS security group configured with QuickSight IPs
- [ ] Data source connected to RDS
- [ ] All datasets created and published
- [ ] SPICE refresh scheduled

### Dashboard Checklist
- [ ] All 8 visualizations created
- [ ] Filters added and tested
- [ ] Dashboard published
- [ ] Shared with team members
- [ ] Email reports configured

### Maintenance Checklist
- [ ] Monitor SPICE usage weekly
- [ ] Review dashboard usage metrics monthly
- [ ] Update visuals based on feedback
- [ ] Check refresh schedules working
- [ ] Audit user access quarterly

---

## 🎓 Next Steps

1. ✅ **Set up QuickSight** and connect to RDS
2. ✅ **Create datasets** from your analytics tables
3. ✅ **Build visualizations** following this guide
4. ✅ **Publish dashboard** and share with team
5. ✅ **Schedule refreshes** to keep data current
6. ✅ **Monitor usage** and optimize based on feedback

---

**Created**: 2024-01-19  
**Author**: ML Platform Team  
**Status**: ✅ Production-Ready



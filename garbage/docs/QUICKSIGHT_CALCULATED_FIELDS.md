# 📊 QuickSight Calculated Fields Reference

Complete reference of all calculated fields used in the Churn Prediction Dashboard.

---

## ⚠️ Important: How Data is Stored & How to Add % Symbol

| Field | Stored Value | How to Display with % |
|-------|--------------|----------------------|
| `churn_rate` | **23.5** (already %) | Use: `concat(toString({churn_rate}), '%')` → shows "23.5%" |
| `avg_risk_score` / `max_risk_score` | **0.85** (decimal 0-1) | Use: `concat(toString({avg_risk_score} * 100), '%')` → shows "85%" |
| Retention Rate | Calculated from churn_rate | Use: `concat(toString(100 - {churn_rate}), '%')` → shows "76.5%" |

### ✅ THE WORKING SOLUTION:

**To add % symbol to any number field:**
```sql
concat(toString({field_name}), '%')
```

**Example for churn_rate:**
```sql
concat(toString({churn_rate}), '%')
```
Result: 26.04 → "26.04%"

### ❌ WHAT DOESN'T WORK:
- `{churn_rate} %` → Syntax error!
- Using "Percentage" data type for `churn_rate` → Shows "2604%"!
- Format options (gear icon) → Doesn't exist in dataset editor

---

## 📋 Table of Contents

1. [Basic Calculations](#basic-calculations)
2. [Aggregations](#aggregations)
3. [Window Functions](#window-functions)
4. [Date/Time Functions](#datetime-functions)
5. [Conditional Logic](#conditional-logic)
6. [String Functions](#string-functions)
7. [Dashboard-Specific Fields](#dashboard-specific-fields)

---

## 🔢 Basic Calculations

### Churn Rate with % Symbol

```sql
-- Field name: churn_rate_pct
concat(toString({churn_rate}), '%')
```
**Result**: 26.04 → displays as **"26.04%"** ✅  
**Use**: Display churn rate with % symbol in visuals

### Retention Rate with % Symbol

```sql
-- Field name: retention_rate_pct
concat(toString(100 - {churn_rate}), '%')
```
**Result**: 26.04 churn → displays as **"73.96%"** retention ✅  
**Use**: Calculate and display retention rate (inverse of churn)

### Risk Score with % Symbol

```sql
-- Field name: avg_risk_score_pct or max_risk_score_pct
concat(toString({avg_risk_score} * 100), '%')
```
**Result**: 0.85 → displays as **"85%"** ✅  
**Use**: Display risk score as percentage (converts 0-1 to 0-100)

### Customer Lifetime Value (CLV)

```sql
-- Field name: customer_ltv
{avg_balance} * {tenure} * (1 - {churn_rate}/100)
```
**Use**: Estimate customer value considering churn risk

### Revenue at Risk

```sql
-- Field name: revenue_at_risk
{avg_balance} * {total_customers} * ({churn_rate}/100)
```
**Use**: Calculate potential revenue loss from churn

---

## 📊 Aggregations

### Customer Share

```sql
-- Field name: customer_share_pct
{total_customers} / sum({total_customers})
```
**Format**: Percentage, 1 decimal  
**Use**: Show what % of customers are in each segment

### Market Concentration

```sql
-- Field name: market_concentration
sum({total_customers}) / countOver({geography}, [], PRE_AGG)
```
**Use**: Calculate average customers per region

### Weighted Churn Rate

```sql
-- Field name: weighted_churn_rate
sumOver({churns} * {total_customers}, [], PRE_AGG) / 
sumOver({total_customers}, [], PRE_AGG)
```
**Use**: Churn rate weighted by customer volume

---

## 🔄 Window Functions

### 7-Day Moving Average

```sql
-- Field name: churn_rate_ma7
windowAvg({churn_rate}, [{date} ASC], 7, 0)
```
**Use**: Smooth out daily fluctuations in churn rate

### 30-Day Moving Average

```sql
-- Field name: churn_rate_ma30
windowAvg({churn_rate}, [{date} ASC], 30, 0)
```
**Use**: Show longer-term trends

### Day-over-Day Change

```sql
-- Field name: churn_rate_dod
{churn_rate} - lag({churn_rate}, [{date} ASC], 1)
```
**Use**: Show daily change in churn rate

### Week-over-Week Change

```sql
-- Field name: churn_rate_wow
{churn_rate} - lag({churn_rate}, [{date} ASC], 7)
```
**Use**: Compare to same day last week

### Cumulative Predictions

```sql
-- Field name: cumulative_predictions
windowSum({total_predictions}, [{date} ASC], 0, 0)
```
**Use**: Running total of predictions

### Rank by Risk Score

```sql
-- Field name: risk_rank
rank({max_risk_score}, [{max_risk_score} DESC])
```
**Use**: Rank customers by risk (1 = highest risk)

### Percentile Rank

```sql
-- Field name: risk_percentile
percentileRank({max_risk_score})
```
**Use**: Show what percentile customer is in (0-100)

---

## 📅 Date/Time Functions

### Hour of Day

```sql
-- Field name: hour_of_day
extract('HH', {hour})
```
**Use**: Extract hour (0-23) for hourly analysis

### Day of Week

```sql
-- Field name: day_of_week
formatDate({date}, 'EEE')
```
**Result**: Mon, Tue, Wed, etc.

### Day Name (Full)

```sql
-- Field name: day_name
formatDate({date}, 'EEEE')
```
**Result**: Monday, Tuesday, etc.

### Week Number

```sql
-- Field name: week_number
extract('WK', {date})
```
**Use**: Group by week (1-52)

### Month Name

```sql
-- Field name: month_name
formatDate({date}, 'MMM yyyy')
```
**Result**: Jan 2024, Feb 2024, etc.

### Quarter

```sql
-- Field name: quarter
concat('Q', toString(extract('QQ', {date})))
```
**Result**: Q1, Q2, Q3, Q4

### Is Weekend

```sql
-- Field name: is_weekend
ifelse(
  extract('DD', {date}) = 1 OR extract('DD', {date}) = 7,
  'Weekend',
  'Weekday'
)
```
**Use**: Segment by weekend vs weekday

### Days Since Last Prediction

```sql
-- Field name: days_since_last_prediction
dateDiff(max({predicted_at}), now())
```
**Use**: Track recency of predictions

---

## ⚡ Conditional Logic

### Churn Rate Status

```sql
-- Field name: churn_rate_status
-- Note: churn_rate is 23.5 (already percentage), so compare to 25, 20, etc.
ifelse(
  {churn_rate} >= 25, 'High',
  ifelse({churn_rate} >= 20, 'Medium', 'Low')
)
```
**Use**: Color-code churn rates (Red/Yellow/Green)  
**Logic**: High if ≥25%, Medium if ≥20%, Low if <20%

### Risk Level

```sql
-- Field name: risk_level
ifelse(
  {max_risk_score} >= 0.9, 'Extreme Risk',
  ifelse(
    {max_risk_score} >= 0.8, 'High Risk',
    ifelse({max_risk_score} >= 0.7, 'Moderate Risk', 'Low Risk')
  )
)
```
**Use**: Categorize customers by risk level

### Age Group

```sql
-- Field name: age_group
ifelse(
  {age} < 30, '18-29',
  ifelse(
    {age} < 50, '30-49',
    ifelse({age} < 65, '50-64', '65+')
  )
)
```
**Use**: Segment customers by age

### Balance Category

```sql
-- Field name: balance_category
ifelse(
  {balance} < 50000, 'Low (<50K)',
  ifelse(
    {balance} < 100000, 'Medium (50K-100K)',
    'High (>100K)'
  )
)
```
**Use**: Segment by account balance

### Tenure Segment

```sql
-- Field name: tenure_segment
ifelse(
  {tenure} < 2, 'New (0-2 yrs)',
  ifelse(
    {tenure} < 5, 'Medium (2-5 yrs)',
    'Long-term (5+ yrs)'
  )
)
```
**Use**: Group by customer tenure

### Is High Risk

```sql
-- Field name: is_high_risk
ifelse({max_risk_score} >= 0.7, 1, 0)
```
**Use**: Binary flag for high-risk customers

### Alert Level

```sql
-- Field name: alert_level
ifelse(
  {max_risk_score} >= 0.9, '🔴 Critical',
  ifelse(
    {max_risk_score} >= 0.8, '🟠 High',
    ifelse(
      {max_risk_score} >= 0.7, '🟡 Medium',
      '🟢 Low'
    )
  )
)
```
**Use**: Visual alerts with emojis

---

## 🔤 String Functions

### Full Customer Label

```sql
-- Field name: customer_label
concat({customer_id}, ' - ', {geography})
```
**Result**: "15634602 - Germany"

### Risk Summary

```sql
-- Field name: risk_summary
concat(
  'Risk: ',
  toString(round({max_risk_score} * 100, 1)),
  '% | ',
  {geography}
)
```
**Result**: "Risk: 85.3% | Germany"

### Customer Profile

```sql
-- Field name: customer_profile
concat(
  'Age: ', toString({age}),
  ' | Balance: $', toString(round({balance}, 0)),
  ' | Tenure: ', toString({tenure}), ' yrs'
)
```
**Result**: "Age: 42 | Balance: $125000 | Tenure: 5 yrs"

---

## 🎯 Dashboard-Specific Fields

### Above Threshold (with Parameter)

```sql
-- Field name: is_above_threshold
-- churn_rate is 23.5, parameter is 0.20, so multiply parameter by 100
-- Example: 23.5 > (0.20 * 100) → 23.5 > 20 → 'Above'
ifelse({churn_rate} > ${churn_threshold} * 100, 'Above', 'Below')
```
**Use**: Compare to user-defined threshold parameter  
**Parameter**: churn_threshold (decimal 0.10-0.40, represents 10%-40%)

### Threshold Color

```sql
-- Field name: threshold_color
-- Same logic: multiply parameter by 100 to match churn_rate scale
ifelse({churn_rate} > ${churn_threshold} * 100, '#FF0000', '#00FF00')
```
**Use**: Dynamic color based on threshold (Red if above, Green if below)  
**Result**: Updates automatically when user adjusts slider

### Geography Emoji

```sql
-- Field name: geography_emoji
ifelse(
  {geography} = 'France', '🇫🇷',
  ifelse({geography} = 'Germany', '🇩🇪', '🇪🇸')
)
```
**Use**: Add country flags to geography

### Performance vs Target

```sql
-- Field name: performance_vs_target
{churn_rate} - ${target_churn_rate}
```
**Use**: Show variance from target

### Predictions This Hour

```sql
-- Field name: predictions_this_hour
sumIf({total_predictions}, extract('HH', {hour}) = extract('HH', now()))
```
**Use**: Real-time current hour count

### YTD Predictions

```sql
-- Field name: predictions_ytd
sumIf(
  {total_predictions},
  extract('YYYY', {date}) = extract('YYYY', now())
)
```
**Use**: Year-to-date total

### Month-over-Month Growth

```sql
-- Field name: mom_growth
({churn_rate} - lag({churn_rate}, [{month_name} ASC], 1)) /
lag({churn_rate}, [{month_name} ASC], 1) * 100
```
**Format**: Percentage, 1 decimal  
**Use**: Show monthly growth rate

---

## 🎨 Conditional Formatting Examples

### Traffic Light Colors

```sql
-- For churn rate visualization
ifelse(
  {churn_rate} > 25, '#DC143C',  -- Crimson Red
  ifelse({churn_rate} > 20, '#FFA500', '#32CD32')  -- Orange or Green
)
```

### Heat Map Colors

```sql
-- For risk score heatmap
ifelse(
  {max_risk_score} >= 0.9, '#8B0000',  -- Dark Red
  ifelse(
    {max_risk_score} >= 0.8, '#DC143C',  -- Crimson
    ifelse(
      {max_risk_score} >= 0.7, '#FF6347',  -- Tomato
      '#90EE90'  -- Light Green
    )
  )
)
```

### Gradient by Value

```sql
-- RGB interpolation for 0-100 scale
concat(
  'rgb(',
  toString(round(255 * {churn_rate}/100, 0)), ', ',
  toString(round(255 * (1 - {churn_rate}/100), 0)), ', 0)'
)
```

---

## 📊 Advanced Calculations

### Churn Prediction Accuracy (if you have actuals)

```sql
-- Field name: prediction_accuracy
countIf({prediction} = {actual_churn}) / count({customer_id}) * 100
```
**Use**: Calculate model accuracy

### Customer Segmentation Score

```sql
-- Field name: segment_score
({max_risk_score} * 0.4) +
({churn_rate}/100 * 0.3) +
({tenure}/10 * 0.2) +
(ifelse({is_active_member} = 1, 0.1, 0))
```
**Use**: Composite score for segmentation

### Retention Rate

```sql
-- Field name: retention_rate
100 - {churn_rate}
```
**Format**: Percentage, 2 decimals  
**Use**: Inverse of churn rate

### At-Risk Customer Count

```sql
-- Field name: at_risk_count
countIf({max_risk_score} >= 0.7)
```
**Use**: Count of high-risk customers

---

## 🔍 Tips for Creating Calculated Fields

### Best Practices

1. **Use Descriptive Names**: `churn_rate_ma7` not `cr_avg`
2. **Add Comments**: Use `-- Field name:` for clarity
3. **Test with Sample Data**: Verify calculations before adding to dashboard
4. **Format Appropriately**: Set number formats, decimals, colors
5. **Document Parameters**: Note what parameters are used

### Common Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `ifelse()` | Conditional logic | `ifelse({x} > 10, 'High', 'Low')` |
| `sum()` | Sum values | `sum({total_predictions})` |
| `avg()` | Average | `avg({churn_rate})` |
| `count()` | Count rows | `count({customer_id})` |
| `windowAvg()` | Moving average | `windowAvg({x}, [{date} ASC], 7, 0)` |
| `lag()` | Previous value | `lag({x}, [{date} ASC], 1)` |
| `extract()` | Date part | `extract('HH', {hour})` |
| `formatDate()` | Format date | `formatDate({date}, 'MMM yyyy')` |
| `concat()` | Join strings | `concat({first}, ' ', {last})` |
| `round()` | Round number | `round({x}, 2)` |

### Syntax Reference

```sql
-- Basic math
{field1} + {field2}
{field1} * 100
{field1} / {field2}

-- Aggregations
sum({field})
avg({field})
min({field})
max({field})
count({field})
countIf({field} > 10)

-- Window functions
windowSum({field}, [{date} ASC], 7, 0)
windowAvg({field}, [{partition_field}], [{sort_field} ASC], 7, 0)
lag({field}, [{date} ASC], 1)
rank({field}, [{field} DESC])

-- Conditional
ifelse(condition, true_value, false_value)
ifelse({x} > 10, 'High', ifelse({x} > 5, 'Medium', 'Low'))

-- Date functions
extract('HH', {timestamp})    -- Hour (0-23)
extract('DD', {date})          -- Day of week (1-7)
extract('WK', {date})          -- Week number
extract('MM', {date})          -- Month (1-12)
extract('YYYY', {date})        -- Year
formatDate({date}, 'MMM yyyy') -- Custom format
dateDiff({date1}, {date2})     -- Difference in days

-- String functions
concat({str1}, {str2})
toString({number})
substring({string}, start, length)
```

---

## 📝 Creating Calculated Fields in QuickSight

### Steps:

1. **Go to Dataset** → **Edit dataset**
2. **Click "Add calculated field"** (top left)
3. **Enter field name** (e.g., `churn_rate_ma7`)
4. **Enter formula** (copy from this guide)
5. **Click "Save"**
6. **Set format** (percentage, number, etc.)
7. **Test in preview**
8. **Click "Save & publish"**

---

**Created**: 2024-01-19  
**Purpose**: QuickSight calculated fields reference  
**Status**: ✅ Production-Ready


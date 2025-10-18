-- ==========================================
-- Kafka Analytics Tables for AWS QuickSight
-- ==========================================
-- Purpose: Real-time churn prediction analytics
-- Author: Zuu Crew ML Team
-- Date: 2025-10-18

-- ==========================================
-- TABLE 1: Individual Predictions (Raw Data)
-- ==========================================
CREATE TABLE IF NOT EXISTS churn_predictions (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    prediction INTEGER NOT NULL,
    probability FLOAT NOT NULL,
    risk_score FLOAT NOT NULL,
    predicted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(50),
    
    -- Customer features (for segmentation)
    geography VARCHAR(50),
    gender VARCHAR(10),
    age INTEGER,
    tenure INTEGER,
    balance FLOAT,
    num_of_products INTEGER,
    has_cr_card INTEGER,
    is_active_member INTEGER,
    estimated_salary FLOAT,
    
    -- Event tracking
    event_id VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE churn_predictions IS 'Individual customer churn predictions with timestamps';
COMMENT ON COLUMN churn_predictions.prediction IS '0=Retain, 1=Churn';
COMMENT ON COLUMN churn_predictions.probability IS 'Probability of churn (0.0-1.0)';
COMMENT ON COLUMN churn_predictions.risk_score IS 'Risk score for dashboards (0.0-1.0)';
COMMENT ON COLUMN churn_predictions.predicted_at IS 'Timestamp when prediction was made (UTC)';

-- ==========================================
-- TABLE 2: Hourly Aggregated Metrics
-- ==========================================
CREATE TABLE IF NOT EXISTS churn_metrics_hourly (
    id SERIAL PRIMARY KEY,
    hour_timestamp TIMESTAMP NOT NULL UNIQUE,
    total_predictions INTEGER NOT NULL,
    churn_count INTEGER NOT NULL,
    churn_rate FLOAT NOT NULL,
    avg_risk_score FLOAT NOT NULL,
    high_risk_count INTEGER NOT NULL,
    avg_age FLOAT,
    avg_balance FLOAT,
    avg_tenure FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE churn_metrics_hourly IS 'Hourly aggregated churn metrics';
COMMENT ON COLUMN churn_metrics_hourly.hour_timestamp IS 'Start of hour (e.g., 2025-10-18 14:00:00)';
COMMENT ON COLUMN churn_metrics_hourly.churn_rate IS 'Percentage of customers predicted to churn';
COMMENT ON COLUMN churn_metrics_hourly.high_risk_count IS 'Number of customers with risk_score >= 0.7';

-- ==========================================
-- TABLE 3: Daily Aggregated Metrics
-- ==========================================
CREATE TABLE IF NOT EXISTS churn_metrics_daily (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    total_predictions INTEGER NOT NULL,
    churn_count INTEGER NOT NULL,
    churn_rate FLOAT NOT NULL,
    avg_risk_score FLOAT NOT NULL,
    high_risk_count INTEGER NOT NULL,
    avg_age FLOAT,
    avg_balance FLOAT,
    avg_tenure FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE churn_metrics_daily IS 'Daily aggregated churn metrics';
COMMENT ON COLUMN churn_metrics_daily.date IS 'Date of metrics (YYYY-MM-DD)';

-- ==========================================
-- TABLE 4: High-Risk Customer Alerts
-- ==========================================
CREATE TABLE IF NOT EXISTS high_risk_customers (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    risk_score FLOAT NOT NULL,
    geography VARCHAR(50),
    gender VARCHAR(10),
    age INTEGER,
    balance FLOAT,
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    alert_sent BOOLEAN DEFAULT FALSE,
    alert_sent_at TIMESTAMP,
    CONSTRAINT unique_customer_alert UNIQUE (customer_id, detected_at)
);

COMMENT ON TABLE high_risk_customers IS 'High-risk customer alerts (risk_score >= 0.7)';
COMMENT ON COLUMN high_risk_customers.detected_at IS 'When high risk was first detected';
COMMENT ON COLUMN high_risk_customers.alert_sent IS 'Whether retention team was notified';

-- ==========================================
-- INDEXES for Query Performance
-- ==========================================

-- Predictions table indexes
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp 
    ON churn_predictions(predicted_at DESC);

CREATE INDEX IF NOT EXISTS idx_predictions_customer 
    ON churn_predictions(customer_id);

CREATE INDEX IF NOT EXISTS idx_predictions_risk 
    ON churn_predictions(risk_score DESC);

CREATE INDEX IF NOT EXISTS idx_predictions_geography 
    ON churn_predictions(geography);

CREATE INDEX IF NOT EXISTS idx_predictions_date 
    ON churn_predictions(DATE(predicted_at));

-- Hourly metrics indexes
CREATE INDEX IF NOT EXISTS idx_hourly_timestamp 
    ON churn_metrics_hourly(hour_timestamp DESC);

-- Daily metrics indexes
CREATE INDEX IF NOT EXISTS idx_daily_date 
    ON churn_metrics_daily(date DESC);

-- High-risk customers indexes
CREATE INDEX IF NOT EXISTS idx_high_risk_detected 
    ON high_risk_customers(detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_high_risk_score 
    ON high_risk_customers(risk_score DESC);

CREATE INDEX IF NOT EXISTS idx_high_risk_customer 
    ON high_risk_customers(customer_id);

-- ==========================================
-- VIEWS for AWS QuickSight Dashboards
-- ==========================================

-- View 1: Real-time Dashboard (Last 24 Hours)
CREATE OR REPLACE VIEW v_realtime_dashboard AS
SELECT 
    DATE_TRUNC('hour', predicted_at) as hour,
    COUNT(*) as total_predictions,
    SUM(prediction) as churn_count,
    ROUND((SUM(prediction)::float / COUNT(*)::float * 100)::numeric, 2) as churn_rate,
    ROUND(AVG(risk_score)::numeric, 3) as avg_risk_score,
    SUM(CASE WHEN risk_score >= 0.7 THEN 1 ELSE 0 END) as high_risk_count,
    MAX(predicted_at) as latest_prediction
FROM churn_predictions
WHERE predicted_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', predicted_at)
ORDER BY hour DESC;

COMMENT ON VIEW v_realtime_dashboard IS 'Real-time metrics for last 24 hours (hourly aggregation)';

-- View 2: Top High-Risk Customers (Last 7 Days)
CREATE OR REPLACE VIEW v_top_risk_customers AS
SELECT 
    customer_id,
    MAX(risk_score) as max_risk_score,
    MAX(predicted_at) as last_prediction,
    geography,
    gender,
    age,
    balance,
    tenure
FROM churn_predictions
WHERE predicted_at >= NOW() - INTERVAL '7 days'
    AND risk_score >= 0.7
GROUP BY customer_id, geography, gender, age, balance, tenure
ORDER BY max_risk_score DESC
LIMIT 100;

COMMENT ON VIEW v_top_risk_customers IS 'Top 100 high-risk customers from last 7 days';

-- View 3: Geography-wise Churn Analysis
CREATE OR REPLACE VIEW v_geography_churn AS
SELECT 
    geography,
    COUNT(*) as total_customers,
    SUM(prediction) as churn_count,
    ROUND((SUM(prediction)::float / COUNT(*)::float * 100)::numeric, 2) as churn_rate,
    ROUND(AVG(risk_score)::numeric, 3) as avg_risk_score,
    ROUND(AVG(age)::numeric, 1) as avg_age,
    ROUND(AVG(balance)::numeric, 2) as avg_balance
FROM churn_predictions
WHERE predicted_at >= NOW() - INTERVAL '30 days'
GROUP BY geography
ORDER BY churn_rate DESC;

COMMENT ON VIEW v_geography_churn IS 'Geography-wise churn analysis for last 30 days';

-- View 4: Time Series for Trend Analysis
CREATE OR REPLACE VIEW v_churn_trends AS
SELECT 
    DATE(predicted_at) as date,
    DATE_TRUNC('hour', predicted_at) as hour,
    COUNT(*) as predictions,
    SUM(prediction) as churns,
    ROUND((SUM(prediction)::float / COUNT(*)::float * 100)::numeric, 2) as churn_rate,
    ROUND(AVG(risk_score)::numeric, 3) as avg_risk
FROM churn_predictions
WHERE predicted_at >= NOW() - INTERVAL '90 days'
GROUP BY DATE(predicted_at), DATE_TRUNC('hour', predicted_at)
ORDER BY date DESC, hour DESC;

COMMENT ON VIEW v_churn_trends IS 'Hourly churn trends for last 90 days';

-- View 5: Model Performance Metrics
CREATE OR REPLACE VIEW v_model_performance AS
SELECT 
    model_version,
    DATE(predicted_at) as date,
    COUNT(*) as total_predictions,
    ROUND(AVG(probability)::numeric, 3) as avg_confidence,
    SUM(CASE WHEN probability >= 0.8 THEN 1 ELSE 0 END) as high_confidence_count,
    SUM(CASE WHEN probability < 0.6 THEN 1 ELSE 0 END) as low_confidence_count
FROM churn_predictions
WHERE predicted_at >= NOW() - INTERVAL '30 days'
GROUP BY model_version, DATE(predicted_at)
ORDER BY date DESC, model_version;

COMMENT ON VIEW v_model_performance IS 'Model confidence metrics for last 30 days';

-- ==========================================
-- DATA RETENTION POLICY (Optional)
-- ==========================================

-- Function to archive old predictions
CREATE OR REPLACE FUNCTION archive_old_predictions()
RETURNS void AS $$
BEGIN
    -- Archive predictions older than 90 days to separate table
    INSERT INTO churn_predictions_archive
    SELECT * FROM churn_predictions
    WHERE predicted_at < NOW() - INTERVAL '90 days';
    
    -- Delete archived predictions
    DELETE FROM churn_predictions
    WHERE predicted_at < NOW() - INTERVAL '90 days';
    
    RAISE NOTICE 'Archived predictions older than 90 days';
END;
$$ LANGUAGE plpgsql;

-- Create archive table (same structure as churn_predictions)
CREATE TABLE IF NOT EXISTS churn_predictions_archive (
    LIKE churn_predictions INCLUDING ALL
);

COMMENT ON FUNCTION archive_old_predictions() IS 'Archive predictions older than 90 days';

-- ==========================================
-- GRANT PERMISSIONS (Update with your user)
-- ==========================================

-- Grant read-only access for QuickSight
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO quicksight_user;
-- GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO quicksight_user;

-- Grant read-write for Kafka services
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kafka_service_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kafka_service_user;

-- ==========================================
-- VERIFICATION QUERIES
-- ==========================================

-- Check table creation
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    AND table_name LIKE 'churn%'
ORDER BY table_name;

-- Check indexes
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public' 
    AND tablename LIKE 'churn%'
ORDER BY tablename, indexname;

-- Check views
SELECT 
    table_name as view_name
FROM information_schema.views
WHERE table_schema = 'public' 
    AND table_name LIKE 'v_%'
ORDER BY table_name;

-- ==========================================
-- SAMPLE QUERIES FOR TESTING
-- ==========================================

-- Test individual predictions
-- SELECT * FROM churn_predictions ORDER BY predicted_at DESC LIMIT 10;

-- Test hourly metrics
-- SELECT * FROM churn_metrics_hourly ORDER BY hour_timestamp DESC LIMIT 24;

-- Test high-risk customers
-- SELECT * FROM high_risk_customers ORDER BY detected_at DESC LIMIT 20;

-- Test real-time dashboard view
-- SELECT * FROM v_realtime_dashboard;

-- ==========================================
-- END OF SCHEMA
-- ==========================================


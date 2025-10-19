# 🚀 Kafka Integration Quick Start Guide

**Complete Real-time Churn Prediction System**

---

## 📋 **Prerequisites**

1. ✅ Docker and Docker Compose installed
2. ✅ AWS credentials configured (for S3 and RDS)
3. ✅ RDS PostgreSQL database running
4. ✅ `.env` file with RDS credentials

### **Required Environment Variables**

Create or update `.env` file:

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_DEFAULT_REGION=ap-south-1

# RDS Database
RDS_HOST=your-rds-endpoint.rds.amazonaws.com
RDS_PORT=5432
RDS_DB_NAME=postgres
RDS_USERNAME=postgres
RDS_PASSWORD=your_password
```

---

## 🗄️ **Step 1: Create RDS Tables**

```bash
# This creates 4 analytics tables + 5 QuickSight views
make setup-analytics-tables
```

**What this creates:**
- `churn_predictions` - Individual predictions
- `churn_metrics_hourly` - Hourly aggregations
- `churn_metrics_daily` - Daily aggregations
- `high_risk_customers` - Real-time alerts

---

## 🔨 **Step 2: Build Kafka Services**

```bash
# Build Docker images for producer, consumer, analytics
make kafka-build
```

This builds 3 services:
1. **Producer** - Streams customer events
2. **Consumer** - Real-time inference (1000 samples / 30 sec)
3. **Analytics** - Aggregates metrics to RDS

---

## 🚀 **Step 3: Start Kafka Stack**

```bash
# Start Kafka broker + services
make kafka-up
```

**What starts:**
- Kafka broker (KRaft mode, port 9092)
- Kafka UI (http://localhost:8090)
- Producer service (streaming customer events)
- Consumer service (real-time inference)
- Analytics service (RDS aggregation)

---

## 📊 **Step 4: Monitor with Kafka UI**

```bash
# Open Kafka UI in browser
make kafka-ui
```

Or visit manually: **http://localhost:8090**

**What you'll see:**
- `customer-events` topic - Raw customer data
- `churn-predictions` topic - Prediction results
- Consumer groups and lag
- Message throughput

---

## 📋 **Step 5: View Logs**

```bash
# Follow all Kafka logs
make kafka-logs

# Or check specific service:
docker logs -f kafka-producer
docker logs -f kafka-consumer
docker logs -f kafka-analytics
```

---

## 📈 **Step 6: Verify RDS Data**

Connect to RDS and check tables:

```bash
# Using psql
psql "host=${RDS_HOST} port=${RDS_PORT} dbname=${RDS_DB_NAME} user=${RDS_USERNAME} sslmode=require"
```

**Sample Queries:**

```sql
-- Check recent predictions
SELECT * FROM churn_predictions ORDER BY predicted_at DESC LIMIT 10;

-- Check hourly metrics
SELECT * FROM churn_metrics_hourly ORDER BY hour_timestamp DESC LIMIT 24;

-- Check high-risk customers
SELECT * FROM high_risk_customers ORDER BY detected_at DESC LIMIT 20;

-- Real-time dashboard view (last 24 hours)
SELECT * FROM v_realtime_dashboard;
```

---

## 🛑 **Management Commands**

### **Check Status**
```bash
make kafka-status
```

### **Restart Services**
```bash
make kafka-restart
```

### **Stop Services**
```bash
make kafka-down
```

### **Clean Everything (including volumes)**
```bash
make kafka-clean
```

---

## 🎯 **Data Flow Overview**

```
┌────────────────┐
│ ChurnModelling │
│     CSV        │ (10,000 customers)
└───────┬────────┘
        │
        ▼
┌────────────────┐
│   Producer     │ Streams events to Kafka
│   Service      │ Rate: 1-10 events/sec
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Kafka Broker   │ customer-events topic
│  (KRaft mode)  │ Port: 9092
└───────┬────────┘
        │
        ▼
┌────────────────┐
│   Consumer     │ Micro-batch: 1000 samples / 30 sec
│   Service      │ Loads sklearn model from S3
│   [INFERENCE]  │ Shared ModelInference class
└───────┬────────┘
        │
   ┌────┴─────┐
   │          │
   ▼          ▼
┌──────┐  ┌────────┐
│ RDS  │  │ Kafka  │ churn-predictions topic
└──┬───┘  └────┬───┘
   │          │
   │          ▼
   │     ┌─────────────┐
   │     │ Analytics   │ Consumes predictions
   │     │  Service    │ Aggregates hourly/daily
   │     └──────┬──────┘
   │            │
   └────────────┘
        │
        ▼
   ┌─────────┐
   │   RDS   │ 4 analytics tables
   │         │ Ready for QuickSight
   └─────────┘
```

---

## 🔍 **Troubleshooting**

### **Kafka broker not starting**
```bash
# Check logs
docker logs kafka-broker

# Clean and restart
make kafka-clean
make kafka-up
```

### **Consumer not processing messages**
```bash
# Check consumer logs
docker logs kafka-consumer -f

# Verify model exists in S3
aws s3 ls s3://your-bucket/artifacts/train_artifacts/
```

### **No predictions in RDS**
```bash
# Check RDS connection
docker logs kafka-consumer | grep "RDS"

# Verify tables exist
psql -h ${RDS_HOST} -U ${RDS_USERNAME} -d ${RDS_DB_NAME} -c "\dt"
```

### **Analytics service not aggregating**
```bash
# Check analytics logs
docker logs kafka-analytics -f

# Manually trigger aggregation (connect to RDS and run)
SELECT * FROM churn_predictions WHERE predicted_at >= NOW() - INTERVAL '1 hour';
```

---

## 📊 **Performance Metrics**

### **Expected Throughput**
- **Producer**: 1-10 events/sec (configurable)
- **Consumer**: 1000 predictions per batch (~30-40 seconds)
- **Latency**: 30-60 seconds (micro-batch)

### **Resource Usage**
- **Kafka Broker**: ~500MB RAM, 1 CPU
- **Consumer**: ~1GB RAM, 1 CPU (model loading)
- **Producer**: ~200MB RAM, 0.5 CPU
- **Analytics**: ~200MB RAM, 0.5 CPU

---

## 🎉 **Next Steps**

1. **QuickSight Dashboard**:
   - Connect QuickSight to RDS
   - Use pre-built views: `v_realtime_dashboard`, `v_top_risk_customers`
   - Create time-series visualizations

2. **CI/CD Integration**:
   - Add GitHub Actions workflow
   - Automated testing for Kafka services
   - Docker image builds

3. **Production Deployment**:
   - Deploy to Kubernetes or VM
   - Set up monitoring (Prometheus + Grafana)
   - Configure alerting for high-risk customers

4. **Feature Enhancements**:
   - Add FastAPI for real-time inference API
   - Implement A/B testing for models
   - Add model drift detection

---

## 📚 **Documentation**

- **Full Plan**: See original implementation plan above
- **Architecture**: `ARCHITECTURE_TRANSITION.md`
- **Changelog**: `changelog.md` (Kafka Integration section)
- **AWS Cleanup**: `AWS_CLEANUP_SUMMARY.md`

---

## 🆘 **Support**

If you encounter issues:
1. Check logs: `make kafka-logs`
2. Verify configuration: `config.yaml`
3. Check RDS connectivity: `psql` command
4. Review Docker status: `make kafka-status`

---

**🎉 Happy Streaming! 🚀**


# Docker Logs Monitoring Guide

Complete reference for monitoring all services in the ML pipeline.

---

## 🚀 Quick Start

```bash
# List all running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Check container status with stats
docker stats --no-stream
```

---

## 📊 MLflow Tracking Server

### Basic Logs
```bash
# Follow logs in real-time
docker logs mlflow-tracking -f

# Last 100 lines
docker logs mlflow-tracking --tail 100

# Last 5 minutes
docker logs mlflow-tracking --since 5m

# Search for errors
docker logs mlflow-tracking 2>&1 | grep -i error
```

### What to Look For
- ✅ "Server started on port 5001"
- ✅ "Backend store: sqlite:///mlflow/mlflow.db"
- ✅ "Artifact root: s3://..."
- ⚠️ S3 connection issues
- ❌ Database errors

### Health Check
```bash
# Check if MLflow is healthy
docker inspect mlflow-tracking --format='{{.State.Health.Status}}'

# Test endpoint
curl http://localhost:5001/health
```

---

## ☁️ Airflow Services

### Webserver
```bash
# Follow logs
docker logs airflow-webserver -f

# Check for errors
docker logs airflow-webserver --tail 200 | grep -E "ERROR|CRITICAL"

# Check DAG loading
docker logs airflow-webserver | grep "DAG"
```

**What to Look For:**
- ✅ "Listening at: http://0.0.0.0:8080"
- ✅ "DAG loaded successfully"
- ⚠️ DAG import errors
- ❌ Port binding issues

### Scheduler
```bash
# Follow logs (most important for execution)
docker logs airflow-scheduler -f

# Check recent task executions
docker logs airflow-scheduler --tail 500 | grep "Task"

# Check for DAG processing
docker logs airflow-scheduler | grep "Processing\|Running"
```

**What to Look For:**
- ✅ "Starting the scheduler"
- ✅ "Task instance <task> succeeded"
- ⚠️ "Task failed"
- ❌ DAG parsing errors

### Worker (Celery)
```bash
# Follow worker logs
docker logs airflow-worker -f

# Check task execution
docker logs airflow-worker --tail 300 | grep "Executing"

# Check for worker readiness
docker logs airflow-worker | grep "ready"
```

**What to Look For:**
- ✅ "celery@worker ready"
- ✅ "Task executed successfully"
- ⚠️ Task failures
- ❌ Memory issues

### Flower (Celery Monitoring)
```bash
# Check Flower UI logs
docker logs airflow-flower --tail 50

# Access Flower UI
open http://localhost:5555
```

### Database & Redis
```bash
# PostgreSQL logs
docker logs airflow-postgres --tail 100

# Redis logs
docker logs airflow-redis --tail 50
```

---

## 🔄 Kafka Services

### Kafka Broker
```bash
# Follow broker logs
docker logs kafka-broker -f

# Check startup
docker logs kafka-broker --tail 200 | grep "started"

# Check for errors
docker logs kafka-broker 2>&1 | grep -i "error\|exception"

# List topics
docker exec kafka-broker kafka-topics --list --bootstrap-server localhost:9092
```

**What to Look For:**
- ✅ "Kafka Server started"
- ✅ "Kafka version: ..."
- ⚠️ Topic creation issues
- ❌ Port conflicts

### Producer Service (Event Streaming)
```bash
# Follow producer logs in real-time
docker logs kafka-producer -f

# Check recent activity (last 100 lines)
docker logs kafka-producer --tail 100

# Check production rate
docker logs kafka-producer --tail 50 | grep "Produced\|Streaming"

# Check for connection issues
docker logs kafka-producer | grep -i "error\|failed"

# Check data loading
docker logs kafka-producer | grep "Loaded.*records"
```

**What to Look For:**
- ✅ `Loaded 10000 customer records`
- ✅ `Streaming 10 events/sec`
- ✅ `Produced message to customer-events`
- ✅ `Total produced: X messages`
- ⚠️ Kafka connection errors
- ❌ Data loading failures

**Key Metrics:**
```bash
# Check how many events produced
docker logs kafka-producer 2>&1 | grep -c "Produced"

# Check production rate
docker logs kafka-producer --since 1m | grep "rate\|/sec"
```

### Consumer Service (ML Inference Engine)
```bash
# Follow consumer logs in real-time (MOST IMPORTANT)
docker logs kafka-consumer -f

# Last 200 lines (see recent predictions)
docker logs kafka-consumer --tail 200

# Check inference activity
docker logs kafka-consumer --tail 100 | grep -E "prediction|inference|batch"

# Check model loading
docker logs kafka-consumer | grep -i "model\|mlflow"

# Check RDS writes
docker logs kafka-consumer | grep -i "rds\|postgres\|saved"

# Check errors
docker logs kafka-consumer 2>&1 | grep -i "error\|exception\|failed"
```

**What to Look For:**
- ✅ `Loaded model from MLflow: runs:/...`
- ✅ `Processing batch of 1000 samples`
- ✅ `Generated 1000 predictions`
- ✅ `Predictions saved to RDS`
- ✅ `Published 1000 predictions to Kafka`
- ✅ `Inference latency: X ms`
- ⚠️ Model loading issues
- ⚠️ RDS connection problems
- ❌ Kafka consumer lag

**Key Metrics:**
```bash
# Count predictions made
docker logs kafka-consumer 2>&1 | grep -c "predictions"

# Check batch sizes
docker logs kafka-consumer | grep "batch.*size"

# Monitor performance
docker stats kafka-consumer --no-stream
```

### Analytics Service (RDS Aggregation)
```bash
# Follow analytics logs
docker logs kafka-analytics -f

# Check aggregation activity
docker logs kafka-analytics --tail 100 | grep -E "aggregat|insert|hourly|daily"

# Check RDS operations
docker logs kafka-analytics | grep -i "rds\|postgres"

# Check for errors
docker logs kafka-analytics 2>&1 | grep -i "error"
```

**What to Look For:**
- ✅ `Connected to RDS`
- ✅ `Consuming from churn-predictions topic`
- ✅ `Aggregating hourly metrics`
- ✅ `Inserted X records into churn_metrics_hourly`
- ✅ `High-risk customers detected: X`
- ⚠️ Database connection issues
- ❌ Aggregation failures

**Key Metrics:**
```bash
# Count aggregations
docker logs kafka-analytics 2>&1 | grep -c "aggregat"

# Check high-risk alerts
docker logs kafka-analytics | grep "high-risk"
```

### Kafka UI (Web Interface)
```bash
# Check Kafka UI logs
docker logs kafka-ui --tail 50

# Access Kafka UI
open http://localhost:8090
```

---

## 🐳 ML Pipeline Services

### Data Pipeline
```bash
# View data pipeline logs
docker logs data-pipeline --tail 200

# Check if it completed
docker logs data-pipeline | grep -E "completed|success|error"
```

### Model Pipeline
```bash
# View training logs
docker logs model-pipeline --tail 300

# Check training progress
docker logs model-pipeline | grep -E "epoch|accuracy|loss|training"

# Check MLflow logging
docker logs model-pipeline | grep "mlflow"
```

### Inference Pipeline
```bash
# View inference logs
docker logs inference-pipeline --tail 200
```

---

## 🔍 Advanced Monitoring

### Monitor Multiple Services
```bash
# Follow logs from multiple containers
docker-compose -f docker-compose.kafka.yml logs -f producer consumer analytics

# Check all Kafka services
docker-compose -f docker-compose.kafka.yml logs --tail 100

# Check all Airflow services
docker-compose -f docker-compose.airflow.yml logs --tail 100
```

### Performance Monitoring
```bash
# Real-time stats for all containers
docker stats

# Stats for Kafka services only
docker stats kafka-producer kafka-consumer kafka-analytics --no-stream

# Memory usage
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Disk usage by container
docker system df -v
```

### Log Analysis
```bash
# Count errors in consumer
docker logs kafka-consumer 2>&1 | grep -c -i error

# Find slowest operations
docker logs kafka-consumer | grep "latency\|duration" | sort -n

# Check last restart time
docker inspect kafka-consumer --format='{{.State.StartedAt}}'

# View container resource limits
docker inspect kafka-consumer --format='{{.HostConfig.Memory}}'
```

### Export Logs
```bash
# Save logs to file
docker logs kafka-consumer > consumer_logs_$(date +%Y%m%d_%H%M%S).log

# Save last 1000 lines
docker logs kafka-consumer --tail 1000 > consumer_recent.log

# Save with timestamps
docker logs kafka-consumer --timestamps > consumer_timestamped.log

# Save logs from specific time range
docker logs kafka-consumer --since "2025-10-18T10:00:00" --until "2025-10-18T11:00:00" > consumer_hour.log
```

---

## 🎯 Common Use Cases

### 1. Verify Real-Time Inference is Working
```bash
# 1. Check producer is sending events
docker logs kafka-producer --tail 20 | grep "Produced"

# 2. Check consumer is processing
docker logs kafka-consumer --tail 50 | grep "batch\|prediction"

# 3. Check analytics is aggregating
docker logs kafka-analytics --tail 30 | grep "aggregat\|insert"

# 4. Check Kafka UI
open http://localhost:8090
```

### 2. Debug Model Loading Issues
```bash
# Check MLflow server
docker logs mlflow-tracking | grep -i "error\|s3"

# Check consumer model loading
docker logs kafka-consumer | grep -i "model\|mlflow\|artifact"

# Verify S3 credentials
docker exec kafka-consumer env | grep AWS
```

### 3. Monitor Training Progress
```bash
# Follow training in real-time
docker logs model-pipeline -f

# Check if training completed
docker logs model-pipeline | grep -E "completed|saved|registered"

# View MLflow UI
open http://localhost:5001
```

### 4. Check DAG Execution in Airflow
```bash
# Check scheduler is processing DAGs
docker logs airflow-scheduler --tail 100 | grep "DAG\|Task"

# Check specific DAG
docker logs airflow-scheduler | grep "data_pipeline"

# Access Airflow UI
open http://localhost:8080
```

### 5. Troubleshoot RDS Connection
```bash
# Check consumer RDS connection
docker logs kafka-consumer | grep -i "rds\|postgres\|database"

# Check analytics RDS connection
docker logs kafka-analytics | grep -i "rds\|postgres"

# Check environment variables
docker exec kafka-consumer env | grep RDS
```

---

## 🛠️ Makefile Shortcuts

```bash
# Docker services status
make docker-status

# Airflow status
make airflow-status

# Kafka status  
make kafka-status

# View Kafka logs
make kafka-logs

# View all logs
docker-compose -f docker-compose.yml logs -f
docker-compose -f docker-compose.kafka.yml logs -f
docker-compose -f docker-compose.airflow.yml logs -f
```

---

## 🚨 Troubleshooting Checklist

### Service Won't Start
```bash
# 1. Check container status
docker ps -a | grep <service-name>

# 2. View startup logs
docker logs <container-name>

# 3. Check port conflicts
docker port <container-name>

# 4. Inspect container
docker inspect <container-name>

# 5. Try restarting
docker restart <container-name>
```

### Service Crashes Repeatedly
```bash
# 1. View full logs
docker logs <container-name> --tail 500

# 2. Check exit code
docker inspect <container-name> --format='{{.State.ExitCode}}'

# 3. Check resource usage
docker stats <container-name> --no-stream

# 4. Check health status
docker inspect <container-name> --format='{{.State.Health}}'
```

### High Memory/CPU Usage
```bash
# Monitor in real-time
docker stats <container-name>

# Check logs for memory issues
docker logs <container-name> | grep -i "memory\|oom"

# Restart container
docker restart <container-name>
```

---

## 📌 Quick Reference

| Service | Container Name | Default Port | Log Command |
|---------|---------------|--------------|-------------|
| MLflow | `mlflow-tracking` | 5001 | `docker logs mlflow-tracking -f` |
| Airflow Web | `airflow-webserver` | 8080 | `docker logs airflow-webserver -f` |
| Airflow Scheduler | `airflow-scheduler` | - | `docker logs airflow-scheduler -f` |
| Flower | `airflow-flower` | 5555 | `docker logs airflow-flower -f` |
| Kafka Broker | `kafka-broker` | 9092 | `docker logs kafka-broker -f` |
| Kafka UI | `kafka-ui` | 8090 | `docker logs kafka-ui -f` |
| **Producer** | `kafka-producer` | - | `docker logs kafka-producer -f` |
| **Consumer** | `kafka-consumer` | - | `docker logs kafka-consumer -f` |
| **Analytics** | `kafka-analytics` | - | `docker logs kafka-analytics -f` |
| Postgres (Airflow) | `airflow-postgres` | 5432 | `docker logs airflow-postgres -f` |
| Redis | `airflow-redis` | 6379 | `docker logs airflow-redis -f` |

---

## 🎓 Best Practices

1. **Use `-f` for Real-Time Monitoring**: Follow logs during active development
2. **Use `--tail N` for Quick Checks**: View recent activity without overwhelming output
3. **Grep for Specific Events**: Filter logs for errors, predictions, or specific operations
4. **Save Important Logs**: Export logs when debugging complex issues
5. **Monitor Multiple Services**: Use docker-compose logs to see the full picture
6. **Check Stats Regularly**: Monitor resource usage to prevent issues
7. **Use Timestamps**: Add `--timestamps` for time-based analysis

---

## 📚 Additional Resources

- [Docker Logs Documentation](https://docs.docker.com/engine/reference/commandline/logs/)
- [Docker Stats Documentation](https://docs.docker.com/engine/reference/commandline/stats/)
- [Kafka UI](http://localhost:8090) - View topics, messages, consumer groups
- [Airflow UI](http://localhost:8080) - View DAG runs, logs, tasks
- [MLflow UI](http://localhost:5001) - View experiments, runs, models
- [Flower UI](http://localhost:5555) - View Celery workers, tasks

---

**Created**: 2025-10-18  
**Last Updated**: 2025-10-18  
**Version**: 1.0


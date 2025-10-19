# 🚀 ML Pipeline Startup Guide

Complete guide for starting the production ML pipeline with MLflow, Airflow, and AWS RDS.

---

## 📋 Prerequisites

1. ✅ Docker Desktop running
2. ✅ AWS credentials configured
3. ✅ RDS instance created and accessible
4. ✅ `.env` file with RDS credentials

---

## 🎯 Quick Start (One Command)

```bash
./run_local.sh
```

This will automatically:
1. Build all Docker images (MLflow + ML pipelines)
2. Start MLflow tracking server (connected to RDS)
3. Start ML pipeline containers
4. Build custom Airflow image
5. Initialize Airflow database on RDS
6. Start Airflow services
7. Verify all connections

**Time:** ~3-5 minutes for first run

---

## 🔧 Manual Step-by-Step (For Debugging)

### Step 1: Build Docker Images
```bash
make docker-build
```
- Builds: `churn-pipeline/data`, `model`, `inference`, `mlflow`
- Time: ~15 minutes (first time), ~30 seconds (cached)

### Step 2: Start MLflow & ML Pipelines
```bash
make docker-up
```
- Starts: MLflow tracking server + 3 pipeline containers
- MLflow connects to RDS PostgreSQL for metadata

### Step 3: Verify MLflow RDS Connection
```bash
sleep 30
docker logs mlflow-tracking | grep postgres
```
Expected output: `Backend Store URI: postgresql://zuucrew@...rds.amazonaws.com:5432/mlflow`

### Step 4: Build Airflow Image
```bash
make airflow-build
```
- Builds custom Airflow image with Amazon & Docker providers
- Time: ~40 seconds

### Step 5: Initialize Airflow Database
```bash
make airflow-init
```
- Creates Airflow schema in RDS
- Creates admin user (admin/admin)
- Time: ~90 seconds

### Step 6: Start Airflow Services
```bash
make airflow-up
```
- Starts: webserver, scheduler, worker, flower, redis
- All connect to RDS for metadata

### Step 7: Verify Airflow Connection
```bash
docker exec airflow-webserver airflow db check
```
Expected output: `Connection successful.`

---

## 🌐 Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **MLflow UI** | http://localhost:5001 | None |
| **Airflow UI** | http://localhost:8080 | admin/admin |
| **Flower UI** | http://localhost:5555 | None |

---

## 📊 Automated DAGs

Once Airflow is running, these DAGs will execute automatically:

| DAG | Schedule | Purpose |
|-----|----------|---------|
| `data_pipeline_every_10m` | Every 10 minutes | Data preprocessing |
| `train_pipeline_hourly` | Every hour | Model training |
| `inference_pipeline_every_2m` | Every 2 minutes | Batch predictions |

**Note:** DAGs start in "paused" state. Unpause them in Airflow UI to activate.

---

## 🛑 Stop All Services

```bash
# Stop Airflow only
make airflow-down

# Stop MLflow & pipelines only
make docker-down

# Stop everything
make airflow-down && make docker-down
```

---

## 🔄 Restart Services

```bash
# Full restart
make docker-down && make airflow-down
./run_local.sh

# Or step-by-step
make docker-down
make docker-up
make airflow-down
make airflow-up
```

---

## 🧹 Clean Restart (Clear All History)

```bash
# Reset Airflow completely (removes all DAG runs)
make airflow-reset

# Then reinitialize
make airflow-init
make airflow-up
```

**Warning:** This deletes all Airflow DAG run history from RDS!

---

## 🔍 Troubleshooting

### MLflow not connecting to RDS?
```bash
# Check MLflow logs
docker logs mlflow-tracking

# Verify RDS connection string
docker exec mlflow-tracking env | grep MLFLOW_BACKEND

# Test RDS connection
./test_rds_connection.sh
```

### Airflow not starting?
```bash
# Check logs
docker logs airflow-scheduler
docker logs airflow-webserver

# Verify RDS connection
docker exec airflow-webserver airflow db check

# Rebuild Airflow image
make airflow-build
```

### DAGs not showing up?
```bash
# List DAGs
docker exec airflow-webserver airflow dags list

# Check for import errors
docker exec airflow-webserver airflow dags list-import-errors

# Restart scheduler
docker restart airflow-scheduler
```

### Port conflicts?
```bash
# Check what's using the ports
lsof -i :5001  # MLflow
lsof -i :8080  # Airflow
lsof -i :5555  # Flower

# Stop conflicting processes or change ports in docker-compose files
```

---

## 📦 What's Running Where?

### Local Docker Containers
- `mlflow-tracking` - MLflow tracking server
- `data-pipeline` - Data preprocessing container
- `model-pipeline` - Model training container
- `inference-pipeline` - Batch inference container
- `airflow-webserver` - Airflow web UI
- `airflow-scheduler` - Airflow task scheduler
- `airflow-worker` - Celery worker for task execution
- `airflow-flower` - Celery monitoring UI
- `airflow-redis` - Message broker for Celery

### AWS RDS (Remote)
- Database: `mlflow` - MLflow experiment metadata
- Database: `airflow` - Airflow DAG runs and task history

### AWS S3 (Remote)
- Bucket: `zuucrew-mlflow-artifacts-prod`
  - `artifacts/data_artifacts/` - Processed datasets
  - `artifacts/train_artifacts/` - Trained models
  - `artifacts/inference_artifacts/` - Predictions
  - `artifacts/mlflow-artifacts/` - MLflow artifacts (plots, models, etc.)

---

## 🎯 Complete Startup Order (Reference)

```bash
# 1. Build Docker images
make docker-build

# 2. Start MLflow (connects to RDS for metadata)
make docker-up

# 3. Wait for MLflow to initialize
sleep 30

# 4. Verify MLflow → RDS connection
docker logs mlflow-tracking | grep postgres

# 5. Build custom Airflow image
make airflow-build

# 6. Initialize Airflow schema in RDS
make airflow-init

# 7. Start Airflow services (connect to RDS)
make airflow-up

# 8. Wait for Airflow to initialize
sleep 15

# 9. Verify Airflow → RDS connection
docker exec airflow-webserver airflow db check

# ✅ Done!
```

---

## 💡 Pro Tips

1. **First-time setup:** Run `./run_local.sh` and let it complete. Takes ~5 minutes.

2. **Daily workflow:** If containers are already running, just restart what you need:
   ```bash
   make docker-down && make docker-up  # Restart pipelines
   ```

3. **Debugging:** Check logs immediately if something fails:
   ```bash
   docker logs mlflow-tracking
   docker logs airflow-scheduler
   ```

4. **Save costs:** Stop services when not in use:
   ```bash
   make airflow-down && make docker-down
   ```
   RDS will keep running but only costs ~$11/month.

5. **Fresh start:** If things get weird:
   ```bash
   make airflow-reset
   make docker-down
   ./run_local.sh
   ```

---

## 📚 Additional Resources

- **RDS Setup:** See `RDS_QUICK_START.md`
- **RDS Migration:** See `docs/RDS_MIGRATION_GUIDE.md`
- **Docker Setup:** See `docs/docker_setup.md`
- **Configuration:** See `docs/configuration_guide.md`

---

**Your production-ready ML pipeline is ready! 🚀**


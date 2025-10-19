SHELL := /usr/bin/env bash
.ONESHELL:

.PHONY: all clean install setup-dirs train-pipeline data-pipeline inference-pipeline help test

# Default Python interpreter
PYTHON = python
VENV = .venv/bin/activate
MLFLOW_PORT ?= 5001

# Default target
all: help

# Help target
help:
	@echo "🚀 Production ML Pipeline System"
	@echo "================================="
	@echo ""
	@echo "🎯 END-TO-END WORKFLOWS (Recommended):"
	@echo "  ./run_local.sh           - 🚀 Deploy LOCAL setup"
	@echo "  ./run_ecs.sh             - ☁️  Deploy ECS setup"
	@echo "  ./stop_ecs.sh            - ⏸️  Stop ECS services (pause, keep resources)"
	@echo "  ./restart_ecs.sh         - 🔄 Restart ECS services"
	@echo "  ./test_rds_connection.sh - 🔍 Test RDS connectivity"
	@echo ""
	@echo "🗑️  CLEANUP:"
	@echo "  ./cleanup_docker.sh      - 🧹 Clean Local Docker + AWS ECS (interactive choice)"
	@echo "  make docker-nuke         - ☢️  NUCLEAR: Remove ALL Docker images/containers/volumes"
	@echo "  make rds-clear-airflow-cache - 🗄️  Flush RDS Airflow metadata"
	@echo "  make clean               - 🧹 Clean local cache only"
	@echo ""
	@echo "📦 Setup Commands:"
	@echo "  make install             - Install project dependencies and set up environment"
	@echo "  make setup-dirs          - Create necessary directories for pipelines"
	@echo "  make clean               - Clean up local cache only (safe)"
	@echo "  make clean-local-artifacts - Remove legacy local artifact folders"
	@echo ""
	@echo "🐳 Docker Commands (Embedded PySpark + Pandas/Scikit-learn Priority):"
	@echo "  make docker-build        - Build embedded PySpark containers"
	@echo "  make docker-up           - Start all 4 services (MLflow + 3 pipelines)"
	@echo "  make docker-down         - Stop all services"
	@echo "  make docker-data-pipeline    - Run data pipeline (pandas/scikit-learn default)"
	@echo "  make docker-model-pipeline   - Run model pipeline (pandas/scikit-learn default)"
	@echo "  make docker-inference-pipeline - Run inference pipeline (pandas default)"
	@echo "  make docker-run-all      - Run all pipelines"
	@echo "  make docker-status       - Show service status"
	@echo "  make docker-logs         - View service logs"
	@echo "  make docker-clean        - Clean up Docker resources (safe)"
	@echo "  make docker-cleanup-preview - Preview what docker-clean-all would remove"
	@echo "  make docker-clean-all    - NUCLEAR cleanup (remove ALL project Docker resources + ECS images)"
	@echo "  make docker-image-sizes  - Show Docker image sizes"
	@echo ""
	@echo "🔄 Kafka Streaming (Real-time Inference):"
	@echo "  make kafka-build         - Build Kafka services"
	@echo "  make kafka-up            - Start Kafka stack (broker, UI, services)"
	@echo "  make kafka-down          - Stop Kafka stack"
	@echo "  make kafka-logs          - View Kafka logs"
	@echo "  make kafka-status        - Show Kafka status"
	@echo "  make kafka-clean         - Clean Kafka (including volumes)"
	@echo "  make kafka-restart       - Restart Kafka stack"
	@echo "  make kafka-ui            - Open Kafka UI in browser"
	@echo "  make setup-analytics-tables - Create RDS analytics tables"
	@echo ""
	@echo "⏸️  Pause/Resume (Kafka + Airflow DAGs):"
	@echo "  make pause-streaming     - ⏸️  Pause Kafka (producer/consumer) + DAGs"
	@echo "  make resume-streaming    - ▶️  Resume Kafka (producer/consumer) + DAGs"
	@echo ""
	@echo "🔄 ML Pipeline Commands (Local - Pandas/Scikit-learn):"
	@echo "  make data-pipeline       - Run data preprocessing (pandas + sklearn)"
	@echo "  make train-pipeline      - Run model training (sklearn)"
	@echo "  make inference-pipeline  - Run batch inference (pandas + sklearn)"
	@echo "  make run-all             - Run all three pipelines in sequence"
	@echo ""
	@echo "🐳 Environment Control:"
	@echo "  CONTAINERIZED=true make train-pipeline    - Use Docker MLflow URL"
	@echo "  CONTAINERIZED=false make train-pipeline   - Use local MLflow URL (default)"
	@echo ""
	@echo "📊 MLflow Commands:"
	@echo "  make mlflow-ui           - Launch MLflow UI (port $(MLFLOW_PORT))"
	@echo "  make stop-mlflow         - Stop MLflow servers"
	@echo ""
	@echo "🔄 Airflow Automation Commands:"
	@echo "  make airflow-build       - Build custom Airflow image with providers"
	@echo "  make airflow-init        - 🗑️  Initialize Airflow (ALWAYS clears DAG history)"
	@echo "  make airflow-up          - Start Airflow services (webserver, scheduler, worker)"
	@echo "  make airflow-down        - Stop Airflow services"
	@echo "  make airflow-reset       - 🔥 Reset only (stop services + delete volumes)"
	@echo "  make airflow-logs        - View Airflow logs"
	@echo "  make automation-up       - Complete setup (ML + Airflow)"
	@echo "  make automation-down     - Stop everything (ML + Airflow)"
	@echo "  Airflow UI: http://localhost:8080 (admin/admin)"
	@echo ""
	@echo "🌐 S3 Commands:"
	@echo "  make s3-upload-data              - Upload data/raw & data/processed to S3 (one-time)"
	@echo "  make s3-list PREFIX=<prefix>     - List S3 keys with prefix"
	@echo "  make s3-clean                    - Clean project S3 artifacts (safe)"
	@echo "  make s3-delete-prefix PREFIX=<>  - Delete S3 keys with prefix (careful!)"
	@echo "  make s3-smoke                    - Test S3 connectivity"
	@echo ""
	@echo "🗄️  RDS Database Visualization:"
	@echo "  ./test_rds_connection.sh         - Test RDS connection"
	@echo "  make rds-show-all                - Show all RDS databases (MLflow & Airflow)"
	@echo "  make rds-show-mlflow             - Show MLflow database schema"
	@echo "  make rds-show-airflow            - Show Airflow database schema"
	@echo "  make rds-clear-airflow-cache     - 🗑️  Clear RDS Airflow DAG cache/history"
	@echo "  make rds-adminer                 - Launch Adminer web UI (port 8081)"
	@echo "  make rds-psql-mlflow             - Connect to MLflow DB with psql"
	@echo "  make rds-psql-airflow            - Connect to Airflow DB with psql"
	@echo ""
	@echo "  💡 RDS credentials: Add to .env file (see backup/env.example)"
	@echo ""
	@echo "🧪 Development Commands:"
	@echo "  make status              - Show project and S3 status"
	@echo "  make dev-install         - Install with development dependencies"
	@echo ""
	@echo "💡 Quick Start (Docker):"
	@echo "  1. Configure AWS credentials (~/.aws/credentials)"
	@echo "  2. cp .env.example .env && edit .env"
	@echo "  3. make docker-build"
	@echo "  4. make docker-run-all"
	@echo "  5. View MLflow UI: http://localhost:5001"
	@echo ""
	@echo "💡 Quick Start (Local - Pandas/Scikit-learn):"
	@echo "  1. make install"
	@echo "  2. Configure AWS settings in config.yaml"
	@echo "  3. make data-pipeline     # Data preprocessing"
	@echo "  4. make train-pipeline    # Model training"
	@echo "  5. make inference-pipeline # Batch inference"
	@echo ""
	@echo "🗑️ Cleanup Commands:"
	@echo "  make docker-clean        - Clean up Docker resources (safe)"
	@echo "  make docker-clean-all    - Remove ALL project Docker images/containers/ECS images (nuclear)"
	@echo "  make clean-all           - Full cleanup: Local + RDS Airflow + ECS (nuclear)"
	@echo ""

# ========================================================================================
# SETUP AND ENVIRONMENT COMMANDS
# ========================================================================================

# Install project dependencies and set up environment using uv
install:
	@echo "📦 Installing project dependencies with uv (fast!)..."
	@echo "Creating virtual environment with uv..."
	@uv venv
	@echo "Installing dependencies with uv..."
	@uv pip install -r requirements.txt
	@echo "Installing project in editable mode..."
	@uv pip install -e .
	@echo "✅ Installation completed successfully!"
	@echo "To activate the virtual environment, run: source .venv/bin/activate"

# Create necessary directories
setup-dirs:
	@echo "📁 Creating necessary directories..."
	@mkdir -p data/raw
	@echo "✅ Directories created successfully!"
	@echo "ℹ️  Note: Artifacts are now stored in S3, no local artifact directories needed"

# Clean up local cache only (safe cleanup)
clean:
	@echo "🧹 Cleaning up local cache and temporary files..."
	@rm -rf mlruns  # MLflow now uses S3 backend
	@find . -path "./.venv" -prune -o -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -path "./.venv" -prune -o -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Local cleanup completed!"
	@echo "ℹ️  All artifacts are now stored in S3. Use 'make s3-clean' to clean S3 artifacts."

# Clean up S3 artifacts (project-specific only)
s3-clean:
	@echo "🗑️ Cleaning S3 ML pipeline artifacts..."
	@echo "⚠️ This will delete project artifacts from S3:"
	@echo "   • artifacts/data_artifacts/"
	@echo "   • artifacts/train_artifacts/"
	@echo "   • artifacts/inference_artifacts/"
	@echo "   • test/ (if exists)"
	@read -p "Continue? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo ""
	@echo "🗑️ Deleting data artifacts..."
	@aws s3 rm s3://zuucrew-mlflow-artifacts-prod/artifacts/data_artifacts/ --recursive 2>/dev/null || echo "No data artifacts found"
	@echo "🗑️ Deleting model artifacts..."
	@aws s3 rm s3://zuucrew-mlflow-artifacts-prod/artifacts/train_artifacts/ --recursive 2>/dev/null || echo "No training artifacts found"
	@echo "🗑️ Deleting inference artifacts..."
	@aws s3 rm s3://zuucrew-mlflow-artifacts-prod/artifacts/inference_artifacts/ --recursive 2>/dev/null || echo "No inference artifacts found"
	@echo "🗑️ Deleting test artifacts..."
	@aws s3 rm s3://zuucrew-mlflow-artifacts-prod/test/ --recursive 2>/dev/null || echo "No test artifacts found"
	@echo "✅ S3 artifacts cleaned!"

# Remove legacy local artifact folders (since we're S3-only now)
clean-local-artifacts:
	@echo "🗑️  Removing legacy local artifact folders..."
	@echo "⚠️ This will permanently delete local folders:"
	@echo "   • artifacts/ (all local ML artifacts)"
	@echo "   • data/processed/ (processed data now in S3)"
	@echo "   • mlruns/ (MLflow now uses S3 backend)"
	@echo "   • test_*.py (test files)"
	@read -p "Continue? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@rm -rf artifacts/
	@rm -rf data/processed/
	@rm -rf mlruns/
	@rm -f test_*.py
	@echo "✅ Legacy local artifacts removed - pipeline now uses S3-only!"

# ========================================================================================
# DOCKER COMMANDS
# ========================================================================================

# Docker compose file (single file - embedded PySpark architecture)
COMPOSE_FILE = docker-compose.yml

# Build all Docker images (embedded PySpark architecture)
docker-build:
	@echo "🚀 Building Docker images with embedded PySpark..."
	@echo "Using optimized multi-stage builds with embedded PySpark"
	@docker-compose -f $(COMPOSE_FILE) build --no-cache
	@echo "✅ Docker images built successfully!"
	@echo "💡 Containers include PySpark but default to pandas/scikit-learn processing"

# Start all services (MLflow + 3 pipeline containers)
docker-up:
	@echo "🚀 Starting all services (MLflow + pipeline containers)..."
	@docker-compose -f $(COMPOSE_FILE) up -d mlflow-tracking data-pipeline model-pipeline inference-pipeline
	@echo "✅ All 4 services started!"
	@echo "🌐 MLflow UI: http://localhost:5001"
	@echo "📊 Services: mlflow-tracking, data-pipeline, model-pipeline, inference-pipeline"

# Stop all services
docker-down:
	@echo "🛑 Stopping all Docker services..."
	@docker-compose -f $(COMPOSE_FILE) down
	@echo "✅ All Docker services stopped!"

# Clean up Docker resources
docker-clean:
	@echo "🧹 Cleaning up Docker resources..."
	@docker-compose -f $(COMPOSE_FILE) down -v --remove-orphans
	@docker system prune -f
	@echo "✅ Docker cleanup completed!"

# Nuclear cleanup - Remove ALL project Docker images and containers
docker-clean-all:
	@echo "🗑️ NUCLEAR DOCKER CLEANUP"
	@echo "========================="
	@echo "⚠️ This will PERMANENTLY delete:"
	@echo "   • All project containers (running and stopped)"
	@echo "   • All project Docker images (local + ECR tagged)"
	@echo "   • All ECS deployment images (churn-pipeline/*)"
	@echo "   • All project Docker volumes"
	@echo "   • All project Docker networks"
	@echo "   • Apache Spark images"
	@echo "   • MLflow images"
	@echo "   • Dangling images (old ARM64 versions)"
	@echo ""
	@read -p "Continue with nuclear cleanup? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo ""
	@echo "🛑 Stopping all containers..."
	@docker-compose down -v --remove-orphans 2>/dev/null || true
	@echo ""
	@echo "🗑️ Removing project containers..."
	@docker rm -f mlflow-tracking data-pipeline model-pipeline inference-pipeline spark-master spark-worker-1 spark-worker-2 spark-history-server 2>/dev/null || true
	@echo ""
	@echo "🗑️ Removing project images..."
	@docker rmi -f churn-pipeline/mlflow:latest 2>/dev/null || true
	@docker rmi -f churn-pipeline/data:latest 2>/dev/null || true
	@docker rmi -f churn-pipeline/model:latest 2>/dev/null || true
	@docker rmi -f churn-pipeline/inference:latest 2>/dev/null || true
	@docker rmi -f ml-pipeline/mlflow:latest 2>/dev/null || true
	@docker rmi -f ml-pipeline/data:latest 2>/dev/null || true
	@docker rmi -f ml-pipeline/model:latest 2>/dev/null || true
	@docker rmi -f ml-pipeline/inference:latest 2>/dev/null || true
	@docker rmi -f data-pipeline:latest 2>/dev/null || true
	@docker rmi -f model-pipeline:latest 2>/dev/null || true
	@docker rmi -f inference-pipeline:latest 2>/dev/null || true
	@docker rmi -f mlflow-tracking:latest 2>/dev/null || true
	@docker rmi -f churn-pipeline/airflow:2.8.1-amazon 2>/dev/null || true
	@echo ""
	@echo "🗑️ Removing ECS/ECR tagged images..."
	@docker images | grep "dkr.ecr" | grep "churn-pipeline" | awk '{print $$1":"$$2}' | xargs -r docker rmi -f 2>/dev/null || true
	@echo ""
	@echo "🗑️ Removing Apache Spark images..."
	@docker rmi -f apache/spark:3.4.1-scala2.12-java11-python3-ubuntu 2>/dev/null || true
	@docker rmi -f apache/spark:latest 2>/dev/null || true
	@docker rmi -f bitnami/spark:3.4.1 2>/dev/null || true
	@docker rmi -f bitnami/spark:latest 2>/dev/null || true
	@echo ""
	@echo "🗑️ Removing project networks..."
	@docker network rm churn-pipeline-network 2>/dev/null || true
	@echo ""
	@echo "🗑️ Removing project volumes..."
	@docker volume rm mlflow-database spark-event-logs 2>/dev/null || true
	@echo ""
	@echo "🗑️ Cleaning up dangling images and build cache..."
	@docker system prune -a -f --volumes
	@echo ""
	@echo "✅ NUCLEAR CLEANUP COMPLETED!"
	@echo "All project Docker resources have been removed."
	@echo ""
	@echo "💡 To rebuild everything:"
	@echo "   make docker-build"
	@echo "   make docker-up"

# Show Docker service status
docker-status:
	@echo "📊 Docker Service Status"
	@echo "======================="
	@docker-compose -f $(COMPOSE_FILE) ps 2>/dev/null || echo "No services running"
	@echo ""
	@echo "🌐 MLflow UI: http://localhost:5001"

# View Docker logs
docker-logs:
	@echo "📋 Docker Service Logs"
	@echo "======================"
	@docker-compose -f $(COMPOSE_FILE) logs --tail=50 -f

# Show Docker image sizes
docker-image-sizes:
	@echo "📏 Docker Image Sizes"
	@echo "===================="
	@docker images | grep "churn-pipeline/" || echo "No images found - run 'make docker-build' first"

# ========================================================================================
# ML PIPELINE COMMANDS (Local)
# ========================================================================================

# Run data preprocessing pipeline
data-pipeline: setup-dirs
	@echo "🔄 Running data preprocessing pipeline..."
	@.venv/bin/python pipelines/data_pipeline.py --engine pandas
	@echo "✅ Data pipeline completed successfully!"

# Run model training pipeline
train-pipeline: setup-dirs
	@echo "🎯 Running model training pipeline..."
	@.venv/bin/python pipelines/training_pipeline.py --engine sklearn
	@echo "✅ Training pipeline completed successfully!"

# Run model training pipeline with Docker MLflow URL
train-pipeline-docker: setup-dirs
	@echo "🎯 Running model training pipeline (Docker MLflow)..."
	@CONTAINERIZED=true .venv/bin/python pipelines/training_pipeline.py --engine sklearn
	@echo "✅ Training pipeline (Docker MLflow) completed successfully!"

# Run batch inference pipeline
inference-pipeline: setup-dirs
	@echo "🔮 Running batch inference pipeline..."
	@.venv/bin/python pipelines/inference_pipeline.py --engine pandas
	@echo "✅ Inference pipeline completed successfully!"

# Run all pipelines in sequence
run-all: data-pipeline train-pipeline inference-pipeline
	@echo "🎉 All pipelines completed successfully!"

# ========================================================================================
# AIRFLOW AUTOMATION COMMANDS (DockerOperator Approach)
# ========================================================================================

AIRFLOW_COMPOSE = "$(CURDIR)/docker-compose.airflow.yml"

# Build custom Airflow image with Docker and Amazon providers
airflow-build:
	@echo "🔨 Building custom Airflow image with Docker and Amazon providers..."
	@docker build -t churn-pipeline/airflow:2.8.1-amazon -f docker/Dockerfile.airflow .
	@echo "✅ Custom Airflow image built successfully!"

# Initialize Airflow database and create admin user (ALWAYS clears DAG history + cache)
airflow-init:
	@echo "🚀 Initializing LOCAL Airflow database..."
	@echo "🗑️  Clearing ALL historical data, volumes, logs, and DAG cache..."
	@docker compose -f $(AIRFLOW_COMPOSE) down -v 2>/dev/null || true
	@docker volume rm airflow-postgres-data 2>/dev/null || true
	@rm -rf airflow/logs/* 2>/dev/null || true
	@rm -rf airflow/__pycache__ 2>/dev/null || true
	@rm -rf airflow/dags/__pycache__ 2>/dev/null || true
	@rm -rf airflow/plugins/__pycache__ 2>/dev/null || true
	@find airflow/dags -name "*.pyc" -delete 2>/dev/null || true
	@find airflow/dags -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Local state, cache, and compiled files cleared"
	@echo ""
	@echo "📦 Creating fresh LOCAL Airflow database and admin user (admin/admin)..."
	@echo "   (Using LOCAL PostgreSQL container - NOT RDS)"
	@set -e; \
	docker network create churn-pipeline-network >/dev/null 2>&1 || true; \
	docker rm -f airflow-init >/dev/null 2>&1 || true; \
	docker compose -f $(AIRFLOW_COMPOSE) up --build airflow-init
	@echo "✅ Local Airflow initialization completed with clean slate!"
	@echo "ℹ️  ECS Airflow uses RDS (completely isolated)"

# Start Airflow services
airflow-up:
	@echo "🚀 Starting Airflow automation services..."
	@echo "Airflow UI will be available at: http://localhost:8080"
	@echo "Default credentials: admin/admin"
	@set -e; \
	docker network create churn-pipeline-network >/dev/null 2>&1 || true; \
	docker compose -f $(AIRFLOW_COMPOSE) up -d
	@echo "✅ Airflow services started!"
	@echo "🌐 Airflow UI: http://localhost:8080"
	@echo "🌸 Flower UI: http://localhost:5555"
	@echo "📋 DAGs available:"
	@echo "  • data_pipeline_every_10m (every 10 minutes)"
	@echo "  • train_pipeline_hourly (every hour)"
	@echo "  • inference_pipeline_every_2m (every 2 minutes)"

# Stop Airflow services
airflow-down:
	@echo "🛑 Stopping Airflow services..."
	@docker compose -f $(AIRFLOW_COMPOSE) down
	@echo "✅ Airflow services stopped!"

# Reset Airflow completely (stop services, remove volumes, clear all DAG history)
airflow-reset:
	@echo "🔥 RESETTING AIRFLOW - This will delete all DAG run history!"
	@echo "Stopping all Airflow services..."
	@docker compose -f $(AIRFLOW_COMPOSE) down -v
	@echo "Removing Airflow volumes..."
	@docker volume rm airflow-postgres-data 2>/dev/null || true
	@echo "Clearing local Airflow logs..."
	@rm -rf airflow/logs/*
	@echo "✅ Airflow reset complete! All DAG history cleared."
	@echo "💡 Run 'make airflow-init' to reinitialize Airflow"

# ========================================================================================
# S3 UTILITY COMMANDS
# ========================================================================================

# List S3 keys with prefix
s3-list:
	@echo "📋 Listing S3 keys..."
	@if [ -z "$(PREFIX)" ]; then echo "❌ Usage: make s3-list PREFIX=your-prefix"; exit 1; fi
	@aws s3 ls s3://zuucrew-mlflow-artifacts-prod/$(PREFIX) --recursive

# Delete specific S3 keys with prefix (use with caution)
s3-delete-prefix:
	@echo "🗑️ Deleting S3 keys with prefix: $(PREFIX)"
	@echo "⚠️ This will permanently delete data!"
	@read -p "Continue? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@./run_local.sh python -c "from utils.s3_io import list_keys, delete_key; keys = list_keys('$(PREFIX)'); [delete_key(k) for k in keys]; print(f'Deleted {len(keys)} keys')"

# Upload local data folders to S3 (one-time setup)
s3-upload-data:
	@echo "📤 Uploading data folders to S3 (one-time setup)..."
	@echo "This will upload:"
	@echo "   • data/raw/ → s3://bucket/data/raw/"
	@echo "   • data/processed/ → s3://bucket/data/processed/"
	@read -p "Continue? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@source $(VENV) && PYTHONPATH=. python scripts/upload_data_to_s3.py

# S3 smoke test (write/read roundtrip)
s3-smoke:
	@echo "🔬 Running S3 smoke test..."
	@./run_local.sh python -c "from utils.s3_io import put_bytes, get_bytes; test_data = b'Hello S3!'; put_bytes(test_data, key='test/smoke_test.txt'); result = get_bytes('test/smoke_test.txt'); print('✅ S3 smoke test passed!' if result == test_data else '❌ S3 smoke test failed!')"

# Test MLflow S3 integration
mlflow-s3-test:
	@echo "🧪 Testing MLflow S3 integration..."
	@source $(VENV) && PYTHONPATH=. python test_mlflow_s3.py

# Show project status
status:
	@echo "📊 Project Status"
	@echo "================="
	@echo "Python Version: $$(python --version 2>/dev/null || echo 'Not found')"
	@echo "Virtual Env: $$([[ -d .venv ]] && echo '✅ Created' || echo '❌ Not found')"
	@echo "Dependencies: $$([[ -f .venv/pyvenv.cfg ]] && echo '✅ Installed' || echo '❌ Not installed')"
	@echo ""
	@echo "🌐 S3 Configuration:"
	@echo "S3 Bucket: $$(source $(VENV) && python -c 'from utils.config import get_s3_bucket; print(get_s3_bucket())' 2>/dev/null || echo 'Not configured')"
	@echo "AWS Region: $$(source $(VENV) && python -c 'from utils.config import get_aws_region; print(get_aws_region())' 2>/dev/null || echo 'Not configured')"
	@echo "Force S3 I/O: $$(source $(VENV) && python -c 'from utils.config import force_s3_io; print(force_s3_io())' 2>/dev/null || echo 'Not configured')"
	@echo ""
	@echo "📈 Recent S3 Artifacts:"
	@source $(VENV) && PYTHONPATH=. python -c "from utils.s3_io import list_keys; keys = list_keys('artifacts/'); print('\\n'.join(keys[:5]))" 2>/dev/null || echo "No S3 artifacts found"

# ========================================================================================
# RDS DATABASE VISUALIZATION COMMANDS
# ========================================================================================

# Load RDS credentials from .env file if it exists
# Otherwise fall back to default values (for backward compatibility)
ifneq (,$(wildcard .env))
    include .env
    export
endif

# RDS Connection Parameters with fallbacks
RDS_HOST ?= churn-pipeline-metadata-db.cbqsg4cugpeo.ap-south-1.rds.amazonaws.com
RDS_USER ?= zuucrew
RDS_PASSWORD ?= churnpipe\#bprmls
RDS_PORT ?= 5432
RDS_MLFLOW_DB ?= mlflow
RDS_AIRFLOW_DB ?= airflow

# Show all RDS databases overview
rds-show-all:
	@echo "📊 Showing all RDS databases..."
	@set -a && [ -f .env ] && . .env && set +a && \
	source $(VENV) && \
	RDS_HOST="$${RDS_HOST:-$(RDS_HOST)}" RDS_USER="$${RDS_USER:-$(RDS_USER)}" RDS_PASSWORD="$${RDS_PASSWORD:-$(RDS_PASSWORD)}" RDS_PORT="$${RDS_PORT:-$(RDS_PORT)}" \
	python scripts/visualize_rds.py

# Show MLflow database schema
rds-show-mlflow:
	@echo "📊 Showing MLflow database schema..."
	@set -a && [ -f .env ] && . .env && set +a && \
	source $(VENV) && \
	RDS_HOST="$${RDS_HOST:-$(RDS_HOST)}" RDS_USER="$${RDS_USER:-$(RDS_USER)}" RDS_PASSWORD="$${RDS_PASSWORD:-$(RDS_PASSWORD)}" RDS_PORT="$${RDS_PORT:-$(RDS_PORT)}" \
	python scripts/visualize_rds.py --database $${RDS_MLFLOW_DB:-$(RDS_MLFLOW_DB)}

# Show Airflow database schema
rds-show-airflow:
	@echo "📊 Showing Airflow database schema..."
	@set -a && [ -f .env ] && . .env && set +a && \
	source $(VENV) && \
	RDS_HOST="$${RDS_HOST:-$(RDS_HOST)}" RDS_USER="$${RDS_USER:-$(RDS_USER)}" RDS_PASSWORD="$${RDS_PASSWORD:-$(RDS_PASSWORD)}" RDS_PORT="$${RDS_PORT:-$(RDS_PORT)}" \
	python scripts/visualize_rds.py --database $${RDS_AIRFLOW_DB:-$(RDS_AIRFLOW_DB)}

# Launch Adminer web UI for database visualization
rds-adminer:
	@echo "🚀 Launching Adminer web UI..."
	@docker run --name adminer-rds -d -p 8081:8080 --rm adminer:latest
	@echo "✅ Adminer started successfully!"
	@echo ""
	@echo "🌐 Adminer UI: http://localhost:8081"
	@echo ""
	@echo "📝 Connection Details:"
	@echo "  System:   PostgreSQL"
	@echo "  Server:   $(RDS_HOST):$(RDS_PORT)"
	@echo "  Username: $(RDS_USER)"
	@echo "  Password: $(RDS_PASSWORD)"
	@echo "  Database: mlflow or airflow"
	@echo ""
	@echo "💡 Stop with: make rds-adminer-down"

# Stop Adminer
rds-adminer-down:
	@echo "🛑 Stopping Adminer..."
	@docker stop adminer-rds 2>/dev/null || echo "Adminer not running"
	@echo "✅ Adminer stopped!"

# Connect to MLflow database with psql
rds-psql-mlflow:
	@echo "🔗 Connecting to MLflow database..."
	@echo "Type \\q to exit"
	@set -a && [ -f .env ] && . .env && set +a && \
	PGPASSWORD="$${RDS_PASSWORD:-$(RDS_PASSWORD)}" psql "sslmode=require host=$${RDS_HOST:-$(RDS_HOST)} port=$${RDS_PORT:-$(RDS_PORT)} dbname=$${RDS_MLFLOW_DB:-$(RDS_MLFLOW_DB)} user=$${RDS_USER:-$(RDS_USER)}"
# Connect to Airflow database with psql
rds-psql-airflow:
	@echo "🔗 Connecting to Airflow database..."
	@echo "Type \\q to exit"
	@set -a && [ -f .env ] && . .env && set +a && \
	PGPASSWORD="$${RDS_PASSWORD:-$(RDS_PASSWORD)}" psql "sslmode=require host=$${RDS_HOST:-$(RDS_HOST)} port=$${RDS_PORT:-$(RDS_PORT)} dbname=$${RDS_AIRFLOW_DB:-$(RDS_AIRFLOW_DB)} user=$${RDS_USER:-$(RDS_USER)}"

# Clear Airflow DAG cache and history from RDS
rds-clear-airflow-cache:
	@echo "🗑️  Clearing RDS Airflow DAG Cache and History..."
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "⚠️  WARNING: This will DELETE all Airflow DAG history from RDS!"
	@echo ""
	@echo "This will truncate the following tables:"
	@echo "  • task_instance (task execution history)"
	@echo "  • dag_run (DAG run history)"
	@echo "  • dag (DAG metadata)"
	@echo "  • xcom (inter-task communication data)"
	@echo "  • log (Airflow logs)"
	@echo "  • job (scheduler/executor jobs)"
	@echo "  • import_error (DAG import errors)"
	@echo ""
	@echo "💡 Use this when:"
	@echo "  - DAGs are missing in ECS Airflow UI"
	@echo "  - Old DAG metadata is causing conflicts"
	@echo "  - Need a fresh start for ECS deployment"
	@echo ""
	@echo "⚠️  Note: This affects ONLY RDS (ECS Airflow), not local setup"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@read -p "Continue? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	@echo ""
	@echo "🗑️  Truncating RDS tables..."
	@set -a && [ -f .env ] && . .env && set +a && \
	PGPASSWORD="$${RDS_PASSWORD:-$(RDS_PASSWORD)}" psql "sslmode=require host=$${RDS_HOST:-$(RDS_HOST)} port=$${RDS_PORT:-$(RDS_PORT)} dbname=$${RDS_AIRFLOW_DB:-$(RDS_AIRFLOW_DB)} user=$${RDS_USER:-$(RDS_USER)}" \
	  -c "SET session_replication_role = 'replica'; TRUNCATE TABLE task_instance CASCADE; TRUNCATE TABLE dag_run CASCADE; TRUNCATE TABLE xcom CASCADE; TRUNCATE TABLE log CASCADE; TRUNCATE TABLE import_error CASCADE; TRUNCATE TABLE job CASCADE; DELETE FROM dag; SET session_replication_role = 'origin';"
	@echo "📊 Verifying table counts..."
	@set -a && [ -f .env ] && . .env && set +a && \
	PGPASSWORD="$${RDS_PASSWORD:-$(RDS_PASSWORD)}" psql "sslmode=require host=$${RDS_HOST:-$(RDS_HOST)} port=$${RDS_PORT:-$(RDS_PORT)} dbname=$${RDS_AIRFLOW_DB:-$(RDS_AIRFLOW_DB)} user=$${RDS_USER:-$(RDS_USER)}" \
	  -c "SELECT 'task_instance' AS table_name, COUNT(*) AS row_count FROM task_instance UNION ALL SELECT 'dag_run', COUNT(*) FROM dag_run UNION ALL SELECT 'dag', COUNT(*) FROM dag UNION ALL SELECT 'xcom', COUNT(*) FROM xcom UNION ALL SELECT 'log', COUNT(*) FROM log UNION ALL SELECT 'import_error', COUNT(*) FROM import_error UNION ALL SELECT 'job', COUNT(*) FROM job;"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "✅ RDS Airflow DAG cache cleared!"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "🔄 Next Steps:"
	@echo "  1. Restart ECS Airflow scheduler:"
	@echo "     cd ecs-deploy && ./update_services.sh"
	@echo ""
	@echo "  2. Wait ~2-3 minutes for services to restart"
	@echo ""
	@echo "  3. Open Airflow UI:"
	@echo "     http://churn-pipeline-alb-375667739.ap-south-1.elb.amazonaws.com"
	@echo ""
	@echo "  4. DAGs should now be visible with clean history!"
	@echo ""

# ============================================================================
# 🎯 END-TO-END WORKFLOWS
# ============================================================================

# 1️⃣ Clean up EVERYTHING (Local + ECS)
clean-all:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🗑️  FULL CLEANUP - Local + ECS"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "1️⃣ Stopping and removing LOCAL Docker setup..."
	@$(MAKE) docker-down 2>/dev/null || true
	@$(MAKE) airflow-down 2>/dev/null || true
	@echo ""
	@echo "2️⃣ Removing LOCAL Docker images and volumes..."
	@$(MAKE) docker-clean-all
	@echo ""
	@echo "3️⃣ Flushing RDS Airflow metadata tables..."
	@set -a && [ -f .env ] && . .env && set +a && \
	if [ -n "$${RDS_HOST:-}" ] && [ -n "$${RDS_PASSWORD:-}" ]; then \
		echo "🗑️  Truncating RDS Airflow tables..."; \
		PGPASSWORD="$${RDS_PASSWORD}" psql "sslmode=require host=$${RDS_HOST} port=$${RDS_PORT:-5432} dbname=$${RDS_AIRFLOW_DB:-airflow} user=$${RDS_USER:-postgres}" -c "SET session_replication_role = 'replica'; TRUNCATE TABLE task_instance CASCADE; TRUNCATE TABLE dag_run CASCADE; TRUNCATE TABLE xcom CASCADE; TRUNCATE TABLE log CASCADE; TRUNCATE TABLE import_error CASCADE; TRUNCATE TABLE job CASCADE; DELETE FROM dag; SET session_replication_role = 'origin';" 2>/dev/null && echo "✅ RDS Airflow tables flushed" || echo "⚠️  RDS flush failed (may not exist yet)"; \
	else \
		echo "⏭️  Skipped (no RDS credentials in .env)"; \
	fi
	@echo ""
	@echo "4️⃣ Cleaning up ECS resources..."
	@echo "⚠️  This will DELETE all ECS services, tasks, and AWS resources!"
	@read -p "Continue with ECS cleanup? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		cd ecs-deploy && ./99_cleanup_all.sh; \
		echo "✅ ECS cleanup complete"; \
	else \
		echo "⏭️  Skipped ECS cleanup"; \
	fi
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "✅ Full cleanup complete!"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ========================================================================================
# KAFKA STREAMING
# ========================================================================================

.PHONY: kafka-build kafka-up kafka-down kafka-logs kafka-status kafka-clean kafka-restart kafka-ui setup-analytics-tables

# Build Kafka services
kafka-build:
	@echo "🔨 Building Kafka services..."
	@docker-compose -f docker-compose.kafka.yml build
	@echo "✅ Kafka services built successfully!"

# Start Kafka stack
kafka-up:
	@echo "🚀 Starting Kafka stack..."
	@docker-compose -f docker-compose.kafka.yml up -d
	@echo "✅ Kafka stack started!"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "🎉 Kafka Endpoints:"
	@echo "   • Kafka Broker: localhost:9092"
	@echo "   • Kafka UI: http://localhost:8090"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Stop Kafka stack
kafka-down:
	@echo "🛑 Stopping Kafka stack..."
	@docker-compose -f docker-compose.kafka.yml down
	@echo "✅ Kafka stack stopped!"

# View Kafka logs
kafka-logs:
	@echo "📋 Showing Kafka logs (Ctrl+C to exit)..."
	@docker-compose -f docker-compose.kafka.yml logs -f

# Show Kafka stack status
kafka-status:
	@echo "📊 Kafka Stack Status:"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@docker-compose -f docker-compose.kafka.yml ps

# Clean Kafka (including volumes)
kafka-clean:
	@echo "🧹 Cleaning Kafka (including volumes)..."
	@docker-compose -f docker-compose.kafka.yml down -v
	@echo "✅ Kafka cleaned!"

# Restart Kafka stack
kafka-restart: kafka-down kafka-up
	@echo "✅ Kafka stack restarted!"

# Open Kafka UI in browser
kafka-ui:
	@echo "🌐 Opening Kafka UI..."
	@open http://localhost:8090 || xdg-open http://localhost:8090 || echo "Open http://localhost:8090 manually"

# Create RDS analytics tables
setup-analytics-tables:
	@echo "🗄️  Creating RDS analytics tables..."
	@set -a && [ -f .env ] && . .env && set +a && \
	if [ -n "$${RDS_HOST:-}" ] && [ -n "$${RDS_PASSWORD:-}" ]; then \
		PGPASSWORD="$${RDS_PASSWORD}" psql "sslmode=require host=$${RDS_HOST} port=$${RDS_PORT:-5432} dbname=$${RDS_DB_NAME:-postgres} user=$${RDS_USERNAME:-postgres}" -f sql/create_analytics_tables.sql && \
		echo "✅ Analytics tables created successfully!" || \
		(echo "❌ Failed to create analytics tables" && exit 1); \
	else \
		echo "❌ RDS credentials not found in .env"; \
		exit 1; \
	fi


# ========================================================================================
# NUCLEAR DOCKER CLEANUP (WARNING: DESTROYS EVERYTHING)
# ========================================================================================

.PHONY: docker-nuke docker-nuke-confirm

# Nuclear cleanup - removes ALL Docker resources
docker-nuke-confirm:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "☢️  NUCLEAR DOCKER CLEANUP - COMPLETE DESTRUCTION"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "⚠️  THIS WILL DELETE EVERYTHING IN DOCKER:"
	@echo ""
	@echo "  ✗ ALL containers (running and stopped)"
	@echo "  ✗ ALL images (including cached layers)"
	@echo "  ✗ ALL volumes (including data)"
	@echo "  ✗ ALL networks (custom networks)"
	@echo "  ✗ ALL build cache"
	@echo "  ✗ ALL dangling resources"
	@echo ""
	@echo "This affects:"
	@echo "  • This project (Airflow, Kafka, MLflow)"
	@echo "  • ALL OTHER Docker projects on your system"
	@echo "  • ALL Docker images (you'll need to rebuild everything)"
	@echo ""
	@echo "💾 Data preserved:"
	@echo "  ✓ AWS S3 (ML artifacts)"
	@echo "  ✓ AWS RDS (database)"
	@echo "  ✓ Local files (code, config)"
	@echo ""

docker-nuke: docker-nuke-confirm
	@read -p "⚠️  Type 'NUKE' to confirm complete destruction: " confirm; \
	if [ "$$confirm" != "NUKE" ]; then \
		echo ""; \
		echo "❌ Cleanup cancelled"; \
		exit 1; \
	fi
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "☢️  Starting Nuclear Cleanup..."
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "1️⃣ Stopping all running containers..."
	@docker stop $$(docker ps -aq) 2>/dev/null || echo "   No running containers"
	@echo "   ✅ All containers stopped"
	@echo ""
	@echo "2️⃣ Removing all containers..."
	@docker rm -f $$(docker ps -aq) 2>/dev/null || echo "   No containers to remove"
	@echo "   ✅ All containers removed"
	@echo ""
	@echo "3️⃣ Removing all images..."
	@docker rmi -f $$(docker images -aq) 2>/dev/null || echo "   No images to remove"
	@echo "   ✅ All images removed"
	@echo ""
	@echo "4️⃣ Removing all volumes..."
	@docker volume rm $$(docker volume ls -q) 2>/dev/null || echo "   No volumes to remove"
	@echo "   ✅ All volumes removed"
	@echo ""
	@echo "5️⃣ Removing all networks..."
	@docker network rm $$(docker network ls -q) 2>/dev/null || echo "   Only default networks remain"
	@echo "   ✅ All custom networks removed"
	@echo ""
	@echo "6️⃣ Pruning Docker system..."
	@docker system prune -af --volumes 2>/dev/null || echo "   System already clean"
	@echo "   ✅ System pruned"
	@echo ""
	@echo "7️⃣ Cleaning build cache..."
	@docker builder prune -af 2>/dev/null || echo "   Build cache already clean"
	@echo "   ✅ Build cache cleaned"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "✅ NUCLEAR CLEANUP COMPLETE!"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "📊 Docker Status:"
	@echo "   Containers: $$(docker ps -a | wc -l | xargs) (should be 1 - header only)"
	@echo "   Images:     $$(docker images | wc -l | xargs) (should be 1 - header only)"
	@echo "   Volumes:    $$(docker volume ls | wc -l | xargs) (should be 1 - header only)"
	@echo "   Networks:   $$(docker network ls | wc -l | xargs) (should be 4 - default networks)"
	@echo ""
	@echo "💾 Disk space reclaimed:"
	@docker system df
	@echo ""
	@echo "🔄 To rebuild and restart:"
	@echo "   ./run_local.sh"
	@echo ""
	@echo "⚠️  Note: First build will take longer (no cached layers)"
	@echo ""


# ========================================================================================
# PAUSE/RESUME STREAMING & TRAINING
# ========================================================================================

.PHONY: pause-streaming resume-streaming

# Pause Kafka services and Airflow DAGs
pause-streaming:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "⏸️  PAUSING STREAMING & TRAINING"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "1️⃣ Pausing Kafka services..."
	@docker stop kafka-producer 2>/dev/null && echo "   ✅ Producer stopped" || echo "   ⚠️  Producer not running"
	@docker stop kafka-consumer 2>/dev/null && echo "   ✅ Consumer stopped" || echo "   ⚠️  Consumer not running"
	@echo ""
	@echo "2️⃣ Pausing Airflow DAGs..."
	@docker exec airflow-webserver airflow dags pause data_pipeline_every_20m 2>/dev/null && \
		echo "   ✅ data_pipeline_every_20m paused" || echo "   ⚠️  data_pipeline_every_20m not found"
	@docker exec airflow-webserver airflow dags pause train_pipeline_every_60m 2>/dev/null && \
		echo "   ✅ train_pipeline_every_60m paused" || echo "   ⚠️  train_pipeline_every_60m not found"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "✅ STREAMING & TRAINING PAUSED"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "📊 Status:"
	@echo "   • Kafka Producer:  Stopped"
	@echo "   • Kafka Consumer:  Stopped (no real-time inference)"
	@echo "   • Data Pipeline:   Paused (won't run on schedule)"
	@echo "   • Training DAG:    Paused (won't run on schedule)"
	@echo ""
	@echo "💡 Note: Kafka broker, analytics, and Airflow still running"
	@echo "🔄 Resume with: make resume-streaming"
	@echo ""

# Resume Kafka services and Airflow DAGs
resume-streaming:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "▶️  RESUMING STREAMING & TRAINING"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "1️⃣ Resuming Kafka services..."
	@docker start kafka-producer 2>/dev/null && echo "   ✅ Producer started" || echo "   ⚠️  Producer failed to start"
	@docker start kafka-consumer 2>/dev/null && echo "   ✅ Consumer started" || echo "   ⚠️  Consumer failed to start"
	@echo ""
	@echo "2️⃣ Resuming Airflow DAGs..."
	@docker exec airflow-webserver airflow dags unpause data_pipeline_every_20m 2>/dev/null && \
		echo "   ✅ data_pipeline_every_20m resumed" || echo "   ⚠️  data_pipeline_every_20m not found"
	@docker exec airflow-webserver airflow dags unpause train_pipeline_every_60m 2>/dev/null && \
		echo "   ✅ train_pipeline_every_60m resumed" || echo "   ⚠️  train_pipeline_every_60m not found"
	@echo ""
	@echo "⏳ Waiting for services to initialize..."
	@sleep 5
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "✅ STREAMING & TRAINING RESUMED"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "📊 Status:"
	@echo "   • Kafka Producer:  Running (streaming events)"
	@echo "   • Kafka Consumer:  Running (real-time inference)"
	@echo "   • Data Pipeline:   Active (scheduled execution)"
	@echo "   • Training DAG:    Active (scheduled execution)"
	@echo ""
	@echo "💡 View logs:"
	@echo "   • Producer:  docker logs -f kafka-producer"
	@echo "   • Consumer:  docker logs -f kafka-consumer"
	@echo "   • All Kafka: make kafka-logs"
	@echo ""